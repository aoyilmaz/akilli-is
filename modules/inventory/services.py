"""
Akıllı İş - Stok Modülü Servisleri
"""

from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from database import get_session
from database.models import (
    Item, ItemCategory, Unit, Warehouse, 
    StockBalance, StockMovement,
    ItemType, StockMovementType
)


class ItemService:
    """Stok kartı servisi"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
    
    def get_all(self, active_only: bool = True) -> List[Item]:
        """Tüm stok kartlarını getir"""
        query = self.session.query(Item)
        if active_only:
            query = query.filter(Item.is_active == True)
        return query.order_by(Item.code).all()
    
    def get_by_id(self, item_id: int) -> Optional[Item]:
        """ID ile stok kartı getir"""
        return self.session.query(Item).filter(Item.id == item_id).first()
    
    def get_by_code(self, code: str) -> Optional[Item]:
        """Kod ile stok kartı getir"""
        return self.session.query(Item).filter(Item.code == code).first()
    
    def search(self, keyword: str, item_type: Optional[ItemType] = None, 
               category_id: Optional[int] = None) -> List[Item]:
        """Stok kartı ara"""
        query = self.session.query(Item).filter(Item.is_active == True)
        
        if keyword:
            search = f"%{keyword}%"
            query = query.filter(
                or_(
                    Item.code.ilike(search),
                    Item.name.ilike(search),
                    Item.barcode.ilike(search)
                )
            )
        
        if item_type:
            query = query.filter(Item.item_type == item_type)
            
        if category_id:
            query = query.filter(Item.category_id == category_id)
            
        return query.order_by(Item.code).all()
    
    def create(self, **kwargs) -> Item:
        """Yeni stok kartı oluştur"""
        item = Item(**kwargs)
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item
    
    def update(self, item_id: int, **kwargs) -> Optional[Item]:
        """Stok kartı güncelle"""
        item = self.get_by_id(item_id)
        if item:
            for key, value in kwargs.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            self.session.commit()
            self.session.refresh(item)
        return item
    
    def delete(self, item_id: int, soft: bool = True) -> bool:
        """Stok kartı sil (varsayılan: soft delete)"""
        item = self.get_by_id(item_id)
        if item:
            if soft:
                item.is_active = False
            else:
                self.session.delete(item)
            self.session.commit()
            return True
        return False
    
    def get_low_stock_items(self) -> List[Item]:
        """Minimum stok altındaki ürünleri getir"""
        items = self.session.query(Item).filter(
            Item.is_active == True,
            Item.min_stock > 0
        ).all()
        
        return [item for item in items if item.total_stock < item.min_stock]
    
    def get_stock_value(self) -> Decimal:
        """Toplam stok değerini hesapla"""
        items = self.get_all()
        total = Decimal(0)
        for item in items:
            total += item.total_stock * (item.purchase_price or 0)
        return total


class CategoryService:
    """Kategori servisi"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
    
    def get_all(self) -> List[ItemCategory]:
        """Tüm kategorileri getir"""
        return self.session.query(ItemCategory).filter(
            ItemCategory.is_active == True
        ).order_by(ItemCategory.name).all()
    
    def get_root_categories(self) -> List[ItemCategory]:
        """Ana kategorileri getir"""
        return self.session.query(ItemCategory).filter(
            ItemCategory.is_active == True,
            ItemCategory.parent_id == None
        ).order_by(ItemCategory.name).all()
    
    def create(self, **kwargs) -> ItemCategory:
        """Yeni kategori oluştur"""
        category = ItemCategory(**kwargs)
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return category


class WarehouseService:
    """Depo servisi"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
    
    def get_all(self) -> List[Warehouse]:
        """Tüm depoları getir"""
        return self.session.query(Warehouse).filter(
            Warehouse.is_active == True
        ).order_by(Warehouse.name).all()
    
    def get_default(self) -> Optional[Warehouse]:
        """Varsayılan depoyu getir"""
        return self.session.query(Warehouse).filter(
            Warehouse.is_active == True,
            Warehouse.is_default == True
        ).first()
    
    def create(self, **kwargs) -> Warehouse:
        """Yeni depo oluştur"""
        warehouse = Warehouse(**kwargs)
        self.session.add(warehouse)
        self.session.commit()
        self.session.refresh(warehouse)
        return warehouse


class UnitService:
    """Birim servisi"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
    
    def get_all(self) -> List[Unit]:
        """Tüm birimleri getir"""
        return self.session.query(Unit).filter(
            Unit.is_active == True
        ).order_by(Unit.name).all()
    
    def create(self, **kwargs) -> Unit:
        """Yeni birim oluştur"""
        unit = Unit(**kwargs)
        self.session.add(unit)
        self.session.commit()
        self.session.refresh(unit)
        return unit
    
    def create_defaults(self):
        """Varsayılan birimleri oluştur"""
        defaults = [
            ("ADET", "Adet"),
            ("KG", "Kilogram"),
            ("GR", "Gram"),
            ("LT", "Litre"),
            ("ML", "Mililitre"),
            ("MT", "Metre"),
            ("CM", "Santimetre"),
            ("M2", "Metrekare"),
            ("M3", "Metreküp"),
            ("RULO", "Rulo"),
            ("PAKET", "Paket"),
            ("KUTU", "Kutu"),
            ("PALET", "Palet"),
        ]
        
        for code, name in defaults:
            existing = self.session.query(Unit).filter(Unit.code == code).first()
            if not existing:
                self.create(code=code, name=name)


class StockMovementService:
    """Stok hareket servisi"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
    
    def create_movement(
        self,
        item_id: int,
        movement_type: StockMovementType,
        quantity: Decimal,
        to_warehouse_id: Optional[int] = None,
        from_warehouse_id: Optional[int] = None,
        unit_price: Decimal = Decimal(0),
        document_no: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> StockMovement:
        """Stok hareketi oluştur ve bakiyeyi güncelle"""
        
        # Hareket oluştur
        movement = StockMovement(
            item_id=item_id,
            movement_type=movement_type,
            quantity=quantity,
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            unit_price=unit_price,
            total_price=quantity * unit_price,
            document_no=document_no,
            description=description,
            **kwargs
        )
        self.session.add(movement)
        
        # Bakiyeleri güncelle
        if movement_type == StockMovementType.GIRIS:
            self._update_balance(item_id, to_warehouse_id, quantity)
            
        elif movement_type == StockMovementType.CIKIS:
            self._update_balance(item_id, from_warehouse_id, -quantity)
            
        elif movement_type == StockMovementType.TRANSFER:
            self._update_balance(item_id, from_warehouse_id, -quantity)
            self._update_balance(item_id, to_warehouse_id, quantity)
        
        self.session.commit()
        self.session.refresh(movement)
        return movement
    
    def _update_balance(self, item_id: int, warehouse_id: int, quantity: Decimal):
        """Stok bakiyesini güncelle"""
        balance = self.session.query(StockBalance).filter(
            StockBalance.item_id == item_id,
            StockBalance.warehouse_id == warehouse_id
        ).first()
        
        if balance:
            balance.quantity += quantity
        else:
            balance = StockBalance(
                item_id=item_id,
                warehouse_id=warehouse_id,
                quantity=quantity
            )
            self.session.add(balance)
    
    def get_movements(
        self,
        item_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
        movement_type: Optional[StockMovementType] = None,
        limit: int = 100
    ) -> List[StockMovement]:
        """Stok hareketlerini getir"""
        query = self.session.query(StockMovement)
        
        if item_id:
            query = query.filter(StockMovement.item_id == item_id)
        
        if warehouse_id:
            query = query.filter(
                or_(
                    StockMovement.from_warehouse_id == warehouse_id,
                    StockMovement.to_warehouse_id == warehouse_id
                )
            )
        
        if movement_type:
            query = query.filter(StockMovement.movement_type == movement_type)
        
        return query.order_by(StockMovement.movement_date.desc()).limit(limit).all()
