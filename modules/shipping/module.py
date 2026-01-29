"""
Akıllı İş - Sevkiyat Ana Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)

from .views import ShipmentModule


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

        # Sevkiyat sayfası
        self.shipment_page = ShipmentModule()
        layout.addWidget(self.shipment_page)

    def _load_data(self):
        """Verileri yükle"""
        if hasattr(self.shipment_page, "_load_data"):
            self.shipment_page._load_data()
