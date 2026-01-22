"""
Akıllı İş - Sevkiyat Modülü Servisleri
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict
from sqlalchemy import desc, and_, or_
from sqlalchemy.orm import joinedload

from database.base import get_session
from database.models.shipping import (
    Vehicle,
    VehicleStatus,
    VehicleType,
    Driver,
    DriverStatus,
    Shipment,
    ShipmentStatus,
    ShipmentItem,
    ShipmentLoad,
)
from database.models.sales import DeliveryNote, DeliveryNoteStatus
from database.models.inventory import StockMovementType
from modules.inventory.services.base import StockMovementService


class VehicleService:
    """Araç yönetimi servisi"""

    def __init__(self):
        self.session = get_session()

    def get_all(
        self,
        status: VehicleStatus = None,
        vehicle_type: VehicleType = None,
        active_only: bool = True,
    ) -> List[Vehicle]:
        """Tüm araçları getir"""
        query = self.session.query(Vehicle)
        if active_only:
            query = query.filter(Vehicle.status != VehicleStatus.PASIF)
        if status:
            query = query.filter(Vehicle.status == status)
        if vehicle_type:
            query = query.filter(Vehicle.vehicle_type == vehicle_type)
        return query.order_by(Vehicle.plate_no).all()

    def get_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        """ID ile araç getir"""
        return self.session.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    def get_by_plate(self, plate_no: str) -> Optional[Vehicle]:
        """Plaka ile araç getir"""
        return self.session.query(Vehicle).filter(Vehicle.plate_no == plate_no).first()

    def get_available(self) -> List[Vehicle]:
        """Uygun araçları getir (aktif durumda)"""
        return (
            self.session.query(Vehicle)
            .filter(Vehicle.status == VehicleStatus.AKTIF)
            .order_by(Vehicle.plate_no)
            .all()
        )

    def create(self, **kwargs) -> Vehicle:
        """Yeni araç oluştur"""
        vehicle = Vehicle(**kwargs)
        self.session.add(vehicle)
        self.session.commit()
        return vehicle

    def update(self, vehicle_id: int, **kwargs) -> Optional[Vehicle]:
        """Araç güncelle"""
        vehicle = self.get_by_id(vehicle_id)
        if not vehicle:
            return None

        for key, value in kwargs.items():
            if hasattr(vehicle, key):
                setattr(vehicle, key, value)

        self.session.commit()
        return vehicle

    def delete(self, vehicle_id: int) -> bool:
        """Araç sil"""
        vehicle = self.get_by_id(vehicle_id)
        if not vehicle:
            return False

        # Aktif sevkiyatları kontrol et
        active_shipments = (
            self.session.query(Shipment)
            .filter(
                Shipment.vehicle_id == vehicle_id,
                Shipment.status.in_(
                    [
                        ShipmentStatus.PLANLANDI,
                        ShipmentStatus.YUKLENIYOR,
                        ShipmentStatus.YOLDA,
                    ]
                ),
            )
            .count()
        )
        if active_shipments > 0:
            raise ValueError(
                "Bu araca ait aktif sevkiyatlar var. Önce sevkiyatları tamamlayın."
            )

        self.session.delete(vehicle)
        self.session.commit()
        return True

    def get_stats(self) -> Dict:
        """Araç istatistikleri"""
        total = self.session.query(Vehicle).count()
        aktif = (
            self.session.query(Vehicle)
            .filter(Vehicle.status == VehicleStatus.AKTIF)
            .count()
        )
        bakimda = (
            self.session.query(Vehicle)
            .filter(Vehicle.status == VehicleStatus.BAKIMDA)
            .count()
        )
        return {
            "total": total,
            "aktif": aktif,
            "bakimda": bakimda,
            "pasif": total - aktif - bakimda,
        }


class DriverService:
    """Sürücü yönetimi servisi"""

    def __init__(self):
        self.session = get_session()

    def get_all(
        self, status: DriverStatus = None, active_only: bool = True
    ) -> List[Driver]:
        """Tüm sürücüleri getir"""
        query = self.session.query(Driver).options(joinedload(Driver.default_vehicle))
        if active_only:
            query = query.filter(Driver.status != DriverStatus.PASIF)
        if status:
            query = query.filter(Driver.status == status)
        return query.order_by(Driver.name).all()

    def get_by_id(self, driver_id: int) -> Optional[Driver]:
        """ID ile sürücü getir"""
        return (
            self.session.query(Driver)
            .options(joinedload(Driver.default_vehicle))
            .filter(Driver.id == driver_id)
            .first()
        )

    def get_by_code(self, code: str) -> Optional[Driver]:
        """Kod ile sürücü getir"""
        return self.session.query(Driver).filter(Driver.code == code).first()

    def get_available(self) -> List[Driver]:
        """Müsait sürücüleri getir"""
        return (
            self.session.query(Driver)
            .options(joinedload(Driver.default_vehicle))
            .filter(Driver.status == DriverStatus.MUSAIT)
            .order_by(Driver.name)
            .all()
        )

    def generate_code(self) -> str:
        """Yeni sürücü kodu oluştur"""
        last = (
            self.session.query(Driver)
            .filter(Driver.code.like("SRC%"))
            .order_by(desc(Driver.code))
            .first()
        )
        if last and last.code.startswith("SRC"):
            try:
                num = int(last.code[3:]) + 1
            except ValueError:
                num = 1
        else:
            num = 1
        return f"SRC{num:04d}"

    def create(self, **kwargs) -> Driver:
        """Yeni sürücü oluştur"""
        if "code" not in kwargs or not kwargs["code"]:
            kwargs["code"] = self.generate_code()
        driver = Driver(**kwargs)
        self.session.add(driver)
        self.session.commit()
        return driver

    def update(self, driver_id: int, **kwargs) -> Optional[Driver]:
        """Sürücü güncelle"""
        driver = self.get_by_id(driver_id)
        if not driver:
            return None

        for key, value in kwargs.items():
            if hasattr(driver, key):
                setattr(driver, key, value)

        self.session.commit()
        return driver

    def delete(self, driver_id: int) -> bool:
        """Sürücü sil"""
        driver = self.get_by_id(driver_id)
        if not driver:
            return False

        # Aktif sevkiyatları kontrol et
        active_shipments = (
            self.session.query(Shipment)
            .filter(
                Shipment.driver_id == driver_id,
                Shipment.status.in_(
                    [
                        ShipmentStatus.PLANLANDI,
                        ShipmentStatus.YUKLENIYOR,
                        ShipmentStatus.YOLDA,
                    ]
                ),
            )
            .count()
        )
        if active_shipments > 0:
            raise ValueError(
                "Bu sürücüye ait aktif sevkiyatlar var. Önce sevkiyatları tamamlayın."
            )

        self.session.delete(driver)
        self.session.commit()
        return True

    def get_stats(self) -> Dict:
        """Sürücü istatistikleri"""
        total = (
            self.session.query(Driver)
            .filter(Driver.status != DriverStatus.PASIF)
            .count()
        )
        musait = (
            self.session.query(Driver)
            .filter(Driver.status == DriverStatus.MUSAIT)
            .count()
        )
        gorevde = (
            self.session.query(Driver)
            .filter(Driver.status == DriverStatus.GOREVDE)
            .count()
        )

        # Süresi dolacak belgeler
        from datetime import timedelta

        threshold = date.today() + timedelta(days=30)
        expiring = (
            self.session.query(Driver)
            .filter(
                Driver.status != DriverStatus.PASIF,
                or_(
                    and_(
                        Driver.license_expiry != None,
                        Driver.license_expiry <= threshold,
                    ),
                    and_(Driver.src_expiry != None, Driver.src_expiry <= threshold),
                ),
            )
            .count()
        )

        return {
            "total": total,
            "musait": musait,
            "gorevde": gorevde,
            "expiring": expiring,
        }


class ShipmentService:
    """Sevkiyat yönetimi servisi"""

    def __init__(self):
        self.session = get_session()
        self.stock_service = StockMovementService()

    def get_available_delivery_notes(self) -> List[DeliveryNote]:
        """Henüz bir sevkiyata atanmamış ve sevke hazır irsaliyeleri getir"""
        # Burada DeliveryNoteStatus.DRAFT dışındakileri veya özel bir durumu filtreleyebiliriz
        # Şimdilik bir sevkiyata (ShipmentItem) bağlanmamış olanları çekelim
        sq = self.session.query(ShipmentItem.delivery_note_id).subquery()

        return (
            self.session.query(DeliveryNote)
            .outerjoin(sq, DeliveryNote.id == sq.c.delivery_note_id)
            .filter(sq.c.delivery_note_id == None)
            .filter(DeliveryNote.status != DeliveryNoteStatus.CANCELLED)
            .options(joinedload(DeliveryNote.customer), joinedload(DeliveryNote.items))
            .order_by(DeliveryNote.delivery_date)
            .all()
        )

    def get_all(
        self,
        status: ShipmentStatus = None,
        start_date: date = None,
        end_date: date = None,
        vehicle_id: int = None,
        driver_id: int = None,
    ) -> List[Shipment]:
        """Tüm sevkiyatları getir"""
        query = self.session.query(Shipment).options(
            joinedload(Shipment.vehicle),
            joinedload(Shipment.driver),
        )
        if status:
            query = query.filter(Shipment.status == status)
        if start_date:
            query = query.filter(Shipment.shipment_date >= start_date)
        if end_date:
            query = query.filter(Shipment.shipment_date <= end_date)
        if vehicle_id:
            query = query.filter(Shipment.vehicle_id == vehicle_id)
        if driver_id:
            query = query.filter(Shipment.driver_id == driver_id)
        return query.order_by(desc(Shipment.shipment_date), desc(Shipment.id)).all()

    def get_by_id(self, shipment_id: int) -> Optional[Shipment]:
        """ID ile sevkiyat getir"""
        return (
            self.session.query(Shipment)
            .options(
                joinedload(Shipment.vehicle),
                joinedload(Shipment.driver),
                joinedload(Shipment.items)
                .joinedload(ShipmentItem.delivery_note)
                .joinedload(DeliveryNote.items),
                joinedload(Shipment.loads).joinedload(ShipmentLoad.transport_unit),
            )
            .filter(Shipment.id == shipment_id)
            .first()
        )

    def get_by_no(self, shipment_no: str) -> Optional[Shipment]:
        """Sevkiyat numarası ile getir"""
        return (
            self.session.query(Shipment)
            .filter(Shipment.shipment_no == shipment_no)
            .first()
        )

    def generate_shipment_no(self) -> str:
        """Yeni sevkiyat numarası oluştur"""
        today = date.today()
        prefix = f"SVK{today.strftime('%Y%m')}"
        last = (
            self.session.query(Shipment)
            .filter(Shipment.shipment_no.like(f"{prefix}%"))
            .order_by(desc(Shipment.shipment_no))
            .first()
        )
        if last:
            try:
                num = int(last.shipment_no[-4:]) + 1
            except ValueError:
                num = 1
        else:
            num = 1
        return f"{prefix}{num:04d}"

    def _validate_capacity(
        self,
        vehicle_id: int,
        total_weight: float,
        total_volume: float,
        total_pallets: int,
    ):
        """Araç kapasite kontrolü"""
        # Eğer araç seçilmediyse veya ağırlık/hacim 0 ise kontrol etme (opsiyonel)
        if not vehicle_id:
            return

        vehicle = self.session.query(Vehicle).get(vehicle_id)
        if not vehicle:
            return

        errors = []
        if vehicle.capacity_kg and total_weight > vehicle.capacity_kg:
            errors.append(
                f"Ağırlık sınırı aşıldı! (Max: {vehicle.capacity_kg} kg, Mevcut: {total_weight} kg)"
            )

        if vehicle.capacity_m3 and total_volume > vehicle.capacity_m3:
            errors.append(
                f"Hacim sınırı aşıldı! (Max: {vehicle.capacity_m3} m³, Mevcut: {total_volume} m³)"
            )

        if vehicle.pallet_capacity and total_pallets > vehicle.pallet_capacity:
            errors.append(
                f"Palet sınırı aşıldı! (Max: {vehicle.pallet_capacity}, Mevcut: {total_pallets})"
            )

        if errors:
            raise ValueError("\n".join(errors))

    def create(
        self,
        items: List[Dict] = None,
        loads: List[Dict] = None,
        delivery_note_ids: List[int] = None,
        **kwargs,
    ) -> Shipment:
        """Yeni sevkiyat oluştur"""
        if "shipment_no" not in kwargs or not kwargs["shipment_no"]:
            kwargs["shipment_no"] = self.generate_shipment_no()

        # Kapasite kontrolü (formdan gelen total değerler ile)
        self._validate_capacity(
            kwargs.get("vehicle_id"),
            float(kwargs.get("total_weight_kg", 0)),
            float(kwargs.get("total_volume_m3", 0)),
            int(kwargs.get("total_pallets", 0)),
        )

        shipment = Shipment(**kwargs)
        self.session.add(shipment)
        self.session.flush()

        # İrsaliyeleri ekle (ShipmentItem olarak)
        if delivery_note_ids:
            for dn_id in delivery_note_ids:
                # İrsaliye kontrolü
                dn = self.session.query(DeliveryNote).get(dn_id)
                if dn:
                    # İrsaliye kalemini oluştur
                    item = ShipmentItem(shipment_id=shipment.id, delivery_note_id=dn.id)
                    self.session.add(item)
                    # İrsaliye durumunu güncelle (Örn: SHIPPED yapılabilir veya shipment status değişince yapılır)

        # Eski tip items (manuel kalem ekleme varsa, opsiyonel)
        if items:
            for item_data in items:
                item = ShipmentItem(shipment_id=shipment.id, **item_data)
                self.session.add(item)

        # Yükleri ekle
        if loads:
            for load_data in loads:
                load = ShipmentLoad(shipment_id=shipment.id, **load_data)
                self.session.add(load)

        self.session.commit()
        return shipment

    def update(
        self,
        shipment_id: int,
        items: List[Dict] = None,
        loads: List[Dict] = None,
        delivery_note_ids: List[int] = None,
        **kwargs,
    ) -> Optional[Shipment]:
        """Sevkiyat güncelle"""
        shipment = self.get_by_id(shipment_id)
        if not shipment:
            return None

        # Kapasite kontrolü
        # kwargs içinde yeni değerler varsa onları kullan, yoksa mevcut değerleri kullan
        new_vid = kwargs.get("vehicle_id", shipment.vehicle_id)
        new_weight = float(kwargs.get("total_weight_kg", shipment.total_weight_kg))
        new_volume = float(kwargs.get("total_volume_m3", shipment.total_volume_m3))
        new_pallets = int(kwargs.get("total_pallets", shipment.total_pallets))

        self._validate_capacity(new_vid, new_weight, new_volume, new_pallets)

        for key, value in kwargs.items():
            if hasattr(shipment, key):
                setattr(shipment, key, value)

        # İrsaliyeleri güncelle
        if delivery_note_ids is not None:
            # Mevcutları temizz
            self.session.query(ShipmentItem).filter(
                ShipmentItem.shipment_id == shipment.id
            ).delete()

            # Yenileri ekle
            for dn_id in delivery_note_ids:
                dn = self.session.query(DeliveryNote).get(dn_id)
                if dn:
                    item = ShipmentItem(shipment_id=shipment.id, delivery_note_id=dn.id)
                    self.session.add(item)

        # Manuel kalemleri güncelle (Eski yapı desteği)
        if items is not None:
            # delivery_note_ids zaten temizlediği için burada sadece ekleme yapabiliriz
            # veya karışık kullanım varsa dikkatli olunmalı. Şimdilik irsaliye bazlı gideceğiz.
            pass

        # Yükleri güncelle
        if loads is not None:
            for load in shipment.loads:
                self.session.delete(load)
            for load_data in loads:
                load = ShipmentLoad(shipment_id=shipment.id, **load_data)
                self.session.add(load)

        self.session.commit()
        return shipment

    def update_status(
        self, shipment_id: int, status: ShipmentStatus
    ) -> Optional[Shipment]:
        """Sevkiyat durumunu güncelle"""
        shipment = self.get_by_id(shipment_id)
        if not shipment:
            return None

        old_status = shipment.status
        shipment.status = status

        # Çıkış zamanını kaydet ve Stoktan Düş
        if status == ShipmentStatus.YOLDA and old_status != ShipmentStatus.YOLDA:
            if not shipment.departure_time:
                shipment.departure_time = datetime.now()

            # Sürücüyü görevde yap
            if shipment.driver:
                shipment.driver.status = DriverStatus.GOREVDE

            # --- STOK HAREKETLERİ ---
            # İlişkili irsaliyelerdeki ürünleri stoktan Transit veya Müşteri deposuna sevk et
            # Buradaki logic: Warehouse (Kaynak) -> Customer (Hedef)
            # Eğer bir 'Transit' depo mantığı varsa oraya da alınabilir.
            # Şimdilik TransactionType.TRANSFER kullanarak stoktan düşelim.

            for s_item in shipment.items:
                dn = s_item.delivery_note
                if not dn or not dn.items:
                    continue

                # İrsaliye durumunu güncelle
                dn.status = DeliveryNoteStatus.SHIPPED

                for dn_item in dn.items:
                    # Kaynak depo
                    source_wh_id = dn.source_warehouse_id

                    self.stock_service.create_movement(
                        item_id=dn_item.item_id,
                        from_warehouse_id=source_wh_id,
                        movement_type=StockMovementType.SATIS,
                        quantity=float(dn_item.quantity),
                        document_type="shipment",
                        document_no=shipment.shipment_no,
                        description=f"Sevkiyat: {shipment.shipment_no}, İrsaliye: {dn.delivery_no}",
                        # Hedef depo olarak müşterinin sanal deposu veya shipment alanı yoksa
                        # sadece çıkış yapılıyor olabilir.
                        # Eğer StockMovementType.SALES kullanırsak stoktan direkt düşer.
                    )

        # Dönüş zamanını kaydet
        if (
            status == ShipmentStatus.TESLIM_EDILDI
            and shipment.status != ShipmentStatus.TESLIM_EDILDI
        ):
            if not shipment.return_time:
                shipment.return_time = datetime.now()

            # Sürücüyü müsait yap
            if shipment.driver:
                shipment.driver.status = DriverStatus.MUSAIT

            # İrsaliyeleri Teslim Edildi yap
            for s_item in shipment.items:
                if s_item.delivery_note:
                    s_item.delivery_note.status = DeliveryNoteStatus.DELIVERED
                    s_item.delivery_note.actual_delivery_date = date.today()

        self.session.commit()
        return shipment

    def delete(self, shipment_id: int) -> bool:
        """Sevkiyat sil"""
        shipment = self.get_by_id(shipment_id)
        if not shipment:
            return False

        if shipment.status in [ShipmentStatus.YOLDA, ShipmentStatus.TESLIM_EDILDI]:
            raise ValueError("Yolda veya teslim edilmiş sevkiyatlar silinemez.")

        self.session.delete(shipment)
        self.session.commit()
        return True

    def get_stats(self, start_date: date = None, end_date: date = None) -> Dict:
        """Sevkiyat istatistikleri"""
        query = self.session.query(Shipment)
        if start_date:
            query = query.filter(Shipment.shipment_date >= start_date)
        if end_date:
            query = query.filter(Shipment.shipment_date <= end_date)

        total = query.count()
        planlanan = query.filter(Shipment.status == ShipmentStatus.PLANLANDI).count()
        yolda = query.filter(Shipment.status == ShipmentStatus.YOLDA).count()
        teslim = query.filter(Shipment.status == ShipmentStatus.TESLIM_EDILDI).count()

        return {
            "total": total,
            "planlanan": planlanan,
            "yolda": yolda,
            "teslim": teslim,
        }

    def get_today_shipments(self) -> List[Shipment]:
        """Bugünkü sevkiyatları getir"""
        return self.get_all(start_date=date.today(), end_date=date.today())
