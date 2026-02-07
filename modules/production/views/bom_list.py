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
    QMenu,
    QMessageBox,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QAction

from config.icons import ICONS
from database.models.production import BOMStatus
from ui.components.base_list_page import BaseListPage
from ui.components.enhanced_table import ColumnConfig


class BOMListPage(BaseListPage):
    """Ürün reçeteleri liste sayfası."""

    bom_selected = pyqtSignal(int)
    # add_clicked, edit_clicked, delete_clicked BaseListPage'den geliyor

    STATUS_NAMES = {
        BOMStatus.DRAFT: ("Taslak", "#94a3b8"),
        BOMStatus.ACTIVE: ("Aktif", "#10b981"),
        BOMStatus.REVISION: ("Revizyon", "#f59e0b"),
        BOMStatus.OBSOLETE: ("İptal", "#ef4444"),
    }

    def __init__(self, parent=None):
        columns = [
            ColumnConfig(
                "code", "Reçete Kodu", width=120, sortable=True, filterable=True
            ),
            ColumnConfig("item", "Ürün", width=250, stretch=True, filterable=True),
            ColumnConfig("version", "Versiyon", width=80),
            ColumnConfig("quantity", "Baz Miktar", width=100, filter_type="number"),
            ColumnConfig("unit", "Birim", width=70),
            ColumnConfig("status", "Durum", width=100, filter_type="enum"),
            ColumnConfig(
                "material_cost", "Malzeme Maliyeti", width=120, filter_type="number"
            ),
        ]

        super().__init__(
            title="Ürün Reçeteleri",
            icon=ICONS.PRODUCTION,
            table_id="bom_list",
            columns=columns,
            show_add=True,
            add_text="Yeni Reçete",
            search_placeholder="Reçete kodu, ürün adı ara...",
            parent=parent,
        )

        self.boms_data = []

        # Footer İstatistikleri
        self.footer.add_stat("active", "Aktif", ICONS.CHECK, "success")
        self.footer.add_stat("draft", "Taslak", ICONS.TIME, "info")
        self.footer.add_stat("revision", "Revizyon", ICONS.EDIT, "warning")

        # Context Menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Sinyal bağlantıları
        self.view_clicked.connect(self.edit_clicked.emit)  # Çift tık -> Düzenle

        # Filtre seçenekleri
        self.table.set_filter_options(
            "status", [n[0] for n in self.STATUS_NAMES.values()]
        )

    def load_data(self, boms: list):
        """Tabloyu verilerle doldur"""
        self.boms_data = boms
        self.table.setRowCount(len(boms))

        active_count = draft_count = revision_count = 0

        self.table.setSortingEnabled(False)
        for row, bom in enumerate(boms):
            self._populate_row(row, bom)

            # İstatistikler
            if bom.status == BOMStatus.ACTIVE:
                active_count += 1
            elif bom.status == BOMStatus.DRAFT:
                draft_count += 1
            elif bom.status == BOMStatus.REVISION:
                revision_count += 1
        self.table.setSortingEnabled(True)

        # İstatistik kartlarını güncelle
        self.update_count(len(boms))
        self.update_stat_card("active", str(active_count))
        self.update_stat_card("draft", str(draft_count))
        self.update_stat_card("revision", str(revision_count))

        # Filtreleri uygula
        self.table.apply_saved_filters()

    def _populate_row(self, row: int, bom):
        # code
        cell = QTableWidgetItem(bom.code)
        cell.setData(Qt.ItemDataRole.UserRole, bom.id)
        cell.setForeground(QColor("#818cf8"))
        self.table.setItem(row, 0, cell)

        # item
        item_code = bom.item.code if bom.item else "-"
        item_name = bom.item.name if bom.item else "-"
        item_text = f"{item_code} - {item_name}"
        self.table.setItem(row, 1, QTableWidgetItem(item_text))

        # version
        ver_text = f"v{bom.version} (Rev {bom.revision})"
        self.table.setItem(row, 2, QTableWidgetItem(ver_text))

        # quantity
        from ui.components.enhanced_table import NumericTableWidgetItem

        cell = NumericTableWidgetItem(bom.base_quantity, f"{bom.base_quantity:,.2f}")
        cell.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.table.setItem(row, 3, cell)

        # unit
        unit_text = bom.unit.code if bom.unit else "-"
        self.table.setItem(row, 4, QTableWidgetItem(unit_text))

        # status
        status_text, color = self.STATUS_NAMES.get(
            bom.status, ("Bilinmiyor", "#000000")
        )
        cell = QTableWidgetItem(status_text)
        cell.setForeground(QColor(color))
        self.table.setItem(row, 5, cell)

        # material_cost
        cost = bom.total_material_cost or 0
        cell = NumericTableWidgetItem(cost, f"₺{cost:,.2f}")
        cell.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.table.setItem(row, 6, cell)

    def get_filters(self) -> dict:
        return {
            "keyword": self.header.get_search_text(),
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
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(bom_id))
        menu.addAction(edit_action)

        menu.addSeparator()

        delete_action = QAction("Sil", self)
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
