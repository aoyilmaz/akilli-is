"""
Akilli Is - Odeme Modulu
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox

from .payment_list import PaymentListPage
from .payment_form import PaymentFormPage

try:
    from modules.development.services import ErrorHandler
except ImportError:
    ErrorHandler = None


class PaymentModule(QWidget):
    """Odeme modulu"""

    page_title = "Odemeler"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.supplier_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # Liste sayfasi
        self.list_page = PaymentListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.view_clicked.connect(self._show_view)
        self.list_page.delete_clicked.connect(self._cancel_payment)
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
                from modules.finance.services import PaymentService
                self.service = PaymentService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "PaymentModule._ensure_services")
                print(f"Odeme servisi yukleme hatasi: {e}")

        if not self.supplier_service:
            try:
                from modules.purchasing.services import SupplierService
                self.supplier_service = SupplierService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "PaymentModule._ensure_services")
                print(f"Tedarikci servisi yukleme hatasi: {e}")

    def _load_data(self):
        if not self.service:
            return

        try:
            filter_data = self.list_page.get_filter_data()
            payments = self.service.get_all(
                date_from=filter_data.get("date_from"),
                date_to=filter_data.get("date_to"),
                status=filter_data.get("status")
            )

            data = []
            for p in payments:
                data.append({
                    "id": p.id,
                    "payment_no": p.payment_no,
                    "payment_date": p.payment_date,
                    "supplier_id": p.supplier_id,
                    "supplier_name": p.supplier.name if p.supplier else "",
                    "amount": p.amount,
                    "payment_method": p.payment_method.value if p.payment_method else "",
                    "status": p.status.value if p.status else "",
                    "description": p.description,
                })
            self.list_page.load_data(data)

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "PaymentModule._load_data")
            print(f"Veri yukleme hatasi: {e}")
            import traceback
            traceback.print_exc()
            self.list_page.load_data([])

    def _get_suppliers(self) -> list:
        """Tedarikci listesini getir"""
        if not self.supplier_service:
            return []
        try:
            suppliers = self.supplier_service.get_all()
            return [{"id": s.id, "code": s.code, "name": s.name} for s in suppliers]
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "PaymentModule._get_suppliers")
            return []

    def _show_add_form(self):
        suppliers = self._get_suppliers()

        # Otomatik no olustur
        payment_no = self.service.generate_payment_no() if self.service else "ODM0001"

        form = PaymentFormPage(
            payment_data={"payment_no": payment_no},
            suppliers=suppliers
        )
        form.saved.connect(self._save_payment)
        form.cancelled.connect(self._back_to_list)
        form.supplier_balance_requested.connect(lambda sid: self._load_supplier_balance(form, sid))
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _load_supplier_balance(self, form, supplier_id: int):
        """Tedarikci borcunu yukle ve forma gonder"""
        try:
            from modules.finance.services import AccountTransactionService
            tx_service = AccountTransactionService()
            balance = tx_service.get_supplier_balance(supplier_id)
            form.set_supplier_balance(balance)
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "PaymentModule._load_supplier_balance")
            from decimal import Decimal
            form.set_supplier_balance(Decimal(0))

    def _show_view(self, payment_id: int):
        if not self.service:
            return

        try:
            payment = self.service.get_by_id(payment_id)
            if payment:
                data = {
                    "id": payment.id,
                    "payment_no": payment.payment_no,
                    "payment_date": payment.payment_date,
                    "supplier_id": payment.supplier_id,
                    "amount": payment.amount,
                    "payment_method": payment.payment_method.value if payment.payment_method else "cash",
                    "bank_name": payment.bank_name,
                    "check_no": payment.check_no,
                    "check_date": payment.check_date,
                    "description": payment.description,
                }

                suppliers = self._get_suppliers()

                form = PaymentFormPage(
                    payment_data=data,
                    suppliers=suppliers
                )
                form.saved.connect(self._save_payment)
                form.cancelled.connect(self._back_to_list)
                form.supplier_balance_requested.connect(lambda sid: self._load_supplier_balance(form, sid))
                self.stack.addWidget(form)
                self.stack.setCurrentWidget(form)

                # Mevcut tedarikci icin bakiyeyi yukle
                if payment.supplier_id:
                    self._load_supplier_balance(form, payment.supplier_id)

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "PaymentModule._show_view")
            print(f"Goruntuleme hatasi: {e}")

    def _save_payment(self, data: dict):
        if not self.service:
            return

        try:
            payment_id = data.pop("id", None)

            if payment_id:
                # Duzenleme desteklenmiyor
                QMessageBox.information(
                    self, "Bilgi",
                    "Odemeler duzenlenemez. Yeni bir odeme olusturun."
                )
                return
            else:
                # Yeni odeme
                self.service.create(
                    supplier_id=data["supplier_id"],
                    amount=data["amount"],
                    payment_method=data["payment_method"],
                    payment_date=data.get("payment_date"),
                    bank_name=data.get("bank_name"),
                    check_no=data.get("check_no"),
                    check_date=data.get("check_date"),
                    description=data.get("description"),
                )
                QMessageBox.information(
                    self, "Basarili", "Odeme kaydedildi!"
                )

            self._back_to_list()
            self._load_data()

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "PaymentModule._save_payment")
            QMessageBox.critical(self, "Hata", f"Kaydetme hatasi: {e}")
            import traceback
            traceback.print_exc()

    def _cancel_payment(self, payment_id: int):
        if not self.service:
            return

        try:
            self.service.cancel(payment_id)
            QMessageBox.information(
                self, "Basarili", "Odeme iptal edildi!"
            )
            self._load_data()

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "PaymentModule._cancel_payment")
            QMessageBox.critical(self, "Hata", f"Iptal hatasi: {e}")

    def _back_to_list(self):
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.setCurrentWidget(self.list_page)
            self.stack.removeWidget(current)
            current.deleteLater()
