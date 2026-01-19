"""
Akıllı İş - Barkod Okuyucu Entegrasyonu

USB veya Bluetooth barkod okuyucuların klavye wedge modunda çalışmasını
destekler. Barkod okuyucular genellikle karakterleri klavye girişi olarak
gönderir ve sonunda Enter tuşuna basarlar.

Kullanım:
    scanner = BarcodeScanner(callback=handle_barcode)
    # Widget'a ekle
    widget.installEventFilter(scanner)
"""

from typing import Callable, Optional
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QObject, QEvent, QTimer
from PyQt6.QtGui import QKeyEvent


class BarcodeScanner(QObject):
    """
    Barkod okuyucu yardımcı sınıfı

    Klavye wedge modunda çalışan barkod okuyucuları destekler.
    Karakterler hızlıca girilip Enter ile tamamlandığında callback çağrılır.
    """

    def __init__(
        self,
        callback: Callable[[str], None],
        timeout_ms: int = 100,
        min_length: int = 4,
        parent: Optional[QObject] = None,
    ):
        """
        Args:
            callback: Barkod okunduğunda çağrılacak fonksiyon
            timeout_ms: Karakter arası maksimum süre (ms)
            min_length: Minimum barkod uzunluğu
            parent: Parent QObject
        """
        super().__init__(parent)
        self._callback = callback
        self._timeout_ms = timeout_ms
        self._min_length = min_length
        self._buffer = ""
        self._last_key_time: Optional[datetime] = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timeout)
        self._timer.setSingleShot(True)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Event filter - klavye girişlerini yakalar"""
        if event.type() == QEvent.Type.KeyPress:
            key_event: QKeyEvent = event

            # Enter tuşu - barkod tamamlandı
            if key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if len(self._buffer) >= self._min_length:
                    self._emit_barcode()
                else:
                    self._clear_buffer()
                return False  # Event'i tüketme, normal işlemeye devam

            # Escape - buffer'ı temizle
            if key_event.key() == Qt.Key.Key_Escape:
                self._clear_buffer()
                return False

            # Yazdırılabilir karakter
            text = key_event.text()
            if text and text.isprintable():
                now = datetime.now()

                # Timeout kontrolü
                if self._last_key_time:
                    elapsed = (now - self._last_key_time).total_seconds() * 1000
                    if elapsed > self._timeout_ms * 2:
                        # Çok uzun süre geçmiş, buffer'ı sıfırla
                        self._buffer = ""

                self._buffer += text
                self._last_key_time = now

                # Timeout timer'ı yeniden başlat
                self._timer.stop()
                self._timer.start(self._timeout_ms * 3)

        return False  # Event'i tüketme

    def _emit_barcode(self):
        """Barkodu callback'e gönder"""
        barcode = self._buffer.strip()
        self._clear_buffer()

        if barcode and len(barcode) >= self._min_length:
            self._callback(barcode)

    def _clear_buffer(self):
        """Buffer'ı temizle"""
        self._buffer = ""
        self._last_key_time = None
        self._timer.stop()

    def _on_timeout(self):
        """Timeout olduğunda buffer'ı temizle"""
        self._clear_buffer()


class BarcodeInput(QWidget):
    """
    Barkod giriş alanı widget'ı

    Hem manuel giriş hem de barkod okuyucu desteği sağlar.
    """

    def __init__(
        self,
        callback: Callable[[str], None],
        placeholder: str = "Barkod okutun veya girin...",
        parent: Optional[QWidget] = None,
    ):
        """
        Args:
            callback: Barkod girildiğinde çağrılacak fonksiyon
            placeholder: Input placeholder text
            parent: Parent widget
        """
        super().__init__(parent)
        self._callback = callback
        self._setup_ui(placeholder)

    def _setup_ui(self, placeholder: str):
        """UI'ı oluştur"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Input
        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.returnPressed.connect(self._on_submit)
        self.input.setStyleSheet(
            """
            QLineEdit {
                background-color: #1e293b;
                border: 2px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
                color: #f8fafc;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """
        )
        layout.addWidget(self.input, stretch=1)

        # Ara butonu
        self.search_btn = QPushButton("🔍")
        self.search_btn.setFixedSize(36, 36)
        self.search_btn.clicked.connect(self._on_submit)
        self.search_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3b82f6;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """
        )
        layout.addWidget(self.search_btn)

    def _on_submit(self):
        """Barkod gönder"""
        barcode = self.input.text().strip()
        if barcode:
            self._callback(barcode)
            self.input.clear()

    def set_focus(self):
        """Input'a odaklan"""
        self.input.setFocus()

    def clear(self):
        """Input'u temizle"""
        self.input.clear()
