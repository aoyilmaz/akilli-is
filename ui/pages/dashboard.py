"""
Akıllı İş ERP - Dashboard Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QScrollArea, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config import settings


class KPICard(QFrame):
    """KPI gösterge kartı"""
    
    def __init__(self, title: str, value: str, change: str, positive: bool, icon: str, parent=None):
        super().__init__(parent)
        self.setup_ui(title, value, change, positive, icon)
        
    def setup_ui(self, title: str, value: str, change: str, positive: bool, icon: str):
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.5);
                border: 1px solid rgba(51, 65, 85, 0.5);
                border-radius: 16px;
            }
            QFrame:hover {
                border-color: rgba(99, 102, 241, 0.3);
            }
        """)
        self.setFixedHeight(140)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Üst satır: icon ve değişim
        top_row = QHBoxLayout()
        
        # Icon container
        icon_container = QFrame()
        icon_container.setFixedSize(48, 48)
        icon_container.setStyleSheet(f"""
            background-color: {'rgba(16, 185, 129, 0.2)' if positive else 'rgba(239, 68, 68, 0.2)'};
            border-radius: 12px;
            border: none;
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 22px; background: transparent; border: none;")
        icon_layout.addWidget(icon_label)
        top_row.addWidget(icon_container)
        
        top_row.addStretch()
        
        # Değişim göstergesi
        change_label = QLabel(f"{'↑' if positive else '↓'} {change}")
        change_label.setStyleSheet(f"""
            color: {'#10b981' if positive else '#ef4444'};
            font-weight: 600;
            font-size: 13px;
            background: transparent;
            border: none;
        """)
        top_row.addWidget(change_label)
        
        layout.addLayout(top_row)
        layout.addStretch()
        
        # Alt satır: başlık ve değer
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: #64748b;
            font-size: 13px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            color: #f8fafc;
            font-size: 28px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        layout.addWidget(value_label)


class ActivityItem(QFrame):
    """Aktivite listesi öğesi"""
    
    def __init__(self, icon: str, text: str, time: str, color: str, parent=None):
        super().__init__(parent)
        self.setup_ui(icon, text, time, color)
        
    def setup_ui(self, icon: str, text: str, time: str, color: str):
        self.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        
        # Icon
        icon_container = QFrame()
        icon_container.setFixedSize(36, 36)
        icon_container.setStyleSheet(f"""
            background-color: #1e293b;
            border-radius: 8px;
            border: none;
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"font-size: 16px; color: {color}; background: transparent; border: none;")
        icon_layout.addWidget(icon_label)
        layout.addWidget(icon_container)
        
        # Metin
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        text_label = QLabel(text)
        text_label.setStyleSheet("color: #e2e8f0; font-size: 13px; background: transparent; border: none;")
        text_layout.addWidget(text_label)
        
        time_label = QLabel(time)
        time_label.setStyleSheet("color: #475569; font-size: 11px; background: transparent; border: none;")
        text_layout.addWidget(time_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()


class QuickActionButton(QPushButton):
    """Hızlı işlem butonu"""
    
    def __init__(self, icon: str, text: str, color: str, parent=None):
        super().__init__(parent)
        self.setText(f"{icon}  {text}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(56)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(30, 41, 59, 0.5);
                color: #e2e8f0;
                border: 1px solid rgba(51, 65, 85, 0.5);
                border-radius: 12px;
                text-align: left;
                padding-left: 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(51, 65, 85, 0.5);
                border-color: {color};
            }}
        """)


class DashboardPage(QWidget):
    """Dashboard ana sayfası"""
    
    page_title = "Dashboard"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        # Ana container
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Hoşgeldin mesajı
        welcome_label = QLabel("Hoş geldin, Okan 👋")
        welcome_label.setStyleSheet("""
            font-size: 14px;
            color: #64748b;
        """)
        layout.addWidget(welcome_label)
        
        # KPI Kartları
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)
        
        kpis = [
            ("Günlük Ciro", "₺125.450", "+12.5%", True, "📈"),
            ("Açık Siparişler", "47", "-8", True, "📋"),
            ("Stok Değeri", "₺2.3M", "-3.2%", False, "📦"),
            ("Üretim Verimi", "%87.5", "+5.2%", True, "⚡"),
        ]
        
        for title, value, change, positive, icon in kpis:
            card = KPICard(title, value, change, positive, icon)
            kpi_layout.addWidget(card)
            
        layout.addLayout(kpi_layout)
        
        # Orta bölüm: Grafik + Uyarılar
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(24)
        
        # Sol: Grafik placeholder
        chart_card = QFrame()
        chart_card.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.5);
                border: 1px solid rgba(51, 65, 85, 0.5);
                border-radius: 16px;
            }
        """)
        chart_card.setMinimumHeight(280)
        
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(24, 24, 24, 24)
        
        chart_header = QHBoxLayout()
        chart_title = QLabel("Haftalık Üretim")
        chart_title.setStyleSheet("font-size: 18px; font-weight: 600; color: #f8fafc;")
        chart_header.addWidget(chart_title)
        chart_header.addStretch()
        
        period_btn = QPushButton("Haftalık")
        period_btn.setStyleSheet("""
            background-color: rgba(99, 102, 241, 0.2);
            color: #818cf8;
            border: none;
            border-radius: 8px;
            padding: 6px 16px;
            font-size: 12px;
            font-weight: 500;
        """)
        chart_header.addWidget(period_btn)
        chart_layout.addLayout(chart_header)
        
        # Grafik placeholder
        chart_placeholder = QLabel("📊 Grafik burada görünecek")
        chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_placeholder.setStyleSheet("""
            color: #475569;
            font-size: 16px;
            padding: 60px;
        """)
        chart_layout.addWidget(chart_placeholder)
        
        middle_layout.addWidget(chart_card, stretch=2)
        
        # Sağ: Uyarılar
        alerts_card = QFrame()
        alerts_card.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.5);
                border: 1px solid rgba(51, 65, 85, 0.5);
                border-radius: 16px;
            }
        """)
        alerts_card.setMinimumHeight(280)
        alerts_card.setFixedWidth(320)
        
        alerts_layout = QVBoxLayout(alerts_card)
        alerts_layout.setContentsMargins(24, 24, 24, 24)
        
        alerts_header = QHBoxLayout()
        alerts_title = QLabel("Uyarılar")
        alerts_title.setStyleSheet("font-size: 18px; font-weight: 600; color: #f8fafc;")
        alerts_header.addWidget(alerts_title)
        alerts_header.addStretch()
        
        alerts_badge = QLabel("3 aktif")
        alerts_badge.setStyleSheet("""
            background-color: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            padding: 4px 10px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        alerts_header.addWidget(alerts_badge)
        alerts_layout.addLayout(alerts_header)
        
        alerts_layout.addSpacing(12)
        
        # Uyarı öğeleri
        alerts = [
            ("⚠️", "5 üründe kritik stok seviyesi", "#ef4444"),
            ("⏰", "3 fatura vadesi yaklaşıyor", "#f59e0b"),
            ("🔧", "Makine-3 bakım zamanı geldi", "#3b82f6"),
        ]
        
        for icon, text, color in alerts:
            alert_frame = QFrame()
            alert_frame.setStyleSheet(f"""
                background-color: rgba(30, 41, 59, 0.8);
                border-radius: 10px;
                padding: 4px;
            """)
            alert_layout = QHBoxLayout(alert_frame)
            alert_layout.setContentsMargins(12, 10, 12, 10)
            
            alert_icon = QLabel(icon)
            alert_icon.setStyleSheet(f"font-size: 18px;")
            alert_layout.addWidget(alert_icon)
            
            alert_text = QLabel(text)
            alert_text.setStyleSheet(f"color: #e2e8f0; font-size: 12px;")
            alert_text.setWordWrap(True)
            alert_layout.addWidget(alert_text, stretch=1)
            
            alerts_layout.addWidget(alert_frame)
        
        alerts_layout.addStretch()
        
        middle_layout.addWidget(alerts_card)
        layout.addLayout(middle_layout)
        
        # Alt bölüm: Aktiviteler + Hızlı İşlemler
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(24)
        
        # Sol: Son aktiviteler
        activities_card = QFrame()
        activities_card.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.5);
                border: 1px solid rgba(51, 65, 85, 0.5);
                border-radius: 16px;
            }
        """)
        
        activities_layout = QVBoxLayout(activities_card)
        activities_layout.setContentsMargins(24, 24, 24, 24)
        
        activities_header = QHBoxLayout()
        activities_title = QLabel("Son Aktiviteler")
        activities_title.setStyleSheet("font-size: 18px; font-weight: 600; color: #f8fafc;")
        activities_header.addWidget(activities_title)
        activities_header.addStretch()
        
        see_all_btn = QPushButton("Tümünü Gör")
        see_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        see_all_btn.setStyleSheet("""
            color: #818cf8;
            background: transparent;
            border: none;
            font-size: 13px;
        """)
        activities_header.addWidget(see_all_btn)
        activities_layout.addLayout(activities_header)
        
        # Aktivite öğeleri
        activities = [
            ("✅", "Sipariş #1234 onaylandı", "5 dk önce", "#10b981"),
            ("🏭", "İş Emri #567 başlatıldı", "12 dk önce", "#3b82f6"),
            ("⚠️", "Hammadde A kritik seviyede", "25 dk önce", "#f59e0b"),
            ("📄", "Fatura #890 kesildi", "1 saat önce", "#a855f7"),
            ("🚚", "Sevkiyat #456 tamamlandı", "2 saat önce", "#06b6d4"),
        ]
        
        for icon, text, time, color in activities:
            item = ActivityItem(icon, text, time, color)
            activities_layout.addWidget(item)
        
        bottom_layout.addWidget(activities_card)
        
        # Sağ: Hızlı işlemler
        actions_card = QFrame()
        actions_card.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.5);
                border: 1px solid rgba(51, 65, 85, 0.5);
                border-radius: 16px;
            }
        """)
        actions_card.setFixedWidth(320)
        
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setContentsMargins(24, 24, 24, 24)
        
        actions_title = QLabel("Hızlı İşlemler")
        actions_title.setStyleSheet("font-size: 18px; font-weight: 600; color: #f8fafc;")
        actions_layout.addWidget(actions_title)
        
        actions_layout.addSpacing(12)
        
        actions = [
            ("➕", "Yeni Sipariş", "#10b981"),
            ("🏭", "İş Emri Oluştur", "#6366f1"),
            ("📦", "Stok Girişi", "#f59e0b"),
            ("📄", "Fatura Kes", "#ec4899"),
        ]
        
        for icon, text, color in actions:
            btn = QuickActionButton(icon, text, color)
            actions_layout.addWidget(btn)
        
        actions_layout.addStretch()
        
        bottom_layout.addWidget(actions_card)
        layout.addLayout(bottom_layout)
        
        # AI Asistan Banner
        ai_banner = QFrame()
        ai_banner.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 rgba(99, 102, 241, 0.15), 
                    stop:1 rgba(168, 85, 247, 0.15));
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 16px;
            }
        """)
        
        ai_layout = QHBoxLayout(ai_banner)
        ai_layout.setContentsMargins(24, 20, 24, 20)
        
        ai_icon = QLabel("🤖")
        ai_icon.setStyleSheet("font-size: 36px;")
        ai_layout.addWidget(ai_icon)
        
        ai_text_layout = QVBoxLayout()
        ai_title = QLabel("AI Asistan")
        ai_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #f8fafc;")
        ai_text_layout.addWidget(ai_title)
        
        ai_message = QLabel(
            '"Bugün satışlar geçen haftaya göre %12 arttı. Mevcut stok seviyelerine göre '
            '3 hammadde için sipariş oluşturmanızı öneriyorum."'
        )
        ai_message.setStyleSheet("color: #94a3b8; font-size: 13px;")
        ai_message.setWordWrap(True)
        ai_text_layout.addWidget(ai_message)
        
        ai_layout.addLayout(ai_text_layout, stretch=1)
        
        ai_btn = QPushButton("Önerileri Gör")
        ai_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ai_btn.setStyleSheet("""
            background-color: #6366f1;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 20px;
            font-weight: 600;
            font-size: 13px;
        """)
        ai_layout.addWidget(ai_btn)
        
        layout.addWidget(ai_banner)
        
        layout.addStretch()
        
        scroll.setWidget(container)
        
        # Ana layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
