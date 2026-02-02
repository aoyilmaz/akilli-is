"""
Akıllı İş - Mini Sparkline Widget

Son 7 gün trendi gösteren kompakt çizgi grafik bileşeni.
Dashboard widget'larına gömülebilir.
"""

from typing import List, Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QPen, QPainterPath, QLinearGradient,
    QColor, QBrush
)

from config.styles import COLORS


class MiniSparkline(QWidget):
    """
    Kompakt sparkline grafik bileşeni.

    Trend verilerini gradient dolgulu çizgi grafik olarak gösterir.
    StatWidget veya diğer widget'lara gömülebilir.
    """

    def __init__(
        self,
        data: Optional[List[float]] = None,
        color: Optional[str] = None,
        show_endpoint: bool = True,
        parent: Optional[QWidget] = None
    ):
        """
        Args:
            data: Gösterilecek veri listesi
            color: Çizgi rengi (varsayılan: primary)
            show_endpoint: Son noktada dot gösterilsin mi
            parent: Parent widget
        """
        super().__init__(parent)
        self._data = data or []
        self._color = color or COLORS['primary']
        self._show_endpoint = show_endpoint

        # Boyut ayarları
        self.setFixedHeight(40)
        self.setMinimumWidth(80)

        # Anti-aliasing için
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_data(self, data: List[float]):
        """
        Sparkline verisini günceller.

        Args:
            data: Yeni veri listesi
        """
        self._data = data
        self.update()

    def set_color(self, color: str):
        """
        Çizgi rengini değiştirir.

        Args:
            color: Yeni renk (hex)
        """
        self._color = color
        self.update()

    def paintEvent(self, event):
        """Sparkline çizimi"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._data or len(self._data) < 2:
            self._draw_empty_state(painter)
            return

        # Veriyi normalize et
        min_val = min(self._data)
        max_val = max(self._data)
        range_val = max_val - min_val or 1

        # Padding
        padding = 4
        width = self.width() - (padding * 2)
        height = self.height() - (padding * 2)

        # Noktaları hesapla
        points: List[QPointF] = []
        for i, val in enumerate(self._data):
            x = padding + (i * width / (len(self._data) - 1))
            # Y eksenini ters çevir (yukarı = yüksek değer)
            normalized = (val - min_val) / range_val
            y = padding + height - (normalized * height)
            points.append(QPointF(x, y))

        # Gradient dolgulu alan çiz
        self._draw_fill(painter, points, height, padding)

        # Çizgiyi çiz
        self._draw_line(painter, points)

        # Son nokta (endpoint dot)
        if self._show_endpoint and points:
            self._draw_endpoint(painter, points[-1])

    def _draw_empty_state(self, painter: QPainter):
        """Veri yokken boş durum çiz"""
        painter.setPen(QPen(QColor(COLORS['text_muted']), 1))
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "—"
        )

    def _draw_fill(
        self,
        painter: QPainter,
        points: List[QPointF],
        height: float,
        padding: float
    ):
        """Gradient dolgulu alan çiz"""
        # Path oluştur
        fill_path = QPainterPath()
        fill_path.moveTo(points[0].x(), padding + height)

        for point in points:
            fill_path.lineTo(point)

        fill_path.lineTo(points[-1].x(), padding + height)
        fill_path.closeSubpath()

        # Gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        base_color = QColor(self._color)
        gradient.setColorAt(0, QColor(
            base_color.red(),
            base_color.green(),
            base_color.blue(),
            80  # %30 opacity
        ))
        gradient.setColorAt(1, QColor(
            base_color.red(),
            base_color.green(),
            base_color.blue(),
            0  # Tamamen şeffaf
        ))

        painter.fillPath(fill_path, QBrush(gradient))

    def _draw_line(self, painter: QPainter, points: List[QPointF]):
        """Ana çizgiyi çiz"""
        pen = QPen(QColor(self._color), 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        # Çizgi path'i
        line_path = QPainterPath()
        line_path.moveTo(points[0])

        for point in points[1:]:
            line_path.lineTo(point)

        painter.drawPath(line_path)

    def _draw_endpoint(self, painter: QPainter, point: QPointF):
        """Son noktada dot çiz"""
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(self._color)))
        painter.drawEllipse(point, 4, 4)

        # İç beyaz nokta
        painter.setBrush(QBrush(QColor(COLORS['bg_card'])))
        painter.drawEllipse(point, 2, 2)


class TrendSparkline(MiniSparkline):
    """
    Trend göstergeli sparkline.

    Pozitif trend yeşil, negatif trend kırmızı olarak gösterilir.
    """

    def __init__(
        self,
        data: Optional[List[float]] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(data=data, parent=parent)
        self._auto_color = True

    def set_data(self, data: List[float]):
        """Veriyi güncelle ve trend rengini ayarla"""
        self._data = data

        if self._auto_color and len(data) >= 2:
            # İlk ve son değeri karşılaştır
            if data[-1] > data[0]:
                self._color = COLORS['success']  # Yeşil - artış
            elif data[-1] < data[0]:
                self._color = COLORS['danger']   # Kırmızı - düşüş
            else:
                self._color = COLORS['text_muted']  # Gri - değişim yok

        self.update()
