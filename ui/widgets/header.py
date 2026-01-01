"""
Akıllı İş ERP - Header Widget (Düzeltilmiş)
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from config.themes import get_theme, ThemeManager


class Header(QFrame):
    """Üst başlık çubuğu"""
    
    search_triggered = pyqtSignal(str)
    ai_assistant_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        ThemeManager.register_callback(self._on_theme_changed)
        
    def _on_theme_changed(self, theme):
        self._apply_styles()
        
    def _apply_styles(self):
        t = get_theme()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {t.header_bg};
                border-bottom: 1px solid {t.border};
            }}
        """)
        
    def setup_ui(self):
        t = get_theme()
        
        self.setFixedHeight(64)
        self._apply_styles()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)
        
        # Sayfa başlığı
        self.title_label = QLabel("Dashboard")
        self.title_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 600;
            color: {t.text_primary};
            background: transparent;
        """)
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # Arama kutusu
        search_container = QFrame()
        search_container.setStyleSheet(f"""
            QFrame {{
                background-color: {t.input_bg};
                border: 1px solid {t.border};
                border-radius: {t.radius_medium}px;
            }}
            QFrame:hover {{
                border-color: {t.border_light};
            }}
        """)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(12, 0, 12, 0)
        search_layout.setSpacing(8)
        
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
                min-width: 200px;
                padding: 10px 0;
            }}
            QLineEdit::placeholder {{
                color: {t.text_muted};
            }}
        """)
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        
        layout.addWidget(search_container)
        
        # Bildirimler
        notif_btn = QPushButton("🔔")
        notif_btn.setFixedSize(40, 40)
        notif_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        notif_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.bg_secondary};
                border: 1px solid {t.border};
                border-radius: {t.radius_medium}px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
                border-color: {t.border_light};
            }}
        """)
        layout.addWidget(notif_btn)
        
        # AI Asistan
        ai_btn = QPushButton("✨ AI Asistan")
        ai_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ai_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.accent_primary};
                border: none;
                color: white;
                font-weight: 600;
                padding: 10px 20px;
                border-radius: {t.radius_medium}px;
            }}
            QPushButton:hover {{
                background-color: {t.accent_secondary};
            }}
        """)
        ai_btn.clicked.connect(self.ai_assistant_clicked.emit)
        layout.addWidget(ai_btn)
        
    def set_title(self, title: str):
        t = get_theme()
        self.title_label.setText(title)
        self.title_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 600;
            color: {t.text_primary};
            background: transparent;
        """)
        
    def _on_search(self):
        query = self.search_input.text().strip()
        if query:
            self.search_triggered.emit(query)
