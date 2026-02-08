"""
Akıllı İş - İzlenebilirlik (Traceability) Motoru
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from database.models.traceability import Lot, TraceLink


class TraceEngine:
    """İleri ve Geri İzlenebilirlik (Genealogy) motoru"""

    def __init__(self, db: Session):
        self.db = db

    def trace_backward(self, lot_id: int, depth: int = 5) -> Dict[str, Any]:
        """Geriye izleme: Bu lotun içindeki bileşenleri/hammaddeyi bulur"""
        if depth <= 0:
            return {"status": "MAX_DEPTH_REACHED"}

        lot = self.db.query(Lot).get(lot_id)
        if not lot:
            return {}

        links = self.db.query(TraceLink).filter(TraceLink.child_lot_id == lot_id).all()

        components = []
        for link in links:
            parent = self.db.query(Lot).get(link.parent_lot_id)
            if not parent:
                continue

            components.append(
                {
                    "lot_id": parent.id,
                    "lot_number": parent.lot_number,
                    "product_name": (parent.product.name if parent.product else "N/A"),
                    "quantity_used": float(link.quantity_used),
                    "sub_trace": self.trace_backward(parent.id, depth - 1),
                }
            )

        return {
            "lot_id": lot.id,
            "lot_number": lot.lot_number,
            "product_name": lot.product.name if lot.product else "N/A",
            "components": components,
        }

    def trace_forward(self, lot_id: int, depth: int = 5) -> Dict[str, Any]:
        """İleriye izleme: Bu lotun kullanıldığı üst ürünleri bulur"""
        if depth <= 0:
            return {"status": "MAX_DEPTH_REACHED"}

        lot = self.db.query(Lot).get(lot_id)
        if not lot:
            return {}

        links = self.db.query(TraceLink).filter(TraceLink.parent_lot_id == lot_id).all()

        usages = []
        for link in links:
            child = self.db.query(Lot).get(link.child_lot_id)
            if not child:
                continue

            usages.append(
                {
                    "lot_id": child.id,
                    "lot_number": child.lot_number,
                    "product_name": (child.product.name if child.product else "N/A"),
                    "quantity_used": float(link.quantity_used),
                    "sub_trace": self.trace_forward(child.id, depth - 1),
                }
            )

        return {
            "lot_id": lot.id,
            "lot_number": lot.lot_number,
            "product_name": lot.product.name if lot.product else "N/A",
            "usages": usages,
        }

    def link_lots(
        self,
        parent_lot_id: int,
        child_lot_id: int,
        qty: float,
        work_order_id: Optional[int] = None,
    ) -> TraceLink:
        """İki lot arasında ebeveyn-çocuk bağı kurar"""
        link = TraceLink(
            parent_lot_id=parent_lot_id,
            child_lot_id=child_lot_id,
            quantity_used=qty,
            work_order_id=work_order_id,
        )
        self.db.add(link)
        self.db.commit()
        return link
