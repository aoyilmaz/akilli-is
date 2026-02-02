"""
Akıllı İş - Fiyat Listesi Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QTableWidgetItem,
    QMessageBox,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

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
        self._total_count = 0
        self._setup_ui()
        self._connect_signals()

        # Otomatik yenileme
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.timeout.connect(lambda: self.refresh_requested.emit())
        self._auto_refresh_timer.start(30000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Fiyat Listeleri",
            icon=ICONS.MONEY,
            show_search=True,
            show_add=True,
            add_text="Yeni Fiyat Listesi",
            search_placeholder="Ara... (kod, ad)",
            parent=self,
        )
        layout.addWidget(self.header)

        # Tablo
        columns = [
            ColumnConfig("code", "Kod", width=100),
            ColumnConfig("name", "Liste Adı", width=200, stretch=True),
            ColumnConfig("type", "Tür", width=80, filter_type="enum"),
            ColumnConfig("currency", "Para Birimi", width=100, filter_type="enum"),
            ColumnConfig("validity", "Geçerlilik", width=180),
            ColumnConfig("is_default", "Varsayılan", width=90, filter_type="enum"),
            ColumnConfig("items", "Kalem", width=80, filter_type="number"),
            ColumnConfig(
                "actions",
                "İşlemler",
                width=150,
                resizable=False,
                movable=False,
                hideable=False,
                filterable=False,
            ),
        ]

        self.table = EnhancedTableWidget(
            table_id="price_lists",
            columns=columns,
            parent=self,
        )
        self.table.set_standard_row_height(48)
        layout.addWidget(self.table)

        # Footer
        self._setup_footer(layout)

    def _setup_footer(self, layout: QVBoxLayout):
        """Footer - kayıt sayısı ve istatistikler"""
        footer = QFrame()
        footer.setProperty("class", "table-footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 8, 0, 0)
        footer_layout.setSpacing(16)

        # Sol: Kayıt sayısı
        self.count_label = QLabel("Toplam: 0 fiyat listesi")
        self.count_label.setProperty("class", "footer-count")
        footer_layout.addWidget(self.count_label)

        # İstatistik kartları (horizontal)
        self.stat_cards = {}
        self.stat_cards["total"] = MiniStatCard(
            "Toplam", "0", "info", orientation="horizontal", icon=ICONS.INVOICE
        )
        self.stat_cards["sales"] = MiniStatCard(
            "Satış", "0", "success", orientation="horizontal", icon=ICONS.EXPORT
        )
        self.stat_cards["purchase"] = MiniStatCard(
            "Alış", "0", "warning", orientation="horizontal", icon=ICONS.IMPORT
        )
        self.stat_cards["default"] = MiniStatCard(
            "Varsayılan", "0", "primary", orientation="horizontal", icon=ICONS.STAR
        )

        for card in self.stat_cards.values():
            footer_layout.addWidget(card)

        footer_layout.addStretch()

        # Sağ: Otomatik yenileme göstergesi
        refresh_indicator = QLabel("⟳")
        refresh_indicator.setProperty("class", "refresh-indicator")
        refresh_indicator.setToolTip("Otomatik yenileme: 30s")
        footer_layout.addWidget(refresh_indicator)

        layout.addWidget(footer)

    def _connect_signals(self):
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search)
        self.table.row_double_clicked.connect(self.view_clicked.emit)
        self.table.filter_changed.connect(self._update_visible_count)

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

        self._total_count = total
        self.count_label.setText(f"Toplam: {self._total_count} fiyat listesi")

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
        self._update_visible_count()

    def _update_visible_count(self, filters: dict = None):
        """Görünen satır sayısını güncelle"""
        visible_count = sum(
            1 for row in range(self.table.rowCount())
            if not self.table.isRowHidden(row)
        )
        if visible_count == self._total_count:
            self.count_label.setText(f"Toplam: {self._total_count} fiyat listesi")
        else:
            self.count_label.setText(
                f"Gösterilen: {visible_count} / {self._total_count} fiyat listesi"
            )

    def get_search_text(self) -> str:
        return self.header.get_search_text()

    def _confirm_delete(self, pl_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu fiyat listesini silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(pl_id)

    def showEvent(self, event):
        super().showEvent(event)
        self._auto_refresh_timer.start(30000)

    def hideEvent(self, event):
        super().hideEvent(event)
        self._auto_refresh_timer.stop()
