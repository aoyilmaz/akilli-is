"""
Akıllı İş - Satın Alma Talepleri Liste Sayfası
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


class PurchaseRequestListPage(QWidget):
    """Satın alma talepleri listesi."""

    # Sinyaller
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    approve_clicked = pyqtSignal(int)
    reject_clicked = pyqtSignal(int)
    create_order_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    STATUS_LABELS = {
        "draft": ("🔵 Taslak", "#64748b"),
        "pending": ("🟡 Onay Bekliyor", "#f59e0b"),
        "approved": ("🟢 Onaylandı", "#10b981"),
        "rejected": ("🔴 Reddedildi", "#ef4444"),
        "ordered": ("📦 Sipariş Verildi", "#8b5cf6"),
        "cancelled": ("⚫ İptal", "#475569"),
    }

    PRIORITY_LABELS = {
        1: ("⬇️ Düşük", "#64748b"),
        2: ("➡️ Normal", "#3b82f6"),
        3: ("⬆️ Yüksek", "#f59e0b"),
        4: ("🔥 Acil", "#ef4444"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.requests = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Satın Alma Talepleri",
            icon="📋",
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Talep",
            search_placeholder="Ara... (talep no, departman)",
            parent=self,
        )

        # Filtre ekle
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("🔵 Taslak", "draft")
        self.status_filter.addItem("🟡 Onay Bekliyor", "pending")
        self.status_filter.addItem("🟢 Onaylandı", "approved")
        self.status_filter.addItem("🔴 Reddedildi", "rejected")
        self.status_filter.addItem("📦 Sipariş Verildi", "ordered")
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
        self.stat_cards["pending"] = MiniStatCard("🟡 Bekleyen", "0", "#f59e0b")
        self.stat_cards["approved"] = MiniStatCard("🟢 Onaylı", "0", "#10b981")
        self.stat_cards["rejected"] = MiniStatCard("🔴 Ret", "0", "#ef4444")

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        columns = [
            ColumnConfig("request_no", "Talep No", width=120),
            ColumnConfig("date", "Tarih", width=100),
            ColumnConfig("requested_by", "Talep Eden", width=120),
            ColumnConfig("department", "Departman", width=150, stretch=True),
            ColumnConfig("items", "Kalem", width=60),
            ColumnConfig("priority", "Öncelik", width=80),
            ColumnConfig("status", "Durum", width=120),
            ColumnConfig("required_date", "Termin", width=100),
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
            table_id="purchase_requests",
            columns=columns,
            parent=self,
        )
        layout.addWidget(self.table)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search)
        self.table.row_double_clicked.connect(self.view_clicked.emit)

    def load_data(self, requests: list):
        self.requests = requests
        self._apply_filter()

    def _apply_filter(self):
        status_filter = self.status_filter.currentData()
        filtered = self.requests
        if status_filter:
            filtered = [r for r in self.requests if r.get("status") == status_filter]
        self._display_data(filtered)
        self._update_stats()

    def _display_data(self, requests: list):
        self.table.setRowCount(len(requests))
        visible_cols = self.table.get_visible_columns()

        for row, req in enumerate(requests):
            self._populate_row(row, req, visible_cols)

    def _populate_row(self, row: int, req: dict, visible_cols: list):
        req_id = req.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "request_no":
                item = QTableWidgetItem(req.get("request_no", ""))
                item.setData(Qt.ItemDataRole.UserRole, req_id)
                self.table.setItem(row, col_idx, item)

            elif col_key == "date":
                self.table.setItem(
                    row,
                    col_idx,
                    QTableWidgetItem(self._format_date(req.get("request_date"))),
                )

            elif col_key == "requested_by":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(req.get("requested_by", "") or "-")
                )

            elif col_key == "department":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(req.get("department", "") or "-")
                )

            elif col_key == "items":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(str(req.get("total_items", 0)))
                )

            elif col_key == "priority":
                priority = req.get("priority", 2)
                label, _ = self.PRIORITY_LABELS.get(priority, ("Normal", "#3b82f6"))
                self.table.setItem(row, col_idx, QTableWidgetItem(label))

            elif col_key == "status":
                status = req.get("status", "draft")
                label, _ = self.STATUS_LABELS.get(status, ("Taslak", "#64748b"))
                self.table.setItem(row, col_idx, QTableWidgetItem(label))

            elif col_key == "required_date":
                self.table.setItem(
                    row,
                    col_idx,
                    QTableWidgetItem(self._format_date(req.get("required_date"))),
                )

            elif col_key == "actions":
                self._add_action_buttons(row, col_idx, req)

        self.table.setRowHeight(row, 52)

    def _format_date(self, dt) -> str:
        if dt:
            if isinstance(dt, date):
                return dt.strftime("%d.%m.%Y")
            return str(dt)
        return "-"

    def _add_action_buttons(self, row: int, col: int, req: dict):
        btn_widget = QWidget()
        btn_widget.setProperty("class", "action-button-group")
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(2, 2, 2, 2)
        btn_layout.setSpacing(2)

        req_id = req.get("id")
        status = req.get("status", "draft")

        # Görüntüle
        view_btn = QPushButton("👁")
        view_btn.setFixedSize(28, 26)
        view_btn.clicked.connect(
            lambda checked, rid=req_id: self.view_clicked.emit(rid)
        )
        btn_layout.addWidget(view_btn)

        if status == "draft":
            edit_btn = QPushButton("✏")
            edit_btn.setFixedSize(28, 26)
            edit_btn.clicked.connect(
                lambda checked, rid=req_id: self.edit_clicked.emit(rid)
            )
            btn_layout.addWidget(edit_btn)

        if status == "pending":
            approve_btn = QPushButton("✓")
            approve_btn.setFixedSize(28, 26)
            approve_btn.setToolTip("Onayla")
            approve_btn.clicked.connect(
                lambda checked, rid=req_id: self.approve_clicked.emit(rid)
            )
            btn_layout.addWidget(approve_btn)

            reject_btn = QPushButton("✗")
            reject_btn.setFixedSize(28, 26)
            reject_btn.setToolTip("Reddet")
            reject_btn.clicked.connect(
                lambda checked, rid=req_id: self.reject_clicked.emit(rid)
            )
            btn_layout.addWidget(reject_btn)

        if status == "approved":
            order_btn = QPushButton("📦")
            order_btn.setFixedSize(28, 26)
            order_btn.setToolTip("Sipariş Oluştur")
            order_btn.clicked.connect(
                lambda checked, rid=req_id: self.create_order_clicked.emit(rid)
            )
            btn_layout.addWidget(order_btn)

        if status == "draft":
            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(28, 26)
            del_btn.clicked.connect(
                lambda checked, rid=req_id: self._confirm_delete(rid)
            )
            btn_layout.addWidget(del_btn)

        self.table.setCellWidget(row, col, btn_widget)

    def _update_stats(self):
        total = len(self.requests)
        draft = sum(1 for r in self.requests if r.get("status") == "draft")
        pending = sum(1 for r in self.requests if r.get("status") == "pending")
        approved = sum(1 for r in self.requests if r.get("status") == "approved")
        rejected = sum(1 for r in self.requests if r.get("status") == "rejected")

        self.stat_cards["total"].update_value(str(total))
        self.stat_cards["draft"].update_value(str(draft))
        self.stat_cards["pending"].update_value(str(pending))
        self.stat_cards["approved"].update_value(str(approved))
        self.stat_cards["rejected"].update_value(str(rejected))

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

    def _confirm_delete(self, req_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu talebi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(req_id)
