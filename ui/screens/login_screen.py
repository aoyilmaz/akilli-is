"""
Akıllı İş ERP - Login Screen
Minimalist Glass Morphism tasarımlı modern login ekranı
"""

import os
import math
import random
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QFrame,
    QGraphicsOpacityEffect,
)
from PyQt6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    pyqtSignal,
    QTimer,
    QPointF,
)
from PyQt6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QLinearGradient,
    QRadialGradient,
    QPixmap,
)

from config import APP_NAME, APP_VERSION

try:
    import qtawesome as qta

    HAS_QTAWESOME = True
except ImportError:
    HAS_QTAWESOME = False


class FloatingOrb:
    """Yüzen ışık küresi"""

    def __init__(self, x, y, radius, color, speed):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.speed = speed
        self.angle = random.uniform(0, 2 * math.pi)
        self.amplitude = random.uniform(20, 50)

    def update(self):
        self.angle += self.speed
        self.x += math.sin(self.angle) * 0.5
        self.y += math.cos(self.angle * 0.7) * 0.3


class GlassMorphismBackground(QWidget):
    """Gradient arka plan + yüzen ışık küreleri"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.orbs = []
        self._init_orbs()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(50)

    def _init_orbs(self):
        colors = [
            QColor(99, 102, 241, 80),  # indigo
            QColor(139, 92, 246, 60),  # violet
            QColor(168, 85, 247, 70),  # purple
            QColor(59, 130, 246, 50),  # blue
            QColor(236, 72, 153, 40),  # pink
        ]
        for _ in range(8):
            self.orbs.append(
                FloatingOrb(
                    x=random.uniform(0, 1200),
                    y=random.uniform(0, 800),
                    radius=random.uniform(80, 200),
                    color=random.choice(colors),
                    speed=random.uniform(0.01, 0.03),
                )
            )

    def _animate(self):
        for orb in self.orbs:
            orb.update()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Gradient arka plan
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor("#0f0c29"))
        gradient.setColorAt(0.5, QColor("#302b63"))
        gradient.setColorAt(1.0, QColor("#24243e"))
        painter.fillRect(self.rect(), gradient)

        # Yüzen ışık küreleri
        for orb in self.orbs:
            radial = QRadialGradient(orb.x, orb.y, orb.radius)
            radial.setColorAt(0, orb.color)
            radial.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(radial)
            painter.drawEllipse(QPointF(orb.x, orb.y), orb.radius, orb.radius)

    def stop_animation(self):
        self._timer.stop()


class AnimatedLogo(QWidget):
    """Yavaş dönen logo animasyonu"""

    def __init__(self, size=80, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size
        self._rotation = 0

        # Logo dosyasını yükle
        self._logo_pixmap = None
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "resources", "icons", "logo.png"
        )
        if os.path.exists(logo_path):
            self._logo_pixmap = QPixmap(logo_path)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_rotation)
        self._timer.start(50)

    def _update_rotation(self):
        self._rotation = (self._rotation + 1) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center = self._size / 2

        # Gradient
        gradient = QLinearGradient(0, 0, self._size, self._size)
        gradient.setColorAt(0, QColor("#6366f1"))
        gradient.setColorAt(0.5, QColor("#8b5cf6"))
        gradient.setColorAt(1, QColor("#a855f7"))

        # Dönen dış kesikli çember
        painter.save()
        painter.translate(center, center)
        painter.rotate(self._rotation)

        pen = QPen(QBrush(gradient), 3)
        pen.setStyle(Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([6, 4])
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(0, 0), center * 0.85, center * 0.85)
        painter.restore()

        # Logo varsa çiz
        if self._logo_pixmap:
            logo_size = int(self._size * 0.65)
            scaled = self._logo_pixmap.scaled(
                logo_size,
                logo_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = int(center - scaled.width() / 2)
            y = int(center - scaled.height() / 2)
            painter.drawPixmap(x, y, scaled)
        else:
            # Fallback merkez daire
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gradient))
            r = center * 0.25
            painter.drawEllipse(QPointF(center, center), r, r)

    def stop_animation(self):
        self._timer.stop()


class GlassLineEdit(QLineEdit):
    """Glass morphism stil input"""

    def __init__(self, placeholder="", icon=None, is_password=False, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._icon = icon
        self._is_password = is_password

        if is_password:
            self.setEchoMode(QLineEdit.EchoMode.Password)

        self._setup_style()

    def _setup_style(self):
        padding_left = "45px" if self._icon else "18px"

        self.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                padding: 14px 18px 14px {padding_left};
                font-size: 14px;
                color: white;
                min-height: 22px;
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(139, 92, 246, 0.6);
                background-color: rgba(255, 255, 255, 0.12);
            }}
            QLineEdit:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QLineEdit::placeholder {{
                color: rgba(255, 255, 255, 0.4);
            }}
        """
        )

    def paintEvent(self, event):
        super().paintEvent(event)

        if self._icon and HAS_QTAWESOME:
            painter = QPainter(self)
            icon = qta.icon(self._icon, color="rgba(255, 255, 255, 0.5)")
            pixmap = icon.pixmap(18, 18)
            y = (self.height() - 18) // 2
            painter.drawPixmap(15, y, pixmap)


class GlassButton(QPushButton):
    """Glass morphism gradient buton"""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(99, 102, 241, 0.9),
                    stop:0.5 rgba(139, 92, 246, 0.9),
                    stop:1 rgba(168, 85, 247, 0.9));
                color: white;
                border: none;
                border-radius: 12px;
                padding: 14px 40px;
                font-size: 15px;
                font-weight: 600;
                min-height: 22px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(124, 127, 242, 1),
                    stop:0.5 rgba(157, 123, 247, 1),
                    stop:1 rgba(180, 110, 248, 1));
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(85, 88, 232, 1),
                    stop:0.5 rgba(122, 77, 245, 1),
                    stop:1 rgba(151, 69, 246, 1));
            }
        """
        )


class GlassCard(QFrame):
    """Glass morphism kart container"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self.setStyleSheet(
            """
            QFrame#GlassCard {
                background-color: rgba(255, 255, 255, 15);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 24px;
            }
        """
        )


class LoginScreen(QWidget):
    """Minimalist Glass Morphism login ekranı"""

    login_successful = pyqtSignal(object)
    forgot_password = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMinimumSize(1100, 700)

        self._setup_ui()
        self._center_on_screen()

    def _setup_ui(self):
        # Ana layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Arka plan widget
        self.background = GlassMorphismBackground()

        # Arka planı layout'a ekle
        bg_layout = QVBoxLayout(self.background)
        bg_layout.setContentsMargins(0, 0, 0, 0)

        # === İÇERİK CONTAINER ===
        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Glass Card
        self.card = GlassCard()
        self.card.setFixedSize(420, 580)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(45, 40, 45, 40)
        card_layout.setSpacing(0)

        # Kapat butonu
        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.6);
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 16px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.8);
                color: white;
            }
        """
        )
        close_btn.clicked.connect(self._on_close)

        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        card_layout.addLayout(close_layout)

        card_layout.addSpacing(10)

        # Logo
        self.logo = AnimatedLogo(80)
        card_layout.addWidget(self.logo, alignment=Qt.AlignmentFlag.AlignCenter)

        card_layout.addSpacing(15)

        # Başlık
        title = QLabel(APP_NAME)
        title.setStyleSheet(
            """
            font-size: 26px;
            font-weight: bold;
            color: white;
            background: transparent;
        """
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        # Alt başlık
        subtitle = QLabel("Enterprise Resource Planning")
        subtitle.setStyleSheet(
            """
            font-size: 13px;
            color: rgba(255, 255, 255, 0.5);
            background: transparent;
            margin-bottom: 25px;
        """
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(20)

        # Kullanıcı adı
        self.username_input = GlassLineEdit(
            placeholder="Kullanıcı Adı", icon="fa5s.user"
        )
        card_layout.addWidget(self.username_input)

        card_layout.addSpacing(16)

        # Şifre
        self.password_input = GlassLineEdit(
            placeholder="Şifre", icon="fa5s.lock", is_password=True
        )
        self.password_input.returnPressed.connect(self._on_login)
        card_layout.addWidget(self.password_input)

        card_layout.addSpacing(16)

        # Beni hatırla ve Şifremi unuttum
        options_layout = QHBoxLayout()

        self.remember_check = QCheckBox("Beni Hatırla")
        self.remember_check.setStyleSheet(
            """
            QCheckBox {
                color: rgba(255, 255, 255, 0.7);
                font-size: 13px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 5px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                background: rgba(255, 255, 255, 0.05);
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a855f7);
                border-color: #6366f1;
            }
            QCheckBox::indicator:hover {
                border-color: rgba(255, 255, 255, 0.5);
            }
        """
        )
        options_layout.addWidget(self.remember_check)

        options_layout.addStretch()

        forgot_btn = QPushButton("Şifremi Unuttum")
        forgot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        forgot_btn.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: rgba(168, 85, 247, 0.9);
                font-size: 13px;
                border: none;
                padding: 0;
            }
            QPushButton:hover {
                color: #c084fc;
            }
        """
        )
        forgot_btn.clicked.connect(lambda: self.forgot_password.emit())
        options_layout.addWidget(forgot_btn)

        card_layout.addLayout(options_layout)

        card_layout.addSpacing(25)

        # Giriş butonu
        self.login_btn = GlassButton("Giriş Yap")
        self.login_btn.clicked.connect(self._on_login)
        card_layout.addWidget(self.login_btn)

        # Hata mesajı
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(
            """
            color: #f87171;
            font-size: 13px;
            background: transparent;
            padding: 10px 0;
        """
        )
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.hide()
        card_layout.addWidget(self.error_label)

        card_layout.addStretch()

        # Versiyon
        version = QLabel(f"v{APP_VERSION}")
        version.setStyleSheet(
            """
            font-size: 11px;
            color: rgba(255, 255, 255, 0.3);
            background: transparent;
        """
        )
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(version)

        content_layout.addWidget(self.card)
        bg_layout.addLayout(content_layout)

        main_layout.addWidget(self.background)

    def _center_on_screen(self):
        from PyQt6.QtWidgets import QApplication

        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def showEvent(self, event):
        super().showEvent(event)
        self.username_input.setFocus()

    def _on_login(self):
        """Login işlemi"""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username:
            self._show_error("Kullanıcı adı gerekli")
            self.username_input.setFocus()
            return

        if not password:
            self._show_error("Şifre gerekli")
            self.password_input.setFocus()
            return

        # Veritabanından kullanıcı doğrulama
        try:
            from database.base import get_session
            from database.models.user import User
            from core.auth_service import AuthService

            session = get_session()
            user = session.query(User).filter(User.username == username).first()

            if user and user.check_password(password):
                if not user.is_active:
                    self._show_error("Hesabınız devre dışı bırakılmış")
                    session.close()
                    return

                # AuthService'e kullanıcıyı kaydet
                AuthService.login(user)

                session.close()
                self._cleanup()
                self.login_successful.emit(user)
            else:
                self._show_error("Kullanıcı adı veya şifre hatalı")
                self.password_input.clear()
                self.password_input.setFocus()
                session.close()

        except Exception:
            # Development modunda: admin/admin ile giriş
            if username == "admin" and password == "admin":
                self._cleanup()
                # Development mode - no AuthService login
                self.login_successful.emit(None)
            else:
                self._show_error("Bağlantı hatası")

    def _show_error(self, message: str):
        """Hata mesajı göster"""
        self.error_label.setText(message)
        self.error_label.show()

        QTimer.singleShot(5000, self.error_label.hide)

    def _cleanup(self):
        """Animasyonları durdur"""
        self.background.stop_animation()
        self.logo.stop_animation()

    def _on_close(self):
        """Uygulamayı kapat"""
        self._cleanup()
        from PyQt6.QtWidgets import QApplication

        QApplication.quit()

    # Pencere sürükleme
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            global_pos = event.globalPosition().toPoint()
            self._drag_pos = global_pos - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            if hasattr(self, "_drag_pos"):
                new_pos = event.globalPosition().toPoint() - self._drag_pos
                self.move(new_pos)
                event.accept()

    def closeEvent(self, event):
        self._cleanup()
        super().closeEvent(event)
