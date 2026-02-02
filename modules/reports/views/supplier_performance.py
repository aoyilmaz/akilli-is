"""
Akıllı İş - Tedarikçi Performans Raporu
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidgetItem,
    QProgressBar,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from config.icons import ICONS
from ui.components.stat_cards import MiniStatCard
from ui.components.page_header import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


class SupplierPerformancePage(QWidget):
    """Tedarikçi performans raporu sayfası"""

    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        self.header = PageHeader(
            title="Tedarikçi Performansı",
            icon=ICONS.CHART,
            show_search=False,
            show_add=False,
            parent=self,
        )
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        h_layout = self.header.header_layout()
        h_layout.addSpacing(16)
        info = QLabel("Tedarikçi performansları mal kabul verilerine göre hesaplanır")
        info.setStyleSheet("color: #888; font-style: italic;")
        h_layout.addWidget(info)
        layout.addWidget(self.header)

        c_layout = QHBoxLayout()
        c_layout.setSpacing(16)
        self.cards = {
            "total": MiniStatCard("Toplam Tedarikçi", "0", "info", icon=ICONS.USER),
            "top": MiniStatCard("En İyi Performans", "-", "success", icon=ICONS.CHART),
            "quality": MiniStatCard(
                "Ort. Kalite Puanı", "0%", "warning", icon=ICONS.CHECK
            ),
            "receipts": MiniStatCard(
                "Toplam Mal Kabul", "0", "info", icon=ICONS.INVOICE
            ),
        }
        for card in self.cards.values():
            c_layout.addWidget(card)
        layout.addLayout(c_layout)

        cols = [
            ColumnConfig("code", "Tedarikçi Kodu", width=120),
            ColumnConfig("name", "Tedarikçi Adı", stretch=True),
            ColumnConfig("receipts", "Mal Kabul", width=100),
            ColumnConfig("orders", "Sipariş", width=100),
            ColumnConfig("quality", "Kalite Puanı", width=120),
            ColumnConfig("score", "Puan", width=80),
            ColumnConfig("perf", "Performans", width=180),
        ]
        self.table = EnhancedTableWidget(
            table_id="report_supplier_perf", columns=cols, parent=self
        )
        layout.addWidget(self.table)

    def load_data(self, data: list):
        self.cards["total"].update_value(str(len(data)))
        if data:
            top = data[0]
            self.cards["top"].update_value(top.get("name", "-"))
            avg_q = sum(s.get("quality_rate", 0) for s in data) / len(data)
            self.cards["quality"].update_value(f"{avg_q:.1f}%")
            tot_r = sum(s.get("total_receipts", 0) for s in data)
            self.cards["receipts"].update_value(str(tot_r))

        self.table.setRowCount(len(data))
        vcols = self.table.get_visible_columns()
        for row, s in enumerate(data):
            for c, key in enumerate(vcols):
                if key == "code":
                    self.table.setItem(row, c, QTableWidgetItem(s.get("code", "")))
                elif key == "name":
                    self.table.setItem(row, c, QTableWidgetItem(s.get("name", "")))
                elif key in ["receipts", "orders"]:
                    val = s.get(
                        "total_receipts" if key == "receipts" else "total_orders", 0
                    )
                    it = QTableWidgetItem(str(val))
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.table.setItem(row, c, it)
                elif key == "quality":
                    q = s.get("quality_rate", 0)
                    it = QTableWidgetItem(f"{q:.1f}%")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    if q >= 95:
                        it.setForeground(QColor("#10b981"))
                    elif q < 80:
                        it.setForeground(QColor("#ef4444"))
                    self.table.setItem(row, c, it)
                elif key == "score":
                    sc = s.get("score", 0)
                    it = QTableWidgetItem(f"{sc:.0f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    if sc >= 90:
                        it.setForeground(QColor("#10b981"))
                    elif sc < 70:
                        it.setForeground(QColor("#ef4444"))
                    else:
                        it.setForeground(QColor("#f59e0b"))
                    self.table.setItem(row, c, it)
                elif key == "perf":
                    sc = s.get("score", 0)
                    bar = QProgressBar()
                    bar.setRange(0, 100)
                    bar.setValue(int(sc))
                    bar.setTextVisible(False)
                    bar.setFixedHeight(12)
                    clr = (
                        "#10b981"
                        if sc >= 90
                        else ("#f59e0b" if sc >= 70 else "#ef4444")
                    )
                    bar.setStyleSheet(
                        f"QProgressBar::chunk {{ background-color: {clr}; border-radius: 6px; }} QProgressBar {{ background-color: #333; border: none; border-radius: 6px; }}"
                    )
                    w = QWidget()
                    bl = QHBoxLayout(w)
                    bl.setContentsMargins(4, 4, 4, 4)
                    bl.addWidget(bar)
                    self.table.setCellWidget(row, c, w)
