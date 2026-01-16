"""
GridSettings - Grid ayarları ve çizimi
"""

from dataclasses import dataclass
from typing import Dict, Any

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPainter, QColor, QPen

from ..unit_converter import UnitConverter


@dataclass
class GridSettings:
    """Grid ayarları"""
    enabled: bool = True
    snap: bool = True
    size_mm: float = 5.0  # Grid aralığı (mm)
    color: str = "#e0e0e0"
    major_color: str = "#c0c0c0"
    major_interval: int = 5  # Her 5 grid çizgisinde bir major

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "snap": self.snap,
            "size_mm": self.size_mm,
            "color": self.color,
            "major_color": self.major_color,
            "major_interval": self.major_interval
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GridSettings":
        return cls(
            enabled=data.get("enabled", True),
            snap=data.get("snap", True),
            size_mm=data.get("size_mm", 5.0),
            color=data.get("color", "#e0e0e0"),
            major_color=data.get("major_color", "#c0c0c0"),
            major_interval=data.get("major_interval", 5)
        )

    def snap_value(self, value_mm: float) -> float:
        """Değeri grid'e snap eder"""
        if not self.snap:
            return value_mm
        return round(value_mm / self.size_mm) * self.size_mm


class GridPainter:
    """Grid çizici"""

    def __init__(self, settings: GridSettings, dpi: int = 96):
        self.settings = settings
        self.dpi = dpi

    def paint(self, painter: QPainter, rect: QRectF, label_width_mm: float, label_height_mm: float):
        """
        Grid'i çizer.

        Args:
            painter: QPainter
            rect: Çizim alanı
            label_width_mm: Etiket genişliği (mm)
            label_height_mm: Etiket yüksekliği (mm)
        """
        if not self.settings.enabled:
            return

        # Piksel cinsinden grid aralığı
        grid_size_px = UnitConverter.mm_to_px(self.settings.size_mm, self.dpi)

        # Piksel cinsinden etiket boyutları
        label_width_px = UnitConverter.mm_to_px(label_width_mm, self.dpi)
        label_height_px = UnitConverter.mm_to_px(label_height_mm, self.dpi)

        # Renkler
        minor_pen = QPen(QColor(self.settings.color), 0.5)
        major_pen = QPen(QColor(self.settings.major_color), 1)

        # Dikey çizgiler
        x = 0
        line_count = 0
        while x <= label_width_px:
            if line_count % self.settings.major_interval == 0:
                painter.setPen(major_pen)
            else:
                painter.setPen(minor_pen)
            painter.drawLine(int(x), 0, int(x), int(label_height_px))
            x += grid_size_px
            line_count += 1

        # Yatay çizgiler
        y = 0
        line_count = 0
        while y <= label_height_px:
            if line_count % self.settings.major_interval == 0:
                painter.setPen(major_pen)
            else:
                painter.setPen(minor_pen)
            painter.drawLine(0, int(y), int(label_width_px), int(y))
            y += grid_size_px
            line_count += 1
