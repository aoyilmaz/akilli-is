"""
Akıllı İş ERP - Ortak İstatistik Kartları
Tüm modüllerde kullanılabilecek modern görünümlü istatistik kartları
Global tema (theme.qss) kullanır - inline stil yoktur
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt


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
        parent=None
    ):
        super().__init__(parent)
        self._title = title
        self._value = value
        self._color_type = color_type
        self._setup_ui()
        
    def _setup_ui(self):
        # QSS class'ı ayarla
        self.setProperty("class", "stat-card")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        
        # Başlık
        title_label = QLabel(self._title)
        title_label.setProperty("class", "card-title")
        layout.addWidget(title_label)
        
        # Değer
        self.value_label = QLabel(self._value)
        self.value_label.setProperty("class", "card-value")
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
        parent=None
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
        
        icon_label = QLabel(self.icon)
        icon_label.setProperty("class", "card-icon")
        icon_class = self.ICON_CLASSES.get(self._color_type, "icon-primary")
        icon_label.setProperty("class", icon_class)
        icon_label.setFixedSize(52, 52)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
