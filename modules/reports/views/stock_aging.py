"""
Akıllı İş - Stok Yaşlandırma Raporu
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidgetItem,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from config.icons import ICONS
from ui.components.stat_cards import MiniStatCard
from ui.components.page_header import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


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
        self.header = PageHeader(
            title="Stok Yaşlandırma",
            icon=ICONS.TIME,
            show_search=False,
            show_add=False,
            parent=self,
        )
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        h_layout = self.header.header_layout()
        h_layout.addSpacing(16)
        h_layout.addWidget(QLabel("Depo:"))
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.addItem("Tüm Depolar", None)
        self.warehouse_combo.setMinimumWidth(150)
        self.warehouse_combo.setFixedHeight(36)
        h_layout.addWidget(self.warehouse_combo)
        layout.addWidget(self.header)

        c_layout = QHBoxLayout()
        c_layout.setSpacing(16)
        self.cards = {
            "0-30": MiniStatCard("0-30 Gün", "₺0", "success", icon=ICONS.TIME),
            "31-60": MiniStatCard("31-60 Gün", "₺0", "warning", icon=ICONS.TIME),
            "61-90": MiniStatCard("61-90 Gün", "₺0", "error", icon=ICONS.TIME),
            "90+": MiniStatCard("90+ Gün", "₺0", "error", icon=ICONS.CLOSE),
        }
        for card in self.cards.values():
            c_layout.addWidget(card)
        layout.addLayout(c_layout)

        cols = [
            ColumnConfig("group", "Yaş Grubu", width=100),
            ColumnConfig("code", "Stok Kodu", width=120),
            ColumnConfig("name", "Stok Adı", stretch=True),
            ColumnConfig("wh", "Depo", width=120),
            ColumnConfig("qty", "Miktar", width=100),
            ColumnConfig("cost", "Birim Maliyet", width=120),
            ColumnConfig("val", "Toplam Değer", width=120),
            ColumnConfig("days", "Gün", width=80),
            ColumnConfig("last", "Son Giriş", width=110),
        ]
        self.table = EnhancedTableWidget(
            table_id="report_stock_aging", columns=cols, parent=self
        )
        layout.addWidget(self.table)

    def load_data(self, data: dict):
        groups = data.get("groups", {})
        for k, card in self.cards.items():
            g = groups.get(k, {})
            card.update_value(f"₺{g.get('value', 0):,.2f}")

        all_items, clrs = [], {
            "0-30": "#10b981",
            "31-60": "#f59e0b",
            "61-90": "#f97316",
            "90+": "#ef4444",
        }
        for gname, gdata in groups.items():
            for item in gdata.get("items", []):
                item["group"] = gname
                item["color"] = clrs.get(gname, "#ffffff")
                all_items.append(item)
        all_items.sort(key=lambda x: x.get("days_old", 0), reverse=True)

        self.table.setRowCount(len(all_items))
        vcols = self.table.get_visible_columns()
        for r, itm in enumerate(all_items):
            for c, key in enumerate(vcols):
                if key == "group":
                    it = QTableWidgetItem(itm.get("group", ""))
                    it.setForeground(QColor(itm.get("color", "#fff")))
                    self.table.setItem(r, c, it)
                elif key == "code":
                    self.table.setItem(r, c, QTableWidgetItem(itm.get("item_code", "")))
                elif key == "name":
                    self.table.setItem(r, c, QTableWidgetItem(itm.get("item_name", "")))
                elif key == "wh":
                    self.table.setItem(r, c, QTableWidgetItem(itm.get("warehouse", "")))
                elif key == "qty":
                    val = itm.get("quantity", 0)
                    it = QTableWidgetItem(f"{val:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.table.setItem(r, c, it)
                elif key == "cost":
                    val = itm.get("unit_cost", 0)
                    it = QTableWidgetItem(f"₺{val:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.table.setItem(r, c, it)
                elif key == "val":
                    val = itm.get("total_value", 0)
                    it = QTableWidgetItem(f"₺{val:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.table.setItem(r, c, it)
                elif key == "days":
                    d = itm.get("days_old", 0)
                    it = QTableWidgetItem(str(d))
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    if d > 90:
                        it.setForeground(QColor("#ef4444"))
                    self.table.setItem(r, c, it)
                elif key == "last":
                    last = itm.get("last_entry")
                    lst = (
                        last.strftime("%d.%m.%Y")
                        if hasattr(last, "strftime")
                        else (str(last)[:10] if last else "-")
                    )
                    self.table.setItem(r, c, QTableWidgetItem(lst))

    def load_warehouses(self, whs: list):
        self.warehouse_combo.clear()
        self.warehouse_combo.addItem("Tüm Depolar", None)
        for w in whs:
            self.warehouse_combo.addItem(w.name, w.id)

    def get_warehouse_id(self):
        return self.warehouse_combo.currentData()
