from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QGridLayout,
    QPushButton,
    QScrollArea,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont

# Not: QChart kullanımı için PyQt6.QtCharts gerekebilir ancak standart widgetlarla basit grafik yapacağız
# veya varsa custom chart widget kullanacağız. Şimdilik bar grafiklerini progress bar veya layout ile simüle edelim.

from modules.reports.analytics import AnalyticsService
from config.styles import SUCCESS, WARNING, ERROR, ACCENT


class MetricCard(QFrame):
    def __init__(self, title, value, unit="", color=ACCENT, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }}
            QLabel#Value {{
                color: {color};
                font-size: 24px;
                font-weight: bold;
            }}
            QLabel#Title {{
                color: #757575;
                font-size: 14px;
            }}
        """
        )

        layout = QVBoxLayout(self)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("Title")
        layout.addWidget(lbl_title)

        lbl_value = QLabel(f"{value} {unit}")
        lbl_value.setObjectName("Value")
        layout.addWidget(lbl_value)


class SimpleBarChart(QFrame):
    def __init__(self, title, data, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("background-color: white; border-radius: 8px;")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(title))

        # Chart Area
        chart_layout = QHBoxLayout()
        chart_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        max_val = max([d["quantity"] for d in data]) if data else 1

        for item in data:
            bar_layout = QVBoxLayout()
            bar_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

            val = item["quantity"]
            height = int((val / max_val) * 100) if max_val > 0 else 0

            bar = QFrame()
            bar.setFixedSize(30, max(height, 2))  # Min height to show something
            bar.setStyleSheet(f"background-color: {ACCENT}; border-radius: 3px;")

            bar_layout.addWidget(bar)
            bar_layout.addWidget(QLabel(item["date"]))

            chart_layout.addLayout(bar_layout)

        layout.addLayout(chart_layout)


class ProductionDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.service = AnalyticsService()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("Üretim Panosu"))

        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self.load_data)
        header.addWidget(refresh_btn)

        main_layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.layout = QVBoxLayout(content)

        # KPI Cards Row
        self.kpi_layout = QHBoxLayout()
        self.layout.addLayout(self.kpi_layout)

        # Charts Row
        self.charts_layout = QHBoxLayout()
        self.layout.addLayout(self.charts_layout)

        # Cost Trend Row
        self.cost_layout = QVBoxLayout()
        self.layout.addLayout(self.cost_layout)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def load_data(self):
        data = self.service.get_dashboard_stats()

        # Clear Layouts
        self._clear_layout(self.kpi_layout)
        self._clear_layout(self.charts_layout)
        self._clear_layout(self.cost_layout)

        # 1. KPI Cards
        self.kpi_layout.addWidget(
            MetricCard(
                "OEE Skoru",
                f"{data['oee_score']:.1f}",
                "%",
                color=SUCCESS if data["oee_score"] > 85 else WARNING,
            )
        )

        self.kpi_layout.addWidget(
            MetricCard("Aktif Siparişler", str(data["active_orders"]), "Adet")
        )

        self.kpi_layout.addWidget(
            MetricCard("Haftalık Üretim", f"{data['weekly_volume']:.0f}", "Br")
        )

        eff = data["cost_efficiency"]
        eff_color = (
            SUCCESS if eff <= 0 else ERROR
        )  # Negatif varyans = Daha az maliyet = İyi
        eff_prefix = "+" if eff > 0 else ""
        self.kpi_layout.addWidget(
            MetricCard(
                "Maliyet Sapması", f"{eff_prefix}{eff:.1f}", "%", color=eff_color
            )
        )

        # 2. Production Trend Chart
        if data["production_trend"]:
            chart = SimpleBarChart(
                "Günlük Üretim Trendi (Son 7 Gün)", data["production_trend"]
            )
            chart.setMinimumHeight(200)
            self.charts_layout.addWidget(chart)

        # 3. Cost Trend (Textual for now)
        self.cost_layout.addWidget(QLabel("Son Sipariş Maliyet Sapmaları:"))
        for item in data["cost_trend"]:
            color = "red" if item["variance_pct"] > 0 else "green"
            lbl = QLabel(
                f"{item['order_no']} ({item['date']}): %{item['variance_pct']:.1f}"
            )
            lbl.setStyleSheet(f"color: {color}")
            self.cost_layout.addWidget(lbl)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
