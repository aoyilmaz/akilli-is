"""
Akıllı İş - Üretim Operatör Paneli
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QGridLayout,
    QInputDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor


class OperatorPanel(QWidget):
    """
    Üretim sahası için basitleştirilmiş arayüz.
    """

    def __init__(self, work_order_id=None):
        super().__init__()
        self.work_order_id = work_order_id
        self.status = "IDLE"  # IDLE, WORKING, BREAK
        self.start_time = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Bilgi Paneli
        info_frame = QFrame()
        info_frame.setStyleSheet(
            "background-color: #2c3e50; border-radius: 10px; color: white;"
        )
        info_lay = QVBoxLayout(info_frame)

        self.lbl_work_order = QLabel("İŞ EMRİ: IE-2026-0042")
        self.lbl_work_order.setFont(QFont("Arial", 18, QFont.Weight.Bold))

        self.lbl_product = QLabel("Ürün: Çelik Gövde A-1")
        self.lbl_product.setFont(QFont("Arial", 14))

        self.lbl_timer = QLabel("00:00:00")
        self.lbl_timer.setFont(QFont("Digital-7", 40))
        self.lbl_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_timer.setStyleSheet("color: #27ae60;")

        info_lay.addWidget(self.lbl_work_order)
        info_lay.addWidget(self.lbl_product)
        info_lay.addWidget(self.lbl_timer)
        layout.addWidget(info_frame)

        # Butonlar
        grid = QGridLayout()
        grid.setSpacing(15)

        self.btn_start = self.create_big_button("İŞİ BAŞLAT", "#27ae60")
        self.btn_pause = self.create_big_button("DURDUR / MOLA", "#f39c12")
        self.btn_reject = self.create_big_button("FİRE GİR", "#e74c3c")
        self.btn_complete = self.create_big_button("İŞİ BİTİR", "#2980b9")

        self.btn_start.clicked.connect(self.start_work)
        self.btn_pause.clicked.connect(self.pause_work)
        self.btn_reject.clicked.connect(self.enter_scrap)
        self.btn_complete.clicked.connect(self.complete_work)

        grid.addWidget(self.btn_start, 0, 0)
        grid.addWidget(self.btn_pause, 0, 1)
        grid.addWidget(self.btn_reject, 1, 0)
        grid.addWidget(self.btn_complete, 1, 1)

        layout.addLayout(grid)

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

    def create_big_button(self, text, color):
        btn = QPushButton(text)
        btn.setFixedHeight(120)
        btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 15px;
                border: 2px solid rgba(255,255,255,0.1);
            }}
            QPushButton:pressed {{
                background-color: #34495e;
            }}
        """
        )
        return btn

    def start_work(self):
        self.status = "WORKING"
        self.start_time = datetime.now()
        self.timer.start(1000)
        self.lbl_timer.setStyleSheet("color: #27ae60;")
        QMessageBox.information(self, "Bilgi", "İş başlatıldı.")

    def pause_work(self):
        reasons = ["Arıza", "Ayarsızlık", "Malzeme Bekleme", "Mola"]
        reason, ok = QInputDialog.getItem(
            self, "Duruş Nedeni", "Duruş nedenini seçin:", reasons, 0, False
        )

        if ok:
            self.status = "BREAK"
            self.timer.stop()
            self.lbl_timer.setStyleSheet("color: #f39c12;")
            # DB'ye downtime kaydı atılacak...
            QMessageBox.warning(self, "Duruş", f"İş durduruldu: {reason}")

    def enter_scrap(self):
        amount, ok = QInputDialog.getInt(
            self, "Fire Girişi", "Fire miktarını girin:", 0, 0, 1000
        )
        if ok:
            QMessageBox.critical(self, "Fire", f"{amount} adet fire kaydedildi.")

    def complete_work(self):
        self.timer.stop()
        QMessageBox.information(self, "Tamamlandı", "İş emri başarıyla tamamlandı.")

    def update_timer(self):
        if self.start_time:
            delta = datetime.now() - self.start_time
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.lbl_timer.setText(f"{hours:02}:{minutes:02}:{seconds:02}")


from datetime import datetime
