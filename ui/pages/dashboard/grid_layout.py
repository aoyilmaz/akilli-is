"""
Akıllı İş - Dashboard Grid Layout

4 sütunlu grid sistemi ile widget yerleşimi yönetimi.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget,
    QGridLayout,
    QFrame,
    QLabel,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QPoint
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QColor

from config.styles import COLORS
from .widgets.base import BaseWidget, WidgetConfig


@dataclass
class GridCell:
    """Grid hücre bilgisi"""
    row: int
    col: int
    occupied: bool = False
    widget_code: Optional[str] = None


class WidgetPlaceholder(QFrame):
    """
    Boş grid hücresi için placeholder

    Düzenleme modunda görünür, widget eklenmesi için alan sağlar.
    """

    clicked = pyqtSignal(int, int)  # row, col

    def __init__(self, row: int, col: int, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col

        self.setMinimumSize(100, 80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet(f"""
            WidgetPlaceholder {{
                background: {COLORS['bg_secondary']};
                border: 2px dashed {COLORS['border']};
                border-radius: 8px;
            }}
            WidgetPlaceholder:hover {{
                border-color: {COLORS['primary']};
                background: {COLORS['bg_hover']};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.row, self.col)
        super().mousePressEvent(event)


class DashboardGridLayout(QWidget):
    """
    Dashboard grid layout yöneticisi

    4 sütunlu sabit grid sistemi. Widget'lar 1x1, 2x1, 1x2, 2x2 boyutlarında olabilir.

    Signals:
        layout_changed: Düzen değiştiğinde
        widget_added: Widget eklendiğinde (widget_code, row, col)
        widget_removed: Widget kaldırıldığında (widget_code)
        cell_clicked: Hücreye tıklandığında (row, col)
    """

    COLUMNS = 4
    MAX_ROWS = 10
    CELL_MIN_WIDTH = 200
    CELL_MIN_HEIGHT = 150
    SPACING = 12

    # Signals
    layout_changed = pyqtSignal()
    widget_added = pyqtSignal(str, int, int)  # widget_code, row, col
    widget_removed = pyqtSignal(str)
    cell_clicked = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._widgets: Dict[str, Tuple[BaseWidget, int, int, int, int]] = {}  # code -> (widget, row, col, width, height)
        self._edit_mode = False
        self._grid: List[List[GridCell]] = []

        self._setup_ui()
        self._init_grid()

    def _setup_ui(self):
        """UI yapısını oluşturur"""
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setSpacing(self.SPACING)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        # Sütun genişliklerini eşitle
        for col in range(self.COLUMNS):
            self.grid_layout.setColumnStretch(col, 1)
            self.grid_layout.setColumnMinimumWidth(col, self.CELL_MIN_WIDTH)

    def _init_grid(self):
        """Grid hücrelerini başlatır"""
        self._grid = []
        for row in range(self.MAX_ROWS):
            row_cells = []
            for col in range(self.COLUMNS):
                row_cells.append(GridCell(row=row, col=col))
            self._grid.append(row_cells)

    def set_edit_mode(self, enabled: bool):
        """
        Düzenleme modunu ayarlar

        Args:
            enabled: Düzenleme modu açık mı
        """
        self._edit_mode = enabled

        # Widget'ların düzenleme modunu güncelle
        for code, (widget, _, _, _, _) in self._widgets.items():
            widget.set_edit_mode(enabled)

        # Boş hücrelere placeholder ekle/kaldır
        self._update_placeholders()

    def _update_placeholders(self):
        """Boş hücrelere placeholder ekler veya kaldırır"""
        # Önce mevcut placeholder'ları kaldır
        for row in range(self.MAX_ROWS):
            for col in range(self.COLUMNS):
                item = self.grid_layout.itemAtPosition(row, col)
                if item and isinstance(item.widget(), WidgetPlaceholder):
                    item.widget().deleteLater()
                    self.grid_layout.removeItem(item)

        if not self._edit_mode:
            return

        # Kullanılan satır sayısını bul
        max_used_row = 0
        for code, (_, row, _, _, height) in self._widgets.items():
            max_used_row = max(max_used_row, row + height)

        # Bir satır daha ekle (yeni widget için)
        display_rows = min(max_used_row + 1, self.MAX_ROWS)

        # Boş hücrelere placeholder ekle
        for row in range(display_rows):
            for col in range(self.COLUMNS):
                if not self._grid[row][col].occupied:
                    placeholder = WidgetPlaceholder(row, col, self)
                    placeholder.clicked.connect(self._on_cell_clicked)
                    self.grid_layout.addWidget(placeholder, row, col)

    def _on_cell_clicked(self, row: int, col: int):
        """Hücreye tıklandığında"""
        self.cell_clicked.emit(row, col)

    def add_widget(
        self,
        widget: BaseWidget,
        row: int,
        col: int,
        width: int = 1,
        height: int = 1
    ) -> bool:
        """
        Widget ekler

        Args:
            widget: Eklenecek widget
            row: Satır
            col: Sütun
            width: Genişlik (1 veya 2)
            height: Yükseklik (1 veya 2)

        Returns:
            Başarılı ise True
        """
        # Sınır kontrolü
        if row < 0 or col < 0 or row + height > self.MAX_ROWS or col + width > self.COLUMNS:
            print(f"Widget sınır dışı: row={row}, col={col}, width={width}, height={height}")
            return False

        # Çakışma kontrolü
        if not self._can_place_widget(row, col, width, height, exclude_code=widget.widget_code):
            print(f"Widget çakışması: {widget.widget_code} at ({row}, {col})")
            return False

        # Eğer widget zaten varsa, önce kaldır
        if widget.widget_code in self._widgets:
            self.remove_widget(widget.widget_code)

        # Grid'e ekle
        self.grid_layout.addWidget(widget, row, col, height, width)

        # Hücreleri işaretle
        self._mark_cells(row, col, width, height, widget.widget_code)

        # Kaydet
        self._widgets[widget.widget_code] = (widget, row, col, width, height)

        # Event bağlantıları
        widget.remove_requested.connect(lambda: self.remove_widget(widget.widget_code))
        widget.set_edit_mode(self._edit_mode)

        self.widget_added.emit(widget.widget_code, row, col)
        self.layout_changed.emit()

        return True

    def remove_widget(self, widget_code: str) -> bool:
        """
        Widget kaldırır

        Args:
            widget_code: Widget kodu

        Returns:
            Başarılı ise True
        """
        if widget_code not in self._widgets:
            return False

        widget, row, col, width, height = self._widgets[widget_code]

        # Grid'den kaldır
        self.grid_layout.removeWidget(widget)

        # Hücreleri temizle
        self._clear_cells(row, col, width, height)

        # Widget'ı temizle
        widget.cleanup()
        widget.deleteLater()

        # Kayıttan sil
        del self._widgets[widget_code]

        self.widget_removed.emit(widget_code)
        self.layout_changed.emit()

        # Placeholder'ları güncelle
        if self._edit_mode:
            self._update_placeholders()

        return True

    def _can_place_widget(
        self,
        row: int,
        col: int,
        width: int,
        height: int,
        exclude_code: Optional[str] = None
    ) -> bool:
        """Widget yerleştirilebilir mi kontrol eder"""
        for r in range(row, row + height):
            for c in range(col, col + width):
                if r >= self.MAX_ROWS or c >= self.COLUMNS:
                    return False
                cell = self._grid[r][c]
                if cell.occupied and cell.widget_code != exclude_code:
                    return False
        return True

    def _mark_cells(self, row: int, col: int, width: int, height: int, widget_code: str):
        """Hücreleri işaretle"""
        for r in range(row, row + height):
            for c in range(col, col + width):
                self._grid[r][c].occupied = True
                self._grid[r][c].widget_code = widget_code

    def _clear_cells(self, row: int, col: int, width: int, height: int):
        """Hücreleri temizle"""
        for r in range(row, row + height):
            for c in range(col, col + width):
                self._grid[r][c].occupied = False
                self._grid[r][c].widget_code = None

    def get_widget(self, widget_code: str) -> Optional[BaseWidget]:
        """Widget'ı döner"""
        if widget_code in self._widgets:
            return self._widgets[widget_code][0]
        return None

    def get_all_widgets(self) -> Dict[str, BaseWidget]:
        """Tüm widget'ları döner"""
        return {code: data[0] for code, data in self._widgets.items()}

    def get_layout_data(self) -> Dict[str, Any]:
        """
        Mevcut düzeni JSON formatında döner

        Returns:
            Layout JSON
        """
        widgets_data = []

        for code, (widget, row, col, width, height) in self._widgets.items():
            widgets_data.append({
                "widget_code": code,
                "position": {"row": row, "col": col},
                "size": {"width": width, "height": height},
                "config": widget.get_config().config
            })

        return {
            "version": "1.0",
            "grid_columns": self.COLUMNS,
            "widgets": widgets_data
        }

    def clear_all(self):
        """Tüm widget'ları kaldırır"""
        codes = list(self._widgets.keys())
        for code in codes:
            self.remove_widget(code)

        self._init_grid()

    def refresh_all(self):
        """Tüm widget'ların verilerini yeniler"""
        for code, (widget, _, _, _, _) in self._widgets.items():
            try:
                widget.refresh_data()
            except Exception as e:
                print(f"Widget yenileme hatası ({code}): {e}")

    def find_empty_position(self, width: int = 1, height: int = 1) -> Optional[Tuple[int, int]]:
        """
        Boş pozisyon bulur

        Args:
            width: Widget genişliği
            height: Widget yüksekliği

        Returns:
            (row, col) veya None
        """
        for row in range(self.MAX_ROWS - height + 1):
            for col in range(self.COLUMNS - width + 1):
                if self._can_place_widget(row, col, width, height):
                    return (row, col)
        return None
