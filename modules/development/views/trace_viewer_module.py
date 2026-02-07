"""
Akıllı İş - Trace Viewer Module
Sistem yöneticileri için trace log görüntüleyici
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget
)
from PyQt6.QtCore import pyqtSignal

from modules.development.views.trace_list_page import TraceListPage
from modules.development.views.trace_detail_page import TraceDetailPage


class TraceViewerModule(QWidget):
    """
    Trace Viewer Ana Modülü

    İki sayfa içerir:
    1. TraceListPage - Session listesi
    2. TraceDetailPage - Timeline + tablo görünümü
    """

    page_title = "Trace Goruntule"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Stacked widget
        self.stack = QStackedWidget()

        # Sayfalar
        self.list_page = TraceListPage()
        self.detail_page = TraceDetailPage()

        self.stack.addWidget(self.list_page)
        self.stack.addWidget(self.detail_page)

        layout.addWidget(self.stack)

        # Başlangıçta list sayfası
        self.stack.setCurrentWidget(self.list_page)

    def _connect_signals(self):
        """Sinyalleri bağla"""
        # List page'den session seçildiğinde detail'e git
        self.list_page.session_selected.connect(self._show_detail)

        # Detail page'den geri dönüldüğünde list'e git
        self.detail_page.back_requested.connect(self._show_list)

    def _show_detail(self, session_id: int):
        """Trace session detayını göster"""
        self.detail_page.load_session(session_id)
        self.stack.setCurrentWidget(self.detail_page)

    def _show_list(self):
        """List sayfasına dön"""
        self.list_page.refresh()
        self.stack.setCurrentWidget(self.list_page)

    def showEvent(self, event):
        """Widget gösterildiğinde verileri yükle"""
        super().showEvent(event)
        self.list_page.refresh()
