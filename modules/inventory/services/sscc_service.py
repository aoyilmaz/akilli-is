"""
Akıllı İş - SSCC (Taşıma Birimi) Servisi
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models import (
    TransportUnit,
    TransportUnitItem,
    TransportUnitType,
    TransportUnitStatus,
    StockMovement,
    StockMovementType,
)
from modules.inventory.services.base import ServiceBase, StockMovementService


class SSCCService(ServiceBase):
    """
    SSCC (Serial Shipping Container Code) / Taşıma Birimi Yönetimi
    """

    def __init__(self, session: Session = None):
        super().__init__()
        if session:
            self.session = session

        # Hareket servisini başlat ve aynı session'ı kullanmasını sağla (Transaction bütünlüğü için)
        self.movement_service = StockMovementService(allow_negative_stock=True)
        self.movement_service.session = self.session

    def generate_sscc(self) -> str:
        """
        Benzersiz bir SSCC barkodu üretir.
        Format: [Genişletme Basamağı][GS1 Firma Öneki][Seri No][Kontrol Basamağı]
        Şimdilik basit bir sequence kullanacağız: "TU" + YYYYMMDD + 6 haneli sıra no
        Örn: TU20240120000001
        """
        prefix = f"TU{datetime.now().strftime('%Y%m%d')}"

        # Günün son numarasını bul
        last_tu = (
            self.session.query(TransportUnit)
            .filter(TransportUnit.sscc.like(f"{prefix}%"))
            .order_by(TransportUnit.sscc.desc())
            .first()
        )

        if last_tu:
            last_seq = int(last_tu.sscc[-6:])
            new_seq = last_seq + 1
        else:
            new_seq = 1

        return f"{prefix}{new_seq:06d}"

    def create_transport_unit(
        self,
        unit_type: TransportUnitType = TransportUnitType.PALET,
        warehouse_id: int = None,
        location_id: int = None,
        notes: str = None,
        sscc: str = None,
    ) -> TransportUnit:
        """Yeni bir taşıma birimi oluşturur"""
        if not sscc:
            sscc = self.generate_sscc()

        tu = TransportUnit(
            sscc=sscc,
            unit_type=unit_type,
            status=TransportUnitStatus.ACIK,
            warehouse_id=warehouse_id,
            location_id=location_id,
            notes=notes,
            created_date=datetime.utcnow(),
        )

        self.session.add(tu)
        self.session.commit()
        return tu

    def get_all(self) -> List[TransportUnit]:
        """Tüm taşıma birimlerini getirir"""
        return (
            self.session.query(TransportUnit)
            .order_by(TransportUnit.created_date.desc())
            .all()
        )

    def get_by_id(self, unit_id: int) -> Optional[TransportUnit]:
        """ID'ye göre birim getirir"""
        return self.session.query(TransportUnit).get(unit_id)

    def get_by_sscc(self, sscc: str) -> Optional[TransportUnit]:
        """SSCC barkoduna göre birim getirir"""
        return self.session.query(TransportUnit).filter_by(sscc=sscc).first()

    def get_unit_items(self, unit_id: int) -> List[TransportUnitItem]:
        """Taşıma birimi içeriklerini getirir"""
        return (
            self.session.query(TransportUnitItem)
            .filter_by(transport_unit_id=unit_id)
            .all()
        )

    def add_item_to_unit(
        self,
        transport_unit_id: int,
        item_id: int,
        quantity: Decimal,
        unit_id: int = None,
        lot_number: str = None,
        added_by_user_id: int = None,
        secondary_quantity: Decimal = None,
        secondary_unit_id: int = None,
    ) -> TransportUnitItem:
        """
        Taşıma birimine ürün ekler.
        Not: Bu işlem stok düşümü YAPMAZ. Stok düşümü için ayrıca StockMovement yapılmalıdır.
        Genellikle:
        1. Üretim -> Paletleme (Stok Giriş + Palete Ekleme)
        2. Depo -> Sevkiyat (Stok Transfer/Rezerve + Palete Ekleme)
        senaryolarında kullanılır.
        """
        tu = self.session.query(TransportUnit).get(transport_unit_id)
        if not tu:
            raise ValueError("Taşıma birimi bulunamadı")

        if tu.status != TransportUnitStatus.ACIK:
            raise ValueError("Sadece AÇIK durumdaki birimlere ürün eklenebilir")

        item = TransportUnitItem(
            transport_unit_id=transport_unit_id,
            item_id=item_id,
            quantity=quantity,
            unit_id=unit_id,
            lot_number=lot_number,
            added_by=added_by_user_id,
            added_date=datetime.utcnow(),
            # Dual-Unit
            secondary_quantity=secondary_quantity,
            secondary_unit_id=secondary_unit_id,
        )

        self.session.add(item)
        self.session.commit()
        return item

    def remove_item_from_unit(self, item_id: int) -> bool:
        """Taşıma biriminden ürün çıkarır"""
        item = self.session.query(TransportUnitItem).get(item_id)
        if not item:
            return False

        if item.transport_unit.status != TransportUnitStatus.ACIK:
            raise ValueError("Sadece AÇIK durumdaki birimlerden ürün çıkarılabilir")

        self.session.delete(item)
        self.session.commit()
        return True

    def close_unit(self, transport_unit_id: int) -> TransportUnit:
        """Taşıma birimini kapatır (Paketleme tamamlandı)"""
        tu = self.session.query(TransportUnit).get(transport_unit_id)
        if not tu:
            raise ValueError("Taşıma birimi bulunamadı")

        tu.status = TransportUnitStatus.KAPALI
        tu.closed_date = datetime.utcnow()
        self.session.commit()
        return tu

    def move_unit(
        self,
        transport_unit_id: int,
        target_warehouse_id: int,
        target_location_id: int = None,
    ):
        """
        Tüm birimi başka bir depo/lokasyona taşır.
        İçindeki tüm ürünler için StockMovement oluşturur.
        """
        tu = self.session.query(TransportUnit).get(transport_unit_id)
        if not tu:
            raise ValueError("Taşıma birimi bulunamadı")

        # 1. Lokasyon güncelle
        old_warehouse_id = tu.warehouse_id
        tu.warehouse_id = target_warehouse_id
        tu.location_id = target_location_id

        # 2. İçerik için stok hareketi oluştur
        for item in tu.items:
            self.movement_service.create_movement(
                item_id=item.item_id,
                movement_type=StockMovementType.TRANSFER,
                quantity=item.quantity,
                from_warehouse_id=old_warehouse_id,
                to_warehouse_id=target_warehouse_id,
                lot_number=item.lot_number,
                description=f"SSCC Transfer: {tu.sscc}",
                document_no=tu.sscc,
                document_type="sscc_transfer",
                # Dual-Unit
                secondary_quantity=item.secondary_quantity,
                secondary_unit_id=item.secondary_unit_id,
            )

        self.session.commit()
