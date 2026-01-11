"""
Akıllı İş - Teslimat İrsaliyesi Modülü
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QMessageBox
)

from .delivery_note_list import DeliveryNoteListPage
from .delivery_note_form import DeliveryNoteFormPage

try:
    from modules.development.services import ErrorHandler
except ImportError:
    ErrorHandler = None

class DeliveryNoteModule(QWidget):
    """Teslimat irsaliyesi modülü"""

    page_title = "Teslimat İrsaliyeleri"

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
        self.list_page = DeliveryNoteListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_note)
        self.list_page.view_clicked.connect(self._show_view)
        self.list_page.ship_clicked.connect(self._ship_note)
        self.list_page.complete_clicked.connect(self._complete_note)
        self.list_page.cancel_clicked.connect(self._cancel_note)
        self.list_page.create_invoice_clicked.connect(self._create_invoice)
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
                    DeliveryNoteService, CustomerService
                )
                self.service = DeliveryNoteService()
                self.customer_service = CustomerService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(
                        e, "DeliveryNoteModule._ensure_services"
                    )
                print(f"İrsaliye servisi yükleme hatası: {e}")

        if not self.item_service:
            try:
                from modules.inventory.services import ItemService
                self.item_service = ItemService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(
                        e, "DeliveryNoteModule._ensure_services"
                    )
                print(f"Stok servisi yükleme hatası: {e}")

        if not self.unit_service:
            try:
                from modules.inventory.services import UnitService
                self.unit_service = UnitService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(
                        e, "DeliveryNoteModule._ensure_services"
                    )
                print(f"Birim servisi yükleme hatası: {e}")

    def _load_data(self):
        if not self.service:
            return

        try:
            notes = self.service.get_all()
            data = []
            for n in notes:
                data.append({
                    "id": n.id,
                    "note_no": n.delivery_no,
                    "note_date": n.delivery_date,
                    "customer_name": n.customer.name if n.customer else "-",
                    "order_no": n.sales_order.order_no if n.sales_order else "",
                    "status": n.status.value if n.status else "draft",
                    "ship_date": n.actual_delivery_date,
                    "total_items": len(n.items) if n.items else 0,
                })
            self.list_page.load_data(data)
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "DeliveryNoteModule._load_data")
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
                ErrorHandler.log_error(e, "DeliveryNoteModule._get_items")
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
                ErrorHandler.log_error(e, "DeliveryNoteModule._get_customers")
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
                ErrorHandler.log_error(e, "DeliveryNoteModule._get_units")
            return []

    def _show_add_form(self):
        items = self._get_items()
        customers = self._get_customers()
        units = self._get_units()

        form = DeliveryNoteFormPage(
            items=items,
            customers=customers,
            units=units
        )
        form.saved.connect(self._save_note)
        form.cancelled.connect(self._back_to_list)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_edit_form(self, note_id: int):
        if not self.service:
            return

        try:
            note = self.service.get_by_id(note_id)
            if note:
                items_data = []
                for item in note.items:
                    items_data.append({
                        "id": item.id,
                        "item_id": item.item_id,
                        "quantity": item.quantity,
                        "unit_id": item.unit_id,
                    })

                data = {
                    "id": note.id,
                    "note_no": note.delivery_no,
                    "note_date": note.delivery_date,
                    "customer_id": note.customer_id,
                    "customer_name": (
                        note.customer.name if note.customer else ""
                    ),
                    "customer_code": (
                        note.customer.code if note.customer else ""
                    ),
                    "order_no": (
                        note.sales_order.order_no if note.sales_order else ""
                    ),
                    "ship_date": note.actual_delivery_date,
                    "delivery_address": note.shipping_address,
                    "status": note.status.value if note.status else "draft",
                    "notes": note.notes,
                    "items": items_data,
                }

                items = self._get_items()
                customers = self._get_customers()
                units = self._get_units()

                form = DeliveryNoteFormPage(
                    note_data=data,
                    items=items,
                    customers=customers,
                    units=units
                )
                form.saved.connect(self._save_note)
                form.cancelled.connect(self._back_to_list)
                form.ship_note.connect(self._ship_note)
                form.complete_note.connect(self._complete_note)
                self.stack.addWidget(form)
                self.stack.setCurrentWidget(form)

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "DeliveryNoteModule._show_edit_form")
            print(f"Düzenleme hatası: {e}")
            import traceback
            traceback.print_exc()

    def _show_view(self, note_id: int):
        self._show_edit_form(note_id)

    def _save_note(self, data: dict):
        if not self.service:
            return

        try:
            note_id = data.pop("id", None)
            items_data = data.pop("items", [])

            if note_id:
                self.service.update(note_id, items_data, **data)
                QMessageBox.information(
                    self, "Başarılı", "İrsaliye güncellendi!"
                )
            else:
                self.service.create(items_data, **data)
                QMessageBox.information(
                    self, "Başarılı", "Yeni irsaliye oluşturuldu!"
                )

            self._back_to_list()
            self._load_data()

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "DeliveryNoteModule._save_note")
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {e}")
            import traceback
            traceback.print_exc()

    def _ship_note(self, note_id: int):
        """Sevk et"""
        if not self.service:
            return

        try:
            self.service.ship(note_id)
            QMessageBox.information(self, "Başarılı", "İrsaliye sevk edildi!")
            self._back_to_list()
            self._load_data()
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "DeliveryNoteModule._ship_note")
            QMessageBox.critical(self, "Hata", f"Hata: {e}")

    def _complete_note(self, note_id: int):
        """Teslim et (stok hareketi oluşturur)"""
        if not self.service:
            return

        reply = QMessageBox.question(
            self, "Onay",
            "Bu irsaliyeyi teslim edildi olarak işaretlemek istiyor musunuz?\n\n"
            "Bu işlem stok hareketlerini oluşturacaktır.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.complete(note_id)
                QMessageBox.information(
                    self, "Başarılı",
                    "İrsaliye teslim edildi ve stok hareketleri oluşturuldu!"
                )
                self._back_to_list()
                self._load_data()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(
                        e, "DeliveryNoteModule._complete_note"
                    )
                QMessageBox.critical(self, "Hata", f"Hata: {e}")
                import traceback
                traceback.print_exc()

    def _cancel_note(self, note_id: int):
        """İptal et"""
        if not self.service:
            return

        reply = QMessageBox.question(
            self, "Onay",
            "Bu irsaliyeyi iptal etmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.cancel(note_id)
                QMessageBox.information(
                    self, "Başarılı", "İrsaliye iptal edildi!"
                )
                self._load_data()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "DeliveryNoteModule._cancel_note")
                QMessageBox.critical(self, "Hata", f"Hata: {e}")

    def _create_invoice(self, note_id: int):
        """Fatura oluştur"""
        if not self.service:
            return

        reply = QMessageBox.question(
            self, "Onay",
            "Bu irsaliye için fatura oluşturmak istiyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                from modules.sales.services import InvoiceService
                invoice_service = InvoiceService()
                invoice = invoice_service.create_from_delivery(note_id)
                QMessageBox.information(
                    self, "Başarılı",
                    f"Fatura oluşturuldu!\nFatura No: {invoice.invoice_no}"
                )
                self._load_data()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(
                        e, "DeliveryNoteModule._create_invoice"
                    )
                QMessageBox.critical(self, "Hata", f"Hata: {e}")
                import traceback
                traceback.print_exc()

    def _delete_note(self, note_id: int):
        if not self.service:
            return

        try:
            if self.service.delete(note_id):
                QMessageBox.information(self, "Başarılı", "İrsaliye silindi!")
                self._load_data()
            else:
                QMessageBox.warning(
                    self, "Uyarı",
                    "İrsaliye silinemedi! (Sadece taslak irsaliyeler silinebilir)"
                )
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "DeliveryNoteModule._delete_note")
            QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")

    def _back_to_list(self):
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.setCurrentWidget(self.list_page)
            self.stack.removeWidget(current)
            current.deleteLater()
