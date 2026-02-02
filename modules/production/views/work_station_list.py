"""
Akıllı İş - İş İstasyonları Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from PyQt6.QtWidgets import (
    QTableWidgetItem,
    QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction
import qtawesome as qta

from config.icons import ICONS
from config.themes import get_theme
from ui.components import (
    BaseListPage,
    ColumnConfig,
)


class WorkStationListPage(BaseListPage):
    """
    İş istasyonları listesi sayfası.
    BaseListPage kullanarak Excel tipi sütun filtreleme destekler.
    """

    # Ek sinyaller
    new_clicked = pyqtSignal()
    copy_clicked = pyqtSignal(int)

    TYPE_DISPLAY = {
        "machine": ("Makine", "#3b82f6"),
        "workstation": ("İş İstasyonu", "#10b981"),
        "assembly": ("Montaj Hattı", "#f59e0b"),
        "manual": ("Manuel", "#8b5cf6"),
    }

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("code", "Kod", width=100),
            ColumnConfig("name", "İstasyon Adı", width=200, stretch=True),
            ColumnConfig("station_type", "Tür", width=120, filter_type="enum"),
            ColumnConfig(
                "capacity_per_hour", "Kapasite/Saat", width=110, filter_type="number"
            ),
            ColumnConfig(
                "efficiency_rate", "Verimlilik", width=100, filter_type="number"
            ),
            ColumnConfig(
                "hourly_rate", "Saatlik Maliyet", width=120, filter_type="number"
            ),
            ColumnConfig("location", "Konum", width=150),
            ColumnConfig("is_active", "Durum", width=100, filter_type="enum"),
        ]

        super().__init__(
            title="İş İstasyonları",
            icon=ICONS.PRODUCTION,
            table_id="work_station_list",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_add=True,
            add_text="Yeni İstasyon",
            search_placeholder="İstasyon ara...",
            parent=parent,
        )

        self.stations = []
        self._setup_stat_cards()

        # Context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # new_clicked için add_clicked bağla
        self.add_clicked.connect(self.new_clicked.emit)

    def _setup_stat_cards(self):
        """İstatistik kartlarını oluştur"""
        self.add_stat_card("total", "Toplam", "0", "info", ICONS.PRODUCTION)
        self.add_stat_card("machine", "Makine", "0", "primary", ICONS.TYPE_SEMI)
        self.add_stat_card("workstation", "İş İstasyonu", "0", "success", ICONS.FIX)
        self.add_stat_card("assembly", "Montaj Hattı", "0", "warning", ICONS.PRODUCTION)

    def load_data(self, stations: list):
        """Verileri yükle"""
        self.stations = stations
        self.table.setRowCount(len(stations))
        visible_cols = self.table.get_visible_columns()

        machine_count = workstation_count = assembly_count = 0

        for row, station in enumerate(stations):
            self._populate_row(row, station, visible_cols)

            station_type = station.get("station_type", "machine")
            if station_type == "machine":
                machine_count += 1
            elif station_type == "workstation":
                workstation_count += 1
            elif station_type == "assembly":
                assembly_count += 1

        # Kartları güncelle
        self.update_stat_card("total", str(len(stations)))
        self.update_stat_card("machine", str(machine_count))
        self.update_stat_card("workstation", str(workstation_count))
        self.update_stat_card("assembly", str(assembly_count))

        self.update_count(len(stations), "istasyon")

    def _populate_row(self, row: int, station: dict, visible_cols: list):
        """Tek satırı doldur"""
        station_id = station.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "code":
                item = QTableWidgetItem(station.get("code", ""))
                item.setData(Qt.ItemDataRole.UserRole, station_id)
                item.setForeground(QColor("#818cf8"))
                self.table.setItem(row, col_idx, item)

            elif col_key == "name":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(station.get("name", ""))
                )

            elif col_key == "station_type":
                stype = station.get("station_type", "machine")
                text, color = self.TYPE_DISPLAY.get(stype, ("?", "#ffffff"))
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color))
                self.table.setItem(row, col_idx, item)

            elif col_key == "capacity_per_hour":
                capacity = station.get("capacity_per_hour", 0)
                item = QTableWidgetItem(f"{capacity:,.0f}" if capacity else "-")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col_idx, item)

            elif col_key == "efficiency_rate":
                efficiency = station.get("efficiency_rate", 100)
                item = QTableWidgetItem(f"%{efficiency:.0f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if efficiency >= 90:
                    item.setForeground(QColor("#10b981"))
                elif efficiency >= 70:
                    item.setForeground(QColor("#f59e0b"))
                else:
                    item.setForeground(QColor("#ef4444"))
                self.table.setItem(row, col_idx, item)

            elif col_key == "hourly_rate":
                rate = station.get("hourly_rate", 0)
                item = QTableWidgetItem(f"₺{rate:,.2f}")
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, item)

            elif col_key == "location":
                loc = station.get("location", "") or station.get("warehouse_name", "")
                self.table.setItem(row, col_idx, QTableWidgetItem(loc or "-"))

            elif col_key == "is_active":
                is_active = station.get("is_active", True)
                t = get_theme()
                item = QTableWidgetItem()
                if is_active:
                    item.setText("Aktif")
                    item.setIcon(
                        qta.icon(ICONS.STATUS_ICONS["active"], color=t.success)
                    )
                    item.setForeground(QColor(t.success))
                else:
                    item.setText("Pasif")
                    item.setIcon(
                        qta.icon(ICONS.STATUS_ICONS["passive"], color=t.text_muted)
                    )
                    item.setForeground(QColor(t.text_muted))
                self.table.setItem(row, col_idx, item)

    def _show_context_menu(self, position):
        """Context menu göster"""
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        station_item = self.table.item(row, 0)
        if not station_item:
            return

        station_id = station_item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)

        edit_action = QAction("Düzenle", self)
        edit_action.setIcon(qta.icon(ICONS.EDIT, color="#cccccc"))
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(station_id))
        menu.addAction(edit_action)

        copy_action = QAction("Kopyala", self)
        copy_action.setIcon(qta.icon(ICONS.COPY, color="#cccccc"))
        copy_action.triggered.connect(lambda: self.copy_clicked.emit(station_id))
        menu.addAction(copy_action)

        menu.addSeparator()

        delete_action = QAction("Sil", self)
        delete_action.setIcon(qta.icon(ICONS.DELETE, color="#ef4444"))
        delete_action.triggered.connect(lambda: self._confirm_delete(station_id))
        menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _confirm_delete(self, station_id: int):
        """Silme onayı"""
        if self.confirm_delete("iş istasyonu"):
            self.delete_clicked.emit(station_id)
