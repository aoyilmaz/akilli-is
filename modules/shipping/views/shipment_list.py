"""
Akıllı İş - Sevkiyat Liste Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QTableWidgetItem,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ui.components import (
    BaseListPage,
    ColumnConfig,
    create_view_button,
    create_edit_button,
    create_delete_button,
)


class ShipmentListPage(BaseListPage):
    """
    Sevkiyat listesi sayfası.
    """

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("shipment_no", "Sevkiyat No", width=120, stretch=False),
            ColumnConfig("shipment_date", "Tarih", width=100),
            ColumnConfig("vehicle", "Araç", width=110),
            ColumnConfig("driver", "Sürücü", width=150, stretch=True),
            ColumnConfig("items", "İrsaliye", width=70),
            ColumnConfig("weight", "Ağırlık (kg)", width=100),
            ColumnConfig("status", "Durum", width=100),
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
            title="Sevkiyatlar",
            icon="📦",
            table_id="shipments",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Sevkiyat",
            search_placeholder="Ara... (sevkiyat no, plaka, sürücü)",
            parent=parent,
        )

        self.shipments = []
        self._setup_stat_cards()

    def _setup_stat_cards(self):
        """İstatistik kartlarını oluştur"""
        self.add_stat_card("total", "Toplam", "0", "#6366f1", "📊")
        self.add_stat_card("planlanan", "Planlandı", "0", "#f59e0b", "📋")
        self.add_stat_card("yolda", "Yolda", "0", "#3b82f6", "🚛")
        self.add_stat_card("teslim", "Teslim", "0", "#10b981", "✅")

    def load_data(self, data: list):
        """Veriyi tabloya yükle"""
        self.shipments = data
        self.table.setRowCount(len(data))

        for row, item in enumerate(data):
            # Sevkiyat No
            self.table.setItem(row, 0, QTableWidgetItem(item.get("shipment_no", "")))

            # Tarih
            self.table.setItem(row, 1, QTableWidgetItem(item.get("shipment_date", "")))

            # Araç
            self.table.setItem(row, 2, QTableWidgetItem(item.get("vehicle", "")))

            # Sürücü
            self.table.setItem(row, 3, QTableWidgetItem(item.get("driver", "")))

            # İrsaliye sayısı
            items_count = item.get("total_items", 0)
            items_item = QTableWidgetItem(str(items_count))
            items_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, items_item)

            # Ağırlık
            weight = item.get("total_weight_kg", 0)
            weight_str = f"{weight:,.0f}" if weight else "-"
            weight_item = QTableWidgetItem(weight_str)
            weight_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            # Kapasite aşımı varsa uyarı
            if item.get("is_capacity_exceeded"):
                weight_item.setForeground(QColor("#ef4444"))
                weight_item.setToolTip("Araç kapasitesi aşıldı!")
            self.table.setItem(row, 5, weight_item)

            # Durum
            status_item = QTableWidgetItem(item.get("status_display", ""))
            status = item.get("status", "")
            if status == "planlandi":
                status_item.setForeground(QColor("#f59e0b"))
            elif status == "yukleniyor":
                status_item.setForeground(QColor("#8b5cf6"))
            elif status == "yolda":
                status_item.setForeground(QColor("#3b82f6"))
            elif status == "teslim":
                status_item.setForeground(QColor("#10b981"))
            elif status == "iptal":
                status_item.setForeground(QColor("#ef4444"))
            self.table.setItem(row, 6, status_item)

            # İşlemler
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            shipment_id = item.get("id")

            view_btn = create_view_button()
            view_btn.clicked.connect(lambda checked, sid=shipment_id: self.view_clicked.emit(sid))

            edit_btn = create_edit_button()
            edit_btn.clicked.connect(lambda checked, sid=shipment_id: self.edit_clicked.emit(sid))
            # Teslim edilmiş sevkiyatlar düzenlenemez
            if status in ["teslim", "iptal"]:
                edit_btn.setEnabled(False)

            delete_btn = create_delete_button()
            delete_btn.clicked.connect(lambda checked, sid=shipment_id: self.delete_clicked.emit(sid))
            # Yolda veya teslim edilmiş sevkiyatlar silinemez
            if status in ["yolda", "teslim"]:
                delete_btn.setEnabled(False)

            actions_layout.addWidget(view_btn)
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()

            self.table.setCellWidget(row, 7, actions_widget)

        # İstatistikleri güncelle
        self._update_stats()

    def _update_stats(self):
        """İstatistikleri güncelle"""
        total = len(self.shipments)
        planlanan = sum(1 for s in self.shipments if s.get("status") in ["planlandi", "yukleniyor"])
        yolda = sum(1 for s in self.shipments if s.get("status") == "yolda")
        teslim = sum(1 for s in self.shipments if s.get("status") == "teslim")

        self.update_stat_card("total", str(total))
        self.update_stat_card("planlanan", str(planlanan))
        self.update_stat_card("yolda", str(yolda))
        self.update_stat_card("teslim", str(teslim))
