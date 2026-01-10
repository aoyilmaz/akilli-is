"""
Akıllı İş - Üretim OEE Raporu
"""

from datetime import date
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
    QDateEdit,
    QProgressBar,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor

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

        # Filtreler
        filter_frame = QFrame()
        filter_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
        """
        )
        filter_layout = QHBoxLayout(filter_frame)

        lbl1 = QLabel("Başlangıç:")
        lbl1.setStyleSheet(f"color: {TEXT_PRIMARY};")
        filter_layout.addWidget(lbl1)
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setStyleSheet(get_input_style())
        filter_layout.addWidget(self.start_date)

        lbl2 = QLabel("Bitiş:")
        lbl2.setStyleSheet(f"color: {TEXT_PRIMARY};")
        filter_layout.addWidget(lbl2)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setStyleSheet(get_input_style())
        filter_layout.addWidget(self.end_date)

        filter_layout.addStretch()

        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        refresh_btn.setStyleSheet(get_button_style())
        filter_layout.addWidget(refresh_btn)

        layout.addWidget(filter_frame)

        # OEE Kartları
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        # OEE Ana Kart
        self.oee_card = self._create_oee_card()
        cards_layout.addWidget(self.oee_card, 2)

        # Bileşen kartları
        components_layout = QVBoxLayout()
        components_layout.setSpacing(8)

        self.availability_bar = self._create_metric_bar(
            "Kullanılabilirlik", SUCCESS
        )
        components_layout.addWidget(self.availability_bar)

        self.performance_bar = self._create_metric_bar("Performans", ACCENT)
        components_layout.addWidget(self.performance_bar)

        self.quality_bar = self._create_metric_bar("Kalite", WARNING)
        components_layout.addWidget(self.quality_bar)

        cards_layout.addLayout(components_layout, 3)

        layout.addLayout(cards_layout)

        # İstatistikler
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.total_orders_card = self._create_mini_card("Toplam İş Emri", "0")
        stats_layout.addWidget(self.total_orders_card)

        self.on_time_card = self._create_mini_card("Zamanında", "0")
        stats_layout.addWidget(self.on_time_card)

        self.planned_card = self._create_mini_card("Plan. Üretim", "0")
        stats_layout.addWidget(self.planned_card)

        self.actual_card = self._create_mini_card("Gerçek Üretim", "0")
        stats_layout.addWidget(self.actual_card)

        layout.addLayout(stats_layout)

        # Detay tablosu
        self.table = QTableWidget()
        self._setup_table(
            self.table,
            [
                ("İş Emri No", 120),
                ("Ürün", 200),
                ("Planlanan", 100),
                ("Gerçekleşen", 100),
                ("Performans", 100),
            ],
        )
        layout.addWidget(self.table)

    def _create_oee_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_TERTIARY};
                border: 2px solid {ACCENT}80;
                border-radius: 12px;
            }}
        """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("OEE (Overall Equipment Effectiveness)")
        title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; font-weight: 500;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.oee_value = QLabel("0%")
        self.oee_value.setStyleSheet(
            f"color: {ACCENT}; font-size: 64px; font-weight: bold;"
        )
        self.oee_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.oee_value)

        formula = QLabel("= Kullanılabilirlik × Performans × Kalite")
        formula.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        formula.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(formula)

        return card

    def _create_metric_bar(self, title: str, color: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
        """
        )

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        label = QLabel(title)
        label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        header.addWidget(label)

        value = QLabel("0%")
        value.setObjectName("value")
        value.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
        header.addWidget(value)
        layout.addLayout(header)

        bar = QProgressBar()
        bar.setObjectName("bar")
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(False)
        bar.setFixedHeight(8)
        bar.setStyleSheet(
            f"""
            QProgressBar {{
                background-color: {BG_TERTIARY};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """
        )
        layout.addWidget(bar)

        return frame

    def _create_mini_card(self, title: str, value: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
        """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 24px; font-weight: bold;")
        layout.addWidget(value_label)

        return card

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

        table.setStyleSheet(get_table_style())

    def load_data(self, data: dict):
        # OEE değeri
        oee = data.get("oee", 0)
        self.oee_value.setText(f"{oee}%")

        # Renk belirle
        if oee >= 85:
            color = SUCCESS
        elif oee >= 60:
            color = WARNING
        else:
            color = ERROR
        self.oee_value.setStyleSheet(
            f"color: {color}; font-size: 64px; font-weight: bold;"
        )

        # Bileşenler
        self._update_metric_bar(self.availability_bar, data.get("availability", 0))
        self._update_metric_bar(self.performance_bar, data.get("performance", 0))
        self._update_metric_bar(self.quality_bar, data.get("quality", 0))

        # İstatistikler
        self._update_mini_card(self.total_orders_card, str(data.get("total_orders", 0)))
        self._update_mini_card(self.on_time_card, str(data.get("on_time_count", 0)))
        self._update_mini_card(
            self.planned_card, f"{data.get('total_planned', 0):,.0f}"
        )
        self._update_mini_card(self.actual_card, f"{data.get('total_actual', 0):,.0f}")

        # Detay tablosu
        details = data.get("details", [])
        self.table.setRowCount(len(details))

        for row, item in enumerate(details):
            self.table.setItem(row, 0, QTableWidgetItem(item.get("work_order_no", "")))
            self.table.setItem(row, 1, QTableWidgetItem(item.get("item_name", "")))

            planned = item.get("planned_qty", 0)
            planned_item = QTableWidgetItem(f"{planned:,.0f}")
            planned_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 2, planned_item)

            actual = item.get("actual_qty", 0)
            actual_item = QTableWidgetItem(f"{actual:,.0f}")
            actual_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 3, actual_item)

            perf = item.get("performance", 0)
            perf_item = QTableWidgetItem(f"{perf:.1f}%")
            perf_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            if perf >= 100:
                perf_item.setForeground(QColor(SUCCESS))
            elif perf < 80:
                perf_item.setForeground(QColor(ERROR))
            self.table.setItem(row, 4, perf_item)

    def _update_metric_bar(self, frame: QFrame, value: float):
        value_label = frame.findChild(QLabel, "value")
        if value_label:
            value_label.setText(f"{value:.1f}%")

        bar = frame.findChild(QProgressBar, "bar")
        if bar:
            bar.setValue(int(value))

    def _update_mini_card(self, card: QFrame, value: str):
        value_label = card.findChild(QLabel, "value")
        if value_label:
            value_label.setText(value)

    def get_date_range(self):
        return (self.start_date.date().toPyDate(), self.end_date.date().toPyDate())
