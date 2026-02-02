"""
Akıllı İş ERP - Temel Liste Sayfası Bileşeni
Tüm liste sayfalarının türeyeceği temel sınıf.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QMessageBox,
)
from PyQt6.QtCore import pyqtSignal, QTimer

# from typing import List, Optional  <- Dict kullanılmıyor artık
from typing import List, Optional

from ui.components.page_header import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


class BaseListPage(QWidget):
    """
    Tüm liste sayfalarının türeyeceği temel sınıf.

    Sağladığı özellikler:
    - PageHeader (başlık, arama, butonlar)
    - EnhancedTableWidget (gelişmiş tablo)
    - Footer (kayıt sayısı + istatistik kartları)
    - Otomatik yenileme
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
    next_page_clicked = pyqtSignal()
    prev_page_clicked = pyqtSignal()
    page_size_changed = pyqtSignal(int)

    # Varsayılan otomatik yenileme aralığı (ms) - 30 saniye
    DEFAULT_AUTO_REFRESH_INTERVAL = 30000

    def __init__(
        self,
        title: str,
        icon: str,
        table_id: str,
        columns: List[ColumnConfig],
        user_id: Optional[int] = None,
        show_stats: bool = True,
        show_search: bool = True,
        show_refresh: bool = False,  # Varsayılan False - otomatik yenileme var
        show_add: bool = True,
        show_export: bool = False,
        add_text: str = "Yeni Ekle",
        search_placeholder: str = "Ara...",
        auto_refresh: bool = True,
        auto_refresh_interval: int = None,
        count_label_text: str = "kayıt",
        parent=None,
    ):
        super().__init__(parent)

        self.title = title
        self.icon = icon
        self.table_id = table_id
        self.columns = columns
        self.user_id = user_id
        self.show_stats = show_stats
        self._count_label_text = count_label_text
        self._auto_refresh_enabled = auto_refresh
        self._auto_refresh_interval = (
            auto_refresh_interval or self.DEFAULT_AUTO_REFRESH_INTERVAL
        )

        # Stat kartları referansları (şimdilik boş, TableFooter yönetiyor)
        # self.stat_cards: Dict[str, MiniStatCard] = {}

        # Toplam ve görünen kayıt sayısı
        self._total_count = 0

        # Otomatik yenileme timer'ı
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.timeout.connect(self._on_auto_refresh)

        self._setup_ui(
            show_search,
            show_refresh,
            show_add,
            show_export,
            add_text,
            search_placeholder,
        )
        self._connect_signals()

        # Otomatik yenilemeyi başlat
        if self._auto_refresh_enabled:
            self.start_auto_refresh()

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

        # Tablo
        self.table = EnhancedTableWidget(
            table_id=self.table_id,
            columns=self.columns,
            user_id=self.user_id,
            parent=self,
        )
        self.table.set_standard_row_height(48)
        layout.addWidget(self.table)

        # Footer - kayıt sayısı, istatistikler ve sayfalama
        self._setup_footer(layout)

    def _setup_footer(self, layout: QVBoxLayout):
        """Tablo altı footer alanını oluştur"""
        from ui.components.table_footer import TableFooter
        from config.icons import ICONS

        self.footer = TableFooter(self)

        # Varsayılan toplam kayıt kartı (key='total_records' çakışmayı önlemek için)
        self.footer.add_stat("total_records", "Toplam", ICONS.LIST, "#3498db")

        # Sinyalleri bağla
        self.footer.page_size_changed.connect(self._on_page_size_changed)
        self.footer.next_page_clicked.connect(self.next_page_clicked.emit)
        self.footer.prev_page_clicked.connect(self.prev_page_clicked.emit)

        layout.addWidget(self.footer)

    def _on_page_size_changed(self, size: int):
        """Sayfa boyutu değiştiğinde"""
        pass

    def _connect_signals(self):
        """Sinyalleri bağla"""
        # Header sinyalleri
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search)
        self.header.export_clicked.connect(self.export_clicked.emit)

        # Tablo sinyalleri
        self.table.row_double_clicked.connect(self.view_clicked.emit)
        self.table.filter_changed.connect(self._update_visible_count)

    def _on_search(self, text: str):
        """Tabloda arama yap (sütun filtreleriyle birlikte çalışır)"""
        search_text = text.lower()
        for row in range(self.table.rowCount()):
            # Önce arama eşleşmesini kontrol et
            search_match = not search_text  # Boş arama = tüm satırlar eşleşir
            if search_text:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item and search_text in item.text().lower():
                        search_match = True
                        break

            # Sütun filtreleriyle birlikte değerlendir
            filter_match = self.table._row_matches_filters(row)

            self.table.setRowHidden(row, not (search_match and filter_match))

        # Görünen satır sayısını güncelle
        self._update_visible_count()

    # === Otomatik Yenileme ===

    def _on_auto_refresh(self):
        """Otomatik yenileme tetiklendiğinde"""
        self.refresh_requested.emit()

    def start_auto_refresh(self):
        """Otomatik yenilemeyi başlat"""
        if not self._auto_refresh_timer.isActive():
            self._auto_refresh_timer.start(self._auto_refresh_interval)

    def stop_auto_refresh(self):
        """Otomatik yenilemeyi durdur"""
        self._auto_refresh_timer.stop()

    def set_auto_refresh_interval(self, interval_ms: int):
        """Otomatik yenileme aralığını değiştir"""
        self._auto_refresh_interval = interval_ms
        if self._auto_refresh_timer.isActive():
            self._auto_refresh_timer.setInterval(interval_ms)

    # === Stat Card Yönetimi ===

    def add_stat_card(
        self,
        key,
        title,
        value="0",
        color="primary",
        icon="",
    ):
        """İstatistik kartı ekle (TableFooter üzerinden)"""
        self.footer.add_stat(key, title, icon, color)
        self.footer.update_stat(key, value)

    def update_stat_card(self, key: str, value: str):
        """İstatistik kartı değerini güncelle"""
        self.footer.update_stat(key, value)

    # === Kayıt Sayısı ===

    def _update_visible_count(self, filters: dict = None):
        """Görünen satır sayısını güncelle"""
        visible_count = 0
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                visible_count += 1

        # text = self._count_label_text (artık kullanılmıyor)
        if visible_count == self._total_count:
            self.footer.update_stat("total_records", str(self._total_count))
        else:
            self.footer.update_stat(
                "total_records", f"{visible_count} / {self._total_count}"
            )

    def update_count(self, count: int, label: str = None):
        """Toplam kayıt sayısını güncelle"""
        self._total_count = count
        self.footer.update_stat("total_records", str(count))

    # === Tablo Yönetimi ===

    def clear_table(self):
        """Tabloyu temizle"""
        self.table.setRowCount(0)
        self.update_count(0)

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

    def get_search_text(self) -> str:
        """Mevcut arama metnini döndür"""
        return self.header.get_search_text()

    def clear_search(self):
        """Arama kutusunu temizle"""
        self.header.clear_search()

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

    def showEvent(self, event):
        """Sayfa görünür olduğunda otomatik yenilemeyi başlat"""
        super().showEvent(event)
        if self._auto_refresh_enabled:
            self.start_auto_refresh()

    def hideEvent(self, event):
        """Sayfa gizlendiğinde otomatik yenilemeyi durdur"""
        super().hideEvent(event)
        self.stop_auto_refresh()
