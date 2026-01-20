"""
Akıllı İş - Satış Siparişleri Liste Sayfası
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
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
)


class SalesOrderListPage(QWidget):
    """
    Satış siparişleri listesi sayfası.
    PageHeader ve EnhancedTableWidget kullanır.
    """

    # Sinyaller
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    confirm_clicked = pyqtSignal(int)
    cancel_clicked = pyqtSignal(int)
    create_delivery_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    STATUS_LABELS = {
        "draft": ("🔵 Taslak", "#64748b"),
        "confirmed": ("🟢 Onaylandı", "#10b981"),
        "partial_delivered": ("🟡 Kısmi Teslim", "#f59e0b"),
        "delivered": ("✅ Teslim Edildi", "#8b5cf6"),
        "closed": ("🔒 Kapatıldı", "#475569"),
        "cancelled": ("⚫ İptal", "#475569"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.orders = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Satış Siparişleri",
            icon="🛒",
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Sipariş",
            search_placeholder="Ara... (sipariş no, müşteri)",
            parent=self,
        )

        # Filtre ekle
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("🔵 Taslak", "draft")
        self.status_filter.addItem("🟢 Onaylandı", "confirmed")
        self.status_filter.addItem("🟡 Kısmi Teslim", "partial_delivered")
        self.status_filter.addItem("✅ Teslim Edildi", "delivered")
        self.status_filter.addItem("🔒 Kapatıldı", "closed")
        self.status_filter.addItem("⚫ İptal", "cancelled")
        self.status_filter.setMinimumWidth(160)
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
        self.stat_cards["total"] = MiniStatCard("📊 Toplam", "0", "#6366f1")
        self.stat_cards["draft"] = MiniStatCard("🔵 Taslak", "0", "#64748b")
        self.stat_cards["confirmed"] = MiniStatCard("🟢 Onaylandı", "0", "#10b981")
        self.stat_cards["partial"] = MiniStatCard("🟡 Kısmi Teslim", "0", "#f59e0b")
        self.stat_cards["delivered"] = MiniStatCard("✅ Teslim", "0", "#8b5cf6")

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
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

        self.table = EnhancedTableWidget(
            table_id="sales_orders",
            columns=columns,
            parent=self,
        )
        layout.addWidget(self.table)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search)
        self.table.row_double_clicked.connect(self.view_clicked.emit)

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
                self.table.setItem(
                    row,
                    col_idx,
                    QTableWidgetItem(self._format_date(order.get("order_date"))),
                )

            elif col_key == "customer":
                self.table.setItem(
                    row,
                    col_idx,
                    QTableWidgetItem(order.get("customer_name", "") or "-"),
                )

            elif col_key == "total":
                total = order.get("total_amount", 0) or 0
                self.table.setItem(row, col_idx, QTableWidgetItem(f"{total:,.2f}"))

            elif col_key == "items":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(str(order.get("total_items", 0)))
                )

            elif col_key == "delivery_date":
                self.table.setItem(
                    row,
                    col_idx,
                    QTableWidgetItem(self._format_date(order.get("delivery_date"))),
                )

            elif col_key == "status":
                status = order.get("status", "draft")
                label, _ = self.STATUS_LABELS.get(status, ("Taslak", "#64748b"))
                self.table.setItem(row, col_idx, QTableWidgetItem(label))

            elif col_key == "currency":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(order.get("currency_code", "TRY"))
                )

            elif col_key == "actions":
                self._add_action_buttons(row, col_idx, order)

        self.table.setRowHeight(row, 52)

    def _format_date(self, dt) -> str:
        if dt:
            if isinstance(dt, date):
                return dt.strftime("%d.%m.%Y")
            return str(dt)
        return "-"

    def _add_action_buttons(self, row: int, col: int, order: dict):
        btn_widget = QWidget()
        btn_widget.setProperty("class", "action-button-group")
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(2, 2, 2, 2)
        btn_layout.setSpacing(2)

        order_id = order.get("id")
        status = order.get("status", "draft")

        # Görüntüle
        view_btn = QPushButton("👁")
        view_btn.setFixedSize(28, 26)
        view_btn.setToolTip("Görüntüle")
        view_btn.clicked.connect(
            lambda checked, oid=order_id: self.view_clicked.emit(oid)
        )
        btn_layout.addWidget(view_btn)

        if status == "draft":
            # Düzenle
            edit_btn = QPushButton("✏")
            edit_btn.setFixedSize(28, 26)
            edit_btn.clicked.connect(
                lambda checked, oid=order_id: self.edit_clicked.emit(oid)
            )
            btn_layout.addWidget(edit_btn)

            # Onayla
            confirm_btn = QPushButton("✓")
            confirm_btn.setFixedSize(28, 26)
            confirm_btn.setToolTip("Onayla")
            confirm_btn.clicked.connect(
                lambda checked, oid=order_id: self.confirm_clicked.emit(oid)
            )
            btn_layout.addWidget(confirm_btn)

        if status in ["confirmed", "partial_delivered"]:
            # İrsaliye Oluştur
            delivery_btn = QPushButton("📦")
            delivery_btn.setFixedSize(28, 26)
            delivery_btn.setToolTip("İrsaliye Oluştur")
            delivery_btn.clicked.connect(
                lambda checked, oid=order_id: self.create_delivery_clicked.emit(oid)
            )
            btn_layout.addWidget(delivery_btn)

        if status in ["draft", "confirmed"]:
            # İptal
            cancel_btn = QPushButton("❌")
            cancel_btn.setFixedSize(28, 26)
            cancel_btn.clicked.connect(
                lambda checked, oid=order_id: self.cancel_clicked.emit(oid)
            )
            btn_layout.addWidget(cancel_btn)

        if status == "draft":
            # Sil
            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(28, 26)
            del_btn.clicked.connect(
                lambda checked, oid=order_id: self._confirm_delete(oid)
            )
            btn_layout.addWidget(del_btn)

        self.table.setCellWidget(row, col, btn_widget)

    def _update_stats(self):
        total = len(self.orders)
        draft = sum(1 for o in self.orders if o.get("status") == "draft")
        confirmed = sum(1 for o in self.orders if o.get("status") == "confirmed")
        partial = sum(1 for o in self.orders if o.get("status") == "partial_delivered")
        delivered = sum(1 for o in self.orders if o.get("status") == "delivered")

        self.stat_cards["total"].update_value(str(total))
        self.stat_cards["draft"].update_value(str(draft))
        self.stat_cards["confirmed"].update_value(str(confirmed))
        self.stat_cards["partial"].update_value(str(partial))
        self.stat_cards["delivered"].update_value(str(delivered))

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
