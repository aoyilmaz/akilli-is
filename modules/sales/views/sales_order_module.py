"""
Akıllı İş - Satış Sipariş Modülü
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QMessageBox,
    QDialog, QFormLayout, QComboBox, QDialogButtonBox
)

from .sales_order_list import SalesOrderListPage
from .sales_order_form import SalesOrderFormPage

try:
    from modules.development.services import ErrorHandler
except ImportError:
    ErrorHandler = None

class WarehouseSelectDialog(QDialog):
    """Depo seçim dialogu"""

    def __init__(self, warehouses: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kaynak Depo Seçin")
        self.setMinimumWidth(350)
        self.warehouses = warehouses
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.warehouse_combo = QComboBox()
        for w in self.warehouses:
            self.warehouse_combo.addItem(
                f"{w.get('code', '')} - {w.get('name', '')}",
                w.get('id')
            )
        layout.addRow("Kaynak Depo:", self.warehouse_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_warehouse_id(self) -> int:
        return self.warehouse_combo.currentData()

class SalesOrderModule(QWidget):
    """Satış sipariş modülü"""

    page_title = "Satış Siparişleri"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.customer_service = None
        self.item_service = None
        self.unit_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # Liste sayfası
        self.list_page = SalesOrderListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_order)
        self.list_page.view_clicked.connect(self._show_view)
        self.list_page.confirm_clicked.connect(self._confirm_order)
        self.list_page.cancel_clicked.connect(self._cancel_order)
        self.list_page.create_delivery_clicked.connect(self._create_delivery)
        self.list_page.refresh_requested.connect(self._load_data)
        self.stack.addWidget(self.list_page)

        layout.addWidget(self.stack)

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_data()

    def _ensure_services(self):
        if not self.service:
            try:
                from modules.sales.services import (
                    SalesOrderService, CustomerService
                )
                self.service = SalesOrderService()
                self.customer_service = CustomerService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(
                        e, "SalesOrderModule._ensure_services"
                    )
                print(f"Satış sipariş servisi yükleme hatası: {e}")

        if not self.item_service:
            try:
                from modules.inventory.services import ItemService
                self.item_service = ItemService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(
                        e, "SalesOrderModule._ensure_services"
                    )
                print(f"Stok servisi yükleme hatası: {e}")

        if not self.unit_service:
            try:
                from modules.inventory.services import UnitService
                self.unit_service = UnitService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(
                        e, "SalesOrderModule._ensure_services"
                    )
                print(f"Birim servisi yükleme hatası: {e}")

    def _load_data(self):
        if not self.service:
            return

        try:
            orders = self.service.get_all()
            data = []
            for o in orders:
                data.append({
                    "id": o.id,
                    "order_no": o.order_no,
                    "order_date": o.order_date,
                    "customer_name": o.customer.name if o.customer else "-",
                    "total_amount": o.total or 0,
                    "status": o.status.value if o.status else "draft",
                    "delivery_date": o.delivery_date,
                    "currency_code": o.currency if o.currency else "TRY",
                    "total_items": len(o.items) if o.items else 0,
                })
            self.list_page.load_data(data)
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesOrderModule._load_data")
            print(f"Veri yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
            self.list_page.load_data([])

    def _get_items(self) -> list:
        """Stok kartlarını getir"""
        if not self.item_service:
            return []
        try:
            items = self.item_service.get_all()
            return [{
                "id": i.id,
                "code": i.code,
                "name": i.name,
                "unit_id": i.unit_id,
                "unit_name": i.unit.name if i.unit else "",
                "stock": 0,
            } for i in items]
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesOrderModule._get_items")
            return []

    def _get_customers(self) -> list:
        """Müşterileri getir"""
        if not self.customer_service:
            return []
        try:
            customers = self.customer_service.get_all()
            return [{
                "id": c.id,
                "code": c.code,
                "name": c.name,
                "phone": c.phone,
                "email": c.email,
            } for c in customers]
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesOrderModule._get_customers")
            return []

    def _get_units(self) -> list:
        """Birimleri getir"""
        if not self.unit_service:
            return []
        try:
            units = self.unit_service.get_all()
            return [{"id": u.id, "name": u.name, "code": u.code} for u in units]
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesOrderModule._get_units")
            return []

    def _show_add_form(self):
        items = self._get_items()
        customers = self._get_customers()
        units = self._get_units()

        form = SalesOrderFormPage(
            items=items,
            customers=customers,
            units=units
        )
        form.saved.connect(self._save_order)
        form.cancelled.connect(self._back_to_list)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_edit_form(self, order_id: int):
        if not self.service:
            return

        try:
            order = self.service.get_by_id(order_id)
            if order:
                items_data = []
                for item in order.items:
                    items_data.append({
                        "id": item.id,
                        "item_id": item.item_id,
                        "quantity": item.quantity,
                        "unit_id": item.unit_id,
                        "unit_price": item.unit_price,
                        "discount_rate": item.discount_rate,
                    })

                data = {
                    "id": order.id,
                    "order_no": order.order_no,
                    "order_date": order.order_date,
                    "customer_id": order.customer_id,
                    "customer_name": (
                        order.customer.name if order.customer else ""
                    ),
                    "customer_code": (
                        order.customer.code if order.customer else ""
                    ),
                    "delivery_date": order.delivery_date,
                    "currency": order.currency if order.currency else "TRY",
                    "status": order.status.value if order.status else "draft",
                    "notes": order.notes,
                    "items": items_data,
                }

                items = self._get_items()
                customers = self._get_customers()
                units = self._get_units()

                form = SalesOrderFormPage(
                    order_data=data,
                    items=items,
                    customers=customers,
                    units=units
                )
                form.saved.connect(self._save_order)
                form.cancelled.connect(self._back_to_list)
                form.confirm_order.connect(self._confirm_order)
                self.stack.addWidget(form)
                self.stack.setCurrentWidget(form)

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesOrderModule._show_edit_form")
            print(f"Düzenleme hatası: {e}")
            import traceback
            traceback.print_exc()

    def _show_view(self, order_id: int):
        self._show_edit_form(order_id)

    def _save_order(self, data: dict):
        if not self.service:
            return

        try:
            order_id = data.pop("id", None)
            items_data = data.pop("items", [])

            if order_id:
                self.service.update(order_id, items_data, **data)
                QMessageBox.information(self, "Başarılı", "Sipariş güncellendi!")
            else:
                self.service.create(items_data, **data)
                QMessageBox.information(
                    self, "Başarılı", "Yeni sipariş oluşturuldu!"
                )

            self._back_to_list()
            self._load_data()

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesOrderModule._save_order")
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {e}")
            import traceback
            traceback.print_exc()

    def _confirm_order(self, order_id: int):
        """Siparişi onayla"""
        if not self.service:
            return

        reply = QMessageBox.question(
            self, "Onay",
            "Bu siparişi onaylamak istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.confirm(order_id)
                QMessageBox.information(self, "Başarılı", "Sipariş onaylandı!")
                self._back_to_list()
                self._load_data()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "SalesOrderModule._confirm_order")
                QMessageBox.critical(self, "Hata", f"Hata: {e}")

    def _cancel_order(self, order_id: int):
        """Siparişi iptal et"""
        if not self.service:
            return

        reply = QMessageBox.question(
            self, "Onay",
            "Bu siparişi iptal etmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.cancel(order_id)
                QMessageBox.information(self, "Başarılı", "Sipariş iptal edildi!")
                self._load_data()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "SalesOrderModule._cancel_order")
                QMessageBox.critical(self, "Hata", f"Hata: {e}")

    def _create_delivery(self, order_id: int):
        """İrsaliye oluştur"""
        if not self.service:
            return

        try:
            # Siparişi getir
            order = self.service.get_by_id(order_id)
            if not order:
                QMessageBox.warning(self, "Uyarı", "Sipariş bulunamadı!")
                return

            # Depoları getir
            warehouses = self._get_warehouses()
            if not warehouses:
                QMessageBox.warning(
                    self, "Uyarı",
                    "Sistemde tanımlı depo bulunamadı!"
                )
                return

            # Depo seçim dialogu
            dialog = WarehouseSelectDialog(warehouses, self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            warehouse_id = dialog.get_warehouse_id()
            if not warehouse_id:
                QMessageBox.warning(self, "Uyarı", "Lütfen bir depo seçin!")
                return

            # Sipariş kalemlerinden irsaliye kalemlerini oluştur
            items_data = []
            for item in order.items:
                remaining = float(item.quantity or 0) - float(
                    item.delivered_quantity or 0
                )
                if remaining > 0:
                    items_data.append({
                        "item_id": item.item_id,
                        "so_item_id": item.id,
                        "quantity": remaining,
                        "unit_id": item.unit_id,
                    })

            if not items_data:
                QMessageBox.warning(
                    self, "Uyarı",
                    "Sevk edilecek kalem bulunamadı!"
                )
                return

            # İrsaliye oluştur
            from modules.sales.services import DeliveryNoteService
            delivery_service = DeliveryNoteService()
            delivery = delivery_service.create_from_order(
                order_id, warehouse_id, items_data
            )
            QMessageBox.information(
                self, "Başarılı",
                f"İrsaliye oluşturuldu!\nİrsaliye No: {delivery.delivery_no}"
            )
            self._load_data()

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesOrderModule._create_delivery")
            QMessageBox.critical(self, "Hata", f"Hata: {e}")
            import traceback
            traceback.print_exc()

    def _get_warehouses(self) -> list:
        """Depoları getir"""
        try:
            from modules.inventory.services import WarehouseService
            warehouse_service = WarehouseService()
            warehouses = warehouse_service.get_all()
            return [{
                "id": w.id,
                "code": w.code,
                "name": w.name,
            } for w in warehouses]
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesOrderModule._get_warehouses")
            return []

    def _delete_order(self, order_id: int):
        if not self.service:
            return

        try:
            if self.service.delete(order_id):
                QMessageBox.information(self, "Başarılı", "Sipariş silindi!")
                self._load_data()
            else:
                QMessageBox.warning(
                    self, "Uyarı",
                    "Sipariş silinemedi! (Sadece taslak siparişler silinebilir)"
                )
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesOrderModule._delete_order")
            QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")

    def _back_to_list(self):
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.setCurrentWidget(self.list_page)
            self.stack.removeWidget(current)
            current.deleteLater()
