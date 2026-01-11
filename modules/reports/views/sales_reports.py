"""
Akilli Is - Satis Raporlari Sayfasi
"""

from datetime import date, timedelta
from decimal import Decimal
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
    QTabWidget,
    QDateEdit,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor
from ui.components.stat_cards import MiniStatCard

from config.styles import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HOVER, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, ACCENT, SUCCESS, WARNING, ERROR,
    get_table_style, get_tab_style, get_input_style, get_button_style,
)

class SalesReportsPage(QWidget):
    """Satis raporlari sayfasi"""

    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Filtreler
        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)

        filter_layout.addWidget(QLabel("Baslangic:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        filter_layout.addWidget(self.start_date)

        filter_layout.addWidget(QLabel("Bitis:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        filter_layout.addWidget(self.end_date)

        filter_layout.addStretch()

        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        filter_layout.addWidget(refresh_btn)

        layout.addWidget(filter_frame)

        # Ozet kartlar
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.total_sales_card = self._create_card("Toplam Satis", "0.00", SUCCESS)
        cards_layout.addWidget(self.total_sales_card)

        self.invoice_count_card = self._create_card("Fatura Sayisi", "0", ACCENT)
        cards_layout.addWidget(self.invoice_count_card)

        self.customer_count_card = self._create_card("Aktif Musteri", "0", WARNING)
        cards_layout.addWidget(self.customer_count_card)

        self.avg_order_card = self._create_card("Ort. Siparis", "0.00", "#5e3b8e")
        cards_layout.addWidget(self.avg_order_card)

        layout.addLayout(cards_layout)

        # Tab Widget
        tabs = QTabWidget()
        tabs.addTab(self._create_customer_tab(), "Musteri Bazli")
        tabs.addTab(self._create_product_tab(), "Urun Bazli")
        tabs.addTab(self._create_period_tab(), "Donemsel")

        layout.addWidget(tabs)

    def _create_card(self, title: str, value: str, color: str) -> MiniStatCard:
        """Dashboard tarzı istatistik kartı"""
        return MiniStatCard(title, value, color)

    def _create_customer_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 16, 0, 0)

        self.customer_table = QTableWidget()
        self._setup_table(
            self.customer_table,
            [
                ("Musteri Kodu", 120),
                ("Musteri Adi", 250),
                ("Fatura Sayisi", 100),
                ("Toplam Satis", 150),
                ("Son Fatura", 120),
            ],
        )
        layout.addWidget(self.customer_table)

        return widget

    def _create_product_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 16, 0, 0)

        self.product_table = QTableWidget()
        self._setup_table(
            self.product_table,
            [
                ("Urun Kodu", 120),
                ("Urun Adi", 250),
                ("Satis Adedi", 100),
                ("Toplam Ciro", 150),
                ("Islem Sayisi", 100),
            ],
        )
        layout.addWidget(self.product_table)

        return widget

    def _create_period_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 16, 0, 0)

        # Periyod secimi
        period_layout = QHBoxLayout()
        lbl = QLabel("Periyod:")
        period_layout.addWidget(lbl)
        self.period_combo = QComboBox()
        self.period_combo.addItem("Gunluk", "daily")
        self.period_combo.addItem("Haftalik", "weekly")
        self.period_combo.addItem("Aylik", "monthly")
        self.period_combo.setCurrentIndex(2)
        period_layout.addWidget(self.period_combo)
        period_layout.addStretch()
        layout.addLayout(period_layout)

        self.period_table = QTableWidget()
        self._setup_table(
            self.period_table,
            [
                ("Donem", 150),
                ("Fatura Sayisi", 120),
                ("Toplam Satis", 150),
            ],
        )
        layout.addWidget(self.period_table)

        return widget

    def _setup_table(self, table: QTableWidget, columns: list):
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels([c[0] for c in columns])

        header = table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 1:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                table.setColumnWidth(i, width)

        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
    def load_customer_data(self, data: list):
        self.customer_table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.customer_table.setItem(row, 0, QTableWidgetItem(item.get("code", "")))
            self.customer_table.setItem(row, 1, QTableWidgetItem(item.get("name", "")))

            count_item = QTableWidgetItem(str(item.get("invoice_count", 0)))
            count_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.customer_table.setItem(row, 2, count_item)

            amount = item.get("total_amount", 0)
            amount_item = QTableWidgetItem(f"{amount:,.2f}")
            amount_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.customer_table.setItem(row, 3, amount_item)

            last_inv = item.get("last_invoice")
            last_str = last_inv.strftime("%d.%m.%Y") if last_inv else "-"
            self.customer_table.setItem(row, 4, QTableWidgetItem(last_str))

    def load_product_data(self, data: list):
        self.product_table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.product_table.setItem(row, 0, QTableWidgetItem(item.get("code", "")))
            self.product_table.setItem(row, 1, QTableWidgetItem(item.get("name", "")))

            qty = item.get("total_qty", 0)
            qty_item = QTableWidgetItem(f"{qty:,.2f}")
            qty_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.product_table.setItem(row, 2, qty_item)

            amount = item.get("total_amount", 0)
            amount_item = QTableWidgetItem(f"{amount:,.2f}")
            amount_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.product_table.setItem(row, 3, amount_item)

            count_item = QTableWidgetItem(str(item.get("sale_count", 0)))
            count_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.product_table.setItem(row, 4, count_item)

    def load_period_data(self, data: list):
        self.period_table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.period_table.setItem(row, 0, QTableWidgetItem(item.get("period", "")))

            count_item = QTableWidgetItem(str(item.get("invoice_count", 0)))
            count_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.period_table.setItem(row, 1, count_item)

            amount = item.get("total_amount", 0)
            amount_item = QTableWidgetItem(f"{amount:,.2f}")
            amount_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.period_table.setItem(row, 2, amount_item)

    def update_summary(self, total: float, count: int, customers: int, avg: float):
        self._update_card(self.total_sales_card, f"{total:,.2f}")
        self._update_card(self.invoice_count_card, str(count))
        self._update_card(self.customer_count_card, str(customers))
        self._update_card(self.avg_order_card, f"{avg:,.2f}")

    def _update_card(self, card: MiniStatCard, value: str):
        card.update_value(value)

    def get_date_range(self):
        return (self.start_date.date().toPyDate(), self.end_date.date().toPyDate())

    def get_period(self):
        return self.period_combo.currentData()
