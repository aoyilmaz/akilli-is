"""
Akilli Is - Tahsilat Modulu
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox

from .receipt_list import ReceiptListPage
from .receipt_form import ReceiptFormPage

try:
    from modules.development.services import ErrorHandler
except ImportError:
    ErrorHandler = None


class ReceiptModule(QWidget):
    """Tahsilat modulu"""

    page_title = "Tahsilatlar"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.customer_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # Liste sayfasi
        self.list_page = ReceiptListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.view_clicked.connect(self._show_view)
        self.list_page.delete_clicked.connect(self._cancel_receipt)
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
                from modules.finance.services import ReceiptService
                self.service = ReceiptService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "ReceiptModule._ensure_services")
                print(f"Tahsilat servisi yukleme hatasi: {e}")

        if not self.customer_service:
            try:
                from modules.sales.services import CustomerService
                self.customer_service = CustomerService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "ReceiptModule._ensure_services")
                print(f"Musteri servisi yukleme hatasi: {e}")

    def _load_data(self):
        if not self.service:
            return

        try:
            filter_data = self.list_page.get_filter_data()
            receipts = self.service.get_all(
                date_from=filter_data.get("date_from"),
                date_to=filter_data.get("date_to"),
                status=filter_data.get("status")
            )

            data = []
            for r in receipts:
                data.append({
                    "id": r.id,
                    "receipt_no": r.receipt_no,
                    "receipt_date": r.receipt_date,
                    "customer_id": r.customer_id,
                    "customer_name": r.customer.name if r.customer else "",
                    "amount": r.amount,
                    "payment_method": r.payment_method.value if r.payment_method else "",
                    "status": r.status.value if r.status else "",
                    "description": r.description,
                })
            self.list_page.load_data(data)

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "ReceiptModule._load_data")
            print(f"Veri yukleme hatasi: {e}")
            import traceback
            traceback.print_exc()
            self.list_page.load_data([])

    def _get_customers(self) -> list:
        """Musteri listesini getir"""
        if not self.customer_service:
            return []
        try:
            customers = self.customer_service.get_all()
            return [{"id": c.id, "code": c.code, "name": c.name} for c in customers]
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "ReceiptModule._get_customers")
            return []

    def _get_open_invoices(self) -> list:
        """Acik faturalari getir"""
        if not self.service:
            return []
        try:
            # Tum musterilerin acik faturalarini al
            invoices = []
            customers = self._get_customers()
            for cust in customers:
                open_invs = self.service.get_customer_open_invoices(cust["id"])
                for inv in open_invs:
                    invoices.append({
                        "id": inv.id,
                        "invoice_no": inv.invoice_no,
                        "invoice_date": inv.invoice_date,
                        "customer_id": inv.customer_id,
                        "total_amount": inv.total_amount,
                        "paid_amount": inv.paid_amount,
                    })
            return invoices
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "ReceiptModule._get_open_invoices")
            return []

    def _show_add_form(self):
        customers = self._get_customers()
        open_invoices = self._get_open_invoices()

        # Otomatik no olustur
        receipt_no = self.service.generate_receipt_no() if self.service else "THS0001"

        form = ReceiptFormPage(
            receipt_data={"receipt_no": receipt_no},
            customers=customers,
            open_invoices=open_invoices
        )
        form.saved.connect(self._save_receipt)
        form.cancelled.connect(self._back_to_list)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_view(self, receipt_id: int):
        if not self.service:
            return

        try:
            receipt = self.service.get_by_id(receipt_id)
            if receipt:
                data = {
                    "id": receipt.id,
                    "receipt_no": receipt.receipt_no,
                    "receipt_date": receipt.receipt_date,
                    "customer_id": receipt.customer_id,
                    "amount": receipt.amount,
                    "payment_method": receipt.payment_method.value if receipt.payment_method else "cash",
                    "bank_name": receipt.bank_name,
                    "check_no": receipt.check_no,
                    "check_date": receipt.check_date,
                    "description": receipt.description,
                }

                customers = self._get_customers()
                open_invoices = self._get_open_invoices()

                form = ReceiptFormPage(
                    receipt_data=data,
                    customers=customers,
                    open_invoices=open_invoices
                )
                form.saved.connect(self._save_receipt)
                form.cancelled.connect(self._back_to_list)
                self.stack.addWidget(form)
                self.stack.setCurrentWidget(form)

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "ReceiptModule._show_view")
            print(f"Goruntuleme hatasi: {e}")

    def _save_receipt(self, data: dict):
        if not self.service:
            return

        try:
            receipt_id = data.pop("id", None)
            allocations = data.pop("allocations", [])

            if receipt_id:
                # Duzenleme desteklenmiyor, sadece goruntulenebilir
                QMessageBox.information(
                    self, "Bilgi",
                    "Tahsilatlar duzenlenemez. Yeni bir tahsilat olusturun."
                )
                return
            else:
                # Yeni tahsilat
                self.service.create(
                    customer_id=data["customer_id"],
                    amount=data["amount"],
                    payment_method=data["payment_method"],
                    receipt_date=data.get("receipt_date"),
                    invoice_allocations=allocations,
                    bank_name=data.get("bank_name"),
                    check_no=data.get("check_no"),
                    check_date=data.get("check_date"),
                    description=data.get("description"),
                )
                QMessageBox.information(
                    self, "Basarili", "Tahsilat kaydedildi!"
                )

            self._back_to_list()
            self._load_data()

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "ReceiptModule._save_receipt")
            QMessageBox.critical(self, "Hata", f"Kaydetme hatasi: {e}")
            import traceback
            traceback.print_exc()

    def _cancel_receipt(self, receipt_id: int):
        if not self.service:
            return

        try:
            self.service.cancel(receipt_id)
            QMessageBox.information(
                self, "Basarili", "Tahsilat iptal edildi!"
            )
            self._load_data()

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "ReceiptModule._cancel_receipt")
            QMessageBox.critical(self, "Hata", f"Iptal hatasi: {e}")

    def _back_to_list(self):
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.setCurrentWidget(self.list_page)
            self.stack.removeWidget(current)
            current.deleteLater()
