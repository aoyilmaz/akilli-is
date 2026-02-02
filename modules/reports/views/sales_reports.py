"""
Akıllı İş - Satış Raporları Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidgetItem,
    QTabWidget,
    QDateEdit,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate

from config.icons import ICONS
from ui.components.stat_cards import MiniStatCard
from ui.components.page_header import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


class SalesReportsPage(QWidget):
    """Satış raporları sayfası"""

    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        self.header = PageHeader(
            title="Satış Raporları",
            icon=ICONS.CHART,
            show_search=False,
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

        c_layout = QHBoxLayout()
        c_layout.setSpacing(12)
        self.cards = {
            "val": MiniStatCard("Toplam Satış", "₺0,00", "success", icon=ICONS.MONEY),
            "cnt": MiniStatCard("Fatura Sayısı", "0", "info", icon=ICONS.INVOICE),
            "cus": MiniStatCard("Aktif Müşteri", "0", "warning", icon=ICONS.USER),
            "avg": MiniStatCard("Ort. Sipariş", "₺0,00", "info", icon=ICONS.MONEY),
        }
        for card in self.cards.values():
            c_layout.addWidget(card)
        layout.addLayout(c_layout)

        self.tabs = QTabWidget()
        self._setup_customer_tab()
        self._setup_product_tab()
        self._setup_period_tab()
        layout.addWidget(self.tabs)

    def _setup_customer_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(0, 16, 0, 0)
        cols = [
            ColumnConfig("code", "Müşteri Kodu", width=120),
            ColumnConfig("name", "Müşteri Adı", stretch=True),
            ColumnConfig("count", "Fatura Sayısı", width=120),
            ColumnConfig("val", "Toplam Satış", width=150),
            ColumnConfig("last", "Son Fatura", width=120),
        ]
        self.customer_table = EnhancedTableWidget(
            table_id="report_sales_customer", columns=cols, parent=tab
        )
        l.addWidget(self.customer_table)
        self.tabs.addTab(tab, "Müşteri Bazlı")

    def _setup_product_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(0, 16, 0, 0)
        cols = [
            ColumnConfig("code", "Ürün Kodu", width=120),
            ColumnConfig("name", "Ürün Adı", stretch=True),
            ColumnConfig("qty", "Satış Adedi", width=120),
            ColumnConfig("val", "Toplam Ciro", width=150),
            ColumnConfig("cnt", "İşlem Sayısı", width=120),
        ]
        self.product_table = EnhancedTableWidget(
            table_id="report_sales_product", columns=cols, parent=tab
        )
        l.addWidget(self.product_table)
        self.tabs.addTab(tab, "Ürün Bazlı")

    def _setup_period_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(0, 16, 0, 0)
        pl = QHBoxLayout()
        pl.addWidget(QLabel("Periyot:"))
        self.period_combo = QComboBox()
        for lbl, val in [
            ("Günlük", "daily"),
            ("Haftalık", "weekly"),
            ("Aylık", "monthly"),
        ]:
            self.period_combo.addItem(lbl, val)
        self.period_combo.setCurrentIndex(2)
        pl.addWidget(self.period_combo)
        pl.addStretch()
        l.addLayout(pl)
        cols = [
            ColumnConfig("period", "Dönem", stretch=True),
            ColumnConfig("cnt", "Fatura Sayısı", width=150),
            ColumnConfig("val", "Toplam Satış", width=180),
        ]
        self.period_table = EnhancedTableWidget(
            table_id="report_sales_period", columns=cols, parent=tab
        )
        l.addWidget(self.period_table)
        self.tabs.addTab(tab, "Dönemsel")

    def load_customer_data(self, data: list):
        self.customer_table.setRowCount(len(data))
        vcols = self.customer_table.get_visible_columns()
        for r, itm in enumerate(data):
            for c, key in enumerate(vcols):
                if key == "code":
                    self.customer_table.setItem(
                        r, c, QTableWidgetItem(itm.get("code", ""))
                    )
                elif key == "name":
                    self.customer_table.setItem(
                        r, c, QTableWidgetItem(itm.get("name", ""))
                    )
                elif key == "count":
                    it = QTableWidgetItem(str(itm.get("invoice_count", 0)))
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.customer_table.setItem(r, c, it)
                elif key == "val":
                    it = QTableWidgetItem(f"₺{itm.get('total_amount', 0):,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.customer_table.setItem(r, c, it)
                elif key == "last":
                    last = itm.get("last_invoice")
                    self.customer_table.setItem(
                        r,
                        c,
                        QTableWidgetItem(last.strftime("%d.%m.%Y") if last else "-"),
                    )

    def load_product_data(self, data: list):
        self.product_table.setRowCount(len(data))
        vcols = self.product_table.get_visible_columns()
        for r, itm in enumerate(data):
            for c, key in enumerate(vcols):
                if key == "code":
                    self.product_table.setItem(
                        r, c, QTableWidgetItem(itm.get("code", ""))
                    )
                elif key == "name":
                    self.product_table.setItem(
                        r, c, QTableWidgetItem(itm.get("name", ""))
                    )
                elif key == "qty":
                    it = QTableWidgetItem(f"{itm.get('total_qty', 0):,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.table.setItem(r, c, it)
                elif key == "val":
                    it = QTableWidgetItem(f"₺{itm.get('total_amount', 0):,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.table.setItem(r, c, it)
                elif key == "cnt":
                    it = QTableWidgetItem(str(itm.get("sale_count", 0)))
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.table.setItem(r, c, it)

    def load_period_data(self, data: list):
        self.period_table.setRowCount(len(data))
        vcols = self.period_table.get_visible_columns()
        for r, itm in enumerate(data):
            for c, key in enumerate(vcols):
                if key == "period":
                    self.period_table.setItem(
                        r, c, QTableWidgetItem(itm.get("period", ""))
                    )
                elif key == "cnt":
                    it = QTableWidgetItem(str(itm.get("invoice_count", 0)))
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.period_table.setItem(r, c, it)
                elif key == "val":
                    it = QTableWidgetItem(f"₺{itm.get('total_amount', 0):,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.period_table.setItem(r, c, it)

    def update_summary(self, total: float, count: int, customers: int, avg: float):
        self.cards["val"].update_value(f"₺{total:,.2f}")
        self.cards["cnt"].update_value(str(count))
        self.cards["cus"].update_value(str(customers))
        self.cards["avg"].update_value(f"₺{avg:,.2f}")

    def get_date_range(self):
        return (self.start_date.date().toPyDate(), self.end_date.date().toPyDate())

    def get_period(self):
        return self.period_combo.currentData()
