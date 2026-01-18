"""
Akıllı İş ERP - Dashboard Sayfası
Doğru Logo ile
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QGridLayout,
    QScrollArea,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QLinearGradient,
    QPainterPath,
    QPixmap,
)
from PyQt6.QtSvg import QSvgRenderer

import os

from config import APP_NAME, APP_VERSION
from config.themes import get_theme, ThemeManager


class DashboardLogo(QWidget):
    """Dashboard için büyük logo"""

    def __init__(self, size: int = 56, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color1 = QColor("#6366f1")
        color2 = QColor("#8b5cf6")
        color3 = QColor("#a855f7")

        gradient = QLinearGradient(0, 0, self._size, self._size)
        gradient.setColorAt(0, color1)
        gradient.setColorAt(0.5, color2)
        gradient.setColorAt(1, color3)

        center = self._size / 2
        scale = self._size / 100

        # Dış kesikli daire
        pen = QPen(QBrush(gradient), 5 * scale)
        pen.setStyle(Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([6, 3])
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        r1 = 38 * scale
        painter.drawEllipse(QPointF(center, center), r1, r1)

        # İç düz daire
        pen2 = QPen(QBrush(gradient), 3.5 * scale)
        pen2.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen2)
        r2 = 25 * scale
        painter.drawEllipse(QPointF(center, center), r2, r2)

        # Merkez dolu daire
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        r3 = 12 * scale
        painter.drawEllipse(QPointF(center, center), r3, r3)

        # Oklar
        self._draw_arrow(painter, center, 12 * scale, 0, color1, scale)
        self._draw_arrow(painter, 88 * scale, center, 90, color2, scale)
        self._draw_arrow(painter, center, 88 * scale, 180, color3, scale)
        self._draw_arrow(painter, 12 * scale, center, 270, color1, scale)

    def _draw_arrow(self, painter, x, y, angle, color, scale):
        painter.save()
        painter.translate(x, y)
        painter.rotate(angle)

        size = 8 * scale

        path = QPainterPath()
        path.moveTo(0, -size)
        path.lineTo(size * 0.5, 0)
        path.lineTo(-size * 0.5, 0)
        path.closeSubpath()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color))
        painter.drawPath(path)

        painter.restore()


class StatCard(QFrame):
    """İstatistik kartı"""

    def __init__(
        self,
        icon: str,
        title: str,
        value: str,
        subtitle: str = "",
        color: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self.icon = icon
        self.title = title
        self.color = color
        self.setup_ui(value, subtitle)

    def setup_ui(self, value: str, subtitle: str):
        t = get_theme()
        color = self.color or t.accent_primary
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()

        icon_label = QLabel(self.icon)
        icon_label.setFixedSize(52, 52)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(icon_label)

        header.addStretch()

        trend_label = QLabel("↑ 12%")
        header.addWidget(trend_label)

        layout.addLayout(header)

        value_label = QLabel(value)
        layout.addWidget(value_label)

        title_label = QLabel(self.title)
        layout.addWidget(title_label)

        if subtitle:
            sub_label = QLabel(subtitle)
            layout.addWidget(sub_label)


class QuickActionCard(QFrame):
    """Hızlı işlem kartı"""

    def __init__(
        self, icon: str, title: str, description: str, color: str = None, parent=None
    ):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._color = color
        self._setup_ui(icon, title, description)

    def _setup_ui(self, icon: str, title: str, description: str):
        t = get_theme()
        color = self._color or t.accent_primary
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        icon_label = QLabel(icon)
        icon_label.setFixedSize(44, 44)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel(title)
        text_layout.addWidget(title_label)

        desc_label = QLabel(description)
        text_layout.addWidget(desc_label)

        layout.addLayout(text_layout)
        layout.addStretch()

        arrow = QLabel("→")
        layout.addWidget(arrow)


class ActivityItem(QFrame):
    """Son aktivite öğesi"""

    def __init__(
        self, icon: str, title: str, time: str, color: str = None, parent=None
    ):
        super().__init__(parent)

        t = get_theme()
        color = color or t.accent_primary
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        icon_label = QLabel(icon)
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        layout.addWidget(title_label)

        layout.addStretch()

        time_label = QLabel(time)
        layout.addWidget(time_label)


class DashboardPage(QWidget):
    """Ana Dashboard sayfası"""

    page_title = "Dashboard"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        ThemeManager.register_callback(self._on_theme_changed)

    def _on_theme_changed(self, theme):
        pass

    def setup_ui(self):
        t = get_theme()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # === HEADER ===
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(32, 28, 32, 28)
        header_layout.setSpacing(24)

        # Logo container
        logo_container = QFrame()
        logo_container.setFixedSize(80, 80)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(10, 10, 10, 10)

        # SVG Logo
        logo_label = QLabel()
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "resources", "icons", "logo.svg"
        )
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled = pixmap.scaled(
                60,
                60,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo_label.setPixmap(scaled)
        else:
            logo_label.setText("📦")
            logo_label.setStyleSheet("font-size: 40px;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)

        header_layout.addWidget(logo_container)

        # Hoşgeldin
        welcome_layout = QVBoxLayout()
        welcome_layout.setSpacing(4)

        welcome_title = QLabel(f"Hoş Geldiniz, {APP_NAME}")
        welcome_layout.addWidget(welcome_title)

        welcome_sub = QLabel("İşletmenizin güncel durumuna göz atın")
        welcome_layout.addWidget(welcome_sub)

        from datetime import datetime

        date_str = datetime.now().strftime("%d %B %Y, %A")
        date_label = QLabel(f"📅 {date_str}")
        welcome_layout.addWidget(date_label)

        header_layout.addLayout(welcome_layout)
        header_layout.addStretch()

        layout.addWidget(header_frame)

        # === İSTATİSTİKLER ===
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        stats = [
            ("📦", "Toplam Ürün", "1,248", "Aktif stok kartı", t.accent_primary),
            ("🏭", "Depolar", "5", "Aktif depo", t.info),
            ("📊", "Stok Değeri", "₺2.4M", "Toplam envanter", t.success),
            ("⚠️", "Kritik Stok", "23", "Dikkat gerektiren", t.warning),
        ]

        for icon, title, value, subtitle, color in stats:
            card = StatCard(icon, title, value, subtitle, color)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            card.setFixedHeight(160)
            stats_layout.addWidget(card)

        layout.addLayout(stats_layout)

        # === HIZLI İŞLEMLER VE AKTİVİTELER ===
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)

        # Hızlı İşlemler
        quick_frame = QFrame()
        quick_layout = QVBoxLayout(quick_frame)
        quick_layout.setContentsMargins(20, 20, 20, 20)
        quick_layout.setSpacing(12)

        quick_title = QLabel("⚡ Hızlı İşlemler")
        quick_layout.addWidget(quick_title)

        actions = [
            ("📦", "Yeni Stok Kartı", "Hızlıca ürün ekleyin", t.accent_primary),
            ("📥", "Stok Girişi", "Depoya ürün girişi", t.success),
            ("📤", "Stok Çıkışı", "Depodan ürün çıkışı", t.error),
            ("🔄", "Transfer", "Depolar arası transfer", t.info),
            ("📋", "Sayım Başlat", "Envanter sayımı", t.warning),
        ]

        for icon, title, desc, color in actions:
            action_card = QuickActionCard(icon, title, desc, color)
            quick_layout.addWidget(action_card)

        quick_layout.addStretch()
        bottom_layout.addWidget(quick_frame, 1)

        # Aktiviteler
        activity_frame = QFrame()
        activity_layout = QVBoxLayout(activity_frame)
        activity_layout.setContentsMargins(20, 20, 20, 20)
        activity_layout.setSpacing(8)

        activity_title = QLabel("🕐 Son Aktiviteler")
        activity_layout.addWidget(activity_title)

        activities = [
            ("📥", "Hammadde girişi yapıldı - 500 KG", "2 dk önce", t.success),
            ("📤", "Mamul çıkışı - Sipariş #1234", "15 dk önce", t.error),
            ("🔄", "Depo transferi tamamlandı", "1 saat önce", t.info),
            ("📋", "Sayım #45 onaylandı", "3 saat önce", t.accent_primary),
            ("⚠️", "Düşük stok uyarısı - PLT-001", "5 saat önce", t.warning),
            ("📦", "Yeni ürün eklendi - YM-2024", "Dün", t.accent_secondary),
        ]

        for icon, title, time, color in activities:
            item = ActivityItem(icon, title, time, color)
            activity_layout.addWidget(item)

        activity_layout.addStretch()

        see_all = QLabel("Tümünü Gör →")
        see_all.setCursor(Qt.CursorShape.PointingHandCursor)
        activity_layout.addWidget(see_all, alignment=Qt.AlignmentFlag.AlignRight)

        bottom_layout.addWidget(activity_frame, 1)

        layout.addLayout(bottom_layout)

        scroll.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
