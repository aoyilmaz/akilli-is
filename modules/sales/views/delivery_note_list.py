"""
Akıllı İş - Teslimat İrsaliyeleri Liste Sayfası
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


class DeliveryNoteListPage(QWidget):
    """Teslimat irsaliyeleri listesi sayfası."""

    # Sinyaller
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    ship_clicked = pyqtSignal(int)
    complete_clicked = pyqtSignal(int)
    cancel_clicked = pyqtSignal(int)
    create_invoice_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    STATUS_LABELS = {
        "draft": ("🔵 Taslak", "#64748b"),
        "shipped": ("📦 Sevk Edildi", "#f59e0b"),
        "delivered": ("✅ Teslim Edildi", "#10b981"),
        "cancelled": ("⚫ İptal", "#475569"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.notes = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Teslimat İrsaliyeleri",
            icon="🚚",
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni İrsaliye",
            search_placeholder="Ara... (irsaliye no, müşteri)",
            parent=self,
        )

        # Filtre
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("🔵 Taslak", "draft")
        self.status_filter.addItem("📦 Sevk Edildi", "shipped")
        self.status_filter.addItem("✅ Teslim Edildi", "delivered")
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
        self.stat_cards["shipped"] = MiniStatCard("📦 Sevk", "0", "#f59e0b")
        self.stat_cards["delivered"] = MiniStatCard("✅ Teslim", "0", "#10b981")

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        columns = [
            ColumnConfig("note_no", "İrsaliye No", width=120),
            ColumnConfig("date", "Tarih", width=100),
            ColumnConfig("customer", "Müşteri", width=200, stretch=True),
            ColumnConfig("order_no", "Sipariş No", width=120),
            ColumnConfig("items", "Kalem", width=60),
            ColumnConfig("ship_date", "Sevk Tarihi", width=100),
            ColumnConfig("status", "Durum", width=130),
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
            table_id="delivery_notes",
            columns=columns,
            parent=self,
        )
        layout.addWidget(self.table)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search)
        self.table.row_double_clicked.connect(self.view_clicked.emit)

    def load_data(self, notes: list):
        self.notes = notes
        self._apply_filter()

    def _apply_filter(self):
        status_filter = self.status_filter.currentData()
        filtered = self.notes
        if status_filter:
            filtered = [n for n in self.notes if n.get("status") == status_filter]
        self._display_data(filtered)
        self._update_stats()

    def _display_data(self, notes: list):
        self.table.setRowCount(len(notes))
        visible_cols = self.table.get_visible_columns()

        for row, note in enumerate(notes):
            self._populate_row(row, note, visible_cols)

    def _populate_row(self, row: int, note: dict, visible_cols: list):
        note_id = note.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "note_no":
                item = QTableWidgetItem(note.get("note_no", ""))
                item.setData(Qt.ItemDataRole.UserRole, note_id)
                self.table.setItem(row, col_idx, item)

            elif col_key == "date":
                self.table.setItem(
                    row,
                    col_idx,
                    QTableWidgetItem(self._format_date(note.get("note_date"))),
                )

            elif col_key == "customer":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(note.get("customer_name", "") or "-")
                )

            elif col_key == "order_no":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(note.get("order_no", "") or "-")
                )

            elif col_key == "items":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(str(note.get("total_items", 0)))
                )

            elif col_key == "ship_date":
                self.table.setItem(
                    row,
                    col_idx,
                    QTableWidgetItem(self._format_date(note.get("ship_date"))),
                )

            elif col_key == "status":
                status = note.get("status", "draft")
                label, _ = self.STATUS_LABELS.get(status, ("Taslak", "#64748b"))
                self.table.setItem(row, col_idx, QTableWidgetItem(label))

            elif col_key == "actions":
                self._add_action_buttons(row, col_idx, note)

        self.table.setRowHeight(row, 52)

    def _format_date(self, dt) -> str:
        if dt:
            if isinstance(dt, date):
                return dt.strftime("%d.%m.%Y")
            return str(dt)
        return "-"

    def _add_action_buttons(self, row: int, col: int, note: dict):
        btn_widget = QWidget()
        btn_widget.setProperty("class", "action-button-group")
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(2, 2, 2, 2)
        btn_layout.setSpacing(2)

        note_id = note.get("id")
        status = note.get("status", "draft")

        # Görüntüle
        view_btn = QPushButton("👁")
        view_btn.setFixedSize(28, 26)
        view_btn.clicked.connect(
            lambda checked, nid=note_id: self.view_clicked.emit(nid)
        )
        btn_layout.addWidget(view_btn)

        if status == "draft":
            edit_btn = QPushButton("✏")
            edit_btn.setFixedSize(28, 26)
            edit_btn.clicked.connect(
                lambda checked, nid=note_id: self.edit_clicked.emit(nid)
            )
            btn_layout.addWidget(edit_btn)

            ship_btn = QPushButton("📦")
            ship_btn.setFixedSize(28, 26)
            ship_btn.setToolTip("Sevk Et")
            ship_btn.clicked.connect(
                lambda checked, nid=note_id: self.ship_clicked.emit(nid)
            )
            btn_layout.addWidget(ship_btn)

        if status == "shipped":
            complete_btn = QPushButton("✓")
            complete_btn.setFixedSize(28, 26)
            complete_btn.setToolTip("Teslim Et")
            complete_btn.clicked.connect(
                lambda checked, nid=note_id: self.complete_clicked.emit(nid)
            )
            btn_layout.addWidget(complete_btn)

        if status == "delivered":
            invoice_btn = QPushButton("📄")
            invoice_btn.setFixedSize(28, 26)
            invoice_btn.setToolTip("Fatura Oluştur")
            invoice_btn.clicked.connect(
                lambda checked, nid=note_id: self.create_invoice_clicked.emit(nid)
            )
            btn_layout.addWidget(invoice_btn)

        if status in ["draft", "shipped"]:
            cancel_btn = QPushButton("❌")
            cancel_btn.setFixedSize(28, 26)
            cancel_btn.clicked.connect(
                lambda checked, nid=note_id: self.cancel_clicked.emit(nid)
            )
            btn_layout.addWidget(cancel_btn)

        if status == "draft":
            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(28, 26)
            del_btn.clicked.connect(
                lambda checked, nid=note_id: self._confirm_delete(nid)
            )
            btn_layout.addWidget(del_btn)

        self.table.setCellWidget(row, col, btn_widget)

    def _update_stats(self):
        total = len(self.notes)
        draft = sum(1 for n in self.notes if n.get("status") == "draft")
        shipped = sum(1 for n in self.notes if n.get("status") == "shipped")
        delivered = sum(1 for n in self.notes if n.get("status") == "delivered")

        self.stat_cards["total"].update_value(str(total))
        self.stat_cards["draft"].update_value(str(draft))
        self.stat_cards["shipped"].update_value(str(shipped))
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

    def _confirm_delete(self, note_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu irsaliyeyi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(note_id)
