"""
Akıllı İş - Satın Alma Talepleri Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

import qtawesome as qta
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QTableWidgetItem,
    QComboBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.components import (
    BaseListPage,
    ColumnConfig,
)
from config.icons import ICONS


class PurchaseRequestListPage(BaseListPage):
    """Satın alma talepleri listesi."""

    # Sinyaller (Ek sinyaller)
    approve_clicked = pyqtSignal(int)
    reject_clicked = pyqtSignal(int)
    create_order_clicked = pyqtSignal(int)

    STATUS_LABELS = {
        "draft": ("Taslak", "#64748b"),
        "pending": ("Onay Bekliyor", "#f59e0b"),
        "approved": ("Onaylandı", "#10b981"),
        "rejected": ("Reddedildi", "#ef4444"),
        "ordered": ("Sipariş Verildi", "#8b5cf6"),
        "cancelled": ("İptal", "#475569"),
    }

    PRIORITY_LABELS = {
        1: ("Düşük", "#64748b"),
        2: ("Normal", "#3b82f6"),
        3: ("Yüksek", "#f59e0b"),
        4: ("Acil", "#ef4444"),
    }

    def __init__(self, parent=None):
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

        super().__init__(
            title="Satın Alma Talepleri",
            icon=ICONS.INVOICE,
            table_id="purchase_requests",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Talep",
            search_placeholder="Ara... (talep no, departman)",
            parent=parent,
        )

        self.requests = []
        self._setup_filters()
        self._setup_stat_cards()

    def _setup_filters(self):
        # Filtre ekle
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("Taslak", "draft")
        self.status_filter.addItem("Onay Bekliyor", "pending")
        self.status_filter.addItem("Onaylandı", "approved")
        self.status_filter.addItem("Reddedildi", "rejected")
        self.status_filter.addItem("Sipariş Verildi", "ordered")
        self.status_filter.setMinimumWidth(160)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)

        if self.header.search_input:
            h_layout = self.header.header_layout()
            idx = h_layout.indexOf(self.header.search_input)
            h_layout.insertWidget(idx, self.status_filter)

    def _setup_stat_cards(self):
        self.add_stat_card("total", "Toplam", "0", "info", ICONS.CRM)
        self.add_stat_card("draft", "Taslak", "0", "warning", ICONS.TIME)
        self.add_stat_card("pending", "Bekleyen", "0", "warning", ICONS.TIME)
        self.add_stat_card("approved", "Onaylı", "0", "success", ICONS.CHECK)
        self.add_stat_card("rejected", "Ret", "0", "danger", ICONS.DANGER)

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
                status = req.get("status", "draft")
                actions = ["view"]

                if status == "draft":
                    actions.extend(["edit", "delete"])
                elif status == "pending":
                    actions.extend(["approve", "cancel"])  # cancel here means reject
                elif status == "approved":
                    actions.append("order")

                callbacks = {
                    "view": lambda _, rid=req_id: self.view_clicked.emit(rid),
                    "edit": lambda _, rid=req_id: self.edit_clicked.emit(rid),
                    "delete": lambda _, rid=req_id: self._confirm_delete(rid),
                    "approve": lambda _, rid=req_id: self.approve_clicked.emit(rid),
                    "cancel": lambda _, rid=req_id: self.reject_clicked.emit(rid),
                    "order": lambda _, rid=req_id: self.create_order_clicked.emit(rid),
                }

                # Özel butonlar için manuel gruplama
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(4, 2, 4, 2)
                layout.setSpacing(4)

                from ui.components.action_buttons import (
                    create_view_button,
                    create_edit_button,
                    create_delete_button,
                    create_approve_button,
                    create_cancel_button,
                    create_custom_button,
                )

                if "view" in actions:
                    btn = create_view_button(widget)
                    btn.clicked.connect(callbacks["view"])
                    layout.addWidget(btn)

                if "edit" in actions:
                    btn = create_edit_button(widget)
                    btn.clicked.connect(callbacks["edit"])
                    layout.addWidget(btn)

                if "approve" in actions:
                    btn = create_approve_button(widget)
                    btn.clicked.connect(callbacks["approve"])
                    layout.addWidget(btn)

                if "cancel" in actions:
                    btn = create_cancel_button(widget)
                    btn.setToolTip("Reddet")
                    btn.clicked.connect(callbacks["cancel"])
                    layout.addWidget(btn)

                if "order" in actions:
                    btn = create_custom_button(
                        widget, ICONS.INVENTORY, "Sipariş Oluştur", "purple"
                    )
                    btn.clicked.connect(callbacks["order"])
                    layout.addWidget(btn)

                if "delete" in actions:
                    btn = create_delete_button(widget)
                    btn.clicked.connect(callbacks["delete"])
                    layout.addWidget(btn)

                layout.addStretch()
                self.table.setCellWidget(row, col_idx, widget)

    def _format_date(self, dt) -> str:
        from datetime import date

        if dt:
            if isinstance(dt, date):
                return dt.strftime("%d.%m.%Y")
            return str(dt)
        return "-"

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
