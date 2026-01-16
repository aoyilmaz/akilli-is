"""
BarcodeItem - Barkod elemanı
"""

from typing import Dict, Any, Optional
from enum import Enum
from io import BytesIO

from PyQt6.QtWidgets import QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QImage, QPixmap, QPen

from .base import LabelItem, ItemGeometry
from ..unit_converter import UnitConverter

# python-barcode kütüphanesi
try:
    import barcode
    from barcode.writer import ImageWriter
    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False


class BarcodeType(Enum):
    """Desteklenen barkod türleri"""
    CODE128 = "code128"
    EAN13 = "ean13"
    CODE39 = "code39"

    @property
    def display_name(self) -> str:
        names = {
            BarcodeType.CODE128: "Code 128",
            BarcodeType.EAN13: "EAN-13",
            BarcodeType.CODE39: "Code 39"
        }
        return names.get(self, self.value)

    @property
    def barcode_class_name(self) -> str:
        """python-barcode sınıf adı"""
        mapping = {
            BarcodeType.CODE128: "code128",
            BarcodeType.EAN13: "ean13",
            BarcodeType.CODE39: "code39"
        }
        return mapping.get(self, "code128")


class BarcodeItem(LabelItem):
    """
    Barkod elemanı.

    Desteklenen türler:
    - Code 128 (genel amaçlı)
    - EAN-13 (ürün barkodu)
    - Code 39 (alfanümerik)

    Özellikleri:
    - Gerçek barkod görüntüsü (placeholder değil)
    - Alt metin gösterme seçeneği
    - Veri bağlama desteği
    """

    def __init__(
        self,
        geometry: ItemGeometry,
        barcode_type: BarcodeType = BarcodeType.CODE128,
        barcode_data: str = "123456789",
        show_text: bool = True,
        parent=None
    ):
        super().__init__(geometry, parent)
        self._barcode_type = barcode_type
        self._barcode_data = barcode_data
        self._show_text = show_text
        self._cached_image: Optional[QPixmap] = None
        self._cache_valid = False

    @property
    def item_type(self) -> str:
        return "barcode"

    @property
    def barcode_type(self) -> BarcodeType:
        return self._barcode_type

    @barcode_type.setter
    def barcode_type(self, value: BarcodeType):
        self._barcode_type = value
        self._invalidate_cache()
        self.update()

    @property
    def barcode_data(self) -> str:
        return self._barcode_data

    @barcode_data.setter
    def barcode_data(self, value: str):
        self._barcode_data = value
        self._invalidate_cache()
        self.update()

    @property
    def show_text(self) -> bool:
        return self._show_text

    @show_text.setter
    def show_text(self, value: bool):
        self._show_text = value
        self._invalidate_cache()
        self.update()

    def _invalidate_cache(self):
        """Barkod önbelleğini geçersiz kılar"""
        self._cache_valid = False
        self._cached_image = None

    def _generate_barcode_image(self, data: str) -> Optional[QPixmap]:
        """Barkod görüntüsü oluşturur"""
        if not BARCODE_AVAILABLE:
            return None

        try:
            # Barkod sınıfını al
            barcode_class = barcode.get_barcode_class(self._barcode_type.barcode_class_name)

            # Writer ayarları
            writer = ImageWriter()
            writer.set_options({
                'write_text': self._show_text,
                'module_height': 15.0,
                'module_width': 0.2,
                'quiet_zone': 2.0,
                'font_size': 10,
                'text_distance': 3.0
            })

            # Barkod oluştur
            barcode_instance = barcode_class(data, writer=writer)

            # BytesIO'ya yaz
            buffer = BytesIO()
            barcode_instance.write(buffer)
            buffer.seek(0)

            # QImage'e dönüştür
            image = QImage()
            image.loadFromData(buffer.read())

            return QPixmap.fromImage(image)

        except Exception as e:
            print(f"Barkod oluşturma hatası: {e}")
            return None

    def _get_barcode_image(self) -> Optional[QPixmap]:
        """Önbellekli barkod görüntüsünü döndürür"""
        if not self._cache_valid or self._cached_image is None:
            self._cached_image = self._generate_barcode_image(self._barcode_data)
            self._cache_valid = True
        return self._cached_image

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Barkodu çizer"""
        rect = self.boundingRect()

        # Barkod görüntüsü varsa çiz
        barcode_image = self._get_barcode_image()

        if barcode_image:
            # Görüntüyü dikdörtgene sığdır
            scaled = barcode_image.scaled(
                int(rect.width()),
                int(rect.height()),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            # Ortala
            x = (rect.width() - scaled.width()) / 2
            y = (rect.height() - scaled.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled)
        else:
            # Barkod kütüphanesi yoksa placeholder çiz
            self._paint_placeholder(painter, rect)

        # Seçim kenarlığı
        self.paint_selection(painter)

    def _paint_placeholder(self, painter: QPainter, rect: QRectF):
        """Barkod kütüphanesi yoksa placeholder çizer"""
        # Arka plan
        painter.setBrush(QColor("#f0f0f0"))
        painter.setPen(QPen(QColor("#cccccc"), 1, Qt.PenStyle.DashLine))
        painter.drawRect(rect)

        # Simüle edilmiş barkod çizgileri
        painter.setPen(QPen(QColor("#333333"), 2))
        bar_width = rect.width() / 40
        x = rect.left() + 10
        while x < rect.right() - 10:
            height = rect.height() * 0.7 if int(x) % 3 == 0 else rect.height() * 0.5
            painter.drawLine(int(x), int(rect.top() + 5), int(x), int(rect.top() + height))
            x += bar_width

        # Metin
        painter.setPen(QColor("#666666"))
        painter.drawText(rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, self._barcode_data)

    def to_dict(self) -> Dict[str, Any]:
        """JSON için sözlük formatı"""
        result = self._base_to_dict()
        result.update({
            "barcode_type": self._barcode_type.value,
            "barcode_data": self._barcode_data,
            "show_text": self._show_text
        })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BarcodeItem":
        """Sözlükten BarcodeItem oluşturur"""
        geometry = ItemGeometry.from_dict(data.get("geometry", {}))

        barcode_type_str = data.get("barcode_type", "code128")
        try:
            barcode_type = BarcodeType(barcode_type_str)
        except ValueError:
            barcode_type = BarcodeType.CODE128

        item = cls(
            geometry=geometry,
            barcode_type=barcode_type,
            barcode_data=data.get("barcode_data", data.get("data_key", "123456789")),
            show_text=data.get("show_text", True)
        )
        item.data_key = data.get("data_key")
        return item

    def validate_data(self, data: str) -> bool:
        """Barkod verisinin geçerliliğini kontrol eder"""
        if not data:
            return False

        if self._barcode_type == BarcodeType.EAN13:
            # EAN-13: 12 veya 13 rakam
            return data.isdigit() and len(data) in (12, 13)
        elif self._barcode_type == BarcodeType.CODE39:
            # Code 39: Büyük harf, rakam ve bazı özel karakterler
            valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-. $/+%")
            return all(c in valid_chars for c in data.upper())
        else:
            # Code 128: ASCII 0-127
            return all(ord(c) < 128 for c in data)

    def get_display_data(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Gösterilecek barkod verisini döndürür.
        context verilmişse veri bağlama uygular.
        """
        if context and self._data_key:
            return self.resolve_data(context)
        return self._barcode_data

    def render_for_print(self, dpi: int = 300) -> Optional[QPixmap]:
        """Yüksek DPI'da baskı için barkod oluşturur"""
        if not BARCODE_AVAILABLE:
            return None

        try:
            barcode_class = barcode.get_barcode_class(self._barcode_type.barcode_class_name)

            # Yüksek çözünürlük için ayarlar
            scale_factor = dpi / UnitConverter.SCREEN_DPI
            writer = ImageWriter()
            writer.set_options({
                'write_text': self._show_text,
                'module_height': 15.0 * scale_factor,
                'module_width': 0.2 * scale_factor,
                'quiet_zone': 2.0 * scale_factor,
                'font_size': int(10 * scale_factor),
                'text_distance': 3.0 * scale_factor,
                'dpi': dpi
            })

            barcode_instance = barcode_class(self._barcode_data, writer=writer)

            buffer = BytesIO()
            barcode_instance.write(buffer)
            buffer.seek(0)

            image = QImage()
            image.loadFromData(buffer.read())

            return QPixmap.fromImage(image)

        except Exception as e:
            print(f"Baskı barkodu oluşturma hatası: {e}")
            return None
