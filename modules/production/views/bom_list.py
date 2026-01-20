"""
Akıllı İş - Ürün Reçeteleri (BOM) Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidgetItem,
    QComboBox,
    QMenu,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction

from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
)


class BOMListPage(QWidget):
    """Ürün reçeteleri listesi."""

    # Sinyaller
    new_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    copy_clicked = pyqtSignal(int)
    activate_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    STATUS_DISPLAY = {
        "draft": ("🟡 Taslak", "#f59e0b"),
        "active": ("✅ Aktif", "#10b981"),
        "revision": ("🔄 Revizyon", "#3b82f6"),
        "obsolete": ("❌ Geçersiz", "#ef4444"),
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
            title="Ürün Reçeteleri (BOM)",
            icon="📋",
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Reçete",
            search_placeholder="Reçete ara...",
            parent=self,
        )

        # Filtre ekle
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem("🟡 Taslak", "draft")
        self.status_combo.addItem("✅ Aktif", "active")
        self.status_combo.addItem("🔄 Revizyon", "revision")
        self.status_combo.addItem("❌ Geçersiz", "obsolete")
        self.status_combo.setMinimumWidth(130)
        self.status_combo.currentIndexChanged.connect(
            lambda: self.refresh_requested.emit()
        )

        if self.header.search_input:
            h_layout = self.header.header_layout()
            idx = h_layout.indexOf(self.header.search_input)
            h_layout.insertWidget(idx, QLabel("Durum:"))
            h_layout.insertWidget(idx + 1, self.status_combo)

        layout.addWidget(self.header)

        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.stat_cards = {}
        self.stat_cards["total"] = MiniStatCard("📋 Toplam Reçete", "0", "#6366f1")
        self.stat_cards["active"] = MiniStatCard("✅ Aktif", "0", "#10b981")
        self.stat_cards["draft"] = MiniStatCard("🟡 Taslak", "0", "#f59e0b")
        self.stat_cards["products"] = MiniStatCard("📦 Ürün Sayısı", "0", "#3b82f6")

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        columns = [
            ColumnConfig("code", "Reçete Kodu", width=120),
            ColumnConfig("item_name", "Mamul", width=200),
            ColumnConfig("name", "Reçete Adı", width=200, stretch=True),
            ColumnConfig("version", "Versiyon", width=80),
            ColumnConfig("line_count", "Malzeme Sayısı", width=110),
            ColumnConfig("total_cost", "Tahmini Maliyet", width=130),
            ColumnConfig("status", "Durum", width=100),
        ]

        self.table = EnhancedTableWidget(
            table_id="bom_list",
            columns=columns,
            parent=self,
        )
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.table)

        # Alt bilgi
        self.count_label = QLabel("Toplam: 0 reçete")
        layout.addWidget(self.count_label)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.new_clicked.emit)
        self.header.search_changed.connect(self._on_search)
        self.table.row_double_clicked.connect(self.edit_clicked.emit)

    def load_data(self, boms: list):
        self.table.setRowCount(len(boms))
        visible_cols = self.table.get_visible_columns()

        active_count = draft_count = 0
        unique_products = set()

        for row, bom in enumerate(boms):
            self._populate_row(row, bom, visible_cols)

            status = bom.get("status", "draft")
            if status == "active":
                active_count += 1
            elif status == "draft":
                draft_count += 1
            unique_products.add(bom.get("item_id"))

        # Kartları güncelle
        self.stat_cards["total"].update_value(str(len(boms)))
        self.stat_cards["active"].update_value(str(active_count))
        self.stat_cards["draft"].update_value(str(draft_count))
        self.stat_cards["products"].update_value(str(len(unique_products)))

        self.count_label.setText(f"Toplam: {len(boms)} reçete")

    def _populate_row(self, row: int, bom: dict, visible_cols: list):
        bom_id = bom.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "code":
                item = QTableWidgetItem(bom.get("code", ""))
                item.setData(Qt.ItemDataRole.UserRole, bom_id)
                item.setForeground(QColor("#818cf8"))
                self.table.setItem(row, col_idx, item)

            elif col_key == "item_name":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(bom.get("item_name", "-"))
                )

            elif col_key == "name":
                self.table.setItem(row, col_idx, QTableWidgetItem(bom.get("name", "")))

            elif col_key == "version":
                version = f"v{bom.get('version', 1)}.{bom.get('revision', 'A')}"
                item = QTableWidgetItem(version)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col_idx, item)

            elif col_key == "line_count":
                item = QTableWidgetItem(str(bom.get("line_count", 0)))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col_idx, item)

            elif col_key == "total_cost":
                cost = bom.get("total_cost", 0)
                item = QTableWidgetItem(f"₺{cost:,.2f}")
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, item)

            elif col_key == "status":
                status = bom.get("status", "draft")
                text, color = self.STATUS_DISPLAY.get(status, ("?", "#ffffff"))
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color))
                self.table.setItem(row, col_idx, item)

        self.table.setRowHeight(row, 48)

    def get_status_filter(self) -> str:
        return self.status_combo.currentData()

    def _on_search(self, text: str):
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = any(
                self.table.item(row, col)
                and text in self.table.item(row, col).text().lower()
                for col in range(self.table.columnCount())
            )
            self.table.setRowHidden(row, not match)

    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        bom_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        status_col = (
            self.table.get_visible_columns().index("status")
            if "status" in self.table.get_visible_columns()
            else 6
        )
        status_text = (
            self.table.item(row, status_col).text()
            if self.table.item(row, status_col)
            else ""
        )

        menu = QMenu(self)
        view_action = QAction("👁 Görüntüle", self)
        view_action.triggered.connect(lambda: self.view_clicked.emit(bom_id))
        menu.addAction(view_action)

        edit_action = QAction("✏️ Düzenle", self)
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(bom_id))
        menu.addAction(edit_action)

        copy_action = QAction("📋 Kopyala", self)
        copy_action.triggered.connect(lambda: self.copy_clicked.emit(bom_id))
        menu.addAction(copy_action)

        menu.addSeparator()

        if "Aktif" not in status_text:
            activate_action = QAction("✅ Aktifleştir", self)
            activate_action.triggered.connect(
                lambda: self.activate_clicked.emit(bom_id)
            )
            menu.addAction(activate_action)

        menu.addSeparator()

        delete_action = QAction("🗑 Sil", self)
        delete_action.triggered.connect(lambda: self._confirm_delete(bom_id))
        menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _confirm_delete(self, bom_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu reçeteyi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(bom_id)
