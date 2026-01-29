"""
Akıllı İş - Kapasite Analizi Modülü
İş istasyonlarının doluluk oranlarını ve kapasite kullanımını analiz eder.
"""

from datetime import datetime, date, timedelta
from typing import List, Dict

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QFrame,
    QPushButton,
    QTableWidgetItem,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen
import qtawesome as qta

from config.icons import ICONS
from ui.components.stat_cards import MiniStatCard
from ui.components.page_header import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


class CapacityChart(QWidget):
    """İş İstasyonu Kapasite Yük Grafiği (Bar Chart)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []  # List of dicts with station, capacity, load
        self.setMinimumHeight(300)

    def set_data(self, data: List[Dict]):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.data:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Veri yok")
            return

        # Çizim alanı
        margin_left = 100
        margin_bottom = 40
        margin_top = 20
        margin_right = 20

        width = self.width() - margin_left - margin_right
        height = self.height() - margin_bottom - margin_top

        # Max değer bul (Kapasite veya Yük'ten hangisi büyükse)
        max_val = 0
        for item in self.data:
            max_val = max(max_val, item["capacity"], item["load"])

        if max_val == 0:
            max_val = 10  # Bölme hatasını önle

        bar_count = len(self.data)
        bar_width = width / bar_count / 2 if bar_count > 0 else 20
        spacing = bar_width / 2

        # Eksenleri çiz
        painter.setPen(QPen(QColor("#64748b"), 1))
        painter.drawLine(
            margin_left, margin_top, margin_left, margin_top + height
        )  # Y ekseni
        painter.drawLine(
            margin_left,
            margin_top + height,
            margin_left + width,
            margin_top + height,
        )  # X ekseni

        # Kılavuz çizgileri ve Değerler
        steps = 5
        for i in range(steps + 1):
            val = max_val * i / steps
            y = margin_top + height - (val / max_val * height)

            painter.setPen(QPen(QColor("#334155"), 1, Qt.PenStyle.DotLine))
            painter.drawLine(margin_left, int(y), margin_left + width, int(y))

            painter.setPen(QPen(QColor("#94a3b8")))
            painter.drawText(
                0,
                int(y) - 5,
                margin_left - 10,
                10,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{val:.1f} sa",
            )

        # Barları çiz
        for i, item in enumerate(self.data):
            x = margin_left + (i * (bar_width * 2 + spacing)) + spacing

            # Kapasite Barı
            cap_height = (item["capacity"] / max_val) * height
            cap_rect = (
                int(x),
                int(margin_top + height - cap_height),
                int(bar_width),
                int(cap_height),
            )

            painter.setBrush(QBrush(QColor("#3b82f6")))  # Mavi
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(*cap_rect, 4, 4)

            # Yük Barı
            load_height = (item["load"] / max_val) * height
            load_rect = (
                int(x + bar_width),
                int(margin_top + height - load_height),
                int(bar_width),
                int(load_height),
            )

            # Aşırı yük varsa kırmızı, yoksa yeşil/turuncu
            cap = item["capacity"]
            utilization = item["load"] / cap if cap > 0 else 0
            if utilization > 1.0:
                load_color = QColor("#ef4444")  # Kırmızı (Aşırı Yük)
            elif utilization > 0.8:
                load_color = QColor("#f59e0b")  # Turuncu (Uyarı)
            else:
                load_color = QColor("#10b981")  # Yeşil (Normal)

            painter.setBrush(QBrush(load_color))
            painter.drawRoundedRect(*load_rect, 4, 4)

            # İstasyon adı
            painter.setPen(QPen(QColor("#cbd5e1")))
            painter.drawText(
                int(x),
                int(margin_top + height + 5),
                int(bar_width * 2),
                30,
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                item.get("code", item["station"]),
            )


class CapacityAnalysisPage(QWidget):
    """Kapasite Analizi Sayfası"""

    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.wo_service = None
        self.ws_service = None

        # Varsayılan değerler
        self.period_days = 7
        self.current_date = date.today()

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # === Header ===
        self.header = PageHeader(
            title="Kapasite Analizi (CRP)",
            icon=ICONS.PRODUCTION,
            show_search=False,
            show_refresh=False,
            show_add=False,
            parent=self,
        )

        h_layout = self.header.header_layout()

        # Dönem Seçimi
        h_layout.addWidget(QLabel("Dönem:"))
        self.period_combo = QComboBox()
        self.period_combo.addItem("Bu Hafta", 7)
        self.period_combo.addItem("Bu Ay", 30)
        self.period_combo.addItem("3 Ay", 90)
        self.period_combo.currentIndexChanged.connect(self._on_period_changed)
        self.period_combo.setMinimumWidth(120)
        h_layout.addWidget(self.period_combo)

        # Refresh butonu
        h_layout.addSpacing(16)
        refresh_btn = QPushButton("Yenile")
        refresh_btn.setIcon(qta.icon(ICONS.REFRESH, color="#ffffff"))
        refresh_btn.setProperty("class", "btn-refresh")
        refresh_btn.setFixedHeight(30)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        h_layout.addWidget(refresh_btn)

        layout.addWidget(self.header)

        # === İçerik ===
        content_layout = QHBoxLayout()

        # Sol Taraf - Grafik
        chart_frame = QFrame()
        chart_frame.setProperty("class", "card")
        chart_layout = QVBoxLayout(chart_frame)

        title_lbl = QLabel("<b>İş İstasyonu Yük Grafiği</b>")
        chart_layout.addWidget(title_lbl)
        self.chart = CapacityChart()
        self.chart.setMinimumHeight(450)
        chart_layout.addWidget(self.chart, 1)

        # Lejant
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(12)
        legend_layout.addStretch()
        legend_layout.addWidget(self._create_legend_item("Kapasite", "#3b82f6"))
        legend_layout.addWidget(self._create_legend_item("Normal Yük", "#10b981"))
        legend_layout.addWidget(
            self._create_legend_item("Riskli Yük (>%80)", "#f59e0b")
        )
        legend_layout.addWidget(
            self._create_legend_item("Aşırı Yük (>%100)", "#ef4444")
        )
        legend_layout.addStretch()
        chart_layout.addLayout(legend_layout)

        content_layout.addWidget(chart_frame, stretch=1)

        # Sağ Taraf - Özet Tablo
        table_frame = QFrame()
        table_frame.setProperty("class", "card")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)

        table_lbl = QLabel("<b>Doluluk Detayları</b>")
        table_layout.addWidget(table_lbl)

        columns = [
            ColumnConfig("station", "İstasyon", width=150, stretch=True),
            ColumnConfig("capacity", "Kapasite", width=100),
            ColumnConfig("load", "Yük", width=100),
            ColumnConfig("utilization", "Doluluk %", width=100),
        ]

        self.table = EnhancedTableWidget(
            table_id="capacity_analysis_list",
            columns=columns,
            parent=self,
        )
        table_layout.addWidget(self.table)

        content_layout.addWidget(table_frame, stretch=1)

        layout.addLayout(content_layout, stretch=1)

        # İstatistik Kartları
        stats_layout = QHBoxLayout()
        self.total_load_card = MiniStatCard(
            "Toplam Yük", "0 Saat", "primary", icon=ICONS.PRODUCTION
        )
        self.overload_card = MiniStatCard(
            "Aşırı Yüklenen", "0 İstasyon", "error", icon=ICONS.WARNING
        )
        self.avg_util_card = MiniStatCard(
            "Ort. Doluluk", "%0", "info", icon=ICONS.INVOICE
        )

        stats_layout.addWidget(self.total_load_card)
        stats_layout.addWidget(self.overload_card)
        stats_layout.addWidget(self.avg_util_card)
        stats_layout.addStretch()

        layout.addLayout(stats_layout)

        # Bağlantılar
        self.refresh_requested.connect(self.load_data)

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self.load_data()

    def _ensure_services(self):
        """Servisleri yükle"""
        if not self.wo_service:
            try:
                from modules.production.services import (
                    WorkOrderService,
                    WorkStationService,
                )

                self.wo_service = WorkOrderService()
                self.ws_service = WorkStationService()
            except Exception as e:
                print(f"Servis yükleme hatası: {e}")

    def _create_legend_item(self, text, color_code):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        box = QLabel()
        box.setFixedSize(10, 10)
        box.setStyleSheet(f"background-color: {color_code}; border-radius: 2px;")
        layout.addWidget(box)

        label = QLabel(text)
        label.setStyleSheet("color: #94a3b8; font-size: 10px;")
        layout.addWidget(label)

        return widget

    def _on_period_changed(self):
        self.period_days = self.period_combo.currentData()
        self.refresh_requested.emit()

    def set_services(self, wo_service, ws_service):
        self.wo_service = wo_service
        self.ws_service = ws_service

    def load_data(self):
        """Verileri hesapla ve arayüzü güncelle"""
        if not self.wo_service or not self.ws_service:
            self._ensure_services()
            if not self.wo_service or not self.ws_service:
                self.chart.set_data([])
                return

        try:
            stations = self.ws_service.get_all(active_only=True)
            start_date = datetime.combine(self.current_date, datetime.min.time())
            end_date = start_date + timedelta(days=self.period_days)

            analysis_data = []
            total_load = 0
            overloaded_count = 0
            total_utilization = 0

            active_orders = self.wo_service.get_all()

            for station in stations:
                work_days = self.period_days
                daily_hours = 8
                efficiency = 1.0
                capacity_hours = work_days * daily_hours * efficiency

                station_load = 0
                for wo in active_orders:
                    if wo.status.name in ["CANCELLED", "CLOSED", "COMPLETED"]:
                        continue
                    if not wo.operations:
                        continue
                    for op in wo.operations:
                        if op.work_station_id == station.id:
                            op_start = op.planned_start or wo.planned_start
                            if op_start and start_date <= op_start <= end_date:
                                setup = float(op.planned_setup_time or 0) / 60
                                run = float(op.planned_run_time or 0) / 60
                                station_load += setup + run

                cap = capacity_hours
                util_rate = (station_load / cap * 100) if cap > 0 else 0

                if util_rate > 100:
                    overloaded_count += 1

                total_load += station_load
                total_utilization += util_rate

                analysis_data.append(
                    {
                        "station": station.name,
                        "code": station.code,
                        "capacity": capacity_hours,
                        "load": station_load,
                    }
                )

            self.chart.set_data(analysis_data)
            self.table.setRowCount(len(analysis_data))
            visible_cols = self.table.get_visible_columns()

            for row, data in enumerate(analysis_data):
                cap = data["capacity"]
                util = data["load"] / cap * 100 if cap > 0 else 0

                for col_idx, col_key in enumerate(visible_cols):
                    if col_key == "station":
                        self.table.setItem(
                            row, col_idx, QTableWidgetItem(data["station"])
                        )
                    elif col_key == "capacity":
                        self.table.setItem(
                            row, col_idx, QTableWidgetItem(f"{data['capacity']:.1f} sa")
                        )
                    elif col_key == "load":
                        self.table.setItem(
                            row, col_idx, QTableWidgetItem(f"{data['load']:.1f} sa")
                        )
                    elif col_key == "utilization":
                        util_item = QTableWidgetItem(f"%{util:.1f}")
                        if util > 100:
                            util_item.setForeground(QColor("#ef4444"))
                        elif util > 80:
                            util_item.setForeground(QColor("#f59e0b"))
                        else:
                            util_item.setForeground(QColor("#10b981"))
                        self.table.setItem(row, col_idx, util_item)

            self.total_load_card.update_value(f"{total_load:.1f} Sa")
            self.overload_card.update_value(f"{overloaded_count} İstasyon")
            avg_util = total_utilization / len(stations) if stations else 0
            self.avg_util_card.update_value(f"%{avg_util:.1f}")

        except Exception as e:
            print(f"Kapasite analizi hatası: {e}")
            import traceback

            traceback.print_exc()
