"""
Akıllı İş - Tedarikçi Form Sayfası
"""

from typing import Optional
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QFrame, QMessageBox, QGridLayout, QScrollArea, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal

class SupplierFormPage(QWidget):
    """Tedarikçi formu"""
    
    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()
    
    def __init__(self, supplier_data: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.supplier_data = supplier_data
        self.is_edit_mode = supplier_data is not None
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
        
        title_text = "Tedarikçi Düzenle" if self.is_edit_mode else "Yeni Tedarikçi"
        title = QLabel(f"🏢 {title_text}")
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
        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.setColumnMinimumWidth(0, 150)
        
        row = 0
        
        # Kod
        layout.addWidget(self._create_label("Tedarikçi Kodu *"), row, 0)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Otomatik oluşturulacak")
        layout.addWidget(self.code_input, row, 1)
        row += 1
        
        # Ad
        layout.addWidget(self._create_label("Tedarikçi Adı *"), row, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Şirket adı")
        layout.addWidget(self.name_input, row, 1)
        row += 1
        
        # Kısa Ad
        layout.addWidget(self._create_label("Kısa Ad"), row, 0)
        self.short_name_input = QLineEdit()
        self.short_name_input.setPlaceholderText("Kısa isim (opsiyonel)")
        layout.addWidget(self.short_name_input, row, 1)
        row += 1
        
        # Vergi No
        layout.addWidget(self._create_label("Vergi Numarası"), row, 0)
        self.tax_number_input = QLineEdit()
        self.tax_number_input.setPlaceholderText("Vergi numarası")
        layout.addWidget(self.tax_number_input, row, 1)
        row += 1
        
        # Vergi Dairesi
        layout.addWidget(self._create_label("Vergi Dairesi"), row, 0)
        self.tax_office_input = QLineEdit()
        self.tax_office_input.setPlaceholderText("Vergi dairesi adı")
        layout.addWidget(self.tax_office_input, row, 1)
        row += 1
        
        # Notlar
        layout.addWidget(self._create_label("Notlar"), row, 0)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        self.notes_input.setPlaceholderText("Ek notlar...")
        layout.addWidget(self.notes_input, row, 1)
        row += 1
        
        layout.setRowStretch(row, 1)
        return tab
        
    def _create_contact_tab(self) -> QWidget:
        """İletişim sekmesi"""
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.setColumnMinimumWidth(0, 150)
        
        row = 0
        
        # Yetkili Kişi
        layout.addWidget(self._create_label("Yetkili Kişi"), row, 0)
        self.contact_person_input = QLineEdit()
        self.contact_person_input.setPlaceholderText("Ad Soyad")
        layout.addWidget(self.contact_person_input, row, 1)
        row += 1
        
        # Telefon
        layout.addWidget(self._create_label("Telefon"), row, 0)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("(5XX) XXX XX XX")
        layout.addWidget(self.phone_input, row, 1)
        row += 1
        
        # Cep Telefonu
        layout.addWidget(self._create_label("Cep Telefonu"), row, 0)
        self.mobile_input = QLineEdit()
        self.mobile_input.setPlaceholderText("(5XX) XXX XX XX")
        layout.addWidget(self.mobile_input, row, 1)
        row += 1
        
        # Faks
        layout.addWidget(self._create_label("Faks"), row, 0)
        self.fax_input = QLineEdit()
        layout.addWidget(self.fax_input, row, 1)
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
        
        # Adres
        layout.addWidget(self._create_label("Adres"), row, 0)
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)
        self.address_input.setPlaceholderText("Tam adres")
        layout.addWidget(self.address_input, row, 1)
        row += 1
        
        # Şehir / İlçe
        layout.addWidget(self._create_label("Şehir / İlçe"), row, 0)
        city_layout = QHBoxLayout()
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Şehir")
        city_layout.addWidget(self.city_input)
        
        self.district_input = QLineEdit()
        self.district_input.setPlaceholderText("İlçe")
        city_layout.addWidget(self.district_input)
        layout.addLayout(city_layout, row, 1)
        row += 1
        
        # Posta Kodu / Ülke
        layout.addWidget(self._create_label("Posta Kodu / Ülke"), row, 0)
        postal_layout = QHBoxLayout()
        self.postal_code_input = QLineEdit()
        self.postal_code_input.setPlaceholderText("Posta kodu")
        self.postal_code_input.setMaximumWidth(120)
        postal_layout.addWidget(self.postal_code_input)
        
        self.country_input = QLineEdit()
        self.country_input.setText("Türkiye")
        postal_layout.addWidget(self.country_input)
        layout.addLayout(postal_layout, row, 1)
        row += 1
        
        layout.setRowStretch(row, 1)
        return tab
        
    def _create_commercial_tab(self) -> QWidget:
        """Ticari bilgiler sekmesi"""
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.setColumnMinimumWidth(0, 150)
        
        row = 0
        
        # Ödeme Vadesi
        layout.addWidget(self._create_label("Ödeme Vadesi"), row, 0)
        vade_layout = QHBoxLayout()
        self.payment_term_input = QSpinBox()
        self.payment_term_input.setRange(0, 365)
        self.payment_term_input.setValue(30)
        self.payment_term_input.setSuffix(" gün")
        vade_layout.addWidget(self.payment_term_input)
        vade_layout.addStretch()
        layout.addLayout(vade_layout, row, 1)
        row += 1
        
        # Kredi Limiti
        layout.addWidget(self._create_label("Kredi Limiti"), row, 0)
        limit_layout = QHBoxLayout()
        self.credit_limit_input = QDoubleSpinBox()
        self.credit_limit_input.setRange(0, 999999999)
        self.credit_limit_input.setDecimals(2)
        self.credit_limit_input.setPrefix("₺ ")
        self.credit_limit_input.setMinimumWidth(200)
        limit_layout.addWidget(self.credit_limit_input)
        limit_layout.addStretch()
        layout.addLayout(limit_layout, row, 1)
        row += 1
        
        # Para Birimi
        layout.addWidget(self._create_label("Para Birimi"), row, 0)
        self.currency_combo = QComboBox()
        self.currency_combo.addItem("🇹🇷 Türk Lirası (TRY)", "TRY")
        self.currency_combo.addItem("🇺🇸 Amerikan Doları (USD)", "USD")
        self.currency_combo.addItem("🇪🇺 Euro (EUR)", "EUR")
        self.currency_combo.addItem("🇬🇧 İngiliz Sterlini (GBP)", "GBP")
        layout.addWidget(self.currency_combo, row, 1)
        row += 1
        
        # Değerlendirme
        layout.addWidget(self._create_label("Değerlendirme"), row, 0)
        rating_layout = QHBoxLayout()
        self.rating_input = QSpinBox()
        self.rating_input.setRange(0, 5)
        self.rating_input.setValue(0)
        self.rating_input.setPrefix("⭐ ")
        rating_layout.addWidget(self.rating_input)
        
        rating_info = QLabel("(0-5 arası puan)")
        rating_layout.addWidget(rating_info)
        rating_layout.addStretch()
        layout.addLayout(rating_layout, row, 1)
        row += 1
        
        layout.setRowStretch(row, 1)
        return tab
        
    def _create_bank_tab(self) -> QWidget:
        """Banka bilgileri sekmesi"""
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.setColumnMinimumWidth(0, 150)
        
        row = 0
        
        # Banka Adı
        layout.addWidget(self._create_label("Banka Adı"), row, 0)
        self.bank_name_input = QLineEdit()
        self.bank_name_input.setPlaceholderText("Banka adı")
        layout.addWidget(self.bank_name_input, row, 1)
        row += 1
        
        # Şube
        layout.addWidget(self._create_label("Şube"), row, 0)
        self.bank_branch_input = QLineEdit()
        self.bank_branch_input.setPlaceholderText("Şube adı")
        layout.addWidget(self.bank_branch_input, row, 1)
        row += 1
        
        # Hesap No
        layout.addWidget(self._create_label("Hesap Numarası"), row, 0)
        self.bank_account_input = QLineEdit()
        self.bank_account_input.setPlaceholderText("Hesap numarası")
        layout.addWidget(self.bank_account_input, row, 1)
        row += 1
        
        # IBAN
        layout.addWidget(self._create_label("IBAN"), row, 0)
        self.iban_input = QLineEdit()
        self.iban_input.setPlaceholderText("TRXX XXXX XXXX XXXX XXXX XXXX XX")
        layout.addWidget(self.iban_input, row, 1)
        row += 1
        
        layout.setRowStretch(row, 1)
        return tab
        
    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return label
        
    def load_data(self):
        """Düzenleme modunda verileri yükle"""
        if not self.supplier_data:
            return
        
        # Temel
        self.code_input.setText(self.supplier_data.get("code", ""))
        self.name_input.setText(self.supplier_data.get("name", ""))
        self.short_name_input.setText(self.supplier_data.get("short_name", "") or "")
        self.tax_number_input.setText(self.supplier_data.get("tax_number", "") or "")
        self.tax_office_input.setText(self.supplier_data.get("tax_office", "") or "")
        self.notes_input.setPlainText(self.supplier_data.get("notes", "") or "")
        
        # İletişim
        self.contact_person_input.setText(self.supplier_data.get("contact_person", "") or "")
        self.phone_input.setText(self.supplier_data.get("phone", "") or "")
        self.mobile_input.setText(self.supplier_data.get("mobile", "") or "")
        self.fax_input.setText(self.supplier_data.get("fax", "") or "")
        self.email_input.setText(self.supplier_data.get("email", "") or "")
        self.website_input.setText(self.supplier_data.get("website", "") or "")
        self.address_input.setPlainText(self.supplier_data.get("address", "") or "")
        self.city_input.setText(self.supplier_data.get("city", "") or "")
        self.district_input.setText(self.supplier_data.get("district", "") or "")
        self.postal_code_input.setText(self.supplier_data.get("postal_code", "") or "")
        self.country_input.setText(self.supplier_data.get("country", "Türkiye") or "Türkiye")
        
        # Ticari
        self.payment_term_input.setValue(self.supplier_data.get("payment_term_days", 30) or 30)
        self.credit_limit_input.setValue(float(self.supplier_data.get("credit_limit", 0) or 0))
        
        currency = self.supplier_data.get("currency", "TRY")
        for i in range(self.currency_combo.count()):
            if self.currency_combo.itemData(i) == currency:
                self.currency_combo.setCurrentIndex(i)
                break
        
        self.rating_input.setValue(self.supplier_data.get("rating", 0) or 0)
        
        # Banka
        self.bank_name_input.setText(self.supplier_data.get("bank_name", "") or "")
        self.bank_branch_input.setText(self.supplier_data.get("bank_branch", "") or "")
        self.bank_account_input.setText(self.supplier_data.get("bank_account_no", "") or "")
        self.iban_input.setText(self.supplier_data.get("iban", "") or "")
        
    def _on_save(self):
        """Kaydet"""
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Uyarı", "Tedarikçi adı zorunludur!")
            self.name_input.setFocus()
            return
        
        data = {
            "code": self.code_input.text().strip() or None,
            "name": name,
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
            
            "payment_term_days": self.payment_term_input.value(),
            "credit_limit": Decimal(str(self.credit_limit_input.value())),
            "currency": self.currency_combo.currentData(),
            "rating": self.rating_input.value(),
            
            "bank_name": self.bank_name_input.text().strip() or None,
            "bank_branch": self.bank_branch_input.text().strip() or None,
            "bank_account_no": self.bank_account_input.text().strip() or None,
            "iban": self.iban_input.text().strip() or None,
        }
        
        if self.is_edit_mode and self.supplier_data:
            data["id"] = self.supplier_data.get("id")
        
        self.saved.emit(data)
        