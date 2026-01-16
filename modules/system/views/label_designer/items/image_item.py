"""
ImageItem - Görüntü elemanı
"""

from typing import Dict, Any, Optional
from enum import Enum
from pathlib import Path
import base64

from PyQt6.QtWidgets import QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPixmap, QPen, QImage

from .base import LabelItem, ItemGeometry
from ..unit_converter import UnitConverter


class AspectMode(Enum):
    """Görüntü en-boy oranı modu"""
    IGNORE = "ignore"       # Oranı yoksay, tam sığdır
    KEEP = "keep"           # Oranı koru
    KEEP_EXPAND = "keep_expand"  # Oranı koru, genişlet

    @property
    def display_name(self) -> str:
        names = {
            AspectMode.IGNORE: "Sığdır (Oran yoksay)",
            AspectMode.KEEP: "Oranı Koru",
            AspectMode.KEEP_EXPAND: "Oranı Koru (Genişlet)"
        }
        return names.get(self, self.value)

    @property
    def qt_mode(self) -> Qt.AspectRatioMode:
        """Qt AspectRatioMode karşılığı"""
        mapping = {
            AspectMode.IGNORE: Qt.AspectRatioMode.IgnoreAspectRatio,
            AspectMode.KEEP: Qt.AspectRatioMode.KeepAspectRatio,
            AspectMode.KEEP_EXPAND: Qt.AspectRatioMode.KeepAspectRatioByExpanding
        }
        return mapping.get(self, Qt.AspectRatioMode.KeepAspectRatio)


class ImageItem(LabelItem):
    """
    Görüntü elemanı.

    Desteklenen formatlar:
    - PNG
    - JPG/JPEG

    Özellikleri:
    - En-boy oranı kontrolü
    - Base64 veya dosya yolu desteği
    - Önizleme ve baskı DPI ayrımı
    """

    def __init__(
        self,
        geometry: ItemGeometry,
        image_path: Optional[str] = None,
        image_data: Optional[str] = None,  # Base64 encoded
        aspect_mode: AspectMode = AspectMode.KEEP,
        parent=None
    ):
        super().__init__(geometry, parent)
        self._image_path = image_path
        self._image_data = image_data  # Base64
        self._aspect_mode = aspect_mode
        self._cached_pixmap: Optional[QPixmap] = None
        self._cache_valid = False

    @property
    def item_type(self) -> str:
        return "image"

    @property
    def image_path(self) -> Optional[str]:
        return self._image_path

    @image_path.setter
    def image_path(self, value: Optional[str]):
        self._image_path = value
        self._invalidate_cache()
        self.update()

    @property
    def image_data(self) -> Optional[str]:
        return self._image_data

    @image_data.setter
    def image_data(self, value: Optional[str]):
        self._image_data = value
        self._invalidate_cache()
        self.update()

    @property
    def aspect_mode(self) -> AspectMode:
        return self._aspect_mode

    @aspect_mode.setter
    def aspect_mode(self, value: AspectMode):
        self._aspect_mode = value
        self.update()

    def _invalidate_cache(self):
        """Görüntü önbelleğini geçersiz kılar"""
        self._cache_valid = False
        self._cached_pixmap = None

    def _load_image(self) -> Optional[QPixmap]:
        """Görüntüyü yükler"""
        pixmap = QPixmap()

        # Önce base64 verisini dene
        if self._image_data:
            try:
                image_bytes = base64.b64decode(self._image_data)
                pixmap.loadFromData(image_bytes)
                if not pixmap.isNull():
                    return pixmap
            except Exception as e:
                print(f"Base64 görüntü yükleme hatası: {e}")

        # Dosya yolunu dene
        if self._image_path:
            path = Path(self._image_path)
            if path.exists():
                pixmap.load(str(path))
                if not pixmap.isNull():
                    return pixmap
            else:
                print(f"Görüntü dosyası bulunamadı: {self._image_path}")

        return None

    def _get_pixmap(self) -> Optional[QPixmap]:
        """Önbellekli görüntüyü döndürür"""
        if not self._cache_valid or self._cached_pixmap is None:
            self._cached_pixmap = self._load_image()
            self._cache_valid = True
        return self._cached_pixmap

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Görüntüyü çizer"""
        rect = self.boundingRect()

        pixmap = self._get_pixmap()

        if pixmap and not pixmap.isNull():
            # Görüntüyü ölçekle
            scaled = pixmap.scaled(
                int(rect.width()),
                int(rect.height()),
                self._aspect_mode.qt_mode,
                Qt.TransformationMode.SmoothTransformation
            )

            # Ortala
            x = (rect.width() - scaled.width()) / 2
            y = (rect.height() - scaled.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled)
        else:
            # Görüntü yoksa placeholder çiz
            self._paint_placeholder(painter, rect)

        # Seçim kenarlığı
        self.paint_selection(painter)

    def _paint_placeholder(self, painter: QPainter, rect: QRectF):
        """Görüntü yoksa placeholder çizer"""
        # Arka plan
        painter.setBrush(QColor("#f5f5f5"))
        painter.setPen(QPen(QColor("#cccccc"), 1, Qt.PenStyle.DashLine))
        painter.drawRect(rect)

        # Çapraz çizgiler
        painter.setPen(QPen(QColor("#dddddd"), 1))
        painter.drawLine(int(rect.left()), int(rect.top()), int(rect.right()), int(rect.bottom()))
        painter.drawLine(int(rect.right()), int(rect.top()), int(rect.left()), int(rect.bottom()))

        # İkon ve metin
        painter.setPen(QColor("#999999"))
        from PyQt6.QtGui import QFont
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "📷 Görüntü")

    def to_dict(self) -> Dict[str, Any]:
        """JSON için sözlük formatı"""
        result = self._base_to_dict()
        result.update({
            "aspect_mode": self._aspect_mode.value
        })

        # Görüntü verisini kaydet (base64 tercih edilir)
        if self._image_data:
            result["image_data"] = self._image_data
        elif self._image_path:
            result["image_path"] = self._image_path

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageItem":
        """Sözlükten ImageItem oluşturur"""
        geometry = ItemGeometry.from_dict(data.get("geometry", {}))

        aspect_mode_str = data.get("aspect_mode", "keep")
        try:
            aspect_mode = AspectMode(aspect_mode_str)
        except ValueError:
            aspect_mode = AspectMode.KEEP

        item = cls(
            geometry=geometry,
            image_path=data.get("image_path"),
            image_data=data.get("image_data"),
            aspect_mode=aspect_mode
        )
        item.data_key = data.get("data_key")
        return item

    def set_image_from_file(self, file_path: str) -> bool:
        """
        Dosyadan görüntü yükler.

        Returns:
            True: Başarılı
            False: Başarısız
        """
        path = Path(file_path)
        if not path.exists():
            return False

        # Desteklenen formatları kontrol et
        suffix = path.suffix.lower()
        if suffix not in ('.png', '.jpg', '.jpeg'):
            return False

        self._image_path = str(path)
        self._image_data = None
        self._invalidate_cache()
        self.update()
        return True

    def set_image_from_base64(self, data: str) -> bool:
        """
        Base64 verisinden görüntü yükler.

        Returns:
            True: Başarılı
            False: Başarısız
        """
        try:
            # Geçerliliğini kontrol et
            decoded = base64.b64decode(data)
            pixmap = QPixmap()
            if not pixmap.loadFromData(decoded):
                return False

            self._image_data = data
            self._image_path = None
            self._invalidate_cache()
            self.update()
            return True
        except Exception:
            return False

    def embed_image(self) -> bool:
        """
        Dosya yolundaki görüntüyü base64 olarak gömer.

        Returns:
            True: Başarılı
            False: Başarısız
        """
        if not self._image_path:
            return False

        path = Path(self._image_path)
        if not path.exists():
            return False

        try:
            with open(path, 'rb') as f:
                data = f.read()
            self._image_data = base64.b64encode(data).decode('utf-8')
            self._image_path = None
            return True
        except Exception as e:
            print(f"Görüntü gömme hatası: {e}")
            return False

    def get_original_size_mm(self, dpi: int = 96) -> tuple:
        """Orijinal görüntü boyutunu mm cinsinden döndürür"""
        pixmap = self._get_pixmap()
        if pixmap and not pixmap.isNull():
            width_mm = UnitConverter.px_to_mm(pixmap.width(), dpi)
            height_mm = UnitConverter.px_to_mm(pixmap.height(), dpi)
            return (width_mm, height_mm)
        return (0, 0)

    def fit_to_original_size(self, dpi: int = 96):
        """Geometriyi orijinal görüntü boyutuna ayarlar"""
        width_mm, height_mm = self.get_original_size_mm(dpi)
        if width_mm > 0 and height_mm > 0:
            self._geometry.width_mm = width_mm
            self._geometry.height_mm = height_mm
            self.prepareGeometryChange()
            self.update()
            self.geometry_changed.emit()

    def render_for_print(self, dpi: int = 300) -> Optional[QPixmap]:
        """Yüksek DPI'da baskı için görüntü döndürür"""
        pixmap = self._get_pixmap()
        if pixmap and not pixmap.isNull():
            # Hedef boyutu hesapla
            width_px = int(UnitConverter.mm_to_px(self._geometry.width_mm, dpi))
            height_px = int(UnitConverter.mm_to_px(self._geometry.height_mm, dpi))

            return pixmap.scaled(
                width_px,
                height_px,
                self._aspect_mode.qt_mode,
                Qt.TransformationMode.SmoothTransformation
            )
        return None
