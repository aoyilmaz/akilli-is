"""
Akıllı İş - Circular Gauge Widget

Yüzde değerlerini dairesel progress göstergesi olarak sunar.
KPI'lar için ideal: verimlilik, kapasite kullanımı, hedef gerçekleşme vb.
"""

from typing import Optional, Callable
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QConicalGradient
)

from config.styles import COLORS, FONT_FAMILY_QT
from .base import BaseWidget, WidgetConfig


class CircularGauge(QWidget):
    """
    Dairesel progress göstergesi.

    Yüzde değerini animasyonlu dolum ile gösterir.
    """

    def __init__(
        self,
        value: float = 0,
        max_value: float = 100,
        color: Optional[str] = None,
        thickness: int = 8,
        parent: Optional[QWidget] = None
    ):
        """
        Args:
            value: Gösterilecek değer
            max_value: Maksimum değer
            color: Gauge rengi
            thickness: Çizgi kalınlığı
            parent: Parent widget
        """
        super().__init__(parent)
        self._value = value
        self._max_value = max_value
        self._color = color or COLORS['primary']
        self._thickness = thickness

        # Animasyon için
        self._animated_value = 0.0
        self._target_value = value
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._animate_step)

        # Boyut
        self.setFixedSize(80, 80)

    def set_value(self, value: float, animate: bool = True):
        """
        Gauge değerini ayarlar.

        Args:
            value: Yeni değer
            animate: Animasyonlu geçiş yapılsın mı
        """
        self._value = min(value, self._max_value)
        self._target_value = self._value

        if animate:
            self._start_animation()
        else:
            self._animated_value = self._value
            self.update()

    def set_color(self, color: str):
        """Gauge rengini değiştirir"""
        self._color = color
        self.update()

    def _start_animation(self):
        """Animasyonu başlat"""
        self._animation_timer.start(16)  # ~60fps

    def _animate_step(self):
        """Animasyon adımı"""
        diff = self._target_value - self._animated_value
        if abs(diff) < 0.5:
            self._animated_value = self._target_value
            self._animation_timer.stop()
        else:
            # Easing
            self._animated_value += diff * 0.15

        self.update()

    def paintEvent(self, event):
        """Gauge çizimi"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Merkez ve yarıçap
        center = self.rect().center()
        radius = min(self.width(), self.height()) / 2 - self._thickness

        # Çizim alanı
        rect = QRectF(
            center.x() - radius,
            center.y() - radius,
            radius * 2,
            radius * 2
        )

        # Arka plan arc (tam daire değil, 270 derece)
        self._draw_background_arc(painter, rect)

        # Değer arc
        self._draw_value_arc(painter, rect)

        # Merkez değer metni
        self._draw_center_text(painter)

    def _draw_background_arc(self, painter: QPainter, rect: QRectF):
        """Arka plan yayını çiz"""
        pen = QPen(QColor(COLORS['border']), self._thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # 135 dereceden başla, 270 derece çiz (aşağıda açık)
        start_angle = 225 * 16  # Qt 1/16 derece kullanır
        span_angle = -270 * 16

        painter.drawArc(rect, start_angle, span_angle)

    def _draw_value_arc(self, painter: QPainter, rect: QRectF):
        """Değer yayını çiz"""
        if self._animated_value <= 0:
            return

        # Gradient
        percentage = self._animated_value / self._max_value
        sweep_angle = int(-270 * percentage * 16)

        # Renk - değere göre değişebilir
        color = self._get_value_color(percentage)

        pen = QPen(QColor(color), self._thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        start_angle = 225 * 16
        painter.drawArc(rect, start_angle, sweep_angle)

    def _get_value_color(self, percentage: float) -> str:
        """Yüzdeye göre renk döndür"""
        # Eğer özel renk ayarlandıysa onu kullan
        if self._color != COLORS['primary']:
            return self._color

        # Varsayılan: yeşil -> sarı -> kırmızı
        if percentage >= 0.9:
            return COLORS['danger']  # %90+ kırmızı
        elif percentage >= 0.7:
            return COLORS['warning']  # %70-90 sarı
        else:
            return COLORS['success']  # %70 altı yeşil

    def _draw_center_text(self, painter: QPainter):
        """Merkezdeki yüzde metnini çiz"""
        painter.setPen(QColor(COLORS['text_primary']))
        font = QFont(FONT_FAMILY_QT, 14, QFont.Weight.Bold)
        painter.setFont(font)

        text = f"{int(self._animated_value)}%"
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            text
        )


class GaugeWidget(BaseWidget):
    """
    Dashboard gauge widget'ı.

    Circular gauge'u BaseWidget içinde kullanır.
    """

    widget_code = "gauge_generic"
    widget_name = "Gauge"
    widget_type = "gauge"
    widget_description = "Yüzde göstergesi"
    widget_icon = "gauge"
    min_size = (1, 1)
    default_size = (1, 1)
    max_size = (1, 1)
    refresh_interval = 300  # 5 dakika

    def __init__(
        self,
        config: Optional[WidgetConfig] = None,
        edit_mode: bool = False,
        parent: Optional[QWidget] = None,
        value_getter: Optional[Callable[[], float]] = None,
    ):
        self._value_getter = value_getter
        self._gauge: Optional[CircularGauge] = None
        super().__init__(config, edit_mode, parent)

    def create_content(self):
        """Widget içeriğini oluştur"""
        # Gauge
        self._gauge = CircularGauge(color=self.get_accent_color())
        self.content_layout.addWidget(
            self._gauge,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Açıklama
        self.description_label = QLabel("")
        self.description_label.setFont(QFont(FONT_FAMILY_QT, 10))
        self.description_label.setStyleSheet(
            f"color: {COLORS['text_secondary']};"
        )
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_label.setWordWrap(True)
        self.content_layout.addWidget(self.description_label)

    def refresh_data(self):
        """Veriyi yenile"""
        self.set_loading(True)
        try:
            if self._value_getter and self._gauge:
                value = self._value_getter()
                self._gauge.set_value(value)

            # Config'den açıklama
            desc = self._config.config.get("description", "")
            self.description_label.setText(desc)
        except Exception as e:
            print(f"GaugeWidget hatası: {e}")
        finally:
            self.set_loading(False)

    def set_value(self, value: float, animate: bool = True):
        """Değeri manuel ayarla"""
        if self._gauge:
            self._gauge.set_value(value, animate)


class CapacityGaugeWidget(GaugeWidget):
    """Kapasite kullanım göstergesi"""

    widget_code = "gauge_capacity"
    widget_name = "Kapasite Kullanımı"
    widget_category = "production"
    widget_description = "Üretim kapasite kullanım oranı"
    required_permission = "production.view"

    def refresh_data(self):
        """Kapasite verisini çek"""
        self.set_loading(True)
        try:
            # Örnek: Gerçek uygulamada veritabanından çekilir
            # Şimdilik sabit değer
            self.set_value(75)
            self.description_label.setText("Kapasite Kullanımı")
        except Exception as e:
            print(f"CapacityGaugeWidget hatası: {e}")
        finally:
            self.set_loading(False)


class EfficiencyGaugeWidget(GaugeWidget):
    """Üretim verimliliği göstergesi"""

    widget_code = "gauge_efficiency"
    widget_name = "Verimlilik"
    widget_category = "production"
    widget_description = "Üretim verimliliği oranı"
    required_permission = "production.view"

    def refresh_data(self):
        """Verimlilik verisini çek"""
        self.set_loading(True)
        try:
            # Örnek değer
            self.set_value(85)
            self.description_label.setText("Üretim Verimliliği")
        except Exception as e:
            print(f"EfficiencyGaugeWidget hatası: {e}")
        finally:
            self.set_loading(False)
