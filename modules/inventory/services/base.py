"""
Akıllı İş - Stok Modülü Servisleri
KRİTİK DÜZELTMELER:
1. Transaction yönetimi (hareket + bakiye aynı transaction'da)
2. Negatif stok kontrolü
3. Maliyet hesaplama düzeltmesi (çıkışlarda mevcut maliyet kullan)
4. Unique constraint kontrolleri
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_session
from database.models import (
    Item,
    Unit,
    Warehouse,
    ItemCategory,
    StockMovement,
    StockMovementType,
    StockBalance,
    Currency,
)

# Alias for backward compatibility
Category = ItemCategory


class ServiceBase:
    """Temel servis sınıfı"""

    def __init__(self):
        self.session: Session = get_session()

    def close(self):
        if self.session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class NegativeStockError(Exception):
    """Negatif stok hatası"""

    def __init__(
        self,
        item_code: str,
        warehouse_name: str,
        available: Decimal,
        requested: Decimal,
    ):
        self.item_code = item_code
        self.warehouse_name = warehouse_name
        self.available = available
        self.requested = requested
        super().__init__(
            f"Yetersiz stok! {item_code} için {warehouse_name} deposunda "
            f"mevcut: {available}, istenen: {requested}"
        )


class DuplicateCodeError(Exception):
    """Tekrarlayan kod hatası"""

    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"{field} '{value}' zaten kullanılıyor!")


class ItemService(ServiceBase):
    """Stok kartı servisi"""

    def get_all(self, active_only: bool = True) -> List[Item]:
        from sqlalchemy.orm import joinedload

        query = self.session.query(Item).options(
            joinedload(Item.currency),
            joinedload(Item.unit),
            joinedload(Item.category),
        )
        if active_only:
            query = query.filter(Item.is_active == True)
        return query.order_by(Item.code).all()

    def get_by_id(self, item_id: int) -> Optional[Item]:
        return self.session.query(Item).filter(Item.id == item_id).first()

    def get_by_code(self, code: str) -> Optional[Item]:
        return self.session.query(Item).filter(Item.code == code).first()

    def get_by_barcode(self, barcode: str) -> Optional[Item]:
        if not barcode:
            return None
        return self.session.query(Item).filter(Item.barcode == barcode).first()

    def check_unique_code(self, code: str, exclude_id: int = None) -> bool:
        """Kod benzersiz mi kontrol et"""
        query = self.session.query(Item).filter(Item.code == code)
        if exclude_id:
            query = query.filter(Item.id != exclude_id)
        return query.first() is None

    def check_unique_barcode(self, barcode: str, exclude_id: int = None) -> bool:
        """Barkod benzersiz mi kontrol et"""
        if not barcode:
            return True
        query = self.session.query(Item).filter(Item.barcode == barcode)
        if exclude_id:
            query = query.filter(Item.id != exclude_id)
        return query.first() is None

    def create(self, **kwargs) -> Item:
        """Yeni stok kartı oluştur - Unique kontrollü"""
        code = kwargs.get("code", "").strip().upper()
        barcode = kwargs.get("barcode", "").strip() if kwargs.get("barcode") else None

        # Unique kontrolleri
        if not self.check_unique_code(code):
            raise DuplicateCodeError("Stok Kodu", code)

        if barcode and not self.check_unique_barcode(barcode):
            raise DuplicateCodeError("Barkod", barcode)

        kwargs["code"] = code
        kwargs["barcode"] = barcode

        item = Item(**kwargs)
        self.session.add(item)
        self.session.commit()
        return item

    def update(self, item_id: int, **kwargs) -> Optional[Item]:
        """Stok kartı güncelle - Unique kontrollü"""
        item = self.get_by_id(item_id)
        if not item:
            return None

        # Kod değişiyorsa unique kontrol
        if "code" in kwargs:
            new_code = kwargs["code"].strip().upper()
            if new_code != item.code and not self.check_unique_code(new_code, item_id):
                raise DuplicateCodeError("Stok Kodu", new_code)
            kwargs["code"] = new_code

        # Barkod değişiyorsa unique kontrol
        if "barcode" in kwargs:
            new_barcode = kwargs["barcode"].strip() if kwargs["barcode"] else None
            if new_barcode and new_barcode != item.barcode:
                if not self.check_unique_barcode(new_barcode, item_id):
                    raise DuplicateCodeError("Barkod", new_barcode)
            kwargs["barcode"] = new_barcode

        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)

        self.session.commit()
        return item

    def delete(self, item_id: int) -> bool:
        item = self.get_by_id(item_id)
        if not item:
            return False

        # 1. Hareket kontrolü
        movement_count = (
            self.session.query(StockMovement)
            .filter(StockMovement.item_id == item_id)
            .count()
        )
        if movement_count > 0:
            raise ValueError(
                "Bu stok kartına ait hareket kayıtları (giriş/çıkış) olduğu için silinemez.\n\n"
                "Bunun yerine kartı düzenleyip 'Aktif' işaretini kaldırarak pasife çekebilirsiniz."
            )

        try:
            self.session.delete(item)
            self.session.commit()
            return True
        except IntegrityError:
            self.session.rollback()
            raise ValueError(
                "Bu stok kartı başka kayıtlarda kullanıldığı için silinemez."
            )

    def search(
        self,
        query: str = None,
        keyword: str = None,
        item_type: str = None,
        is_active: bool = True,
        stock_status: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Item]:
        """Stok kartı ara - keyword, query veya item_type parametresi ile"""
        search_term = keyword or query or ""

        q = self.session.query(Item)

        # Aktiflik filtresi (None ise hepsi, True/False ise ona göre)
        if is_active is not None:
            q = q.filter(Item.is_active == is_active)

        if search_term:
            q = q.filter(
                (
                    Item.code.ilike(f"%{search_term}%")
                    | Item.name.ilike(f"%{search_term}%")
                    | Item.barcode.ilike(f"%{search_term}%")
                )
            )

        if item_type:
            q = q.filter(Item.item_type == item_type)

        if stock_status:
            q = self._apply_stock_status_filter(q, stock_status)

        return q.order_by(Item.code.asc()).offset(offset).limit(limit).all()

    def count_search(
        self,
        query: str = None,
        keyword: str = None,
        item_type: str = None,
        is_active: bool = True,
        stock_status: str = None,
    ) -> int:
        """Arama kriterlerine uyan toplam kayıt sayısını döner"""
        search_term = keyword or query or ""

        # Eğer stok durumu filtresi varsa, COUNT(*) yerine subquery kullanmalıyız
        if stock_status:
            q = self.session.query(Item.id)
        else:
            q = self.session.query(func.count(Item.id))

        # Aktiflik filtresi
        if is_active is not None:
            q = q.filter(Item.is_active == is_active)

        if search_term:
            q = q.filter(
                (
                    Item.code.ilike(f"%{search_term}%")
                    | Item.name.ilike(f"%{search_term}%")
                    | Item.barcode.ilike(f"%{search_term}%")
                )
            )

        if item_type:
            q = q.filter(Item.item_type == item_type)

        if stock_status:
            q = self._apply_stock_status_filter(q, stock_status)
            return q.count()

        return q.scalar()

    def get_stats(
        self,
        query: str = None,
        keyword: str = None,
        item_type: str = None,
        is_active: bool = True,
        stock_status: str = None,
    ) -> dict:
        """Stok istatistiklerini hesapla"""
        search_term = keyword or query or ""

        q = self.session.query(Item)

        if is_active is not None:
            q = q.filter(Item.is_active == is_active)

        if search_term:
            q = q.filter(
                (
                    Item.code.ilike(f"%{search_term}%")
                    | Item.name.ilike(f"%{search_term}%")
                    | Item.barcode.ilike(f"%{search_term}%")
                )
            )

        if item_type:
            q = q.filter(Item.item_type == item_type)

        # Performans için sadece gerekli kolonları ve ilişkileri çekmek gerekebilir
        # Şimdilik tutarlılık için model üzerinden gidiyoruz
        items = q.all()

        stats = {
            "total": len(items),
            "normal": 0,
            "low": 0,
            "critical": 0,
            "out_of_stock": 0,
            "total_value": Decimal(0),
        }

        for item in items:
            status = item.stock_status
            if status == "normal":
                stats["normal"] += 1
            elif status == "low":
                stats["low"] += 1
            elif status == "critical":
                stats["critical"] += 1
            elif status == "out_of_stock":
                stats["out_of_stock"] += 1

            # Stok değeri
            qty = item.total_stock
            price = item.purchase_price or Decimal(0)
            stats["total_value"] += qty * price

        return stats

    def get_last_purchase_price(self, item_id: int) -> Optional[Decimal]:
        """Stok kartının son satınalma fiyatını getir"""
        from database.models import StockMovement, StockMovementType

        last_purchase = (
            self.session.query(StockMovement)
            .filter(
                StockMovement.item_id == item_id,
                StockMovement.movement_type == StockMovementType.SATIN_ALMA,
            )
            .order_by(StockMovement.created_at.desc())
            .first()
        )

        return last_purchase.unit_price if last_purchase else None

    def _apply_stock_status_filter(self, query, status):
        """Stok durumu filtresini uygula"""
        if not status:
            return query

        # Join ve Group By ekle
        # Not: outerjoin kullanıyoruz çünkü stoğu 0 olan (kaydı olmayan) ürünler de listede olmalı
        query = query.outerjoin(StockBalance, Item.id == StockBalance.item_id).group_by(
            Item.id
        )

        # Toplam stok miktarı ifadesi
        total_stock = func.sum(func.coalesce(StockBalance.quantity, 0))

        if status == "out_of_stock":
            query = query.having(total_stock <= 0)
        elif status == "critical":
            # Min stok varsa ve stok <= min_stock
            query = query.having(
                (total_stock > 0) & (total_stock <= func.coalesce(Item.min_stock, 0))
            )
        elif status == "low":
            # Model: elif self.reorder_point and total <= self.reorder_point: return "low"
            # Ayrıca kritik veya bitik olmamalı
            query = query.having(
                (total_stock > func.coalesce(Item.min_stock, 0))
                & (total_stock <= func.coalesce(Item.reorder_point, 0))
            )
        elif status == "normal":
            # Diğer durumların tersi
            query = query.having(
                (total_stock > 0)
                & (total_stock > func.coalesce(Item.min_stock, 0))
                & (total_stock > func.coalesce(Item.reorder_point, 0))
            )

        return query

    def get_next_code(self, prefix: str = "STK") -> str:
        """
        Sonraki stok kodunu üret
        NOT: Çok kullanıcılı sistemde race condition riski var.
        Üretim ortamında DB sequence veya SELECT FOR UPDATE kullanılmalı.
        """
        last_item = (
            self.session.query(Item)
            .filter(Item.code.like(f"{prefix}%"))
            .order_by(Item.code.desc())
            .first()
        )

        if last_item:
            try:
                last_num = int(last_item.code.replace(prefix, ""))
                return f"{prefix}{last_num + 1:06d}"
            except ValueError:
                pass
        return f"{prefix}000001"


class UnitService(ServiceBase):
    """Birim servisi"""

    def get_all(self, active_only: bool = True) -> List[Unit]:
        query = self.session.query(Unit)
        if active_only:
            query = query.filter(Unit.is_active == True)
        return query.order_by(Unit.code).all()

    def get_by_id(self, unit_id: int) -> Optional[Unit]:
        return self.session.query(Unit).filter(Unit.id == unit_id).first()

    def get_by_code(self, code: str) -> Optional[Unit]:
        return self.session.query(Unit).filter(Unit.code == code).first()

    def create(self, **kwargs) -> Unit:
        code = kwargs.get("code", "").strip().upper()
        existing = self.get_by_code(code)
        if existing:
            raise DuplicateCodeError("Birim Kodu", code)

        kwargs["code"] = code
        unit = Unit(**kwargs)
        self.session.add(unit)
        self.session.commit()
        return unit

    def update(self, unit_id: int, **kwargs) -> Optional[Unit]:
        unit = self.get_by_id(unit_id)
        if not unit:
            return None

        if "code" in kwargs:
            new_code = kwargs["code"].strip().upper()
            if new_code != unit.code:
                existing = self.get_by_code(new_code)
                if existing:
                    raise DuplicateCodeError("Birim Kodu", new_code)
            kwargs["code"] = new_code

        for key, value in kwargs.items():
            if hasattr(unit, key):
                setattr(unit, key, value)
        self.session.commit()
        return unit

    def convert(self, amount: Decimal, from_unit_id: int, to_unit_id: int) -> Decimal:
        """Birim dönüşümü yap."""
        if from_unit_id == to_unit_id:
            return amount

        # Basit dönüşüm mantığı - Şimdilik sadece 1-1 varsayıyoruz veya conversion tablosu eklenecek.
        # İleride UnitConversion tablosundan katsayı alınacak.
        # Şu anlık proje kapsamında birim dönüşüm tablosu olmadığı için
        # sadece isim bazlı (kg->ton gibi) basit kontrol yapabiliriz veya
        # kullanıcı manuel girmeli.
        # Plan gereği şimdilik pas geçiyoruz, stok giriş ekranında kullanıcı yönetecek.
        return amount


class CategoryService(ServiceBase):
    """Kategori servisi"""

    def get_all(self, active_only: bool = True) -> List[Category]:
        query = self.session.query(Category)
        if active_only:
            query = query.filter(Category.is_active == True)
        return query.order_by(Category.name).all()

    def get_by_id(self, category_id: int) -> Optional[Category]:
        return self.session.query(Category).filter(Category.id == category_id).first()

    def get_root_categories(self) -> List[Category]:
        return (
            self.session.query(Category)
            .filter(Category.parent_id == None, Category.is_active == True)
            .order_by(Category.name)
            .all()
        )

    def create(self, **kwargs) -> Category:
        category = Category(**kwargs)
        self.session.add(category)
        self.session.commit()
        return category

    def update(self, category_id: int, **kwargs) -> Optional[Category]:
        category = self.get_by_id(category_id)
        if not category:
            return None
        for key, value in kwargs.items():
            if hasattr(category, key):
                setattr(category, key, value)
        self.session.commit()
        return category

    def delete(self, category_id: int) -> bool:
        category = self.get_by_id(category_id)
        if category:
            self.session.delete(category)
            self.session.commit()
            return True
        return False


class WarehouseService(ServiceBase):
    """Depo servisi"""

    def get_all(self, active_only: bool = True) -> List[Warehouse]:
        query = self.session.query(Warehouse)
        if active_only:
            query = query.filter(Warehouse.is_active == True)
        return query.order_by(Warehouse.code).all()

    def get_by_id(self, warehouse_id: int) -> Optional[Warehouse]:
        return (
            self.session.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        )

    def get_by_code(self, code: str) -> Optional[Warehouse]:
        return self.session.query(Warehouse).filter(Warehouse.code == code).first()

    def get_default(self) -> Optional[Warehouse]:
        return (
            self.session.query(Warehouse)
            .filter(Warehouse.is_default == True, Warehouse.is_active == True)
            .first()
        )

    def create(self, **kwargs) -> Warehouse:
        code = kwargs.get("code", "").strip().upper()
        existing = self.get_by_code(code)
        if existing:
            raise DuplicateCodeError("Depo Kodu", code)

        # Tek default depo kuralı
        if kwargs.get("is_default", False):
            self._clear_default()

        kwargs["code"] = code
        warehouse = Warehouse(**kwargs)
        self.session.add(warehouse)
        self.session.commit()
        return warehouse

    def update(self, warehouse_id: int, **kwargs) -> Optional[Warehouse]:
        warehouse = self.get_by_id(warehouse_id)
        if not warehouse:
            return None

        if "code" in kwargs:
            new_code = kwargs["code"].strip().upper()
            if new_code != warehouse.code:
                existing = self.get_by_code(new_code)
                if existing:
                    raise DuplicateCodeError("Depo Kodu", new_code)
            kwargs["code"] = new_code

        # Tek default depo kuralı
        if kwargs.get("is_default", False) and not warehouse.is_default:
            self._clear_default()

        for key, value in kwargs.items():
            if hasattr(warehouse, key):
                setattr(warehouse, key, value)
        self.session.commit()
        return warehouse

    def _clear_default(self):
        """Tüm depoların default durumunu kaldır"""
        self.session.query(Warehouse).filter(Warehouse.is_default == True).update(
            {Warehouse.is_default: False}
        )

    def delete(self, warehouse_id: int) -> bool:
        warehouse = self.get_by_id(warehouse_id)
        if warehouse:
            self.session.delete(warehouse)
            self.session.commit()
            return True
        return False


class StockMovementService(ServiceBase):
    """
    Stok hareket servisi
    KRİTİK DÜZELTMELER:
    1. Transaction yönetimi - hareket ve bakiye aynı transaction'da
    2. Negatif stok kontrolü - çıkışlarda stok yeterliliği kontrolü
    3. Maliyet hesaplama - çıkışlarda mevcut stok maliyeti kullanılır
    """

    def __init__(self, allow_negative_stock: bool = False):
        super().__init__()
        self.allow_negative_stock = allow_negative_stock

    def get_all(self, limit: int = 100) -> List[StockMovement]:
        return (
            self.session.query(StockMovement)
            .order_by(StockMovement.movement_date.desc())
            .limit(limit)
            .all()
        )

    def get_movements(
        self,
        item_id: int = None,
        warehouse_id: int = None,
        movement_type: StockMovementType = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100,
    ) -> List[StockMovement]:
        """Filtrelenmiş stok hareketleri listesi"""
        from sqlalchemy.orm import joinedload

        query = self.session.query(StockMovement).options(
            joinedload(StockMovement.item),
            joinedload(StockMovement.unit),
            joinedload(StockMovement.from_warehouse),
            joinedload(StockMovement.to_warehouse),
            joinedload(StockMovement.secondary_unit),
            joinedload(StockMovement.currency),
        )

        if item_id:
            query = query.filter(StockMovement.item_id == item_id)

        if warehouse_id:
            query = query.filter(
                (StockMovement.from_warehouse_id == warehouse_id)
                | (StockMovement.to_warehouse_id == warehouse_id)
            )

        if movement_type:
            query = query.filter(StockMovement.movement_type == movement_type)

        if start_date:
            query = query.filter(StockMovement.movement_date >= start_date)

        if end_date:
            query = query.filter(StockMovement.movement_date <= end_date)

        return query.order_by(StockMovement.movement_date.desc()).limit(limit).all()

    def get_by_id(self, movement_id: int) -> Optional[StockMovement]:
        return (
            self.session.query(StockMovement)
            .filter(StockMovement.id == movement_id)
            .first()
        )

    def get_by_item(self, item_id: int, limit: int = 50) -> List[StockMovement]:
        return (
            self.session.query(StockMovement)
            .filter(StockMovement.item_id == item_id)
            .order_by(StockMovement.movement_date.desc())
            .limit(limit)
            .all()
        )

    def get_by_warehouse(
        self, warehouse_id: int, limit: int = 50
    ) -> List[StockMovement]:
        return (
            self.session.query(StockMovement)
            .filter(
                (StockMovement.from_warehouse_id == warehouse_id)
                | (StockMovement.to_warehouse_id == warehouse_id)
            )
            .order_by(StockMovement.movement_date.desc())
            .limit(limit)
            .all()
        )

    def get_balance(self, item_id: int, warehouse_id: int) -> Optional[StockBalance]:
        """Belirli depo için stok bakiyesi"""
        return (
            self.session.query(StockBalance)
            .filter(
                StockBalance.item_id == item_id,
                StockBalance.warehouse_id == warehouse_id,
            )
            .first()
        )

    def get_available_quantity(self, item_id: int, warehouse_id: int) -> Decimal:
        """Mevcut stok miktarı (rezerve edilen hariç)"""
        balance = self.get_balance(item_id, warehouse_id)
        if not balance:
            return Decimal(0)
        # Kullanılabilir miktar = Toplam miktar - Rezerve miktar
        reserved = balance.reserved_quantity or Decimal(0)
        return balance.quantity - reserved

    def get_current_cost(self, item_id: int, warehouse_id: int) -> Decimal:
        """Mevcut stok birim maliyeti (ağırlıklı ortalama)"""
        balance = self.get_balance(item_id, warehouse_id)
        if balance and balance.quantity > 0:
            return balance.unit_cost

        # Bakiye yoksa stok kartından al
        item = self.session.query(Item).filter(Item.id == item_id).first()
        return item.purchase_price if item and item.purchase_price else Decimal(0)

    def create_movement(
        self,
        item_id: int,
        movement_type: StockMovementType,
        quantity: Decimal,
        from_warehouse_id: int = None,
        to_warehouse_id: int = None,
        unit_price: Decimal = None,
        document_no: str = None,
        document_type: str = None,
        description: str = None,
        lot_number: str = None,
        movement_date: datetime = None,
        # === Dual-Unit (İkincil Birim) ===
        secondary_quantity: Decimal = None,
        secondary_unit_id: int = None,
        # === Currency ===
        currency_id: int = None,
        exchange_rate: Decimal = None,
    ) -> StockMovement:
        """
        Stok hareketi oluştur
        """

        if quantity <= 0:
            raise ValueError("Miktar sıfırdan büyük olmalıdır!")

        quantity = Decimal(str(quantity))
        unit_price = Decimal(str(unit_price)) if unit_price else Decimal(0)

        # Kur dönüşümü
        exchange_rate = Decimal(str(exchange_rate)) if exchange_rate else Decimal(1)
        if currency_id and exchange_rate > 1:
            # Fiyat dövizli gelmiş, TL'ye çevirip unit_price (TL) olarak kaydedelim mi?
            # Modelde unit_price TL tutulmalı (standart), ayrıca currency_id ve rate saklanmalı.
            # Gelen unit_price DÖVİZLİ ise:
            movement_cost = unit_price * exchange_rate  # TL Maliyet
            # Ancak unit_price parametresi fonksiyona hangisi geliyor?
            # Servis çağrılırken TL'ye çevrilmiş mi yoksa ham mı?
            # Ham kabul edelim, burada çevirelim.
            # unit_price -> Veritabanında TL tutulur.
            # O yüzden veritabanına yazarken unit_price alanına TL yazacağız.
            pass
        else:
            movement_cost = unit_price

        # İkincil birim miktarını Decimal'e çevir
        if secondary_quantity is not None:
            secondary_quantity = Decimal(str(secondary_quantity))

        # Hareket tipine göre kontroller ve maliyet belirleme
        if movement_type in [
            StockMovementType.GIRIS,
            StockMovementType.SATIN_ALMA,
            StockMovementType.URETIM_CIKIS,
            StockMovementType.SAYIM_FAZLA,
            StockMovementType.IADE_ALIS,
        ]:
            # GİRİŞ işlemleri - to_warehouse zorunlu
            if not to_warehouse_id:
                raise ValueError("Giriş işlemleri için hedef depo zorunludur!")

            # Giriş maliyeti (TL)
            # Eğer yukarıda kur ile çarptıysak movement_cost TL'dir.
            # Eğer kur yoksa movement_cost = unit_price (TL)
            pass

        elif movement_type in [
            StockMovementType.CIKIS,
            StockMovementType.SATIS,
            StockMovementType.URETIM_GIRIS,
            StockMovementType.SAYIM_EKSIK,
            StockMovementType.FIRE,
            StockMovementType.IADE_SATIS,
        ]:
            # ÇIKIŞ işlemleri - from_warehouse zorunlu
            if not from_warehouse_id:
                raise ValueError("Çıkış işlemleri için kaynak depo zorunludur!")

            # NEGATİF STOK KONTROLÜ
            available = self.get_available_quantity(item_id, from_warehouse_id)
            if not self.allow_negative_stock and available < quantity:
                item = self.session.query(Item).filter(Item.id == item_id).first()
                warehouse = (
                    self.session.query(Warehouse)
                    .filter(Warehouse.id == from_warehouse_id)
                    .first()
                )
                raise NegativeStockError(
                    item.code if item else str(item_id),
                    warehouse.name if warehouse else str(from_warehouse_id),
                    available,
                    quantity,
                )

            # ÇIKIŞ MALİYETİ = MEVCUT STOK MALİYETİ (düzeltilmiş)
            movement_cost = self.get_current_cost(item_id, from_warehouse_id)

        elif movement_type == StockMovementType.TRANSFER:
            # Transfer - her iki depo da zorunlu
            if not from_warehouse_id or not to_warehouse_id:
                raise ValueError("Transfer için kaynak ve hedef depo zorunludur!")

            # NEGATİF STOK KONTROLÜ
            available = self.get_available_quantity(item_id, from_warehouse_id)
            if not self.allow_negative_stock and available < quantity:
                item = self.session.query(Item).filter(Item.id == item_id).first()
                warehouse = (
                    self.session.query(Warehouse)
                    .filter(Warehouse.id == from_warehouse_id)
                    .first()
                )
                raise NegativeStockError(
                    item.code if item else str(item_id),
                    warehouse.name if warehouse else str(from_warehouse_id),
                    available,
                    quantity,
                )

            # Transfer maliyeti = kaynak depodaki maliyet
            movement_cost = self.get_current_cost(item_id, from_warehouse_id)
        else:
            movement_cost = unit_price

        try:
            # === TRANSACTION BAŞLANGICI ===

            # 1. Hareketi oluştur
            movement = StockMovement(
                item_id=item_id,
                movement_type=movement_type,
                quantity=quantity,
                unit_price=movement_cost,
                total_price=quantity * movement_cost,
                from_warehouse_id=from_warehouse_id,
                to_warehouse_id=to_warehouse_id,
                document_no=document_no,
                document_type=document_type,
                description=description,
                lot_number=lot_number,
                movement_date=movement_date or datetime.now(),
                # Dual-Unit alanları
                secondary_quantity=secondary_quantity,
                secondary_unit_id=secondary_unit_id,
                # Currency
                currency_id=currency_id,
                exchange_rate=exchange_rate,
            )
            self.session.add(movement)

            # 2. Bakiyeleri güncelle
            self._update_balances(
                item_id=item_id,
                quantity=quantity,
                unit_cost=movement_cost,
                from_warehouse_id=from_warehouse_id,
                to_warehouse_id=to_warehouse_id,
                movement_type=movement_type,
                # Dual-Unit bilgileri
                secondary_quantity=secondary_quantity,
                secondary_unit_id=secondary_unit_id,
            )

            # 3. Stok Kartı Fiyatını Güncelle
            if movement_type == StockMovementType.SATIN_ALMA:
                # Satınalma işleminde: Son Alış Fiyatı = İşlem Fiyatı
                item = self.session.query(Item).filter(Item.id == item_id).first()
                if item:
                    item.purchase_price = movement_cost
                    # Eğer işlemde para birimi varsa güncelle
                    if currency_id:
                        item.currency_id = currency_id
                    self.session.add(item)

            elif movement_type == StockMovementType.GIRIS:
                # Diğer girişlerde: Genel Ortalama Maliyet
                summary = self.get_stock_summary(item_id)
                avg_cost = summary.get("average_cost", Decimal(0))
                if avg_cost > 0:
                    item = self.session.query(Item).filter(Item.id == item_id).first()
                    if item:
                        item.purchase_price = avg_cost
                        # Girişlerde para birimi zorunlu değil, varsayılan TRY kontrolü
                        if not item.currency_id:
                            try_currency = (
                                self.session.query(Currency)
                                .filter(Currency.code == "TRY")
                                .first()
                            )
                            if try_currency:
                                item.currency_id = try_currency.id

                        self.session.add(item)

            # 4. Transaction'ı tamamla
            self.session.commit()

            return movement

        except Exception as e:
            # Hata durumunda geri al
            self.session.rollback()
            raise e

    def _update_balances(
        self,
        item_id: int,
        quantity: Decimal,
        unit_cost: Decimal,
        from_warehouse_id: int,
        to_warehouse_id: int,
        movement_type: StockMovementType,
        # === Dual-Unit ===
        secondary_quantity: Decimal = None,
        secondary_unit_id: int = None,
    ):
        """
        Stok bakiyelerini güncelle

        Moving Average (Ağırlıklı Ortalama) maliyet yöntemi kullanılır.
        Dual-Unit desteği ile ikincil birim miktarları da takip edilir.
        """

        # Çıkış yapılacak depodan düş
        if from_warehouse_id:
            from_balance = self.get_balance(item_id, from_warehouse_id)

            if from_balance:
                from_balance.quantity -= quantity
                # İkincil birim miktarını düş
                if secondary_quantity is not None:
                    curr = from_balance.secondary_quantity or Decimal(0)
                    from_balance.secondary_quantity = curr - secondary_quantity
                # Stok sıfır veya altına düştüyse maliyeti sıfırlama
                if from_balance.quantity <= 0:
                    from_balance.quantity = Decimal(0)
                    # Maliyet bilgisini koru, sıfırlama
            else:
                # Bakiye yoksa negatif bakiye oluştur
                from_balance = StockBalance(
                    item_id=item_id,
                    warehouse_id=from_warehouse_id,
                    quantity=-quantity,
                    unit_cost=unit_cost,
                    secondary_quantity=(
                        -secondary_quantity if secondary_quantity else None
                    ),
                    secondary_unit_id=secondary_unit_id,
                )
                self.session.add(from_balance)

        # Giriş yapılacak depoya ekle
        if to_warehouse_id:
            to_balance = self.get_balance(item_id, to_warehouse_id)

            if to_balance:
                # AĞIRLIKLI ORTALAMA MALİYET HESAPLAMASI (düzeltilmiş)
                old_quantity = to_balance.quantity
                old_cost = to_balance.unit_cost
                new_quantity = old_quantity + quantity

                if new_quantity > 0:
                    # Yeni ortalama maliyet
                    old_value = old_quantity * old_cost
                    new_value = quantity * unit_cost
                    to_balance.unit_cost = (old_value + new_value) / new_quantity

                to_balance.quantity = new_quantity

                # İkincil birim miktarını ekle
                if secondary_quantity is not None:
                    curr = to_balance.secondary_quantity or Decimal(0)
                    to_balance.secondary_quantity = curr + secondary_quantity
                    if secondary_unit_id:
                        to_balance.secondary_unit_id = secondary_unit_id
            else:
                # Yeni bakiye oluştur
                to_balance = StockBalance(
                    item_id=item_id,
                    warehouse_id=to_warehouse_id,
                    quantity=quantity,
                    unit_cost=unit_cost,
                    secondary_quantity=secondary_quantity,
                    secondary_unit_id=secondary_unit_id,
                )
                self.session.add(to_balance)

    def get_stock_summary(self, item_id: int) -> dict:
        """Stok özeti - tüm depolardaki bakiye"""
        balances = (
            self.session.query(StockBalance)
            .filter(StockBalance.item_id == item_id)
            .all()
        )

        total_qty = Decimal(0)
        total_value = Decimal(0)

        for b in balances:
            total_qty += b.quantity
            total_value += b.quantity * b.unit_cost

        avg_cost = total_value / total_qty if total_qty > 0 else Decimal(0)

        return {
            "total_quantity": total_qty,
            "total_value": total_value,
            "average_cost": avg_cost,
            "warehouse_details": [
                {
                    "warehouse_id": b.warehouse_id,
                    "quantity": b.quantity,
                    "unit_cost": b.unit_cost,
                    "value": b.quantity * b.unit_cost,
                }
                for b in balances
            ],
        }

    def rebuild_balance(self, item_id: int, warehouse_id: int) -> StockBalance:
        """
        Bakiyeyi hareketlerden yeniden hesapla (reconcile)
        Bakiye tutarsızlığı şüphesi varsa kullanılır.
        """
        # Tüm hareketleri al
        movements = (
            self.session.query(StockMovement)
            .filter(
                StockMovement.item_id == item_id,
                (StockMovement.from_warehouse_id == warehouse_id)
                | (StockMovement.to_warehouse_id == warehouse_id),
            )
            .order_by(StockMovement.movement_date)
            .all()
        )

        quantity = Decimal(0)
        total_value = Decimal(0)

        for m in movements:
            if m.to_warehouse_id == warehouse_id:
                # Giriş
                quantity += m.quantity
                total_value += m.quantity * m.unit_price
            if m.from_warehouse_id == warehouse_id:
                # Çıkış
                quantity -= m.quantity
                total_value -= m.quantity * m.unit_price

        # Bakiyeyi güncelle veya oluştur
        balance = self.get_balance(item_id, warehouse_id)
        if not balance:
            balance = StockBalance(
                item_id=item_id,
                warehouse_id=warehouse_id,
            )
            self.session.add(balance)

        balance.quantity = max(Decimal(0), quantity)
        balance.unit_cost = total_value / quantity if quantity > 0 else Decimal(0)

        self.session.commit()
        return balance

    def reserve_stock(
        self,
        item_id: int,
        warehouse_id: int,
        quantity: Decimal,
        reference_type: str = None,
        reference_id: int = None,
    ) -> bool:
        """
        Stok rezerve et (fiziksel çıkış yapmadan)

        Args:
            item_id: Stok kartı ID
            warehouse_id: Depo ID
            quantity: Rezerve edilecek miktar
            reference_type: Referans tipi (work_order, sales_order, etc.)
            reference_id: Referans ID

        Returns:
            bool: Başarılı ise True

        Raises:
            NegativeStockError: Yetersiz stok varsa
        """
        quantity = Decimal(str(quantity))

        if quantity <= 0:
            raise ValueError("Rezerve miktarı sıfırdan büyük olmalıdır!")

        # Kullanılabilir miktarı kontrol et
        available = self.get_available_quantity(item_id, warehouse_id)
        if available < quantity:
            item = self.session.query(Item).filter(Item.id == item_id).first()
            warehouse = (
                self.session.query(Warehouse)
                .filter(Warehouse.id == warehouse_id)
                .first()
            )
            raise NegativeStockError(
                item.code if item else str(item_id),
                warehouse.name if warehouse else str(warehouse_id),
                available,
                quantity,
            )

        # Bakiyeyi getir veya oluştur
        balance = self.get_balance(item_id, warehouse_id)
        if not balance:
            balance = StockBalance(
                item_id=item_id,
                warehouse_id=warehouse_id,
                quantity=Decimal(0),
                reserved_quantity=Decimal(0),
            )
            self.session.add(balance)

        # Rezerve miktarı artır
        if balance.reserved_quantity is None:
            balance.reserved_quantity = Decimal(0)
        balance.reserved_quantity += quantity

        self.session.commit()
        return True

    def release_reservation(
        self, item_id: int, warehouse_id: int, quantity: Decimal
    ) -> bool:
        """
        Rezervasyonu serbest bırak

        Args:
            item_id: Stok kartı ID
            warehouse_id: Depo ID
            quantity: Serbest bırakılacak miktar

        Returns:
            bool: Başarılı ise True
        """
        quantity = Decimal(str(quantity))

        if quantity <= 0:
            raise ValueError("Serbest bırakılacak miktar sıfırdan büyük olmalıdır!")

        balance = self.get_balance(item_id, warehouse_id)
        if not balance:
            return False

        # Rezerve miktarı azalt
        if balance.reserved_quantity is None:
            balance.reserved_quantity = Decimal(0)

        balance.reserved_quantity = max(
            Decimal(0), balance.reserved_quantity - quantity
        )

        self.session.commit()
        return True
