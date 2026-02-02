"""
Akıllı İş - Stok Talep Listesi (Yönetici Paneli)
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidgetItem,
    QMenu,
    QMessageBox,
    QInputDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor
import qtawesome as qta

from config.icons import ICONS
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
)
from database.models import StockRequestStatus


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
        self.header = PageHeader(
            title="Stok Talepleri",
            icon=ICONS.INVENTORY,
            show_back=True,
            show_search=True,
            show_add=False,
            search_placeholder="Talep arayın...",
            parent=self,
        )
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        layout.addWidget(self.header)
        cols = [
            ColumnConfig("date", "Talep Tarihi", width=120),
            ColumnConfig("requester", "Talep Eden", width=150),
            ColumnConfig("name", "Önerilen Stok Adı", width=250, stretch=True),
            ColumnConfig("type", "Tür", width=120),
            ColumnConfig("ref", "Referans", width=150),
            ColumnConfig("status", "Durum", width=120),
        ]
        self.table = EnhancedTableWidget(
            table_id="stock_requests", columns=cols, parent=self
        )
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.doubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self.table)

        # Footer ekle
        from ui.components.table_footer import TableFooter

        self.footer = TableFooter(self)
        self.footer.add_stat("total", "Toplam", ICONS.INVENTORY, "#3498db")
        self.footer.add_stat("pending", "Bekleyen", ICONS.TIME, "#f59e0b")
        self.footer.add_stat("approved", "Onaylanan", ICONS.CHECK, "#10b981")
        self.footer.add_stat("rejected", "Reddedilen", ICONS.CLOSE, "#ef4444")

        self.footer.page_size_changed.connect(
            lambda s: self.table.setRowCount(0)
        )  # Şimdilik dummy
        layout.addWidget(self.footer)

    def load_data(self, requests: list):
        self.requests = requests
        self.table.setRowCount(len(requests))

        # İstatistikleri güncelle
        total = len(requests)
        pending = sum(1 for r in requests if r.status == StockRequestStatus.PENDING)
        approved = sum(1 for r in requests if r.status == StockRequestStatus.APPROVED)
        rejected = sum(1 for r in requests if r.status == StockRequestStatus.REJECTED)

        if hasattr(self, "footer"):
            self.footer.update_stat("total", str(total))
            self.footer.update_stat("pending", str(pending))
            self.footer.update_stat("approved", str(approved))
            self.footer.update_stat("rejected", str(rejected))
            self.footer.update_pagination(1, 1, total)

        vcols = self.table.get_visible_columns()
        for r, req in enumerate(requests):
            self._populate_row(r, req, vcols)

    def _populate_row(self, r, req, vcols):
        for ci, k in enumerate(vcols):
            if k == "date":
                ds = (
                    req.request_date.strftime("%d.%m.%Y %H:%M")
                    if req.request_date
                    else "-"
                )
                it = QTableWidgetItem(ds)
                it.setData(Qt.ItemDataRole.UserRole, req)
                self.table.setItem(r, ci, it)
            elif k == "requester":
                rn = (
                    f"{req.requester.first_name} {req.requester.last_name}"
                    if req.requester
                    else "Bilinmiyor"
                )
                self.table.setItem(r, ci, QTableWidgetItem(rn))
            elif k == "name":
                self.table.setItem(r, ci, QTableWidgetItem(req.proposed_name))
            elif k == "type":
                tv = (
                    req.item_type.value
                    if hasattr(req.item_type, "value")
                    else str(req.item_type)
                )
                self.table.setItem(r, ci, QTableWidgetItem(tv.title()))
            elif k == "ref":
                self.table.setItem(
                    r,
                    ci,
                    QTableWidgetItem(
                        req.reference_stock.code if req.reference_stock else "-"
                    ),
                )
            elif k == "status":
                s, st, c = req.status, "Beklemede", "#f59e0b"
                if s == StockRequestStatus.APPROVED:
                    st, c = "Onaylandı", "#10b981"
                elif s == StockRequestStatus.REJECTED:
                    st, c = "Reddedildi", "#ef4444"
                it = QTableWidgetItem(st)
                it.setForeground(QColor(c))
                self.table.setItem(r, ci, it)

    def _show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        req = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if req.status != StockRequestStatus.PENDING:
            return
        menu = QMenu(self)
        ap = QAction("Onayla ve Oluştur", self)
        ap.setIcon(qta.icon(ICONS.CHECK, color="#10b981"))
        ap.triggered.connect(lambda: self.request_approved.emit(req))
        menu.addAction(ap)
        re = QAction("Reddet", self)
        re.setIcon(qta.icon(ICONS.CLOSE, color="#ef4444"))
        re.triggered.connect(lambda: self._reject_request(req))
        menu.addAction(re)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _on_row_double_clicked(self, index):
        req = self.table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
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
