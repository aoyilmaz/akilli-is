"""
Akıllı İş ERP - Stok Listesi Sayfası
Stok kartlarını listeler, arama ve filtreleme sağlar.
"""

from decimal import Decimal
from typing import List
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidgetItem,
    QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QAction
import qtawesome as qta

from config.icons import ICONS
from config.styles import COLORS
from ui.components.page_header import PageHeader
from ui.components.enhanced_table import (
    EnhancedTableWidget,
    ColumnConfig,
    NumericTableWidgetItem,
)
from ui.components.table_footer import TableFooter
from core.export_manager import ExportManager


class StockListPage(QWidget):
    """
    Stok kartlarını listeleyen sayfa.
    """

    # Sinyaller (InventoryModule tarafından beklenenler)
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    duplicate_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()
    next_page_clicked = pyqtSignal()
    prev_page_clicked = pyqtSignal()
    page_size_changed = pyqtSignal(int)  # Sayfa boyutu değişti
    row_double_clicked = pyqtSignal(int)
    table_filters_changed = pyqtSignal(
        dict
    )  # Tablo içi filtreler değişti ve filtreleri taşıyor

    # Stok türleri (Sabitler)
    TYPE_NAMES = {
        "hammadde": "Hammadde",
        "mamul": "Mamul",
        "yari_mamul": "Yarı Mamul",
        "ambalaj": "Ambalaj",
        "sarf": "Sarf Malzemesi",
        "ticari": "Ticari Mal",
        "hizmet": "Hizmet",
        "diger": "Diğer",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating_from_backend = False  # Sonsuz döngüyü önlemek için
        self.setup_ui()

        # Arama için timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(500)
        self.search_timer.timeout.connect(lambda: self.refresh_requested.emit())

        # Otomatik yenileme timer
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.timeout.connect(lambda: self.refresh_requested.emit())
        self._auto_refresh_timer.start(30000)  # 30 saniye

    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Sayfa Başlığı
        self.header = PageHeader(
            title="Stok Kartları",
            icon=ICONS.INVENTORY,
            show_add=True,
            show_export=True,
            add_text="Yeni Stok Kartı",
            search_placeholder="Stok kodu, adı veya barkod ile ara...",
            parent=self,
        )

        # Export menüsü
        if self.header.export_btn:
            export_menu = ExportManager.create_export_menu(self, self._get_export_data)
            export_menu.addSeparator()
            label_action = QAction("Ürün Etiketi Bas", self)
            label_action.setIcon(qta.icon(ICONS.TAG, color="black"))
            label_action.triggered.connect(self._print_labels)
            export_menu.addAction(label_action)
            self.header.export_btn.setMenu(export_menu)

        layout.addWidget(self.header)

        # Tablo
        columns = [
            ColumnConfig("code", "Kod", width=120, filterable=True),
            ColumnConfig("name", "Stok Adı", width=250, stretch=True, filterable=True),
            ColumnConfig("type", "Tür", width=120, filter_type="enum"),
            ColumnConfig("category", "Kategori", width=150, filterable=True),
            ColumnConfig("unit", "Birim", width=80, filterable=True),
            ColumnConfig("quantity", "Miktar", width=100, filterable=True),
            ColumnConfig("min_stock", "Min. Stok", width=90, filterable=True),
            ColumnConfig("purchase_price", "Alış Fiyatı", width=110, filterable=True),
            ColumnConfig("sale_price", "Satış Fiyatı", width=110, filterable=True),
            ColumnConfig("stock_status", "Stok Durumu", width=120, filter_type="enum"),
            ColumnConfig("is_active", "Aktif", width=80, filter_type="enum"),
        ]

        self.table = EnhancedTableWidget(
            table_id="inventory_item_list", columns=columns, parent=self
        )
        self.table.set_standard_row_height(48)
        layout.addWidget(self.table)

        # Footer - sayfalama ve istatistikler
        self._setup_footer(layout)

        # Sinyal bağlantıları
        self.header.add_btn.clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search_changed)
        # Çift tıklama ile düzenleme devre dışı - kullanıcı sağ tık menüsünü kullanmalı
        # self.table.row_double_clicked.connect(self.row_double_clicked_handler)
        self.table.rows_filtered.connect(self.update_filtered_stats)

        # Context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Filtre seçeneklerini tanımla
        self.table.set_filter_options("type", sorted(list(self.TYPE_NAMES.values())))
        self.table.set_filter_options("is_active", ["Aktif", "Pasif"])

    def _setup_footer(self, layout: QVBoxLayout):
        """Footer - sayfalama ve istatistikler"""
        self.footer = TableFooter(self)

        # İstatistik kartlarını ekle
        self.footer.add_stat("total", "Toplam", ICONS.INVENTORY, COLORS["info"])
        self.footer.add_stat("normal", "Normal", ICONS.SUCCESS, COLORS["success"])
        self.footer.add_stat("low", "Düşük", ICONS.WARNING, COLORS["warning"])
        self.footer.add_stat("critical", "Kritik", ICONS.ERROR, COLORS["error"])
        self.footer.add_stat("out_of_stock", "Stok Yok", ICONS.DANGER, COLORS["error"])

        # Sinyalleri bağla
        self.footer.next_page_clicked.connect(self.next_page_clicked.emit)
        self.footer.prev_page_clicked.connect(self.prev_page_clicked.emit)
        self.footer.page_size_changed.connect(self.page_size_changed.emit)

        layout.addWidget(self.footer)

    def update_filtered_stats(self, visible, total):
        """Filtreleme sonrası backend'den güncel istatistikleri al"""
        # Backend'den veri yüklenirken tetikleniyorsa, sonsuz döngüye girme
        if self._updating_from_backend:
            return

        # Filtreleri al ve backend'den yeni veri iste
        filters = self.table.get_backend_filters()
        self.table_filters_changed.emit(filters)

    def row_double_clicked_handler(self, row):
        """Satıra çift tıklandığında item_id ile sinyal gönder"""
        item = self.table.item(row, 0)
        if item:
            item_id = item.data(Qt.ItemDataRole.UserRole)
            if item_id:
                self.edit_clicked.emit(item_id)
                self.row_double_clicked.emit(item_id)

    def update_stats(self, stats: dict):
        """İstatistikleri güncelle"""
        if not stats:
            return
        self.footer.update_stats(stats)

    def update_pagination(self, current: int, total_pages: int, total_records: int):
        """Sayfalama bilgilerini güncelle"""
        self.footer.update_pagination(current, total_pages, total_records)

    def get_page_size(self) -> int:
        """Mevcut sayfa boyutunu döndür"""
        return self.footer.get_page_size()

    def load_data(self, items: List):
        """Tabloya veri yükle"""
        self._updating_from_backend = True  # Flag'ı aç
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(items))

        # Tüm sütunları doldur (gizli olanlar dahil, böylece açıldığında dolu gelir)
        for row, item in enumerate(items):
            self._populate_row(row, item)

        self.table.setSortingEnabled(True)

        # Kaydedilmiş filtreleri uygula
        self.table.apply_saved_filters()
        self._updating_from_backend = False  # Flag'ı kapat

    def _populate_row(self, row, item):
        """Tek bir satırı doldur"""
        for col_idx, col_key in enumerate(self.table.column_order):
            if col_key == "code":
                cell = QTableWidgetItem(item.code)
                cell.setData(Qt.ItemDataRole.UserRole, item.id)
                if not item.is_active:
                    cell.setForeground(QColor(COLORS["text_muted"]))
                self.table.setItem(row, col_idx, cell)
            elif col_key == "name":
                cell = QTableWidgetItem(item.name)
                if not item.is_active:
                    cell.setForeground(QColor(COLORS["text_muted"]))
                self.table.setItem(row, col_idx, cell)
            elif col_key == "type":
                item_type = (
                    item.item_type.value
                    if hasattr(item.item_type, "value")
                    else item.item_type
                )
                type_name = self.TYPE_NAMES.get(item_type, "Diğer")
                cell = QTableWidgetItem(type_name)
                if not item.is_active:
                    cell.setForeground(QColor(COLORS["text_muted"]))
                self.table.setItem(row, col_idx, cell)
            elif col_key == "category":
                cat_text = item.category.name if item.category else "-"
                cell = QTableWidgetItem(cat_text)
                if not item.is_active:
                    cell.setForeground(QColor(COLORS["text_muted"]))
                self.table.setItem(row, col_idx, cell)
            elif col_key == "unit":
                unit_text = item.unit.code if item.unit else "-"
                cell = QTableWidgetItem(unit_text)
                if not item.is_active:
                    cell.setForeground(QColor(COLORS["text_muted"]))
                self.table.setItem(row, col_idx, cell)
            elif col_key == "quantity":
                qty = item.total_stock or Decimal(0)
                cell = NumericTableWidgetItem(qty, f"{qty:,.2f}")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                if not item.is_active:
                    cell.setForeground(QColor(COLORS["text_muted"]))
                self.table.setItem(row, col_idx, cell)
            elif col_key == "min_stock":
                ms = item.min_stock or Decimal(0)
                cell = NumericTableWidgetItem(ms, f"{ms:,.2f}")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                if not item.is_active:
                    cell.setForeground(QColor(COLORS["text_muted"]))
                self.table.setItem(row, col_idx, cell)
            elif col_key == "purchase_price":
                p = item.purchase_price or Decimal(0)
                cell = NumericTableWidgetItem(p, f"{p:,.2f} TL")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                if not item.is_active:
                    cell.setForeground(QColor(COLORS["text_muted"]))
                self.table.setItem(row, col_idx, cell)
            elif col_key == "sale_price":
                p = item.sale_price or Decimal(0)
                cell = NumericTableWidgetItem(p, f"{p:,.2f} TL")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                if not item.is_active:
                    cell.setForeground(QColor(COLORS["text_muted"]))
                self.table.setItem(row, col_idx, cell)
            elif col_key == "stock_status":
                cell = QTableWidgetItem()
                status = item.stock_status
                if status == "out_of_stock":
                    color = "#ef4444"
                    cell.setText("Stok Yok")
                    cell.setIcon(
                        qta.icon(ICONS.STATUS_ICONS["out_of_stock"], color=color)
                    )
                elif status == "critical":
                    color = "#f97316"
                    cell.setText("Kritik Seviye")
                    cell.setIcon(qta.icon(ICONS.STATUS_ICONS["critical"], color=color))
                elif status == "low":
                    color = "#eab308"
                    cell.setText("Düşük Stok")
                    cell.setIcon(qta.icon(ICONS.STATUS_ICONS["low"], color=color))
                else:
                    color = "#22c55e"
                    cell.setText("Normal")
                    cell.setIcon(qta.icon(ICONS.STATUS_ICONS["success"], color=color))
                cell.setForeground(QColor(color))
                if not item.is_active:
                    cell.setForeground(QColor(COLORS["text_muted"]))
                self.table.setItem(row, col_idx, cell)
            elif col_key == "is_active":
                cell = QTableWidgetItem()
                if item.is_active:
                    cell.setText("Aktif")
                    cell.setIcon(
                        qta.icon(ICONS.STATUS_ICONS["success"], color="#22c55e")
                    )
                    cell.setForeground(QColor("#22c55e"))
                else:
                    cell.setText("Pasif")
                    cell.setIcon(
                        qta.icon(
                            ICONS.STATUS_ICONS["passive"], color=COLORS["text_muted"]
                        )
                    )
                    cell.setForeground(QColor(COLORS["text_muted"]))
                self.table.setItem(row, col_idx, cell)

    def _on_search_changed(self, text: str):
        """Arama metni değiştiğinde timer başlat"""
        self.search_timer.stop()
        self.search_timer.start()

    def get_filters(self) -> dict:
        """Mevcut filtreleri döndür"""
        return {"keyword": self.header.get_search_text(), "is_active": None}

    def get_search_text(self) -> str:
        """Arama metnini döndür"""
        return self.header.get_search_text()

    def _get_export_data(self):
        """Export için tabloyu döndür"""
        return self.table

    def _print_labels(self):
        """Barkod etiketi yazdır"""
        pass

    def showEvent(self, event):
        """Sayfa görünür olduğunda otomatik yenilemeyi başlat"""
        super().showEvent(event)
        self._auto_refresh_timer.start(30000)

    def hideEvent(self, event):
        """Sayfa gizlendiğinde otomatik yenilemeyi durdur"""
        super().hideEvent(event)

    def _show_context_menu(self, pos):
        """Sağ tık context menüsü göster"""
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        item_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not item_id:
            return

        menu = QMenu(self)

        # Düzenle
        edit_action = QAction("Düzenle", self)
        edit_action.setIcon(qta.icon(ICONS.EDIT, color="#3498db"))
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(item_id))
        menu.addAction(edit_action)

        # Çoğalt
        duplicate_action = QAction("Çoğalt", self)
        duplicate_action.setIcon(qta.icon(ICONS.COPY, color="#8b5cf6"))
        duplicate_action.triggered.connect(lambda: self.duplicate_clicked.emit(item_id))
        menu.addAction(duplicate_action)

        menu.addSeparator()

        # Sil
        delete_action = QAction("Sil", self)
        delete_action.setIcon(qta.icon(ICONS.DELETE, color="#ef4444"))
        delete_action.triggered.connect(lambda: self._confirm_delete(item_id))
        menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _confirm_delete(self, item_id: int):
        """Silme onayı"""
        from PyQt6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "Stok Kartı Sil",
            "Bu stok kartını silmek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(item_id)
