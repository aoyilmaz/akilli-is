"""
Akıllı İş - Fiyat Listesi Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QTableWidgetItem,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta

from config.icons import ICONS
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
)


class PriceListListPage(QWidget):
    """Fiyat listesi listesi sayfası."""

    # Sinyaller
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.price_lists = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Fiyat Listeleri",
            icon=ICONS.MONEY,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Fiyat Listesi",
            search_placeholder="Ara... (kod, ad)",
            parent=self,
        )
        layout.addWidget(self.header)

        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.stat_cards = {}
        self.stat_cards["total"] = MiniStatCard(
            "Toplam", "0", "info", icon=ICONS.INVOICE
        )
        self.stat_cards["sales"] = MiniStatCard(
            "Satış", "0", "success", icon=ICONS.EXPORT
        )
        self.stat_cards["purchase"] = MiniStatCard(
            "Alış", "0", "warning", icon=ICONS.IMPORT
        )
        self.stat_cards["default"] = MiniStatCard(
            "Varsayılan", "0", "primary", icon=ICONS.STAR
        )

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        columns = [
            ColumnConfig("code", "Kod", width=100),
            ColumnConfig("name", "Liste Adı", width=200, stretch=True),
            ColumnConfig("type", "Tür", width=80),
            ColumnConfig("currency", "Para Birimi", width=100),
            ColumnConfig("validity", "Geçerlilik", width=180),
            ColumnConfig("is_default", "Varsayılan", width=90),
            ColumnConfig("items", "Kalem", width=80),
            ColumnConfig(
                "actions",
                "İşlemler",
                width=150,
                resizable=False,
                movable=False,
                hideable=False,
            ),
        ]

        self.table = EnhancedTableWidget(
            table_id="price_lists",
            columns=columns,
            parent=self,
        )
        layout.addWidget(self.table)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search)
        self.table.row_double_clicked.connect(self.view_clicked.emit)

    def load_data(self, price_lists: list):
        self.price_lists = price_lists
        self.table.setRowCount(len(price_lists))

        # İstatistikler
        total = len(price_lists)
        sales_count = sum(1 for p in price_lists if p.get("list_type") == "sales")
        purchase_count = total - sales_count
        default = sum(1 for p in price_lists if p.get("is_default"))

        self.stat_cards["total"].update_value(str(total))
        self.stat_cards["sales"].update_value(str(sales_count))
        self.stat_cards["purchase"].update_value(str(purchase_count))
        self.stat_cards["default"].update_value(str(default))

        # Tabloyu doldur
        visible_cols = self.table.get_visible_columns()
        for row, pl in enumerate(price_lists):
            self._populate_row(row, pl, visible_cols)

    def _populate_row(self, row: int, pl: dict, visible_cols: list):
        pl_id = pl.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "code":
                item = QTableWidgetItem(pl.get("code", ""))
                item.setData(Qt.ItemDataRole.UserRole, pl_id)
                self.table.setItem(row, col_idx, item)

            elif col_key == "name":
                self.table.setItem(row, col_idx, QTableWidgetItem(pl.get("name", "")))

            elif col_key == "type":
                list_type = pl.get("list_type", "sales")
                type_text = "Satış" if list_type == "sales" else "Alış"
                self.table.setItem(row, col_idx, QTableWidgetItem(type_text))

            elif col_key == "currency":
                curr = pl.get("currency", "TRY")
                self.table.setItem(row, col_idx, QTableWidgetItem(curr))

            elif col_key == "validity":
                v_from = pl.get("valid_from")
                v_until = pl.get("valid_until")
                validity = ""
                if v_from:
                    validity = str(v_from)
                if v_until:
                    validity += f" - {v_until}"
                if not validity:
                    validity = "Süresiz"
                self.table.setItem(row, col_idx, QTableWidgetItem(validity))

            elif col_key == "is_default":
                is_default = pl.get("is_default", False)
                text = "Evet" if is_default else "-"
                item = QTableWidgetItem(text)
                if is_default:
                    item.setForeground(Qt.GlobalColor.green)
                self.table.setItem(row, col_idx, item)

            elif col_key == "items":
                item_count = str(pl.get("item_count", 0))
                self.table.setItem(row, col_idx, QTableWidgetItem(item_count))

            elif col_key == "actions":
                self._add_action_buttons(row, col_idx, pl_id)

    def _add_action_buttons(self, row: int, col: int, pl_id: int):
        callbacks = {
            "view": lambda pid=pl_id: self.view_clicked.emit(pid),
            "edit": lambda pid=pl_id: self.edit_clicked.emit(pid),
            "delete": lambda pid=pl_id: self._confirm_delete(pid),
        }
        widget = self.table.create_action_widget(
            pl_id, ["view", "edit", "delete"], callbacks
        )
        self.table.setCellWidget(row, col, widget)

    def _on_search(self, text: str):
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            # İlk 4 kolona bak
            for col in range(min(4, self.table.columnCount())):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def _confirm_delete(self, pl_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu fiyat listesini silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(pl_id)
