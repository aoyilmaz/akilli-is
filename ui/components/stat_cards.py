"""
Akıllı İş ERP - Ortak İstatistik Kartları
Tüm modüllerde kullanılabilecek modern görünümlü istatistik kartları
Global tema (theme.qss) kullanır - inline stil yoktur
"""

from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QScrollArea,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QSize
import qtawesome as qta
from config.styles import TEXT_MUTED, STAT_COLORS, ACCENT


class MiniStatCard(QFrame):
    """
    Kompakt istatistik kartı - Liste sayfaları için
    Global tema üzerinden stillendirilir (class="stat-card")

    Kullanım:
        card = MiniStatCard("� Taslak", "5", "warning")
    """

    COLOR_CLASSES = {
        "primary": "value-primary",
        "success": "value-success",
        "warning": "value-warning",
        "error": "value-error",
        "info": "value-info",
    }

    def __init__(
        self,
        title: str,
        value: str,
        color_type: str = "primary",
        orientation: str = "vertical",
        icon: str = "",
        icon_color: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._title = title
        self._value = value
        self._color_type = color_type
        self._orientation = orientation
        self._icon = icon
        self._icon_color = icon_color or TEXT_MUTED
        self._setup_ui()

    def _setup_ui(self):
        # QSS class'ı ayarla
        self.setProperty("class", "stat-card")

        if self._orientation == "horizontal":
            layout = QHBoxLayout(self)
            layout.setContentsMargins(12, 8, 12, 8)
            layout.setSpacing(8)

            # İkon
            if self._icon and self._icon.startswith("ph."):
                icon_lbl = QLabel()
                icon_lbl.setPixmap(
                    qta.icon(self._icon, color=self._icon_color).pixmap(18, 18)
                )
                layout.addWidget(icon_lbl)

            # Başlık
            title_label = QLabel(self._title)
            title_label.setProperty("class", "card-title")
            # Horizontal modda başlık fontunu biraz daha küçük tutmak isteyebiliriz
            # ama şimdilik standart bırakalım
            layout.addWidget(title_label)

            # Arada boşluk bırakmak istenirse:
            # layout.addStretch()

            # Değer
            self.value_label = QLabel(self._value)
            self.value_label.setProperty("class", "card-value")
            # Yatay modda değerin fontu çok büyük olmamalı, CSS ile ayarlanabilir
            # ama biz renk sınıfını ekleyelim
            color_class = self.COLOR_CLASSES.get(self._color_type, "value-primary")
            self.value_label.setProperty("class", color_class)
            layout.addWidget(self.value_label)

        else:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(12, 10, 12, 10)  # Reduced padding
            layout.setSpacing(4)  # Reduced spacing

            # Başlık satırı (İkon + Title)
            h_layout = QHBoxLayout()
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.setSpacing(8)

            h_layout.addStretch()

            if self._icon and self._icon.startswith("ph."):
                icon_lbl = QLabel()
                # Rengi title rengine yakın yapalım
                icon_lbl.setPixmap(
                    qta.icon(self._icon, color=self._icon_color).pixmap(
                        16, 16
                    )  # Slightly smaller icon
                )
                h_layout.addWidget(icon_lbl)

            title_label = QLabel(self._title)
            title_label.setProperty("class", "card-title")
            h_layout.addWidget(title_label)

            h_layout.addStretch()

            layout.addLayout(h_layout)

            # Değer
            self.value_label = QLabel(self._value)
            self.value_label.setProperty("class", "card-value")
            self.value_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )  # Center alignment
            # Renk class'ı
            color_class = self.COLOR_CLASSES.get(self._color_type, "value-primary")
            self.value_label.setProperty("class", color_class)
            layout.addWidget(self.value_label)

    def update_value(self, value: str, color_type: str = None):
        """Kart değerini güncelle"""
        self._value = value
        self.value_label.setText(value)
        if color_type:
            self._color_type = color_type
            color_class = self.COLOR_CLASSES.get(color_type, "value-primary")
            self.value_label.setProperty("class", color_class)
            # Style'ı yeniden uygula
            self.value_label.style().unpolish(self.value_label)
            self.value_label.style().polish(self.value_label)


class StatCard(QFrame):
    """
    Dashboard istatistik kartı - Büyük kartlar
    Global tema üzerinden stillendirilir (class="dashboard-card")

    Kullanım:
        card = StatCard("📦", "Toplam Ürün", "1,248", "Aktif stok", "primary")
    """

    ICON_CLASSES = {
        "primary": "icon-primary",
        "success": "icon-success",
        "warning": "icon-warning",
        "error": "icon-error",
        "info": "icon-info",
    }

    def __init__(
        self,
        icon: str,
        title: str,
        value: str,
        subtitle: str = "",
        color_type: str = "primary",
        show_trend: bool = False,
        trend_value: str = "",
        trend_positive: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.icon = icon
        self.title = title
        self._value = value
        self._subtitle = subtitle
        self._color_type = color_type
        self._show_trend = show_trend
        self._trend_value = trend_value
        self._trend_positive = trend_positive
        self._setup_ui()

    def _setup_ui(self):
        # QSS class'ı ayarla
        self.setProperty("class", "dashboard-card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header - Icon ve Trend
        header = QHBoxLayout()

        icon_label = QLabel()
        if self.icon and self.icon.startswith("ph."):
            # Global temadan renk al
            icon_color = STAT_COLORS.get(self._color_type, ACCENT)
            icon_label.setPixmap(qta.icon(self.icon, color=icon_color).pixmap(48, 48))
        else:
            icon_label.setText(self.icon)
            icon_class = self.ICON_CLASSES.get(self._color_type, "icon-primary")
            icon_label.setProperty("class", icon_class)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label.setProperty("class", "card-icon")
        # Fixed size biraz artırıldı
        icon_label.setFixedSize(52, 52)
        header.addWidget(icon_label)

        header.addStretch()

        if self._show_trend and self._trend_value:
            trend_arrow = "↑" if self._trend_positive else "↓"
            trend_label = QLabel(f"{trend_arrow} {self._trend_value}")
            trend_class = "trend-up" if self._trend_positive else "trend-down"
            trend_label.setProperty("class", trend_class)
            header.addWidget(trend_label)

        layout.addLayout(header)

        # Değer
        self.value_label = QLabel(self._value)
        self.value_label.setProperty("class", "card-value")
        layout.addWidget(self.value_label)

        # Başlık
        title_label = QLabel(self.title)
        title_label.setProperty("class", "card-title")
        layout.addWidget(title_label)

        # Alt başlık
        if self._subtitle:
            sub_label = QLabel(self._subtitle)
            sub_label.setProperty("class", "muted")
            layout.addWidget(sub_label)

    def update_value(self, value: str):
        """Kart değerini güncelle"""
        self._value = value
        self.value_label.setText(value)


class ScrollableCardContainer(QScrollArea):
    """
    Yatay kaydırılabilir kart konteyneri.
    Pencerenin gereksiz genişlemesini önler.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(
            100
        )  # Prevent window expansion logic from forcing wide width
        self.setFixedHeight(100)  # Yeterli yükseklik

        self.container = QWidget()
        self.layout = QHBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(12)
        # Sola hizala
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.setWidget(self.container)

    def add_card(self, card):
        self.layout.addWidget(card)

    def add_stretch(self):
        self.layout.addStretch()
