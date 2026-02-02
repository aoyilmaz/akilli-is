"""
Akıllı İş - Workflow Admin Modülü

Workflow tanımlarını yönetmek için ana modül.
Liste ve form sayfaları arasında geçiş yapar.
"""

from PyQt6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout

from .workflow_list import WorkflowListPage
from .workflow_form import WorkflowFormPage


class WorkflowAdminModule(QWidget):
    """Workflow yönetim modülü"""

    page_title = "İş Akışı Yönetimi"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Stack widget for page switching
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Liste sayfası
        self.list_page = WorkflowListPage()
        self.list_page.edit_requested.connect(self._on_edit)
        self.list_page.create_requested.connect(self._on_create)
        self.stack.addWidget(self.list_page)

        # Form sayfası (başlangıçta None)
        self.form_page = None

    def _on_create(self):
        """Yeni workflow oluştur"""
        self._show_form(None)

    def _on_edit(self, workflow_id: int):
        """Workflow düzenle"""
        self._show_form(workflow_id)

    def _show_form(self, workflow_id: int = None):
        """Form sayfasını göster"""
        # Eski formu temizle
        if self.form_page:
            self.stack.removeWidget(self.form_page)
            self.form_page.deleteLater()

        # Yeni form oluştur
        self.form_page = WorkflowFormPage(workflow_id=workflow_id)
        self.form_page.saved.connect(self._on_form_saved)
        self.form_page.cancelled.connect(self._on_form_cancelled)
        self.stack.addWidget(self.form_page)
        self.stack.setCurrentWidget(self.form_page)

    def _on_form_saved(self):
        """Form kaydedildi"""
        self._show_list()
        self.list_page.load_data()

    def _on_form_cancelled(self):
        """Form iptal edildi"""
        self._show_list()

    def _show_list(self):
        """Liste sayfasına dön"""
        self.stack.setCurrentWidget(self.list_page)

        # Formu temizle
        if self.form_page:
            self.stack.removeWidget(self.form_page)
            self.form_page.deleteLater()
            self.form_page = None
