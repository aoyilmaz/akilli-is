"""
Akıllı İş - Rota Planlama: Sevkiyat Havuzu Widget'ı
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QAbstractItemView,
    QLineEdit,
)
from PyQt6.QtCore import Qt, QMimeData, QSize
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QColor, QFont

from database.models.shipping import Shipment, ShipmentStatus


class ShipmentPoolWidget(QWidget):
    """Atanmamış sevkiyatların listelendiği ve sürüklenebildiği panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Başlık ve Filtre
        self.header_layout = QVBoxLayout()
        self.title = QLabel("Bekleyen Sevkiyatlar")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara (Sevkiyat No, Bölge...)")
        self.header_layout.addWidget(self.title)
        self.header_layout.addWidget(self.search_input)
        self.layout.addLayout(self.header_layout)

        # Liste
        self.list_widget = QListWidget()
        self.list_widget.setDragEnabled(True)
        self.list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.list_widget.setStyleSheet(
            """
            QListWidget::item {
                border-bottom: 1px solid #eee;
                padding: 10px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #000;
            }
            """
        )
        self.layout.addWidget(self.list_widget)

        # Events
        self.search_input.textChanged.connect(self.filter_shipments)

        # Data
        self.shipments = []

    def load_shipments(self, shipments):
        """Sevkiyat listesini yükler."""
        self.shipments = shipments
        self.filter_shipments()

    def filter_shipments(self):
        """Filtreleme uygular ve listeyi yeniler."""
        search_text = self.search_input.text().lower()
        self.list_widget.clear()

        for shipment in self.shipments:
            # Şimdilik sadece APPROVED olan sevkiyatları gösterelim
            # veya henüz bir rotaya atanmamış olanları (bu kontrol serviste yapılmalı)
            if (
                shipment.status != ShipmentStatus.PLANLANDI
            ):  # Örn: Sadece planlandı olanlar
                # Demo amaçlı hepsini gösterelim veya servisten filtreli gelir
                pass

            # Arama filtresi
            text_repr = f"{shipment.shipment_no} - {shipment.shipment_date}".lower()
            if search_text and search_text not in text_repr:
                continue

            item = QListWidgetItem()
            # Custom widget veya sadece text
            item.setData(Qt.ItemDataRole.UserRole, shipment.id)
            item.setText(
                f"📦 {shipment.shipment_no}\n📅 {shipment.shipment_date}\n📍 {self._get_destinations(shipment)}"
            )
            self.list_widget.addItem(item)

    def _get_destinations(self, shipment):
        """Sevkiyatın gideceği yerleri özetler."""
        # Burada irsaliyelerden gidilecek yerleri çekmek lazım
        # Şimdilik placeholder
        return "Çeşitli Noktalar"

    def startDrag(self, supportedActions):
        """Drag işlemini başlatır."""
        item = self.list_widget.currentItem()
        if not item:
            return

        shipment_id = item.data(Qt.ItemDataRole.UserRole)
        shipment_no = item.text().split("\n")[0]  # İlk satırı al

        mime_data = QMimeData()
        mime_data.setText(str(shipment_id))
        mime_data.setData("application/x-shipment-id", str(shipment_id).encode())

        drag = QDrag(self)
        drag.setMimeData(mime_data)

        # Pixmap oluştur (Sürüklerken görünen hayalet resim)
        pixmap = QPixmap(200, 50)
        pixmap.fill(QColor(255, 255, 255, 0))  # Transparent
        painter = QPainter(pixmap)
        painter.setBrush(QColor(240, 240, 240))
        painter.setPen(Qt.PenStyle.SolidLine)
        painter.drawRect(0, 0, 199, 49)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, shipment_no)
        painter.end()

        drag.setPixmap(pixmap)
        drag.setHotSpot(QSize(100, 25).toPoint())

        drag.exec(Qt.DropAction.CopyAction)
