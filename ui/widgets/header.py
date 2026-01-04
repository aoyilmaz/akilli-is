"""
Akıllı İş ERP - Header Widget
PyERP Pro stili - Backdrop blur, badge'li butonlar
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor

from config.themes import get_theme, ThemeManager


class NotificationButton(QPushButton):
    """Bildirim butonu - Badge'li"""
    
    def __init__(self, icon: str, badge: int = 0, parent=None):
        super().__init__(icon, parent)
        self.badge = badge
        self.setFixedSize(42, 42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()
    
    def set_badge(self, count: int):
        self.badge = count
        self.update()
    
    def _apply_style(self):
        t = get_theme()
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.bg_tertiary};
                border: none;
                border-radius: {t.radius_medium}px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
            }}
        """)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        if self.badge > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Badge arka plan
            badge_size = 18
            badge_x = self.width() - badge_size + 2
            badge_y = -2
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#ef4444"))  # red-500
            painter.drawEllipse(badge_x, badge_y, badge_size, badge_size)
            
            # Badge text
            painter.setPen(QColor("white"))
            from PyQt6.QtGui import QFont
            font = QFont()
            font.setPointSize(9)
            font.setBold(True)
            painter.setFont(font)
            
            text = str(self.badge) if self.badge < 10 else "9+"
            painter.drawText(badge_x, badge_y, badge_size, badge_size,
                           Qt.AlignmentFlag.AlignCenter, text)


class Header(QFrame):
    """Üst başlık çubuğu - PyERP Pro stili"""
    
    search_triggered = pyqtSignal(str)
    ai_assistant_clicked = pyqtSignal()
    notifications_clicked = pyqtSignal()
    help_clicked = pyqtSignal()
    theme_toggle_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        ThemeManager.register_callback(self._on_theme_changed)
        
    def _on_theme_changed(self, theme):
        self._apply_styles()
        
    def _apply_styles(self):
        t = get_theme()
        # Backdrop blur efekti için yarı saydam arka plan
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {t.header_bg}CC;
                border-bottom: 1px solid {t.border}80;
            }}
        """)
        
    def setup_ui(self):
        t = get_theme()
        
        self.setFixedHeight(64)
        self._apply_styles()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)
        
        # Sayfa başlığı
        self.title_label = QLabel("Dashboard")
        self.title_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 700;
            color: {t.text_primary};
            background: transparent;
            letter-spacing: -0.5px;
        """)
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # Arama kutusu - daha geniş ve modern
        search_container = QFrame()
        search_container.setStyleSheet(f"""
            QFrame {{
                background-color: {t.bg_secondary};
                border: 1px solid {t.border};
                border-radius: {t.radius_medium}px;
            }}
            QFrame:hover {{
                border-color: {t.border_light};
            }}
        """)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(14, 0, 14, 0)
        search_layout.setSpacing(10)
        
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 14px; background: transparent;")
        search_layout.addWidget(search_icon)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara... (⌘K)")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {t.text_primary};
                font-size: 14px;
                min-width: 280px;
                padding: 12px 0;
            }}
            QLineEdit::placeholder {{
                color: {t.text_muted};
            }}
        """)
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        
        layout.addWidget(search_container)
        
        layout.addSpacing(8)
        
        # AI Asistan butonu - Gradient, shadow
        ai_btn = QPushButton("💬 AI Asistan")
        ai_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ai_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #6366f1, stop:1 #a855f7);
                border: none;
                color: white;
                font-weight: 600;
                font-size: 13px;
                padding: 12px 20px;
                border-radius: {t.radius_medium}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #5558e3, stop:1 #9333ea);
            }}
        """)
        ai_btn.clicked.connect(self.ai_assistant_clicked.emit)
        layout.addWidget(ai_btn)
        
        # Tema toggle
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setFixedSize(42, 42)
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.setToolTip("Temayı değiştir")
        self.theme_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.bg_tertiary};
                border: none;
                border-radius: {t.radius_medium}px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
            }}
        """)
        self.theme_btn.clicked.connect(self.theme_toggle_clicked.emit)
        layout.addWidget(self.theme_btn)
        
        # Bildirimler - Badge'li
        self.notif_btn = NotificationButton("🔔", badge=3)
        self.notif_btn.setToolTip("Bildirimler")
        self.notif_btn.clicked.connect(self.notifications_clicked.emit)
        layout.addWidget(self.notif_btn)
        
        # Yardım
        help_btn = QPushButton("❓")
        help_btn.setFixedSize(42, 42)
        help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        help_btn.setToolTip("Yardım")
        help_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.bg_tertiary};
                border: none;
                border-radius: {t.radius_medium}px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
            }}
        """)
        help_btn.clicked.connect(self.help_clicked.emit)
        layout.addWidget(help_btn)
        
    def set_title(self, title: str):
        t = get_theme()
        self.title_label.setText(title)
        self.title_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 700;
            color: {t.text_primary};
            background: transparent;
            letter-spacing: -0.5px;
        """)
    
    def set_notification_count(self, count: int):
        """Bildirim sayısını güncelle"""
        self.notif_btn.set_badge(count)
        
    def _on_search(self):
        query = self.search_input.text().strip()
        if query:
            self.search_triggered.emit(query)
