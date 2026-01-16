"""
Akıllı İş - Aday Müşteri Form Sayfası
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QGridLayout,
    QMessageBox,
    QTabWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal
from database.models.crm import LeadStatus, LeadSource


class LeadFormPage(QWidget):
    """Aday Müşteri (Lead) formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(self, lead_data: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.lead_data = lead_data
        self.is_edit_mode = lead_data is not None
        self.setup_ui()
        if self.is_edit_mode:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        back_btn = QPushButton("← Geri")
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)

        title_text = (
            "Aday Müşteri Düzenle" if self.is_edit_mode else "Yeni Aday Müşteri"
        )
        title = QLabel(f"🚀 {title_text}")
        header_layout.addWidget(title)
        header_layout.addStretch()

        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(self._on_save)
        header_layout.addWidget(save_btn)

        layout.addLayout(header_layout)

        # Tab Widget
        self.tabs = QTabWidget()

        # Tab 1: Temel Bilgiler
        tab1 = self._create_basic_tab()
        self.tabs.addTab(tab1, "📋 Kimlik & İletişim")

        # Tab 2: Detaylar (Adres, Durum)
        tab2 = self._create_details_tab()
        self.tabs.addTab(tab2, "📍 Detaylar")

        layout.addWidget(self.tabs)

    def _create_basic_tab(self) -> QWidget:
        """Temel bilgiler sekmesi"""
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.setColumnMinimumWidth(0, 150)

        row = 0

        # Ad
        layout.addWidget(self._create_label("Ad *"), row, 0)
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("İsim")
        layout.addWidget(self.first_name_input, row, 1)
        row += 1

        # Soyad
        layout.addWidget(self._create_label("Soyad *"), row, 0)
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Soyisim")
        layout.addWidget(self.last_name_input, row, 1)
        row += 1

        # Şirket
        layout.addWidget(self._create_label("Şirket Adı"), row, 0)
        self.company_name_input = QLineEdit()
        self.company_name_input.setPlaceholderText("Firma unvanı")
        layout.addWidget(self.company_name_input, row, 1)
        row += 1

        # Unvan
        layout.addWidget(self._create_label("Unvan"), row, 0)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Örn: Satın Alma Müdürü")
        layout.addWidget(self.title_input, row, 1)
        row += 1

        # Telefon
        layout.addWidget(self._create_label("Telefon"), row, 0)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("0212 XXX XX XX")
        layout.addWidget(self.phone_input, row, 1)
        row += 1

        # Mobil
        layout.addWidget(self._create_label("Mobil"), row, 0)
        self.mobile_input = QLineEdit()
        self.mobile_input.setPlaceholderText("0532 XXX XX XX")
        layout.addWidget(self.mobile_input, row, 1)
        row += 1

        # E-posta
        layout.addWidget(self._create_label("E-posta"), row, 0)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("ornek@sirket.com")
        layout.addWidget(self.email_input, row, 1)
        row += 1

        # Website
        layout.addWidget(self._create_label("Website"), row, 0)
        self.website_input = QLineEdit()
        self.website_input.setPlaceholderText("www.sirket.com")
        layout.addWidget(self.website_input, row, 1)
        row += 1

        layout.setRowStretch(row, 1)
        return tab

    def _create_details_tab(self) -> QWidget:
        """Detaylar sekmesi"""
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.setColumnMinimumWidth(0, 150)

        row = 0

        # Durum
        layout.addWidget(self._create_label("Durum"), row, 0)
        self.status_combo = QComboBox()
        self.status_combo.addItems([e.value for e in LeadStatus])
        layout.addWidget(self.status_combo, row, 1)
        row += 1

        # Kaynak
        layout.addWidget(self._create_label("Kaynak"), row, 0)
        self.source_combo = QComboBox()
        self.source_combo.addItems([e.value for e in LeadSource])
        layout.addWidget(self.source_combo, row, 1)
        row += 1

        # Şehir
        layout.addWidget(self._create_label("Şehir"), row, 0)
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Şehir")
        layout.addWidget(self.city_input, row, 1)
        row += 1

        # Ülke
        layout.addWidget(self._create_label("Ülke"), row, 0)
        self.country_input = QLineEdit()
        self.country_input.setText("Türkiye")
        layout.addWidget(self.country_input, row, 1)
        row += 1

        # Adres
        layout.addWidget(self._create_label("Adres"), row, 0)
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)
        self.address_input.setPlaceholderText("Açık adres")
        layout.addWidget(self.address_input, row, 1)
        row += 1

        # Notlar
        layout.addWidget(self._create_label("Notlar"), row, 0)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        self.notes_input.setPlaceholderText("Görüşme notları, hatırlatmalar...")
        layout.addWidget(self.notes_input, row, 1)
        row += 1

        layout.setRowStretch(row, 1)
        return tab

    def _create_label(self, text: str) -> QLabel:
        """Label oluştur"""
        label = QLabel(text)
        return label

    def load_data(self):
        """Verileri yükle"""
        if not self.lead_data:
            return

        data = self.lead_data

        # Temel
        self.first_name_input.setText(data.get("first_name", ""))
        self.last_name_input.setText(data.get("last_name", ""))
        self.company_name_input.setText(data.get("company_name", "") or "")
        self.title_input.setText(data.get("title", "") or "")
        self.phone_input.setText(data.get("phone", "") or "")
        self.mobile_input.setText(data.get("mobile", "") or "")
        self.email_input.setText(data.get("email", "") or "")
        self.website_input.setText(data.get("website", "") or "")

        # Detay
        status = data.get("status")
        if status:
            idx = self.status_combo.findText(status)
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)

        source = data.get("source")
        if source:
            idx = self.source_combo.findText(source)
            if idx >= 0:
                self.source_combo.setCurrentIndex(idx)

        self.city_input.setText(data.get("city", "") or "")
        self.country_input.setText(data.get("country", "Türkiye"))
        self.address_input.setText(data.get("address", "") or "")
        self.notes_input.setText(data.get("notes", "") or "")

    def _on_save(self):
        """Kaydet"""
        if (
            not self.first_name_input.text().strip()
            or not self.last_name_input.text().strip()
        ):
            QMessageBox.warning(self, "Uyarı", "Ad ve Soyad zorunludur!")
            return

        data = {
            "first_name": self.first_name_input.text().strip(),
            "last_name": self.last_name_input.text().strip(),
            "company_name": self.company_name_input.text().strip() or None,
            "title": self.title_input.text().strip() or None,
            "phone": self.phone_input.text().strip() or None,
            "mobile": self.mobile_input.text().strip() or None,
            "email": self.email_input.text().strip() or None,
            "website": self.website_input.text().strip() or None,
            "status": self.status_combo.currentText(),
            "source": self.source_combo.currentText(),
            "city": self.city_input.text().strip() or None,
            "country": self.country_input.text().strip(),
            "address": self.address_input.toPlainText().strip() or None,
            "notes": self.notes_input.toPlainText().strip() or None,
        }

        if self.is_edit_mode and self.lead_data:
            data["id"] = self.lead_data.get("id")

        self.saved.emit(data)
