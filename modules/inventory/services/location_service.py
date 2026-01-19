"""
Akıllı İş - Lokasyon Yönetim Servisi
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
import uuid
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database.base import get_session
from database.models.inventory import (
    WarehouseLocation,
    LocationType,
    Warehouse,
    StockBalance,
)


class LocationService:
    """Depo lokasyon işlemleri servisi"""

    @staticmethod
    def get_all(
        warehouse_id: Optional[int] = None,
        location_type: Optional[LocationType] = None,
        is_active: Optional[bool] = True,
        zone: Optional[str] = None,
    ) -> List[WarehouseLocation]:
        """Lokasyonları listele"""
        session = get_session()
        try:
            query = session.query(WarehouseLocation)

            if warehouse_id:
                query = query.filter(WarehouseLocation.warehouse_id == warehouse_id)

            if location_type:
                query = query.filter(WarehouseLocation.location_type == location_type)

            if is_active is not None:
                query = query.filter(WarehouseLocation.is_active == is_active)

            if zone:
                query = query.filter(WarehouseLocation.zone == zone)

            return query.order_by(
                WarehouseLocation.aisle,
                WarehouseLocation.rack,
                WarehouseLocation.shelf,
                WarehouseLocation.bin,
            ).all()
        finally:
            session.close()

    @staticmethod
    def get_by_id(location_id: int) -> Optional[WarehouseLocation]:
        """ID ile lokasyon getir"""
        session = get_session()
        try:
            return session.query(WarehouseLocation).get(location_id)
        finally:
            session.close()

    @staticmethod
    def get_by_barcode(barcode: str) -> Optional[WarehouseLocation]:
        """Barkod ile lokasyon getir"""
        session = get_session()
        try:
            return (
                session.query(WarehouseLocation)
                .filter(WarehouseLocation.barcode == barcode)
                .first()
            )
        finally:
            session.close()

    @staticmethod
    def get_by_code(warehouse_id: int, code: str) -> Optional[WarehouseLocation]:
        """Kod ile lokasyon getir"""
        session = get_session()
        try:
            return (
                session.query(WarehouseLocation)
                .filter(
                    WarehouseLocation.warehouse_id == warehouse_id,
                    WarehouseLocation.code == code,
                )
                .first()
            )
        finally:
            session.close()

    @staticmethod
    def create(data: Dict[str, Any]) -> WarehouseLocation:
        """Yeni lokasyon oluştur"""
        session = get_session()
        try:
            # Barkod otomatik oluştur
            if not data.get("barcode"):
                data["barcode"] = LocationService._generate_barcode()

            location = WarehouseLocation(**data)
            session.add(location)
            session.commit()
            session.refresh(location)
            return location
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def update(location_id: int, data: Dict[str, Any]) -> Optional[WarehouseLocation]:
        """Lokasyon güncelle"""
        session = get_session()
        try:
            location = session.query(WarehouseLocation).get(location_id)
            if not location:
                return None

            for key, value in data.items():
                if hasattr(location, key):
                    setattr(location, key, value)

            session.commit()
            session.refresh(location)
            return location
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def delete(location_id: int) -> bool:
        """Lokasyon sil (stok varsa silinemez)"""
        session = get_session()
        try:
            location = session.query(WarehouseLocation).get(location_id)
            if not location:
                return False

            # Stok kontrolü
            has_stock = (
                session.query(StockBalance)
                .filter(
                    StockBalance.location_id == location_id,
                    StockBalance.quantity > 0,
                )
                .first()
            )

            if has_stock:
                raise ValueError("Bu lokasyonda stok bulunuyor, silinemez!")

            session.delete(location)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def create_bulk(
        warehouse_id: int,
        aisle_start: str,
        aisle_end: str,
        rack_start: int,
        rack_end: int,
        shelf_start: int,
        shelf_end: int,
        zone: Optional[str] = None,
        location_type: LocationType = LocationType.NORMAL,
    ) -> List[WarehouseLocation]:
        """
        Toplu lokasyon oluşturma

        Örnek: A-Z koridorları, 1-10 raflar, 1-5 katlar
        """
        session = get_session()
        try:
            locations = []

            # Koridor harflerini oluştur (A-Z veya AA-ZZ)
            aisles = LocationService._generate_aisle_codes(aisle_start, aisle_end)

            for aisle in aisles:
                for rack in range(rack_start, rack_end + 1):
                    for shelf in range(shelf_start, shelf_end + 1):
                        code = f"{aisle}-{rack:02d}-{shelf:02d}"
                        name = f"Koridor {aisle}, Raf {rack}, Kat {shelf}"

                        # Var mı kontrol
                        existing = (
                            session.query(WarehouseLocation)
                            .filter(
                                WarehouseLocation.warehouse_id == warehouse_id,
                                WarehouseLocation.code == code,
                            )
                            .first()
                        )

                        if not existing:
                            location = WarehouseLocation(
                                warehouse_id=warehouse_id,
                                code=code,
                                name=name,
                                aisle=aisle,
                                rack=str(rack),
                                shelf=str(shelf),
                                location_type=location_type,
                                zone=zone,
                                barcode=LocationService._generate_barcode(),
                                is_active=True,
                            )
                            session.add(location)
                            locations.append(location)

            session.commit()
            return locations
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def get_available_locations(
        warehouse_id: int,
        item_id: Optional[int] = None,
        location_type: Optional[LocationType] = None,
    ) -> List[Dict[str, Any]]:
        """Boş veya uygun lokasyonları getir (put-away için)"""
        session = get_session()
        try:
            query = session.query(WarehouseLocation).filter(
                WarehouseLocation.warehouse_id == warehouse_id,
                WarehouseLocation.is_active == True,
            )

            if location_type:
                query = query.filter(WarehouseLocation.location_type == location_type)

            locations = query.order_by(
                WarehouseLocation.priority,
                WarehouseLocation.aisle,
                WarehouseLocation.rack,
                WarehouseLocation.shelf,
            ).all()

            result = []
            for loc in locations:
                # Bu lokasyondaki toplam stok
                total_qty = (
                    session.query(StockBalance)
                    .filter(
                        StockBalance.location_id == loc.id,
                    )
                    .count()
                )

                # Kapasite kontrolü
                available = True
                if loc.max_items and total_qty >= loc.max_items:
                    available = False

                result.append(
                    {
                        "id": loc.id,
                        "code": loc.code,
                        "full_code": loc.full_code,
                        "name": loc.name,
                        "barcode": loc.barcode,
                        "zone": loc.zone,
                        "current_items": total_qty,
                        "max_items": loc.max_items,
                        "available": available,
                        "priority": loc.priority,
                    }
                )

            return result
        finally:
            session.close()

    @staticmethod
    def get_location_stock(location_id: int) -> List[Dict[str, Any]]:
        """Lokasyondaki stokları getir"""
        session = get_session()
        try:
            balances = (
                session.query(StockBalance)
                .filter(
                    StockBalance.location_id == location_id,
                    StockBalance.quantity > 0,
                )
                .all()
            )

            result = []
            for balance in balances:
                result.append(
                    {
                        "item_id": balance.item_id,
                        "item_code": balance.item.code if balance.item else "",
                        "item_name": balance.item.name if balance.item else "",
                        "quantity": float(balance.quantity),
                        "lot_number": balance.lot_number,
                        "expiry_date": balance.expiry_date,
                        "unit_cost": float(balance.unit_cost or 0),
                    }
                )

            return result
        finally:
            session.close()

    @staticmethod
    def _generate_barcode() -> str:
        """Benzersiz lokasyon barkodu oluştur"""
        # LOC- prefix + 8 karakter UUID
        return f"LOC-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def _generate_aisle_codes(start: str, end: str) -> List[str]:
        """Koridor kodlarını oluştur (A-Z, AA-AZ vb.)"""
        result = []
        current = start.upper()
        end = end.upper()

        while current <= end:
            result.append(current)
            # Sonraki harfe geç
            if len(current) == 1:
                if current == "Z":
                    current = "AA"
                else:
                    current = chr(ord(current) + 1)
            elif len(current) == 2:
                if current[1] == "Z":
                    current = chr(ord(current[0]) + 1) + "A"
                else:
                    current = current[0] + chr(ord(current[1]) + 1)
            else:
                break

            if len(result) > 702:  # A-ZZ = 702 maksimum
                break

        return result
