"""
Akıllı İş - İade Yönetimi Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QMessageBox,
    QStackedWidget,
)

from .sales_return_list import SalesReturnListPage
from .sales_return_form import SalesReturnFormPage
from modules.returns.services.sales_return import SalesReturnService
from modules.returns.services.purchase_return import PurchaseReturnService
from database.models.returns import ReturnType, ReturnStatus

try:
    from modules.development.services import ErrorHandler
except ImportError:
    ErrorHandler = None


class ReturnModule(QWidget):
    """İade Yönetimi Ana Modülü"""

    page_title = "İade Yönetimi"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sales_service = None
        self.purchase_service = None
        self.customer_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_sales_return_tab(), "Satış İadeleri")
        self.tabs.addTab(self._create_purchase_return_tab(), "Satın Alma İadeleri")

        layout.addWidget(self.tabs)

    def _create_sales_return_tab(self):
        """Satış İadeleri Sekmesi"""
        self.sales_stack = QStackedWidget()

        # Liste
        self.sales_list = SalesReturnListPage()
        self.sales_list.add_clicked.connect(self._show_sales_add_form)
        self.sales_list.edit_clicked.connect(self._show_sales_edit_form)
        self.sales_list.approve_clicked.connect(self._approve_sales_return)
        # self.sales_list.view_clicked.connect(self._show_sales_view)
        # self.sales_list.delete_clicked.connect(self._delete_sales_return)
        self.sales_list.refresh_requested.connect(self._load_sales_data)

        self.sales_stack.addWidget(self.sales_list)
        return self.sales_stack

    def _create_purchase_return_tab(self):
        """Satın Alma İadeleri Sekmesi (Placeholder)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # Placeholder for Purchase Return List
        from PyQt6.QtWidgets import QLabel

        layout.addWidget(QLabel("Satın Alma İadeleri - Yakında"))
        return widget

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_sales_data()

    def _ensure_services(self):
        if not self.sales_service:
            try:
                self.sales_service = SalesReturnService()
                # self.purchase_service = PurchaseReturnService()
                from modules.sales.services import CustomerService

                self.customer_service = CustomerService()
            except Exception as e:
                print(f"Service init error: {e}")

    def _load_sales_data(self):
        if not self.sales_service:
            return

        try:
            returns = self.sales_service.list_returns(type=ReturnType.SALES)
            data = []
            for r in returns:
                data.append(
                    {
                        "id": r.id,
                        "code": r.code,
                        "return_date": r.return_date,
                        "customer_name": r.customer.name if r.customer else "-",
                        "status": r.status,
                        "item_count": len(r.lines),
                        "total_amount": 0,  # TODO: Calculate total
                    }
                )
            self.sales_list.load_data(data)
        except Exception as e:
            print(f"Load data error: {e}")

    def _show_sales_add_form(self):
        # Siparişleri getir (Seçim için)
        from modules.sales.services import SalesOrderService

        order_service = SalesOrderService()
        orders = (
            order_service.get_all()
        )  # Filtrele: Sadece faturalanmış veya sevk edilmişler?

        orders_data = []
        for o in orders:
            orders_data.append(
                {
                    "id": o.id,
                    "order_no": o.order_no,
                    "order_date": o.order_date,
                    "customer_name": o.customer.name if o.customer else "-",
                    "customer_id": o.customer_id,
                    "total_amount": o.total,
                    "items": [
                        {
                            "item_id": i.item_id,
                            "code": i.item.code if i.item else "",
                            "name": i.item.name if i.item else "",
                            "quantity": i.quantity,
                            "unit_price": i.unit_price,
                            "unit_name": i.unit.name if i.unit else "",
                        }
                        for i in o.items
                    ],
                }
            )

        form = SalesReturnFormPage(orders=orders_data)
        form.saved.connect(self._save_sales_return)
        form.cancelled.connect(self._back_to_sales_list)

        self.sales_stack.addWidget(form)
        self.sales_stack.setCurrentWidget(form)

    def _show_sales_edit_form(self, return_id: int):
        # Mevcut iadeyi getir ve formu aç
        pass

    def _save_sales_return(self, data: dict):
        if not self.sales_service:
            return

        try:
            user_id = 1  # TODO: Get current user
            if "order_id" in data:
                # Siparişten oluştur
                self.sales_service.create_from_sales_order(
                    order_id=data["order_id"], lines_data=data["lines"], user_id=user_id
                )
            else:
                # update
                pass

            QMessageBox.information(self, "Başarılı", "İade oluşturuldu.")
            self._back_to_sales_list()
            self._load_sales_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {e}")

    def _approve_sales_return(self, return_id: int):
        if not self.sales_service:
            return

        try:
            user_id = 1
            # Workflow: DRAFT -> PENDING -> APPROVED
            # Direct approval for now if user has permission
            self.sales_service.update_status(
                return_id, ReturnStatus.PENDING_APPROVAL, user_id
            )
            self.sales_service.approve_return(return_id, user_id)

            QMessageBox.information(
                self, "Başarılı", "İade onaylandı ve stok hareketleri oluşturuldu."
            )
            self._load_sales_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Onay hatası: {e}")

    def _back_to_sales_list(self):
        current = self.sales_stack.currentWidget()
        if current != self.sales_list:
            self.sales_stack.setCurrentWidget(self.sales_list)
            self.sales_stack.removeWidget(current)
            current.deleteLater()
