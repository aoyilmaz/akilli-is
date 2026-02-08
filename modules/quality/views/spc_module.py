"""
Akıllı İş - SPC (İstatistiksel Proses Kontrol) Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QFrame,
    QGridLayout,
    QScrollArea,
    QPushButton,
    QMessageBox,
)
from PyQt6.QtCore import Qt
import qtawesome as qta

from config.icons import ICONS
from config.styles import COLORS
from modules.quality.spc_service import SPCService
from modules.quality.services import QualityService
from modules.quality.views.spc_charts import SPCChartWidget


class SPCStatCard(QFrame):
    """İstatistik verileri için görsel kart."""

    def __init__(self, title, icon, color):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("stat_card")
        self.setStyleSheet(
            f"""
            #stat_card {{
                background-color: white;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon, color=color).pixmap(32, 32))
        layout.addWidget(icon_label)

        text_layout = QVBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px;"
        )
        self.value_label = QLabel("0.00")
        self.value_label.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 18px; font-weight: bold;"
        )

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.value_label)
        layout.addLayout(text_layout)
        layout.addStretch()

    def set_value(self, val):
        self.value_label.setText(str(val))


class SPCModule(QWidget):
    """SPC Dashboard Modülü"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.spc_service = SPCService()
        self.quality_service = QualityService()
        self.setup_ui()
        self.load_items()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Üst Panel (Filtreler)
        filter_frame = QFrame()
        filter_frame.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; border-radius: 8px;"
        )
        filter_layout = QHBoxLayout(filter_frame)

        self.item_combo = QComboBox()
        self.item_combo.setPlaceholderText("Malzeme Seçiniz...")
        self.item_combo.setMinimumWidth(250)
        self.item_combo.currentIndexChanged.connect(self.load_criteria)
        filter_layout.addWidget(QLabel("Malzeme:"))
        filter_layout.addWidget(self.item_combo)

        filter_layout.addSpacing(20)

        self.criteria_combo = QComboBox()
        self.criteria_combo.setPlaceholderText("Kriter Seçiniz...")
        self.criteria_combo.setMinimumWidth(250)
        self.criteria_combo.currentIndexChanged.connect(self.refresh_stats)
        filter_layout.addWidget(QLabel("Kriter:"))
        filter_layout.addWidget(self.criteria_combo)

        filter_layout.addStretch()

        self.refresh_btn = QPushButton("Yenile")
        self.refresh_btn.setIcon(qta.icon(ICONS.REFRESH))
        self.refresh_btn.clicked.connect(self.refresh_stats)
        filter_layout.addWidget(self.refresh_btn)

        layout.addWidget(filter_frame)

        # İstatistik Kartları
        stats_layout = QGridLayout()
        self.card_mean = SPCStatCard("Ortalama (Mean)", ICONS.INFO, COLORS["info"])
        self.card_cp = SPCStatCard("Cp (Kapasite)", ICONS.DASHBOARD, COLORS["accent"])
        self.card_cpk = SPCStatCard(
            "Cpk (Yeterlilik)", ICONS.DASHBOARD, COLORS["success"]
        )
        self.card_std = SPCStatCard("Std. Sapma", ICONS.HISTORY, COLORS["warning"])

        stats_layout.addWidget(self.card_mean, 0, 0)
        stats_layout.addWidget(self.card_cp, 0, 1)
        stats_layout.addWidget(self.card_cpk, 0, 2)
        stats_layout.addWidget(self.card_std, 0, 3)
        layout.addLayout(stats_layout)

        # Grafikler
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)

        self.xbar_chart = SPCChartWidget("X-bar (Ortalama) Grafiği")
        self.r_chart = SPCChartWidget("R (Range) Grafiği")

        scroll_layout.addWidget(self.xbar_chart)
        scroll_layout.addWidget(self.r_chart)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def load_items(self):
        self.item_combo.blockSignals(True)
        self.item_combo.clear()
        self.item_combo.addItem("Seçiniz...", None)

        templates = self.quality_service.get_all_templates()
        added_items = set()
        for t in templates:
            if t.item and t.item.id not in added_items:
                self.item_combo.addItem(f"{t.item.code} - {t.item.name}", t.item.id)
                added_items.add(t.item.id)
        self.item_combo.blockSignals(False)

    def load_criteria(self):
        item_id = self.item_combo.currentData()
        self.criteria_combo.blockSignals(True)
        self.criteria_combo.clear()
        self.criteria_combo.addItem("Seçiniz...", None)

        if item_id:
            template = self.quality_service.get_template_by_item(item_id)
            if template:
                for c in template.criteria:
                    if c.is_spc:
                        self.criteria_combo.addItem(c.name, c.id)
        self.criteria_combo.blockSignals(False)

    def refresh_stats(self):
        criteria_id = self.criteria_combo.currentData()
        if not criteria_id:
            self.xbar_chart.set_data([])
            self.r_chart.set_data([])
            return

        try:
            stats = self.spc_service.get_process_stats(criteria_id)
            if stats:
                self.card_mean.set_value(f"{stats['mean']:.4f}")
                self.card_cp.set_value(
                    f"{stats['cp']:.2f}" if stats["cp"] is not None else "N/A"
                )
                self.card_cpk.set_value(
                    f"{stats['cpk']:.2f}" if stats["cpk"] is not None else "N/A"
                )
                self.card_std.set_value(f"{stats['std']:.4f}")

                # Limitleri al
                limits = self.spc_service.calculate_control_limits(criteria_id)
                ucl, lcl, cl = (None, None, None)
                if limits:
                    ucl, lcl, cl = limits["ucl"], limits["lcl"], limits["cl"]

                # Grafik verilerini al
                chart_data = self.spc_service.get_control_chart_data(criteria_id)

                xbar_points = [
                    {"label": p["timestamp"], "val": p["x_bar"]} for p in chart_data
                ]
                self.xbar_chart.set_data(xbar_points, ucl=ucl, lcl=lcl, cl=cl)

                r_points = [
                    {"label": p["timestamp"], "val": p["r"]} for p in chart_data
                ]
                self.r_chart.set_data(r_points)
            else:
                self.xbar_chart.set_data([])
                self.r_chart.set_data([])
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"İstatistikler yüklenemedi: {str(e)}")
