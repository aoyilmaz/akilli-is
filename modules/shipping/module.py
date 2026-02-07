from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
)

from .views import ShipmentModule
from .views.route_planning import RoutePlanningWidget


class ShippingMainModule(QWidget):
    """Sevkiyat ana modülü - Sadece sevkiyat yönetimi"""

    page_title = "Sevkiyatlar"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab Widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Sevkiyat sayfası
        self.shipment_page = ShipmentModule()
        self.tabs.addTab(self.shipment_page, "Sevkiyat Yönetimi")

        # Rota Planlama sayfası
        self.route_planning_page = RoutePlanningWidget()
        self.tabs.addTab(self.route_planning_page, "Rota ve Taşıyıcı Planlama")

    def _load_data(self):
        """Verileri yükle"""
        if hasattr(self.shipment_page, "_load_data"):
            self.shipment_page._load_data()

        if hasattr(self.route_planning_page, "refresh_data"):
            self.route_planning_page.refresh_data()
