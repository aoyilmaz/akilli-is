"""
ShapeItem - Şekil elemanları (Dikdörtgen, Çizgi, Elips)
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QRectF, QLineF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

from .base import LabelItem, ItemGeometry


class ShapeType(Enum):
    """Şekil türleri"""
    RECTANGLE = "rectangle"
    LINE = "line"
    ELLIPSE = "ellipse"

    @property
    def display_name(self) -> str:
        names = {
            ShapeType.RECTANGLE: "Dikdörtgen",
            ShapeType.LINE: "Çizgi",
            ShapeType.ELLIPSE: "Elips"
        }
        return names.get(self, self.value)


class LineStyle(Enum):
    """Çizgi stili"""
    SOLID = "solid"
    DASH = "dash"
    DOT = "dot"
    DASH_DOT = "dash_dot"

    @property
    def display_name(self) -> str:
        names = {
            LineStyle.SOLID: "Düz",
            LineStyle.DASH: "Kesikli",
            LineStyle.DOT: "Noktalı",
            LineStyle.DASH_DOT: "Kesik-Nokta"
        }
        return names.get(self, self.value)

    @property
    def qt_style(self) -> Qt.PenStyle:
        mapping = {
            LineStyle.SOLID: Qt.PenStyle.SolidLine,
            LineStyle.DASH: Qt.PenStyle.DashLine,
            LineStyle.DOT: Qt.PenStyle.DotLine,
            LineStyle.DASH_DOT: Qt.PenStyle.DashDotLine
        }
        return mapping.get(self, Qt.PenStyle.SolidLine)


@dataclass
class ShapeStyle:
    """Şekil stili"""
    stroke_color: str = "#000000"
    stroke_width: float = 1.0
    line_style: LineStyle = LineStyle.SOLID
    fill_color: Optional[str] = None  # None = şeffaf
    corner_radius: float = 0.0  # Sadece dikdörtgen için

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stroke_color": self.stroke_color,
            "stroke_width": self.stroke_width,
            "line_style": self.line_style.value,
            "fill_color": self.fill_color,
            "corner_radius": self.corner_radius
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShapeStyle":
        line_style = data.get("line_style", "solid")
        if isinstance(line_style, str):
            try:
                line_style = LineStyle(line_style)
            except ValueError:
                line_style = LineStyle.SOLID

        return cls(
            stroke_color=data.get("stroke_color", "#000000"),
            stroke_width=data.get("stroke_width", 1.0),
            line_style=line_style,
            fill_color=data.get("fill_color"),
            corner_radius=data.get("corner_radius", 0.0)
        )

    def to_qpen(self) -> QPen:
        """QPen nesnesine dönüştürür"""
        pen = QPen(QColor(self.stroke_color))
        pen.setWidthF(self.stroke_width)
        pen.setStyle(self.line_style.qt_style)
        return pen

    def to_qbrush(self) -> QBrush:
        """QBrush nesnesine dönüştürür"""
        if self.fill_color:
            return QBrush(QColor(self.fill_color))
        return QBrush(Qt.BrushStyle.NoBrush)


class ShapeItem(LabelItem):
    """
    Temel şekil elemanı.

    Alt sınıflar:
    - RectangleItem: Dikdörtgen
    - LineItem: Çizgi
    - EllipseItem: Elips
    """

    def __init__(
        self,
        geometry: ItemGeometry,
        shape_type: ShapeType,
        style: Optional[ShapeStyle] = None,
        parent=None
    ):
        super().__init__(geometry, parent)
        self._shape_type = shape_type
        self._style = style or ShapeStyle()

    @property
    def item_type(self) -> str:
        return self._shape_type.value

    @property
    def shape_type(self) -> ShapeType:
        return self._shape_type

    @property
    def style(self) -> ShapeStyle:
        return self._style

    @style.setter
    def style(self, value: ShapeStyle):
        self._style = value
        self.update()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Şekli çizer"""
        rect = self.boundingRect()

        # Stil ayarları
        painter.setPen(self._style.to_qpen())
        painter.setBrush(self._style.to_qbrush())

        # Şekle göre çiz
        if self._shape_type == ShapeType.RECTANGLE:
            self._paint_rectangle(painter, rect)
        elif self._shape_type == ShapeType.LINE:
            self._paint_line(painter, rect)
        elif self._shape_type == ShapeType.ELLIPSE:
            self._paint_ellipse(painter, rect)

        # Seçim kenarlığı
        self.paint_selection(painter)

    def _paint_rectangle(self, painter: QPainter, rect: QRectF):
        """Dikdörtgen çizer"""
        if self._style.corner_radius > 0:
            painter.drawRoundedRect(
                rect,
                self._style.corner_radius,
                self._style.corner_radius
            )
        else:
            painter.drawRect(rect)

    def _paint_line(self, painter: QPainter, rect: QRectF):
        """Çizgi çizer (sol üstten sağ alta)"""
        line = QLineF(rect.topLeft(), rect.bottomRight())
        painter.drawLine(line)

    def _paint_ellipse(self, painter: QPainter, rect: QRectF):
        """Elips çizer"""
        painter.drawEllipse(rect)

    def to_dict(self) -> Dict[str, Any]:
        """JSON için sözlük formatı"""
        result = self._base_to_dict()
        result.update({
            "shape_type": self._shape_type.value,
            "style": self._style.to_dict()
        })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShapeItem":
        """Sözlükten ShapeItem oluşturur"""
        geometry = ItemGeometry.from_dict(data.get("geometry", {}))

        shape_type_str = data.get("shape_type", data.get("type", "rectangle"))
        try:
            shape_type = ShapeType(shape_type_str)
        except ValueError:
            shape_type = ShapeType.RECTANGLE

        style = ShapeStyle.from_dict(data.get("style", {}))

        # Uygun alt sınıfı kullan
        if shape_type == ShapeType.RECTANGLE:
            item = RectangleItem(geometry=geometry, style=style)
        elif shape_type == ShapeType.LINE:
            item = LineItem(geometry=geometry, style=style)
        elif shape_type == ShapeType.ELLIPSE:
            item = EllipseItem(geometry=geometry, style=style)
        else:
            item = cls(geometry=geometry, shape_type=shape_type, style=style)

        item.data_key = data.get("data_key")
        return item

    def set_stroke_color(self, color: str):
        """Kenar rengini ayarlar"""
        self._style.stroke_color = color
        self.update()

    def set_stroke_width(self, width: float):
        """Kenar kalınlığını ayarlar"""
        self._style.stroke_width = max(0.1, min(20, width))
        self.update()

    def set_line_style(self, style: LineStyle):
        """Çizgi stilini ayarlar"""
        self._style.line_style = style
        self.update()

    def set_fill_color(self, color: Optional[str]):
        """Dolgu rengini ayarlar (None = şeffaf)"""
        self._style.fill_color = color
        self.update()


class RectangleItem(ShapeItem):
    """Dikdörtgen elemanı"""

    def __init__(
        self,
        geometry: ItemGeometry,
        style: Optional[ShapeStyle] = None,
        parent=None
    ):
        super().__init__(geometry, ShapeType.RECTANGLE, style, parent)

    def set_corner_radius(self, radius: float):
        """Köşe yuvarlaklığını ayarlar"""
        self._style.corner_radius = max(0, radius)
        self.update()

    def make_square(self):
        """Geometriyi kare yapar"""
        size = max(self._geometry.width_mm, self._geometry.height_mm)
        self._geometry.width_mm = size
        self._geometry.height_mm = size
        self.prepareGeometryChange()
        self.update()
        self.geometry_changed.emit()


class LineItem(ShapeItem):
    """
    Çizgi elemanı.

    Not: Geometry'nin width ve height'ı çizginin başlangıç ve bitiş noktalarını
    tanımlar. Çizgi sol üstten (0,0) sağ alta (width, height) çizilir.
    """

    def __init__(
        self,
        geometry: ItemGeometry,
        style: Optional[ShapeStyle] = None,
        diagonal: bool = True,  # True: sol üst->sağ alt, False: sol alt->sağ üst
        parent=None
    ):
        super().__init__(geometry, ShapeType.LINE, style, parent)
        self._diagonal = diagonal

    @property
    def diagonal(self) -> bool:
        """Çapraz yönü"""
        return self._diagonal

    @diagonal.setter
    def diagonal(self, value: bool):
        self._diagonal = value
        self.update()

    def _paint_line(self, painter: QPainter, rect: QRectF):
        """Çizgi çizer"""
        if self._diagonal:
            # Sol üst -> Sağ alt
            line = QLineF(rect.topLeft(), rect.bottomRight())
        else:
            # Sol alt -> Sağ üst
            line = QLineF(rect.bottomLeft(), rect.topRight())
        painter.drawLine(line)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Çizgiyi çizer"""
        rect = self.boundingRect()

        # Sadece pen kullan (fill yok)
        painter.setPen(self._style.to_qpen())
        painter.setBrush(Qt.BrushStyle.NoBrush)

        self._paint_line(painter, rect)

        # Seçim kenarlığı
        self.paint_selection(painter)

    def to_dict(self) -> Dict[str, Any]:
        """JSON için sözlük formatı"""
        result = super().to_dict()
        result["diagonal"] = self._diagonal
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LineItem":
        """Sözlükten LineItem oluşturur"""
        geometry = ItemGeometry.from_dict(data.get("geometry", {}))
        style = ShapeStyle.from_dict(data.get("style", {}))

        item = cls(
            geometry=geometry,
            style=style,
            diagonal=data.get("diagonal", True)
        )
        item.data_key = data.get("data_key")
        return item

    def flip_diagonal(self):
        """Çapraz yönünü değiştirir"""
        self._diagonal = not self._diagonal
        self.update()


class EllipseItem(ShapeItem):
    """Elips elemanı"""

    def __init__(
        self,
        geometry: ItemGeometry,
        style: Optional[ShapeStyle] = None,
        parent=None
    ):
        super().__init__(geometry, ShapeType.ELLIPSE, style, parent)

    def make_circle(self):
        """Geometriyi daire yapar"""
        size = max(self._geometry.width_mm, self._geometry.height_mm)
        self._geometry.width_mm = size
        self._geometry.height_mm = size
        self.prepareGeometryChange()
        self.update()
        self.geometry_changed.emit()
