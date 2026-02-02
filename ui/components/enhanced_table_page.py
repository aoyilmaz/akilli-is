"""
Akıllı İş ERP - Gelişmiş Tablo Sayfası Bileşeni
Tablo, istatistikler ve sayfalama bir arada.
"""

from typing import List, Dict, Optional, Callable
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig
from ui.components.table_footer import TableFooter


class StatConfig:
    """İstatistik kartı yapılandırması"""

    def __init__(
        self,
        key: str,
        title: str,
        icon: str = None,
        color: str = None,
    ):
        self.key = key
        self.title = title
        self.icon = icon
        self.color = color


class EnhancedTablePage(QWidget):
    """
    Tablo + Footer (stats + pagination) içeren sayfa bileşeni.
    Liste sayfaları için standart yapı sağlar.
    """

    # Tablo sinyalleri (proxy)
    row_double_clicked = pyqtSignal(int)
    row_selected = pyqtSignal(int)
    filter_changed = pyqtSignal(dict)
    rows_filtered = pyqtSignal(int, int)

    # Footer sinyalleri (proxy)
    page_size_changed = pyqtSignal(int)
    next_page_clicked = pyqtSignal()
    prev_page_clicked = pyqtSignal()

    def __init__(
        self,
        table_id: str,
        columns: List[ColumnConfig],
        stats: List[StatConfig] = None,
        page_sizes: List[int] = None,
        default_page_size: int = 25,
        parent=None,
    ):
        super().__init__(parent)

        self._table_id = table_id
        self._columns = columns
        self._stats_config = stats or []
        self._page_sizes = page_sizes or [10, 25, 50, 100]
        self._default_page_size = default_page_size

        self._header_widget: Optional[QWidget] = None
        self._populate_row_func: Optional[Callable] = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI oluştur"""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(24, 24, 24, 24)
        self._layout.setSpacing(16)

        # Header slot (sonra set_header ile doldurulacak)
        self._header_slot_index = 0

        # Tablo
        self._table = EnhancedTableWidget(
            table_id=self._table_id,
            columns=self._columns,
            parent=self,
        )
        self._layout.addWidget(self._table)

        # Footer
        self._footer = TableFooter(self)
        self._layout.addWidget(self._footer)

        # İstatistik kartlarını ekle
        for stat in self._stats_config:
            self._footer.add_stat(stat.key, stat.title, stat.icon, stat.color)

        # Varsayılan sayfa boyutunu ayarla
        self._footer.set_page_size(self._default_page_size)

    def _connect_signals(self):
        """Sinyalleri bağla"""
        # Tablo -> dış
        self._table.row_double_clicked.connect(self.row_double_clicked.emit)
        self._table.row_selected.connect(self.row_selected.emit)
        self._table.filter_changed.connect(self.filter_changed.emit)
        self._table.rows_filtered.connect(self.rows_filtered.emit)

        # Footer -> dış
        self._footer.page_size_changed.connect(self.page_size_changed.emit)
        self._footer.next_page_clicked.connect(self.next_page_clicked.emit)
        self._footer.prev_page_clicked.connect(self.prev_page_clicked.emit)

    @property
    def table(self) -> EnhancedTableWidget:
        """Tabloya erişim"""
        return self._table

    @property
    def footer(self) -> TableFooter:
        """Footer'a erişim"""
        return self._footer

    def set_header(self, widget: QWidget):
        """Header widget'ı ayarla"""
        if self._header_widget:
            self._layout.removeWidget(self._header_widget)
            self._header_widget.deleteLater()

        self._header_widget = widget
        self._layout.insertWidget(0, widget)

    def set_populate_row_func(self, func: Callable):
        """Satır doldurma fonksiyonunu ayarla"""
        self._populate_row_func = func

    def load_data(self, items: List):
        """Tabloya veri yükle"""
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(items))

        visible_cols = self._table.get_logical_visible_columns()

        for row, item in enumerate(items):
            if self._populate_row_func:
                self._populate_row_func(self._table, row, item, visible_cols)

        self._table.setSortingEnabled(True)
        self._table.apply_saved_filters()

    def update_stats(self, stats: dict):
        """İstatistikleri güncelle"""
        self._footer.update_stats(stats)

    def update_pagination(
        self,
        current: int,
        total_pages: int,
        total_records: int = None,
    ):
        """Sayfalama bilgilerini güncelle"""
        self._footer.update_pagination(current, total_pages, total_records)

    def get_page_size(self) -> int:
        """Mevcut sayfa boyutunu döndür"""
        return self._footer.get_page_size()

    def set_standard_row_height(self, height: int):
        """Satır yüksekliğini ayarla"""
        self._table.set_standard_row_height(height)

    def set_filter_options(self, column_key: str, options: List[str]):
        """Filtre seçeneklerini ayarla"""
        self._table.set_filter_options(column_key, options)
