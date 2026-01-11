"""
Akıllı İş - Müşteri Modülü
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox

from .customer_list import CustomerListPage
from .customer_form import CustomerFormPage
from modules.development import ErrorHandler

class CustomerModule(QWidget):
    """Müşteri yönetimi modülü"""

    page_title = "Müşteriler"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # Liste sayfası
        self.list_page = CustomerListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_customer)
        self.list_page.view_clicked.connect(self._show_view)
        self.list_page.refresh_requested.connect(self._load_data)
        self.stack.addWidget(self.list_page)

        layout.addWidget(self.stack)

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_service()
        self._load_data()

    def _ensure_service(self):
        if not self.service:
            try:
                from modules.sales.services import CustomerService
                self.service = CustomerService()
            except Exception as e:
                ErrorHandler.handle_error(
                    e,
                    module='sales',
                    screen='CustomerModule',
                    function='_ensure_service',
                    parent_widget=self,
                    show_message=False
                )

    def _load_data(self):
        if not self.service:
            return

        try:
            customers = self.service.get_all(active_only=False)
            data = []
            for c in customers:
                data.append({
                    "id": c.id,
                    "code": c.code,
                    "name": c.name,
                    "phone": c.phone,
                    "email": c.email,
                    "city": c.city,
                    "payment_term_days": c.payment_term_days,
                    "credit_limit": float(c.credit_limit or 0),
                    "rating": c.rating,
                    "is_active": c.is_active,
                })
            self.list_page.load_data(data)
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='sales',
                screen='CustomerModule',
                function='_load_data',
                parent_widget=self,
                show_message=False
            )
            self.list_page.load_data([])

    def _show_add_form(self):
        form = CustomerFormPage()
        form.saved.connect(self._save_customer)
        form.cancelled.connect(self._back_to_list)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_edit_form(self, customer_id: int):
        if not self.service:
            return

        try:
            customer = self.service.get_by_id(customer_id)
            if customer:
                data = {
                    "id": customer.id,
                    "code": customer.code,
                    "name": customer.name,
                    "short_name": customer.short_name,
                    "tax_number": customer.tax_number,
                    "tax_office": customer.tax_office,
                    "contact_person": customer.contact_person,
                    "phone": customer.phone,
                    "mobile": customer.mobile,
                    "fax": customer.fax,
                    "email": customer.email,
                    "website": customer.website,
                    "address": customer.address,
                    "city": customer.city,
                    "district": customer.district,
                    "postal_code": customer.postal_code,
                    "country": customer.country,
                    "payment_term_days": customer.payment_term_days,
                    "credit_limit": float(customer.credit_limit or 0),
                    "currency": customer.currency if customer.currency else "TRY",
                    "rating": customer.rating,
                    "bank_name": customer.bank_name,
                    "bank_branch": customer.bank_branch,
                    "bank_account_no": customer.bank_account_no,
                    "iban": customer.iban,
                    "notes": customer.notes,
                }
                form = CustomerFormPage(data)
                form.saved.connect(self._save_customer)
                form.cancelled.connect(self._back_to_list)
                self.stack.addWidget(form)
                self.stack.setCurrentWidget(form)
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='sales',
                screen='CustomerModule',
                function='_show_edit_form',
                parent_widget=self
            )

    def _show_view(self, customer_id: int):
        self._show_edit_form(customer_id)

    def _save_customer(self, data: dict):
        if not self.service:
            return

        try:
            customer_id = data.pop("id", None)

            # Kod yoksa otomatik oluştur
            if not data.get("code"):
                data["code"] = self.service.generate_code()

            if customer_id:
                self.service.update(customer_id, **data)
                QMessageBox.information(self, "Başarılı", "Müşteri güncellendi!")
            else:
                self.service.create(**data)
                QMessageBox.information(self, "Başarılı", "Yeni müşteri oluşturuldu!")

            self._back_to_list()
            self._load_data()

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='sales',
                screen='CustomerModule',
                function='_save_customer',
                parent_widget=self
            )

    def _delete_customer(self, customer_id: int):
        if not self.service:
            return

        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu müşteriyi silmek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            if self.service.delete(customer_id):
                QMessageBox.information(self, "Başarılı", "Müşteri silindi!")
                self._load_data()
            else:
                QMessageBox.warning(self, "Uyarı", "Müşteri silinemedi!")
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='sales',
                screen='CustomerModule',
                function='_delete_customer',
                parent_widget=self
            )

    def _back_to_list(self):
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.setCurrentWidget(self.list_page)
            self.stack.removeWidget(current)
            current.deleteLater()
