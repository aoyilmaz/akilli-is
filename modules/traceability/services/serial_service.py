"""
Akıllı İş - Seri Numarası Servis Katmanı
"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from database.models.traceability import SerialNumber
from datetime import date


class SerialService:
    """Seri Numarası takibi için servis sınıfı"""

    def __init__(self, db: Session):
        self.db = db

    def create_serials(
        self, product_id: int, count: int, lot_id: Optional[int] = None
    ) -> List[SerialNumber]:
        """Belirli sayıda seri numarası üretir ve kaydeder"""
        serials = []
        for _ in range(count):
            serial_no = self.generate_serial_number(product_id)
            sn = SerialNumber(
                serial=serial_no,
                product_id=product_id,
                lot_id=lot_id,
                status="in_stock",
            )
            self.db.add(sn)
            serials.append(sn)

        self.db.commit()
        return serials

    def generate_serial_number(self, product_id: int) -> str:
        """Benzersiz seri numarası üretir"""
        # Proje kuralına göre formatlanabilir (Örn: SN-ITEMID-UUID)
        unique_suffix = uuid.uuid4().hex[:8].upper()
        return f"SN-{product_id}-{unique_suffix}"

    def register_sale(self, serial: str, customer_id: int) -> SerialNumber:
        """Seri numarasının satışını (müşteriye çıkışını) kaydeder"""
        sn = self.db.query(SerialNumber).filter(SerialNumber.serial == serial).first()
        if not sn:
            raise ValueError(f"Seri numarası {serial} bulunamadı")

        sn.status = "sold"
        sn.customer_id = customer_id
        sn.sale_date = date.today()

        self.db.commit()
        self.db.refresh(sn)
        return sn

    def get_serial_history(self, serial: str) -> Dict[str, Any]:
        """Bir seri numarasının tüm geçmişini döner"""
        sn = self.db.query(SerialNumber).filter(SerialNumber.serial == serial).first()
        if not sn:
            return {}

        return {
            "serial": sn.serial,
            "status": sn.status,
            "product_name": sn.product.name if sn.product else "N/A",
            "lot_number": sn.lot.lot_number if sn.lot else "N/A",
            "sale_date": sn.sale_date,
            "customer": sn.customer.name if sn.customer else "N/A",
        }
