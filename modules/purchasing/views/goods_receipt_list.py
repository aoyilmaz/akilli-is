"""
Akıllı İş - Mal Kabul Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from datetime import date
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QTableWidgetItem,
    QComboBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
)


class GoodsReceiptListPage(QWidget):
    """Mal kabul listesi."""

    # Sinyaller
    add_clicked = pyqtSignal()
    add_from_order_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    complete_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    STATUS_LABELS = {
        "draft": ("🔵 Taslak", "#64748b"),
        "completed": ("🟢 Tamamlandı", "#10b981"),
        "cancelled": ("⚫ İptal", "#475569"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.receipts = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Mal Kabul",
            icon="📥",
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Manuel Giriş",
            search_placeholder="Ara... (fiş no, tedarikçi)",
            parent=self,
        )

        # Siparişten ekle butonu
        from_order_btn = QPushButton("📦 Siparişten")
        from_order_btn.setProperty("class", "btn-secondary")
        from_order_btn.clicked.connect(self.add_from_order_clicked.emit)

        # Filtre ekle
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("🔵 Taslak", "draft")
        self.status_filter.addItem("🟢 Tamamlandı", "completed")
        self.status_filter.addItem("⚫ İptal", "cancelled")
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

        layout.addWidget(self.header)

        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.stat_cards = {}
        self.stat_cards["total"] = MiniStatCard("📊 Toplam", "0", "#6366f1")
        self.stat_cards["draft"] = MiniStatCard("🔵 Taslak", "0", "#64748b")
        self.stat_cards["completed"] = MiniStatCard("🟢 Tamamlandı", "0", "#10b981")
        self.stat_cards["today"] = MiniStatCard("📅 Bugün", "0", "#f59e0b")

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
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

        self.table = EnhancedTableWidget(
            table_id="goods_receipts",
            columns=columns,
            parent=self,
        )
        layout.addWidget(self.table)

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
                self._add_action_buttons(row, col_idx, rec)

        self.table.setRowHeight(row, 52)

    def _format_date(self, dt) -> str:
        if dt:
            if isinstance(dt, date):
                return dt.strftime("%d.%m.%Y")
            return str(dt)
        return "-"

    def _add_action_buttons(self, row: int, col: int, rec: dict):
        btn_widget = QWidget()
        btn_widget.setProperty("class", "action-button-group")
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(2, 2, 2, 2)
        btn_layout.setSpacing(2)

        rec_id = rec.get("id")
        status = rec.get("status", "draft")

        # Görüntüle
        view_btn = QPushButton("👁")
        view_btn.setFixedSize(28, 26)
        view_btn.clicked.connect(
            lambda checked, rid=rec_id: self.view_clicked.emit(rid)
        )
        btn_layout.addWidget(view_btn)

        if status == "draft":
            edit_btn = QPushButton("✏")
            edit_btn.setFixedSize(28, 26)
            edit_btn.clicked.connect(
                lambda checked, rid=rec_id: self.edit_clicked.emit(rid)
            )
            btn_layout.addWidget(edit_btn)

            complete_btn = QPushButton("✓")
            complete_btn.setFixedSize(28, 26)
            complete_btn.setToolTip("Tamamla (Stok Girişi)")
            complete_btn.clicked.connect(
                lambda checked, rid=rec_id: self.complete_clicked.emit(rid)
            )
            btn_layout.addWidget(complete_btn)

            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(28, 26)
            del_btn.clicked.connect(
                lambda checked, rid=rec_id: self._confirm_delete(rid)
            )
            btn_layout.addWidget(del_btn)

        self.table.setCellWidget(row, col, btn_widget)

    def _update_stats(self):
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
