"""
Akıllı İş ERP - Filtrelenebilir Tablo Başlığı
Excel benzeri filtreleme özellikli QHeaderView.
"""

from typing import Dict, List, Optional, Callable
from PyQt6.QtWidgets import QHeaderView, QStyleOptionHeader, QStyle, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QMouseEvent, QIcon
import qtawesome as qta

from config.styles import COLORS, FONT_FAMILY_QT
from config.icons import ICONS


class FilterableHeaderView(QHeaderView):
    """
    Excel benzeri filtreleme özellikli tablo başlığı.

    Her sütunda:
    - Sütun başlığı metni
    - Filtre ikonu (▼)
    - Aktif filtre göstergesi (mavi nokta)

    Tıklama:
    - Sol: Sıralama
    - Filtre ikonuna: FilterPopup aç
    """

    # Sinyaller
    filter_icon_clicked = pyqtSignal(int, QPoint)  # section_idx, global_pos
    filter_cleared = pyqtSignal(int)  # section_idx

    # Filtre ikonu boyutları
    FILTER_ICON_WIDTH = 20
    FILTER_ICON_MARGIN = 4

    def __init__(
        self,
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(orientation, parent)

        # Filtrelenebilir sütunlar ve aktif filtreler
        self._filterable_columns: Dict[int, bool] = {}  # section_idx -> filterable
        self._active_filters: Dict[int, bool] = {}  # section_idx -> has_active_filter

        # Hover durumu
        self._hover_section = -1
        self._hover_on_filter_icon = False

        # Mouse tracking aç
        self.setMouseTracking(True)

        # Stil
        self.setHighlightSections(False)
        self.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        # Sıralama için
        self.setSectionsClickable(True)
        self.setSortIndicatorShown(True)

    def set_column_filterable(self, section: int, filterable: bool):
        """Sütunun filtrelenebilir olup olmadığını ayarla"""
        self._filterable_columns[section] = filterable

    def set_filter_active(self, section: int, active: bool):
        """Sütundaki filtrenin aktif olup olmadığını ayarla"""
        self._active_filters[section] = active
        self.updateSection(section)

    def is_filter_active(self, section: int) -> bool:
        """Sütunda aktif filtre var mı?"""
        return self._active_filters.get(section, False)

    def is_column_filterable(self, section: int) -> bool:
        """Sütun filtrelenebilir mi?"""
        return self._filterable_columns.get(section, True)

    def clear_all_filter_indicators(self):
        """Tüm filtre göstergelerini temizle"""
        self._active_filters.clear()
        self.viewport().update()

    def _get_filter_icon_rect(self, rect: QRect) -> QRect:
        """Filtre ikonu için dikdörtgen hesapla (paintSection'dan gelen rect kullan)"""
        # Sağ tarafta filtre ikonu
        icon_rect = QRect(
            rect.right() - self.FILTER_ICON_WIDTH - self.FILTER_ICON_MARGIN,
            rect.top(),
            self.FILTER_ICON_WIDTH,
            rect.height(),
        )
        return icon_rect

    def _get_filter_icon_rect_for_section(self, section: int) -> QRect:
        """Section index için filtre ikonu dikdörtgenini hesapla (mouse events için)"""
        if section < 0 or section >= self.count():
            return QRect()

        # Viewport'a göre pozisyon al
        x = self.sectionViewportPosition(section)
        width = self.sectionSize(section)
        height = self.height()

        section_rect = QRect(x, 0, width, height)
        return self._get_filter_icon_rect(section_rect)

    def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int):
        """Sütun başlığını çiz"""
        painter.save()

        # Arka plan
        is_hover = logicalIndex == self._hover_section
        bg_color = COLORS["bg_hover"] if is_hover else COLORS["bg_secondary"]
        painter.fillRect(rect, QColor(bg_color))

        # Alt çizgi
        painter.setPen(QPen(QColor(COLORS["border"]), 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())

        # Sağ çizgi (ayırıcı)
        painter.drawLine(rect.topRight(), rect.bottomRight())

        # Metin
        text = self.model().headerData(
            logicalIndex, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
        )
        if text:
            painter.setPen(QColor(COLORS["text_primary"]))
            font = QFont(FONT_FAMILY_QT, 11)
            font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(font)

            # Metin alanı (filtre ikonu için yer bırak)
            text_rect = rect.adjusted(
                8,
                0,
                (
                    -self.FILTER_ICON_WIDTH - self.FILTER_ICON_MARGIN * 2
                    if self.is_column_filterable(logicalIndex)
                    else -8
                ),
                0,
            )
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                str(text),
            )

        # Sıralama göstergesi - filtre simgesinin solunda
        sort_indicator = self.sortIndicatorSection()
        if sort_indicator == logicalIndex:
            sort_order = self.sortIndicatorOrder()
            # qtawesome ikonları kullan
            icon_name = (
                ICONS.SORT_UP
                if sort_order == Qt.SortOrder.AscendingOrder
                else ICONS.SORT_DOWN
            )
            icon = qta.icon(icon_name, color=COLORS["primary"])
            # İkon filtre simgesinin solunda olacak
            icon_size = 16
            icon_x = rect.right() - self.FILTER_ICON_WIDTH - icon_size - 8
            icon_y = rect.top() + (rect.height() - icon_size) // 2
            icon.paint(painter, QRect(icon_x, icon_y, icon_size, icon_size))

        # Filtre ikonu
        is_filterable = self.is_column_filterable(logicalIndex)
        if is_filterable:
            self._draw_filter_icon(painter, rect, logicalIndex)

        painter.restore()

    def _draw_filter_icon(self, painter: QPainter, rect: QRect, section: int):
        """Filtre ikonunu çiz"""
        icon_rect = self._get_filter_icon_rect(rect)

        # Hover durumunda arka plan
        is_icon_hover = section == self._hover_section and self._hover_on_filter_icon
        if is_icon_hover:
            painter.fillRect(
                icon_rect.adjusted(2, 4, -2, -4), QColor(COLORS["bg_active"])
            )

        # Filtre ikonu (▼)
        painter.setPen(QColor(COLORS["text_secondary"]))
        font = QFont(FONT_FAMILY_QT, 9)
        painter.setFont(font)
        painter.drawText(
            icon_rect,
            Qt.AlignmentFlag.AlignCenter,
            "▼",
        )

        # Aktif filtre göstergesi (mavi nokta)
        if self.is_filter_active(section):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(COLORS["primary"]))
            # Küçük daire
            center = icon_rect.center()
            painter.drawEllipse(center.x() + 5, center.y() - 6, 6, 6)

    def _get_section_at(self, pos: QPoint) -> int:
        """Pozisyondaki logical index'i manuel bul (daha güvenli)"""
        for logical_idx in range(self.count()):
            if self.isSectionHidden(logical_idx):
                continue

            x = self.sectionViewportPosition(logical_idx)
            w = self.sectionSize(logical_idx)

            # Viewport sınırları dışında mı?
            # x ve x+w, viewport koordinatlarıdır.
            # pos.x() de viewport koordinatıdır.
            if x <= pos.x() < x + w:
                return logical_idx
        return -1

    def mouseMoveEvent(self, event: QMouseEvent):
        """Mouse hareket eventi"""
        pos = event.position().toPoint()
        section = self._get_section_at(pos)

        old_hover = self._hover_section
        old_icon_hover = self._hover_on_filter_icon

        self._hover_section = section

        # Filtre ikonu üzerinde mi?
        if section >= 0 and self.is_column_filterable(section):
            icon_rect = self._get_filter_icon_rect_for_section(section)
            self._hover_on_filter_icon = icon_rect.contains(pos)
        else:
            self._hover_on_filter_icon = False

        # Değişiklik varsa yeniden çiz
        if (
            old_hover != self._hover_section
            or old_icon_hover != self._hover_on_filter_icon
        ):
            self.viewport().update()

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """Mouse tıklama eventi"""
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        pos = event.position().toPoint()
        section = self._get_section_at(pos)

        if section >= 0 and self.is_column_filterable(section):
            icon_rect = self._get_filter_icon_rect_for_section(section)
            if icon_rect.contains(pos):
                # Filtre ikonuna tıklandı
                global_pos = self.mapToGlobal(icon_rect.bottomLeft())
                self.filter_icon_clicked.emit(section, global_pos)
                return

        # Normal tıklama (sıralama)
        super().mousePressEvent(event)

    def leaveEvent(self, event):
        """Mouse widget'tan çıktı"""
        self._hover_section = -1
        self._hover_on_filter_icon = False
        self.viewport().update()
        super().leaveEvent(event)

    def sizeHint(self):
        """Önerilen boyut"""
        hint = super().sizeHint()
        hint.setHeight(36)  # Sabit yükseklik
        return hint
