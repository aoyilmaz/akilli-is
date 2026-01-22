"""
Akıllı İş - Araç Liste Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QTableWidgetItem,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.components import (
    BaseListPage,
    ColumnConfig,
    create_view_button,
    create_edit_button,
    create_delete_button,
)


class VehicleListPage(BaseListPage):
    """
    Araç listesi sayfası.
    """

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("plate_no", "Plaka", width=100, stretch=False),
            ColumnConfig("vehicle_type", "Tür", width=100),
            ColumnConfig("brand_model", "Marka / Model", width=180, stretch=True),
            ColumnConfig("capacity_kg", "Kapasite (kg)", width=100),
            ColumnConfig("pallet_capacity", "Palet", width=70),
            ColumnConfig("status", "Durum", width=90),
            ColumnConfig(
                "actions",
                "İşlemler",
                width=120,
                resizable=False,
                movable=False,
                hideable=False,
            ),
        ]

        super().__init__(
            title="Araçlar",
            icon="🚛",
            table_id="vehicles",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Araç",
            search_placeholder="Ara... (plaka, marka, model)",
            parent=parent,
        )

        self.vehicles = []
        self._setup_stat_cards()

    def _setup_stat_cards(self):
        """İstatistik kartlarını oluştur"""
        self.add_stat_card("total", "Toplam", "0", "#6366f1", "📊")
        self.add_stat_card("aktif", "Aktif", "0", "#10b981", "✅")
        self.add_stat_card("bakimda", "Bakımda", "0", "#f59e0b", "🔧")
        self.add_stat_card("pasif", "Pasif", "0", "#ef4444", "⛔")

    def load_data(self, data: list):
        """Veriyi tabloya yükle"""
        self.vehicles = data
        self.table.setRowCount(len(data))

        for row, item in enumerate(data):
            # Plaka
            self.table.setItem(row, 0, QTableWidgetItem(item.get("plate_no", "")))

            # Tür
            self.table.setItem(row, 1, QTableWidgetItem(item.get("vehicle_type", "")))

            # Marka / Model
            brand_model = f"{item.get('brand', '')} {item.get('model', '')}".strip()
            self.table.setItem(row, 2, QTableWidgetItem(brand_model))

            # Kapasite
            capacity = item.get("capacity_kg", 0)
            capacity_str = f"{capacity:,.0f}" if capacity else "-"
            capacity_item = QTableWidgetItem(capacity_str)
            capacity_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, capacity_item)

            # Palet
            pallet = item.get("pallet_capacity", 0)
            pallet_str = str(pallet) if pallet else "-"
            pallet_item = QTableWidgetItem(pallet_str)
            pallet_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, pallet_item)

            # Durum
            status_item = QTableWidgetItem(item.get("status_display", ""))
            status = item.get("status", "")
            if status == "aktif":
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif status == "bakimda":
                status_item.setForeground(Qt.GlobalColor.darkYellow)
            elif status == "pasif":
                status_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 5, status_item)

            # İşlemler
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            vehicle_id = item.get("id")

            view_btn = create_view_button()
            view_btn.clicked.connect(lambda checked, vid=vehicle_id: self.view_clicked.emit(vid))

            edit_btn = create_edit_button()
            edit_btn.clicked.connect(lambda checked, vid=vehicle_id: self.edit_clicked.emit(vid))

            delete_btn = create_delete_button()
            delete_btn.clicked.connect(lambda checked, vid=vehicle_id: self.delete_clicked.emit(vid))

            actions_layout.addWidget(view_btn)
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()

            self.table.setCellWidget(row, 6, actions_widget)

        # İstatistikleri güncelle
        self._update_stats()

    def _update_stats(self):
        """İstatistikleri güncelle"""
        total = len(self.vehicles)
        aktif = sum(1 for v in self.vehicles if v.get("status") == "aktif")
        bakimda = sum(1 for v in self.vehicles if v.get("status") == "bakimda")
        pasif = sum(1 for v in self.vehicles if v.get("status") == "pasif")

        self.update_stat_card("total", str(total))
        self.update_stat_card("aktif", str(aktif))
        self.update_stat_card("bakimda", str(bakimda))
        self.update_stat_card("pasif", str(pasif))
