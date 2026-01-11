"""
Akıllı İş - Fatura Modülü
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QMessageBox, QDialog,
    QFormLayout, QDoubleSpinBox, QDateEdit, QTextEdit, QDialogButtonBox
)
from PyQt6.QtCore import QDate

from .invoice_list import InvoiceListPage
from .invoice_form import InvoiceFormPage

try:
    from modules.development.services import ErrorHandler
except ImportError:
    ErrorHandler = None

class PaymentDialog(QDialog):
    """Ödeme kayıt dialogu"""

    def __init__(self, remaining_amount: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ödeme Kaydet")
        self.setMinimumWidth(400)
        self.remaining_amount = remaining_amount
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        # Ödeme tutarı
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, self.remaining_amount)
        self.amount_spin.setValue(self.remaining_amount)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setSuffix(" TL")
        layout.addRow("Ödeme Tutarı:", self.amount_spin)

        # Ödeme tarihi
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        layout.addRow("Ödeme Tarihi:", self.date_edit)

        # Açıklama
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        layout.addRow("Açıklama:", self.notes_edit)

        # Butonlar
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> dict:
        return {
            "amount": self.amount_spin.value(),
            "payment_date": self.date_edit.date().toPyDate(),
            "notes": self.notes_edit.toPlainText(),
        }

class InvoiceModule(QWidget):
    """Fatura modülü"""

    page_title = "Faturalar"

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
        self.list_page = InvoiceListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_invoice)
        self.list_page.view_clicked.connect(self._show_view)
        self.list_page.issue_clicked.connect(self._issue_invoice)
        self.list_page.payment_clicked.connect(self._record_payment)
        self.list_page.cancel_clicked.connect(self._cancel_invoice)
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
                from modules.sales.services import InvoiceService, CustomerService
                self.service = InvoiceService()
                self.customer_service = CustomerService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "InvoiceModule._ensure_services")
                print(f"Fatura servisi yükleme hatası: {e}")

        if not self.item_service:
            try:
                from modules.inventory.services import ItemService
                self.item_service = ItemService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "InvoiceModule._ensure_services")
                print(f"Stok servisi yükleme hatası: {e}")

        if not self.unit_service:
            try:
                from modules.inventory.services import UnitService
                self.unit_service = UnitService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "InvoiceModule._ensure_services")
                print(f"Birim servisi yükleme hatası: {e}")

    def _load_data(self):
        if not self.service:
            return

        try:
            invoices = self.service.get_all()
            data = []
            for inv in invoices:
                total = inv.total or 0
                paid = inv.paid_amount or 0
                remaining = total - paid
                data.append({
                    "id": inv.id,
                    "invoice_no": inv.invoice_no,
                    "invoice_date": inv.invoice_date,
                    "customer_name": inv.customer.name if inv.customer else "-",
                    "delivery_no": (
                        inv.delivery_note.delivery_no if inv.delivery_note else ""
                    ),
                    "total_amount": total,
                    "paid_amount": paid,
                    "remaining": remaining,
                    "status": inv.status.value if inv.status else "draft",
                    "due_date": inv.due_date,
                    "currency_code": inv.currency if inv.currency else "TRY",
                    "total_items": len(inv.items) if inv.items else 0,
                })
            self.list_page.load_data(data)
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "InvoiceModule._load_data")
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
                ErrorHandler.log_error(e, "InvoiceModule._get_items")
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
                ErrorHandler.log_error(e, "InvoiceModule._get_customers")
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
                ErrorHandler.log_error(e, "InvoiceModule._get_units")
            return []

    def _show_add_form(self):
        items = self._get_items()
        customers = self._get_customers()
        units = self._get_units()

        form = InvoiceFormPage(
            items=items,
            customers=customers,
            units=units
        )
        form.saved.connect(self._save_invoice)
        form.cancelled.connect(self._back_to_list)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_edit_form(self, invoice_id: int):
        if not self.service:
            return

        try:
            invoice = self.service.get_by_id(invoice_id)
            if invoice:
                items_data = []
                for item in invoice.items:
                    items_data.append({
                        "id": item.id,
                        "item_id": item.item_id,
                        "quantity": item.quantity,
                        "unit_id": item.unit_id,
                        "unit_price": item.unit_price,
                        "discount_rate": item.discount_rate,
                    })

                data = {
                    "id": invoice.id,
                    "invoice_no": invoice.invoice_no,
                    "invoice_date": invoice.invoice_date,
                    "customer_id": invoice.customer_id,
                    "customer_name": (
                        invoice.customer.name if invoice.customer else ""
                    ),
                    "customer_code": (
                        invoice.customer.code if invoice.customer else ""
                    ),
                    "delivery_no": (
                        invoice.delivery_note.note_no
                        if invoice.delivery_note else ""
                    ),
                    "due_date": invoice.due_date,
                    "currency": invoice.currency if invoice.currency else "TRY",
                    "status": invoice.status.value if invoice.status else "draft",
                    "notes": invoice.notes,
                    "items": items_data,
                }

                items = self._get_items()
                customers = self._get_customers()
                units = self._get_units()

                form = InvoiceFormPage(
                    invoice_data=data,
                    items=items,
                    customers=customers,
                    units=units
                )
                form.saved.connect(self._save_invoice)
                form.cancelled.connect(self._back_to_list)
                form.issue_invoice.connect(self._issue_invoice)
                self.stack.addWidget(form)
                self.stack.setCurrentWidget(form)

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "InvoiceModule._show_edit_form")
            print(f"Düzenleme hatası: {e}")
            import traceback
            traceback.print_exc()

    def _show_view(self, invoice_id: int):
        self._show_edit_form(invoice_id)

    def _save_invoice(self, data: dict):
        if not self.service:
            return

        try:
            invoice_id = data.pop("id", None)
            items_data = data.pop("items", [])

            if invoice_id:
                self.service.update(invoice_id, items_data, **data)
                QMessageBox.information(self, "Başarılı", "Fatura güncellendi!")
            else:
                self.service.create(items_data, **data)
                QMessageBox.information(self, "Başarılı", "Yeni fatura oluşturuldu!")

            self._back_to_list()
            self._load_data()

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "InvoiceModule._save_invoice")
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {e}")
            import traceback
            traceback.print_exc()

    def _issue_invoice(self, invoice_id: int):
        """Fatura kes"""
        if not self.service:
            return

        reply = QMessageBox.question(
            self, "Onay",
            "Bu faturayı kesmek istediğinize emin misiniz?\n\n"
            "Bu işlem geri alınamaz.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.issue(invoice_id)
                QMessageBox.information(self, "Başarılı", "Fatura kesildi!")
                self._back_to_list()
                self._load_data()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "InvoiceModule._issue_invoice")
                QMessageBox.critical(self, "Hata", f"Hata: {e}")

    def _record_payment(self, invoice_id: int):
        """Ödeme kaydet"""
        if not self.service:
            return

        try:
            invoice = self.service.get_by_id(invoice_id)
            if not invoice:
                return

            remaining = (invoice.total or 0) - (invoice.paid_amount or 0)
            if remaining <= 0:
                QMessageBox.information(
                    self, "Bilgi", "Bu fatura tamamen ödenmiş."
                )
                return

            dialog = PaymentDialog(remaining, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                payment_data = dialog.get_data()
                self.service.record_payment(invoice_id, payment_data["amount"])
                QMessageBox.information(
                    self, "Başarılı",
                    f"Ödeme kaydedildi!\nTutar: {payment_data['amount']:.2f} TL"
                )
                self._load_data()

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "InvoiceModule._record_payment")
            QMessageBox.critical(self, "Hata", f"Hata: {e}")
            import traceback
            traceback.print_exc()

    def _cancel_invoice(self, invoice_id: int):
        """Fatura iptal et"""
        if not self.service:
            return

        reply = QMessageBox.question(
            self, "Onay",
            "Bu faturayı iptal etmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.cancel(invoice_id)
                QMessageBox.information(self, "Başarılı", "Fatura iptal edildi!")
                self._load_data()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "InvoiceModule._cancel_invoice")
                QMessageBox.critical(self, "Hata", f"Hata: {e}")

    def _delete_invoice(self, invoice_id: int):
        if not self.service:
            return

        try:
            if self.service.delete(invoice_id):
                QMessageBox.information(self, "Başarılı", "Fatura silindi!")
                self._load_data()
            else:
                QMessageBox.warning(
                    self, "Uyarı",
                    "Fatura silinemedi! (Sadece taslak faturalar silinebilir)"
                )
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "InvoiceModule._delete_invoice")
            QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")

    def _back_to_list(self):
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.setCurrentWidget(self.list_page)
            self.stack.removeWidget(current)
            current.deleteLater()
