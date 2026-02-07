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
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QAction

from config import COLORS
from config.icons import ICONS
from database.models import TransportUnitType, TransportUnitStatus
from ui.components.base_list_page import BaseListPage
from ui.components.enhanced_table import ColumnConfig


class SSCCListPage(BaseListPage):
    """Taşıma birimleri (SSCC) liste sayfası."""

    unit_selected = pyqtSignal(int)
    # add_clicked, edit_clicked, delete_clicked BaseListPage'den geliyor

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("sscc", "SSCC Kodu", width=160),
            ColumnConfig("type", "Tip", width=100, filter_type="enum"),
            ColumnConfig("status", "Durum", width=100, filter_type="enum"),
            ColumnConfig("warehouse", "Depo", width=150),
            ColumnConfig("location", "Raf/Konum", width=100),
            ColumnConfig("item_count", "Kalem", width=80),
            ColumnConfig("created_at", "Oluşturulma", width=140),
            ColumnConfig("notes", "Notlar", width=200, stretch=True),
        ]

        super().__init__(
            title="Taşıma Birimleri (SSCC)",
            icon=ICONS.INVENTORY,
            table_id="sscc_units",
            columns=columns,
            show_add=True,
            show_export=True,
            add_text="Yeni Palet/Koli",
            search_placeholder="SSCC, barkod veya notlarda ara...",
            parent=parent,
        )

        self.units_data = []
        self._setup_extra_ui()

    def _setup_extra_ui(self):
        """Header filtreleri ve footer istatistikleri"""

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
            # Arama kutusunun yanına ekle
            if idx != -1:
                h_layout.insertWidget(idx, QLabel("Tip:"))
                h_layout.insertWidget(idx + 1, self.type_combo)
                h_layout.insertWidget(idx + 2, QLabel("Durum:"))
                h_layout.insertWidget(idx + 3, self.status_combo)

        # Footer İstatistikleri
        self.footer.add_stat("open", "Açık", ICONS.UNLOCKED, "success")
        self.footer.add_stat("closed", "Kapalı", ICONS.LOCKED, "warning")
        self.footer.add_stat("shipped", "Sevk Edildi", ICONS.TRUCK, "error")

        # Context Menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Sinyal bağlantıları (BaseListPage sinyallerini kendi sinyallerimize yönlendirebiliriz gerekirse)
        # Ancak BaseListPage edit_clicked -> int bekler. SSCCListPage de öyle.
        # BaseListPage row double click -> view_clicked. SSCCListPage -> edit_clicked.
        # Bu mapping farkını yönetelim.
        self.view_clicked.connect(self.edit_clicked.emit)

        # Filtre seçenekleri
        self.table.set_filter_options("type", [t.value for t in TransportUnitType])
        self.table.set_filter_options("status", [s.value for s in TransportUnitStatus])

    def _do_search(self):
        """Filtre değiştiğinde"""
        self.refresh_requested.emit()

    def load_data(self, units: list):
        """Tabloyu verilerle doldur"""
        self.units_data = units
        self.table.setRowCount(len(units))

        open_count = closed_count = shipped_count = 0

        self.table.setSortingEnabled(False)
        for row, unit in enumerate(units):
            self._populate_row(row, unit)

            # İstatistikler
            if unit.status == TransportUnitStatus.ACIK:
                open_count += 1
            elif unit.status == TransportUnitStatus.KAPALI:
                closed_count += 1
            elif unit.status == TransportUnitStatus.SEVK_EDILDI:
                shipped_count += 1
        self.table.setSortingEnabled(True)

        # İstatistik kartlarını güncelle
        self.update_count(len(units))
        self.update_stat_card("open", str(open_count))
        self.update_stat_card("closed", str(closed_count))
        self.update_stat_card("shipped", str(shipped_count))

        # Tablo filtrelerini uygula
        self.table.apply_saved_filters()

    def _populate_row(self, row: int, unit):
        # sscc
        cell = QTableWidgetItem(unit.sscc)
        cell.setData(Qt.ItemDataRole.UserRole, unit.id)
        cell.setForeground(QColor("#818cf8"))
        self.table.setItem(row, 0, cell)

        # type
        self.table.setItem(row, 1, QTableWidgetItem(unit.unit_type.value))

        # status
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
        self.table.setItem(row, 2, cell)

        # warehouse
        wh_text = unit.warehouse.name if unit.warehouse else "-"
        self.table.setItem(row, 3, QTableWidgetItem(wh_text))

        # location
        loc_text = unit.location.name if unit.location else "-"
        self.table.setItem(row, 4, QTableWidgetItem(loc_text))

        # item_count
        count = len(unit.items) if unit.items else 0
        cell = QTableWidgetItem(str(count))
        cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 5, cell)

        # created_at
        date_str = (
            unit.created_date.strftime("%d.%m.%Y %H:%M") if unit.created_date else "-"
        )
        self.table.setItem(row, 6, QTableWidgetItem(date_str))

        # notes
        self.table.setItem(row, 7, QTableWidgetItem(unit.notes or ""))

    def get_filters(self) -> dict:
        return {
            "keyword": self.header.get_search_text(),
            "unit_type": self.type_combo.currentData(),
            "status": self.status_combo.currentData(),
        }

    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        unit_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)

        view_action = QAction("Detay/Düzenle", self)
        view_action.triggered.connect(lambda: self.edit_clicked.emit(unit_id))
        menu.addAction(view_action)

        menu.addSeparator()

        print_action = QAction("Etiket Yazdır", self)
        menu.addAction(print_action)

        menu.exec(self.table.viewport().mapToGlobal(position))
