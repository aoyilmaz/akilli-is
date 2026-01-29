"""
Akıllı İş - Sürücü Liste Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QTableWidgetItem,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from config.icons import ICONS

from ui.components import (
    BaseListPage,
    ColumnConfig,
    create_view_button,
    create_edit_button,
    create_delete_button,
)


class DriverListPage(BaseListPage):
    """
    Sürücü listesi sayfası.
    """

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("code", "Kod", width=80, stretch=False),
            ColumnConfig("name", "Ad Soyad", width=180, stretch=True),
            ColumnConfig("phone", "Telefon", width=120),
            ColumnConfig("license_type", "Ehliyet", width=70),
            ColumnConfig("license_expiry", "Ehliyet Bitiş", width=100),
            ColumnConfig("default_vehicle", "Varsayılan Araç", width=120),
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
            title="Sürücüler",
            icon=ICONS.USER,
            table_id="drivers",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Sürücü",
            search_placeholder="Ara... (kod, ad, telefon)",
            parent=parent,
        )

        self.drivers = []
        self._setup_stat_cards()

    def _setup_stat_cards(self):
        """İstatistik kartlarını oluştur"""
        self.add_stat_card("total", "Toplam", "0", "info", ICONS.USER)
        self.add_stat_card("musait", "Müsait", "0", "success", ICONS.CHECK)
        self.add_stat_card("gorevde", "Görevde", "0", "primary", ICONS.TRUCK)
        self.add_stat_card("expiring", "Belge Dolacak", "0", "error", ICONS.DANGER)

    def load_data(self, data: list):
        """Veriyi tabloya yükle"""
        self.drivers = data
        self.table.setRowCount(len(data))

        for row, item in enumerate(data):
            # Kod
            self.table.setItem(row, 0, QTableWidgetItem(item.get("code", "")))

            # Ad Soyad
            self.table.setItem(row, 1, QTableWidgetItem(item.get("name", "")))

            # Telefon
            self.table.setItem(row, 2, QTableWidgetItem(item.get("phone", "")))

            # Ehliyet tipi
            license_item = QTableWidgetItem(item.get("license_type", ""))
            license_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, license_item)

            # Ehliyet bitiş
            license_expiry = item.get("license_expiry", "")
            expiry_item = QTableWidgetItem(license_expiry)
            if item.get("is_license_expiring"):
                expiry_item.setForeground(QColor("#ef4444"))
                expiry_item.setToolTip("Ehliyet süresi dolmak üzere!")
            self.table.setItem(row, 4, expiry_item)

            # Varsayılan araç
            self.table.setItem(
                row, 5, QTableWidgetItem(item.get("default_vehicle", ""))
            )

            # Durum
            status_item = QTableWidgetItem(item.get("status_display", ""))
            status = item.get("status", "")
            if status == "musait":
                status_item.setForeground(QColor("#10b981"))
            elif status == "gorevde":
                status_item.setForeground(QColor("#3b82f6"))
            elif status == "izinli":
                status_item.setForeground(QColor("#f59e0b"))
            elif status == "pasif":
                status_item.setForeground(QColor("#6b7280"))
            self.table.setItem(row, 6, status_item)

            # İşlemler
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            driver_id = item.get("id")

            view_btn = create_view_button()
            view_btn.clicked.connect(
                lambda checked, did=driver_id: self.view_clicked.emit(did)
            )

            edit_btn = create_edit_button()
            edit_btn.clicked.connect(
                lambda checked, did=driver_id: self.edit_clicked.emit(did)
            )

            delete_btn = create_delete_button()
            delete_btn.clicked.connect(
                lambda checked, did=driver_id: self.delete_clicked.emit(did)
            )

            actions_layout.addWidget(view_btn)
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()

            self.table.setCellWidget(row, 7, actions_widget)

        # İstatistikleri güncelle
        self._update_stats()

    def _update_stats(self):
        """İstatistikleri güncelle"""
        total = len(self.drivers)
        musait = sum(1 for d in self.drivers if d.get("status") == "musait")
        gorevde = sum(1 for d in self.drivers if d.get("status") == "gorevde")
        expiring = sum(
            1
            for d in self.drivers
            if d.get("is_license_expiring") or d.get("is_src_expiring")
        )

        self.update_stat_card("total", str(total))
        self.update_stat_card("musait", str(musait))
        self.update_stat_card("gorevde", str(gorevde))
        self.update_stat_card("expiring", str(expiring))
