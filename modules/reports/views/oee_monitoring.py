"""
Akıllı İş - Canlı OEE İzleme Ekranı
"""

from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QTableWidgetItem,
    QProgressBar,
    QGridLayout,
    QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QColor, QFont
import qtawesome as qta

from config.icons import ICONS
from config.styles import COLORS, FONT_FAMILY_QT
from ui.components.page_header import PageHeader
from ui.pages.dashboard.widgets.gauge_widget import CircularGauge


class StationOEECard(QFrame):
    """Bireysel iş istasyonu OEE kartı"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(
            f"""
            StationOEECard {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
            StationOEECard:hover {{
                border: 1px solid {COLORS['primary']};
            }}
        """
        )
        self.setMinimumSize(300, 220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header: Station Name & Work Order
        header_layout = QVBoxLayout()
        self.station_label = QLabel("İstasyon Adı")
        self.station_label.setFont(QFont(FONT_FAMILY_QT, 12, QFont.Weight.Bold))
        self.station_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        header_layout.addWidget(self.station_label)

        self.wo_label = QLabel("İş Emri: -")
        self.wo_label.setFont(QFont(FONT_FAMILY_QT, 10))
        self.wo_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header_layout.addWidget(self.wo_label)

        layout.addLayout(header_layout)

        # Main Display: Gauge + APQ Bars
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)

        # Left: OEE Gauge
        self.gauge = CircularGauge(thickness=10)
        self.gauge.setFixedSize(100, 100)
        main_layout.addWidget(self.gauge)

        # Right: APQ Bars
        bars_layout = QVBoxLayout()
        bars_layout.setSpacing(8)

        self.bars = {
            "avail": self._create_mini_bar("A", COLORS["success"]),
            "perf": self._create_mini_bar("P", COLORS["primary"]),
            "qual": self._create_mini_bar("Q", COLORS["warning"]),
        }

        for bar_widget in self.bars.values():
            bars_layout.addWidget(bar_widget)

        main_layout.addLayout(bars_layout)
        layout.addLayout(main_layout)

    def _create_mini_bar(self, label: str, color: str) -> QWidget:
        container = QWidget()
        l = QHBoxLayout(container)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(8)

        lbl = QLabel(label)
        lbl.setFixedWidth(15)
        lbl.setFont(QFont(FONT_FAMILY_QT, 9, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
        l.addWidget(lbl)

        bar = QProgressBar()
        bar.setFixedHeight(8)
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(False)
        bar.setStyleSheet(
            f"""
            QProgressBar {{
                background-color: {COLORS['bg_hover']};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """
        )
        l.addWidget(bar)

        val = QLabel("0%")
        val.setFixedWidth(35)
        val.setFont(QFont(FONT_FAMILY_QT, 9))
        val.setStyleSheet(f"color: {COLORS['text_primary']};")
        l.addWidget(val)

        container.bar = bar
        container.val = val
        return container

    def update_data(self, data: Dict):
        """Kart verilerini güncelle"""
        self.station_label.setText(data.get("work_station", "Bilinmiyor"))
        self.wo_label.setText(
            f"İş Emri: {data.get('work_order_no', '-')} | {data.get('item_name', '')}"
        )

        oee = data.get("oee", 0)
        self.gauge.set_value(oee)

        # Renk ayarı (OEE'ye göre)
        if oee >= 85:
            oee_color = COLORS["success"]
        elif oee >= 65:
            oee_color = COLORS["warning"]
        else:
            oee_color = COLORS["danger"]
        self.gauge.set_color(oee_color)

        self._update_mini_bar(self.bars["avail"], data.get("availability", 0))
        self._update_mini_bar(self.bars["perf"], data.get("performance", 0))
        self._update_mini_bar(self.bars["qual"], data.get("quality", 0))

    def _update_mini_bar(self, widget, value):
        widget.bar.setValue(int(value))
        widget.val.setText(f"{value:.0f}%")


class OEEMonitoringPage(QWidget):
    """Canlı OEE İzleme Sayfası"""

    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards: Dict[int, StationOEECard] = {}
        self.setup_ui()

        # Otomatik yenileme timer'ı (10 saniye)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_requested.emit)
        self.timer.start(10000)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Canlı OEE İzleme",
            icon=ICONS.CHART,
            show_search=False,
            show_add=False,
            parent=self,
        )
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        layout.addWidget(self.header)

        # Scroll Area for Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"background-color: transparent;")

        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setContentsMargins(16, 16, 16, 16)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )

        scroll.setWidget(self.container)
        layout.addWidget(scroll)

        # Empty State
        self.empty_label = QLabel("Şu an aktif üretim operasyonu bulunmuyor.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 16px; margin-top: 50px;"
        )
        self.empty_label.setVisible(False)
        layout.addWidget(self.empty_label)

    def update_data(self, data_list: List[Dict]):
        """Tüm kartları güncelle veya oluştur"""
        active_ids = {d["id"] for d in data_list}

        # Eskiyen kartları kaldır
        for op_id in list(self.cards.keys()):
            if op_id not in active_ids:
                card = self.cards.pop(op_id)
                self.grid_layout.removeWidget(card)
                card.deleteLater()

        # Yeni kartları ekle veya güncelle
        for i, data in enumerate(data_list):
            op_id = data["id"]
            if op_id not in self.cards:
                card = StationOEECard()
                self.cards[op_id] = card
                # Grid pozisyonu (3 sütunlu)
                row = i // 3
                col = i % 3
                self.grid_layout.addWidget(card, row, col)

            self.cards[op_id].update_data(data)

        self.empty_label.setVisible(len(data_list) == 0)
        self.container.setVisible(len(data_list) > 0)

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)
