"""
Label Designer - Profesyonel Etiket Tasarım Modülü

Bu modül PyQt6 tabanlı profesyonel bir etiket tasarım aracı sağlar.

Özellikler:
- Drag-drop eleman ekleme (Metin, Barkod, QR Kod, Görüntü, Şekil)
- Resize handle ile boyutlandırma
- Grid ve snap-to-grid desteği
- JSON serialize/deserialize
- Çoklu çıktı formatı (Ekran, PDF, ZPL)
- DPI yönetimi (96, 203, 300)
- Veri bağlama ({değişken} formatında)

Kullanım:
    from modules.system.views.label_designer import LabelDesignerWidget, LabelSize

    # Widget oluştur
    designer = LabelDesignerWidget(LabelSize(100, 50))

    # Şablon yükle
    designer.load_from_file("template.json")

    # Şablon kaydet
    designer.save_to_file("template.json")

    # Önizleme oluştur
    pixmap = designer.render_preview({"Urun_Adi": "Test", "Barkod": "123"})
"""

from .unit_converter import UnitConverter

# Items
from .items.base import LabelItem, ItemGeometry, LabelSize
from .items.text_item import TextItem, TextStyle, TextAlignment
from .items.barcode_item import BarcodeItem, BarcodeType
from .items.qrcode_item import QRCodeItem, QRErrorLevel
from .items.image_item import ImageItem, AspectMode
from .items.shape_item import (
    ShapeItem, ShapeType, ShapeStyle, LineStyle,
    RectangleItem, LineItem, EllipseItem
)

# Canvas
from .canvas.scene import LabelScene
from .canvas.view import LabelView
from .canvas.grid import GridSettings
from .canvas.resize_handle import ResizeHandle, HandlePosition

# Renderers
from .renderers.base import RenderStrategy, RenderContext, RenderOutput
from .renderers.screen_renderer import ScreenRenderer
from .renderers.pdf_renderer import PDFRenderer
from .renderers.zpl_renderer import ZPLRenderer

# Widgets
from .widgets.toolbar import DesignerToolbar
from .widgets.properties_panel import PropertiesPanel
from .widgets.ruler import HorizontalRuler, VerticalRuler

# Main Widget
from .designer_widget import LabelDesignerWidget

__all__ = [
    # Main
    "LabelDesignerWidget",
    "UnitConverter",

    # Items
    "LabelItem",
    "ItemGeometry",
    "LabelSize",
    "TextItem",
    "TextStyle",
    "TextAlignment",
    "BarcodeItem",
    "BarcodeType",
    "QRCodeItem",
    "QRErrorLevel",
    "ImageItem",
    "AspectMode",
    "ShapeItem",
    "ShapeType",
    "ShapeStyle",
    "LineStyle",
    "RectangleItem",
    "LineItem",
    "EllipseItem",

    # Canvas
    "LabelScene",
    "LabelView",
    "GridSettings",
    "ResizeHandle",
    "HandlePosition",

    # Renderers
    "RenderStrategy",
    "RenderContext",
    "RenderOutput",
    "ScreenRenderer",
    "PDFRenderer",
    "ZPLRenderer",

    # Widgets
    "DesignerToolbar",
    "PropertiesPanel",
    "HorizontalRuler",
    "VerticalRuler",
]

__version__ = "2.0.0"
