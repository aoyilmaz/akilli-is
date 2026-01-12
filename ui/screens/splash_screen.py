"""
Akıllı İş ERP - Splash Screen
Animasyonlu logo ve progress bar ile modern splash ekranı
"""

import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QGraphicsOpacityEffect,
)
from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    pyqtSignal,
    QPointF,
)
from PyQt6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QLinearGradient,
    QFont,
    QPixmap,
)

from config import APP_NAME, APP_VERSION
from config.themes import get_theme


class AnimatedLogo(QWidget):
    """Dönen kesikli çember animasyonlu logo widget"""

    def __init__(self, size=150, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size
        self._rotation = 0
        self._inner_rotation = 0

        # Logo dosyasını yükle
        self._logo_pixmap = None
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "resources", "icons", "logo.png"
        )
        if os.path.exists(logo_path):
            self._logo_pixmap = QPixmap(logo_path)

        # Rotasyon animasyonu
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_rotation)
        self._timer.start(30)  # ~33 FPS

    def _update_rotation(self):
        self._rotation = (self._rotation + 2) % 360
        self._inner_rotation = (self._inner_rotation - 1) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center = self._size / 2

        # Arka plan gradient çemberi (dış)
        outer_radius = self._size * 0.45

        # Gradient oluştur
        gradient = QLinearGradient(0, 0, self._size, self._size)
        gradient.setColorAt(0, QColor("#6366f1"))  # indigo
        gradient.setColorAt(0.5, QColor("#8b5cf6"))  # violet
        gradient.setColorAt(1, QColor("#a855f7"))  # purple

        # Dönen kesikli çember
        painter.save()
        painter.translate(center, center)
        painter.rotate(self._rotation)

        pen = QPen(QBrush(gradient), 4)
        pen.setStyle(Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([8, 4])
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(0, 0), outer_radius, outer_radius)

        painter.restore()

        # İç çember (ters yönde döner)
        inner_radius = self._size * 0.32

        painter.save()
        painter.translate(center, center)
        painter.rotate(self._inner_rotation)

        pen2 = QPen(QBrush(gradient), 2)
        pen2.setStyle(Qt.PenStyle.CustomDashLine)
        pen2.setDashPattern([4, 6])
        pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen2)
        painter.drawEllipse(QPointF(0, 0), inner_radius, inner_radius)

        painter.restore()

        # Merkez dolu daire
        center_radius = self._size * 0.15
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(center, center), center_radius, center_radius)

        # Logo varsa ortaya çiz
        if self._logo_pixmap:
            logo_size = int(self._size * 0.5)
            scaled_logo = self._logo_pixmap.scaled(
                logo_size, logo_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            x = int(center - scaled_logo.width() / 2)
            y = int(center - scaled_logo.height() / 2)
            painter.drawPixmap(x, y, scaled_logo)

    def stop_animation(self):
        self._timer.stop()


class SplashScreen(QWidget):
    """Modern splash screen with animated logo and progress bar"""

    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(500, 400)

        self._progress = 0
        self._messages = [
            "Başlatılıyor...",
            "Veritabanı bağlantısı kuruluyor...",
            "Modüller yükleniyor...",
            "Arayüz hazırlanıyor...",
            "Tamamlandı!"
        ]

        self._setup_ui()
        self._center_on_screen()

        # Progress timer
        self._progress_timer = QTimer(self)
        self._progress_timer.timeout.connect(self._update_progress)

    def _setup_ui(self):
        t = get_theme()

        # Ana container
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # İçerik container (rounded background)
        self.content = QWidget()
        self.content.setStyleSheet(f"""
            QWidget {{
                background-color: {t.bg_primary};
                border-radius: 20px;
                border: 1px solid {t.border};
            }}
        """)

        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(20)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Animasyonlu logo
        self.logo = AnimatedLogo(150)
        content_layout.addWidget(self.logo, alignment=Qt.AlignmentFlag.AlignCenter)

        # Uygulama adı
        self.title = QLabel(APP_NAME)
        self.title.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {t.text_primary};
            background: transparent;
            border: none;
        """)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.title)

        # Alt başlık
        self.subtitle = QLabel("Enterprise Resource Planning")
        self.subtitle.setStyleSheet(f"""
            font-size: 14px;
            color: {t.text_muted};
            background: transparent;
            border: none;
        """)
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.subtitle)

        content_layout.addSpacing(20)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {t.bg_tertiary};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:0.5 #8b5cf6, stop:1 #a855f7);
                border-radius: 3px;
            }}
        """)
        content_layout.addWidget(self.progress_bar)

        # Durum mesajı
        self.status_label = QLabel(self._messages[0])
        self.status_label.setStyleSheet(f"""
            font-size: 12px;
            color: {t.text_secondary};
            background: transparent;
            border: none;
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.status_label)

        content_layout.addStretch()

        # Versiyon
        self.version = QLabel(f"v{APP_VERSION}")
        self.version.setStyleSheet(f"""
            font-size: 11px;
            color: {t.text_muted};
            background: transparent;
            border: none;
        """)
        self.version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.version)

        layout.addWidget(self.content)

        # Fade-in efekti
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)

        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(500)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _center_on_screen(self):
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def start(self):
        """Splash screen'i başlat"""
        self.show()
        self.fade_in.start()
        self._progress_timer.start(50)  # Her 50ms'de güncelle

    def _update_progress(self):
        self._progress += 2
        self.progress_bar.setValue(self._progress)

        # Mesaj güncelle
        if self._progress < 20:
            idx = 0
        elif self._progress < 40:
            idx = 1
        elif self._progress < 60:
            idx = 2
        elif self._progress < 80:
            idx = 3
        else:
            idx = 4

        self.status_label.setText(self._messages[idx])

        if self._progress >= 100:
            self._progress_timer.stop()
            self._finish()

    def _finish(self):
        """Splash screen'i kapat ve sinyali gönder"""
        # Fade-out
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out.finished.connect(self._on_fade_out_finished)
        self.fade_out.start()

    def _on_fade_out_finished(self):
        self.logo.stop_animation()
        self.finished.emit()
        self.close()

    def set_progress(self, value: int, message: str = None):
        """Manuel progress güncelleme"""
        self._progress = min(value, 100)
        self.progress_bar.setValue(self._progress)
        if message:
            self.status_label.setText(message)
