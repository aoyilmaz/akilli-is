"""
Akıllı İş - Tahsilat Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from PyQt6.QtWidgets import (
    QTableWidgetItem,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from decimal import Decimal

from ui.components import (
    BaseListPage,
    ColumnConfig,
)
from config.icons import ICONS


class ReceiptListPage(BaseListPage):
    """Tahsilat listesi sayfası"""

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("receipt_no", "Tahsilat No", width=120),
            ColumnConfig("receipt_date", "Tarih", width=100, filter_type="date"),
            ColumnConfig("customer_name", "Müşteri", stretch=True),
            ColumnConfig("amount", "Tutar", width=120, filter_type="number"),
            ColumnConfig("payment_method", "Ödeme Yöntemi", width=130, filter_type="enum"),
            ColumnConfig("status", "Durum", width=100, filter_type="enum"),
            ColumnConfig("description", "Açıklama", stretch=True),
            ColumnConfig("actions", "İşlemler", width=120, filterable=False),
        ]

        super().__init__(
            title="Tahsilatlar",
            icon=ICONS.MONEY,
            table_id="receipt_list",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_add=True,
            add_text="Yeni Tahsilat",
            search_placeholder="No, müşteri ara...",
            parent=parent,
        )

        self.receipts = []
        self._setup_stat_cards()

    def _setup_stat_cards(self):
        self.add_stat_card("total", "Toplam", "0", "info", ICONS.INVENTORY)
        self.add_stat_card("completed", "Tamamlanan", "0", "success", ICONS.CHECK)
        self.add_stat_card("amount", "Toplam Tutar", "₺0", "primary", ICONS.MONEY)

    def _update_stats(self):
        total = len(self.receipts)
        completed = sum(1 for r in self.receipts if r.get("status") == "completed")
        total_amount = sum(
            Decimal(str(r.get("amount", 0) or 0))
            for r in self.receipts
            if r.get("status") == "completed"
        )

        self.update_stat_card("total", str(total))
        self.update_stat_card("completed", str(completed))
        self.update_stat_card("amount", f"₺{total_amount:,.2f}")

    def load_data(self, receipts: list):
        self.receipts = receipts
        self._display_data(receipts)
        self._update_stats()

    def _display_data(self, receipts: list):
        self.clear_table()
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

            elif col_key == "receipt_date":
                date_val = rec.get("receipt_date")
                if hasattr(date_val, "strftime"):
                    date_str = date_val.strftime("%d.%m.%Y")
                else:
                    date_str = str(date_val) if date_val else ""
                self.table.setItem(row, col_idx, QTableWidgetItem(date_str))

            elif col_key == "customer_name":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(rec.get("customer_name", ""))
                )

            elif col_key == "amount":
                amount = float(rec.get("amount") or 0)
                item = QTableWidgetItem(f"₺{amount:,.2f}")
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, item)

            elif col_key == "payment_method":
                method_map = {
                    "cash": "Nakit",
                    "bank_transfer": "Havale/EFT",
                    "check": "Çek",
                    "credit_card": "Kredi Kartı",
                    "promissory_note": "Senet",
                }
                method = rec.get("payment_method", "")
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(method_map.get(method, method))
                )

            elif col_key == "status":
                status_map = {
                    "pending": "Beklemede",
                    "completed": "Tamamlandı",
                    "cancelled": "İptal",
                }
                status = rec.get("status", "")
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(status_map.get(status, status))
                )

            elif col_key == "description":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(rec.get("description", "") or "")
                )

            elif col_key == "actions":
                actions = ["view"]
                if rec.get("status") != "cancelled":
                    actions.append("cancel")

                callbacks = {
                    "view": lambda rid=rec_id: self.view_clicked.emit(rid),
                    "cancel": lambda rid=rec_id: self._confirm_cancel(rid),
                }

                widget = self.table.create_action_widget(rec_id, actions, callbacks)
                self.table.setCellWidget(row, col_idx, widget)

    def _confirm_cancel(self, receipt_id: int):
        reply = QMessageBox.question(
            self,
            "İptal Onayı",
            "Bu tahsilatı iptal etmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(receipt_id)
