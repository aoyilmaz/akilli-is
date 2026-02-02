"""
Akıllı İş - Faturalar Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from datetime import date
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QTableWidgetItem,
)
from PyQt6.QtCore import Qt, pyqtSignal

from config.icons import ICONS
from ui.components import (
    BaseListPage,
    ColumnConfig,
)


class InvoiceListPage(BaseListPage):
    """
    Faturalar listesi sayfası.
    BaseListPage kullanarak Excel tipi sütun filtreleme destekler.
    """

    # Ek sinyaller
    issue_clicked = pyqtSignal(int)
    payment_clicked = pyqtSignal(int)
    cancel_clicked = pyqtSignal(int)

    # Durum etiketleri
    STATUS_LABELS = {
        "draft": ("Taslak", "#64748b"),
        "issued": ("Kesildi", "#3b82f6"),
        "partial_paid": ("Kısmi Ödendi", "#f59e0b"),
        "paid": ("Ödendi", "#10b981"),
        "overdue": ("Vadesi Geçti", "#ef4444"),
        "cancelled": ("İptal", "#475569"),
    }

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("invoice_no", "Fatura No", width=120),
            ColumnConfig("date", "Tarih", width=100, filter_type="date"),
            ColumnConfig("customer", "Müşteri", width=200, stretch=True),
            ColumnConfig("total", "Toplam Tutar", width=110, filter_type="number"),
            ColumnConfig("paid", "Ödenen", width=100, filter_type="number"),
            ColumnConfig("remaining", "Kalan", width=100, filter_type="number"),
            ColumnConfig("due_date", "Vade", width=100, filter_type="date"),
            ColumnConfig("status", "Durum", width=120, filter_type="enum"),
            ColumnConfig(
                "actions",
                "İşlemler",
                width=180,
                resizable=False,
                movable=False,
                hideable=False,
                filterable=False,
            ),
        ]

        super().__init__(
            title="Faturalar",
            icon=ICONS.INVOICE,
            table_id="invoices",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_add=True,
            add_text="Yeni Fatura",
            search_placeholder="Ara... (fatura no, müşteri)",
            parent=parent,
        )

        self.invoices = []
        self._setup_stat_cards()

    def _setup_stat_cards(self):
        """İstatistik kartlarını oluştur"""
        self.add_stat_card("total", "Toplam", "0", "info", ICONS.INVOICE)
        self.add_stat_card("draft", "Taslak", "0", "info", ICONS.TIME)
        self.add_stat_card("issued", "Kesildi", "0", "primary", ICONS.EXPORT)
        self.add_stat_card("paid", "Ödendi", "0", "success", ICONS.CHECK)
        self.add_stat_card("overdue", "Vadesi Geçti", "0", "error", ICONS.DANGER)

    def load_data(self, invoices: list):
        """Verileri yükle"""
        self.invoices = invoices
        self._display_data(invoices)
        self._update_stats()

    def _display_data(self, invoices: list):
        """Tabloya verileri yükle"""
        self.table.setRowCount(len(invoices))
        visible_cols = self.table.get_visible_columns()

        for row, inv in enumerate(invoices):
            self._populate_row(row, inv, visible_cols)

    def _populate_row(self, row: int, inv: dict, visible_cols: list):
        """Tek satırı doldur"""
        inv_id = inv.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "invoice_no":
                item = QTableWidgetItem(inv.get("invoice_no", ""))
                item.setData(Qt.ItemDataRole.UserRole, inv_id)
                self.table.setItem(row, col_idx, item)

            elif col_key == "date":
                inv_date = inv.get("invoice_date")
                date_str = self._format_date(inv_date)
                self.table.setItem(row, col_idx, QTableWidgetItem(date_str))

            elif col_key == "customer":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(inv.get("customer_name", "") or "-")
                )

            elif col_key == "total":
                total = inv.get("total_amount", 0) or 0
                self.table.setItem(row, col_idx, QTableWidgetItem(f"{total:,.2f}"))

            elif col_key == "paid":
                paid = inv.get("paid_amount", 0) or 0
                self.table.setItem(row, col_idx, QTableWidgetItem(f"{paid:,.2f}"))

            elif col_key == "remaining":
                total = inv.get("total_amount", 0) or 0
                paid = inv.get("paid_amount", 0) or 0
                remaining = total - paid
                item = QTableWidgetItem(f"{remaining:,.2f}")
                if remaining > 0:
                    item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, col_idx, item)

            elif col_key == "due_date":
                due_date = inv.get("due_date")
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(self._format_date(due_date))
                )

            elif col_key == "status":
                status = inv.get("status", "draft")
                status_text, _ = self.STATUS_LABELS.get(status, ("Taslak", "#64748b"))
                self.table.setItem(row, col_idx, QTableWidgetItem(status_text))

            elif col_key == "actions":
                self._add_action_buttons(row, col_idx, inv)

    def _format_date(self, dt) -> str:
        """Tarihi formatla"""
        if dt:
            if isinstance(dt, date):
                return dt.strftime("%d.%m.%Y")
            return str(dt)
        return "-"

    def _add_action_buttons(self, row: int, col: int, inv: dict):
        """İşlem butonlarını ekle"""
        from ui.components.action_buttons import (
            create_view_button,
            create_edit_button,
            create_delete_button,
            create_cancel_button,
            create_custom_button,
        )

        btn_widget = QWidget()
        btn_widget.setProperty("class", "action-button-group")
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(4, 2, 4, 2)
        btn_layout.setSpacing(4)

        inv_id = inv.get("id")
        status = inv.get("status", "draft")

        # Görüntüle
        view_btn = create_view_button(btn_widget)
        view_btn.clicked.connect(lambda: self.view_clicked.emit(inv_id))
        btn_layout.addWidget(view_btn)

        # Düzenle (sadece taslak)
        if status == "draft":
            edit_btn = create_edit_button(btn_widget)
            edit_btn.clicked.connect(lambda: self.edit_clicked.emit(inv_id))
            btn_layout.addWidget(edit_btn)

            # Fatura Kes (Custom)
            issue_btn = create_custom_button(
                btn_widget, ICONS.EXPORT, "Fatura Kes", "success"
            )
            issue_btn.clicked.connect(lambda: self.issue_clicked.emit(inv_id))
            btn_layout.addWidget(issue_btn)

        # Ödeme Kaydet (Custom)
        if status in ["issued", "partial_paid", "overdue"]:
            pay_btn = create_custom_button(
                btn_widget, ICONS.PAYMENT, "Ödeme Kaydet", "warning"
            )
            pay_btn.clicked.connect(lambda: self.payment_clicked.emit(inv_id))
            btn_layout.addWidget(pay_btn)

        # İptal
        if status in ["draft", "issued"]:
            cancel_btn = create_cancel_button(btn_widget)
            cancel_btn.setToolTip("İptal Et")
            cancel_btn.clicked.connect(lambda: self.cancel_clicked.emit(inv_id))
            btn_layout.addWidget(cancel_btn)

        # Sil (sadece taslak)
        if status == "draft":
            del_btn = create_delete_button(btn_widget)
            del_btn.clicked.connect(lambda: self._confirm_delete(inv_id))
            btn_layout.addWidget(del_btn)

        btn_layout.addStretch()
        self.table.setCellWidget(row, col, btn_widget)

    def _update_stats(self):
        """İstatistikleri güncelle"""
        total = len(self.invoices)
        draft = sum(1 for i in self.invoices if i.get("status") == "draft")
        issued = sum(1 for i in self.invoices if i.get("status") == "issued")
        paid = sum(1 for i in self.invoices if i.get("status") == "paid")
        overdue = sum(1 for i in self.invoices if i.get("status") == "overdue")

        self.update_stat_card("total", str(total))
        self.update_stat_card("draft", str(draft))
        self.update_stat_card("issued", str(issued))
        self.update_stat_card("paid", str(paid))
        self.update_stat_card("overdue", str(overdue))

    def _confirm_delete(self, inv_id: int):
        """Silme onayı"""
        if self.confirm_delete("fatura"):
            self.delete_clicked.emit(inv_id)
