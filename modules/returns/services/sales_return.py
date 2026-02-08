from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from modules.returns.services.base import BaseReturnService
from database.models.returns import ReturnType, ReturnStatus, ReturnOrder
from database.models.sales import SalesOrder, SalesOrderItem


class SalesReturnService(BaseReturnService):
    """
    Satış İade Servisi
    """

    def create_return(self, data: Dict[str, Any], user_id: int) -> ReturnOrder:
        """
        Satış iadesi oluştur
        """
        data["type"] = ReturnType.SALES
        return super().create_return(data, user_id)

    def create_from_sales_order(
        self, order_id: int, lines_data: list[Dict[str, Any]], user_id: int
    ) -> ReturnOrder:
        """
        Satış siparişinden iade oluştura
        """
        order = self.db.query(SalesOrder).get(order_id)
        if not order:
            raise ValueError(f"Sales order {order_id} not found")

        # İade başlık verilerini hazırla
        return_data = {
            "type": ReturnType.SALES,
            "customer_id": order.customer_id,
            "related_sale_order_id": order.id,
            "lines": [],
        }

        # İade kalemlerini hazırla
        for line_data in lines_data:
            item_id = line_data.get("item_id")
            quantity = line_data.get("quantity")

            # Siparişteki kalemi bul (Fiyat bilgisi için)
            # Bu basit eşleşme. Gerçekte order_line_id gelmeli.
            order_line = (
                self.db.query(SalesOrderItem)
                .filter(
                    SalesOrderItem.order_id == order.id,
                    SalesOrderItem.item_id == item_id,
                )
                .first()
            )

            unit_price = order_line.unit_price if order_line else 0

            return_data["lines"].append(
                {
                    "item_id": item_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "unit_id": order_line.unit_id if order_line else None,
                    "related_sale_line_id": order_line.id if order_line else None,
                    "reason": line_data.get("reason"),
                    "condition": line_data.get("condition"),
                }
            )

        return self.create_return(return_data, user_id)
