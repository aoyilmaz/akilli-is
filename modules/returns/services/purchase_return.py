from typing import Dict, Any
from modules.returns.services.base import BaseReturnService
from database.models.returns import ReturnType, ReturnOrder
from database.models.purchasing import PurchaseOrder, PurchaseOrderItem


class PurchaseReturnService(BaseReturnService):
    """
    Satınalma İade Servisi
    """

    def create_return(self, data: Dict[str, Any], user_id: int) -> ReturnOrder:
        """
        Satınalma iadesi oluştur
        """
        data["type"] = ReturnType.PURCHASE
        return super().create_return(data, user_id)

    def create_from_purchase_order(
        self, order_id: int, lines_data: list[Dict[str, Any]], user_id: int
    ) -> ReturnOrder:
        """
        Satınalma siparişinden iade oluştur
        """
        order = self.db.query(PurchaseOrder).get(order_id)
        if not order:
            raise ValueError(f"Purchase order {order_id} not found")

        # İade başlık verilerini hazırla
        return_data = {
            "type": ReturnType.PURCHASE,
            "supplier_id": order.supplier_id,
            "related_purchase_order_id": order.id,
            "lines": [],
        }

        # İade kalemlerini hazırla
        for line_data in lines_data:
            item_id = line_data.get("item_id")
            quantity = line_data.get("quantity")

            # Siparişteki kalemi bul
            order_line = (
                self.db.query(PurchaseOrderItem)
                .filter(
                    PurchaseOrderItem.order_id == order.id,
                    PurchaseOrderItem.item_id == item_id,
                )
                .first()
            )

            unit_price = order_line.unit_price if order_line else 0

            return_data["lines"].append(
                {
                    "item_id": item_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "warehouse_id": line_data.get(
                        "warehouse_id"
                    ),  # Ensure warehouse_id is passed
                    "reason": line_data.get("reason"),
                    "condition": line_data.get("condition"),
                    # related lines?
                }
            )

        return self.create_return(return_data, user_id)
