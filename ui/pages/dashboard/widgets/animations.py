"""
Dashboard Widget Animation Utilities
PyQt animasyon yardımcıları - modern micro-interactions için.
"""

from typing import Callable, Optional, List
from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QTimer,
    QObject, QAbstractAnimation, Qt
)
from PyQt6.QtWidgets import (
    QWidget, QGraphicsOpacityEffect, QLabel, QFrame, QVBoxLayout
)

from config.styles import COLORS, SKELETON_BASE, SKELETON_HIGHLIGHT


class ValueAnimator(QObject):
    """
    Sayısal değer geçiş animasyonu.
    Eski değerden yeni değere smooth count-up/down efekti.
    """

    def __init__(
        self,
        label: QLabel,
        formatter: Callable[[float], str],
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self._label = label
        self._formatter = formatter
        self._current = 0.0
        self._target = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._steps_remaining = 0
        self._step_value = 0.0

    def animate(self, start: float, end: float, duration: int = 400):
        """
        Değeri animate et.

        Args:
            start: Başlangıç değeri
            end: Bitiş değeri
            duration: Animasyon süresi (ms)
        """
        self._timer.stop()
        self._current = start
        self._target = end

        # 60fps hedefi
        interval = 16  # ~60fps
        total_steps = max(1, duration // interval)
        self._steps_remaining = total_steps
        self._step_value = (end - start) / total_steps

        self._timer.start(interval)

    def _step(self):
        """Animasyon adımı"""
        if self._steps_remaining <= 0:
            self._timer.stop()
            self._current = self._target
            self._label.setText(self._formatter(self._target))
            return

        self._current += self._step_value
        self._steps_remaining -= 1
        self._label.setText(self._formatter(self._current))

    def stop(self):
        """Animasyonu durdur"""
        self._timer.stop()


class FadeAnimator:
    """
    Fade in/out animasyon yardımcısı.
    Widget'lara opacity animasyonu ekler.
    """

    @staticmethod
    def fade_in(
        widget: QWidget,
        duration: int = 300,
        callback: Optional[Callable] = None
    ) -> QPropertyAnimation:
        """
        Widget'ı fade-in ile göster.

        Args:
            widget: Animate edilecek widget
            duration: Süre (ms)
            callback: Animasyon bittiğinde çağrılacak fonksiyon
        """
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)

        effect.setOpacity(0.0)
        widget.setVisible(True)

        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        if callback:
            anim.finished.connect(callback)

        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        return anim

    @staticmethod
    def fade_out(
        widget: QWidget,
        duration: int = 200,
        callback: Optional[Callable] = None
    ) -> QPropertyAnimation:
        """
        Widget'ı fade-out ile gizle.

        Args:
            widget: Animate edilecek widget
            duration: Süre (ms)
            callback: Animasyon bittiğinde çağrılacak fonksiyon
        """
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(duration)
        anim.setStartValue(effect.opacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)

        def on_finished():
            widget.setVisible(False)
            if callback:
                callback()

        anim.finished.connect(on_finished)
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        return anim


class PulseGlowAnimator(QObject):
    """
    Pulsating glow efekti.
    Kritik değerler için dikkat çekici animasyon.
    """

    def __init__(
        self,
        widget: QWidget,
        color: Optional[str] = None,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self._widget = widget
        self._color = color or COLORS['danger']
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._pulse)
        self._pulse_count = 0
        self._max_pulses = 3
        self._is_bright = False
        self._original_style = ""

    def start(self, pulse_count: int = 3):
        """
        Pulse animasyonunu başlat.

        Args:
            pulse_count: Kaç kez pulse yapılacak
        """
        self._max_pulses = pulse_count * 2  # Her pulse = bright + dim
        self._pulse_count = 0
        self._is_bright = False
        self._original_style = self._widget.styleSheet()
        self._timer.start(300)  # 300ms interval

    def stop(self):
        """Animasyonu durdur ve orijinal stile dön"""
        self._timer.stop()
        self._widget.setStyleSheet(self._original_style)

    def _pulse(self):
        """Pulse adımı"""
        if self._pulse_count >= self._max_pulses:
            self.stop()
            return

        self._is_bright = not self._is_bright
        self._pulse_count += 1

        if self._is_bright:
            # Glow efekti ekle - border rengini değiştir
            glow_style = f"""
                QFrame {{
                    border: 2px solid {self._color};
                }}
            """
            self._widget.setStyleSheet(self._original_style + glow_style)
        else:
            self._widget.setStyleSheet(self._original_style)


class SkeletonWidget(QFrame):
    """
    Skeleton loading placeholder.
    Shimmer efekti ile yükleme durumunu gösterir.
    """

    def __init__(
        self,
        width: int = 100,
        height: int = 24,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._gradient_pos = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._setup_style()

    def _setup_style(self):
        """Temel skeleton stili"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {SKELETON_BASE};
                border-radius: 4px;
            }}
        """)

    def start_animation(self):
        """Shimmer animasyonunu başlat"""
        self._timer.start(50)  # 50ms = 20fps shimmer

    def stop_animation(self):
        """Animasyonu durdur"""
        self._timer.stop()

    def _animate(self):
        """Shimmer efekti - gradient pozisyonunu güncelle"""
        self._gradient_pos = (self._gradient_pos + 5) % 200

        # CSS linear-gradient ile shimmer efekti
        pos1 = self._gradient_pos / 200
        pos2 = min(1, (self._gradient_pos + 50) / 200)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {SKELETON_BASE},
                    stop:{pos1:.2f} {SKELETON_HIGHLIGHT},
                    stop:{pos2:.2f} {SKELETON_BASE}
                );
                border-radius: 4px;
            }}
        """)


class SkeletonGroup(QWidget):
    """
    Birden fazla skeleton elemanını gruplayan container.
    StatWidget için hazır skeleton layout.
    """

    def __init__(
        self,
        layout_type: str = "stat",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._skeletons: List[SkeletonWidget] = []
        self._setup_layout(layout_type)

    def _setup_layout(self, layout_type: str):
        """Layout tipine göre skeleton'ları oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        if layout_type == "stat":
            # StatWidget için: değer + trend + açıklama
            value_skeleton = SkeletonWidget(80, 32)
            trend_skeleton = SkeletonWidget(50, 16)
            desc_skeleton = SkeletonWidget(120, 14)

            layout.addStretch()
            layout.addWidget(
                value_skeleton,
                alignment=Qt.AlignmentFlag.AlignCenter
            )
            layout.addWidget(
                trend_skeleton,
                alignment=Qt.AlignmentFlag.AlignCenter
            )
            layout.addWidget(
                desc_skeleton,
                alignment=Qt.AlignmentFlag.AlignCenter
            )
            layout.addStretch()

            self._skeletons = [value_skeleton, trend_skeleton, desc_skeleton]

        elif layout_type == "list":
            # Liste widget için: 3 satır
            for _ in range(3):
                item = SkeletonWidget(180, 20)
                layout.addWidget(item)
                self._skeletons.append(item)
            layout.addStretch()

    def start_animation(self):
        """Tüm skeleton'ların animasyonunu başlat"""
        for skeleton in self._skeletons:
            skeleton.start_animation()

    def stop_animation(self):
        """Tüm animasyonları durdur"""
        for skeleton in self._skeletons:
            skeleton.stop_animation()


class StaggeredAnimator:
    """
    Sıralı (staggered) animasyon yöneticisi.
    Widget listesini belirli aralıklarla animate eder.
    """

    @staticmethod
    def fade_in_sequence(
        widgets: List[QWidget],
        delay: int = 50,
        duration: int = 300
    ):
        """
        Widget'ları sırayla fade-in yap.

        Args:
            widgets: Animate edilecek widget listesi
            delay: Her widget arasındaki gecikme (ms)
            duration: Her animasyonun süresi (ms)
        """
        for i, widget in enumerate(widgets):
            QTimer.singleShot(
                i * delay,
                lambda w=widget, d=duration: FadeAnimator.fade_in(w, d)
            )
