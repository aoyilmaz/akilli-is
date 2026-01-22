"""
Akıllı İş - Sevkiyat Kiosk Modu UI
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QListWidget,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette
from datetime import datetime


class ShipmentLoadingKiosk(QDialog):
    """Sevkiyat Yükleme Kiosk Modu"""

    def __init__(self, shipment_no: str, shipment_loads: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Yükleme Kiosk - {shipment_no}")
        self.shipment_loads = shipment_loads
        self.setModal(True)
        # Tam ekran veya çok geniş
        self.showMaximized()

        # UI
        self.setup_ui()

        # Focus timer (Sürekli inputta kalsın)
        self.timer = QTimer()
        self.timer.timeout.connect(self._keep_focus)
        self.timer.start(2000)

    def setup_ui(self):
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(30)

        # Başlık
        title = QLabel("YÜKLEME MODU")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        layout.addWidget(title)

        # Alt Başlık
        sub_title = QLabel("Lütfen SSCC Barkodunu Okutunuz")
        sub_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_title.setFont(QFont("Arial", 24))
        sub_title.setStyleSheet("color: #cccccc;")
        layout.addWidget(sub_title)

        # Input Alanı
        self.barcode_input = QLineEdit()
        self.barcode_input.setFont(QFont("Courier New", 36))
        self.barcode_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.barcode_input.setStyleSheet(
            """
            QLineEdit {
                border: 4px solid #3b82f6;
                border-radius: 10px;
                padding: 10px;
                background-color: #333;
                color: #fff;
            }
            QLineEdit:focus {
                border-color: #60a5fa;
            }
        """
        )
        self.barcode_input.returnPressed.connect(self._handle_scan)
        layout.addWidget(self.barcode_input)

        # Sonuç Mesajı
        self.result_label = QLabel("HAZIR")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setFont(QFont("Arial", 64, QFont.Weight.Bold))
        self.result_label.setStyleSheet("color: #3b82f6;")
        self.result_label.setFixedHeight(150)
        layout.addWidget(self.result_label)

        # İstatistik
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("0 / 0 Yüklendi")
        self.stats_label.setFont(QFont("Arial", 24))
        stats_layout.addStretch()
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Son İşlemler Listesi
        self.history_list = QListWidget()
        self.history_list.setFont(QFont("Arial", 14))
        self.history_list.setMaximumHeight(200)
        self.history_list.setStyleSheet("background-color: #333; border-radius: 5px;")
        layout.addWidget(self.history_list)

        # Çıkış Button
        close_btn = QPushButton("KIOSK KAPAT")
        close_btn.setFixedHeight(60)
        close_btn.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        close_btn.setStyleSheet(
            "background-color: #ef4444; color: white; border-radius: 10px;"
        )
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self._update_stats()

    def _keep_focus(self):
        if self.isVisible() and not self.barcode_input.hasFocus():
            self.barcode_input.setFocus()

    def _handle_scan(self):
        barcode = self.barcode_input.text().strip()
        if not barcode:
            return

        self.barcode_input.clear()

        # Mantık Kontrolü
        found_load = None
        for load in self.shipment_loads:
            if load.get("sscc") == barcode:
                found_load = load
                break

        if found_load:
            if found_load.get("loaded_at"):
                self._show_feedback("TEKRAR OKUTMA", "warning")
                self._add_history(f"⚠️ {barcode} zaten yüklü")
            else:
                found_load["loaded_at"] = datetime.now().isoformat()
                self._show_feedback("BAŞARILI", "success")
                self._add_history(f"✅ {barcode} yüklendi")
        else:
            self._show_feedback("HATALI BARKOD", "error")
            self._add_history(f"❌ {barcode} planda yok")
            QApplication.beep()

        self._update_stats()

    def _show_feedback(self, text, type_):
        self.result_label.setText(text)

        color_map = {
            "success": "#10b981",  # Green
            "warning": "#f59e0b",  # Orange
            "error": "#ef4444",  # Red
        }
        color = color_map.get(type_, "#ffffff")
        self.result_label.setStyleSheet(f"color: {color};")

        # Arkaplan flash efekti (basitçe stil değiştirip geri alabiliriz ama QWidget için zor, şimdilik label yeterli)

    def _update_stats(self):
        total = len(self.shipment_loads)
        loaded = sum(1 for l in self.shipment_loads if l.get("loaded_at"))
        self.stats_label.setText(f"{loaded} / {total} Yüklendi")

    def _add_history(self, text):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.history_list.insertItem(0, f"[{time_str}] {text}")
