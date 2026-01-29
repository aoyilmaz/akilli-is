"""
Akıllı İş - Depo Listesi Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidgetItem,
    QMenu,
    QMessageBox,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction
import qtawesome as qta

from config.icons import ICONS
from config.themes import get_theme
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
)


class WarehouseListPage(QWidget):
    """Depo listesi sayfası."""

    add_clicked, edit_clicked = pyqtSignal(), pyqtSignal(int)
    delete_clicked, refresh_requested = pyqtSignal(int), pyqtSignal()
    locations_clicked = pyqtSignal(int)

    TYPE_NAMES = {
        "general": "Genel",
        "raw": "Hammadde",
        "finished": "Mamül",
        "cold": "Soğuk",
        "bonded": "Antrepo",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self.header = PageHeader(
            title="Depolar",
            icon=ICONS.WAREHOUSE,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Depo",
            search_placeholder="Depo kodu veya adı ile ara...",
            parent=self,
        )

        # Status Filter
        self.status_filter = QComboBox()
        self.status_filter.setFixedWidth(120)
        self.status_filter.setFixedHeight(36)
        self.status_filter.addItems(["Tümü", "Aktif", "Pasif"])

        # Add filter and move refresh button
        hl = self.header.header_layout()
        idx = hl.indexOf(self.header.search_input) if self.header.search_input else -1
        if idx >= 0:
            hl.insertWidget(idx, QLabel("Durum:"))
            hl.insertWidget(idx + 1, self.status_filter)

        if self.header.refresh_btn:
            hl.removeWidget(self.header.refresh_btn)
            hl.addWidget(self.header.refresh_btn)

        layout.addWidget(self.header)

        cols = [
            ColumnConfig("code", "Kod", width=100),
            ColumnConfig("name", "Depo Adı", width=200, stretch=True),
            ColumnConfig("type", "Tür", width=120),
            ColumnConfig("city", "Şehir", width=120),
            ColumnConfig("manager", "Yetkili", width=150),
            ColumnConfig("phone", "Telefon", width=120),
            ColumnConfig("locations", "Lokasyon", width=80),
            ColumnConfig("is_default", "Varsayılan", width=90),
            ColumnConfig("status", "Durum", width=90),
        ]
        self.table = EnhancedTableWidget(
            table_id="warehouses", columns=cols, parent=self
        )
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.table)
        self.count_label = QLabel("Toplam: 0 depo")
        layout.addWidget(self.count_label)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._filter_rows)
        self.status_filter.currentIndexChanged.connect(self._filter_rows)
        self.table.row_double_clicked.connect(self.edit_clicked.emit)

    def load_data(self, warehouses: list):
        self.table.setRowCount(len(warehouses))
        vcols = self.table.get_visible_columns()
        for r, wh in enumerate(warehouses):
            self._populate_row(r, wh, vcols)
        self.count_label.setText(f"Toplam: {len(warehouses)} depo")
        self._filter_rows()

    def _filter_rows(self, text=None):
        search_text = (
            self.header.search_input.text().lower().strip()
            if self.header.search_input
            else ""
        )
        status = self.status_filter.currentText()

        visible_count = 0
        for r in range(self.table.rowCount()):
            code = self.table.item(r, 0).text().lower()
            name = self.table.item(r, 1).text().lower()
            # Status column is likely the last one or we find it
            # Columns: code, name, type, city, manager, phone, locations, is_default, status
            # Status is index 8 based on cols array
            row_status = self.table.item(r, 8).text()

            text_match = (
                (not search_text) or (search_text in code) or (search_text in name)
            )
            status_match = (status == "Tümü") or (row_status == status)

            visible = text_match and status_match
            self.table.setRowHidden(r, not visible)
            if visible:
                visible_count += 1

        self.count_label.setText(f"Toplam: {visible_count} depo")

    def _populate_row(self, r, wh, vcols):
        for ci, key in enumerate(vcols):
            if key == "code":
                it = QTableWidgetItem(wh.code)
                it.setData(Qt.ItemDataRole.UserRole, wh.id)
                it.setForeground(QColor("#818cf8"))
                self.table.setItem(r, ci, it)
            elif key == "name":
                self.table.setItem(r, ci, QTableWidgetItem(wh.name))
            elif key == "type":
                self.table.setItem(
                    r,
                    ci,
                    QTableWidgetItem(self.TYPE_NAMES.get(wh.warehouse_type, "Genel")),
                )
            elif key == "city":
                self.table.setItem(r, ci, QTableWidgetItem(wh.city or "-"))
            elif key == "manager":
                self.table.setItem(r, ci, QTableWidgetItem(wh.manager_name or "-"))
            elif key == "phone":
                self.table.setItem(r, ci, QTableWidgetItem(wh.phone or "-"))
            elif key == "locations":
                it = QTableWidgetItem(str(len(wh.locations) if wh.locations else 0))
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, ci, it)
            elif key == "is_default":
                it = QTableWidgetItem("Varsayılan" if wh.is_default else "")
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if wh.is_default:
                    it.setForeground(QColor("#10b981"))
                self.table.setItem(r, ci, it)
            elif key == "status":
                act, it, t = wh.is_active, QTableWidgetItem(), get_theme()
                if act:
                    it.setText("Aktif")
                    it.setIcon(qta.icon(ICONS.CHECK, color=t.success))
                    it.setForeground(QColor(t.success))
                else:
                    it.setText("Pasif")
                    it.setIcon(qta.icon(ICONS.CLOSE, color=t.text_muted))
                    it.setForeground(QColor(t.text_muted))
                self.table.setItem(r, ci, it)

    def get_search_text(self) -> str:
        return (
            self.header.search_input.text().strip() if self.header.search_input else ""
        )

    def _show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        wh_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        ed = QAction("Düzenle", self)
        ed.setIcon(qta.icon(ICONS.EDIT, color="#3498db"))
        ed.triggered.connect(lambda: self.edit_clicked.emit(wh_id))
        menu.addAction(ed)
        lo = QAction("Lokasyonlar", self)
        lo.setIcon(qta.icon(ICONS.TAG, color="#8b5cf6"))
        lo.triggered.connect(lambda: self.locations_clicked.emit(wh_id))
        menu.addAction(lo)
        menu.addSeparator()
        de = QAction("Sil", self)
        de.setIcon(qta.icon(ICONS.DELETE, color="#ef4444"))
        de.triggered.connect(lambda: self._confirm_delete(wh_id))
        menu.addAction(de)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _confirm_delete(self, wh_id: int):
        if (
            QMessageBox.question(
                self,
                "Silme Onayı",
                "Bu depoyu silmek istediğinize emin misiniz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.delete_clicked.emit(wh_id)
