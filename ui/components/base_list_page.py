"""
Akıllı İş ERP - Temel Liste Sayfası Bileşeni
Tüm liste sayfalarının türeyeceği temel sınıf.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QMessageBox,
)
from PyQt6.QtCore import pyqtSignal
from typing import List, Dict, Optional

from ui.components.page_header import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig
from ui.components.stat_cards import MiniStatCard, ScrollableCardContainer


class BaseListPage(QWidget):
    """
    Tüm liste sayfalarının türeyeceği temel sınıf.

    Sağladığı özellikler:
    - PageHeader (başlık, arama, butonlar)
    - İstatistik kartları alanı
    - EnhancedTableWidget (gelişmiş tablo)
    - Standart sinyaller ve event'ler
    - Tutarlı layout ve stil
    """

    # Standart sinyaller
    refresh_requested = pyqtSignal()
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    export_clicked = pyqtSignal()

    def __init__(
        self,
        title: str,
        icon: str,
        table_id: str,
        columns: List[ColumnConfig],
        user_id: Optional[int] = None,
        show_stats: bool = True,
        show_search: bool = True,
        show_refresh: bool = True,
        show_add: bool = True,
        show_export: bool = False,
        add_text: str = "Yeni Ekle",
        search_placeholder: str = "Ara...",
        parent=None,
    ):
        super().__init__(parent)

        self.title = title
        self.icon = icon
        self.table_id = table_id
        self.columns = columns
        self.user_id = user_id
        self.show_stats = show_stats

        # Stat kartları referansları
        self.stat_cards: Dict[str, MiniStatCard] = {}

        self._setup_ui(
            show_search,
            show_refresh,
            show_add,
            show_export,
            add_text,
            search_placeholder,
        )
        self._connect_signals()

    def _setup_ui(
        self,
        show_search,
        show_refresh,
        show_add,
        show_export,
        add_text,
        search_placeholder,
    ):
        """Ana UI yapısını oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Page Header
        self.header = PageHeader(
            title=self.title,
            icon=self.icon,
            show_search=show_search,
            show_refresh=show_refresh,
            show_add=show_add,
            show_export=show_export,
            add_text=add_text,
            search_placeholder=search_placeholder,
            parent=self,
        )
        layout.addWidget(self.header)

        # İstatistik Kartları Alanı
        if self.show_stats:
            self.stats_container = ScrollableCardContainer()
            self.stats_layout = self.stats_container.layout
            self.stats_layout.addStretch()
            layout.addWidget(self.stats_container)
        else:
            self.stats_layout = None

        # Tablo
        self.table = EnhancedTableWidget(
            table_id=self.table_id,
            columns=self.columns,
            user_id=self.user_id,
            parent=self,
        )
        layout.addWidget(self.table)

    def _connect_signals(self):
        """Sinyalleri bağla"""
        # Header sinyalleri
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search)
        self.header.export_clicked.connect(self.export_clicked.emit)

        # Tablo sinyalleri
        self.table.row_double_clicked.connect(self.view_clicked.emit)

    def _on_search(self, text: str):
        """Tabloda arama yap"""
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    # === Stat Card Yönetimi ===

    def add_stat_card(
        self,
        key: str,
        title: str,
        value: str = "0",
        color: str = "#007acc",
        icon: str = "📊",
    ) -> Optional[MiniStatCard]:
        """İstatistik kartı ekle"""
        if not self.stats_layout:
            return None

        card = MiniStatCard(f"{icon} {title}", value, color)
        self.stat_cards[key] = card

        # Stretch'ten önce ekle
        self.stats_layout.insertWidget(self.stats_layout.count() - 1, card)
        return card

    def update_stat_card(self, key: str, value: str):
        """İstatistik kartı değerini güncelle"""
        if key in self.stat_cards:
            self.stat_cards[key].update_value(value)

    # === Tablo Yönetimi ===

    def clear_table(self):
        """Tabloyu temizle"""
        self.table.setRowCount(0)

    def set_row_count(self, count: int):
        """Satır sayısını ayarla"""
        self.table.setRowCount(count)

    def get_selected_id(self) -> Optional[int]:
        """Seçili satırın ID'sini al"""
        return self.table.get_selected_id()

    def set_user_id(self, user_id: int):
        """Kullanıcı ID'sini ayarla (tablo ayarları için)"""
        self.user_id = user_id
        self.table.set_user_id(user_id)

    # === Yardımcı Metodlar ===

    def confirm_delete(self, item_name: str = "öğe") -> bool:
        """Silme onayı al"""
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            f"Bu {item_name}yi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def show_error(self, title: str, message: str):
        """Hata mesajı göster"""
        QMessageBox.critical(self, title, message)

    def show_info(self, title: str, message: str):
        """Bilgi mesajı göster"""
        QMessageBox.information(self, title, message)
