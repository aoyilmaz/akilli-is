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
        self._total_count = 0
        self._setup_ui()
        self._connect_signals()

        # Otomatik yenileme
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.timeout.connect(lambda: self.refresh_requested.emit())
        self._auto_refresh_timer.start(30000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Ürün Reçeteleri",
            icon=ICONS.PRODUCTION,
            show_search=True,
            show_add=True,
            add_text="Yeni Reçete",
            search_placeholder="Reçete kodu, ürün adı ara...",
            parent=self,
        )
        layout.addWidget(self.header)

        # Tablo
        columns = [
            ColumnConfig("code", "Reçete Kodu", width=120),
            ColumnConfig("item", "Ürün", width=250, stretch=True),
            ColumnConfig("version", "Versiyon", width=80),
            ColumnConfig("quantity", "Baz Miktar", width=100, filter_type="number"),
            ColumnConfig("unit", "Birim", width=70),
            ColumnConfig("status", "Durum", width=100, filter_type="enum"),
            ColumnConfig("material_cost", "Malzeme Maliyeti", width=120, filter_type="number"),
        ]

        self.table = EnhancedTableWidget(
            table_id="bom_list",
            columns=columns,
            parent=self,
        )
        self.table.set_standard_row_height(48)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.table)

        # Footer
        self._setup_footer(layout)

        # Arama debounce timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._do_search)

    def _setup_footer(self, layout: QVBoxLayout):
        """Footer - kayıt sayısı ve istatistikler"""
        footer = QFrame()
        footer.setProperty("class", "table-footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 8, 0, 0)
        footer_layout.setSpacing(16)

        # Sol: Kayıt sayısı
        self.count_label = QLabel("Toplam: 0 reçete")
        self.count_label.setProperty("class", "footer-count")
        footer_layout.addWidget(self.count_label)

        # İstatistik kartları (horizontal)
        self.stat_cards = {}
        self.stat_cards["total"] = MiniStatCard(
            "Toplam", "0", "info", orientation="horizontal", icon=ICONS.PRODUCTION
        )
        self.stat_cards["active"] = MiniStatCard(
            "Aktif", "0", "success", orientation="horizontal", icon=ICONS.CHECK
        )
        self.stat_cards["draft"] = MiniStatCard(
            "Taslak", "0", "info", orientation="horizontal", icon=ICONS.TIME
        )
        self.stat_cards["revision"] = MiniStatCard(
            "Revizyon", "0", "warning", orientation="horizontal", icon=ICONS.EDIT
        )

        for card in self.stat_cards.values():
            footer_layout.addWidget(card)

        footer_layout.addStretch()

        # Sağ: Otomatik yenileme göstergesi
        refresh_indicator = QLabel("⟳")
        refresh_indicator.setProperty("class", "refresh-indicator")
        refresh_indicator.setToolTip("Otomatik yenileme: 30s")
        footer_layout.addWidget(refresh_indicator)

        layout.addWidget(footer)

    def _connect_signals(self):
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search_changed)
        self.table.row_double_clicked.connect(self.edit_clicked.emit)
        self.table.filter_changed.connect(self._update_visible_count)

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

        self._total_count = len(boms)
        self.count_label.setText(f"Toplam: {self._total_count} reçete")

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

    def _update_visible_count(self, filters: dict = None):
        """Görünen satır sayısını güncelle"""
        visible_count = sum(
            1 for row in range(self.table.rowCount())
            if not self.table.isRowHidden(row)
        )
        if visible_count == self._total_count:
            self.count_label.setText(f"Toplam: {self._total_count} reçete")
        else:
            self.count_label.setText(
                f"Gösterilen: {visible_count} / {self._total_count} reçete"
            )

    def get_filters(self) -> dict:
        return {
            "keyword": self.header.get_search_text(),
        }

    def get_search_text(self) -> str:
        return self.header.get_search_text()

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

    def showEvent(self, event):
        super().showEvent(event)
        self._auto_refresh_timer.start(30000)

    def hideEvent(self, event):
        super().hideEvent(event)
        self._auto_refresh_timer.stop()
