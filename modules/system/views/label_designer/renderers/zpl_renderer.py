"""
ZPLRenderer - Zebra ZPL II renderer
"""

from typing import List, Optional
from io import BytesIO
import base64

from .base import RenderStrategy, RenderContext, RenderOutput
from ..items.base import LabelItem, LabelSize
from ..unit_converter import UnitConverter


class ZPLRenderer(RenderStrategy):
    """
    Zebra ZPL II komut renderer.

    Desteklenen DPI:
    - 203 DPI (8 dot/mm)
    - 300 DPI (12 dot/mm)

    Çıktı: ZPL komutları (str)
    """

    def __init__(self, dpi: int = 203):
        # ZPL için sadece 203 veya 300 DPI
        if dpi not in (203, 300):
            dpi = 203
        super().__init__(dpi)

    @property
    def name(self) -> str:
        return f"ZPL ({self._dpi} DPI)"

    @property
    def output_type(self) -> str:
        return "zpl"

    @property
    def dots_per_mm(self) -> float:
        """mm başına dot sayısı"""
        return self._dpi / 25.4

    def _mm_to_dots(self, mm: float) -> int:
        """mm'i dot'a çevirir"""
        return int(mm * self.dots_per_mm)

    def render(
        self,
        items: List[LabelItem],
        label_size: LabelSize,
        context: Optional[RenderContext] = None
    ) -> RenderOutput:
        """
        Elemanları ZPL komutlarına render eder.

        Args:
            items: Render edilecek elemanlar
            label_size: Etiket boyutu
            context: Veri bağlama bağlamı

        Returns:
            RenderOutput (data = ZPL string)
        """
        try:
            zpl_commands = []

            # Etiket başlangıcı
            zpl_commands.append("^XA")  # Start format

            # Etiket boyutu
            width_dots = self._mm_to_dots(label_size.width_mm)
            height_dots = self._mm_to_dots(label_size.height_mm)
            zpl_commands.append(f"^PW{width_dots}")  # Print width
            zpl_commands.append(f"^LL{height_dots}")  # Label length

            # Her elemanı render et
            for item in items:
                item_zpl = self._render_item(item, label_size, context)
                if item_zpl:
                    zpl_commands.append(item_zpl)

            # Etiket sonu
            zpl_commands.append("^XZ")  # End format

            zpl_string = "\n".join(zpl_commands)

            return RenderOutput(
                success=True,
                data=zpl_string,
                metadata={
                    "dpi": self._dpi,
                    "width_dots": width_dots,
                    "height_dots": height_dots,
                    "command_count": len(zpl_commands)
                }
            )

        except Exception as e:
            return RenderOutput(success=False, error=str(e))

    def _render_item(
        self,
        item: LabelItem,
        label_size: LabelSize,
        context: Optional[RenderContext]
    ) -> Optional[str]:
        """Tek bir elemanı ZPL komutuna çevirir"""
        geometry = item.geometry
        item_type = item.item_type

        # Pozisyon (dot cinsinden)
        x = self._mm_to_dots(geometry.x_mm)
        y = self._mm_to_dots(geometry.y_mm)

        if item_type == "text":
            return self._render_text(item, x, y, context)
        elif item_type == "barcode":
            return self._render_barcode(item, x, y, context)
        elif item_type == "qrcode":
            return self._render_qrcode(item, x, y, context)
        elif item_type == "image":
            return self._render_image(item, x, y)
        elif item_type == "rectangle":
            return self._render_rectangle(item, x, y)
        elif item_type == "line":
            return self._render_line(item, x, y)
        elif item_type == "ellipse":
            # ZPL elips desteklemiyor, dikdörtgen olarak yaklaşık
            return self._render_rectangle(item, x, y)

        return None

    def _render_text(
        self,
        item: LabelItem,
        x: int, y: int,
        context: Optional[RenderContext]
    ) -> str:
        """Metin elemanını ZPL'e render eder"""
        from ..items.text_item import TextItem, TextAlignment
        if not isinstance(item, TextItem):
            return ""

        # Veri bağlama
        text = item.text
        if context and item.data_key:
            text = context.resolve(item.data_key)

        style = item.style

        # Font boyutu (dot cinsinden)
        font_height = self._mm_to_dots(style.font_size * 0.35)  # pt -> mm yaklaşık
        font_width = font_height

        # Hizalama
        alignment = "L"  # Left
        if style.alignment == TextAlignment.CENTER:
            alignment = "C"
        elif style.alignment == TextAlignment.RIGHT:
            alignment = "R"

        # ZPL komutları
        # ^FO: Field Origin
        # ^A: Scalable font
        # ^FB: Field Block (hizalama için)
        # ^FD: Field Data
        # ^FS: Field Separator

        field_width = self._mm_to_dots(item.geometry.width_mm)

        zpl = f"^FO{x},{y}"
        zpl += f"^A0N,{font_height},{font_width}"
        zpl += f"^FB{field_width},1,0,{alignment}"
        zpl += f"^FD{text}^FS"

        return zpl

    def _render_barcode(
        self,
        item: LabelItem,
        x: int, y: int,
        context: Optional[RenderContext]
    ) -> str:
        """Barkod elemanını ZPL'e render eder"""
        from ..items.barcode_item import BarcodeItem, BarcodeType
        if not isinstance(item, BarcodeItem):
            return ""

        # Veri bağlama
        data = item.barcode_data
        if context and item.data_key:
            data = context.resolve(item.data_key)

        # Barkod yüksekliği
        height = self._mm_to_dots(item.geometry.height_mm)

        # Barkod türüne göre ZPL komutu
        barcode_type = item.barcode_type

        zpl = f"^FO{x},{y}"

        if barcode_type == BarcodeType.CODE128:
            # ^BC: Code 128
            # N: Normal, h: height, Y: print human readable, N: no check digit
            show_text = "Y" if item.show_text else "N"
            zpl += f"^BCN,{height},{show_text},N,N"
        elif barcode_type == BarcodeType.EAN13:
            # ^BE: EAN-13
            show_text = "Y" if item.show_text else "N"
            zpl += f"^BEN,{height},{show_text},N"
        elif barcode_type == BarcodeType.CODE39:
            # ^B3: Code 39
            show_text = "Y" if item.show_text else "N"
            zpl += f"^B3N,N,{height},{show_text},N"

        zpl += f"^FD{data}^FS"

        return zpl

    def _render_qrcode(
        self,
        item: LabelItem,
        x: int, y: int,
        context: Optional[RenderContext]
    ) -> str:
        """QR kod elemanını ZPL'e render eder"""
        from ..items.qrcode_item import QRCodeItem, QRErrorLevel
        if not isinstance(item, QRCodeItem):
            return ""

        # Veri bağlama
        data = item.qr_data
        if context and item.data_key:
            data = context.resolve(item.data_key)

        # QR boyutu (modül boyutu)
        size_mm = min(item.geometry.width_mm, item.geometry.height_mm)
        # Yaklaşık modül boyutu (5-10 arası)
        magnification = max(1, min(10, int(size_mm / 5)))

        # Hata düzeltme seviyesi
        error_level = item.error_level.value  # L, M, Q, H

        # ^BQ: QR Code
        # 2: Model 2
        # magnification: 1-10
        # error_level: H, Q, M, L
        zpl = f"^FO{x},{y}"
        zpl += f"^BQN,2,{magnification}"
        # QR data formatı: error_level + A (auto) + data
        zpl += f"^FD{error_level}A,{data}^FS"

        return zpl

    def _render_image(
        self,
        item: LabelItem,
        x: int, y: int
    ) -> str:
        """Görüntü elemanını ZPL'e render eder (GRF formatı)"""
        from ..items.image_item import ImageItem
        if not isinstance(item, ImageItem):
            return ""

        pixmap = item._get_pixmap()
        if not pixmap:
            return ""

        # Hedef boyut
        width_dots = self._mm_to_dots(item.geometry.width_mm)
        height_dots = self._mm_to_dots(item.geometry.height_mm)

        # Görüntüyü ölçekle
        from PyQt6.QtCore import Qt
        scaled = pixmap.scaled(
            width_dots,
            height_dots,
            item.aspect_mode.qt_mode,
            Qt.TransformationMode.FastTransformation
        )

        # QImage'e çevir ve mono (1-bit) yap
        image = scaled.toImage()
        image = image.convertToFormat(image.Format.Format_Mono)

        # GRF formatına çevir
        grf_data = self._image_to_grf(image)
        if not grf_data:
            return ""

        bytes_per_row = (image.width() + 7) // 8
        total_bytes = bytes_per_row * image.height()

        # ^GF: Graphic Field
        # A: ASCII hex
        # total_bytes: toplam byte sayısı
        # total_bytes: grafik byte sayısı
        # bytes_per_row: satır başına byte
        zpl = f"^FO{x},{y}"
        zpl += f"^GFA,{total_bytes},{total_bytes},{bytes_per_row},"
        zpl += grf_data
        zpl += "^FS"

        return zpl

    def _image_to_grf(self, image) -> Optional[str]:
        """QImage'i ZPL GRF formatına çevirir"""
        try:
            width = image.width()
            height = image.height()
            bytes_per_row = (width + 7) // 8

            grf_hex = []
            for y in range(height):
                row_bytes = []
                for x in range(0, width, 8):
                    byte_val = 0
                    for bit in range(8):
                        if x + bit < width:
                            # Piksel değeri (0=siyah, 1=beyaz)
                            pixel = image.pixelIndex(x + bit, y)
                            # ZPL'de 1=siyah (tersine çevir)
                            if pixel == 0:
                                byte_val |= (1 << (7 - bit))
                    row_bytes.append(f"{byte_val:02X}")
                grf_hex.append("".join(row_bytes))

            return "".join(grf_hex)
        except Exception:
            return None

    def _render_rectangle(
        self,
        item: LabelItem,
        x: int, y: int
    ) -> str:
        """Dikdörtgen elemanını ZPL'e render eder"""
        from ..items.shape_item import RectangleItem, ShapeItem
        if not isinstance(item, ShapeItem):
            return ""

        width = self._mm_to_dots(item.geometry.width_mm)
        height = self._mm_to_dots(item.geometry.height_mm)
        thickness = max(1, int(item.style.stroke_width))

        # ^GB: Graphic Box
        # width, height, thickness, color, rounding
        rounding = int(item.style.corner_radius) if hasattr(item.style, 'corner_radius') else 0

        zpl = f"^FO{x},{y}"
        zpl += f"^GB{width},{height},{thickness},B,{rounding}^FS"

        return zpl

    def _render_line(
        self,
        item: LabelItem,
        x: int, y: int
    ) -> str:
        """Çizgi elemanını ZPL'e render eder"""
        from ..items.shape_item import LineItem
        if not isinstance(item, LineItem):
            return ""

        width = self._mm_to_dots(item.geometry.width_mm)
        height = self._mm_to_dots(item.geometry.height_mm)
        thickness = max(1, int(item.style.stroke_width))

        # Yatay çizgi
        if height < 2:
            zpl = f"^FO{x},{y}"
            zpl += f"^GB{width},{thickness},{thickness}^FS"
            return zpl

        # Dikey çizgi
        if width < 2:
            zpl = f"^FO{x},{y}"
            zpl += f"^GB{thickness},{height},{thickness}^FS"
            return zpl

        # Çapraz çizgi - ZPL'de doğrudan desteklenmiyor
        # Grafik olarak çizilmeli, şimdilik dikdörtgen kullan
        zpl = f"^FO{x},{y}"
        if item.diagonal:
            # Sol üst -> Sağ alt (\ şeklinde)
            zpl += f"^GD{width},{height},{thickness},B,L^FS"
        else:
            # Sol alt -> Sağ üst (/ şeklinde)
            zpl += f"^GD{width},{height},{thickness},B,R^FS"

        return zpl

    def render_multiple_labels(
        self,
        items: List[LabelItem],
        label_size: LabelSize,
        data_list: List[dict],
        copies_per_label: int = 1
    ) -> RenderOutput:
        """
        Birden fazla etiketi ZPL olarak render eder.

        Args:
            items: Şablon elemanları
            label_size: Etiket boyutu
            data_list: Her etiket için veri listesi
            copies_per_label: Her etiketten kaç kopya

        Returns:
            RenderOutput (data = ZPL string)
        """
        try:
            all_zpl = []

            for data in data_list:
                context = RenderContext(data=data)
                output = self.render(items, label_size, context)

                if output.success:
                    if copies_per_label > 1:
                        # ^PQ: Print Quantity
                        zpl = output.data.replace("^XZ", f"^PQ{copies_per_label}^XZ")
                    else:
                        zpl = output.data
                    all_zpl.append(zpl)

            combined_zpl = "\n".join(all_zpl)

            return RenderOutput(
                success=True,
                data=combined_zpl,
                metadata={
                    "label_count": len(data_list),
                    "copies_per_label": copies_per_label,
                    "total_labels": len(data_list) * copies_per_label
                }
            )

        except Exception as e:
            return RenderOutput(success=False, error=str(e))
