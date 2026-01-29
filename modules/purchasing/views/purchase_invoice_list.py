"""
Akıllı İş - Satınalma Faturası Liste Sayfası
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

from ui.components import (
    BaseListPage,
    ColumnConfig,
)
from config.icons import ICONS


class PurchaseInvoiceListPage(BaseListPage):
    """Satınalma faturası listesi."""

    # Sinyaller (Ek sinyaller)
    add_from_receipt_clicked = pyqtSignal()
    confirm_clicked = pyqtSignal(int)
    pay_clicked = pyqtSignal(int)

    STATUS_LABELS = {
        "draft": ("🔵 Taslak", "#64748b"),
        "received": ("📥 Alındı", "#3b82f6"),
        "partial": ("🟡 Kısmi Ödendi", "#f59e0b"),
        "paid": ("🟢 Ödendi", "#10b981"),
        "overdue": ("🔴 Vadesi Geçti", "#ef4444"),
        "cancelled": ("⚫ İptal", "#475569"),
    }

    def __init__(self, parent=None):
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

        super().__init__(
            title="Satınalma Faturaları",
            icon=ICONS.INVOICE,
            table_id="purchase_invoices",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Fatura",
            search_placeholder="Ara... (fatura no, tedarikçi)",
            parent=parent,
        )

        self.invoices = []
        self._setup_filters()
        self._setup_stat_cards()

    def _setup_filters(self):
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

    def _setup_stat_cards(self):
        self.add_stat_card("total", "Toplam", "0", "info", ICONS.INVENTORY)
        self.add_stat_card("open", "Açık", "0", "warning", ICONS.TIME)
        self.add_stat_card("paid", "Ödendi", "0", "success", ICONS.CHECK)
        self.add_stat_card("overdue", "Vadesi Geçti", "0", "danger", ICONS.DANGER)
        self.add_stat_card("balance", "Borç", "₺0", "danger", ICONS.MONEY)

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
                symbol = inv.get("currency_symbol", "₺")
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(f"{symbol}{float(total):,.2f}")
                )

            elif col_key == "paid":
                paid = inv.get("paid_amount", 0) or 0
                symbol = inv.get("currency_symbol", "₺")
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(f"{symbol}{float(paid):,.2f}")
                )

            elif col_key == "balance":
                balance = inv.get("balance", 0) or 0
                symbol = inv.get("currency_symbol", "₺")
                item = QTableWidgetItem(f"{symbol}{float(balance):,.2f}")
                if float(balance) > 0:
                    item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, col_idx, item)

            elif col_key == "status":
                status = inv.get("status", "draft")
                label, _ = self.STATUS_LABELS.get(status, ("Taslak", "#64748b"))
                self.table.setItem(row, col_idx, QTableWidgetItem(label))

            elif col_key == "actions":
                status = inv.get("status", "draft")
                actions = ["view"]

                if status == "draft":
                    actions.extend(["edit", "confirm", "delete"])
                elif status in ["received", "partial", "overdue"]:
                    actions.append("pay")

                callbacks = {
                    "view": lambda _, rid=inv_id: self.view_clicked.emit(rid),
                    "edit": lambda _, rid=inv_id: self.edit_clicked.emit(rid),
                    "delete": lambda _, rid=inv_id: self._confirm_delete(rid),
                    "confirm": lambda _, rid=inv_id: self.confirm_clicked.emit(rid),
                    "pay": lambda _, rid=inv_id: self.pay_clicked.emit(rid),
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
                    create_custom_button,
                )

                if "view" in actions:
                    btn = create_view_button(widget)
                    btn.clicked.connect(callbacks["view"])
                    layout.addWidget(btn)

                if "edit" in actions:
                    btn = create_edit_button(widget)
                    btn.clicked.connect(callbacks["edit"])
                    layout.addWidget(btn)

                if "confirm" in actions:
                    btn = create_approve_button(widget)
                    btn.setToolTip("Onayla")
                    btn.clicked.connect(callbacks["confirm"])
                    layout.addWidget(btn)

                if "pay" in actions:
                    btn = create_custom_button(
                        widget, ICONS.PAYMENT, "Ödeme Kaydet", "green"
                    )
                    btn.clicked.connect(callbacks["pay"])
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
