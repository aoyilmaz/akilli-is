"""
Akıllı İş - Sevkiyat Ana Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
)

from .views import VehicleModule, DriverModule, ShipmentModule


class ShippingMainModule(QWidget):
    """Sevkiyat ana modülü - tab yapısı ile araç, sürücü ve sevkiyat yönetimi"""

    page_title = "Sevkiyat"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab widget
        self.tabs = QTabWidget()

        # Sevkiyatlar tab'ı (ana sayfa)
        self.shipment_page = ShipmentModule()
        self.tabs.addTab(self.shipment_page, "📦 Sevkiyatlar")

        # Araçlar tab'ı
        self.vehicle_page = VehicleModule()
        self.tabs.addTab(self.vehicle_page, "🚛 Araçlar")

        # Sürücüler tab'ı
        self.driver_page = DriverModule()
        self.tabs.addTab(self.driver_page, "👤 Sürücüler")

        self.tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self.tabs)

    def _on_tab_changed(self, index: int):
        """Tab değiştiğinde ilgili sayfayı yenile"""
        current_widget = self.tabs.currentWidget()
        if hasattr(current_widget, '_load_data'):
            current_widget._load_data()
