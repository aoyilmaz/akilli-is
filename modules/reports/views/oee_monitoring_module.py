"""
Akilli Is - Canli OEE Izleme Modulu (Wrapper)
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from modules.reports.services import ReportsService
from modules.reports.views.oee_monitoring import OEEMonitoringPage


class OEEMonitoringModule(QWidget):
    """Canli OEE izleme modulu - bagimsiz calisir"""

    page_title = "Canli OEE İzleme"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.reports_service = None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.page = OEEMonitoringPage()
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
        """Canli OEE verilerini yukle"""
        try:
            service = self._get_service()
            data = service.get_realtime_oee()
            self.page.update_data(data)
        except Exception as e:
            # Canli ekranda hata diyologu yerine loglamak daha iyi olabilir
            # ama mevcut yapiya uyum sagliyoruz.
            print(f"OEE Izleme hatasi: {e}")
        finally:
            # Singleton session kullanmadigimiz icin her seferinde kapatmiyoruz
            # (veya service icinde manage ediliyor demektir)
            # production_oee_module'de her seferinde kapatiyor, biz de kapatalim.
            self._close_service()

    def closeEvent(self, event):
        self._close_service()
        super().closeEvent(event)
