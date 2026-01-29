"""
Akıllı İş - Satış Teklifleri Liste Sayfası
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
    QLabel,
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


class SalesQuoteListPage(QWidget):
    """Satış teklifleri listesi sayfası."""

    # Sinyaller
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    send_clicked = pyqtSignal(int)
    accept_clicked = pyqtSignal(int)
    reject_clicked = pyqtSignal(int)
    convert_to_order_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    STATUS_LABELS = {
        "draft": ("Taslak", "#64748b"),
        "sent": ("Gönderildi", "#3b82f6"),
        "accepted": ("Kabul Edildi", "#10b981"),
        "rejected": ("Reddedildi", "#ef4444"),
        "ordered": ("Siparişe Dönüştü", "#8b5cf6"),
        "expired": ("Süresi Doldu", "#f59e0b"),
        "cancelled": ("İptal", "#475569"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.quotes = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Satış Teklifleri",
            icon=ICONS.INVOICE,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Teklif",
            search_placeholder="Ara... (teklif no, müşteri)",
            parent=self,
        )

        # Filtre
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("Taslak", "draft")
        self.status_filter.addItem("Gönderildi", "sent")
        self.status_filter.addItem("Kabul Edildi", "accepted")
        self.status_filter.addItem("Reddedildi", "rejected")
        self.status_filter.addItem("Siparişe Dönüştü", "ordered")
        self.status_filter.addItem("Süresi Doldu", "expired")
        self.status_filter.addItem("İptal", "cancelled")
        self.status_filter.setMinimumWidth(180)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)

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
        self.stat_cards["draft"] = MiniStatCard("Taslak", "0", "info", icon=ICONS.TIME)
        self.stat_cards["sent"] = MiniStatCard(
            "Gönderildi", "0", "primary", icon=ICONS.EXPORT
        )
        self.stat_cards["accepted"] = MiniStatCard(
            "Kabul", "0", "success", icon=ICONS.CHECK
        )
        self.stat_cards["rejected"] = MiniStatCard(
            "Red", "0", "error", icon=ICONS.CLOSE
        )

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        columns = [
            ColumnConfig("quote_no", "Teklif No", width=120),
            ColumnConfig("date", "Tarih", width=100),
            ColumnConfig("customer", "Müşteri", width=200, stretch=True),
            ColumnConfig("total", "Toplam Tutar", width=120),
            ColumnConfig("items", "Kalem", width=60),
            ColumnConfig("valid_until", "Geçerlilik", width=100),
            ColumnConfig("status", "Durum", width=130),
            ColumnConfig("currency", "Para Birimi", width=80),
            ColumnConfig(
                "actions",
                "İşlemler",
                width=200,
                resizable=False,
                movable=False,
                hideable=False,
            ),
        ]

        self.table = EnhancedTableWidget(
            table_id="sales_quotes",
            columns=columns,
            parent=self,
        )
        layout.addWidget(self.table)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search)
        self.table.row_double_clicked.connect(self.view_clicked.emit)

    def load_data(self, quotes: list):
        self.quotes = quotes
        self._apply_filter()

    def _apply_filter(self):
        status_filter = self.status_filter.currentData()
        filtered = self.quotes
        if status_filter:
            filtered = [q for q in self.quotes if q.get("status") == status_filter]
        self._display_data(filtered)
        self._update_stats()

    def _display_data(self, quotes: list):
        self.table.setRowCount(len(quotes))
        visible_cols = self.table.get_visible_columns()

        for row, quote in enumerate(quotes):
            self._populate_row(row, quote, visible_cols)

    def _populate_row(self, row: int, quote: dict, visible_cols: list):
        quote_id = quote.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "quote_no":
                item = QTableWidgetItem(quote.get("quote_no", ""))
                item.setData(Qt.ItemDataRole.UserRole, quote_id)
                self.table.setItem(row, col_idx, item)

            elif col_key == "date":
                dt = self._format_date(quote.get("quote_date"))
                self.table.setItem(row, col_idx, QTableWidgetItem(dt))

            elif col_key == "customer":
                name = quote.get("customer_name", "") or "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(name))

            elif col_key == "total":
                total = quote.get("total_amount", 0) or 0
                self.table.setItem(row, col_idx, QTableWidgetItem(f"{total:,.2f}"))

            elif col_key == "items":
                item_count = str(quote.get("total_items", 0))
                self.table.setItem(row, col_idx, QTableWidgetItem(item_count))

            elif col_key == "valid_until":
                dt = self._format_date(quote.get("valid_until"))
                self.table.setItem(row, col_idx, QTableWidgetItem(dt))

            elif col_key == "status":
                status = quote.get("status", "draft")
                label, _ = self.STATUS_LABELS.get(status, ("Taslak", "#64748b"))
                self.table.setItem(row, col_idx, QTableWidgetItem(label))

            elif col_key == "currency":
                curr = quote.get("currency_code", "TRY")
                self.table.setItem(row, col_idx, QTableWidgetItem(curr))

            elif col_key == "actions":
                self._add_action_buttons(row, col_idx, quote)

    def _format_date(self, dt) -> str:
        if dt:
            if isinstance(dt, date):
                return dt.strftime("%d.%m.%Y")
            return str(dt)
        return "-"

    def _add_action_buttons(self, row: int, col: int, quote: dict):
        qid = quote.get("id")
        status = quote.get("status", "draft")

        actions = ["view"]
        callbacks = {"view": lambda quote_id=qid: self.view_clicked.emit(quote_id)}

        if status == "draft":
            actions.append("edit")
            callbacks["edit"] = lambda quote_id=qid: self.edit_clicked.emit(quote_id)

        widget = self.table.create_action_widget(qid, actions, callbacks)
        layout = widget.layout()

        from ui.components.action_buttons import create_custom_button

        if status == "draft":
            send_btn = create_custom_button(
                widget, ICONS.EXPORT, "Müşteriye Gönder", "primary"
            )
            send_btn.clicked.connect(lambda: self.send_clicked.emit(qid))
            layout.insertWidget(layout.count() - 1, send_btn)

        if status == "sent":
            accept_btn = create_custom_button(
                widget, ICONS.CHECK, "Kabul Et", "success"
            )
            accept_btn.clicked.connect(lambda: self.accept_clicked.emit(qid))
            layout.insertWidget(layout.count() - 1, accept_btn)

            reject_btn = create_custom_button(widget, ICONS.CLOSE, "Reddet", "error")
            reject_btn.clicked.connect(lambda: self.reject_clicked.emit(qid))
            layout.insertWidget(layout.count() - 1, reject_btn)

        if status == "accepted":
            order_btn = create_custom_button(
                widget, ICONS.INVENTORY, "Siparişe Dönüştür", "primary"
            )
            order_btn.clicked.connect(lambda: self.convert_to_order_clicked.emit(qid))
            layout.insertWidget(layout.count() - 1, order_btn)

        if status == "draft":
            del_btn = create_custom_button(widget, ICONS.DELETE, "Sil", "error")
            del_btn.clicked.connect(lambda: self._confirm_delete(qid))
            layout.insertWidget(layout.count() - 1, del_btn)

        self.table.setCellWidget(row, col, widget)

    def _update_stats(self):
        total = len(self.quotes)
        draft = sum(1 for q in self.quotes if q.get("status") == "draft")
        sent = sum(1 for q in self.quotes if q.get("status") == "sent")
        accepted = sum(1 for q in self.quotes if q.get("status") == "accepted")
        rejected = sum(1 for q in self.quotes if q.get("status") == "rejected")

        self.stat_cards["total"].update_value(str(total))
        self.stat_cards["draft"].update_value(str(draft))
        self.stat_cards["sent"].update_value(str(sent))
        self.stat_cards["accepted"].update_value(str(accepted))
        self.stat_cards["rejected"].update_value(str(rejected))

    def _on_search(self, text: str):
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
        self._apply_filter()

    def _confirm_delete(self, quote_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu teklifi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(quote_id)
