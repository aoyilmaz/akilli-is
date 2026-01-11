"""
Akıllı İş - Stok Yaşlandırma Raporu
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from ui.components.stat_cards import MiniStatCard

from config.styles import (
    BG_SECONDARY,
    BG_TERTIARY,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    ACCENT,
    SUCCESS,
    WARNING,
    ERROR,
    get_table_style,
    get_button_style,
    get_input_style,
)

class StockAgingPage(QWidget):
    """Stok yaşlandırma raporu sayfası"""

    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Filtre
        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)

        lbl = QLabel("Depo:")
        filter_layout.addWidget(lbl)
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.addItem("Tüm Depolar", None)
        self.warehouse_combo.setMinimumWidth(150)
        filter_layout.addWidget(self.warehouse_combo)

        filter_layout.addStretch()

        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        filter_layout.addWidget(refresh_btn)

        layout.addWidget(filter_frame)

        # Yaşlandırma kartları
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.fresh_card = self._create_card("0-30 Gün", "₺0", SUCCESS, "Yeni Stok")
        cards_layout.addWidget(self.fresh_card)

        self.normal_card = self._create_card("31-60 Gün", "₺0", WARNING, "Normal")
        cards_layout.addWidget(self.normal_card)

        self.slow_card = self._create_card(
            "61-90 Gün", "₺0", "#f97316", "Yavaş Hareket"
        )
        cards_layout.addWidget(self.slow_card)

        self.dead_card = self._create_card(
            "90+ Gün", "₺0", ERROR, "Ölü Stok Riski"
        )
        cards_layout.addWidget(self.dead_card)

        layout.addLayout(cards_layout)

        # Tablo
        self.table = QTableWidget()
        self._setup_table(
            self.table,
            [
                ("Yaş Grubu", 100),
                ("Stok Kodu", 100),
                ("Stok Adı", 200),
                ("Depo", 120),
                ("Miktar", 80),
                ("Birim Maliyet", 110),
                ("Toplam Değer", 120),
                ("Gün Sayısı", 80),
                ("Son Giriş", 100),
            ],
        )
        layout.addWidget(self.table)

    def _create_card(self, title: str, value: str, color: str, subtitle: str) -> MiniStatCard:
        """Dashboard tarzı istatistik kartı"""
        return MiniStatCard(title, value, color)

    def _setup_table(self, table: QTableWidget, columns: list):
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels([c[0] for c in columns])

        header = table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 2:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                table.setColumnWidth(i, width)

        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
    def load_data(self, data: dict):
        groups = data.get("groups", {})

        # Kartları güncelle
        self._update_group_card(self.fresh_card, groups.get("0-30", {}))
        self._update_group_card(self.normal_card, groups.get("31-60", {}))
        self._update_group_card(self.slow_card, groups.get("61-90", {}))
        self._update_group_card(self.dead_card, groups.get("90+", {}))

        # Tüm ürünleri tabloya ekle
        all_items = []
        group_colors = {
            "0-30": SUCCESS,
            "31-60": WARNING,
            "61-90": "#f97316",
            "90+": ERROR,
        }

        for group_name, group_data in groups.items():
            for item in group_data.get("items", []):
                item["group"] = group_name
                item["group_color"] = group_colors.get(group_name, "#ffffff")
                all_items.append(item)

        # Gün sayısına göre sırala (en eski en üstte)
        all_items.sort(key=lambda x: x.get("days_old", 0), reverse=True)

        self.table.setRowCount(len(all_items))
        for row, item in enumerate(all_items):
            group_item = QTableWidgetItem(item.get("group", ""))
            group_item.setForeground(QColor(item.get("group_color", "#fff")))
            self.table.setItem(row, 0, group_item)

            self.table.setItem(row, 1, QTableWidgetItem(item.get("item_code", "")))
            self.table.setItem(row, 2, QTableWidgetItem(item.get("item_name", "")))
            self.table.setItem(row, 3, QTableWidgetItem(item.get("warehouse", "")))

            qty = item.get("quantity", 0)
            qty_item = QTableWidgetItem(f"{qty:,.2f}")
            qty_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 4, qty_item)

            cost = item.get("unit_cost", 0)
            cost_item = QTableWidgetItem(f"₺{cost:,.2f}")
            cost_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 5, cost_item)

            total = item.get("total_value", 0)
            total_item = QTableWidgetItem(f"₺{total:,.2f}")
            total_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 6, total_item)

            days = item.get("days_old", 0)
            days_item = QTableWidgetItem(str(days))
            days_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            if days > 90:
                days_item.setForeground(QColor(ERROR))
            self.table.setItem(row, 7, days_item)

            last_entry = item.get("last_entry")
            if last_entry:
                if hasattr(last_entry, "strftime"):
                    last_str = last_entry.strftime("%d.%m.%Y")
                else:
                    last_str = str(last_entry)[:10]
            else:
                last_str = "-"
            self.table.setItem(row, 8, QTableWidgetItem(last_str))

    def _update_group_card(self, card: QFrame, group_data: dict):
        value = group_data.get("value", 0)
        count = group_data.get("count", 0)

        value_label = card.findChild(QLabel, "value")
        if value_label:
            value_label.setText(f"₺{value:,.2f}")

        count_label = card.findChild(QLabel, "count")
        if count_label:
            count_label.setText(f"{count} ürün")

    def load_warehouses(self, warehouses: list):
        self.warehouse_combo.clear()
        self.warehouse_combo.addItem("Tüm Depolar", None)
        for wh in warehouses:
            self.warehouse_combo.addItem(wh.name, wh.id)

    def get_warehouse_id(self):
        return self.warehouse_combo.currentData()
