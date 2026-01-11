"""
Akilli Is - Tedarikci Performans Raporu Modulu (Bagimsiz)
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox

from modules.reports.services import ReportsService
from modules.reports.views.supplier_performance import SupplierPerformancePage

class SupplierPerformanceModule(QWidget):
    """Tedarikci performans raporu modulu - bagimsiz calisir"""

    page_title = "Tedarikci Performans"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.reports_service = None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.page = SupplierPerformancePage()
        self.page.refresh_requested.connect(self.load_data)
        layout.addWidget(self.page)

    def _get_service(self):
        if self.reports_service is None:
            self.reports_service = ReportsService()
        return self.reports_service

    def _close_service(self):
        if self.reports_service:
            self.reports_service.close()
            self.reports_service = None

    def load_data(self):
        """Tedarikci performans raporunu yukle"""
        try:
            service = self._get_service()
            data = service.get_supplier_performance()
            self.page.load_data(data)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Uyari",
                f"Tedarikci performans raporu yuklenirken hata:\n{str(e)}",
            )
        finally:
            self._close_service()
