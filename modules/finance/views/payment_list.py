"""
Akıllı İş - Ödeme Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from PyQt6.QtWidgets import (
    QTableWidgetItem,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import qtawesome as qta
from decimal import Decimal

from ui.components import (
    BaseListPage,
    ColumnConfig,
)
from config.icons import ICONS


class PaymentListPage(BaseListPage):
    """Ödeme listesi sayfası."""

    # Sinyaller (Ek sinyaller)
    # add, edit, delete, view, refresh zaten BaseListPage'de var

    STATUS_MAP = {
        "pending": ("Beklemede", "#f59e0b", ICONS.TIME),
        "completed": ("Tamamlandı", "#10b981", ICONS.SUCCESS),
        "cancelled": ("İptal", "#ef4444", ICONS.CANCEL),
    }

    METHOD_MAP = {
        "cash": ("Nakit", ICONS.MONEY),
        "bank_transfer": ("Havale/EFT", ICONS.BANK),
        "check": ("Çek", ICONS.INVOICE),
        "credit_card": ("Kredi Kartı", ICONS.PAYMENT),
        "promissory_note": ("Senet", ICONS.WORK_ORDER),
    }

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("payment_no", "Ödeme No", width=120),
            ColumnConfig("payment_date", "Tarih", width=100, filter_type="date"),
            ColumnConfig("supplier_name", "Tedarikçi", stretch=True),
            ColumnConfig("amount", "Tutar", width=120, filter_type="number"),
            ColumnConfig(
                "payment_method", "Ödeme Yöntemi", width=130, filter_type="enum"
            ),
            ColumnConfig("status", "Durum", width=110, filter_type="enum"),
            ColumnConfig("description", "Açıklama", width=150),
            ColumnConfig("actions", "İşlemler", width=120, filterable=False),
        ]

        super().__init__(
            title="Ödemeler",
            icon=ICONS.PAYMENT,
            table_id="payment_list",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_add=True,
            add_text="Yeni Ödeme",
            search_placeholder="No, tedarikçi ara...",
            parent=parent,
        )

        self.payments = []
        self._setup_stat_cards()

    def _setup_stat_cards(self):
        self.add_stat_card("total", "Toplam", "0", "info", ICONS.INVENTORY)
        self.add_stat_card("completed", "Tamamlanan", "0", "success", ICONS.SUCCESS)
        self.add_stat_card("amount", "Toplam Tutar", "₺0", "danger", ICONS.MONEY)

    def _connect_signals(self):
        super()._connect_signals()

        # Alt bilgi

    def load_data(self, payments: list):
        self.payments = payments
        self._display_data(payments)
        self._update_stats()

    def _display_data(self, payments: list):
        self.table.setRowCount(len(payments))
        visible_cols = self.table.get_visible_columns()

        for row, pmt in enumerate(payments):
            self._populate_row(row, pmt, visible_cols)

    def _update_stats(self):
        completed = 0
        total_amount = Decimal(0)

        for pmt in self.payments:
            if pmt.get("status") == "completed":
                completed += 1
                total_amount += Decimal(str(pmt.get("amount", 0) or 0))

        # Kartları güncelle
        self.update_stat_card("total", str(len(self.payments)))
        self.update_stat_card("completed", str(completed))
        self.update_stat_card("amount", f"₺{total_amount:,.2f}")

        # Assuming _total_count and visible_count are managed by the BaseListPage or derived from table state
        # For this specific change, we'll assume these variables are available or will be handled elsewhere.
        # If not, this part would cause a NameError.
        self.update_count(len(self.payments), "ödeme")

    def _populate_row(self, row: int, pmt: dict, visible_cols: list):
        pmt_id = pmt.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "payment_no":
                item = QTableWidgetItem(pmt.get("payment_no", ""))
                item.setData(Qt.ItemDataRole.UserRole, pmt_id)
                item.setForeground(QColor("#818cf8"))
                self.table.setItem(row, col_idx, item)

            elif col_key == "payment_date":
                date_val = pmt.get("payment_date")
                if hasattr(date_val, "strftime"):
                    date_str = date_val.strftime("%d.%m.%Y")
                else:
                    date_str = str(date_val) if date_val else ""
                self.table.setItem(row, col_idx, QTableWidgetItem(date_str))

            elif col_key == "supplier_name":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(pmt.get("supplier_name", ""))
                )

            elif col_key == "amount":
                amount = pmt.get("amount") or 0
                item = QTableWidgetItem(f"₺{float(amount):,.2f}")
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, item)

            elif col_key == "payment_method":
                method = pmt.get("payment_method", "")
                text, icon = self.METHOD_MAP.get(method, (method, ICONS.TYPE_OTHER))
                item = QTableWidgetItem(text)
                if icon:
                    item.setIcon(qta.icon(icon, color="#475569"))
                self.table.setItem(row, col_idx, item)

            elif col_key == "status":
                status = pmt.get("status", "")
                status_info = self.STATUS_MAP.get(status, (status, "#ffffff", ""))
                text, color, icon = status_info
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color))
                if icon:
                    item.setIcon(qta.icon(icon, color=color))
                self.table.setItem(row, col_idx, item)

            elif col_key == "description":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(pmt.get("description", "") or "")
                )

            elif col_key == "actions":
                actions = ["view"]
                if pmt.get("status") != "cancelled":
                    actions.append("cancel")

                callbacks = {
                    "view": lambda sid=pmt_id: self.view_clicked.emit(sid),
                    "cancel": lambda sid=pmt_id: self._confirm_cancel(sid),
                }

                widget = self.table.create_action_widget(pmt_id, actions, callbacks)
                self.table.setCellWidget(row, col_idx, widget)

    def _on_search(self, text: str):
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = any(
                self.table.item(row, col)
                and text in self.table.item(row, col).text().lower()
                for col in range(self.table.columnCount())
            )
            self.table.setRowHidden(row, not match)

    def _confirm_cancel(self, payment_id: int):
        reply = QMessageBox.question(
            self,
            "İptal Onayı",
            "Bu ödemeyi iptal etmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(payment_id)
