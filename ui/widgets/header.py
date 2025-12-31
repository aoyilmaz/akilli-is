"""
Akıllı İş ERP - Header Widget
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

from config import settings


class Header(QFrame):
    """Üst başlık çubuğu"""
    
    search_triggered = pyqtSignal(str)
    ai_assistant_clicked = pyqtSignal()
    notifications_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """UI oluştur"""
        self.setFixedHeight(64)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.8);
                border-bottom: 1px solid rgba(51, 65, 85, 0.5);
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        
        # Sayfa başlığı
        self.title_label = QLabel("Dashboard")
        self.title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
            color: #f8fafc;
        """)
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # Arama kutusu
        search_container = QFrame()
        search_container.setFixedWidth(380)
        search_container.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.8);
                border: 1px solid #334155;
                border-radius: 12px;
            }
            QFrame:focus-within {
                border: 2px solid #6366f1;
            }
        """)
        
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(16, 0, 16, 0)
        
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 16px; border: none; background: transparent;")
        search_layout.addWidget(search_icon)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara... (⌘K)")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #e2e8f0;
                font-size: 14px;
                padding: 12px 0;
            }
            QLineEdit::placeholder {
                color: #64748b;
            }
        """)
        self.search_input.returnPressed.connect(self.on_search)
        search_layout.addWidget(self.search_input)
        
        layout.addWidget(search_container)
        
        layout.addSpacing(16)
        
        # AI Asistan butonu
        ai_btn = QPushButton("  🤖  AI Asistan")
        ai_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ai_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #6366f1, stop:1 #a855f7);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #818cf8, stop:1 #c084fc);
            }
        """)
        ai_btn.clicked.connect(self.ai_assistant_clicked.emit)
        layout.addWidget(ai_btn)
        
        layout.addSpacing(8)
        
        # Bildirimler butonu
        notif_btn = QPushButton("🔔")
        notif_btn.setFixedSize(44, 44)
        notif_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        notif_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #334155;
            }
        """)
        notif_btn.clicked.connect(self.notifications_clicked.emit)
        layout.addWidget(notif_btn)
        
        # Yardım butonu
        help_btn = QPushButton("❓")
        help_btn.setFixedSize(44, 44)
        help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #334155;
            }
        """)
        layout.addWidget(help_btn)
        
    def set_title(self, title: str):
        """Sayfa başlığını güncelle"""
        self.title_label.setText(title)
        
    def on_search(self):
        """Arama yapıldığında"""
        query = self.search_input.text().strip()
        if query:
            self.search_triggered.emit(query)
