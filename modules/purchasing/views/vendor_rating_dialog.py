from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QMessageBox,
    QFrame,
)
from PyQt6.QtCore import Qt

try:
    import qtawesome as qta
except ImportError:
    qta = None

from modules.purchasing.services.vendor_rating_service import VendorRatingService


class VendorRatingDialog(QDialog):
    def __init__(self, supplier, parent=None):
        super().__init__(parent)
        self.supplier = supplier
        self.service = VendorRatingService()
        self.setWindowTitle(f"Performans Değerlendirme: {supplier.name}")
        self.resize(600, 500)
        self.setup_ui()
        self.load_performance()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"{self.supplier.name} - Performans Özeti")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(header)

        # Performance Bars
        self.perf_layout = QVBoxLayout()
        layout.addLayout(self.perf_layout)

        # Scores
        self.quality_bar = self._create_score_row(
            "Kalite (Mal Kabul)", self.perf_layout
        )
        self.delivery_bar = self._create_score_row(
            "Termin (Zamanında Teslimat)", self.perf_layout
        )
        self.cost_bar = self._create_score_row(
            "Maliyet (Fiyat Rekabetçiliği)", self.perf_layout
        )

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shape.Sunken)
        layout.addWidget(line)

        # Total Score
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("GENEL PERFORMANS PUANI:"))
        self.lbl_total = QLabel("0")
        self.lbl_total.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #2196F3;"
        )
        total_layout.addWidget(self.lbl_total)
        total_layout.addStretch()
        layout.addLayout(total_layout)

        # Comments
        layout.addWidget(QLabel("Değerlendirme Notları:"))
        self.txt_comments = QTextEdit()
        self.txt_comments.setPlaceholderText(
            "Tedarikçi hakkındaki görüşlerinizi buraya yazabilirsiniz..."
        )
        layout.addWidget(self.txt_comments)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_recalc = QPushButton("Yeniden Hesapla")
        if qta:
            btn_recalc.setIcon(qta.icon("fa5s.sync"))
        btn_recalc.clicked.connect(self.load_performance)
        btn_layout.addWidget(btn_recalc)

        btn_save = QPushButton("Puanı Kaydet")
        btn_save.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 10px;"
        )
        btn_save.clicked.connect(self.save)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def _create_score_row(self, label, layout):
        row = QHBoxLayout()
        row.addWidget(QLabel(label), 2)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(True)
        bar.setFormat("%p / 100")
        row.addWidget(bar, 3)

        layout.addLayout(row)
        return bar

    def load_performance(self):
        try:
            scores = self.service.calculate_supplier_scores(self.supplier.id)
            self.scores = scores

            self.quality_bar.setValue(int(scores["quality"]))
            self.delivery_bar.setValue(int(scores["delivery"]))
            self.cost_bar.setValue(int(scores["cost"]))

            self.lbl_total.setText(str(scores["total"]))

            # Color update based on score
            self._update_bar_color(self.quality_bar, scores["quality"])
            self._update_bar_color(self.delivery_bar, scores["delivery"])
            self._update_bar_color(self.cost_bar, scores["cost"])

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Performans hesaplanamadı: {str(e)}")

    def _update_bar_color(self, bar, score):
        if score >= 85:
            color = "#4CAF50"  # Green
        elif score >= 60:
            color = "#FFC107"  # Yellow
        else:
            color = "#F44336"  # Red

        bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")

    def save(self):
        try:
            comments = self.txt_comments.toPlainText()
            self.service.save_rating(self.supplier.id, self.scores, comments)
            QMessageBox.information(
                self, "Bilgi", "Değerlendirme başarıyla kaydedildi."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydedilemedi: {str(e)}")
