"""
QRCodeItem - QR Kod elemanı
"""

from typing import Dict, Any, Optional
from enum import Enum
from io import BytesIO

from PyQt6.QtWidgets import QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QImage, QPixmap, QPen

from .base import LabelItem, ItemGeometry
from ..unit_converter import UnitConverter

# qrcode kütüphanesi
try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False


class QRErrorLevel(Enum):
    """QR Kod hata düzeltme seviyesi"""
    LOW = "L"       # %7 kurtarma
    MEDIUM = "M"    # %15 kurtarma
    QUARTILE = "Q"  # %25 kurtarma
    HIGH = "H"      # %30 kurtarma

    @property
    def display_name(self) -> str:
        names = {
            QRErrorLevel.LOW: "Düşük (L - %7)",
            QRErrorLevel.MEDIUM: "Orta (M - %15)",
            QRErrorLevel.QUARTILE: "Yüksek (Q - %25)",
            QRErrorLevel.HIGH: "Çok Yüksek (H - %30)"
        }
        return names.get(self, self.value)

    @property
    def qrcode_constant(self) -> int:
        """qrcode kütüphanesi sabiti"""
        if not QRCODE_AVAILABLE:
            return 0
        mapping = {
            QRErrorLevel.LOW: ERROR_CORRECT_L,
            QRErrorLevel.MEDIUM: ERROR_CORRECT_M,
            QRErrorLevel.QUARTILE: ERROR_CORRECT_Q,
            QRErrorLevel.HIGH: ERROR_CORRECT_H
        }
        return mapping.get(self, ERROR_CORRECT_M)


class QRCodeItem(LabelItem):
    """
    QR Kod elemanı.

    Özellikleri:
    - Hata düzeltme seviyesi seçimi
    - Otomatik boyutlandırma
    - Veri bağlama desteği
    """

    def __init__(
        self,
        geometry: ItemGeometry,
        qr_data: str = "https://example.com",
        error_level: QRErrorLevel = QRErrorLevel.MEDIUM,
        parent=None
    ):
        super().__init__(geometry, parent)
        self._qr_data = qr_data
        self._error_level = error_level
        self._cached_image: Optional[QPixmap] = None
        self._cache_valid = False

    @property
    def item_type(self) -> str:
        return "qrcode"

    @property
    def qr_data(self) -> str:
        return self._qr_data

    @qr_data.setter
    def qr_data(self, value: str):
        self._qr_data = value
        self._invalidate_cache()
        self.update()

    @property
    def error_level(self) -> QRErrorLevel:
        return self._error_level

    @error_level.setter
    def error_level(self, value: QRErrorLevel):
        self._error_level = value
        self._invalidate_cache()
        self.update()

    def _invalidate_cache(self):
        """QR kod önbelleğini geçersiz kılar"""
        self._cache_valid = False
        self._cached_image = None

    def _generate_qrcode_image(self, data: str, box_size: int = 10) -> Optional[QPixmap]:
        """QR kod görüntüsü oluşturur"""
        if not QRCODE_AVAILABLE:
            return None

        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=self._error_level.qrcode_constant,
                box_size=box_size,
                border=2
            )
            qr.add_data(data)
            qr.make(fit=True)

            # PIL Image oluştur
            img = qr.make_image(fill_color="black", back_color="white")

            # BytesIO'ya kaydet
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            # QImage'e dönüştür
            qimage = QImage()
            qimage.loadFromData(buffer.read())

            return QPixmap.fromImage(qimage)

        except Exception as e:
            print(f"QR kod oluşturma hatası: {e}")
            return None

    def _get_qrcode_image(self) -> Optional[QPixmap]:
        """Önbellekli QR kod görüntüsünü döndürür"""
        if not self._cache_valid or self._cached_image is None:
            self._cached_image = self._generate_qrcode_image(self._qr_data)
            self._cache_valid = True
        return self._cached_image

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """QR kodu çizer"""
        rect = self.boundingRect()

        # QR kod görüntüsü varsa çiz
        qr_image = self._get_qrcode_image()

        if qr_image:
            # Kare olarak ölçekle (en küçük kenar)
            size = min(rect.width(), rect.height())
            scaled = qr_image.scaled(
                int(size),
                int(size),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            # Ortala
            x = (rect.width() - scaled.width()) / 2
            y = (rect.height() - scaled.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled)
        else:
            # QR kod kütüphanesi yoksa placeholder çiz
            self._paint_placeholder(painter, rect)

        # Seçim kenarlığı
        self.paint_selection(painter)

    def _paint_placeholder(self, painter: QPainter, rect: QRectF):
        """QR kod kütüphanesi yoksa placeholder çizer"""
        # Kare alan hesapla
        size = min(rect.width(), rect.height())
        x = (rect.width() - size) / 2
        y = (rect.height() - size) / 2
        square = QRectF(x, y, size, size)

        # Arka plan
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QPen(QColor("#cccccc"), 1, Qt.PenStyle.DashLine))
        painter.drawRect(square)

        # Basit QR kod simülasyonu
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#333333"))

        # Köşe kareleri
        corner_size = size / 7
        # Sol üst
        painter.drawRect(QRectF(x + corner_size * 0.5, y + corner_size * 0.5, corner_size * 2, corner_size * 2))
        # Sağ üst
        painter.drawRect(QRectF(x + size - corner_size * 2.5, y + corner_size * 0.5, corner_size * 2, corner_size * 2))
        # Sol alt
        painter.drawRect(QRectF(x + corner_size * 0.5, y + size - corner_size * 2.5, corner_size * 2, corner_size * 2))

        # QR yazısı
        painter.setPen(QColor("#666666"))
        from PyQt6.QtGui import QFont
        font = QFont("Arial", 8)
        painter.setFont(font)
        painter.drawText(square, Qt.AlignmentFlag.AlignCenter, "QR")

    def to_dict(self) -> Dict[str, Any]:
        """JSON için sözlük formatı"""
        result = self._base_to_dict()
        result.update({
            "qr_data": self._qr_data,
            "error_level": self._error_level.value
        })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QRCodeItem":
        """Sözlükten QRCodeItem oluşturur"""
        geometry = ItemGeometry.from_dict(data.get("geometry", {}))

        error_level_str = data.get("error_level", "M")
        try:
            error_level = QRErrorLevel(error_level_str)
        except ValueError:
            error_level = QRErrorLevel.MEDIUM

        item = cls(
            geometry=geometry,
            qr_data=data.get("qr_data", data.get("data_key", "https://example.com")),
            error_level=error_level
        )
        item.data_key = data.get("data_key")
        return item

    def get_display_data(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Gösterilecek QR verisini döndürür.
        context verilmişse veri bağlama uygular.
        """
        if context and self._data_key:
            return self.resolve_data(context)
        return self._qr_data

    def render_for_print(self, dpi: int = 300) -> Optional[QPixmap]:
        """Yüksek DPI'da baskı için QR kod oluşturur"""
        # Daha büyük box_size ile oluştur
        scale_factor = dpi / UnitConverter.SCREEN_DPI
        box_size = int(10 * scale_factor)
        return self._generate_qrcode_image(self._qr_data, box_size=box_size)

    def make_square(self):
        """Geometriyi kare yapar (QR kodlar için ideal)"""
        size = max(self._geometry.width_mm, self._geometry.height_mm)
        self._geometry.width_mm = size
        self._geometry.height_mm = size
        self.prepareGeometryChange()
        self.update()
        self.geometry_changed.emit()
