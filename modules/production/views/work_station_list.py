"""
Akıllı İş - İş İstasyonları Liste Sayfası
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

from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
)


class WorkStationListPage(QWidget):
    """İş istasyonları listesi."""

    # Sinyaller
    new_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    copy_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    TYPE_DISPLAY = {
        "machine": ("⚙️ Makine", "#3b82f6"),
        "workstation": ("🔧 İş İstasyonu", "#10b981"),
        "assembly": ("🔩 Montaj Hattı", "#f59e0b"),
        "manual": ("✋ Manuel", "#8b5cf6"),
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
            title="İş İstasyonları",
            icon="🏭",
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni İstasyon",
            search_placeholder="İstasyon ara...",
            parent=self,
        )
        layout.addWidget(self.header)

        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.stat_cards = {}
        self.stat_cards["total"] = MiniStatCard("🏭 Toplam", "0", "#6366f1")
        self.stat_cards["machine"] = MiniStatCard("⚙️ Makine", "0", "#3b82f6")
        self.stat_cards["workstation"] = MiniStatCard("🔧 İş İstasyonu", "0", "#10b981")
        self.stat_cards["assembly"] = MiniStatCard("🔩 Montaj Hattı", "0", "#f59e0b")

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        columns = [
            ColumnConfig("code", "Kod", width=100),
            ColumnConfig("name", "İstasyon Adı", width=200, stretch=True),
            ColumnConfig("station_type", "Tür", width=120),
            ColumnConfig("capacity_per_hour", "Kapasite/Saat", width=110),
            ColumnConfig("efficiency_rate", "Verimlilik", width=100),
            ColumnConfig("hourly_rate", "Saatlik Maliyet", width=120),
            ColumnConfig("location", "Konum", width=150),
            ColumnConfig("is_active", "Durum", width=100),
        ]

        self.table = EnhancedTableWidget(
            table_id="work_station_list",
            columns=columns,
            parent=self,
        )
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.table)

        # Alt bilgi
        self.count_label = QLabel("Toplam: 0 istasyon")
        layout.addWidget(self.count_label)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.new_clicked.emit)
        self.header.search_changed.connect(self._on_search)
        self.table.row_double_clicked.connect(self.edit_clicked.emit)

    def load_data(self, stations: list):
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
        self.stat_cards["total"].update_value(str(len(stations)))
        self.stat_cards["machine"].update_value(str(machine_count))
        self.stat_cards["workstation"].update_value(str(workstation_count))
        self.stat_cards["assembly"].update_value(str(assembly_count))

        self.count_label.setText(f"Toplam: {len(stations)} istasyon")

    def _populate_row(self, row: int, station: dict, visible_cols: list):
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
                text = "✅ Aktif" if is_active else "❌ Pasif"
                color = "#10b981" if is_active else "#ef4444"
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color))
                self.table.setItem(row, col_idx, item)

        self.table.setRowHeight(row, 48)

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

        station_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)

        edit_action = QAction("✏️ Düzenle", self)
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(station_id))
        menu.addAction(edit_action)

        copy_action = QAction("📋 Kopyala", self)
        copy_action.triggered.connect(lambda: self.copy_clicked.emit(station_id))
        menu.addAction(copy_action)

        menu.addSeparator()

        delete_action = QAction("🗑 Sil", self)
        delete_action.triggered.connect(lambda: self._confirm_delete(station_id))
        menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _confirm_delete(self, station_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu iş istasyonunu silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(station_id)
