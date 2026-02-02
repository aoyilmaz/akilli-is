"""
Akıllı İş - Satış Teklifleri Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from datetime import date
from PyQt6.QtWidgets import (
    QTableWidgetItem,
)
from PyQt6.QtCore import Qt, pyqtSignal

from config.icons import ICONS
from ui.components import (
    BaseListPage,
    ColumnConfig,
)


class SalesQuoteListPage(BaseListPage):
    """
    Satış teklifleri listesi sayfası.
    BaseListPage kullanarak Excel tipi sütun filtreleme destekler.
    """

    # Ek sinyaller
    send_clicked = pyqtSignal(int)
    accept_clicked = pyqtSignal(int)
    reject_clicked = pyqtSignal(int)
    convert_to_order_clicked = pyqtSignal(int)

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
        columns = [
            ColumnConfig("quote_no", "Teklif No", width=120),
            ColumnConfig("date", "Tarih", width=100, filter_type="date"),
            ColumnConfig("customer", "Müşteri", width=200, stretch=True),
            ColumnConfig("total", "Toplam Tutar", width=120, filter_type="number"),
            ColumnConfig("items", "Kalem", width=60, filter_type="number"),
            ColumnConfig("valid_until", "Geçerlilik", width=100, filter_type="date"),
            ColumnConfig("status", "Durum", width=130, filter_type="enum"),
            ColumnConfig("currency", "Para Birimi", width=80, filter_type="enum"),
            ColumnConfig(
                "actions",
                "İşlemler",
                width=200,
                resizable=False,
                movable=False,
                hideable=False,
                filterable=False,
            ),
        ]

        super().__init__(
            title="Satış Teklifleri",
            icon=ICONS.INVOICE,
            table_id="sales_quotes",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_add=True,
            add_text="Yeni Teklif",
            search_placeholder="Ara... (teklif no, müşteri)",
            parent=parent,
        )

        self.quotes = []
        self._setup_stat_cards()

    def _setup_stat_cards(self):
        """İstatistik kartlarını oluştur"""
        self.add_stat_card("total", "Toplam", "0", "info", ICONS.INVOICE)
        self.add_stat_card("draft", "Taslak", "0", "info", ICONS.TIME)
        self.add_stat_card("sent", "Gönderildi", "0", "primary", ICONS.EXPORT)
        self.add_stat_card("accepted", "Kabul", "0", "success", ICONS.CHECK)
        self.add_stat_card("rejected", "Red", "0", "error", ICONS.CLOSE)

    def load_data(self, quotes: list):
        """Verileri yükle"""
        self.quotes = quotes
        self._display_data(quotes)
        self._update_stats()

    def _display_data(self, quotes: list):
        """Tabloya verileri yükle"""
        self.table.setRowCount(len(quotes))
        visible_cols = self.table.get_visible_columns()

        for row, quote in enumerate(quotes):
            self._populate_row(row, quote, visible_cols)

    def _populate_row(self, row: int, quote: dict, visible_cols: list):
        """Tek satırı doldur"""
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
        """Tarihi formatla"""
        if dt:
            if isinstance(dt, date):
                return dt.strftime("%d.%m.%Y")
            return str(dt)
        return "-"

    def _add_action_buttons(self, row: int, col: int, quote: dict):
        """İşlem butonlarını ekle"""
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
        """İstatistikleri güncelle"""
        total = len(self.quotes)
        draft = sum(1 for q in self.quotes if q.get("status") == "draft")
        sent = sum(1 for q in self.quotes if q.get("status") == "sent")
        accepted = sum(1 for q in self.quotes if q.get("status") == "accepted")
        rejected = sum(1 for q in self.quotes if q.get("status") == "rejected")

        self.update_stat_card("total", str(total))
        self.update_stat_card("draft", str(draft))
        self.update_stat_card("sent", str(sent))
        self.update_stat_card("accepted", str(accepted))
        self.update_stat_card("rejected", str(rejected))

    def _confirm_delete(self, quote_id: int):
        """Silme onayı"""
        if self.confirm_delete("teklif"):
            self.delete_clicked.emit(quote_id)
