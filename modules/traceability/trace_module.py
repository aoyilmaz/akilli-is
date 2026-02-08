"""
Akıllı İş - İzlenebilirlik Ana Modülü
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from modules.traceability.views.lot_list import LotListPage
from modules.traceability.views.serial_list import SerialListPage


class TraceabilityModule(QWidget):
    """
    İzlenebilirlik modülü ana konteynırı.
    Lot ve Seri Numarası takibi sekmelerini barındırır.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Sekmeli yapı
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            "QTabBar::tab { height: 40px; padding: 0 20px; font-weight: 500; }"
        )

        # Sayfaları oluştur
        self.lot_page = LotListPage()
        self.serial_page = SerialListPage()

        # Sekmelere ekle
        self.tabs.addTab(self.lot_page, "Lot / Parti Yönetimi")
        self.tabs.addTab(self.serial_page, "Seri Numarası Takibi")

        layout.addWidget(self.tabs)

    def refresh_all(self):
        """Tüm sekmeleri yenile"""
        self.lot_page.load_data()
        self.serial_page.load_data()
