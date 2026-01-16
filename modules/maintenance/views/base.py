"""
Bakım Modülü - Base Widget
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from database.base import get_session
from modules.maintenance.services import MaintenanceService


class MaintenanceBaseWidget(QWidget):
    """Temel Bakım Widget'ı - Tüm bakım ekranlarının base class'ı"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # Başlık
        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; margin-bottom: 20px;"
        )
        self.layout.addWidget(title_label)

        # Database session ve service
        self.db_session = get_session()
        self.service = MaintenanceService(self.db_session)

    def closeEvent(self, event):
        """Widget kapanırken session'ı kapat"""
        if hasattr(self, 'db_session') and self.db_session:
            self.db_session.close()
        super().closeEvent(event)

    def refresh_data(self):
        """Alt sınıflar tarafından override edilecek"""
        pass
