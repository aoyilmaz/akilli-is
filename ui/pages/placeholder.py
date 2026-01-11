"""
Akıllı İş ERP - Placeholder Sayfası
Yapım aşamasındaki modüller için geçici sayfa
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class PlaceholderPage(QWidget):
    """Geçici placeholder sayfa"""
    
    def __init__(self, title: str, icon: str = "🚧", parent=None):
        super().__init__(parent)
        self.page_title = title
        self.setup_ui(title, icon)
        
    def setup_ui(self, title: str, icon: str):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Başlık
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Alt başlık
        subtitle = QLabel("Bu modül yakında aktif olacak")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Bilgi
        info = QLabel("Faz 1 geliştirme sürecindeyiz 🚀")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)
