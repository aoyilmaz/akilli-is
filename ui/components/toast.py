"""
Akıllı İş ERP - Modern Toast Bildirim Sistemi
Bu modül, ekranın sağ alt köşesinde veya durum çubuğu üzerinde yüzen,
animasyonlu ve modern bildirim (toast) pencerelerini yönetir.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QGraphicsDropShadowEffect,
    QApplication,
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, QTimer, QEasingCurve
from PyQt6.QtGui import QColor
from config.themes import get_theme


class ToastNotification(QWidget):
    """Bireysel Bildirim Penceresi"""

    def __init__(self, message, level="INFO", parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.message = message
        self.level = level.upper()
        self.t = get_theme()

        self._setup_ui()
        self._setup_animation()

    def _setup_ui(self):
        # Ana Konteyner
        self.container = QWidget(self)
        self.container.setObjectName("ToastContainer")

        # Renk Belirleme
        colors = {
            "SUCCESS": self.t.success,
            "ERROR": self.t.error,
            "WARNING": self.t.warning,
            "INFO": self.t.accent_primary,
        }
        accent_color = colors.get(self.level, self.t.accent_primary)

        # İkon Seçimi
        icons = {
            "SUCCESS": "✅",
            "ERROR": "⛔",
            "WARNING": "⚠️",
            "INFO": "ℹ️",
        }
        icon_text = icons.get(self.level, "ℹ️")

        # Stil
        # Cam efekti (Glassmorphism) için arka planı hafif şeffaf yapıyoruz
        bg_rgb = QColor(self.t.bg_secondary).getRgb()
        style = f"""
            QWidget#ToastContainer {{
                background-color: rgba({bg_rgb[0]}, {bg_rgb[1]}, 
                                       {bg_rgb[2]}, 230);
                border: 1px solid {self.t.border};
                border-left: 4px solid {accent_color};
                border-radius: 8px;
            }}
            QLabel {{
                color: {self.t.text_primary};
                background: transparent;
                font-size: 13px;
                padding: 10px;
            }}
            QLabel#IconLabel {{
                font-size: 16px;
                padding-right: 0px;
            }}
        """
        self.container.setStyleSheet(style)

        # Layout
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(10)

        icon_label = QLabel(icon_text)
        icon_label.setObjectName("IconLabel")
        layout.addWidget(icon_label)

        self.msg_label = QLabel(self.message)
        self.msg_label.setWordWrap(True)
        layout.addWidget(self.msg_label)

        # Gölge Efekti
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)

        # Boyutlandırma
        self.container.adjustSize()
        self.setFixedSize(self.container.size())

    def _setup_animation(self):
        # Fade In Animasyonu
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(300)
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Slide Animasyonu (Yalnızca gösterilirken kullanılacak)
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.pos_anim.setDuration(400)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutBack)

    def show_animated(self, target_pos):
        self.move(target_pos + QPoint(40, 0))  # Hafif sağdan gelsin
        self.show()
        self.opacity_anim.start()

        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(target_pos)
        self.pos_anim.start()

        # Kapanma Timer'ı
        QTimer.singleShot(5000, self.hide_animated)

    def hide_animated(self):
        self.opacity_anim.setDirection(QPropertyAnimation.Direction.Backward)
        self.opacity_anim.finished.connect(self.close)
        self.opacity_anim.start()


class NotificationManager:
    """Bildirimleri Yöneten ve İstifleyen Sınıf"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(NotificationManager, cls).__new__(cls)
            cls._instance.notifications = []
            cls._instance.offset_y = 60  # Status bar üstünden başla
        return cls._instance

    def notify(self, message, level="INFO"):
        toast = ToastNotification(message, level)
        self.notifications.append(toast)

        # Pozisyonu hesapla (Sağ Alt)
        screen_geo = QApplication.primaryScreen().availableGeometry()
        margin = 20

        # Mevcut bildirimlerin yüksekliğine göre yeni konumu belirle
        current_y_offset = margin + self.offset_y
        for t in self.notifications[:-1]:
            current_y_offset += t.height() + 10

        target_x = screen_geo.right() - toast.width() - margin
        target_y = screen_geo.bottom() - current_y_offset - toast.height()

        # Debug print
        print(f"DEBUG: Toast: {message} -> Pos: {target_x}, {target_y}")

        toast.show_animated(QPoint(target_x, target_y))

        # Toast kapandığında listeden çıkar ve diğerlerini kaydır (opsiyonel)
        toast.destroyed.connect(lambda: self._on_destroyed(toast))

    def _on_destroyed(self, toast):
        if toast in self.notifications:
            self.notifications.remove(toast)
            # Not: Diğerlerini aşağı kaydırmak için ek mantık eklenebilir
            # Ancak basitlik için şimdilik sadece listeden çıkarıyoruz.


# Singleton Erişimi
_manager = None


def show_toast(message, level="INFO"):
    global _manager
    if _manager is None:
        _manager = NotificationManager()
    _manager.notify(message, level)
