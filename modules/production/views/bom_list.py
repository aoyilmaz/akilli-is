"""
Akıllı İş - Ürün Reçeteleri (BOM) Liste Sayfası
EnhancedTableWidget kullanılarak yeniden yapılandırıldı.
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
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QAction

from config.icons import ICONS
from database.models.production import BOMStatus
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
)


class BOMListPage(QWidget):
    """Ürün reçeteleri liste sayfası."""

    # Sinyaller
    bom_selected = pyqtSignal(int)
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    STATUS_NAMES = {
        BOMStatus.DRAFT: ("Taslak", "#94a3b8"),
        BOMStatus.ACTIVE: ("Aktif", "#10b981"),
        BOMStatus.REVISION: ("Revizyon", "#f59e0b"),
        BOMStatus.OBSOLETE: ("İptal", "#ef4444"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.boms_data = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Ürün Reçeteleri",
            icon=ICONS.PRODUCTION,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Reçete",
            search_placeholder="Reçete kodu, ürün adı ara...",
            parent=self,
        )

        # Filtreleri header'a ekle
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem("Aktif", BOMStatus.ACTIVE)
        self.status_combo.addItem("Taslak", BOMStatus.DRAFT)
        self.status_combo.addItem("Revizyon", BOMStatus.REVISION)
        self.status_combo.addItem("İptal", BOMStatus.OBSOLETE)
        self.status_combo.setMinimumWidth(130)
        self.status_combo.setFixedHeight(36)
        self.status_combo.currentIndexChanged.connect(self._do_search)

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
        self.stat_cards["total"] = MiniStatCard(
            "Toplam", "0", "info", icon=ICONS.PRODUCTION
        )
        self.stat_cards["active"] = MiniStatCard(
            "Aktif", "0", "success", icon=ICONS.CHECK
        )
        self.stat_cards["draft"] = MiniStatCard("Taslak", "0", "info", icon=ICONS.TIME)
        self.stat_cards["revision"] = MiniStatCard(
            "Revizyon", "0", "warning", icon=ICONS.EDIT
        )

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        columns = [
            ColumnConfig("code", "Reçete Kodu", width=120),
            ColumnConfig("item", "Ürün", width=250),
            ColumnConfig("version", "Versiyon", width=80),
            ColumnConfig("quantity", "Baz Miktar", width=100),
            ColumnConfig("unit", "Birim", width=70),
            ColumnConfig("status", "Durum", width=100),
            ColumnConfig("material_cost", "Malzeme Maliyeti", width=120),
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
        footer_layout = QHBoxLayout()
        self.count_label = QLabel("Toplam: 0 reçete")
        footer_layout.addWidget(self.count_label)
        layout.addLayout(footer_layout)

        # Arama debounce timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._do_search)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search_changed)
        self.table.row_double_clicked.connect(self.edit_clicked.emit)

    def load_data(self, boms: list):
        """Tabloyu verilerle doldur"""
        self.boms_data = boms
        self.table.setRowCount(len(boms))
        visible_cols = self.table.get_visible_columns()

        active_count = draft_count = revision_count = 0

        for row, bom in enumerate(boms):
            self._populate_row(row, bom, visible_cols)

            # İstatistikler
            if bom.status == BOMStatus.ACTIVE:
                active_count += 1
            elif bom.status == BOMStatus.DRAFT:
                draft_count += 1
            elif bom.status == BOMStatus.REVISION:
                revision_count += 1

        # İstatistik kartlarını güncelle
        self.stat_cards["total"].update_value(str(len(boms)))
        self.stat_cards["active"].update_value(str(active_count))
        self.stat_cards["draft"].update_value(str(draft_count))
        self.stat_cards["revision"].update_value(str(revision_count))

        self.count_label.setText(f"Toplam: {len(boms)} reçete")

    def _populate_row(self, row: int, bom, visible_cols: list):
        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "code":
                cell = QTableWidgetItem(bom.code)
                cell.setData(Qt.ItemDataRole.UserRole, bom.id)
                cell.setForeground(QColor("#818cf8"))
                self.table.setItem(row, col_idx, cell)

            elif col_key == "item":
                item_code = bom.item.code if bom.item else "-"
                item_name = bom.item.name if bom.item else "-"
                item_text = f"{item_code} - {item_name}"
                self.table.setItem(row, col_idx, QTableWidgetItem(item_text))

            elif col_key == "version":
                ver_text = f"v{bom.version} (Rev {bom.revision})"
                self.table.setItem(row, col_idx, QTableWidgetItem(ver_text))

            elif col_key == "quantity":
                cell = QTableWidgetItem(f"{bom.base_quantity:,.2f}")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, cell)

            elif col_key == "unit":
                unit_text = bom.unit.code if bom.unit else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(unit_text))

            elif col_key == "material_cost":
                cost = bom.total_material_cost or 0
                cell = QTableWidgetItem(f"₺{cost:,.2f}")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, cell)

            elif col_key == "status":
                status_text, color = self.STATUS_NAMES.get(
                    bom.status, ("Bilinmiyor", "#000000")
                )
                cell = QTableWidgetItem(status_text)
                cell.setForeground(QColor(color))
                self.table.setItem(row, col_idx, cell)

    def _on_search_changed(self, text: str):
        self.search_timer.stop()
        self.search_timer.start(300)

    def _do_search(self):
        self.refresh_requested.emit()

    def get_filters(self) -> dict:
        return {
            "keyword": (
                self.header.search_input.text().strip()
                if self.header.search_input
                else ""
            ),
            "status": self.status_combo.currentData(),
        }

    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        bom_item = self.table.item(row, 0)
        if not bom_item:
            return

        bom_id = bom_item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)

        edit_action = QAction("Düzenle", self)
        edit_action.setIcon(
            ICONS.EDIT_ICON if hasattr(ICONS, "EDIT_ICON") else ICONS.EDIT
        )
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(bom_id))
        menu.addAction(edit_action)

        menu.addSeparator()

        delete_action = QAction("Sil", self)
        delete_action.setIcon(
            ICONS.DELETE_ICON if hasattr(ICONS, "DELETE_ICON") else ICONS.DELETE
        )
        delete_action.triggered.connect(lambda: self._confirm_delete(bom_id))
        menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _confirm_delete(self, bom_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu reçeteyi silmek istediğinize emin misiniz?\n\nBu işlem geri alınamaz.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(bom_id)
