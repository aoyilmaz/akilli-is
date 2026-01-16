"""
LabelScene - Etiket tasarım sahnesi
"""

from typing import List, Optional, Dict, Any, Type

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsItem
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen

from ..items.base import LabelItem, ItemGeometry, LabelSize
from ..items.text_item import TextItem
from ..items.barcode_item import BarcodeItem
from ..items.qrcode_item import QRCodeItem
from ..items.image_item import ImageItem
from ..items.shape_item import ShapeItem, RectangleItem, LineItem, EllipseItem
from .grid import GridSettings, GridPainter
from .resize_handle import create_handles_for_item, ResizeHandle
from ..unit_converter import UnitConverter


# Item türlerini kayıt
ITEM_TYPES: Dict[str, Type[LabelItem]] = {
    "text": TextItem,
    "barcode": BarcodeItem,
    "qrcode": QRCodeItem,
    "image": ImageItem,
    "rectangle": RectangleItem,
    "line": LineItem,
    "ellipse": EllipseItem,
}


class LabelScene(QGraphicsScene):
    """
    Etiket tasarım sahnesi.

    Özellikleri:
    - Grid gösterimi ve snap-to-grid
    - Eleman yönetimi (ekleme, silme, seçim)
    - JSON serialize/deserialize
    - Undo/Redo desteği (gelecek faz)
    """

    # Sinyaller
    item_added = pyqtSignal(LabelItem)
    item_removed = pyqtSignal(LabelItem)
    selection_changed = pyqtSignal(list)  # Seçili item listesi
    scene_modified = pyqtSignal()

    def __init__(
        self,
        label_size: Optional[LabelSize] = None,
        grid_settings: Optional[GridSettings] = None,
        parent=None
    ):
        super().__init__(parent)
        self._label_size = label_size or LabelSize()
        self._grid_settings = grid_settings or GridSettings()
        self._dpi = UnitConverter.SCREEN_DPI
        self._items: List[LabelItem] = []
        self._handles: Dict[LabelItem, List[ResizeHandle]] = {}

        self._setup_scene()

    def _setup_scene(self):
        """Sahneyi yapılandırır"""
        # Sahne boyutu
        width_px, height_px = self._label_size.to_pixels(self._dpi)
        self.setSceneRect(0, 0, width_px, height_px)

        # Arka plan
        self.setBackgroundBrush(QBrush(QColor("#ffffff")))

        # Seçim değişikliği
        self.selectionChanged.connect(self._on_selection_changed)

    @property
    def label_size(self) -> LabelSize:
        return self._label_size

    @label_size.setter
    def label_size(self, value: LabelSize):
        self._label_size = value
        width_px, height_px = self._label_size.to_pixels(self._dpi)
        self.setSceneRect(0, 0, width_px, height_px)
        self.update()

    @property
    def grid_settings(self) -> GridSettings:
        return self._grid_settings

    @grid_settings.setter
    def grid_settings(self, value: GridSettings):
        self._grid_settings = value
        self.update()

    @property
    def items_list(self) -> List[LabelItem]:
        """Tüm etiket elemanlarını döndürür"""
        return self._items.copy()

    def add_item(self, item: LabelItem) -> LabelItem:
        """
        Sahneye eleman ekler.

        Args:
            item: Eklenecek eleman

        Returns:
            Eklenen eleman
        """
        # Sahneye ekle
        self.addItem(item)
        self._items.append(item)

        # Resize handle'ları oluştur ve ekle
        handles = create_handles_for_item(item)
        for handle in handles:
            self.addItem(handle)
            handle.update_position()
        self._handles[item] = handles
        item.set_handles(handles)

        # Geometri değişikliğini dinle
        item.geometry_changed.connect(lambda: self._on_item_geometry_changed(item))

        # Sinyalleri emit et
        self.item_added.emit(item)
        self.scene_modified.emit()

        return item

    def remove_item(self, item: LabelItem):
        """Sahneden eleman siler"""
        if item not in self._items:
            return

        # Handle'ları sil
        if item in self._handles:
            for handle in self._handles[item]:
                self.removeItem(handle)
            del self._handles[item]

        # Item'ı sil
        self.removeItem(item)
        self._items.remove(item)

        # Sinyaller
        self.item_removed.emit(item)
        self.scene_modified.emit()

    def clear_items(self):
        """Tüm elemanları temizler"""
        for item in self._items.copy():
            self.remove_item(item)

    def _on_item_geometry_changed(self, item: LabelItem):
        """Eleman geometrisi değiştiğinde handle'ları günceller"""
        if item in self._handles:
            for handle in self._handles[item]:
                handle.update_position()
        self.scene_modified.emit()

    def _on_selection_changed(self):
        """Seçim değiştiğinde çağrılır"""
        selected = self.get_selected_items()

        # Handle görünürlüğünü güncelle
        for item, handles in self._handles.items():
            visible = item in selected
            for handle in handles:
                handle.setVisible(visible)
                if visible:
                    handle.update_position()

        self.selection_changed.emit(selected)

    def get_selected_items(self) -> List[LabelItem]:
        """Seçili elemanları döndürür"""
        return [item for item in self._items if item.isSelected()]

    def select_all(self):
        """Tüm elemanları seçer"""
        for item in self._items:
            item.setSelected(True)

    def deselect_all(self):
        """Tüm seçimleri kaldırır"""
        for item in self._items:
            item.setSelected(False)

    def delete_selected(self):
        """Seçili elemanları siler"""
        for item in self.get_selected_items():
            self.remove_item(item)

    def duplicate_selected(self) -> List[LabelItem]:
        """Seçili elemanları çoğaltır"""
        new_items = []
        for item in self.get_selected_items():
            clone = item.clone()
            self.add_item(clone)
            new_items.append(clone)
        return new_items

    def snap_selected_to_grid(self):
        """Seçili elemanları grid'e hizalar"""
        if not self._grid_settings.snap:
            return
        for item in self.get_selected_items():
            item.snap_to_grid(self._grid_settings.size_mm)

    # --- Fabrika metodları ---

    def add_text(
        self,
        x_mm: float = 10,
        y_mm: float = 10,
        width_mm: float = 50,
        height_mm: float = 10,
        text: str = "Metin"
    ) -> TextItem:
        """Metin elemanı ekler"""
        geometry = ItemGeometry(x_mm, y_mm, width_mm, height_mm)
        item = TextItem(geometry, text)
        return self.add_item(item)

    def add_barcode(
        self,
        x_mm: float = 10,
        y_mm: float = 20,
        width_mm: float = 60,
        height_mm: float = 15,
        data: str = "123456789"
    ) -> BarcodeItem:
        """Barkod elemanı ekler"""
        geometry = ItemGeometry(x_mm, y_mm, width_mm, height_mm)
        item = BarcodeItem(geometry, barcode_data=data)
        return self.add_item(item)

    def add_qrcode(
        self,
        x_mm: float = 10,
        y_mm: float = 10,
        size_mm: float = 20,
        data: str = "https://example.com"
    ) -> QRCodeItem:
        """QR kod elemanı ekler"""
        geometry = ItemGeometry(x_mm, y_mm, size_mm, size_mm)
        item = QRCodeItem(geometry, qr_data=data)
        return self.add_item(item)

    def add_image(
        self,
        x_mm: float = 10,
        y_mm: float = 10,
        width_mm: float = 30,
        height_mm: float = 30,
        image_path: Optional[str] = None
    ) -> ImageItem:
        """Görüntü elemanı ekler"""
        geometry = ItemGeometry(x_mm, y_mm, width_mm, height_mm)
        item = ImageItem(geometry, image_path=image_path)
        return self.add_item(item)

    def add_rectangle(
        self,
        x_mm: float = 10,
        y_mm: float = 10,
        width_mm: float = 30,
        height_mm: float = 20
    ) -> RectangleItem:
        """Dikdörtgen ekler"""
        geometry = ItemGeometry(x_mm, y_mm, width_mm, height_mm)
        item = RectangleItem(geometry)
        return self.add_item(item)

    def add_line(
        self,
        x_mm: float = 10,
        y_mm: float = 10,
        width_mm: float = 30,
        height_mm: float = 0
    ) -> LineItem:
        """Çizgi ekler"""
        geometry = ItemGeometry(x_mm, y_mm, width_mm, height_mm)
        item = LineItem(geometry)
        return self.add_item(item)

    def add_ellipse(
        self,
        x_mm: float = 10,
        y_mm: float = 10,
        width_mm: float = 20,
        height_mm: float = 20
    ) -> EllipseItem:
        """Elips ekler"""
        geometry = ItemGeometry(x_mm, y_mm, width_mm, height_mm)
        item = EllipseItem(geometry)
        return self.add_item(item)

    # --- Serialization ---

    def to_dict(self) -> Dict[str, Any]:
        """JSON için sözlük formatı"""
        return {
            "version": "2.0",
            "size": self._label_size.to_dict(),
            "grid": self._grid_settings.to_dict(),
            "items": [item.to_dict() for item in self._items]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LabelScene":
        """Sözlükten LabelScene oluşturur"""
        version = data.get("version", "1.0")

        # Boyut
        size = LabelSize.from_dict(data.get("size", {}))

        # Grid
        grid = GridSettings.from_dict(data.get("grid", {}))

        # Sahne oluştur
        scene = cls(label_size=size, grid_settings=grid)

        # Elemanları ekle
        for item_data in data.get("items", []):
            item = scene._create_item_from_dict(item_data)
            if item:
                scene.add_item(item)

        return scene

    def _create_item_from_dict(self, data: Dict[str, Any]) -> Optional[LabelItem]:
        """Sözlükten eleman oluşturur"""
        item_type = data.get("type", "")

        # Shape türleri için özel kontrol
        if item_type in ("rectangle", "line", "ellipse"):
            return ShapeItem.from_dict(data)

        # Diğer türler
        item_class = ITEM_TYPES.get(item_type)
        if item_class:
            return item_class.from_dict(data)

        print(f"Bilinmeyen eleman türü: {item_type}")
        return None

    # --- Drawing ---

    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Arka planı çizer (grid dahil)"""
        # Beyaz arka plan
        painter.fillRect(rect, QColor("#ffffff"))

        # Etiket sınırı
        label_rect = self.sceneRect()
        painter.setPen(QPen(QColor("#cccccc"), 1))
        painter.drawRect(label_rect)

        # Grid
        if self._grid_settings.enabled:
            grid_painter = GridPainter(self._grid_settings, self._dpi)
            grid_painter.paint(
                painter,
                label_rect,
                self._label_size.width_mm,
                self._label_size.height_mm
            )
