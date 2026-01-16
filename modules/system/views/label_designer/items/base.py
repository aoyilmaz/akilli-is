"""
LabelItem - Tüm etiket elemanlarının temel sınıfı
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from enum import Enum

from PyQt6.QtWidgets import QGraphicsObject, QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush

if TYPE_CHECKING:
    from ..canvas.resize_handle import ResizeHandle

from ..unit_converter import UnitConverter


@dataclass
class LabelSize:
    """Etiket boyutları (milimetre)"""
    width_mm: float = 100.0
    height_mm: float = 50.0

    def to_pixels(self, dpi: int = 96) -> tuple:
        """Piksel boyutlarını döndürür"""
        return UnitConverter.size_mm_to_px(self.width_mm, self.height_mm, dpi)

    def to_dict(self) -> Dict[str, float]:
        return {"width_mm": self.width_mm, "height_mm": self.height_mm}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LabelSize":
        return cls(
            width_mm=data.get("width_mm", 100.0),
            height_mm=data.get("height_mm", 50.0)
        )


@dataclass
class ItemGeometry:
    """Eleman geometrisi (milimetre cinsinden)"""
    x_mm: float = 0.0
    y_mm: float = 0.0
    width_mm: float = 20.0
    height_mm: float = 10.0
    rotation: int = 0  # 0, 90, 180, 270

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x_mm": round(self.x_mm, 2),
            "y_mm": round(self.y_mm, 2),
            "width_mm": round(self.width_mm, 2),
            "height_mm": round(self.height_mm, 2),
            "rotation": self.rotation
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ItemGeometry":
        return cls(
            x_mm=data.get("x_mm", 0.0),
            y_mm=data.get("y_mm", 0.0),
            width_mm=data.get("width_mm", 20.0),
            height_mm=data.get("height_mm", 10.0),
            rotation=data.get("rotation", 0)
        )

    def to_rect_px(self, dpi: int = 96) -> QRectF:
        """Piksel cinsinden QRectF döndürür"""
        conv = UnitConverter()
        return QRectF(
            conv.mm_to_px(self.x_mm, dpi),
            conv.mm_to_px(self.y_mm, dpi),
            conv.mm_to_px(self.width_mm, dpi),
            conv.mm_to_px(self.height_mm, dpi)
        )


class LabelItem(QGraphicsObject):
    """
    Tüm etiket elemanlarının temel sınıfı.

    Özellikler:
    - Geometri (mm cinsinden)
    - Sürükle-bırak ve seçim
    - 8-nokta resize handle
    - JSON serialize/deserialize
    - Veri bağlama (data binding)

    Alt sınıflar item_type, paint, to_dict, from_dict metodlarını
    implement etmelidir.
    """

    # Sinyaller
    geometry_changed = pyqtSignal()
    selection_changed = pyqtSignal(bool)

    # Seçim kenarlığı rengi
    SELECTION_COLOR = QColor("#007acc")
    HANDLE_SIZE = 8

    def __init__(self, geometry: ItemGeometry, parent=None):
        super().__init__(parent)
        self._geometry = geometry
        self._data_key: Optional[str] = None
        self._dpi = UnitConverter.SCREEN_DPI
        self._handles: List["ResizeHandle"] = []

        self._setup_item()

    def _setup_item(self):
        """Item ayarlarını yapılandırır"""
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges |
            QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
        )
        self.setAcceptHoverEvents(True)

        # Pozisyonu ayarla
        self._update_position()

    def _update_position(self):
        """Geometriye göre pozisyonu günceller"""
        x_px = UnitConverter.mm_to_px(self._geometry.x_mm, self._dpi)
        y_px = UnitConverter.mm_to_px(self._geometry.y_mm, self._dpi)
        self.setPos(x_px, y_px)

        # Rotasyon
        self.setRotation(self._geometry.rotation)

    @property
    def geometry(self) -> ItemGeometry:
        return self._geometry

    @geometry.setter
    def geometry(self, value: ItemGeometry):
        self._geometry = value
        self._update_position()
        self.prepareGeometryChange()
        self.update()
        self.geometry_changed.emit()

    @property
    def data_key(self) -> Optional[str]:
        return self._data_key

    @data_key.setter
    def data_key(self, value: Optional[str]):
        self._data_key = value

    @property
    def item_type(self) -> str:
        """Eleman türünü döndürür (örn: 'text', 'barcode')"""
        raise NotImplementedError("Alt sınıflar item_type'ı implement etmeli")

    def boundingRect(self) -> QRectF:
        """Elemanın sınırlayıcı dikdörtgeni"""
        w_px = UnitConverter.mm_to_px(self._geometry.width_mm, self._dpi)
        h_px = UnitConverter.mm_to_px(self._geometry.height_mm, self._dpi)
        return QRectF(0, 0, w_px, h_px)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Elemanı çizer - alt sınıflar implement etmeli"""
        raise NotImplementedError("Alt sınıflar paint'i implement etmeli")

    def paint_selection(self, painter: QPainter):
        """Seçim kenarlığını çizer"""
        if self.isSelected():
            painter.setPen(QPen(self.SELECTION_COLOR, 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect())

    def to_dict(self) -> Dict[str, Any]:
        """JSON için sözlük formatında döndürür"""
        raise NotImplementedError("Alt sınıflar to_dict'i implement etmeli")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LabelItem":
        """Sözlükten eleman oluşturur"""
        raise NotImplementedError("Alt sınıflar from_dict'i implement etmeli")

    def _base_to_dict(self) -> Dict[str, Any]:
        """Temel özellikleri sözlüğe çevirir"""
        result = {
            "type": self.item_type,
            "geometry": self._geometry.to_dict()
        }
        if self._data_key:
            result["data_key"] = self._data_key
        return result

    def resolve_data(self, context: Dict[str, Any]) -> str:
        """
        Veri bağlama - {değişken} ifadelerini gerçek değerlerle değiştirir.

        Args:
            context: Değişken değerlerini içeren sözlük

        Returns:
            Değiştirilmiş metin
        """
        if not self._data_key:
            return ""

        result = self._data_key
        for key, value in context.items():
            # {key} formatı
            result = result.replace(f"{{{key}}}", str(value))
            # {{ key }} formatı (boşluklu)
            result = result.replace(f"{{{{ {key} }}}}", str(value))
        return result

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """Eleman değişikliklerini yakalar"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Pozisyon değişti - geometriyi güncelle
            pos = self.pos()
            self._geometry.x_mm = UnitConverter.px_to_mm(pos.x(), self._dpi)
            self._geometry.y_mm = UnitConverter.px_to_mm(pos.y(), self._dpi)
            self.geometry_changed.emit()

        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            # Seçim durumu değişti
            self.selection_changed.emit(bool(value))
            self._update_handles_visibility(bool(value))

        return super().itemChange(change, value)

    def _update_handles_visibility(self, visible: bool):
        """Resize handle'ların görünürlüğünü günceller"""
        for handle in self._handles:
            handle.setVisible(visible)

    def set_handles(self, handles: List["ResizeHandle"]):
        """Resize handle'ları ayarlar"""
        self._handles = handles

    def update_geometry_from_handles(self, new_rect_px: QRectF):
        """Handle'lardan gelen boyut değişikliğini uygular"""
        self._geometry.width_mm = UnitConverter.px_to_mm(new_rect_px.width(), self._dpi)
        self._geometry.height_mm = UnitConverter.px_to_mm(new_rect_px.height(), self._dpi)
        self.prepareGeometryChange()
        self.update()
        self.geometry_changed.emit()

    def snap_to_grid(self, grid_size_mm: float) -> None:
        """Pozisyonu grid'e hizalar"""
        self._geometry.x_mm = round(self._geometry.x_mm / grid_size_mm) * grid_size_mm
        self._geometry.y_mm = round(self._geometry.y_mm / grid_size_mm) * grid_size_mm
        self._update_position()

    def set_rotation(self, angle: int):
        """Rotasyonu ayarlar (0, 90, 180, 270)"""
        angle = angle % 360
        if angle not in (0, 90, 180, 270):
            angle = round(angle / 90) * 90
        self._geometry.rotation = angle
        self.setRotation(angle)
        self.geometry_changed.emit()

    def clone(self) -> "LabelItem":
        """Elemanın bir kopyasını oluşturur"""
        data = self.to_dict()
        # Pozisyonu biraz kaydır
        data["geometry"]["x_mm"] += 5
        data["geometry"]["y_mm"] += 5
        return self.__class__.from_dict(data)
