"""
Akıllı İş - Satınalma Faturası Liste Sayfası
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


class PurchaseInvoiceListPage(QWidget):
    """Satınalma faturası listesi."""

    # Sinyaller
    add_clicked = pyqtSignal()
    add_from_receipt_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    confirm_clicked = pyqtSignal(int)
    pay_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    STATUS_LABELS = {
        "draft": ("🔵 Taslak", "#64748b"),
        "received": ("📥 Alındı", "#3b82f6"),
        "partial": ("🟡 Kısmi Ödendi", "#f59e0b"),
        "paid": ("🟢 Ödendi", "#10b981"),
        "overdue": ("🔴 Vadesi Geçti", "#ef4444"),
        "cancelled": ("⚫ İptal", "#475569"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.invoices = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Satınalma Faturaları",
            icon="📄",
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Fatura",
            search_placeholder="Ara... (fatura no, tedarikçi)",
            parent=self,
        )

        # Mal Kabulden ekle butonu
        from_receipt_btn = QPushButton("📦 Mal Kabulden")
        from_receipt_btn.setProperty("class", "btn-secondary")
        from_receipt_btn.clicked.connect(self.add_from_receipt_clicked.emit)

        # Filtre ekle
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("🔵 Taslak", "draft")
        self.status_filter.addItem("📥 Alındı", "received")
        self.status_filter.addItem("🟡 Kısmi Ödendi", "partial")
        self.status_filter.addItem("🟢 Ödendi", "paid")
        self.status_filter.addItem("🔴 Vadesi Geçti", "overdue")
        self.status_filter.addItem("⚫ İptal", "cancelled")
        self.status_filter.setMinimumWidth(150)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)

        if self.header.search_input:
            h_layout = self.header.header_layout()
            idx = h_layout.indexOf(self.header.search_input)
            h_layout.insertWidget(idx, self.status_filter)
            # Add butonu öncesine Mal Kabulden butonunu ekle
            if self.header.add_btn:
                add_idx = h_layout.indexOf(self.header.add_btn)
                h_layout.insertWidget(add_idx, from_receipt_btn)

        layout.addWidget(self.header)

        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.stat_cards = {}
        self.stat_cards["total"] = MiniStatCard("📊 Toplam", "0", "#6366f1")
        self.stat_cards["open"] = MiniStatCard("📥 Açık", "0", "#f59e0b")
        self.stat_cards["paid"] = MiniStatCard("🟢 Ödendi", "0", "#10b981")
        self.stat_cards["overdue"] = MiniStatCard("🔴 Vadesi Geçti", "0", "#ef4444")
        self.stat_cards["balance"] = MiniStatCard("💰 Borç", "₺0", "#8b5cf6")

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        columns = [
            ColumnConfig("invoice_no", "Fatura No", width=120),
            ColumnConfig("date", "Tarih", width=100),
            ColumnConfig("due_date", "Vade", width=100),
            ColumnConfig("supplier", "Tedarikçi", width=200, stretch=True),
            ColumnConfig("total", "Toplam", width=110),
            ColumnConfig("paid", "Ödenen", width=110),
            ColumnConfig("balance", "Bakiye", width=110),
            ColumnConfig("status", "Durum", width=120),
            ColumnConfig(
                "actions",
                "İşlemler",
                width=160,
                resizable=False,
                movable=False,
                hideable=False,
            ),
        ]

        self.table = EnhancedTableWidget(
            table_id="purchase_invoices",
            columns=columns,
            parent=self,
        )
        layout.addWidget(self.table)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search)
        self.table.row_double_clicked.connect(self.view_clicked.emit)

    def load_data(self, invoices: list):
        self.invoices = invoices
        self._apply_filter()

    def _apply_filter(self):
        status_filter = self.status_filter.currentData()
        filtered = self.invoices
        if status_filter:
            filtered = [i for i in self.invoices if i.get("status") == status_filter]
        self._display_data(filtered)
        self._update_stats()

    def _display_data(self, invoices: list):
        self.table.setRowCount(len(invoices))
        visible_cols = self.table.get_visible_columns()

        for row, inv in enumerate(invoices):
            self._populate_row(row, inv, visible_cols)

    def _populate_row(self, row: int, inv: dict, visible_cols: list):
        inv_id = inv.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "invoice_no":
                item = QTableWidgetItem(inv.get("invoice_no", ""))
                item.setData(Qt.ItemDataRole.UserRole, inv_id)
                self.table.setItem(row, col_idx, item)

            elif col_key == "date":
                self.table.setItem(
                    row,
                    col_idx,
                    QTableWidgetItem(self._format_date(inv.get("invoice_date"))),
                )

            elif col_key == "due_date":
                self.table.setItem(
                    row,
                    col_idx,
                    QTableWidgetItem(self._format_date(inv.get("due_date"))),
                )

            elif col_key == "supplier":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(inv.get("supplier_name", "") or "-")
                )

            elif col_key == "total":
                total = inv.get("total", 0) or 0
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(f"₺{float(total):,.2f}")
                )

            elif col_key == "paid":
                paid = inv.get("paid_amount", 0) or 0
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(f"₺{float(paid):,.2f}")
                )

            elif col_key == "balance":
                balance = inv.get("balance", 0) or 0
                item = QTableWidgetItem(f"₺{float(balance):,.2f}")
                if float(balance) > 0:
                    item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, col_idx, item)

            elif col_key == "status":
                status = inv.get("status", "draft")
                label, _ = self.STATUS_LABELS.get(status, ("Taslak", "#64748b"))
                self.table.setItem(row, col_idx, QTableWidgetItem(label))

            elif col_key == "actions":
                self._add_action_buttons(row, col_idx, inv)

        self.table.setRowHeight(row, 52)

    def _format_date(self, dt) -> str:
        if dt:
            if isinstance(dt, date):
                return dt.strftime("%d.%m.%Y")
            return str(dt)
        return "-"

    def _add_action_buttons(self, row: int, col: int, inv: dict):
        btn_widget = QWidget()
        btn_widget.setProperty("class", "action-button-group")
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(2, 2, 2, 2)
        btn_layout.setSpacing(2)

        inv_id = inv.get("id")
        status = inv.get("status", "draft")

        # Görüntüle
        view_btn = QPushButton("👁")
        view_btn.setFixedSize(28, 26)
        view_btn.clicked.connect(
            lambda checked, iid=inv_id: self.view_clicked.emit(iid)
        )
        btn_layout.addWidget(view_btn)

        if status == "draft":
            edit_btn = QPushButton("✏")
            edit_btn.setFixedSize(28, 26)
            edit_btn.clicked.connect(
                lambda checked, iid=inv_id: self.edit_clicked.emit(iid)
            )
            btn_layout.addWidget(edit_btn)

            confirm_btn = QPushButton("✓")
            confirm_btn.setFixedSize(28, 26)
            confirm_btn.setToolTip("Onayla")
            confirm_btn.clicked.connect(
                lambda checked, iid=inv_id: self.confirm_clicked.emit(iid)
            )
            btn_layout.addWidget(confirm_btn)

            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(28, 26)
            del_btn.clicked.connect(
                lambda checked, iid=inv_id: self._confirm_delete(iid)
            )
            btn_layout.addWidget(del_btn)

        elif status in ["received", "partial", "overdue"]:
            pay_btn = QPushButton("💳")
            pay_btn.setFixedSize(28, 26)
            pay_btn.setToolTip("Ödeme Kaydet")
            pay_btn.clicked.connect(
                lambda checked, iid=inv_id: self.pay_clicked.emit(iid)
            )
            btn_layout.addWidget(pay_btn)

        self.table.setCellWidget(row, col, btn_widget)

    def _update_stats(self):
        total = len(self.invoices)
        open_count = sum(
            1
            for i in self.invoices
            if i.get("status") in ["received", "partial", "overdue"]
        )
        paid = sum(1 for i in self.invoices if i.get("status") == "paid")
        overdue = sum(1 for i in self.invoices if i.get("status") == "overdue")
        total_balance = sum(float(i.get("balance", 0) or 0) for i in self.invoices)

        self.stat_cards["total"].update_value(str(total))
        self.stat_cards["open"].update_value(str(open_count))
        self.stat_cards["paid"].update_value(str(paid))
        self.stat_cards["overdue"].update_value(str(overdue))
        self.stat_cards["balance"].update_value(f"₺{total_balance:,.0f}")

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

    def _confirm_delete(self, inv_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu faturayı silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(inv_id)
