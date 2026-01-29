"""
Akıllı İş - Üretim Performans (OEE) Raporu
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QTableWidgetItem,
    QDateEdit,
    QProgressBar,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor
import qtawesome as qta

from config.icons import ICONS
from ui.components.stat_cards import MiniStatCard
from ui.components.page_header import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


class ProductionOEEPage(QWidget):
    """Üretim performans (OEE) raporu sayfası"""

    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        self.header = PageHeader(
            title="Üretim OEE Raporu",
            icon=ICONS.CHART,
            show_search=False,
            show_refresh=True,
            show_add=False,
            parent=self,
        )
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        h_layout = self.header.header_layout()
        h_layout.addSpacing(16)
        h_layout.addWidget(QLabel("Başlangıç:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setFixedHeight(36)
        h_layout.addWidget(self.start_date)
        h_layout.addSpacing(8)
        h_layout.addWidget(QLabel("Bitiş:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setFixedHeight(36)
        h_layout.addWidget(self.end_date)
        layout.addWidget(self.header)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(16)
        self.oee_card = self._create_oee_card()
        top_layout.addWidget(self.oee_card, 2)
        comp_layout = QVBoxLayout()
        comp_layout.setSpacing(8)
        self.bars = {
            "avail": self._create_metric_bar("Kullanılabilirlik", "#10b981"),
            "perf": self._create_metric_bar("Performans", "#3b82f6"),
            "qual": self._create_metric_bar("Kalite", "#f59e0b"),
        }
        for b in self.bars.values():
            comp_layout.addWidget(b)
        top_layout.addLayout(comp_layout, 3)
        layout.addLayout(top_layout)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        self.mini_cards = {
            "orders": MiniStatCard("Toplam İş Emri", "0", "info", icon=ICONS.INVOICE),
            "on_time": MiniStatCard("Zamanında", "0", "success", icon=ICONS.TIME),
            "planned": MiniStatCard("Plan. Üretim", "0", "info", icon=ICONS.LIST),
            "actual": MiniStatCard("Gerçek Üretim", "0", "success", icon=ICONS.CHART),
        }
        for card in self.mini_cards.values():
            stats_layout.addWidget(card)
        layout.addLayout(stats_layout)

        cols = [
            ColumnConfig("wo", "İş Emri No", width=120),
            ColumnConfig("item", "Ürün", stretch=True),
            ColumnConfig("planned", "Planlanan", width=100),
            ColumnConfig("actual", "Gerçekleşen", width=100),
            ColumnConfig("perf", "Performans", width=120),
        ]
        self.table = EnhancedTableWidget(
            table_id="report_oee_details", columns=cols, parent=self
        )
        layout.addWidget(self.table)

    def _create_oee_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            "background-color: #1e1e1e; border: 1px solid #333; border-radius: 12px;"
        )
        l = QVBoxLayout(card)
        l.setContentsMargins(20, 20, 20, 20)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t = QLabel("OEE (Overall Equipment Effectiveness)")
        t.setStyleSheet("color: #999; font-size: 14px;")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(t)
        self.oee_value = QLabel("0%")
        self.oee_value.setStyleSheet(
            "color: #10b981; font-size: 48px; font-weight: bold; margin: 10px 0;"
        )
        self.oee_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.oee_value)
        f = QLabel("Kullanılabilirlik × Performans × Kalite")
        f.setStyleSheet("color: #666; font-size: 12px; font-style: italic;")
        f.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(f)
        return card

    def _create_metric_bar(self, title: str, color: str) -> QFrame:
        f = QFrame()
        f.setStyleSheet(
            "background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px;"
        )
        l = QVBoxLayout(f)
        l.setContentsMargins(12, 10, 12, 10)
        l.setSpacing(6)
        hl = QHBoxLayout()
        lbl = QLabel(title)
        lbl.setStyleSheet("color: #ccc; font-weight: bold;")
        hl.addWidget(lbl)
        val = QLabel("0%")
        val.setObjectName("val")
        val.setStyleSheet(f"color: {color}; font-weight: bold;")
        hl.addWidget(val)
        l.addLayout(hl)
        bar = QProgressBar()
        bar.setObjectName("bar")
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        bar.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color}; border-radius: 3px; }} QProgressBar {{ background-color: #333; border: none; border-radius: 3px; }}"
        )
        l.addWidget(bar)
        return f

    def load_data(self, data: dict):
        oee = data.get("oee", 0)
        self.oee_value.setText(f"{oee}%")
        self.oee_value.setStyleSheet(
            f"color: {'#10b981' if oee >= 85 else ('#f59e0b' if oee >= 60 else '#ef4444')}; font-size: 48px; font-weight: bold;"
        )
        self._update_bar(self.bars["avail"], data.get("availability", 0))
        self._update_bar(self.bars["perf"], data.get("performance", 0))
        self._update_bar(self.bars["qual"], data.get("quality", 0))

        self.mini_cards["orders"].update_value(str(data.get("total_orders", 0)))
        self.mini_cards["on_time"].update_value(str(data.get("on_time_count", 0)))
        self.mini_cards["planned"].update_value(f"{data.get('total_planned', 0):,.0f}")
        self.mini_cards["actual"].update_value(f"{data.get('total_actual', 0):,.0f}")

        details = data.get("details", [])
        self.table.setRowCount(len(details))
        vcols = self.table.get_visible_columns()
        for r, itm in enumerate(details):
            for c, key in enumerate(vcols):
                if key == "wo":
                    self.table.setItem(
                        r, c, QTableWidgetItem(itm.get("work_order_no", ""))
                    )
                elif key == "item":
                    self.table.setItem(r, c, QTableWidgetItem(itm.get("item_name", "")))
                elif key == "planned":
                    v = itm.get("planned_qty", 0)
                    it = QTableWidgetItem(f"{v:,.0f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.table.setItem(r, c, it)
                elif key == "actual":
                    v = itm.get("actual_qty", 0)
                    it = QTableWidgetItem(f"{v:,.0f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.table.setItem(r, c, it)
                elif key == "perf":
                    p = itm.get("performance", 0)
                    it = QTableWidgetItem(f"{p:.1f}%")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    if p >= 100:
                        it.setForeground(QColor("#10b981"))
                    elif p < 80:
                        it.setForeground(QColor("#ef4444"))
                    self.table.setItem(r, c, it)

    def _update_bar(self, f: QFrame, v: float):
        vlbl = f.findChild(QLabel, "val")
        if vlbl:
            vlbl.setText(f"{v:.1f}%")
        bar = f.findChild(QProgressBar, "bar")
        if bar:
            bar.setValue(int(v))

    def get_date_range(self):
        return (self.start_date.date().toPyDate(), self.end_date.date().toPyDate())
