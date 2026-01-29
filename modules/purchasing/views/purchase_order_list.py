"""
Akıllı İş - Satın Alma Siparişleri Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from datetime import date
import qtawesome as qta
from PyQt6.QtWidgets import (
    QTableWidgetItem,
    QComboBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from config.icons import ICONS
from ui.components import (
    BaseListPage,
    ColumnConfig,
)


class PurchaseOrderListPage(BaseListPage):
    """Satın alma siparişleri listesi."""

    # Sinyaller (Ek sinyaller)
    send_clicked = pyqtSignal(int)
    receive_clicked = pyqtSignal(int)
    create_receipt_clicked = pyqtSignal(int)

    STATUS_LABELS = {
        "draft": ("Taslak", "#64748b"),
        "sent": ("Gönderildi", "#3b82f6"),
        "confirmed": ("Onaylandı", "#10b981"),
        "partial": ("Kısmi", "#f59e0b"),
        "received": ("Teslim", "#10b981"),
        "closed": ("Kapalı", "#475569"),
        "cancelled": ("İptal", "#ef4444"),
    }

    def __init__(self, parent=None):
        # Tablo
        columns = [
            ColumnConfig("order_no", "Sipariş No", width=120),
            ColumnConfig("date", "Tarih", width=90),
            ColumnConfig("supplier", "Tedarikçi", width=200, stretch=True),
            ColumnConfig("delivery_date", "Teslim Tarihi", width=90),
            ColumnConfig("items", "Kalem", width=50),
            ColumnConfig("total", "Tutar", width=110),
            ColumnConfig("status", "Durum", width=110),
            ColumnConfig("received_rate", "Teslim %", width=70),
            ColumnConfig(
                "actions",
                "İşlemler",
                width=180,
                resizable=False,
                movable=False,
                hideable=False,
            ),
        ]

        super().__init__(
            title="Satın Alma Siparişleri",
            icon=ICONS.INVENTORY,
            table_id="purchase_orders",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Sipariş",
            search_placeholder="Ara... (sipariş no, tedarikçi)",
            parent=parent,
        )

        self.orders = []
        self._setup_filters()
        self._setup_stat_cards()

    def _format_date(self, dt) -> str:
        """Tarih formatla (GG.AA.YYYY)"""
        if dt:
            if isinstance(dt, date):
                return dt.strftime("%d.%m.%Y")
            return str(dt)
        return "-"

    def _setup_filters(self):
        # Filtre ekle
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("Taslak", "draft")
        self.status_filter.addItem("Gönderildi", "sent")
        self.status_filter.addItem("Onaylandı", "confirmed")
        self.status_filter.addItem("Kısmi Teslim", "partial")
        self.status_filter.addItem("Teslim Alındı", "received")
        self.status_filter.addItem("Kapatıldı", "closed")
        self.status_filter.addItem("İptal", "cancelled")
        self.status_filter.setMinimumWidth(160)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)

        if self.header.search_input:
            h_layout = self.header.header_layout()
            idx = h_layout.indexOf(self.header.search_input)
            h_layout.insertWidget(idx, self.status_filter)

    def _setup_stat_cards(self):
        """İstatistik kartlarını oluştur"""
        self.add_stat_card("total", "Toplam", "0", "info", ICONS.INVENTORY)
        self.add_stat_card("draft", "Taslak", "0", "info", ICONS.TIME)
        self.add_stat_card("open", "Açık", "0", "warning", ICONS.EXPORT)
        self.add_stat_card("received", "Teslim", "0", "success", ICONS.CHECK)
        self.add_stat_card("amount", "Tutar", "₺0", "primary", ICONS.MONEY)

    def _connect_signals(self):
        super()._connect_signals()

    def load_data(self, orders: list):
        self.orders = orders
        self._apply_filter()

    def _apply_filter(self):
        status_filter = self.status_filter.currentData()
        filtered = self.orders
        if status_filter:
            filtered = [o for o in self.orders if o.get("status") == status_filter]
        self._display_data(filtered)
        self._update_stats()

    def _display_data(self, orders: list):
        self.table.setRowCount(len(orders))
        visible_cols = self.table.get_visible_columns()

        for row, order in enumerate(orders):
            self._populate_row(row, order, visible_cols)

    def _populate_row(self, row: int, order: dict, visible_cols: list):
        order_id = order.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "order_no":
                item = QTableWidgetItem(order.get("order_no", ""))
                item.setData(Qt.ItemDataRole.UserRole, order_id)
                self.table.setItem(row, col_idx, item)

            elif col_key == "date":
                dt = self._format_date(order.get("order_date"))
                self.table.setItem(row, col_idx, QTableWidgetItem(dt))

            elif col_key == "supplier":
                sup = order.get("supplier_name", "") or "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(sup))

            elif col_key == "delivery_date":
                dt = self._format_date(order.get("delivery_date"))
                self.table.setItem(row, col_idx, QTableWidgetItem(dt))

            elif col_key == "items":
                cnt = str(order.get("total_items", 0))
                self.table.setItem(row, col_idx, QTableWidgetItem(cnt))

            elif col_key == "total":
                total = order.get("total", 0) or 0
                currency = order.get("currency", "TRY")
                symbol = {"TRY": "₺", "USD": "$", "EUR": "€"}.get(currency, "₺")
                val = f"{symbol}{float(total):,.2f}"
                self.table.setItem(row, col_idx, QTableWidgetItem(val))

            elif col_key == "status":
                status = order.get("status", "draft")
                label, _ = self.STATUS_LABELS.get(status, ("Taslak", "#64748b"))
                self.table.setItem(row, col_idx, QTableWidgetItem(label))

            elif col_key == "received_rate":
                rate = order.get("received_rate", 0) or 0
                self.table.setItem(row, col_idx, QTableWidgetItem(f"%{int(rate)}"))

            elif col_key == "actions":
                self._add_action_buttons(row, col_idx, order)

    def _add_action_buttons(self, row: int, col: int, order: dict):
        order_id = order.get("id")
        status = order.get("status", "draft")

        actions = ["view"]
        callbacks = {"view": lambda _, sid=order_id: self.view_clicked.emit(sid)}

        if status == "draft":
            actions.extend(["edit", "delete"])
            callbacks.update(
                {
                    "edit": lambda _, sid=order_id: self.edit_clicked.emit(sid),
                    "delete": lambda _, sid=order_id: self._confirm_delete(sid),
                }
            )

        # create_action_widget kullan
        widget = self.table.create_action_widget(order_id, actions, callbacks)
        layout = widget.layout()

        # Özel butonlar (Gönder, Mal Kabul)
        from ui.components.action_buttons import create_custom_button
        from config.icons import ICONS

        if status == "draft":
            send_btn = create_custom_button(
                widget, ICONS.TRUCK, "Tedarikçiye Gönder", "info"
            )
            send_btn.clicked.connect(
                lambda _, sid=order_id: self.send_clicked.emit(sid)
            )
            layout.insertWidget(layout.count() - 1, send_btn)

        elif status in ["sent", "confirmed", "partial"]:
            receive_btn = create_custom_button(
                widget, ICONS.INVENTORY, "Mal Kabul Oluştur", "success"
            )
            receive_btn.clicked.connect(
                lambda _, sid=order_id: self.create_receipt_clicked.emit(sid)
            )
            layout.insertWidget(layout.count() - 1, receive_btn)

        self.table.setCellWidget(row, col, widget)

    def _update_stats(self):
        total = len(self.orders)
        draft = sum(1 for o in self.orders if o.get("status") == "draft")
        open_orders = sum(
            1
            for o in self.orders
            if o.get("status") in ["sent", "confirmed", "partial"]
        )
        received = sum(
            1 for o in self.orders if o.get("status") in ["received", "closed"]
        )
        total_amount = sum(float(o.get("total", 0) or 0) for o in self.orders)

        self.update_stat_card("total", str(total))
        self.update_stat_card("draft", str(draft))
        self.update_stat_card("open", str(open_orders))
        self.update_stat_card("received", str(received))
        self.update_stat_card("amount", f"₺{total_amount:,.0f}")

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

    def _confirm_delete(self, order_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu siparişi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(order_id)
