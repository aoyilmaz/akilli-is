"""
Akıllı İş - Alacak Yaşlandırma Raporu
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QTableWidgetItem,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from config.icons import ICONS
from ui.components.stat_cards import MiniStatCard
from ui.components.page_header import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


class ReceivablesAgingPage(QWidget):
    """Alacak yaşlandırma raporu sayfası"""

    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        self.header = PageHeader(
            title="Alacak Yaşlandırma",
            icon=ICONS.CHART,
            show_search=False,
            show_refresh=True,
            show_add=False,
            parent=self,
        )
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        h_layout = self.header.header_layout()
        h_layout.addSpacing(16)
        info = QLabel(
            "Vadesi geçmiş ve açık faturalar müşteri bazında gruplandırılmıştır"
        )
        info.setStyleSheet("color: #888; font-style: italic;")
        h_layout.addWidget(info)
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

        sum_f = QFrame()
        sl = QHBoxLayout(sum_f)
        self.total_label = QLabel("Toplam Alacak: ₺0")
        sl.addWidget(self.total_label)
        sl.addStretch()
        self.customer_count_label = QLabel("0 müşteri")
        sl.addWidget(self.customer_count_label)
        layout.addWidget(sum_f)

        cols = [
            ColumnConfig("risk", "Risk", width=60),
            ColumnConfig("code", "Müşteri Kodu", width=120),
            ColumnConfig("name", "Müşteri Adı", stretch=True),
            ColumnConfig("count", "Fatura Sayısı", width=120),
            ColumnConfig("bal", "Toplam Bakiye", width=150),
            ColumnConfig("days", "En Eski Vade", width=120),
        ]
        self.table = EnhancedTableWidget(
            table_id="report_receivables_aging", columns=cols, parent=self
        )
        layout.addWidget(self.table)

    def load_data(self, data: dict):
        groups = data.get("groups", {})
        for k, card in self.cards.items():
            g = groups.get(k, {})
            card.update_value(f"₺{g.get('total', 0):,.2f}")

        total = data.get("total_receivables", 0)
        self.total_label.setText(f"Toplam Alacak: ₺{total:,.2f}")
        cnt = data.get("total_customers", 0)
        self.customer_count_label.setText(f"{cnt} müşteri")

        all_cus, clrs = [], {
            "0-30": "#10b981",
            "31-60": "#f59e0b",
            "61-90": "#f97316",
            "90+": "#ef4444",
        }
        for gname, gdata in groups.items():
            for c in gdata.get("customers", []):
                c["risk_color"] = clrs.get(gname, "#ffffff")
                c["risk_group"] = gname
                all_cus.append(c)
        all_cus.sort(key=lambda x: x.get("max_days", 0), reverse=True)

        self.table.setRowCount(len(all_cus))
        vcols = self.table.get_visible_columns()
        for row, cus in enumerate(all_cus):
            for c, key in enumerate(vcols):
                if key == "risk":
                    it = QTableWidgetItem("●")
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    it.setForeground(QColor(cus.get("risk_color", "#fff")))
                    self.table.setItem(row, c, it)
                elif key == "code":
                    self.table.setItem(
                        row, c, QTableWidgetItem(cus.get("customer_code", ""))
                    )
                elif key == "name":
                    self.table.setItem(
                        row, c, QTableWidgetItem(cus.get("customer_name", ""))
                    )
                elif key == "count":
                    it = QTableWidgetItem(str(cus.get("invoice_count", 0)))
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.table.setItem(row, c, it)
                elif key == "bal":
                    v = cus.get("total_balance", 0)
                    it = QTableWidgetItem(f"₺{v:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    it.setForeground(QColor(cus.get("risk_color", "#fff")))
                    self.table.setItem(row, c, it)
                elif key == "days":
                    d = cus.get("max_days", 0)
                    it = QTableWidgetItem(f"{d} gün")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    if d > 90:
                        it.setForeground(QColor("#ef4444"))
                    elif d > 60:
                        it.setForeground(QColor("#f97316"))
                    elif d > 30:
                        it.setForeground(QColor("#f59e0b"))
                    self.table.setItem(row, c, it)
