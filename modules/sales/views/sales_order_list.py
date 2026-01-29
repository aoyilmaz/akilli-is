"""
Akıllı İş - Satış Siparişleri Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from datetime import date
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


class SalesOrderListPage(BaseListPage):
    """
    Satış siparişleri listesi sayfası.
    """

    # Sinyaller (Ek sinyaller)
    confirm_clicked = pyqtSignal(int)
    cancel_clicked = pyqtSignal(int)
    create_delivery_clicked = pyqtSignal(int)

    # Durum etiketleri
    STATUS_LABELS = {
        "draft": ("Taslak", "#64748b"),
        "confirmed": ("Onaylandı", "#10b981"),
        "partial_delivered": ("Kısmi Teslim", "#f59e0b"),
        "delivered": ("Teslim Edildi", "#8b5cf6"),
        "closed": ("Kapatıldı", "#475569"),
        "cancelled": ("İptal", "#475569"),
    }

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("order_no", "Sipariş No", width=120),
            ColumnConfig("date", "Tarih", width=100),
            ColumnConfig("customer", "Müşteri", width=200, stretch=True),
            ColumnConfig("total", "Toplam Tutar", width=120),
            ColumnConfig("items", "Kalem", width=60),
            ColumnConfig("delivery_date", "Teslim Tarihi", width=100),
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

        super().__init__(
            title="Satış Siparişleri",
            icon="ph.shopping-cart",
            table_id="sales_orders",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Sipariş",
            search_placeholder="Ara... (sipariş no, müşteri)",
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
        self.status_filter.addItem("Onaylandı", "confirmed")
        self.status_filter.addItem("Kısmi Teslim", "partial_delivered")
        self.status_filter.addItem("Teslim Edildi", "delivered")
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
        self.add_stat_card("total", "Toplam", "0", "info", ICONS.INVOICE)
        self.add_stat_card("draft", "Taslak", "0", "info", ICONS.TIME)
        self.add_stat_card("confirmed", "Onaylandı", "0", "success", ICONS.CHECK)
        self.add_stat_card("partial", "Kısmi Teslim", "0", "warning", ICONS.TIME)
        self.add_stat_card("delivered", "Teslim", "0", "primary", ICONS.CHECK)

    def _connect_signals(self):
        # BaseListPage sinyalleri
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

            elif col_key == "customer":
                cust = order.get("customer_name", "") or "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(cust))

            elif col_key == "total":
                total = order.get("total_amount", 0) or 0
                self.table.setItem(row, col_idx, QTableWidgetItem(f"{total:,.2f}"))

            elif col_key == "items":
                item_count = str(order.get("total_items", 0))
                self.table.setItem(row, col_idx, QTableWidgetItem(item_count))

            elif col_key == "delivery_date":
                dt = self._format_date(order.get("delivery_date"))
                self.table.setItem(row, col_idx, QTableWidgetItem(dt))

            elif col_key == "status":
                status = order.get("status", "draft")
                label, _ = self.STATUS_LABELS.get(status, ("Taslak", "#64748b"))
                self.table.setItem(row, col_idx, QTableWidgetItem(label))

            elif col_key == "currency":
                curr = order.get("currency_code", "TRY")
                self.table.setItem(row, col_idx, QTableWidgetItem(curr))

            elif col_key == "actions":
                self._add_action_buttons(row, col_idx, order)

    def _add_action_buttons(self, row: int, col: int, order: dict):
        order_id = order.get("id")
        status = order.get("status", "draft")

        actions = ["view"]
        callbacks = {"view": lambda sid=order_id: self.view_clicked.emit(sid)}

        if status == "draft":
            actions.extend(["edit", "approve", "delete"])
            callbacks.update(
                {
                    "edit": lambda sid=order_id: self.edit_clicked.emit(sid),
                    "approve": lambda sid=order_id: self.confirm_clicked.emit(sid),
                    "delete": lambda sid=order_id: self._confirm_delete(sid),
                }
            )

        if status in ["confirmed", "partial_delivered"]:
            # Özel butonlar için create_custom_button kullanılabilir veya actions listesi genişletilebilir
            # Mevcut create_action_widget 'view', 'edit', 'delete', 'approve', 'cancel' destekliyor
            pass

        if status in ["draft", "confirmed"]:
            actions.append("cancel")
            callbacks["cancel"] = lambda sid=order_id: self.cancel_clicked.emit(sid)

        # create_action_widget kullan
        widget = self.table.create_action_widget(order_id, actions, callbacks)

        # 'İrsaliye Oluştur' gibi özel butonları manuel ekleyelim (Şimdilik)
        if status in ["confirmed", "partial_delivered"]:
            from ui.components.action_buttons import create_custom_button
            from config.icons import ICONS

            delivery_btn = create_custom_button(
                widget, ICONS.INVENTORY, "İrsaliye Oluştur", "info"
            )
            delivery_btn.clicked.connect(
                lambda sid=order_id: self.create_delivery_clicked.emit(sid)
            )
            # Layout'a stretch'ten önce ekleyelim
            layout = widget.layout()
            layout.insertWidget(layout.count() - 1, delivery_btn)

        self.table.setCellWidget(row, col, widget)

    def _update_stats(self):
        total = len(self.orders)
        draft = sum(1 for o in self.orders if o.get("status") == "draft")
        confirmed = sum(1 for o in self.orders if o.get("status") == "confirmed")
        partial = sum(1 for o in self.orders if o.get("status") == "partial_delivered")
        delivered = sum(1 for o in self.orders if o.get("status") == "delivered")

        self.update_stat_card("total", str(total))
        self.update_stat_card("draft", str(draft))
        self.update_stat_card("confirmed", str(confirmed))
        self.update_stat_card("partial", str(partial))
        self.update_stat_card("delivered", str(delivered))

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
