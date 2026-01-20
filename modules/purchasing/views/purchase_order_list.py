"""
Akıllı İş - Satın Alma Siparişleri Liste Sayfası
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


class PurchaseOrderListPage(QWidget):
    """Satın alma siparişleri listesi."""

    # Sinyaller
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    send_clicked = pyqtSignal(int)
    receive_clicked = pyqtSignal(int)
    create_receipt_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    STATUS_LABELS = {
        "draft": ("🔵 Taslak", "#64748b"),
        "sent": ("📤 Gönderildi", "#3b82f6"),
        "confirmed": ("✅ Onaylandı", "#10b981"),
        "partial": ("🟡 Kısmi", "#f59e0b"),
        "received": ("🟢 Teslim", "#10b981"),
        "closed": ("⚫ Kapalı", "#475569"),
        "cancelled": ("🔴 İptal", "#ef4444"),
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
            title="Satın Alma Siparişleri",
            icon="📦",
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Sipariş",
            search_placeholder="Ara... (sipariş no, tedarikçi)",
            parent=self,
        )

        # Filtre ekle
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("🔵 Taslak", "draft")
        self.status_filter.addItem("📤 Gönderildi", "sent")
        self.status_filter.addItem("✅ Onaylandı", "confirmed")
        self.status_filter.addItem("🟡 Kısmi Teslim", "partial")
        self.status_filter.addItem("🟢 Teslim Alındı", "received")
        self.status_filter.addItem("⚫ Kapatıldı", "closed")
        self.status_filter.addItem("🔴 İptal", "cancelled")
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
        self.stat_cards["open"] = MiniStatCard("📤 Açık", "0", "#f59e0b")
        self.stat_cards["received"] = MiniStatCard("🟢 Teslim", "0", "#10b981")
        self.stat_cards["amount"] = MiniStatCard("💰 Tutar", "₺0", "#8b5cf6")

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

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

        self.table = EnhancedTableWidget(
            table_id="purchase_orders",
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

            elif col_key == "supplier":
                self.table.setItem(
                    row,
                    col_idx,
                    QTableWidgetItem(order.get("supplier_name", "") or "-"),
                )

            elif col_key == "delivery_date":
                self.table.setItem(
                    row,
                    col_idx,
                    QTableWidgetItem(self._format_date(order.get("delivery_date"))),
                )

            elif col_key == "items":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(str(order.get("total_items", 0)))
                )

            elif col_key == "total":
                total = order.get("total", 0) or 0
                currency = order.get("currency", "TRY")
                symbol = {"TRY": "₺", "USD": "$", "EUR": "€"}.get(currency, "₺")
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(f"{symbol}{float(total):,.2f}")
                )

            elif col_key == "status":
                status = order.get("status", "draft")
                label, _ = self.STATUS_LABELS.get(status, ("Taslak", "#64748b"))
                self.table.setItem(row, col_idx, QTableWidgetItem(label))

            elif col_key == "received_rate":
                rate = order.get("received_rate", 0) or 0
                self.table.setItem(row, col_idx, QTableWidgetItem(f"%{int(rate)}"))

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
        view_btn.clicked.connect(
            lambda checked, oid=order_id: self.view_clicked.emit(oid)
        )
        btn_layout.addWidget(view_btn)

        if status == "draft":
            edit_btn = QPushButton("✏")
            edit_btn.setFixedSize(28, 26)
            edit_btn.clicked.connect(
                lambda checked, oid=order_id: self.edit_clicked.emit(oid)
            )
            btn_layout.addWidget(edit_btn)

            send_btn = QPushButton("📤")
            send_btn.setFixedSize(28, 26)
            send_btn.setToolTip("Tedarikçiye Gönder")
            send_btn.clicked.connect(
                lambda checked, oid=order_id: self.send_clicked.emit(oid)
            )
            btn_layout.addWidget(send_btn)

            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(28, 26)
            del_btn.clicked.connect(
                lambda checked, oid=order_id: self._confirm_delete(oid)
            )
            btn_layout.addWidget(del_btn)

        elif status in ["sent", "confirmed", "partial"]:
            receive_btn = QPushButton("📥")
            receive_btn.setFixedSize(28, 26)
            receive_btn.setToolTip("Mal Kabul Oluştur")
            receive_btn.clicked.connect(
                lambda checked, oid=order_id: self.create_receipt_clicked.emit(oid)
            )
            btn_layout.addWidget(receive_btn)

        self.table.setCellWidget(row, col, btn_widget)

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

        self.stat_cards["total"].update_value(str(total))
        self.stat_cards["draft"].update_value(str(draft))
        self.stat_cards["open"].update_value(str(open_orders))
        self.stat_cards["received"].update_value(str(received))
        self.stat_cards["amount"].update_value(f"₺{total_amount:,.0f}")

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
