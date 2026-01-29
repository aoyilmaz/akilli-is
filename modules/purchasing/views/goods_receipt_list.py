"""
Akıllı İş - Mal Kabul Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QTableWidgetItem,
    QComboBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta

from ui.components import (
    BaseListPage,
    ColumnConfig,
)
from config.icons import ICONS


class GoodsReceiptListPage(BaseListPage):
    """Mal kabul listesi."""

    # Sinyaller (Ek sinyaller)
    add_from_order_clicked = pyqtSignal()
    complete_clicked = pyqtSignal(int)

    STATUS_LABELS = {
        "draft": ("Taslak", "#64748b"),
        "completed": ("Tamamlandı", "#10b981"),
        "cancelled": ("İptal", "#475569"),
    }

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("receipt_no", "Fiş No", width=120),
            ColumnConfig("date", "Tarih", width=100),
            ColumnConfig("supplier", "Tedarikçi", width=200, stretch=True),
            ColumnConfig("order_no", "Sipariş No", width=120),
            ColumnConfig("warehouse", "Depo", width=120),
            ColumnConfig("items", "Kalem", width=60),
            ColumnConfig("status", "Durum", width=110),
            ColumnConfig(
                "actions",
                "İşlemler",
                width=150,
                resizable=False,
                movable=False,
                hideable=False,
            ),
        ]

        super().__init__(
            title="Mal Kabul",
            icon=ICONS.INVENTORY,
            table_id="goods_receipts",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Manuel Giriş",
            search_placeholder="Ara... (fiş no, tedarikçi)",
            parent=parent,
        )

        self.receipts = []
        self._setup_filters()
        self._setup_stat_cards()

    def _setup_filters(self):
        # Siparişten ekle butonu
        from_order_btn = QPushButton("Siparişten")
        from_order_btn.setIcon(qta.icon(ICONS.INVENTORY, color="#ffffff"))
        from_order_btn.setProperty("class", "btn-secondary")
        from_order_btn.clicked.connect(self.add_from_order_clicked.emit)

        # Filtre ekle
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("Taslak", "draft")
        self.status_filter.addItem("Tamamlandı", "completed")
        self.status_filter.addItem("İptal", "cancelled")
        self.status_filter.setMinimumWidth(150)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)

        if self.header.search_input:
            h_layout = self.header.header_layout()
            idx = h_layout.indexOf(self.header.search_input)
            h_layout.insertWidget(idx, self.status_filter)
            # Add butonu öncesine siparişten ekle butonunu ekle
            if self.header.add_btn:
                add_idx = h_layout.indexOf(self.header.add_btn)
                h_layout.insertWidget(add_idx, from_order_btn)

    def _setup_stat_cards(self):
        self.add_stat_card("total", "Toplam", "0", "info", ICONS.INVENTORY)
        self.add_stat_card("draft", "Taslak", "0", "warning", ICONS.TIME)
        self.add_stat_card("completed", "Tamamlandı", "0", "success", ICONS.CHECK)
        self.add_stat_card("today", "Bugün", "0", "info", ICONS.TIME)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search)
        self.table.row_double_clicked.connect(self.view_clicked.emit)

    def load_data(self, receipts: list):
        self.receipts = receipts
        self._apply_filter()

    def _apply_filter(self):
        status_filter = self.status_filter.currentData()
        filtered = self.receipts
        if status_filter:
            filtered = [r for r in self.receipts if r.get("status") == status_filter]
        self._display_data(filtered)
        self._update_stats()

    def _display_data(self, receipts: list):
        self.table.setRowCount(len(receipts))
        visible_cols = self.table.get_visible_columns()

        for row, rec in enumerate(receipts):
            self._populate_row(row, rec, visible_cols)

    def _populate_row(self, row: int, rec: dict, visible_cols: list):
        rec_id = rec.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "receipt_no":
                item = QTableWidgetItem(rec.get("receipt_no", ""))
                item.setData(Qt.ItemDataRole.UserRole, rec_id)
                self.table.setItem(row, col_idx, item)

            elif col_key == "date":
                self.table.setItem(
                    row,
                    col_idx,
                    QTableWidgetItem(self._format_date(rec.get("receipt_date"))),
                )

            elif col_key == "supplier":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(rec.get("supplier_name", "") or "-")
                )

            elif col_key == "order_no":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(rec.get("order_no", "") or "-")
                )

            elif col_key == "warehouse":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(rec.get("warehouse_name", "") or "-")
                )

            elif col_key == "items":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(str(rec.get("total_items", 0)))
                )

            elif col_key == "status":
                status = rec.get("status", "draft")
                label, _ = self.STATUS_LABELS.get(status, ("Taslak", "#64748b"))
                self.table.setItem(row, col_idx, QTableWidgetItem(label))

            elif col_key == "actions":
                status = rec.get("status", "draft")
                actions = ["view"]

                if status == "draft":
                    actions.extend(["edit", "complete", "delete"])

                callbacks = {
                    "view": lambda _, rid=rec_id: self.view_clicked.emit(rid),
                    "edit": lambda _, rid=rec_id: self.edit_clicked.emit(rid),
                    "delete": lambda _, rid=rec_id: self._confirm_delete(rid),
                    "complete": lambda _, rid=rec_id: self.complete_clicked.emit(rid),
                }

                # Özel butonlar için manuel gruplama
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(4, 2, 4, 2)
                layout.setSpacing(4)

                from ui.components.action_buttons import (
                    create_view_button,
                    create_edit_button,
                    create_delete_button,
                    create_approve_button,
                )

                if "view" in actions:
                    btn = create_view_button(widget)
                    btn.clicked.connect(callbacks["view"])
                    layout.addWidget(btn)

                if "edit" in actions:
                    btn = create_edit_button(widget)
                    btn.clicked.connect(callbacks["edit"])
                    layout.addWidget(btn)

                if "complete" in actions:
                    btn = create_approve_button(widget)
                    btn.setToolTip("Tamamla (Stok Girişi)")
                    btn.clicked.connect(callbacks["complete"])
                    layout.addWidget(btn)

                if "delete" in actions:
                    btn = create_delete_button(widget)
                    btn.clicked.connect(callbacks["delete"])
                    layout.addWidget(btn)

                layout.addStretch()
                self.table.setCellWidget(row, col_idx, widget)

    def _format_date(self, dt) -> str:
        from datetime import date

        if dt:
            if isinstance(dt, date):
                return dt.strftime("%d.%m.%Y")
            return str(dt)
        return "-"

    def _update_stats(self):
        from datetime import date

        total = len(self.receipts)
        draft = sum(1 for r in self.receipts if r.get("status") == "draft")
        completed = sum(1 for r in self.receipts if r.get("status") == "completed")
        today = sum(1 for r in self.receipts if r.get("receipt_date") == date.today())

        self.stat_cards["total"].update_value(str(total))
        self.stat_cards["draft"].update_value(str(draft))
        self.stat_cards["completed"].update_value(str(completed))
        self.stat_cards["today"].update_value(str(today))

    def _on_search(self, text: str):
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = any(
                self.table.item(row, col)
                and text in self.table.item(row, col).text().lower()
                for col in range(self.table.columnCount() - 1)
            )
            self.table.setRowHidden(row, not match)

    def _on_filter_changed(self):
        self._apply_filter()

    def _confirm_delete(self, rec_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu mal kabul fişini silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(rec_id)
