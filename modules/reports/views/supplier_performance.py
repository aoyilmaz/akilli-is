"""
Akıllı İş - Tedarikçi Performans Raporu
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
    QProgressBar,
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
)

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

        # Başlık
        header_layout = QHBoxLayout()

        info = QLabel(
            "Tedarikçi performansları mal kabul verilerine göre hesaplanır"
        )
        header_layout.addWidget(info)

        header_layout.addStretch()

        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Özet kartlar
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.total_suppliers_card = self._create_card(
            "Toplam Tedarikçi", "0", ACCENT
        )
        cards_layout.addWidget(self.total_suppliers_card)

        self.top_performer_card = self._create_card(
            "En İyi Performans", "-", SUCCESS
        )
        cards_layout.addWidget(self.top_performer_card)

        self.avg_quality_card = self._create_card(
            "Ort. Kalite Puanı", "0%", WARNING
        )
        cards_layout.addWidget(self.avg_quality_card)

        self.total_receipts_card = self._create_card(
            "Toplam Mal Kabul", "0", "#8b5cf6"
        )
        cards_layout.addWidget(self.total_receipts_card)

        layout.addLayout(cards_layout)

        # Performans tablosu
        self.table = QTableWidget()
        self._setup_table(
            self.table,
            [
                ("Tedarikçi Kodu", 100),
                ("Tedarikçi Adı", 200),
                ("Mal Kabul", 90),
                ("Sipariş", 80),
                ("Kalite Puanı", 120),
                ("Puan", 80),
                ("Performans", 150),
            ],
        )
        layout.addWidget(self.table)

    def _create_card(self, title: str, value: str, color: str) -> MiniStatCard:
        """Dashboard tarzı istatistik kartı"""
        return MiniStatCard(title, value, color)

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
    def load_data(self, data: list):
        # Özet kartları güncelle
        total = len(data)
        self._update_card(self.total_suppliers_card, str(total))

        if data:
            top = data[0]  # Puana göre sıralı
            self._update_card(self.top_performer_card, top.get("name", "-"))

            avg_quality = (
                sum(s.get("quality_rate", 0) for s in data) / len(data) if data else 0
            )
            self._update_card(self.avg_quality_card, f"{avg_quality:.1f}%")

            total_receipts = sum(s.get("total_receipts", 0) for s in data)
            self._update_card(self.total_receipts_card, str(total_receipts))

        # Tabloyu doldur
        self.table.setRowCount(len(data))

        for row, supplier in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(supplier.get("code", "")))
            self.table.setItem(row, 1, QTableWidgetItem(supplier.get("name", "")))

            receipts = supplier.get("total_receipts", 0)
            receipts_item = QTableWidgetItem(str(receipts))
            receipts_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 2, receipts_item)

            orders = supplier.get("total_orders", 0)
            orders_item = QTableWidgetItem(str(orders))
            orders_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 3, orders_item)

            quality = supplier.get("quality_rate", 0)
            quality_item = QTableWidgetItem(f"{quality:.1f}%")
            quality_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            if quality >= 95:
                quality_item.setForeground(QColor(SUCCESS))
            elif quality < 80:
                quality_item.setForeground(QColor(ERROR))
            self.table.setItem(row, 4, quality_item)

            score = supplier.get("score", 0)
            score_item = QTableWidgetItem(f"{score:.0f}")
            score_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            if score >= 90:
                score_item.setForeground(QColor(SUCCESS))
            elif score < 70:
                score_item.setForeground(QColor(ERROR))
            else:
                score_item.setForeground(QColor(WARNING))
            self.table.setItem(row, 5, score_item)

            # Progress bar widget
            bar_widget = QWidget()
            bar_layout = QHBoxLayout(bar_widget)
            bar_layout.setContentsMargins(4, 4, 4, 4)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(int(score))
            bar.setTextVisible(False)
            bar.setFixedHeight(12)

            if score >= 90:
                bar_color = SUCCESS
            elif score >= 70:
                bar_color = WARNING
            else:
                bar_color = ERROR
            bar_layout.addWidget(bar)

            self.table.setCellWidget(row, 6, bar_widget)

    def _update_card(self, card: MiniStatCard, value: str):
        card.update_value(value)
