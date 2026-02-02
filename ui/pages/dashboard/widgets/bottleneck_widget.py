"""
Akıllı İş - Dashboard Kapasite Darboğaz Widget

Dashboard için kapasite darboğazlarını gösteren widget.
30 gün içinde %100+ yüklenmiş istasyonları listeler.
"""

from datetime import date, timedelta
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QPen

from config.styles import COLORS, FONT_FAMILY_QT
from core.threads.worker_manager import WorkerManager

from .base import BaseWidget, WidgetConfig


class MiniCapacityBar(QWidget):
    """Mini kapasite doluluk barı."""

    def __init__(self, utilization: float, parent=None):
        super().__init__(parent)
        self.utilization = utilization
        self.setFixedHeight(16)
        self.setMinimumWidth(60)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        height = rect.height()
        width = rect.width()

        # Arka plan
        painter.setBrush(QBrush(QColor("#e5e7eb")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, width, height, 3, 3)

        # Doluluk barı
        fill_width = min(width, int(width * self.utilization / 100))

        # Renk seçimi
        if self.utilization >= 120:
            color = QColor("#dc2626")  # Koyu kırmızı
        elif self.utilization >= 100:
            color = QColor("#ef4444")  # Kırmızı
        elif self.utilization >= 80:
            color = QColor("#f59e0b")  # Turuncu
        else:
            color = QColor("#10b981")  # Yeşil

        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(0, 0, fill_width, height, 3, 3)

        # Yüzde metni
        painter.setPen(QPen(QColor("#1f2937")))
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"%{self.utilization:.0f}")


class BottleneckRow(QFrame):
    """Tek bir darboğaz satırı."""

    def __init__(self, station_name: str, target_date: date, utilization: float, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"""
            QFrame {{
                background: {COLORS['bg_secondary']};
                border-radius: 4px;
                padding: 4px;
            }}
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # İstasyon adı
        name_label = QLabel(station_name)
        name_label.setFont(QFont(FONT_FAMILY_QT, 9))
        name_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(name_label, 1)

        # Tarih
        date_label = QLabel(target_date.strftime("%d.%m"))
        date_label.setFont(QFont(FONT_FAMILY_QT, 9))
        date_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(date_label)

        # Doluluk barı
        bar = MiniCapacityBar(utilization)
        layout.addWidget(bar)


class CapacityBottleneckDashboardWidget(BaseWidget):
    """
    Dashboard Kapasite Darboğaz Widget

    Gelecek 30 gün içinde >%100 yüklü istasyonları listeler.
    """

    widget_code = "capacity_bottleneck"
    widget_name = "Kapasite Darboğazları"
    widget_type = "list"
    min_size = (1, 2)
    default_size = (1, 2)
    max_size = (2, 3)
    required_permission = "production.view"
    refresh_interval = 300  # 5 dakika

    def __init__(
        self,
        config: Optional[WidgetConfig] = None,
        edit_mode: bool = False,
        parent: Optional[QWidget] = None,
    ):
        self.aps_service = None
        self.bottlenecks = []
        super().__init__(config, edit_mode, parent)

    def create_content(self) -> QWidget:
        """Widget içeriğini oluşturur."""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()

        scroll.setWidget(self.list_container)
        layout.addWidget(scroll, 1)

        # Alt özet satırı
        self.summary_frame = QFrame()
        self.summary_frame.setStyleSheet(
            f"""
            QFrame {{
                background: {COLORS['warning']}20;
                border-radius: 4px;
                padding: 4px 8px;
            }}
            """
        )
        summary_layout = QHBoxLayout(self.summary_frame)
        summary_layout.setContentsMargins(0, 0, 0, 0)

        self.summary_label = QLabel("Yükleniyor...")
        self.summary_label.setFont(QFont(FONT_FAMILY_QT, 9))
        self.summary_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        summary_layout.addWidget(self.summary_label)

        layout.addWidget(self.summary_frame)

        # Servisi al ve veri yükle
        self._init_service()

        return content

    def _init_service(self):
        """APS servisini başlat."""
        try:
            from modules.aps import APSService

            self.aps_service = APSService()
        except ImportError:
            self.summary_label.setText("APS modülü yüklenemedi")

    def refresh_data(self):
        """Veriyi yeniler."""
        if not self.aps_service:
            self._init_service()
            if not self.aps_service:
                return

        start = date.today()
        end = start + timedelta(days=30)

        def fetch():
            return self.aps_service.get_bottleneck_stations(start, end, 100.0)

        def on_result(bottlenecks):
            self.bottlenecks = bottlenecks[:5]  # İlk 5 darboğaz
            self._update_display()

        def on_error(error):
            try:
                if hasattr(self, 'summary_label') and self.summary_label:
                    self.summary_label.setText(f"Hata: {str(error)[:20]}...")
            except RuntimeError:
                pass  # Widget silindi, hata yoksay

        WorkerManager().run_task(fetch, on_result=on_result, on_error=on_error)

    def _update_display(self):
        """Görüntüyü günceller."""
        # Mevcut satırları temizle
        while self.list_layout.count() > 1:  # Son stretch hariç
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.bottlenecks:
            # Darboğaz yok
            self.summary_frame.setStyleSheet(
                f"""
                QFrame {{
                    background: {COLORS['success']}20;
                    border-radius: 4px;
                    padding: 4px 8px;
                }}
                """
            )
            self.summary_label.setText("✅ Darboğaz tespit edilmedi")
            return

        # Darboğaz satırları ekle
        for bn in self.bottlenecks:
            row = BottleneckRow(
                station_name=bn.get("station_code", "?"),
                target_date=bn.get("date", date.today()),
                utilization=bn.get("utilization", 0),
            )
            self.list_layout.insertWidget(self.list_layout.count() - 1, row)

        # Özet
        total = len(self.bottlenecks)
        critical = sum(1 for bn in self.bottlenecks if bn.get("utilization", 0) >= 120)

        if critical > 0:
            self.summary_frame.setStyleSheet(
                f"""
                QFrame {{
                    background: {COLORS['danger']}20;
                    border-radius: 4px;
                    padding: 4px 8px;
                }}
                """
            )
            self.summary_label.setText(f"⚠️ {total} darboğaz ({critical} kritik)")
        else:
            self.summary_frame.setStyleSheet(
                f"""
                QFrame {{
                    background: {COLORS['warning']}20;
                    border-radius: 4px;
                    padding: 4px 8px;
                }}
                """
            )
            self.summary_label.setText(f"⚠️ {total} darboğaz tespit edildi")
