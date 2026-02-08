"""
Akıllı İş - Satış İadeleri Liste Sayfası
"""

from datetime import date
from PyQt6.QtWidgets import (
    QTableWidgetItem,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from config.icons import ICONS
from ui.components import (
    BaseListPage,
    ColumnConfig,
)
from database.models.returns import ReturnStatus, ReturnType


class SalesReturnListPage(BaseListPage):
    """
    Satış iadeleri listesi sayfası.
    """

    # Sinyaller
    approve_clicked = pyqtSignal(int)
    cancel_clicked = pyqtSignal(int)

    # Durum etiketleri
    STATUS_LABELS = {
        ReturnStatus.DRAFT: ("Taslak", "#64748b"),
        ReturnStatus.PENDING_APPROVAL: ("Onay Bekliyor", "#f59e0b"),
        ReturnStatus.APPROVED: ("Onaylandı", "#10b981"),
        ReturnStatus.REJECTED: ("Reddedildi", "#ef4444"),
        ReturnStatus.CANCELLED: ("İptal", "#475569"),
        ReturnStatus.COMPLETED: ("Tamamlandı", "#3b82f6"),
    }

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("code", "İade No", width=120),
            ColumnConfig("date", "Tarih", width=100, filter_type="date"),
            ColumnConfig("customer", "Müşteri", width=200, stretch=True),
            ColumnConfig("amount", "Toplam Tutar", width=120, filter_type="number"),
            ColumnConfig("items", "Kalem", width=60, filter_type="number"),
            ColumnConfig("status", "Durum", width=130, filter_type="enum"),
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
            title="Satış İadeleri",
            icon=ICONS.RETURN,  # Assuming ICONS.RETURN exists, otherwise use something similar
            table_id="sales_returns",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_add=True,
            add_text="Yeni İade",
            search_placeholder="Ara... (iade no, müşteri)",
            parent=parent,
        )

        self.returns = []
        self._setup_stat_cards()

    def _format_date(self, dt) -> str:
        """Tarih formatla (GG.AA.YYYY)"""
        if dt:
            if isinstance(dt, date):
                return dt.strftime("%d.%m.%Y")
            return str(dt)
        return "-"

    def _setup_stat_cards(self):
        """İstatistik kartlarını oluştur"""
        self.add_stat_card("total", "Toplam", "0", "info", ICONS.RETURN)
        self.add_stat_card("draft", "Taslak", "0", "secondary", ICONS.EDIT)
        self.add_stat_card("pending", "Onay Bekleyen", "0", "warning", ICONS.TIME)
        self.add_stat_card("approved", "Onaylanan", "0", "success", ICONS.CHECK)

    def load_data(self, returns: list):
        """İade verilerini yükle"""
        self.returns = returns
        self._display_data(returns)
        self._update_stats()

    def _display_data(self, returns: list):
        self.table.setRowCount(len(returns))
        visible_cols = self.table.get_visible_columns()

        for row, ret in enumerate(returns):
            self._populate_row(row, ret, visible_cols)

    def _populate_row(self, row: int, ret: dict, visible_cols: list):
        return_id = ret.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "code":
                item = QTableWidgetItem(ret.get("code", ""))
                item.setData(Qt.ItemDataRole.UserRole, return_id)
                self.table.setItem(row, col_idx, item)

            elif col_key == "date":
                dt = self._format_date(ret.get("return_date"))
                self.table.setItem(row, col_idx, QTableWidgetItem(dt))

            elif col_key == "customer":
                cust = ret.get("customer_name", "") or "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(cust))

            elif col_key == "amount":
                # Assuming total_amount is calculated elsewhere or 0 for now
                total = ret.get("total_amount", 0) or 0
                self.table.setItem(row, col_idx, QTableWidgetItem(f"{total:,.2f}"))

            elif col_key == "items":
                item_count = str(ret.get("item_count", 0))
                self.table.setItem(row, col_idx, QTableWidgetItem(item_count))

            elif col_key == "status":
                status = ret.get("status", ReturnStatus.DRAFT)
                label, color = self.STATUS_LABELS.get(status, ("Taslak", "#64748b"))

                # Custom widget for badge style or just text
                self.table.setItem(row, col_idx, QTableWidgetItem(label))
                # Text color logic handled by delegate or simple logic here
                # item_widget = QLabel(label)
                # item_widget.setStyleSheet(f"color: {color}; font-weight: bold;")
                # self.table.setCellWidget(row, col_idx, item_widget)

            elif col_key == "actions":
                self._add_action_buttons(row, col_idx, ret)

    def _add_action_buttons(self, row: int, col: int, ret: dict):
        return_id = ret.get("id")
        status = ret.get("status", ReturnStatus.DRAFT)

        actions = ["view"]
        callbacks = {"view": lambda rid=return_id: self.view_clicked.emit(rid)}

        if status == ReturnStatus.DRAFT:
            actions.extend(["edit", "approve", "delete"])
            callbacks.update(
                {
                    "edit": lambda rid=return_id: self.edit_clicked.emit(rid),
                    "approve": lambda rid=return_id: self.approve_clicked.emit(rid),
                    "delete": lambda rid=return_id: self._confirm_delete(rid),
                }
            )
        elif status == ReturnStatus.PENDING_APPROVAL:
            actions.extend(["approve", "cancel"])  # Approve = Finalize?
            callbacks.update(
                {
                    "approve": lambda rid=return_id: self.approve_clicked.emit(rid),
                    "cancel": lambda rid=return_id: self.cancel_clicked.emit(rid),
                }
            )

        # create_action_widget kullan
        widget = self.table.create_action_widget(return_id, actions, callbacks)
        self.table.setCellWidget(row, col, widget)

    def _update_stats(self):
        total = len(self.returns)
        draft = sum(1 for r in self.returns if r.get("status") == ReturnStatus.DRAFT)
        pending = sum(
            1 for r in self.returns if r.get("status") == ReturnStatus.PENDING_APPROVAL
        )
        approved = sum(
            1 for r in self.returns if r.get("status") == ReturnStatus.APPROVED
        )

        self.update_stat_card("total", str(total))
        self.update_stat_card("draft", str(draft))
        self.update_stat_card("pending", str(pending))
        self.update_stat_card("approved", str(approved))

    def _on_search(self, text: str):
        """Tabloda arama yap"""
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = any(
                self.table.item(row, col)
                and text in self.table.item(row, col).text().lower()
                for col in range(self.table.columnCount() - 1)
            )
            self.table.setRowHidden(row, not match)

    def _confirm_delete(self, return_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu iade kaydını silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(return_id)
