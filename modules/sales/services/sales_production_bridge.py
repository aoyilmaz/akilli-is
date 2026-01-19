"""
Akıllı İş - Satış ve Üretim Entegrasyonu (MTO Trigger)
"""

from decimal import Decimal
from sqlalchemy.orm import Session
from database.models.sales import SalesOrder, SalesOrderItem
from database.models.production import WorkOrder, WorkOrderStatus, BillOfMaterials
from database.models.inventory import Item


class SalesProductionBridge:
    @staticmethod
    def trigger_mto_check(session: Session, sales_order: SalesOrder):
        """
        Satış siparişi onaylandığında stok kontrolü yapar ve gerekirse iş emri açar.
        """
        for item in sales_order.items:
            product = session.query(Item).get(item.item_id)

            # Üretilebilir mi ve stok yeterli mi?
            if product.is_producible:
                available = product.total_stock
                if available < item.quantity:
                    # Eksik miktar için iş emri oluştur
                    needed_qty = item.quantity - available
                    SalesProductionBridge.create_work_order_draft(
                        session, product, needed_qty, sales_order
                    )

    @staticmethod
    def create_work_order_draft(
        session: Session, item: Item, quantity: Decimal, sales_order: SalesOrder
    ):
        """Otomatik iş emri taslağı oluşturur"""
        # Varsayılan aktif reçeteyi bul
        bom = (
            session.query(BillOfMaterials)
            .filter(
                BillOfMaterials.item_id == item.id, BillOfMaterials.is_active == True
            )
            .first()
        )

        if not bom:
            return None

        work_order = WorkOrder(
            order_no=f"WO-MTO-{sales_order.order_no}-{item.code}",
            item_id=item.id,
            bom_id=bom.id,
            planned_quantity=quantity,
            status=WorkOrderStatus.DRAFT,
            description=f"Otomatik MTO: {sales_order.order_no} nolu sipariş için.",
            sales_order_id=sales_order.id,
        )
        session.add(work_order)
        session.flush()
        return work_order
