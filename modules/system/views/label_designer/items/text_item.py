"""
TextItem - Metin elemanı
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum

from PyQt6.QtWidgets import QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QFont, QColor, QFontMetrics, QTextOption

from .base import LabelItem, ItemGeometry
from ..unit_converter import UnitConverter


class TextAlignment(Enum):
    """Metin hizalama"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


@dataclass
class TextStyle:
    """Metin stili"""
    font_family: str = "Arial"
    font_size: int = 12
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: str = "#000000"
    alignment: TextAlignment = TextAlignment.LEFT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "color": self.color,
            "alignment": self.alignment.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextStyle":
        alignment = data.get("alignment", "left")
        if isinstance(alignment, str):
            alignment = TextAlignment(alignment)
        return cls(
            font_family=data.get("font_family", "Arial"),
            font_size=data.get("font_size", 12),
            bold=data.get("bold", False),
            italic=data.get("italic", False),
            underline=data.get("underline", False),
            color=data.get("color", "#000000"),
            alignment=alignment
        )

    def to_qfont(self) -> QFont:
        """QFont nesnesine dönüştürür"""
        font = QFont(self.font_family, self.font_size)
        font.setBold(self.bold)
        font.setItalic(self.italic)
        font.setUnderline(self.underline)
        return font

    def to_qt_alignment(self) -> Qt.AlignmentFlag:
        """Qt alignment flag'ine dönüştürür"""
        mapping = {
            TextAlignment.LEFT: Qt.AlignmentFlag.AlignLeft,
            TextAlignment.CENTER: Qt.AlignmentFlag.AlignHCenter,
            TextAlignment.RIGHT: Qt.AlignmentFlag.AlignRight
        }
        return mapping.get(self.alignment, Qt.AlignmentFlag.AlignLeft) | Qt.AlignmentFlag.AlignVCenter


class TextItem(LabelItem):
    """
    Metin elemanı.

    Özellikleri:
    - Çoklu satır desteği
    - Font seçimi (family, size, bold, italic, underline)
    - Renk
    - Hizalama (sol, orta, sağ)
    - Veri bağlama ({degisken} formatında)
    """

    def __init__(
        self,
        geometry: ItemGeometry,
        text: str = "Metin",
        style: Optional[TextStyle] = None,
        parent=None
    ):
        super().__init__(geometry, parent)
        self._text = text
        self._style = style or TextStyle()

    @property
    def item_type(self) -> str:
        return "text"

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str):
        self._text = value
        self.update()

    @property
    def style(self) -> TextStyle:
        return self._style

    @style.setter
    def style(self, value: TextStyle):
        self._style = value
        self.update()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Metni çizer"""
        # Font ayarla
        font = self._style.to_qfont()
        painter.setFont(font)
        painter.setPen(QColor(self._style.color))

        # Metin alanı
        rect = self.boundingRect()

        # Text option (hizalama ve kelime sarma)
        text_option = QTextOption()
        text_option.setAlignment(self._style.to_qt_alignment())
        text_option.setWrapMode(QTextOption.WrapMode.WordWrap)

        # Metni çiz
        display_text = self._text
        # Veri bağlama göstergesi
        if self._data_key and "{" in self._text:
            # Tasarım modunda değişken adını göster
            pass

        painter.drawText(rect, display_text, text_option)

        # Seçim kenarlığı
        self.paint_selection(painter)

    def to_dict(self) -> Dict[str, Any]:
        """JSON için sözlük formatı"""
        result = self._base_to_dict()
        result.update({
            "text": self._text,
            "style": self._style.to_dict()
        })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextItem":
        """Sözlükten TextItem oluşturur"""
        geometry = ItemGeometry.from_dict(data.get("geometry", {}))
        style = TextStyle.from_dict(data.get("style", {}))
        item = cls(
            geometry=geometry,
            text=data.get("text", "Metin"),
            style=style
        )
        item.data_key = data.get("data_key")
        return item

    def set_font_family(self, family: str):
        """Font ailesini ayarlar"""
        self._style.font_family = family
        self.update()

    def set_font_size(self, size: int):
        """Font boyutunu ayarlar"""
        self._style.font_size = max(6, min(144, size))
        self.update()

    def set_bold(self, bold: bool):
        """Kalın yazıyı ayarlar"""
        self._style.bold = bold
        self.update()

    def set_italic(self, italic: bool):
        """İtalik yazıyı ayarlar"""
        self._style.italic = italic
        self.update()

    def set_underline(self, underline: bool):
        """Altı çizili yazıyı ayarlar"""
        self._style.underline = underline
        self.update()

    def set_color(self, color: str):
        """Rengi ayarlar (#RRGGBB formatında)"""
        self._style.color = color
        self.update()

    def set_alignment(self, alignment: TextAlignment):
        """Hizalamayı ayarlar"""
        self._style.alignment = alignment
        self.update()

    def auto_size(self):
        """Metne göre boyutu otomatik ayarlar"""
        font = self._style.to_qfont()
        fm = QFontMetrics(font)
        text_rect = fm.boundingRect(self._text)

        # Biraz padding ekle
        padding_mm = 2
        self._geometry.width_mm = UnitConverter.px_to_mm(text_rect.width(), self._dpi) + padding_mm
        self._geometry.height_mm = UnitConverter.px_to_mm(text_rect.height(), self._dpi) + padding_mm

        self.prepareGeometryChange()
        self.update()
        self.geometry_changed.emit()

    def get_display_text(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Gösterilecek metni döndürür.
        context verilmişse veri bağlama uygular.
        """
        if context and self._data_key:
            return self.resolve_data(context)
        return self._text
