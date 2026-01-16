"""
PDFRenderer - ReportLab vektörel PDF renderer
"""

from typing import List, Optional, Dict
from io import BytesIO

from .base import RenderStrategy, RenderContext, RenderOutput
from ..items.base import LabelItem, LabelSize
from ..unit_converter import UnitConverter

# ReportLab
try:
    from reportlab.lib.pagesizes import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class PDFRenderer(RenderStrategy):
    """
    ReportLab vektörel PDF renderer.

    Çıktı: PDF bytes (300 DPI)
    """

    def __init__(self, dpi: int = 300):
        super().__init__(dpi)

    @property
    def name(self) -> str:
        return "PDF"

    @property
    def output_type(self) -> str:
        return "pdf"

    def render(
        self,
        items: List[LabelItem],
        label_size: LabelSize,
        context: Optional[RenderContext] = None
    ) -> RenderOutput:
        """
        Elemanları PDF olarak render eder.

        Args:
            items: Render edilecek elemanlar
            label_size: Etiket boyutu
            context: Veri bağlama bağlamı

        Returns:
            RenderOutput (data = PDF bytes)
        """
        if not REPORTLAB_AVAILABLE:
            return RenderOutput(
                success=False,
                error="ReportLab kütüphanesi bulunamadı. 'pip install reportlab' ile yükleyin."
            )

        try:
            # BytesIO buffer
            buffer = BytesIO()

            # Sayfa boyutu (mm cinsinden)
            page_width = label_size.width_mm * mm
            page_height = label_size.height_mm * mm

            # Canvas oluştur
            c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

            # Her elemanı çiz
            for item in items:
                self._render_item(c, item, label_size, context)

            # Kaydet
            c.save()
            buffer.seek(0)
            pdf_bytes = buffer.read()

            return RenderOutput(
                success=True,
                data=pdf_bytes,
                metadata={
                    "width_mm": label_size.width_mm,
                    "height_mm": label_size.height_mm,
                    "dpi": self._dpi,
                    "page_count": 1
                }
            )

        except Exception as e:
            return RenderOutput(success=False, error=str(e))

    def _render_item(
        self,
        c: "canvas.Canvas",
        item: LabelItem,
        label_size: LabelSize,
        context: Optional[RenderContext]
    ):
        """Tek bir elemanı PDF'e render eder"""
        geometry = item.geometry

        # ReportLab koordinatları sol alttan başlar
        # PyQt6 koordinatları sol üstten başlar
        # Dönüşüm gerekli
        x_mm = geometry.x_mm
        # Y koordinatını ters çevir
        y_mm = label_size.height_mm - geometry.y_mm - geometry.height_mm
        w_mm = geometry.width_mm
        h_mm = geometry.height_mm

        # mm'den point'e çevir
        x = x_mm * mm
        y = y_mm * mm
        w = w_mm * mm
        h = h_mm * mm

        # State kaydet
        c.saveState()

        # Rotasyon (merkez etrafında)
        if geometry.rotation:
            cx = x + w / 2
            cy = y + h / 2
            c.translate(cx, cy)
            c.rotate(geometry.rotation)
            c.translate(-cx, -cy)

        # Eleman türüne göre çiz
        item_type = item.item_type

        if item_type == "text":
            self._render_text(c, item, x, y, w, h, context)
        elif item_type == "barcode":
            self._render_barcode(c, item, x, y, w, h, context)
        elif item_type == "qrcode":
            self._render_qrcode(c, item, x, y, w, h, context)
        elif item_type == "image":
            self._render_image(c, item, x, y, w, h)
        elif item_type in ("rectangle", "line", "ellipse"):
            self._render_shape(c, item, x, y, w, h)

        # State geri yükle
        c.restoreState()

    def _render_text(
        self,
        c: "canvas.Canvas",
        item: LabelItem,
        x: float, y: float, w: float, h: float,
        context: Optional[RenderContext]
    ):
        """Metin elemanını PDF'e render eder"""
        from ..items.text_item import TextItem, TextAlignment
        if not isinstance(item, TextItem):
            return

        # Veri bağlama
        text = item.text
        if context and item.data_key:
            text = context.resolve(item.data_key)

        style = item.style

        # Font
        font_name = style.font_family
        font_size = style.font_size

        # ReportLab standart font'u kullan
        if style.bold:
            font_name = "Helvetica-Bold"
        elif style.italic:
            font_name = "Helvetica-Oblique"
        else:
            font_name = "Helvetica"

        c.setFont(font_name, font_size)

        # Renk
        try:
            c.setFillColor(HexColor(style.color))
        except Exception:
            c.setFillColor(black)

        # Hizalama
        if style.alignment == TextAlignment.CENTER:
            text_x = x + w / 2
            c.drawCentredString(text_x, y + h / 2, text)
        elif style.alignment == TextAlignment.RIGHT:
            text_x = x + w
            c.drawRightString(text_x, y + h / 2, text)
        else:
            c.drawString(x, y + h / 2, text)

    def _render_barcode(
        self,
        c: "canvas.Canvas",
        item: LabelItem,
        x: float, y: float, w: float, h: float,
        context: Optional[RenderContext]
    ):
        """Barkod elemanını PDF'e render eder"""
        from ..items.barcode_item import BarcodeItem
        if not isinstance(item, BarcodeItem):
            return

        # Veri bağlama
        data = item.barcode_data
        if context and item.data_key:
            data = context.resolve(item.data_key)

        # Yüksek DPI barkod görüntüsü oluştur
        original_data = item.barcode_data
        item._barcode_data = data
        item._invalidate_cache()

        barcode_pixmap = item.render_for_print(self._dpi)

        item._barcode_data = original_data
        item._invalidate_cache()

        if barcode_pixmap:
            # QPixmap'i bytes'a çevir
            from PyQt6.QtCore import QByteArray, QBuffer, QIODevice
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            barcode_pixmap.save(buffer, "PNG")
            buffer.close()

            # ImageReader ile PDF'e ekle
            img_buffer = BytesIO(bytes(byte_array.data()))
            img = ImageReader(img_buffer)
            c.drawImage(img, x, y, w, h, preserveAspectRatio=True)

    def _render_qrcode(
        self,
        c: "canvas.Canvas",
        item: LabelItem,
        x: float, y: float, w: float, h: float,
        context: Optional[RenderContext]
    ):
        """QR kod elemanını PDF'e render eder"""
        from ..items.qrcode_item import QRCodeItem
        if not isinstance(item, QRCodeItem):
            return

        # Veri bağlama
        data = item.qr_data
        if context and item.data_key:
            data = context.resolve(item.data_key)

        # Yüksek DPI QR kod görüntüsü
        original_data = item.qr_data
        item._qr_data = data
        item._invalidate_cache()

        qr_pixmap = item.render_for_print(self._dpi)

        item._qr_data = original_data
        item._invalidate_cache()

        if qr_pixmap:
            from PyQt6.QtCore import QByteArray, QBuffer, QIODevice
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            qr_pixmap.save(buffer, "PNG")
            buffer.close()

            img_buffer = BytesIO(bytes(byte_array.data()))
            img = ImageReader(img_buffer)

            # Kare olarak çiz
            size = min(w, h)
            offset_x = (w - size) / 2
            offset_y = (h - size) / 2
            c.drawImage(img, x + offset_x, y + offset_y, size, size)

    def _render_image(
        self,
        c: "canvas.Canvas",
        item: LabelItem,
        x: float, y: float, w: float, h: float
    ):
        """Görüntü elemanını PDF'e render eder"""
        from ..items.image_item import ImageItem, AspectMode
        if not isinstance(item, ImageItem):
            return

        pixmap = item._get_pixmap()
        if not pixmap:
            return

        # QPixmap'i bytes'a çevir
        from PyQt6.QtCore import QByteArray, QBuffer, QIODevice
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, "PNG")
        buffer.close()

        img_buffer = BytesIO(bytes(byte_array.data()))
        img = ImageReader(img_buffer)

        preserve_aspect = item.aspect_mode != AspectMode.IGNORE
        c.drawImage(img, x, y, w, h, preserveAspectRatio=preserve_aspect)

    def _render_shape(
        self,
        c: "canvas.Canvas",
        item: LabelItem,
        x: float, y: float, w: float, h: float
    ):
        """Şekil elemanını PDF'e render eder"""
        from ..items.shape_item import ShapeItem, ShapeType
        if not isinstance(item, ShapeItem):
            return

        style = item.style

        # Stroke rengi
        try:
            c.setStrokeColor(HexColor(style.stroke_color))
        except Exception:
            c.setStrokeColor(black)

        c.setLineWidth(style.stroke_width)

        # Fill rengi
        if style.fill_color:
            try:
                c.setFillColor(HexColor(style.fill_color))
            except Exception:
                pass

        # Türe göre çiz
        if item.shape_type == ShapeType.RECTANGLE:
            if style.corner_radius > 0:
                c.roundRect(x, y, w, h, style.corner_radius,
                           stroke=1, fill=1 if style.fill_color else 0)
            else:
                c.rect(x, y, w, h, stroke=1, fill=1 if style.fill_color else 0)

        elif item.shape_type == ShapeType.LINE:
            from ..items.shape_item import LineItem
            if isinstance(item, LineItem) and not item.diagonal:
                c.line(x, y + h, x + w, y)  # Sol alt -> Sağ üst
            else:
                c.line(x, y + h, x + w, y)  # Sol üst -> Sağ alt (PDF koordinatları)

        elif item.shape_type == ShapeType.ELLIPSE:
            c.ellipse(x, y, x + w, y + h,
                     stroke=1, fill=1 if style.fill_color else 0)

    def render_multiple_labels(
        self,
        items: List[LabelItem],
        label_size: LabelSize,
        data_list: List[Dict],
        columns: int = 2,
        rows: int = 5,
        margin_mm: float = 5
    ) -> RenderOutput:
        """
        Birden fazla etiketi tek PDF'te render eder.

        Args:
            items: Şablon elemanları
            label_size: Tek etiket boyutu
            data_list: Her etiket için veri listesi
            columns: Sayfa başına sütun sayısı
            rows: Sayfa başına satır sayısı
            margin_mm: Kenar boşluğu

        Returns:
            RenderOutput (data = PDF bytes)
        """
        if not REPORTLAB_AVAILABLE:
            return RenderOutput(
                success=False,
                error="ReportLab kütüphanesi bulunamadı."
            )

        try:
            buffer = BytesIO()

            # Sayfa boyutu (A4 varsayılan)
            page_width = (columns * label_size.width_mm + (columns + 1) * margin_mm) * mm
            page_height = (rows * label_size.height_mm + (rows + 1) * margin_mm) * mm

            c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

            labels_per_page = columns * rows
            total_labels = len(data_list)
            page_count = 0

            for idx, data in enumerate(data_list):
                # Sayfa içi pozisyon
                pos_on_page = idx % labels_per_page
                col = pos_on_page % columns
                row = pos_on_page // columns

                # Yeni sayfa gerekli mi?
                if pos_on_page == 0 and idx > 0:
                    c.showPage()
                    page_count += 1

                # Etiket pozisyonu hesapla
                label_x = (margin_mm + col * (label_size.width_mm + margin_mm)) * mm
                # Y koordinatı üstten alta
                label_y = page_height - (margin_mm + (row + 1) * label_size.height_mm + row * margin_mm) * mm

                # Context oluştur
                context = RenderContext(data=data)

                # State kaydet
                c.saveState()
                c.translate(label_x, label_y)

                # Elemanları çiz
                for item in items:
                    self._render_item_relative(c, item, label_size, context)

                c.restoreState()

            c.save()
            buffer.seek(0)
            pdf_bytes = buffer.read()

            return RenderOutput(
                success=True,
                data=pdf_bytes,
                metadata={
                    "label_count": total_labels,
                    "page_count": page_count + 1,
                    "columns": columns,
                    "rows": rows
                }
            )

        except Exception as e:
            return RenderOutput(success=False, error=str(e))

    def _render_item_relative(
        self,
        c: "canvas.Canvas",
        item: LabelItem,
        label_size: LabelSize,
        context: Optional[RenderContext]
    ):
        """Elemanı göreceli konumda render eder"""
        # _render_item ile aynı, ancak translate yapılmış durumda
        geometry = item.geometry

        x = geometry.x_mm * mm
        y = (label_size.height_mm - geometry.y_mm - geometry.height_mm) * mm
        w = geometry.width_mm * mm
        h = geometry.height_mm * mm

        c.saveState()

        if geometry.rotation:
            cx = x + w / 2
            cy = y + h / 2
            c.translate(cx, cy)
            c.rotate(geometry.rotation)
            c.translate(-cx, -cy)

        item_type = item.item_type

        if item_type == "text":
            self._render_text(c, item, x, y, w, h, context)
        elif item_type == "barcode":
            self._render_barcode(c, item, x, y, w, h, context)
        elif item_type == "qrcode":
            self._render_qrcode(c, item, x, y, w, h, context)
        elif item_type == "image":
            self._render_image(c, item, x, y, w, h)
        elif item_type in ("rectangle", "line", "ellipse"):
            self._render_shape(c, item, x, y, w, h)

        c.restoreState()
