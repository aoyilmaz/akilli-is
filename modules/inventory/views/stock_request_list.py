"""
Akıllı İş - Stok Talep Listesi (Yönetici Paneli)
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMenu,
    QMessageBox,
    QInputDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor

from ui.components.page_header import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig
from database.models import StockRequestStatus, ItemType


class StockRequestListPage(QWidget):
    """Stok taleplerini yönetme sayfası"""

    request_approved = pyqtSignal(object)  # StockRequest object
    request_rejected = pyqtSignal(int, str)  # request_id, reason
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.requests = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Stok Talepleri",
            icon="📨",
            show_back=True,
            show_search=True,
            show_refresh=True,
            show_add=False,
            search_placeholder="Talep arayın...",
            parent=self,
        )
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        layout.addWidget(self.header)

        # Tablo
        columns = [
            ColumnConfig("date", "Talep Tarihi", width=120),
            ColumnConfig("requester", "Talep Eden", width=150),
            ColumnConfig("name", "Önerilen Stok Adı", width=250, stretch=True),
            ColumnConfig("type", "Tür", width=120),
            ColumnConfig("ref", "Referans", width=150),
            ColumnConfig("status", "Durum", width=120),
        ]

        self.table = EnhancedTableWidget(
            table_id="stock_requests",
            columns=columns,
            parent=self,
        )
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

    def load_data(self, requests: list):
        """Talepleri yükle"""
        self.requests = requests
        self.table.setRowCount(len(requests))
        visible_cols = self.table.get_visible_columns()

        for row, req in enumerate(requests):
            self._populate_row(row, req, visible_cols)

    def _populate_row(self, row: int, req, visible_cols: list):
        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "date":
                date_str = (
                    req.request_date.strftime("%d.%m.%Y %H:%M")
                    if req.request_date
                    else "-"
                )
                item = QTableWidgetItem(date_str)
                item.setData(Qt.ItemDataRole.UserRole, req)
                self.table.setItem(row, col_idx, item)

            elif col_key == "requester":
                requester_name = (
                    f"{req.requester.first_name} {req.requester.last_name}"
                    if req.requester
                    else "Bilinmiyor"
                )
                self.table.setItem(row, col_idx, QTableWidgetItem(requester_name))

            elif col_key == "name":
                self.table.setItem(row, col_idx, QTableWidgetItem(req.proposed_name))

            elif col_key == "type":
                type_val = (
                    req.item_type.value
                    if hasattr(req.item_type, "value")
                    else str(req.item_type)
                )
                self.table.setItem(row, col_idx, QTableWidgetItem(type_val.title()))

            elif col_key == "ref":
                ref_text = req.reference_stock.code if req.reference_stock else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(ref_text))

            elif col_key == "status":
                status = req.status
                status_text = "Beklemede"
                color = "#f59e0b"  # Turuncu

                if status == StockRequestStatus.APPROVED:
                    status_text = "Onaylandı"
                    color = "#10b981"  # Yeşil
                elif status == StockRequestStatus.REJECTED:
                    status_text = "Reddedildi"
                    color = "#ef4444"  # Kırmızı

                item = QTableWidgetItem(status_text)
                item.setForeground(QColor(color))
                self.table.setItem(row, col_idx, item)

        self.table.setRowHeight(row, 40)

    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        item = self.table.item(row, 0)
        req = item.data(Qt.ItemDataRole.UserRole)

        if req.status != StockRequestStatus.PENDING:
            return

        menu = QMenu(self)

        approve_action = QAction("✅ Onayla ve Oluştur", self)
        approve_action.triggered.connect(lambda: self.request_approved.emit(req))
        menu.addAction(approve_action)

        reject_action = QAction("❌ Reddet", self)
        reject_action.triggered.connect(lambda: self._reject_request(req))
        menu.addAction(reject_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _on_double_click(self, index):
        row = index.row()
        item = self.table.item(row, 0)
        req = item.data(Qt.ItemDataRole.UserRole)

        if req.status == StockRequestStatus.PENDING:
            self.request_approved.emit(req)
        else:
            QMessageBox.information(
                self, "Bilgi", f"Bu talep zaten {req.status.value} durumunda."
            )

    def _reject_request(self, req):
        reason, ok = QInputDialog.getText(
            self, "Reddetme Nedeni", "Lütfen reddetme nedenini giriniz:"
        )
        if ok and reason:
            self.request_rejected.emit(req.id, reason)
