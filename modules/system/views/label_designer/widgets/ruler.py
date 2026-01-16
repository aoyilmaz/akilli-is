"""
RulerWidget - Cetvel widget'ları
"""

from typing import Optional

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

from ..unit_converter import UnitConverter


class RulerWidget(QWidget):
    """
    Temel cetvel widget'ı.

    Alt sınıflar:
    - HorizontalRuler
    - VerticalRuler
    """

    def __init__(
        self,
        orientation: Qt.Orientation,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._orientation = orientation
        self._zoom_level = 1.0
        self._offset = 0.0  # Scroll offset (px)
        self._label_size_mm = 100.0  # Etiket boyutu
        self._dpi = UnitConverter.SCREEN_DPI
        self._cursor_pos: Optional[float] = None  # Fare pozisyonu (mm)

        # Boyut
        if orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(25)
            self.setMinimumWidth(100)
        else:
            self.setFixedWidth(25)
            self.setMinimumHeight(100)

        # Stil
        self.setStyleSheet("background-color: #f5f5f5;")

    def set_zoom(self, level: float):
        """Zoom seviyesini ayarlar"""
        self._zoom_level = level
        self.update()

    def set_offset(self, offset: float):
        """Scroll offset'i ayarlar (piksel)"""
        self._offset = offset
        self.update()

    def set_label_size(self, size_mm: float):
        """Etiket boyutunu ayarlar (mm)"""
        self._label_size_mm = size_mm
        self.update()

    def set_cursor_position(self, pos_mm: Optional[float]):
        """Fare pozisyonunu ayarlar (mm)"""
        self._cursor_pos = pos_mm
        self.update()

    def paintEvent(self, event):
        """Cetveli çizer"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Arka plan
        painter.fillRect(self.rect(), QColor("#f5f5f5"))

        # Kenarlık
        painter.setPen(QPen(QColor("#cccccc"), 1))
        if self._orientation == Qt.Orientation.Horizontal:
            painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        else:
            painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())

        # Ölçek çizgileri ve etiketler
        self._draw_ruler_marks(painter)

        # Fare pozisyonu göstergesi
        if self._cursor_pos is not None:
            self._draw_cursor_indicator(painter)

        painter.end()

    def _draw_ruler_marks(self, painter: QPainter):
        """Cetvel işaretlerini çizer"""
        painter.setPen(QPen(QColor("#666666"), 1))
        font = QFont("Arial", 8)
        painter.setFont(font)

        # mm başına piksel
        px_per_mm = UnitConverter.mm_to_px(1, self._dpi) * self._zoom_level

        # Görünür aralık
        if self._orientation == Qt.Orientation.Horizontal:
            total_px = self.width()
        else:
            total_px = self.height()

        # Ölçek aralığı (zoom'a göre ayarla)
        if self._zoom_level >= 2:
            major_interval = 5  # Her 5mm'de bir büyük işaret
            minor_interval = 1  # Her 1mm'de bir küçük işaret
        elif self._zoom_level >= 1:
            major_interval = 10
            minor_interval = 5
        else:
            major_interval = 20
            minor_interval = 10

        # İşaretleri çiz
        mm = 0
        while mm <= self._label_size_mm:
            px = (mm * px_per_mm) - self._offset

            if px < 0 or px > total_px:
                mm += 1
                continue

            is_major = mm % major_interval == 0
            is_minor = mm % minor_interval == 0

            if is_major:
                self._draw_major_mark(painter, px, mm)
            elif is_minor:
                self._draw_minor_mark(painter, px)

            mm += 1

    def _draw_major_mark(self, painter: QPainter, px: float, mm: int):
        """Büyük işaret çizer (etiketli)"""
        if self._orientation == Qt.Orientation.Horizontal:
            painter.drawLine(int(px), self.height() - 10, int(px), self.height())
            painter.drawText(int(px) + 2, 12, str(mm))
        else:
            painter.drawLine(self.width() - 10, int(px), self.width(), int(px))
            painter.save()
            painter.translate(12, int(px) + 2)
            painter.rotate(-90)
            painter.drawText(0, 0, str(mm))
            painter.restore()

    def _draw_minor_mark(self, painter: QPainter, px: float):
        """Küçük işaret çizer"""
        if self._orientation == Qt.Orientation.Horizontal:
            painter.drawLine(int(px), self.height() - 5, int(px), self.height())
        else:
            painter.drawLine(self.width() - 5, int(px), self.width(), int(px))

    def _draw_cursor_indicator(self, painter: QPainter):
        """Fare pozisyonu göstergesini çizer"""
        if self._cursor_pos is None:
            return

        px_per_mm = UnitConverter.mm_to_px(1, self._dpi) * self._zoom_level
        px = (self._cursor_pos * px_per_mm) - self._offset

        painter.setPen(QPen(QColor("#ff0000"), 1))

        if self._orientation == Qt.Orientation.Horizontal:
            if 0 <= px <= self.width():
                painter.drawLine(int(px), 0, int(px), self.height())
        else:
            if 0 <= px <= self.height():
                painter.drawLine(0, int(px), self.width(), int(px))


class HorizontalRuler(RulerWidget):
    """Yatay cetvel"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(Qt.Orientation.Horizontal, parent)


class VerticalRuler(RulerWidget):
    """Dikey cetvel"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(Qt.Orientation.Vertical, parent)
