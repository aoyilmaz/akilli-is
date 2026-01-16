from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QColor, QFont, QPen

# 1mm = ? px (Ekran DPI'ına göre değişir ama biz sabit scaling kullanıyoruz VisualEditor'de)
# VisualEditor MM_TO_PX = 5 kullanıyor.
MM_TO_PX = 5


class LabelRuler(QWidget):
    """
    Etiket tasarımcısı için milimetrik cetvel.
    """

    HORIZONTAL = 0
    VERTICAL = 1

    def __init__(self, orientation=HORIZONTAL, parent=None):
        super().__init__(parent)
        self.orientation = orientation
        self.zoom_factor = 1.0
        self.offset = 0  # Scroll ofset (piksel)
        self.start_pos = 0  # Başlangıç noktası (piksel - margin vs için)

        # Stil ayarları
        self.bg_color = QColor("#F0F0F0")
        self.tick_color = QColor("#555555")
        self.text_color = QColor("#333333")
        self.font = QFont("Arial", 8)

        if self.orientation == self.HORIZONTAL:
            self.setFixedHeight(25)
        else:
            self.setFixedWidth(25)

    def set_zoom(self, zoom):
        self.zoom_factor = zoom
        self.update()

    def set_offset(self, val):
        self.offset = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.bg_color)

        painter.setPen(QPen(self.tick_color, 1))
        painter.setFont(self.font)

        # Cetvelin piksel cinsinden effective birimi
        # 1mm = 5px * Zoom
        # Ancak cetvelde her 1mm'yi çizmek çok sık olabilir.
        # 10mm (1cm) ana çizgiler, 5mm orta, 1mm küçük.

        unit_px = MM_TO_PX * self.zoom_factor

        if self.orientation == self.HORIZONTAL:
            self._draw_horizontal(painter, unit_px)
        else:
            self._draw_vertical(painter, unit_px)

    def _draw_horizontal(self, painter, unit_px):
        width = self.width()
        # Başlangıçtaki boşluk (Margin) rulerın 0 noktası nerede?
        # Offset scrollbar değeridir.
        # Diyelim ki ruler canvas ile birebir hizalı.

        # Döngü için başlangıç (görünen alan)
        start_mm = int(self.offset / unit_px)
        end_mm = int((self.offset + width) / unit_px) + 1

        for mm_val in range(start_mm, end_mm + 1):
            pos = int((mm_val * unit_px) - self.offset)

            # Çizgi uzunluğu
            if mm_val % 10 == 0:
                length = 15
                # Metin çiz
                text = str(mm_val)
                painter.drawText(pos + 2, 10, text)
            elif mm_val % 5 == 0:
                length = 10
            else:
                length = 5

            painter.drawLine(pos, 24, pos, 24 - length)

    def _draw_vertical(self, painter, unit_px):
        height = self.height()

        start_mm = int(self.offset / unit_px)
        end_mm = int((self.offset + height) / unit_px) + 1

        for mm_val in range(start_mm, end_mm + 1):
            pos = int((mm_val * unit_px) - self.offset)

            # Çizgi uzunluğu
            if mm_val % 10 == 0:
                length = 15
                # Metin (Dikey yazı çevirmek yerine yanına yazalım veya küçük font)
                text = str(mm_val)
                # Dikey metin çizimi
                painter.save()
                painter.translate(10, pos + 2)
                painter.rotate(90)
                painter.drawText(0, 0, text)
                painter.restore()

            elif mm_val % 5 == 0:
                length = 10
            else:
                length = 5

            painter.drawLine(24, pos, 24 - length, pos)
