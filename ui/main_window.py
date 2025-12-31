"""
Akıllı İş ERP - Ana Pencere
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QStackedWidget, QScrollArea, QSizePolicy,
    QGraphicsDropShadowEffect, QSpacerItem
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QColor, QFont
from PyQt6.QtSvgWidgets import QSvgWidget
from pathlib import Path

from config import settings
from ui.widgets.sidebar import Sidebar
from ui.widgets.header import Header
from ui.pages.dashboard import DashboardPage
from ui.pages.placeholder import PlaceholderPage


class MainWindow(QMainWindow):
    """Ana uygulama penceresi"""
    
    def __init__(self):
        super().__init__()
        self.setup_window()
        self.setup_ui()
        self.connect_signals()
        
    def setup_window(self):
        """Pencere özelliklerini ayarla"""
        self.setWindowTitle(f"{settings.APP_NAME} - {settings.APP_DESCRIPTION}")
        self.setMinimumSize(1280, 800)
        
        # Tam ekran boyutunda başlat (macOS için optimize)
        screen = self.screen().availableGeometry()
        self.resize(int(screen.width() * 0.9), int(screen.height() * 0.9))
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        # Ana container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout (yatay - sidebar + content)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Header
        self.header = Header()
        content_layout.addWidget(self.header)
        
        # Sayfa container (stacked widget)
        self.page_stack = QStackedWidget()
        content_layout.addWidget(self.page_stack)
        
        # Sayfaları ekle
        self.pages = {}
        self.add_pages()
        
        main_layout.addWidget(content_widget)
        
    def add_pages(self):
        """Tüm sayfaları ekle"""
        # Dashboard
        self.pages['dashboard'] = DashboardPage()
        self.page_stack.addWidget(self.pages['dashboard'])
        
        # Stok Modülü
        self.pages['stock-cards'] = PlaceholderPage("Stok Kartları", "📦")
        self.page_stack.addWidget(self.pages['stock-cards'])
        
        self.pages['warehouses'] = PlaceholderPage("Depolar", "🏭")
        self.page_stack.addWidget(self.pages['warehouses'])
        
        self.pages['movements'] = PlaceholderPage("Stok Hareketleri", "↔️")
        self.page_stack.addWidget(self.pages['movements'])
        
        # Üretim Modülü
        self.pages['work-orders'] = PlaceholderPage("İş Emirleri", "📋")
        self.page_stack.addWidget(self.pages['work-orders'])
        
        self.pages['bom'] = PlaceholderPage("Ürün Reçeteleri", "📝")
        self.page_stack.addWidget(self.pages['bom'])
        
        self.pages['planning'] = PlaceholderPage("Üretim Planlama", "📅")
        self.page_stack.addWidget(self.pages['planning'])
        
        # Diğer modüller
        self.pages['purchasing'] = PlaceholderPage("Satın Alma", "🛒")
        self.page_stack.addWidget(self.pages['purchasing'])
        
        self.pages['sales'] = PlaceholderPage("Satış", "💰")
        self.page_stack.addWidget(self.pages['sales'])
        
        self.pages['finance'] = PlaceholderPage("Finans", "💳")
        self.page_stack.addWidget(self.pages['finance'])
        
        self.pages['hr'] = PlaceholderPage("İnsan Kaynakları", "👥")
        self.page_stack.addWidget(self.pages['hr'])
        
        self.pages['reports'] = PlaceholderPage("Raporlar", "📊")
        self.page_stack.addWidget(self.pages['reports'])
        
        self.pages['settings'] = PlaceholderPage("Ayarlar", "⚙️")
        self.page_stack.addWidget(self.pages['settings'])
        
    def connect_signals(self):
        """Sinyalleri bağla"""
        self.sidebar.page_changed.connect(self.change_page)
        self.sidebar.sidebar_toggled.connect(self.on_sidebar_toggle)
        self.header.search_triggered.connect(self.on_search)
        self.header.ai_assistant_clicked.connect(self.show_ai_assistant)
        
    def change_page(self, page_id: str):
        """Sayfa değiştir"""
        if page_id in self.pages:
            self.page_stack.setCurrentWidget(self.pages[page_id])
            self.header.set_title(self.pages[page_id].page_title)
            
    def on_sidebar_toggle(self, collapsed: bool):
        """Sidebar toggle edildiğinde"""
        pass  # Animasyon eklenebilir
        
    def on_search(self, query: str):
        """Arama yapıldığında"""
        print(f"Arama: {query}")
        
    def show_ai_assistant(self):
        """AI Asistan penceresini göster"""
        print("AI Asistan açılıyor...")


# UI init dosyaları
