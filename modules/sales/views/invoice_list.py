"""
Akıllı İş - Faturalar Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from datetime import date
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QTableWidgetItem,
    QComboBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from config.icons import ICONS
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
)


class InvoiceListPage(QWidget):
    """
    Faturalar listesi sayfası.
    Filtre özelliği nedeniyle doğrudan BaseListPage yerine
    özelleştirilmiş bir yapı kullanır.
    """

    # Sinyaller
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    issue_clicked = pyqtSignal(int)
    payment_clicked = pyqtSignal(int)
    cancel_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

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
        super().__init__(parent)
        self.invoices = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI yapısını oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Page Header (arama ve butonlar için)
        self.header = PageHeader(
            title="Faturalar",
            icon=ICONS.INVOICE,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Fatura",
            search_placeholder="Ara... (fatura no, müşteri)",
            parent=self,
        )

        # Filtreyi header'a ekle (search'ten önce)
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("Taslak", "draft")
        self.status_filter.addItem("Kesildi", "issued")
        self.status_filter.addItem("Kısmi Ödendi", "partial_paid")
        self.status_filter.addItem("Ödendi", "paid")
        self.status_filter.addItem("Vadesi Geçti", "overdue")
        self.status_filter.addItem("İptal", "cancelled")
        self.status_filter.setMinimumWidth(160)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)

        # Header layout'unu özelleştir
        # Search input'tan önce filter ekle
        if self.header.search_input:
            h_layout = self.header.header_layout()
            idx = h_layout.indexOf(self.header.search_input)
            h_layout.insertWidget(idx, self.status_filter)

        layout.addWidget(self.header)

        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.stat_cards = {}
        self.stat_cards["total"] = MiniStatCard(
            "Toplam", "0", "info", icon=ICONS.INVOICE
        )
        stats_layout.addWidget(self.stat_cards["total"])

        self.stat_cards["draft"] = MiniStatCard("Taslak", "0", "info", icon=ICONS.TIME)
        stats_layout.addWidget(self.stat_cards["draft"])

        self.stat_cards["issued"] = MiniStatCard(
            "Kesildi", "0", "primary", icon=ICONS.EXPORT
        )
        stats_layout.addWidget(self.stat_cards["issued"])

        self.stat_cards["paid"] = MiniStatCard(
            "Ödendi", "0", "success", icon=ICONS.CHECK
        )
        stats_layout.addWidget(self.stat_cards["paid"])

        self.stat_cards["overdue"] = MiniStatCard(
            "Vadesi Geçti", "0", "error", icon=ICONS.DANGER
        )
        stats_layout.addWidget(self.stat_cards["overdue"])

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        columns = [
            ColumnConfig("invoice_no", "Fatura No", width=120),
            ColumnConfig("date", "Tarih", width=100),
            ColumnConfig("customer", "Müşteri", width=200, stretch=True),
            ColumnConfig("total", "Toplam Tutar", width=110),
            ColumnConfig("paid", "Ödenen", width=100),
            ColumnConfig("remaining", "Kalan", width=100),
            ColumnConfig("due_date", "Vade", width=100),
            ColumnConfig("status", "Durum", width=120),
            ColumnConfig(
                "actions",
                "İşlemler",
                width=180,
                resizable=False,
                movable=False,
                hideable=False,
            ),
        ]

        self.table = EnhancedTableWidget(
            table_id="invoices",
            columns=columns,
            parent=self,
        )
        self.table.set_standard_row_height(48)
        layout.addWidget(self.table)

    def _connect_signals(self):
        """Sinyalleri bağla"""
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search)
        self.table.row_double_clicked.connect(self.view_clicked.emit)

    def load_data(self, invoices: list):
        """Verileri yükle"""
        self.invoices = invoices
        self._apply_filter()

    def _apply_filter(self):
        """Filtreyi uygula"""
        status_filter = self.status_filter.currentData()

        filtered = self.invoices
        if status_filter:
            filtered = [i for i in self.invoices if i.get("status") == status_filter]

        self._display_data(filtered)
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
            cancel_btn.setToolTip("İptal Et")  # Override tooltip if needed
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

        self.stat_cards["total"].update_value(str(total))
        self.stat_cards["draft"].update_value(str(draft))
        self.stat_cards["issued"].update_value(str(issued))
        self.stat_cards["paid"].update_value(str(paid))
        self.stat_cards["overdue"].update_value(str(overdue))

    def _on_search(self, text: str):
        """Tabloda arama yap"""
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount() - 1):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def _on_filter_changed(self):
        """Filtre değiştiğinde"""
        self._apply_filter()

    def _confirm_delete(self, inv_id: int):
        """Silme onayı"""
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu faturayı silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(inv_id)
