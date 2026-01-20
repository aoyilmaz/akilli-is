"""
Akıllı İş - Depo Listesi Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidgetItem,
    QMenu,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction

from config import COLORS
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
)


class WarehouseListPage(QWidget):
    """Depo listesi sayfası."""

    # Sinyaller
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()
    locations_clicked = pyqtSignal(int)

    TYPE_NAMES = {
        "general": "🏭 Genel",
        "raw": "🧱 Hammadde",
        "finished": "📦 Mamul",
        "cold": "❄️ Soğuk",
        "bonded": "🔒 Antrepo",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Depolar",
            icon="🏭",
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Depo",
            search_placeholder="Depo kodu veya adı ile ara...",
            parent=self,
        )
        layout.addWidget(self.header)

        # Tablo
        columns = [
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
            table_id="warehouses",
            columns=columns,
            parent=self,
        )
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.table)

        # Alt bilgi
        self.count_label = QLabel("Toplam: 0 depo")
        layout.addWidget(self.count_label)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(lambda: self.refresh_requested.emit())
        self.table.row_double_clicked.connect(self.edit_clicked.emit)

    def load_data(self, warehouses: list):
        """Verileri yükle"""
        self.table.setRowCount(len(warehouses))
        visible_cols = self.table.get_visible_columns()

        for row, wh in enumerate(warehouses):
            self._populate_row(row, wh, visible_cols)

        self.count_label.setText(f"Toplam: {len(warehouses)} depo")

    def _populate_row(self, row: int, wh, visible_cols: list):
        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "code":
                item = QTableWidgetItem(wh.code)
                item.setData(Qt.ItemDataRole.UserRole, wh.id)
                item.setForeground(QColor("#818cf8"))
                self.table.setItem(row, col_idx, item)

            elif col_key == "name":
                self.table.setItem(row, col_idx, QTableWidgetItem(wh.name))

            elif col_key == "type":
                type_text = self.TYPE_NAMES.get(wh.warehouse_type, "🏭 Genel")
                self.table.setItem(row, col_idx, QTableWidgetItem(type_text))

            elif col_key == "city":
                self.table.setItem(row, col_idx, QTableWidgetItem(wh.city or "-"))

            elif col_key == "manager":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(wh.manager_name or "-")
                )

            elif col_key == "phone":
                self.table.setItem(row, col_idx, QTableWidgetItem(wh.phone or "-"))

            elif col_key == "locations":
                loc_count = len(wh.locations) if wh.locations else 0
                item = QTableWidgetItem(str(loc_count))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col_idx, item)

            elif col_key == "is_default":
                item = QTableWidgetItem("✓" if wh.is_default else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if wh.is_default:
                    item.setForeground(QColor(COLORS["success"]))
                self.table.setItem(row, col_idx, item)

            elif col_key == "status":
                is_active = wh.is_active
                item = QTableWidgetItem("✅ Aktif" if is_active else "❌ Pasif")
                item.setForeground(
                    QColor(COLORS["success"] if is_active else COLORS["error"])
                )
                self.table.setItem(row, col_idx, item)

        self.table.setRowHeight(row, 48)

    def get_search_text(self) -> str:
        return (
            self.header.search_input.text().strip() if self.header.search_input else ""
        )

    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        wh_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)
        edit_action = QAction("✏️ Düzenle", self)
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(wh_id))
        menu.addAction(edit_action)

        loc_action = QAction("📍 Lokasyonlar", self)
        loc_action.triggered.connect(lambda: self.locations_clicked.emit(wh_id))
        menu.addAction(loc_action)

        menu.addSeparator()

        delete_action = QAction("🗑 Sil", self)
        delete_action.triggered.connect(lambda: self._confirm_delete(wh_id))
        menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _confirm_delete(self, wh_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu depoyu silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(wh_id)
