from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from .einvoice_list import EInvoiceListPage
from modules.einvoice.services.base import EInvoiceService


class EInvoiceModule(QWidget):
    page_title = "e-Faturalar"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()

        self.list_page = EInvoiceListPage()
        self.list_page.send_clicked.connect(self._on_send_clicked)
        self.list_page.status_check_clicked.connect(self._on_check_status_clicked)
        self.list_page.xml_clicked.connect(self._on_xml_clicked)
        self.list_page.html_clicked.connect(self._on_html_clicked)
        self.list_page.refresh_requested.connect(self._load_data)

        self.stack.addWidget(self.list_page)
        layout.addWidget(self.stack)

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_service()
        self._load_data()

    def _ensure_service(self):
        if not self.service:
            self.service = EInvoiceService()

    def _load_data(self):
        if not self.service:
            return

        try:
            invoices = self.service.get_all()
            data = [inv.to_dict() for inv in invoices]
            self.list_page.load_data(data)
        except Exception as e:
            print(f"Error loading e-invoices: {e}")
            import traceback

            traceback.print_exc()
            self.list_page.load_data([])

    def _on_send_clicked(self, uuid: str):
        try:
            result = self.service.send_invoice(uuid)
            if result.get("success"):
                QMessageBox.information(self, "Başarılı", "Fatura gönderildi.")
            else:
                QMessageBox.critical(
                    self, "Hata", f"Gönderim hatası: {result.get('error')}"
                )
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İşlem hatası: {e}")

    def _on_check_status_clicked(self, uuid: str):
        # TODO: Implement status check in service
        QMessageBox.information(self, "Bilgi", "Durum sorgulama henüz aktif değil.")

    def _on_xml_clicked(self, uuid: str):
        try:
            xml_content = self.service.generate_xml(uuid)
            from .preview_dialog import PreviewDialog

            dialog = PreviewDialog(xml_content, title="XML Önizleme")
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"XML oluşturma hatası: {e}")

    def _on_html_clicked(self, uuid: str):
        try:
            html_content = self.service.get_html(uuid)
            from .preview_dialog import PreviewDialog

            dialog = PreviewDialog(html_content, title="Fatura Önizleme", is_html=True)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"HTML oluşturma hatası: {e}")
