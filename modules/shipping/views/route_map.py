"""
Akıllı İş - Rota Planlama: Harita Widget'ı (Placeholder)
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QFont


class RouteMapWidget(QWidget):
    """Harita görselleştirmesi için yer tutucu."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Placeholder içeriği
        label = QLabel("Harita Görünümü\n(Gelecek Versiyon)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #888; font-size: 16px; font-weight: bold;")
        self.layout.addWidget(label)

        self.setStyleSheet("background-color: #f9f9f9; border: 1px dashed #ccc;")

    def paintEvent(self, event):
        """Basit bir şematik çizim (Opsiyonel)."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Arkaplan
        painter.fillRect(self.rect(), QColor(249, 249, 249))

        # Basit bir yol çizimi (Dekoratif)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(220, 220, 220))

        # Rastgele noktalar ve yollar (Statik)
        w, h = self.width(), self.height()

        # Merkez Depo
        painter.setBrush(QColor(100, 181, 246))
        painter.drawEllipse(w // 2 - 10, h // 2 - 10, 20, 20)

        # Yollar
        painter.setPen(QColor(200, 200, 200))
        # ... (Daha sonra detaylandırılabilir)
