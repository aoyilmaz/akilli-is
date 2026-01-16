"""
ScreenRenderer - Ekran önizleme renderer
"""

from typing import List, Optional

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QColor

from .base import RenderStrategy, RenderContext, RenderOutput
from ..items.base import LabelItem, LabelSize
from ..unit_converter import UnitConverter


class ScreenRenderer(RenderStrategy):
    """
    Ekran önizleme renderer.

    Çıktı: QPixmap (96 DPI)
    """

    def __init__(self, dpi: int = 96):
        super().__init__(dpi)

    @property
    def name(self) -> str:
        return "Ekran Önizleme"

    @property
    def output_type(self) -> str:
        return "pixmap"

    def render(
        self,
        items: List[LabelItem],
        label_size: LabelSize,
        context: Optional[RenderContext] = None
    ) -> RenderOutput:
        """
        Elemanları QPixmap olarak render eder.

        Args:
            items: Render edilecek elemanlar
            label_size: Etiket boyutu
            context: Veri bağlama bağlamı

        Returns:
            RenderOutput (data = QPixmap)
        """
        try:
            # Piksel boyutları
            width_px, height_px = label_size.to_pixels(self._dpi)

            # Pixmap oluştur
            pixmap = QPixmap(int(width_px), int(height_px))
            pixmap.fill(QColor("#ffffff"))

            # Painter
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

            # Her elemanı çiz
            for item in items:
                self._render_item(painter, item, context)

            painter.end()

            return RenderOutput(
                success=True,
                data=pixmap,
                metadata={
                    "width_px": width_px,
                    "height_px": height_px,
                    "dpi": self._dpi
                }
            )

        except Exception as e:
            return RenderOutput(success=False, error=str(e))

    def _render_item(
        self,
        painter: QPainter,
        item: LabelItem,
        context: Optional[RenderContext]
    ):
        """Tek bir elemanı render eder"""
        # Pozisyon ve boyut
        geometry = item.geometry
        x_px = UnitConverter.mm_to_px(geometry.x_mm, self._dpi)
        y_px = UnitConverter.mm_to_px(geometry.y_mm, self._dpi)
        w_px = UnitConverter.mm_to_px(geometry.width_mm, self._dpi)
        h_px = UnitConverter.mm_to_px(geometry.height_mm, self._dpi)

        # Painter state'i kaydet
        painter.save()

        # Transform uygula
        painter.translate(x_px, y_px)
        if geometry.rotation:
            painter.rotate(geometry.rotation)

        # Eleman türüne göre çiz
        item_type = item.item_type

        if item_type == "text":
            self._render_text(painter, item, w_px, h_px, context)
        elif item_type == "barcode":
            self._render_barcode(painter, item, w_px, h_px, context)
        elif item_type == "qrcode":
            self._render_qrcode(painter, item, w_px, h_px, context)
        elif item_type == "image":
            self._render_image(painter, item, w_px, h_px)
        elif item_type in ("rectangle", "line", "ellipse"):
            self._render_shape(painter, item, w_px, h_px)

        # Painter state'i geri yükle
        painter.restore()

    def _render_text(
        self,
        painter: QPainter,
        item: LabelItem,
        width: float,
        height: float,
        context: Optional[RenderContext]
    ):
        """Metin elemanını render eder"""
        from ..items.text_item import TextItem
        if not isinstance(item, TextItem):
            return

        # Veri bağlama
        text = item.text
        if context and item.data_key:
            text = context.resolve(item.data_key)

        # Font ve renk
        font = item.style.to_qfont()
        painter.setFont(font)
        painter.setPen(QColor(item.style.color))

        # Çiz
        rect = QRectF(0, 0, width, height)
        from PyQt6.QtGui import QTextOption
        text_option = QTextOption()
        text_option.setAlignment(item.style.to_qt_alignment())
        text_option.setWrapMode(QTextOption.WrapMode.WordWrap)
        painter.drawText(rect, text, text_option)

    def _render_barcode(
        self,
        painter: QPainter,
        item: LabelItem,
        width: float,
        height: float,
        context: Optional[RenderContext]
    ):
        """Barkod elemanını render eder"""
        from ..items.barcode_item import BarcodeItem
        if not isinstance(item, BarcodeItem):
            return

        # Veri bağlama
        data = item.barcode_data
        if context and item.data_key:
            data = context.resolve(item.data_key)

        # Barkod görüntüsü
        # Geçici olarak item'ın verisiyle oluştur
        original_data = item.barcode_data
        item._barcode_data = data
        item._invalidate_cache()

        barcode_pixmap = item._get_barcode_image()

        # Orijinal veriyi geri yükle
        item._barcode_data = original_data
        item._invalidate_cache()

        if barcode_pixmap:
            scaled = barcode_pixmap.scaled(
                int(width),
                int(height),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (width - scaled.width()) / 2
            y = (height - scaled.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled)

    def _render_qrcode(
        self,
        painter: QPainter,
        item: LabelItem,
        width: float,
        height: float,
        context: Optional[RenderContext]
    ):
        """QR kod elemanını render eder"""
        from ..items.qrcode_item import QRCodeItem
        if not isinstance(item, QRCodeItem):
            return

        # Veri bağlama
        data = item.qr_data
        if context and item.data_key:
            data = context.resolve(item.data_key)

        # QR kod görüntüsü
        original_data = item.qr_data
        item._qr_data = data
        item._invalidate_cache()

        qr_pixmap = item._get_qrcode_image()

        item._qr_data = original_data
        item._invalidate_cache()

        if qr_pixmap:
            size = min(width, height)
            scaled = qr_pixmap.scaled(
                int(size),
                int(size),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (width - scaled.width()) / 2
            y = (height - scaled.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled)

    def _render_image(
        self,
        painter: QPainter,
        item: LabelItem,
        width: float,
        height: float
    ):
        """Görüntü elemanını render eder"""
        from ..items.image_item import ImageItem
        if not isinstance(item, ImageItem):
            return

        pixmap = item._get_pixmap()
        if pixmap:
            scaled = pixmap.scaled(
                int(width),
                int(height),
                item.aspect_mode.qt_mode,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (width - scaled.width()) / 2
            y = (height - scaled.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled)

    def _render_shape(
        self,
        painter: QPainter,
        item: LabelItem,
        width: float,
        height: float
    ):
        """Şekil elemanını render eder"""
        from ..items.shape_item import ShapeItem, ShapeType
        if not isinstance(item, ShapeItem):
            return

        rect = QRectF(0, 0, width, height)

        # Stil
        painter.setPen(item.style.to_qpen())
        painter.setBrush(item.style.to_qbrush())

        # Türe göre çiz
        if item.shape_type == ShapeType.RECTANGLE:
            if item.style.corner_radius > 0:
                painter.drawRoundedRect(
                    rect,
                    item.style.corner_radius,
                    item.style.corner_radius
                )
            else:
                painter.drawRect(rect)
        elif item.shape_type == ShapeType.LINE:
            from PyQt6.QtCore import QLineF
            # LineItem'ın diagonal özelliğini kontrol et
            from ..items.shape_item import LineItem
            if isinstance(item, LineItem) and not item.diagonal:
                painter.drawLine(QLineF(rect.bottomLeft(), rect.topRight()))
            else:
                painter.drawLine(QLineF(rect.topLeft(), rect.bottomRight()))
        elif item.shape_type == ShapeType.ELLIPSE:
            painter.drawEllipse(rect)

    def render_to_bytes(
        self,
        items: List[LabelItem],
        label_size: LabelSize,
        context: Optional[RenderContext] = None,
        format: str = "PNG"
    ) -> RenderOutput:
        """
        Elemanları bytes olarak render eder.

        Args:
            format: "PNG", "JPG", "BMP"

        Returns:
            RenderOutput (data = bytes)
        """
        output = self.render(items, label_size, context)
        if not output.success:
            return output

        try:
            from PyQt6.QtCore import QByteArray, QBuffer, QIODevice
            pixmap = output.data

            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            pixmap.save(buffer, format)
            buffer.close()

            return RenderOutput(
                success=True,
                data=bytes(byte_array.data()),
                metadata={**output.metadata, "format": format}
            )
        except Exception as e:
            return RenderOutput(success=False, error=str(e))
