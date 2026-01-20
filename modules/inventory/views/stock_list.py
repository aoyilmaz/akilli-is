"""
Akıllı İş - Stok Kartları Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidgetItem,
    QComboBox,
    QMenu,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QAction

from config import COLORS
from database.models import ItemType
from core.export_manager import ExportManager
from core.label_manager import LabelManager
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
)


class StockListPage(QWidget):
    """Stok kartları liste sayfası."""

    # Sinyaller
    item_selected = pyqtSignal(int)
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    TYPE_NAMES = {
        ItemType.HAMMADDE: "🧱 Hammadde",
        ItemType.MAMUL: "📦 Mamül",
        ItemType.YARI_MAMUL: "⚙️ Yarı Mamül",
        ItemType.AMBALAJ: "🎁 Ambalaj",
        ItemType.SARF: "🔧 Sarf",
        ItemType.TICARI: "🏷️ Ticari",
        ItemType.HIZMET: "💼 Hizmet",
        ItemType.DIGER: "📋 Diğer",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items_data = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Stok Kartları",
            icon="📦",
            show_search=True,
            show_refresh=True,
            show_add=True,
            show_export=True,
            add_text="Yeni Stok Kartı",
            search_placeholder="Stok kodu, adı veya barkod ile ara...",
            parent=self,
        )

        # Export menüsüne etiket ekleme
        if self.header.export_btn:
            export_menu = ExportManager.create_export_menu(self, self._get_export_data)
            export_menu.addSeparator()
            label_action = QAction("🏷️ Ürün Etiketi Bas", self)
            label_action.triggered.connect(self._print_labels)
            export_menu.addAction(label_action)
            self.header.export_btn.setMenu(export_menu)

        # Filtreleri header'a ekle
        self.type_combo = QComboBox()
        self.type_combo.addItem("Tümü", None)
        self.type_combo.addItem("🧱 Hammadde", ItemType.HAMMADDE)
        self.type_combo.addItem("📦 Mamül", ItemType.MAMUL)
        self.type_combo.addItem("⚙️ Yarı Mamül", ItemType.YARI_MAMUL)
        self.type_combo.addItem("🎁 Ambalaj", ItemType.AMBALAJ)
        self.type_combo.addItem("🔧 Sarf", ItemType.SARF)
        self.type_combo.addItem("🏷️ Ticari", ItemType.TICARI)
        self.type_combo.setMinimumWidth(130)
        self.type_combo.setFixedHeight(36)
        self.type_combo.currentIndexChanged.connect(self._do_search)

        self.status_combo = QComboBox()
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem("✅ Normal", "normal")
        self.status_combo.addItem("⚠️ Düşük Stok", "low")
        self.status_combo.addItem("🔴 Kritik", "critical")
        self.status_combo.addItem("❌ Stok Yok", "out_of_stock")
        self.status_combo.setMinimumWidth(120)
        self.status_combo.setFixedHeight(36)
        self.status_combo.currentIndexChanged.connect(self._do_search)

        if self.header.search_input:
            h_layout = self.header.header_layout()
            idx = h_layout.indexOf(self.header.search_input)
            h_layout.insertWidget(idx, QLabel("Tür:"))
            h_layout.insertWidget(idx + 1, self.type_combo)
            h_layout.insertWidget(idx + 2, QLabel("Durum:"))
            h_layout.insertWidget(idx + 3, self.status_combo)

        layout.addWidget(self.header)

        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.stat_cards = {}
        self.stat_cards["total"] = MiniStatCard("📊 Toplam", "0", "#6366f1")
        self.stat_cards["normal"] = MiniStatCard("✅ Normal", "0", "#10b981")
        self.stat_cards["low"] = MiniStatCard("⚠️ Düşük", "0", "#f59e0b")
        self.stat_cards["critical"] = MiniStatCard("🔴 Kritik", "0", "#ef4444")

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        columns = [
            ColumnConfig("code", "Kod", width=100),
            ColumnConfig("name", "Stok Adı", width=280, stretch=True),
            ColumnConfig("type", "Tür", width=100),
            ColumnConfig("category", "Kategori", width=120),
            ColumnConfig("unit", "Birim", width=70),
            ColumnConfig("quantity", "Miktar", width=100),
            ColumnConfig("min_stock", "Min. Stok", width=90),
            ColumnConfig("purchase_price", "Alış Fiyatı", width=110),
            ColumnConfig("sale_price", "Satış Fiyatı", width=110),
            ColumnConfig("status", "Durum", width=100),
        ]

        self.table = EnhancedTableWidget(
            table_id="stock_items",
            columns=columns,
            parent=self,
        )
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.table)

        # Alt bilgi
        footer_layout = QHBoxLayout()
        self.count_label = QLabel("Toplam: 0 kayıt")
        footer_layout.addWidget(self.count_label)
        footer_layout.addStretch()
        self.value_label = QLabel("Toplam Değer: ₺0,00")
        footer_layout.addWidget(self.value_label)
        layout.addLayout(footer_layout)

        # Arama debounce timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._do_search)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search_changed)
        self.table.row_double_clicked.connect(self.edit_clicked.emit)

    def load_data(self, items: list):
        """Tabloyu verilerle doldur"""
        self.items_data = items
        self.table.setRowCount(len(items))
        visible_cols = self.table.get_visible_columns()

        total_value = Decimal(0)
        normal_count = low_count = critical_count = 0

        for row, item in enumerate(items):
            self._populate_row(row, item, visible_cols)

            # İstatistikler
            status = item.stock_status
            if status == "normal":
                normal_count += 1
            elif status == "low":
                low_count += 1
            elif status in ["critical", "out_of_stock"]:
                critical_count += 1

            # Toplam değer
            total_stock = item.total_stock or Decimal(0)
            purchase_price = item.purchase_price or Decimal(0)
            total_value += total_stock * purchase_price

        # İstatistik kartlarını güncelle
        self.stat_cards["total"].update_value(str(len(items)))
        self.stat_cards["normal"].update_value(str(normal_count))
        self.stat_cards["low"].update_value(str(low_count))
        self.stat_cards["critical"].update_value(str(critical_count))

        self.count_label.setText(f"Toplam: {len(items)} kayıt")
        self.value_label.setText(f"Toplam Değer: ₺{total_value:,.2f}")

    def _populate_row(self, row: int, item, visible_cols: list):
        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "code":
                cell = QTableWidgetItem(item.code)
                cell.setData(Qt.ItemDataRole.UserRole, item.id)
                cell.setForeground(QColor("#818cf8"))
                self.table.setItem(row, col_idx, cell)

            elif col_key == "name":
                self.table.setItem(row, col_idx, QTableWidgetItem(item.name))

            elif col_key == "type":
                type_text = self.TYPE_NAMES.get(item.item_type, "📋 Diğer")
                self.table.setItem(row, col_idx, QTableWidgetItem(type_text))

            elif col_key == "category":
                cat_text = item.category.name if item.category else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(cat_text))

            elif col_key == "unit":
                unit_text = item.unit.code if item.unit else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(unit_text))

            elif col_key == "quantity":
                total_stock = item.total_stock or Decimal(0)
                cell = QTableWidgetItem(f"{total_stock:,.2f}")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, cell)

            elif col_key == "min_stock":
                min_stock = item.min_stock or Decimal(0)
                cell = QTableWidgetItem(f"{min_stock:,.2f}")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, cell)

            elif col_key == "purchase_price":
                price = item.purchase_price or Decimal(0)
                cell = QTableWidgetItem(f"₺{price:,.2f}")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, cell)

            elif col_key == "sale_price":
                price = item.sale_price or Decimal(0)
                cell = QTableWidgetItem(f"₺{price:,.2f}")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, cell)

            elif col_key == "status":
                status = item.stock_status
                cell = QTableWidgetItem()
                if status == "out_of_stock":
                    cell.setText("❌ Stok Yok")
                    cell.setForeground(QColor(COLORS["error"]))
                elif status == "critical":
                    cell.setText("🔴 Kritik")
                    cell.setForeground(QColor(COLORS["error"]))
                elif status == "low":
                    cell.setText("⚠️ Düşük")
                    cell.setForeground(QColor(COLORS["warning"]))
                else:
                    cell.setText("✅ Normal")
                    cell.setForeground(QColor(COLORS["success"]))
                self.table.setItem(row, col_idx, cell)

        self.table.setRowHeight(row, 48)

    def _on_search_changed(self, text: str):
        self.search_timer.stop()
        self.search_timer.start(300)

    def _do_search(self):
        self.refresh_requested.emit()

    def get_filters(self) -> dict:
        return {
            "keyword": (
                self.header.search_input.text().strip()
                if self.header.search_input
                else ""
            ),
            "item_type": self.type_combo.currentData(),
            "stock_status": self.status_combo.currentData(),
        }

    def _get_export_data(self):
        return ExportManager.extract_data_from_table(self.table)

    def _print_labels(self):
        data = self._get_export_data()
        LabelManager.print_product_labels(self, data)

    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        item_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)
        view_action = QAction("👁 Görüntüle", self)
        view_action.triggered.connect(lambda: self.item_selected.emit(item_id))
        menu.addAction(view_action)

        edit_action = QAction("✏️ Düzenle", self)
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(item_id))
        menu.addAction(edit_action)

        menu.addSeparator()

        movement_action = QAction("📦 Stok Hareketi", self)
        menu.addAction(movement_action)

        history_action = QAction("📋 Hareket Geçmişi", self)
        menu.addAction(history_action)

        menu.addSeparator()

        delete_action = QAction("🗑 Sil", self)
        delete_action.triggered.connect(lambda: self._confirm_delete(item_id))
        menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _confirm_delete(self, item_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu stok kartını silmek istediğinize emin misiniz?\n\nBu işlem geri alınamaz.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(item_id)
