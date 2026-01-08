"""
Akıllı İş - Müşteri Form Sayfası
"""

from typing import Optional
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QFrame, QMessageBox, QGridLayout, QScrollArea, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal


class CustomerFormPage(QWidget):
    """Müşteri formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(self, customer_data: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.customer_data = customer_data
        self.is_edit_mode = customer_data is not None
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
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #334155;
                color: #94a3b8;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #334155; color: #f8fafc; }
        """)
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)

        title_text = "Müşteri Düzenle" if self.is_edit_mode else "Yeni Müşteri"
        title = QLabel(f"👥 {title_text}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc; margin-left: 16px;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #a855f7);
                border: none;
                color: white;
                font-weight: 600;
                padding: 12px 24px;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #9333ea);
            }
        """)
        save_btn.clicked.connect(self._on_save)
        header_layout.addWidget(save_btn)

        layout.addLayout(header_layout)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: rgba(30, 41, 59, 0.3);
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 16px;
            }
            QTabBar::tab {
                background-color: #1e293b;
                color: #94a3b8;
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background-color: #334155;
                color: #f8fafc;
            }
            QTabBar::tab:hover {
                background-color: #334155;
            }
        """)

        # Tab 1: Temel Bilgiler
        tab1 = self._create_basic_tab()
        self.tabs.addTab(tab1, "📋 Temel Bilgiler")

        # Tab 2: İletişim
        tab2 = self._create_contact_tab()
        self.tabs.addTab(tab2, "📞 İletişim")

        # Tab 3: Ticari Bilgiler
        tab3 = self._create_commercial_tab()
        self.tabs.addTab(tab3, "💼 Ticari Bilgiler")

        # Tab 4: Banka Bilgileri
        tab4 = self._create_bank_tab()
        self.tabs.addTab(tab4, "🏦 Banka Bilgileri")

        layout.addWidget(self.tabs)

    def _create_basic_tab(self) -> QWidget:
        """Temel bilgiler sekmesi"""
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")

        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.setColumnMinimumWidth(0, 150)

        row = 0

        # Kod
        layout.addWidget(self._create_label("Müşteri Kodu *"), row, 0)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Otomatik oluşturulacak")
        self._style_input(self.code_input)
        layout.addWidget(self.code_input, row, 1)
        row += 1

        # Ad
        layout.addWidget(self._create_label("Müşteri Adı *"), row, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Şirket veya kişi adı")
        self._style_input(self.name_input)
        layout.addWidget(self.name_input, row, 1)
        row += 1

        # Kısa Ad
        layout.addWidget(self._create_label("Kısa Ad"), row, 0)
        self.short_name_input = QLineEdit()
        self.short_name_input.setPlaceholderText("Kısa isim (opsiyonel)")
        self._style_input(self.short_name_input)
        layout.addWidget(self.short_name_input, row, 1)
        row += 1

        # Vergi No
        layout.addWidget(self._create_label("Vergi Numarası"), row, 0)
        self.tax_number_input = QLineEdit()
        self.tax_number_input.setPlaceholderText("Vergi numarası")
        self._style_input(self.tax_number_input)
        layout.addWidget(self.tax_number_input, row, 1)
        row += 1

        # Vergi Dairesi
        layout.addWidget(self._create_label("Vergi Dairesi"), row, 0)
        self.tax_office_input = QLineEdit()
        self.tax_office_input.setPlaceholderText("Vergi dairesi adı")
        self._style_input(self.tax_office_input)
        layout.addWidget(self.tax_office_input, row, 1)
        row += 1

        # Notlar
        layout.addWidget(self._create_label("Notlar"), row, 0)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        self.notes_input.setPlaceholderText("Ek notlar...")
        self._style_textedit(self.notes_input)
        layout.addWidget(self.notes_input, row, 1)
        row += 1

        layout.setRowStretch(row, 1)
        return tab

    def _create_contact_tab(self) -> QWidget:
        """İletişim sekmesi"""
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")

        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.setColumnMinimumWidth(0, 150)

        row = 0

        # Yetkili Kişi
        layout.addWidget(self._create_label("Yetkili Kişi"), row, 0)
        self.contact_person_input = QLineEdit()
        self.contact_person_input.setPlaceholderText("Ad Soyad")
        self._style_input(self.contact_person_input)
        layout.addWidget(self.contact_person_input, row, 1)
        row += 1

        # Telefon
        layout.addWidget(self._create_label("Telefon"), row, 0)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("0212 XXX XX XX")
        self._style_input(self.phone_input)
        layout.addWidget(self.phone_input, row, 1)
        row += 1

        # Mobil
        layout.addWidget(self._create_label("Mobil"), row, 0)
        self.mobile_input = QLineEdit()
        self.mobile_input.setPlaceholderText("0532 XXX XX XX")
        self._style_input(self.mobile_input)
        layout.addWidget(self.mobile_input, row, 1)
        row += 1

        # Fax
        layout.addWidget(self._create_label("Faks"), row, 0)
        self.fax_input = QLineEdit()
        self.fax_input.setPlaceholderText("Faks numarası")
        self._style_input(self.fax_input)
        layout.addWidget(self.fax_input, row, 1)
        row += 1

        # E-posta
        layout.addWidget(self._create_label("E-posta"), row, 0)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("ornek@sirket.com")
        self._style_input(self.email_input)
        layout.addWidget(self.email_input, row, 1)
        row += 1

        # Website
        layout.addWidget(self._create_label("Website"), row, 0)
        self.website_input = QLineEdit()
        self.website_input.setPlaceholderText("www.sirket.com")
        self._style_input(self.website_input)
        layout.addWidget(self.website_input, row, 1)
        row += 1

        # Adres
        layout.addWidget(self._create_label("Adres"), row, 0)
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)
        self.address_input.setPlaceholderText("Açık adres")
        self._style_textedit(self.address_input)
        layout.addWidget(self.address_input, row, 1)
        row += 1

        # Şehir / İlçe
        city_layout = QHBoxLayout()

        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Şehir")
        self._style_input(self.city_input)
        city_layout.addWidget(self.city_input)

        self.district_input = QLineEdit()
        self.district_input.setPlaceholderText("İlçe")
        self._style_input(self.district_input)
        city_layout.addWidget(self.district_input)

        layout.addWidget(self._create_label("Şehir / İlçe"), row, 0)
        layout.addLayout(city_layout, row, 1)
        row += 1

        # Posta Kodu / Ülke
        postal_layout = QHBoxLayout()

        self.postal_code_input = QLineEdit()
        self.postal_code_input.setPlaceholderText("Posta Kodu")
        self._style_input(self.postal_code_input)
        postal_layout.addWidget(self.postal_code_input)

        self.country_input = QLineEdit()
        self.country_input.setPlaceholderText("Ülke")
        self.country_input.setText("Türkiye")
        self._style_input(self.country_input)
        postal_layout.addWidget(self.country_input)

        layout.addWidget(self._create_label("Posta Kodu / Ülke"), row, 0)
        layout.addLayout(postal_layout, row, 1)
        row += 1

        layout.setRowStretch(row, 1)
        return tab

    def _create_commercial_tab(self) -> QWidget:
        """Ticari bilgiler sekmesi"""
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")

        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.setColumnMinimumWidth(0, 150)

        row = 0

        # Para Birimi
        layout.addWidget(self._create_label("Para Birimi"), row, 0)
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["TRY", "USD", "EUR", "GBP"])
        self._style_combo(self.currency_combo)
        layout.addWidget(self.currency_combo, row, 1)
        row += 1

        # Ödeme Vadesi
        layout.addWidget(self._create_label("Ödeme Vadesi (Gün)"), row, 0)
        self.payment_term_input = QSpinBox()
        self.payment_term_input.setRange(0, 365)
        self.payment_term_input.setValue(30)
        self._style_spinbox(self.payment_term_input)
        layout.addWidget(self.payment_term_input, row, 1)
        row += 1

        # Kredi Limiti
        layout.addWidget(self._create_label("Kredi Limiti (₺)"), row, 0)
        self.credit_limit_input = QDoubleSpinBox()
        self.credit_limit_input.setRange(0, 999999999)
        self.credit_limit_input.setDecimals(2)
        self.credit_limit_input.setSingleStep(1000)
        self._style_spinbox(self.credit_limit_input)
        layout.addWidget(self.credit_limit_input, row, 1)
        row += 1

        # Puan
        layout.addWidget(self._create_label("Değerlendirme (1-5)"), row, 0)
        self.rating_input = QSpinBox()
        self.rating_input.setRange(0, 5)
        self.rating_input.setValue(0)
        self._style_spinbox(self.rating_input)
        layout.addWidget(self.rating_input, row, 1)
        row += 1

        layout.setRowStretch(row, 1)
        return tab

    def _create_bank_tab(self) -> QWidget:
        """Banka bilgileri sekmesi"""
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")

        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.setColumnMinimumWidth(0, 150)

        row = 0

        # Banka Adı
        layout.addWidget(self._create_label("Banka Adı"), row, 0)
        self.bank_name_input = QLineEdit()
        self.bank_name_input.setPlaceholderText("Banka adı")
        self._style_input(self.bank_name_input)
        layout.addWidget(self.bank_name_input, row, 1)
        row += 1

        # Şube
        layout.addWidget(self._create_label("Şube"), row, 0)
        self.bank_branch_input = QLineEdit()
        self.bank_branch_input.setPlaceholderText("Şube adı")
        self._style_input(self.bank_branch_input)
        layout.addWidget(self.bank_branch_input, row, 1)
        row += 1

        # Hesap No
        layout.addWidget(self._create_label("Hesap No"), row, 0)
        self.bank_account_input = QLineEdit()
        self.bank_account_input.setPlaceholderText("Hesap numarası")
        self._style_input(self.bank_account_input)
        layout.addWidget(self.bank_account_input, row, 1)
        row += 1

        # IBAN
        layout.addWidget(self._create_label("IBAN"), row, 0)
        self.iban_input = QLineEdit()
        self.iban_input.setPlaceholderText("TRXX XXXX XXXX XXXX XXXX XXXX XX")
        self._style_input(self.iban_input)
        layout.addWidget(self.iban_input, row, 1)
        row += 1

        layout.setRowStretch(row, 1)
        return tab

    def _create_label(self, text: str) -> QLabel:
        """Label oluştur"""
        label = QLabel(text)
        label.setStyleSheet("color: #94a3b8; font-size: 14px; background: transparent;")
        return label

    def _style_input(self, widget: QLineEdit):
        """Input stili"""
        widget.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 14px;
                color: #f8fafc;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #6366f1;
            }
        """)

    def _style_textedit(self, widget: QTextEdit):
        """TextEdit stili"""
        widget.setStyleSheet("""
            QTextEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                color: #f8fafc;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #6366f1;
            }
        """)

    def _style_combo(self, widget: QComboBox):
        """ComboBox stili"""
        widget.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 14px;
                color: #f8fafc;
                font-size: 14px;
            }
            QComboBox:focus {
                border-color: #6366f1;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #f8fafc;
                selection-background-color: #6366f1;
            }
        """)

    def _style_spinbox(self, widget):
        """SpinBox stili"""
        widget.setStyleSheet("""
            QSpinBox, QDoubleSpinBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 14px;
                color: #f8fafc;
                font-size: 14px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #6366f1;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                background-color: #334155;
                border: none;
                width: 20px;
            }
        """)

    def load_data(self):
        """Verileri form alanlarına yükle"""
        if not self.customer_data:
            return

        data = self.customer_data

        # Temel bilgiler
        self.code_input.setText(data.get("code", ""))
        self.name_input.setText(data.get("name", ""))
        self.short_name_input.setText(data.get("short_name", "") or "")
        self.tax_number_input.setText(data.get("tax_number", "") or "")
        self.tax_office_input.setText(data.get("tax_office", "") or "")
        self.notes_input.setText(data.get("notes", "") or "")

        # İletişim
        self.contact_person_input.setText(data.get("contact_person", "") or "")
        self.phone_input.setText(data.get("phone", "") or "")
        self.mobile_input.setText(data.get("mobile", "") or "")
        self.fax_input.setText(data.get("fax", "") or "")
        self.email_input.setText(data.get("email", "") or "")
        self.website_input.setText(data.get("website", "") or "")
        self.address_input.setText(data.get("address", "") or "")
        self.city_input.setText(data.get("city", "") or "")
        self.district_input.setText(data.get("district", "") or "")
        self.postal_code_input.setText(data.get("postal_code", "") or "")
        self.country_input.setText(data.get("country", "Türkiye") or "Türkiye")

        # Ticari
        currency = data.get("currency", "TRY")
        index = self.currency_combo.findText(currency)
        if index >= 0:
            self.currency_combo.setCurrentIndex(index)

        self.payment_term_input.setValue(data.get("payment_term_days", 30) or 30)
        self.credit_limit_input.setValue(float(data.get("credit_limit", 0) or 0))
        self.rating_input.setValue(data.get("rating", 0) or 0)

        # Banka
        self.bank_name_input.setText(data.get("bank_name", "") or "")
        self.bank_branch_input.setText(data.get("bank_branch", "") or "")
        self.bank_account_input.setText(data.get("bank_account_no", "") or "")
        self.iban_input.setText(data.get("iban", "") or "")

    def _on_save(self):
        """Kaydet"""
        # Validasyon
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Uyarı", "Müşteri adı zorunludur!")
            self.name_input.setFocus()
            return

        # Verileri topla
        data = {
            "code": self.code_input.text().strip(),
            "name": self.name_input.text().strip(),
            "short_name": self.short_name_input.text().strip() or None,
            "tax_number": self.tax_number_input.text().strip() or None,
            "tax_office": self.tax_office_input.text().strip() or None,
            "notes": self.notes_input.toPlainText().strip() or None,

            "contact_person": self.contact_person_input.text().strip() or None,
            "phone": self.phone_input.text().strip() or None,
            "mobile": self.mobile_input.text().strip() or None,
            "fax": self.fax_input.text().strip() or None,
            "email": self.email_input.text().strip() or None,
            "website": self.website_input.text().strip() or None,
            "address": self.address_input.toPlainText().strip() or None,
            "city": self.city_input.text().strip() or None,
            "district": self.district_input.text().strip() or None,
            "postal_code": self.postal_code_input.text().strip() or None,
            "country": self.country_input.text().strip() or "Türkiye",

            "currency": self.currency_combo.currentText(),
            "payment_term_days": self.payment_term_input.value(),
            "credit_limit": Decimal(str(self.credit_limit_input.value())),
            "rating": self.rating_input.value(),

            "bank_name": self.bank_name_input.text().strip() or None,
            "bank_branch": self.bank_branch_input.text().strip() or None,
            "bank_account_no": self.bank_account_input.text().strip() or None,
            "iban": self.iban_input.text().strip() or None,
        }

        # Edit modunda ID ekle
        if self.is_edit_mode and self.customer_data:
            data["id"] = self.customer_data.get("id")

        self.saved.emit(data)
