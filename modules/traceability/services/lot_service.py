"""
Akıllı İş - Lot (Parti) Servis Katmanı
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from database.models.traceability import Lot, LotStatus
from datetime import date


class LotService:
    """Lot (Parti) yönetimi için servis sınıfı"""

    def __init__(self, db: Session):
        self.db = db

    def create_lot(self, data: Dict[str, Any]) -> Lot:
        """Yeni bir Lot (Parti) oluşturur"""
        lot = Lot(**data)
        if not lot.lot_number:
            lot.lot_number = self.generate_lot_number(lot.product_id)

        if lot.quantity and not lot.remaining_qty:
            lot.remaining_qty = lot.quantity

        self.db.add(lot)
        self.db.commit()
        self.db.refresh(lot)
        return lot

    def generate_lot_number(self, product_id: int) -> str:
        """Ürün bazlı benzersiz Lot numarası üretir"""
        today = date.today().strftime("%Y%m%d")
        prefix = f"LOT-{product_id}-{today}"

        # Mevcut lotları say (Basit sayaç)
        count = (
            self.db.query(Lot)
            .filter(
                Lot.product_id == product_id,
                Lot.lot_number.like(f"{prefix}-%"),
            )
            .count()
        )

        return f"{prefix}-{count + 1:04d}"

    def update_quantity(self, lot_id: int, qty_change: float) -> Lot:
        """Lot miktarını günceller (tüketim veya mal kabul)"""
        lot = self.db.query(Lot).get(lot_id)
        if not lot:
            raise ValueError(f"Lot ID {lot_id} bulunamadı")

        lot.remaining_qty += qty_change
        if lot.remaining_qty < 0:
            lot.remaining_qty = 0

        # Miktar sıfırlandıysa durumu güncelle
        if lot.remaining_qty == 0:
            lot.status = LotStatus.CONSUMED

        self.db.commit()
        self.db.refresh(lot)
        return lot

    def quarantine_lot(self, lot_id: int, reason: str) -> Lot:
        """Lot'u karantinaya (blokaj) alır"""
        lot = self.db.query(Lot).get(lot_id)
        if not lot:
            raise ValueError(f"Lot ID {lot_id} bulunamadı")

        lot.status = LotStatus.QUARANTINE
        timestamp = date.today().strftime("%d.%m.%Y")
        note_entry = f"[{timestamp}] Karantina: {reason}"

        if lot.notes:
            lot.notes += f"\n{note_entry}"
        else:
            lot.notes = note_entry

        self.db.commit()
        self.db.refresh(lot)
        return lot

    def release_lot(self, lot_id: int) -> Lot:
        """Lot'u karantinadan çıkarır"""
        lot = self.db.query(Lot).get(lot_id)
        if not lot:
            raise ValueError(f"Lot ID {lot_id} bulunamadı")

        lot.status = LotStatus.ACTIVE
        self.db.commit()
        self.db.refresh(lot)
        return lot
