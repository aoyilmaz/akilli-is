"""
Akıllı İş ERP - Dashboard Sayfası (Düzeltilmiş)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtSvgWidgets import QSvgWidget
from pathlib import Path

from config import APP_NAME, APP_VERSION, BASE_DIR
from config.themes import get_theme, ThemeManager


class StatCard(QFrame):
    """İstatistik kartı"""
    
    def __init__(self, icon: str, title: str, value: str, subtitle: str = "", 
                 color: str = None, parent=None):
        super().__init__(parent)
        self.icon = icon
        self.title = title
        self.color = color
        self.setup_ui(value, subtitle)
        
    def setup_ui(self, value: str, subtitle: str):
        t = get_theme()
        color = self.color or t.accent_primary
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {t.card_bg};
                border: 1px solid {t.border};
                border-radius: {t.radius_large}px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet(f"""
            background-color: {color};
            border-radius: {t.radius_medium}px;
            padding: 12px;
            font-size: 24px;
        """)
        icon_label.setFixedSize(52, 52)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(icon_label)
        
        header.addStretch()
        
        trend_label = QLabel("↑ 12%")
        trend_label.setStyleSheet(f"color: {t.success}; font-size: 12px; background: transparent;")
        header.addWidget(trend_label)
        
        layout.addLayout(header)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            color: {t.text_primary};
            font-size: 32px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(value_label)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"color: {t.text_muted}; font-size: 14px; background: transparent;")
        layout.addWidget(title_label)
        
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet(f"color: {t.text_muted}; font-size: 12px; background: transparent;")
            layout.addWidget(sub_label)


class QuickActionCard(QFrame):
    """Hızlı işlem kartı"""
    
    def __init__(self, icon: str, title: str, description: str, 
                 color: str = None, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._color = color
        self._setup_ui(icon, title, description)
        
    def _setup_ui(self, icon: str, title: str, description: str):
        t = get_theme()
        color = self._color or t.accent_primary
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {t.card_bg};
                border: 1px solid {t.border};
                border-radius: {t.radius_medium}px;
            }}
            QFrame:hover {{
                background-color: {t.bg_hover};
                border-color: {t.border_light};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            background-color: {color};
            border-radius: 10px;
            padding: 10px;
            font-size: 20px;
        """)
        icon_label.setFixedSize(44, 44)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {t.text_primary}; font-weight: 600; font-size: 14px; background: transparent;")
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"color: {t.text_muted}; font-size: 12px; background: transparent;")
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # Arrow
        arrow = QLabel("→")
        arrow.setStyleSheet(f"color: {t.text_muted}; font-size: 16px; background: transparent;")
        layout.addWidget(arrow)


class ActivityItem(QFrame):
    """Son aktivite öğesi"""
    
    def __init__(self, icon: str, title: str, time: str, color: str = None, parent=None):
        super().__init__(parent)
        
        t = get_theme()
        color = color or t.accent_primary
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: none;
                border-left: 3px solid {color};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 16px; background: transparent;")
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {t.text_secondary}; font-size: 13px; background: transparent;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Time
        time_label = QLabel(time)
        time_label.setStyleSheet(f"color: {t.text_muted}; font-size: 12px; background: transparent;")
        layout.addWidget(time_label)


class DashboardPage(QWidget):
    """Ana Dashboard sayfası"""
    
    page_title = "Dashboard"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        ThemeManager.register_callback(self._on_theme_changed)
        
    def _on_theme_changed(self, theme):
        # Sayfayı yeniden oluşturmak yerine sadece renkleri güncelle
        pass
        
    def setup_ui(self):
        t = get_theme()
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        # Ana container
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # === HEADER - LOGO VE HOŞGELDİN ===
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {t.card_bg};
                border: 1px solid {t.border};
                border-radius: {t.radius_large}px;
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(32, 28, 32, 28)
        header_layout.setSpacing(24)
        
        # Logo
        logo_container = QFrame()
        logo_container.setFixedSize(80, 80)
        logo_container.setStyleSheet(f"""
            QFrame {{
                background-color: {t.bg_secondary};
                border: 2px solid {t.accent_primary};
                border-radius: 20px;
            }}
        """)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(12, 12, 12, 12)
        
        logo_path = Path(BASE_DIR) / "assets" / "favicon.svg"
        if logo_path.exists():
            logo = QSvgWidget(str(logo_path))
            logo.setFixedSize(56, 56)
            logo_layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            logo_label = QLabel("🔄")
            logo_label.setStyleSheet("font-size: 36px; background: transparent;")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_layout.addWidget(logo_label)
        
        header_layout.addWidget(logo_container)
        
        # Hoşgeldin metni
        welcome_layout = QVBoxLayout()
        welcome_layout.setSpacing(4)
        
        welcome_title = QLabel(f"Hoş Geldiniz, {APP_NAME}")
        welcome_title.setStyleSheet(f"""
            color: {t.text_primary};
            font-size: 28px;
            font-weight: bold;
            background: transparent;
        """)
        welcome_layout.addWidget(welcome_title)
        
        welcome_sub = QLabel("İşletmenizin güncel durumuna göz atın")
        welcome_sub.setStyleSheet(f"color: {t.text_muted}; font-size: 15px; background: transparent;")
        welcome_layout.addWidget(welcome_sub)
        
        # Tarih
        from datetime import datetime
        date_str = datetime.now().strftime("%d %B %Y, %A")
        date_label = QLabel(f"📅 {date_str}")
        date_label.setStyleSheet(f"color: {t.text_accent}; font-size: 13px; margin-top: 8px; background: transparent;")
        welcome_layout.addWidget(date_label)
        
        header_layout.addLayout(welcome_layout)
        header_layout.addStretch()
        
        # Sağ taraf
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet(f"""
            background-color: {t.accent_primary};
            color: white;
            padding: 6px 14px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        """)
        info_layout.addWidget(version_label, alignment=Qt.AlignmentFlag.AlignRight)
        
        status_label = QLabel("● Sistem Aktif")
        status_label.setStyleSheet(f"color: {t.success}; font-size: 13px; background: transparent;")
        info_layout.addWidget(status_label, alignment=Qt.AlignmentFlag.AlignRight)
        
        header_layout.addLayout(info_layout)
        
        layout.addWidget(header_frame)
        
        # === İSTATİSTİK KARTLARI ===
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
        
        # === HIZLI İŞLEMLER VE SON AKTİVİTELER ===
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)
        
        # Sol - Hızlı İşlemler
        quick_frame = QFrame()
        quick_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {t.card_bg};
                border: 1px solid {t.border};
                border-radius: {t.radius_large}px;
            }}
        """)
        quick_layout = QVBoxLayout(quick_frame)
        quick_layout.setContentsMargins(20, 20, 20, 20)
        quick_layout.setSpacing(12)
        
        quick_title = QLabel("⚡ Hızlı İşlemler")
        quick_title.setStyleSheet(f"color: {t.text_primary}; font-size: 18px; font-weight: bold; background: transparent;")
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
        
        # Sağ - Son Aktiviteler
        activity_frame = QFrame()
        activity_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {t.card_bg};
                border: 1px solid {t.border};
                border-radius: {t.radius_large}px;
            }}
        """)
        activity_layout = QVBoxLayout(activity_frame)
        activity_layout.setContentsMargins(20, 20, 20, 20)
        activity_layout.setSpacing(8)
        
        activity_title = QLabel("🕐 Son Aktiviteler")
        activity_title.setStyleSheet(f"color: {t.text_primary}; font-size: 18px; font-weight: bold; background: transparent;")
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
        see_all.setStyleSheet(f"color: {t.text_accent}; font-size: 13px; padding: 8px; background: transparent;")
        see_all.setCursor(Qt.CursorShape.PointingHandCursor)
        activity_layout.addWidget(see_all, alignment=Qt.AlignmentFlag.AlignRight)
        
        bottom_layout.addWidget(activity_frame, 1)
        
        layout.addLayout(bottom_layout)
        
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
