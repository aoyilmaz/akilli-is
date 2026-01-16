"""
LabelDesignerWidget - Ana etiket tasarımcı widget'ı
"""

from typing import Optional, Dict, Any, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMessageBox, QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal

from .items.base import LabelItem, LabelSize, ItemGeometry
from .items.text_item import TextItem, TextStyle, TextAlignment
from .items.barcode_item import BarcodeItem, BarcodeType
from .items.qrcode_item import QRCodeItem, QRErrorLevel
from .items.image_item import ImageItem, AspectMode
from .items.shape_item import ShapeItem, ShapeStyle, RectangleItem, LineItem, EllipseItem

from .canvas.scene import LabelScene
from .canvas.view import LabelView
from .canvas.grid import GridSettings

from .renderers.base import RenderContext
from .renderers.screen_renderer import ScreenRenderer
from .renderers.pdf_renderer import PDFRenderer
from .renderers.zpl_renderer import ZPLRenderer

from .widgets.toolbar import DesignerToolbar
from .widgets.properties_panel import PropertiesPanel
from .widgets.ruler import HorizontalRuler, VerticalRuler


class LabelDesignerWidget(QWidget):
    """
    Ana etiket tasarımcı widget'ı.

    Tüm bileşenleri bir araya getirir:
    - Araç çubuğu
    - Canvas (scene + view)
    - Özellikler paneli
    - Cetveller
    """

    # Sinyaller
    template_changed = pyqtSignal()  # Şablon değişti
    template_saved = pyqtSignal(str)  # Şablon kaydedildi (path)

    def __init__(
        self,
        label_size: Optional[LabelSize] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._label_size = label_size or LabelSize(100, 50)
        self._current_file: Optional[str] = None
        self._modified = False

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI'ı oluşturur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Araç çubuğu
        self.toolbar = DesignerToolbar()
        layout.addWidget(self.toolbar)

        # Ana içerik alanı
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sol taraf: Cetveller + Canvas
        canvas_container = QWidget()
        canvas_layout = QVBoxLayout(canvas_container)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(0)

        # Yatay cetvel
        ruler_row = QHBoxLayout()
        ruler_row.setContentsMargins(0, 0, 0, 0)
        ruler_row.setSpacing(0)

        # Cetvel köşesi (boş alan)
        corner = QWidget()
        corner.setFixedSize(25, 25)
        corner.setStyleSheet("background-color: #f5f5f5;")
        ruler_row.addWidget(corner)

        self.h_ruler = HorizontalRuler()
        self.h_ruler.set_label_size(self._label_size.width_mm)
        ruler_row.addWidget(self.h_ruler)

        canvas_layout.addLayout(ruler_row)

        # Dikey cetvel + View
        view_row = QHBoxLayout()
        view_row.setContentsMargins(0, 0, 0, 0)
        view_row.setSpacing(0)

        self.v_ruler = VerticalRuler()
        self.v_ruler.set_label_size(self._label_size.height_mm)
        view_row.addWidget(self.v_ruler)

        # Scene ve View
        self.scene = LabelScene(self._label_size)
        self.view = LabelView(self.scene)
        view_row.addWidget(self.view)

        canvas_layout.addLayout(view_row)

        # Splitter: Canvas | Properties
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(canvas_container)

        # Özellikler paneli
        self.properties_panel = PropertiesPanel()
        splitter.addWidget(self.properties_panel)

        # Splitter oranları
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        content_layout.addWidget(splitter)
        layout.addLayout(content_layout)

    def _connect_signals(self):
        """Sinyalleri bağlar"""
        # Toolbar sinyalleri
        self.toolbar.add_text_clicked.connect(self._add_text)
        self.toolbar.add_barcode_clicked.connect(self._add_barcode)
        self.toolbar.add_qrcode_clicked.connect(self._add_qrcode)
        self.toolbar.add_image_clicked.connect(self._add_image)
        self.toolbar.add_rectangle_clicked.connect(self._add_rectangle)
        self.toolbar.add_line_clicked.connect(self._add_line)
        self.toolbar.add_ellipse_clicked.connect(self._add_ellipse)

        self.toolbar.zoom_in_clicked.connect(self.view.zoom_in)
        self.toolbar.zoom_out_clicked.connect(self.view.zoom_out)
        self.toolbar.zoom_fit_clicked.connect(self.view.zoom_fit)
        self.toolbar.zoom_reset_clicked.connect(self.view.zoom_reset)

        self.toolbar.grid_toggled.connect(self._toggle_grid)
        self.toolbar.snap_toggled.connect(self._toggle_snap)

        self.toolbar.delete_clicked.connect(self._delete_selected)
        self.toolbar.duplicate_clicked.connect(self._duplicate_selected)

        self.toolbar.save_clicked.connect(self._save)
        self.toolbar.export_pdf_clicked.connect(self._export_pdf)
        self.toolbar.export_zpl_clicked.connect(self._export_zpl)

        # View sinyalleri
        self.view.zoom_changed.connect(self._on_zoom_changed)
        self.view.cursor_position_changed.connect(self._on_cursor_moved)

        # Scene sinyalleri
        self.scene.selection_changed.connect(self._on_selection_changed)
        self.scene.scene_modified.connect(self._on_scene_modified)

        # Properties panel sinyalleri
        self.properties_panel.property_changed.connect(self._on_property_changed)

    # === Eleman Ekleme ===

    def _add_text(self):
        """Metin elemanı ekler"""
        item = self.scene.add_text(10, 10, 50, 10, "Metin")
        item.setSelected(True)
        self._mark_modified()

    def _add_barcode(self):
        """Barkod elemanı ekler"""
        item = self.scene.add_barcode(10, 10, 60, 15, "123456789")
        item.setSelected(True)
        self._mark_modified()

    def _add_qrcode(self):
        """QR kod elemanı ekler"""
        item = self.scene.add_qrcode(10, 10, 20, "https://example.com")
        item.setSelected(True)
        self._mark_modified()

    def _add_image(self):
        """Görüntü elemanı ekler"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Görüntü Seç",
            "",
            "Görüntü Dosyaları (*.png *.jpg *.jpeg)"
        )
        if file_path:
            item = self.scene.add_image(10, 10, 30, 30, file_path)
            item.setSelected(True)
            self._mark_modified()

    def _add_rectangle(self):
        """Dikdörtgen ekler"""
        item = self.scene.add_rectangle(10, 10, 30, 20)
        item.setSelected(True)
        self._mark_modified()

    def _add_line(self):
        """Çizgi ekler"""
        item = self.scene.add_line(10, 10, 40, 0)
        item.setSelected(True)
        self._mark_modified()

    def _add_ellipse(self):
        """Elips ekler"""
        item = self.scene.add_ellipse(10, 10, 20, 20)
        item.setSelected(True)
        self._mark_modified()

    # === Düzenleme ===

    def _delete_selected(self):
        """Seçili elemanları siler"""
        self.scene.delete_selected()
        self._mark_modified()

    def _duplicate_selected(self):
        """Seçili elemanları çoğaltır"""
        self.scene.duplicate_selected()
        self._mark_modified()

    # === Grid & Snap ===

    def _toggle_grid(self, enabled: bool):
        """Grid'i açar/kapatır"""
        self.scene.grid_settings.enabled = enabled
        self.scene.update()

    def _toggle_snap(self, enabled: bool):
        """Snap'i açar/kapatır"""
        self.scene.grid_settings.snap = enabled

    # === Zoom ===

    def _on_zoom_changed(self, level: float):
        """Zoom değiştiğinde"""
        self.toolbar.set_zoom_level(level)
        self.h_ruler.set_zoom(level)
        self.v_ruler.set_zoom(level)

    def _on_cursor_moved(self, x_mm: float, y_mm: float):
        """Fare hareket ettiğinde"""
        self.h_ruler.set_cursor_position(x_mm)
        self.v_ruler.set_cursor_position(y_mm)

    # === Seçim ===

    def _on_selection_changed(self, items: List[LabelItem]):
        """Seçim değiştiğinde"""
        self.properties_panel.set_items(items)

    def _on_scene_modified(self):
        """Sahne değiştiğinde"""
        self._mark_modified()

    # === Özellik Değişikliği ===

    def _on_property_changed(self, prop: str, value):
        """Özellik değiştiğinde"""
        selected = self.scene.get_selected_items()
        if not selected:
            return

        for item in selected:
            self._apply_property(item, prop, value)

        self._mark_modified()

    def _apply_property(self, item: LabelItem, prop: str, value):
        """Özelliği elemana uygular"""
        # Geometri özellikleri
        if prop == "x_mm":
            item.geometry.x_mm = value
            item._update_position()
        elif prop == "y_mm":
            item.geometry.y_mm = value
            item._update_position()
        elif prop == "width_mm":
            item.geometry.width_mm = value
            item.prepareGeometryChange()
            item.update()
        elif prop == "height_mm":
            item.geometry.height_mm = value
            item.prepareGeometryChange()
            item.update()
        elif prop == "rotation":
            item.set_rotation(value)

        # Veri bağlama
        elif prop == "data_key":
            item.data_key = value if value else None

        # Metin özellikleri
        elif isinstance(item, TextItem):
            if prop == "text":
                item.text = value
            elif prop == "font_family":
                item.set_font_family(value)
            elif prop == "font_size":
                item.set_font_size(value)
            elif prop == "bold":
                item.set_bold(value)
            elif prop == "italic":
                item.set_italic(value)
            elif prop == "underline":
                item.set_underline(value)
            elif prop == "alignment":
                item.set_alignment(value)
            elif prop == "color":
                item.set_color(value)

        # Barkod özellikleri
        elif isinstance(item, BarcodeItem):
            if prop == "barcode_data":
                item.barcode_data = value
            elif prop == "barcode_type":
                item.barcode_type = value
            elif prop == "show_text":
                item.show_text = value

        # QR kod özellikleri
        elif isinstance(item, QRCodeItem):
            if prop == "qr_data":
                item.qr_data = value
            elif prop == "error_level":
                item.error_level = value
            elif prop == "make_square":
                item.make_square()

        # Görüntü özellikleri
        elif isinstance(item, ImageItem):
            if prop == "image_path":
                item.set_image_from_file(value)
            elif prop == "aspect_mode":
                item.aspect_mode = value
            elif prop == "embed_image":
                item.embed_image()

        # Şekil özellikleri
        elif isinstance(item, ShapeItem):
            if prop == "stroke_color":
                item.set_stroke_color(value)
            elif prop == "stroke_width":
                item.set_stroke_width(value)
            elif prop == "line_style":
                item.set_line_style(value)
            elif prop == "fill_color":
                item.set_fill_color(value)
            elif prop == "corner_radius" and isinstance(item, RectangleItem):
                item.set_corner_radius(value)

        item.update()

    # === Dosya İşlemleri ===

    def _mark_modified(self):
        """Şablonu değiştirilmiş olarak işaretler"""
        self._modified = True
        self.template_changed.emit()

    def _save(self):
        """Şablonu kaydeder"""
        if self._current_file:
            self.save_to_file(self._current_file)
        else:
            self._save_as()

    def _save_as(self):
        """Şablonu farklı kaydet"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Şablonu Kaydet",
            "",
            "JSON Dosyası (*.json)"
        )
        if file_path:
            self.save_to_file(file_path)

    def save_to_file(self, file_path: str) -> bool:
        """Şablonu dosyaya kaydeder"""
        try:
            import json
            data = self.scene.to_dict()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self._current_file = file_path
            self._modified = False
            self.template_saved.emit(file_path)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {e}")
            return False

    def load_from_file(self, file_path: str) -> bool:
        """Şablonu dosyadan yükler"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.load_from_dict(data)
            self._current_file = file_path
            self._modified = False
            return True
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Yükleme hatası: {e}")
            return False

    def load_from_dict(self, data: Dict[str, Any]):
        """Sözlükten şablon yükler"""
        # Mevcut sahneyi temizle
        self.scene.clear_items()

        # Boyut
        size_data = data.get("size", {})
        self._label_size = LabelSize.from_dict(size_data)
        self.scene.label_size = self._label_size

        # Cetvelleri güncelle
        self.h_ruler.set_label_size(self._label_size.width_mm)
        self.v_ruler.set_label_size(self._label_size.height_mm)

        # Grid
        grid_data = data.get("grid", {})
        self.scene.grid_settings = GridSettings.from_dict(grid_data)
        self.toolbar.set_grid_enabled(self.scene.grid_settings.enabled)
        self.toolbar.set_snap_enabled(self.scene.grid_settings.snap)

        # Elemanları yükle
        new_scene = LabelScene.from_dict(data)
        for item in new_scene.items_list:
            self.scene.add_item(item)

    def get_template_dict(self) -> Dict[str, Any]:
        """Şablonu sözlük olarak döndürür"""
        return self.scene.to_dict()

    # === Export ===

    def _export_pdf(self):
        """PDF olarak dışa aktar"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "PDF Olarak Kaydet",
            "",
            "PDF Dosyası (*.pdf)"
        )
        if file_path:
            renderer = PDFRenderer(dpi=300)
            output = renderer.save_to_file(
                self.scene.items_list,
                self._label_size,
                file_path
            )
            if output.success:
                QMessageBox.information(self, "Başarılı", f"PDF kaydedildi: {file_path}")
            else:
                QMessageBox.critical(self, "Hata", f"PDF oluşturma hatası: {output.error}")

    def _export_zpl(self):
        """ZPL olarak dışa aktar"""
        # DPI seçimi
        dpi, ok = QInputDialog.getItem(
            self,
            "Yazıcı DPI",
            "Yazıcı DPI değerini seçin:",
            ["203 DPI", "300 DPI"],
            0,
            False
        )
        if not ok:
            return

        dpi_value = 203 if "203" in dpi else 300

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "ZPL Olarak Kaydet",
            "",
            "ZPL Dosyası (*.zpl);;Metin Dosyası (*.txt)"
        )
        if file_path:
            renderer = ZPLRenderer(dpi=dpi_value)
            output = renderer.save_to_file(
                self.scene.items_list,
                self._label_size,
                file_path
            )
            if output.success:
                QMessageBox.information(self, "Başarılı", f"ZPL kaydedildi: {file_path}")
            else:
                QMessageBox.critical(self, "Hata", f"ZPL oluşturma hatası: {output.error}")

    def render_preview(self, context: Optional[Dict[str, Any]] = None) -> Optional[any]:
        """Önizleme görüntüsü oluşturur"""
        renderer = ScreenRenderer()
        ctx = RenderContext(data=context) if context else None
        output = renderer.render(self.scene.items_list, self._label_size, ctx)
        if output.success:
            return output.data
        return None

    # === Public API ===

    @property
    def label_size(self) -> LabelSize:
        return self._label_size

    @label_size.setter
    def label_size(self, value: LabelSize):
        self._label_size = value
        self.scene.label_size = value
        self.h_ruler.set_label_size(value.width_mm)
        self.v_ruler.set_label_size(value.height_mm)

    @property
    def is_modified(self) -> bool:
        return self._modified

    @property
    def current_file(self) -> Optional[str]:
        return self._current_file

    def new_template(self):
        """Yeni şablon oluşturur"""
        if self._modified:
            reply = QMessageBox.question(
                self,
                "Kaydet?",
                "Değişiklikler kaydedilmedi. Kaydetmek ister misiniz?",
                QMessageBox.StandardButton.Yes |
                QMessageBox.StandardButton.No |
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._save()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self.scene.clear_items()
        self._current_file = None
        self._modified = False

    def set_label_dimensions(self, width_mm: float, height_mm: float):
        """Etiket boyutlarını ayarlar"""
        self.label_size = LabelSize(width_mm, height_mm)
        self._mark_modified()
