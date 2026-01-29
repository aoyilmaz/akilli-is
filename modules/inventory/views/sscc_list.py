"""
Akıllı İş - SSCC (Taşıma Birimi) Liste Sayfası
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

from config import COLORS
from config.icons import ICONS
from database.models import TransportUnitType, TransportUnitStatus
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
    ScrollableCardContainer,
)


class SSCCListPage(QWidget):
    """Taşıma birimleri (SSCC) liste sayfası."""

    # Sinyaller
    unit_selected = pyqtSignal(int)
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.units_data = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Taşıma Birimleri (SSCC)",
            icon=ICONS.INVENTORY,
            show_search=True,
            show_refresh=True,
            show_add=True,
            show_export=True,
            add_text="Yeni Palet/Koli",
            search_placeholder="SSCC, barkod veya notlarda ara...",
            parent=self,
        )

        # Filtreleri header'a ekle
        self.type_combo = QComboBox()
        self.type_combo.addItem("Tüm Tipler", None)
        for t in TransportUnitType:
            self.type_combo.addItem(t.value, t)
        self.type_combo.setMinimumWidth(130)
        self.type_combo.setFixedHeight(36)
        self.type_combo.currentIndexChanged.connect(self._do_search)

        self.status_combo = QComboBox()
        self.status_combo.addItem("Tüm Durumlar", None)
        for s in TransportUnitStatus:
            self.status_combo.addItem(s.value, s)
        self.status_combo.setMinimumWidth(120)
        self.status_combo.setFixedHeight(36)
        self.status_combo.currentIndexChanged.connect(self._do_search)

        if self.header.search_input:
            h_layout = self.header.header_layout()
            idx = h_layout.indexOf(self.header.search_input)
            h_layout.insertWidget(idx, QLabel("Tip:"))
            h_layout.insertWidget(idx + 1, self.type_combo)
            h_layout.insertWidget(idx + 2, QLabel("Durum:"))
            h_layout.insertWidget(idx + 3, self.status_combo)

        layout.addWidget(self.header)

        # İstatistik kartları (Scrollable)
        stats_container = ScrollableCardContainer()
        self.stat_cards = {}

        self.stat_cards["total"] = MiniStatCard(
            "Toplam", "0", "info", icon=ICONS.INVENTORY, icon_color="#6366f1"
        )
        self.stat_cards["open"] = MiniStatCard(
            "Açık", "0", "success", icon=ICONS.UNLOCKED, icon_color="#10b981"
        )
        self.stat_cards["closed"] = MiniStatCard(
            "Kapalı", "0", "warning", icon=ICONS.LOCKED, icon_color="#f59e0b"
        )
        self.stat_cards["shipped"] = MiniStatCard(
            "Sevk Edildi", "0", "error", icon=ICONS.TRUCK, icon_color="#ef4444"
        )

        for card in self.stat_cards.values():
            stats_container.add_card(card)
        stats_container.add_stretch()

        layout.addWidget(stats_container)

        # Tablo
        columns = [
            ColumnConfig("sscc", "SSCC Kodu", width=160),
            ColumnConfig("type", "Tip", width=100),
            ColumnConfig("status", "Durum", width=100),
            ColumnConfig("warehouse", "Depo", width=150),
            ColumnConfig("location", "Raf/Konum", width=100),
            ColumnConfig("item_count", "Kalem", width=80),
            ColumnConfig("created_at", "Oluşturulma", width=140),
            ColumnConfig("notes", "Notlar", width=200, stretch=True),
        ]

        self.table = EnhancedTableWidget(
            table_id="sscc_units",
            columns=columns,
            parent=self,
        )
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.table)

        # Footer
        footer_layout = QHBoxLayout()
        self.count_label = QLabel("Toplam: 0 kayıt")
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

    def load_data(self, units: list):
        """Tabloyu verilerle doldur"""
        self.units_data = units
        self.table.setRowCount(len(units))
        visible_cols = self.table.get_visible_columns()

        open_count = closed_count = shipped_count = 0

        for row, unit in enumerate(units):
            self._populate_row(row, unit, visible_cols)

            # İstatistikler
            if unit.status == TransportUnitStatus.ACIK:
                open_count += 1
            elif unit.status == TransportUnitStatus.KAPALI:
                closed_count += 1
            elif unit.status == TransportUnitStatus.SEVK_EDILDI:
                shipped_count += 1

        # İstatistik kartlarını güncelle
        self.stat_cards["total"].update_value(str(len(units)))
        self.stat_cards["open"].update_value(str(open_count))
        self.stat_cards["closed"].update_value(str(closed_count))
        self.stat_cards["shipped"].update_value(str(shipped_count))

        self.count_label.setText(f"Toplam: {len(units)} kayıt")

    def _populate_row(self, row: int, unit, visible_cols: list):
        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "sscc":
                cell = QTableWidgetItem(unit.sscc)
                cell.setData(Qt.ItemDataRole.UserRole, unit.id)
                cell.setForeground(QColor("#818cf8"))
                self.table.setItem(row, col_idx, cell)

            elif col_key == "type":
                self.table.setItem(row, col_idx, QTableWidgetItem(unit.unit_type.value))

            elif col_key == "status":
                status = unit.status
                cell = QTableWidgetItem(status.value)
                if status == TransportUnitStatus.ACIK:
                    cell.setForeground(QColor(COLORS["success"]))
                elif status == TransportUnitStatus.KAPALI:
                    cell.setForeground(QColor(COLORS["warning"]))
                elif status == TransportUnitStatus.SEVK_EDILDI:
                    cell.setForeground(QColor(COLORS["info"]))
                elif status == TransportUnitStatus.IPTAL:
                    cell.setForeground(QColor(COLORS["error"]))
                self.table.setItem(row, col_idx, cell)

            elif col_key == "warehouse":
                wh_text = unit.warehouse.name if unit.warehouse else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(wh_text))

            elif col_key == "location":
                loc_text = unit.location.name if unit.location else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(loc_text))

            elif col_key == "item_count":
                # items ilişkisi varsa
                count = len(unit.items) if unit.items else 0
                cell = QTableWidgetItem(str(count))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col_idx, cell)

            elif col_key == "created_at":
                date_str = (
                    unit.created_date.strftime("%d.%m.%Y %H:%M")
                    if unit.created_date
                    else "-"
                )
                self.table.setItem(row, col_idx, QTableWidgetItem(date_str))

            elif col_key == "notes":
                self.table.setItem(row, col_idx, QTableWidgetItem(unit.notes or ""))

        self.table.setRowHeight(row, 40)

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
            "unit_type": self.type_combo.currentData(),
            "status": self.status_combo.currentData(),
        }

    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        unit_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)

        view_action = QAction("👁 Detay/Düzenle", self)
        view_action.triggered.connect(lambda: self.edit_clicked.emit(unit_id))
        menu.addAction(view_action)

        menu.addSeparator()

        print_action = QAction("🖨 Etiket Yazdır", self)
        # print_action.triggered.connect(...)
        menu.addAction(print_action)

        menu.exec(self.table.viewport().mapToGlobal(position))
