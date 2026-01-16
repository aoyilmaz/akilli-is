"""
Akıllı İş - CRM Modülü
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from .lead_list import LeadListPage
from .lead_form import LeadFormPage
from modules.development import ErrorHandler
from database.base import get_session
from modules.crm.services import CRMService


class CRMModule(QWidget):
    """CRM Ana Modülü (Lead Yönetimi)"""

    page_title = "CRM"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = get_session()
        self.service = CRMService(self.session)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()

        # Liste Sayfası
        self.list_page = LeadListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_lead)
        self.list_page.convert_clicked.connect(self._convert_lead)
        self.list_page.refresh_requested.connect(self._load_data)

        self.stack.addWidget(self.list_page)
        layout.addWidget(self.stack)

    def showEvent(self, event):
        super().showEvent(event)
        self._load_data()

    def _load_data(self):
        try:
            leads = self.service.list_leads()
            # Model objelerini dict'e çevirip UI'a gönder
            data = [lead.to_dict() for lead in leads]
            self.list_page.load_data(data)
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module="crm",
                screen="CRMModule",
                function="_load_data",
                parent_widget=self,
            )

    def _show_add_form(self):
        form = LeadFormPage()
        form.saved.connect(self._save_lead)
        form.cancelled.connect(self._back_to_list)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_edit_form(self, lead_id: int):
        try:
            lead = self.service.get_lead(lead_id)
            if lead:
                form = LeadFormPage(lead.to_dict())
                form.saved.connect(self._save_lead)
                form.cancelled.connect(self._back_to_list)
                self.stack.addWidget(form)
                self.stack.setCurrentWidget(form)
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module="crm",
                screen="CRMModule",
                function="_show_edit_form",
                parent_widget=self,
            )

    def _save_lead(self, data: dict):
        try:
            lead_id = data.pop("id", None)
            if lead_id:
                self.service.update_lead(lead_id, data)
                QMessageBox.information(self, "Başarılı", "Aday müşteri güncellendi!")
            else:
                self.service.create_lead(data)
                QMessageBox.information(
                    self, "Başarılı", "Yeni aday müşteri oluşturuldu!"
                )

            self._back_to_list()
            self._load_data()

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module="crm",
                screen="CRMModule",
                function="_save_lead",
                parent_widget=self,
            )

    def _delete_lead(self, lead_id: int):
        try:
            # Şu an servis katmanında delete metodu yok, eklememiz gerekebilir
            # Şimdilik basic SQL delete yapabilir veya soft delete
            # self.service.delete_lead(lead_id)
            # Servis katmanında delete olmadığı için basitçe session üzerinden siliyorum
            from database.models.crm import Lead

            lead = self.session.query(Lead).get(lead_id)
            if lead:
                self.session.delete(lead)
                self.session.commit()
                QMessageBox.information(self, "Başarılı", "Kayıt silindi.")
                self._load_data()
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module="crm",
                screen="CRMModule",
                function="_delete_lead",
                parent_widget=self,
            )

    def _convert_lead(self, lead_id: int):
        reply = QMessageBox.question(
            self,
            "Dönüştürme Onayı",
            "Bu adayı Müşteriye dönüştürmek istediğinize emin misiniz?\nSatış modülünde yeni bir müşteri kartı açılacak.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            customer = self.service.convert_lead_to_customer(lead_id)
            if customer:
                QMessageBox.information(
                    self,
                    "Başarılı",
                    f"Müşteri oluşturuldu:\n{customer.name}\n({customer.code})",
                )
                self._load_data()
            else:
                QMessageBox.warning(
                    self, "Uyarı", "Dönüştürme başarısız veya aday zaten dönüştürülmüş."
                )
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module="crm",
                screen="CRMModule",
                function="_convert_lead",
                parent_widget=self,
            )

    def _back_to_list(self):
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.setCurrentWidget(self.list_page)
            self.stack.removeWidget(current)
            current.deleteLater()
