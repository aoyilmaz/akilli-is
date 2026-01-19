"""
Akıllı İş - Çalışan Kimlik Kartı Dialog
QR kodlu kimlik kartı önizleme ve yazdırma
"""

import os
from io import BytesIO

import qrcode
from PIL import Image

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QMessageBox,
    QFileDialog,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QPen
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter

from config.styles import (
    BG_PRIMARY,
    BG_SECONDARY,
    TEXT_PRIMARY,
    ACCENT,
    get_button_style,
)


# Kimlik kartı boyutları (piksel olarak, 300 DPI için)
# Standart kredi kartı: 85.6mm x 53.98mm
CARD_WIDTH = 340  # px (ekran önizleme)
CARD_HEIGHT = 215  # px

# Renk paleti
CARD_BG = "#1a1f2e"
CARD_HEADER_BG = "#0d47a1"
CARD_TEXT = "#ffffff"
CARD_ACCENT = "#64b5f6"


class IdCardDialog(QDialog):
    """Çalışan kimlik kartı dialog'u"""

    def __init__(self, employee, parent=None):
        super().__init__(parent)
        self.employee = employee
        self.setWindowTitle(f"Kimlik Kartı - {employee.full_name}")
        self.setMinimumSize(450, 400)
        self.setStyleSheet(f"background-color: {BG_PRIMARY}; color: {TEXT_PRIMARY};")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        title = QLabel("👤 Kimlik Kartı Önizleme")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Kart önizleme
        self.card_frame = QFrame()
        self.card_frame.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        self.card_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {CARD_BG};
                border-radius: 12px;
                border: 1px solid #334155;
            }}
        """
        )

        # Kart içeriği için pixmap oluştur
        self.card_pixmap = self._generate_card()

        card_label = QLabel()
        card_label.setPixmap(self.card_pixmap)
        card_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.addWidget(card_label)

        # Ortala
        card_container = QHBoxLayout()
        card_container.addStretch()
        card_container.addWidget(self.card_frame)
        card_container.addStretch()
        layout.addLayout(card_container)

        layout.addStretch()

        # Butonlar
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet(get_button_style("add"))
        save_btn.clicked.connect(self._save_card)
        btn_layout.addWidget(save_btn)

        print_btn = QPushButton("🖨 Yazdır")
        print_btn.setStyleSheet(get_button_style("refresh"))
        print_btn.clicked.connect(self._print_card)
        btn_layout.addWidget(print_btn)

        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _generate_card(self) -> QPixmap:
        """Kimlik kartı pixmap'i oluştur"""
        pixmap = QPixmap(CARD_WIDTH, CARD_HEIGHT)
        pixmap.fill(QColor(CARD_BG))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Header (mavi şerit)
        painter.fillRect(0, 0, CARD_WIDTH, 40, QColor(CARD_HEADER_BG))

        # Logo ve Şirket adı
        painter.setPen(QColor(CARD_TEXT))
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        painter.drawText(12, 28, "⚙ AKILLIŞ A.Ş.")

        # Fotoğraf alanı (sol)
        photo_x, photo_y = 15, 55
        photo_w, photo_h = 80, 100

        photo_pixmap = self._get_photo()
        if photo_pixmap:
            scaled = photo_pixmap.scaled(
                photo_w,
                photo_h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            # Ortalayarak kırp
            x_offset = (scaled.width() - photo_w) // 2
            y_offset = (scaled.height() - photo_h) // 2
            cropped = scaled.copy(x_offset, y_offset, photo_w, photo_h)
            painter.drawPixmap(photo_x, photo_y, cropped)
        else:
            # Placeholder
            painter.fillRect(photo_x, photo_y, photo_w, photo_h, QColor("#334155"))
            painter.setPen(QColor("#64748b"))
            painter.setFont(QFont("Segoe UI", 24))
            painter.drawText(
                photo_x, photo_y, photo_w, photo_h, Qt.AlignmentFlag.AlignCenter, "👤"
            )

        # Fotoğraf çerçevesi
        painter.setPen(QPen(QColor(CARD_ACCENT), 2))
        painter.drawRect(photo_x, photo_y, photo_w, photo_h)

        # Bilgiler (sağ)
        info_x = 110
        painter.setPen(QColor(CARD_TEXT))

        # İsim
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        name = self.employee.full_name.upper()
        painter.drawText(info_x, 72, name[:25])

        # Departman
        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(QColor(CARD_ACCENT))
        dept = self.employee.department.name if self.employee.department else "-"
        painter.drawText(info_x, 90, dept[:30])

        # Pozisyon
        painter.setPen(QColor("#94a3b8"))
        pos = self.employee.position.name if self.employee.position else "-"
        painter.drawText(info_x, 105, pos[:30])

        # Sicil No
        painter.setPen(QColor(CARD_TEXT))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(info_x, 130, f"Sicil: {self.employee.employee_no}")

        # QR Kod (sol alt)
        qr_x, qr_y = 15, 160
        qr_size = 45
        qr_pixmap = self._generate_qr(self.employee.employee_no)
        if qr_pixmap:
            scaled_qr = qr_pixmap.scaled(
                qr_size,
                qr_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap(qr_x, qr_y, scaled_qr)

        # Alt bilgi
        painter.setPen(QColor("#64748b"))
        painter.setFont(QFont("Segoe UI", 7))
        painter.drawText(75, 185, "Bu kart şirkete aittir.")
        painter.drawText(75, 197, "Kaybetme durumunda İK'ya başvurunuz.")

        painter.end()
        return pixmap

    def _get_photo(self) -> QPixmap:
        """Çalışan fotoğrafını getir, yoksa logo"""
        # Fotoğraf yolu kontrol et
        if self.employee.photo:
            photo_path = os.path.join(
                "assets", "photos", "employees", self.employee.photo
            )
            if os.path.exists(photo_path):
                return QPixmap(photo_path)

        # Fotoğraf yoksa logo kullan
        logo_path = os.path.join("assets", "images", "logo.svg")
        if os.path.exists(logo_path):
            return QPixmap(logo_path)

        # Hiçbiri yoksa None
        return None

    def _generate_qr(self, data: str) -> QPixmap:
        """QR kod oluştur"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=1,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # PIL Image'dan QPixmap'e çevir
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())
            return pixmap
        except Exception as e:
            print(f"QR oluşturma hatası: {e}")
            return None

    def _save_card(self):
        """Kartı dosyaya kaydet"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Kimlik Kartını Kaydet",
            f"kimlik_karti_{self.employee.employee_no}.png",
            "PNG Dosyası (*.png)",
        )

        if file_path:
            # Yüksek çözünürlüklü versiyon
            high_res = self._generate_high_res_card()
            high_res.save(file_path, "PNG")
            QMessageBox.information(
                self, "Kaydedildi", f"Kimlik kartı kaydedildi:\n{file_path}"
            )

    def _generate_high_res_card(self) -> QPixmap:
        """Yüksek çözünürlüklü kart (yazdırma için)"""
        # 300 DPI için 2x boyut
        scale = 2
        pixmap = QPixmap(CARD_WIDTH * scale, CARD_HEIGHT * scale)
        pixmap.fill(QColor(CARD_BG))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(scale, scale)

        # Header
        painter.fillRect(0, 0, CARD_WIDTH, 40, QColor(CARD_HEADER_BG))

        # Logo ve Şirket adı
        painter.setPen(QColor(CARD_TEXT))
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        painter.drawText(12, 28, "⚙ AKILLIŞ A.Ş.")

        # Fotoğraf
        photo_x, photo_y = 15, 55
        photo_w, photo_h = 80, 100

        photo_pixmap = self._get_photo()
        if photo_pixmap:
            scaled = photo_pixmap.scaled(
                photo_w * scale,
                photo_h * scale,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x_offset = (scaled.width() - photo_w * scale) // 2
            y_offset = (scaled.height() - photo_h * scale) // 2
            cropped = scaled.copy(x_offset, y_offset, photo_w * scale, photo_h * scale)
            painter.drawPixmap(photo_x, photo_y, cropped.scaled(photo_w, photo_h))
        else:
            painter.fillRect(photo_x, photo_y, photo_w, photo_h, QColor("#334155"))
            painter.setPen(QColor("#64748b"))
            painter.setFont(QFont("Segoe UI", 24))
            painter.drawText(
                photo_x, photo_y, photo_w, photo_h, Qt.AlignmentFlag.AlignCenter, "👤"
            )

        painter.setPen(QPen(QColor(CARD_ACCENT), 2))
        painter.drawRect(photo_x, photo_y, photo_w, photo_h)

        # Bilgiler
        info_x = 110
        painter.setPen(QColor(CARD_TEXT))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.drawText(info_x, 72, self.employee.full_name.upper()[:25])

        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(QColor(CARD_ACCENT))
        dept = self.employee.department.name if self.employee.department else "-"
        painter.drawText(info_x, 90, dept[:30])

        painter.setPen(QColor("#94a3b8"))
        pos = self.employee.position.name if self.employee.position else "-"
        painter.drawText(info_x, 105, pos[:30])

        painter.setPen(QColor(CARD_TEXT))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(info_x, 130, f"Sicil: {self.employee.employee_no}")

        # QR
        qr_pixmap = self._generate_qr(self.employee.employee_no)
        if qr_pixmap:
            painter.drawPixmap(15, 160, qr_pixmap.scaled(45, 45))

        painter.setPen(QColor("#64748b"))
        painter.setFont(QFont("Segoe UI", 7))
        painter.drawText(75, 185, "Bu kart şirkete aittir.")
        painter.drawText(75, 197, "Kaybetme durumunda İK'ya başvurunuz.")

        painter.end()
        return pixmap

    def _print_card(self):
        """Kartı yazdır - 8.6 x 5.4 cm boyutunda"""
        from PyQt6.QtCore import QSizeF, QMarginsF
        from PyQt6.QtGui import QPageSize, QPageLayout

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)

        # Kimlik kartı boyutları: 86mm x 54mm (8.6 x 5.4 cm)
        card_size = QSizeF(86, 54)  # mm cinsinden
        page_size = QPageSize(card_size, QPageSize.Unit.Millimeter, "ID Card")

        # Sayfa düzeni - kenar boşluksuz
        margins = QMarginsF(0, 0, 0, 0)
        page_layout = QPageLayout(
            page_size,
            QPageLayout.Orientation.Landscape,
            margins,
            QPageLayout.Unit.Millimeter,
        )
        printer.setPageLayout(page_layout)

        dialog = QPrintDialog(printer, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            painter = QPainter(printer)

            # Yazdırma alanını al
            page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)

            # Yüksek çözünürlüklü kart oluştur
            high_res = self._generate_print_card()

            # Kartı sayfa boyutuna ölçekle
            scaled = high_res.scaled(
                int(page_rect.width()),
                int(page_rect.height()),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            # Ortala ve yazdır
            x = int((page_rect.width() - scaled.width()) / 2)
            y = int((page_rect.height() - scaled.height()) / 2)

            painter.drawPixmap(x, y, scaled)
            painter.end()

            QMessageBox.information(
                self,
                "Yazdırıldı",
                "Kimlik kartı yazıcıya gönderildi.\n" "Kart boyutu: 8.6 x 5.4 cm",
            )

    def _generate_print_card(self) -> QPixmap:
        """Yazdırma için yüksek çözünürlüklü kart (300 DPI)"""
        # 300 DPI için: 86mm = 1016px, 54mm = 638px
        print_width = 1016
        print_height = 638

        pixmap = QPixmap(print_width, print_height)
        pixmap.fill(QColor(CARD_BG))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Ölçek faktörü
        scale_x = print_width / CARD_WIDTH
        scale_y = print_height / CARD_HEIGHT
        scale = min(scale_x, scale_y)
        painter.scale(scale, scale)

        # Header
        painter.fillRect(0, 0, CARD_WIDTH, 40, QColor(CARD_HEADER_BG))

        # Logo ve Şirket adı
        painter.setPen(QColor(CARD_TEXT))
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        painter.drawText(12, 28, "⚙ AKILLIŞ A.Ş.")

        # Fotoğraf
        photo_x, photo_y = 15, 55
        photo_w, photo_h = 80, 100

        photo_pixmap = self._get_photo()
        if photo_pixmap:
            scaled_photo = photo_pixmap.scaled(
                int(photo_w * scale),
                int(photo_h * scale),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x_off = (scaled_photo.width() - int(photo_w * scale)) // 2
            y_off = (scaled_photo.height() - int(photo_h * scale)) // 2
            cropped = scaled_photo.copy(
                x_off, y_off, int(photo_w * scale), int(photo_h * scale)
            )
            painter.drawPixmap(photo_x, photo_y, cropped.scaled(photo_w, photo_h))
        else:
            painter.fillRect(photo_x, photo_y, photo_w, photo_h, QColor("#334155"))
            painter.setPen(QColor("#64748b"))
            painter.setFont(QFont("Segoe UI", 24))
            painter.drawText(
                photo_x, photo_y, photo_w, photo_h, Qt.AlignmentFlag.AlignCenter, "👤"
            )

        painter.setPen(QPen(QColor(CARD_ACCENT), 2))
        painter.drawRect(photo_x, photo_y, photo_w, photo_h)

        # Bilgiler
        info_x = 110
        painter.setPen(QColor(CARD_TEXT))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.drawText(info_x, 72, self.employee.full_name.upper()[:25])

        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(QColor(CARD_ACCENT))
        dept = self.employee.department.name if self.employee.department else "-"
        painter.drawText(info_x, 90, dept[:30])

        painter.setPen(QColor("#94a3b8"))
        pos = self.employee.position.name if self.employee.position else "-"
        painter.drawText(info_x, 105, pos[:30])

        painter.setPen(QColor(CARD_TEXT))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(info_x, 130, f"Sicil: {self.employee.employee_no}")

        # QR
        qr_pixmap = self._generate_qr(self.employee.employee_no)
        if qr_pixmap:
            painter.drawPixmap(15, 160, qr_pixmap.scaled(45, 45))

        painter.setPen(QColor("#64748b"))
        painter.setFont(QFont("Segoe UI", 7))
        painter.drawText(75, 185, "Bu kart şirkete aittir.")
        painter.drawText(75, 197, "Kaybetme durumunda İK'ya başvurunuz.")

        painter.end()
        return pixmap
