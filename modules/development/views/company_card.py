"""
Akıllı İş - Firma Kartı Sayfası
Geliştirme Araçları altında firma bilgilerini yönetir
"""

import os
import shutil
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QDateEdit,
    QPushButton,
    QLabel,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFileDialog,
    QSpinBox,
    QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QPixmap, QFont

from config.styles import (
    BG_PRIMARY,
    TEXT_PRIMARY,
    ACCENT,
    get_button_style,
    BTN_HEIGHT_NORMAL,
)
from modules.system.services.company_service import CompanyService
from database.models.company import (
    CompanyType,
    AddressType,
    BankAccountType,
)


class CompanyCard(QWidget):
    """Firma Kartı Sayfası"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = CompanyService()
        self.company = None
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        header = QHBoxLayout()
        title = QLabel("🏢 Firma Kartı")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.addWidget(title)

        # Firma seçici
        header.addSpacing(32)
        header.addWidget(QLabel("Firma:"))
        self.cmb_company = QComboBox()
        self.cmb_company.setMinimumWidth(250)
        self.cmb_company.currentIndexChanged.connect(self._on_company_changed)
        header.addWidget(self.cmb_company)

        # Yeni firma butonu
        new_btn = QPushButton("➕ Yeni Firma")
        new_btn.setStyleSheet(get_button_style("add"))
        new_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        new_btn.clicked.connect(self._create_new_company)
        header.addWidget(new_btn)

        # Firma sil butonu
        del_btn = QPushButton("🗑 Sil")
        del_btn.setStyleSheet(get_button_style("delete"))
        del_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        del_btn.clicked.connect(self._delete_company)
        header.addWidget(del_btn)

        header.addStretch()

        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet(get_button_style("add"))
        save_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        save_btn.clicked.connect(self._save_all)
        header.addWidget(save_btn)

        layout.addLayout(header)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_basic_tab(), "Temel Bilgiler")
        self.tabs.addTab(self._create_contact_tab(), "İletişim")
        self.tabs.addTab(self._create_address_tab(), "Adresler")
        self.tabs.addTab(self._create_bank_tab(), "Banka Hesapları")
        self.tabs.addTab(self._create_finance_tab(), "Finans Ayarları")
        self.tabs.addTab(self._create_operation_tab(), "Operasyon")
        self.tabs.addTab(self._create_integration_tab(), "Entegrasyon")
        self.tabs.addTab(self._create_document_tab(), "Dökümanlar")

        layout.addWidget(self.tabs)

    def _create_basic_tab(self) -> QWidget:
        """Temel Bilgiler sekmesi"""
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(24)

        # Sol kolon - Kimlik bilgileri
        left_group = QGroupBox("Kimlik Bilgileri")
        left_layout = QFormLayout(left_group)
        left_layout.setSpacing(10)

        self.txt_code = QLineEdit()
        self.txt_code.setPlaceholderText("Örn: FRM001")
        left_layout.addRow("Firma Kodu:", self.txt_code)

        self.txt_name = QLineEdit()
        left_layout.addRow("Firma Adı:", self.txt_name)

        self.txt_legal_name = QLineEdit()
        left_layout.addRow("Ticari Ünvan:", self.txt_legal_name)

        self.cmb_type = QComboBox()
        self.cmb_type.addItem("A.Ş.", CompanyType.ANONIM)
        self.cmb_type.addItem("Ltd. Şti.", CompanyType.LIMITED)
        self.cmb_type.addItem("Şahıs", CompanyType.SAHIS)
        self.cmb_type.addItem("Kooperatif", CompanyType.KOOPERATIF)
        self.cmb_type.addItem("Kamu", CompanyType.KAMU)
        self.cmb_type.addItem("Diğer", CompanyType.DIGER)
        left_layout.addRow("Firma Türü:", self.cmb_type)

        self.dt_foundation = QDateEdit()
        self.dt_foundation.setCalendarPopup(True)
        self.dt_foundation.setDate(QDate.currentDate())
        left_layout.addRow("Kuruluş Tarihi:", self.dt_foundation)

        self.txt_nace = QLineEdit()
        self.txt_nace.setPlaceholderText("NACE kodu")
        left_layout.addRow("Faaliyet Kodu:", self.txt_nace)

        main_layout.addWidget(left_group)

        # Orta kolon - Vergi bilgileri
        middle_group = QGroupBox("Vergi & Resmi Bilgiler")
        middle_layout = QFormLayout(middle_group)
        middle_layout.setSpacing(10)

        self.txt_tax_country = QLineEdit()
        self.txt_tax_country.setText("TR")
        self.txt_tax_country.setMaxLength(3)
        middle_layout.addRow("Vergi Ülkesi:", self.txt_tax_country)

        self.txt_tax_office = QLineEdit()
        middle_layout.addRow("Vergi Dairesi:", self.txt_tax_office)

        self.txt_tax_number = QLineEdit()
        self.txt_tax_number.setMaxLength(11)
        middle_layout.addRow("Vergi No:", self.txt_tax_number)

        self.txt_mersis = QLineEdit()
        middle_layout.addRow("MERSİS No:", self.txt_mersis)

        self.txt_trade_reg = QLineEdit()
        middle_layout.addRow("Ticaret Sicil:", self.txt_trade_reg)

        self.txt_sgk = QLineEdit()
        middle_layout.addRow("SGK İşyeri No:", self.txt_sgk)

        self.txt_kep = QLineEdit()
        middle_layout.addRow("KEP Adresi:", self.txt_kep)

        main_layout.addWidget(middle_group)

        # Sağ kolon - E-Dönüşüm
        right_group = QGroupBox("E-Dönüşüm")
        right_layout = QVBoxLayout(right_group)
        right_layout.setSpacing(12)

        self.chk_efatura = QCheckBox("E-Fatura Mükellefi")
        right_layout.addWidget(self.chk_efatura)

        self.chk_earsiv = QCheckBox("E-Arşiv Mükellefi")
        right_layout.addWidget(self.chk_earsiv)

        self.chk_eirsaliye = QCheckBox("E-İrsaliye Kullanımı")
        right_layout.addWidget(self.chk_eirsaliye)

        self.chk_edefter = QCheckBox("E-Defter Kullanımı")
        right_layout.addWidget(self.chk_edefter)

        right_layout.addStretch()

        main_layout.addWidget(right_group)

        return tab

    def _create_contact_tab(self) -> QWidget:
        """İletişim sekmesi"""
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(24)

        # Sol - Genel iletişim
        left_group = QGroupBox("Genel İletişim")
        left_layout = QFormLayout(left_group)
        left_layout.setSpacing(10)

        self.txt_phone = QLineEdit()
        left_layout.addRow("Telefon:", self.txt_phone)

        self.txt_phone2 = QLineEdit()
        left_layout.addRow("Telefon 2:", self.txt_phone2)

        self.txt_fax = QLineEdit()
        left_layout.addRow("Fax:", self.txt_fax)

        self.txt_email = QLineEdit()
        left_layout.addRow("E-posta:", self.txt_email)

        self.txt_website = QLineEdit()
        left_layout.addRow("Web Sitesi:", self.txt_website)

        main_layout.addWidget(left_group)

        # Sağ - Yetkili kişiler (tablo)
        right_group = QGroupBox("Yetkili Kişiler")
        right_layout = QVBoxLayout(right_group)

        # Butonlar
        btn_layout = QHBoxLayout()
        add_contact_btn = QPushButton("➕ Ekle")
        add_contact_btn.clicked.connect(self._add_contact)
        btn_layout.addWidget(add_contact_btn)
        btn_layout.addStretch()
        right_layout.addLayout(btn_layout)

        self.contact_table = QTableWidget()
        self.contact_table.setColumnCount(5)
        self.contact_table.setHorizontalHeaderLabels(
            ["ID", "Ad Soyad", "Ünvan", "Telefon", "E-posta"]
        )
        self.contact_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.contact_table.setColumnHidden(0, True)
        right_layout.addWidget(self.contact_table)

        main_layout.addWidget(right_group)

        return tab

    def _create_address_tab(self) -> QWidget:
        """Adresler sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Butonlar
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Adres Ekle")
        add_btn.clicked.connect(self._add_address)
        btn_layout.addWidget(add_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.address_table = QTableWidget()
        self.address_table.setColumnCount(7)
        self.address_table.setHorizontalHeaderLabels(
            ["ID", "Tür", "Şehir", "İlçe", "Posta Kodu", "Adres", "Varsayılan"]
        )
        self.address_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.address_table.setColumnHidden(0, True)
        layout.addWidget(self.address_table)

        return tab

    def _create_bank_tab(self) -> QWidget:
        """Banka hesapları sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Butonlar
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Hesap Ekle")
        add_btn.clicked.connect(self._add_bank)
        btn_layout.addWidget(add_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.bank_table = QTableWidget()
        self.bank_table.setColumnCount(7)
        self.bank_table.setHorizontalHeaderLabels(
            ["ID", "Banka", "Şube", "Hesap Sahibi", "IBAN", "Para Birimi", "Varsayılan"]
        )
        self.bank_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.bank_table.setColumnHidden(0, True)
        layout.addWidget(self.bank_table)

        return tab

    def _create_finance_tab(self) -> QWidget:
        """Finans ayarları sekmesi"""
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(24)

        # Sol - Para birimi ve vergi
        left_group = QGroupBox("Para Birimi & Vergi")
        left_layout = QFormLayout(left_group)
        left_layout.setSpacing(10)

        self.txt_currency = QLineEdit()
        self.txt_currency.setText("TRY")
        self.txt_currency.setMaxLength(3)
        left_layout.addRow("Para Birimi:", self.txt_currency)

        self.spn_vat = QDoubleSpinBox()
        self.spn_vat.setRange(0, 100)
        self.spn_vat.setValue(20)
        self.spn_vat.setSuffix(" %")
        left_layout.addRow("Varsayılan KDV:", self.spn_vat)

        self.spn_withholding = QDoubleSpinBox()
        self.spn_withholding.setRange(0, 100)
        self.spn_withholding.setValue(0)
        self.spn_withholding.setSuffix(" %")
        left_layout.addRow("Varsayılan Stopaj:", self.spn_withholding)

        self.spn_fiscal_start = QSpinBox()
        self.spn_fiscal_start.setRange(1, 12)
        self.spn_fiscal_start.setValue(1)
        left_layout.addRow("Mali Yıl Başlangıç:", self.spn_fiscal_start)

        self.spn_fiscal_end = QSpinBox()
        self.spn_fiscal_end.setRange(1, 12)
        self.spn_fiscal_end.setValue(12)
        left_layout.addRow("Mali Yıl Bitiş:", self.spn_fiscal_end)

        main_layout.addWidget(left_group)

        # Sağ - Numaralandırma
        right_group = QGroupBox("Belge Numaralandırma")
        right_layout = QFormLayout(right_group)
        right_layout.setSpacing(10)

        self.txt_invoice_prefix = QLineEdit()
        self.txt_invoice_prefix.setText("FTR")
        right_layout.addRow("Fatura Öneki:", self.txt_invoice_prefix)

        self.txt_order_prefix = QLineEdit()
        self.txt_order_prefix.setText("SIP")
        right_layout.addRow("Sipariş Öneki:", self.txt_order_prefix)

        self.txt_delivery_prefix = QLineEdit()
        self.txt_delivery_prefix.setText("IRS")
        right_layout.addRow("İrsaliye Öneki:", self.txt_delivery_prefix)

        self.txt_purchase_prefix = QLineEdit()
        self.txt_purchase_prefix.setText("SAT")
        right_layout.addRow("Satınalma Öneki:", self.txt_purchase_prefix)

        main_layout.addWidget(right_group)

        return tab

    def _create_operation_tab(self) -> QWidget:
        """Operasyon ayarları sekmesi"""
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(24)

        # Sol - Stok ayarları
        left_group = QGroupBox("Stok & Takip")
        left_layout = QVBoxLayout(left_group)
        left_layout.setSpacing(12)

        self.chk_lot = QCheckBox("Lot Takibi Aktif")
        self.chk_lot.setChecked(True)
        left_layout.addWidget(self.chk_lot)

        self.chk_serial = QCheckBox("Seri Takibi Aktif")
        left_layout.addWidget(self.chk_serial)

        form = QFormLayout()
        self.txt_barcode = QLineEdit()
        self.txt_barcode.setText("EAN13")
        form.addRow("Barkod Standardı:", self.txt_barcode)
        left_layout.addLayout(form)

        left_layout.addStretch()
        main_layout.addWidget(left_group)

        # Sağ - Bölgesel ayarlar
        right_group = QGroupBox("Bölgesel Ayarlar")
        right_layout = QFormLayout(right_group)
        right_layout.setSpacing(10)

        self.txt_timezone = QLineEdit()
        self.txt_timezone.setText("Europe/Istanbul")
        right_layout.addRow("Zaman Dilimi:", self.txt_timezone)

        self.txt_language = QLineEdit()
        self.txt_language.setText("tr")
        right_layout.addRow("Dil:", self.txt_language)

        self.txt_date_format = QLineEdit()
        self.txt_date_format.setText("DD.MM.YYYY")
        right_layout.addRow("Tarih Formatı:", self.txt_date_format)

        main_layout.addWidget(right_group)

        return tab

    def _create_integration_tab(self) -> QWidget:
        """Entegrasyon sekmesi"""
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(24)

        # Sol - API
        left_group = QGroupBox("API & Entegrasyon")
        left_layout = QFormLayout(left_group)
        left_layout.setSpacing(10)

        self.txt_erp_uuid = QLineEdit()
        self.txt_erp_uuid.setReadOnly(True)
        left_layout.addRow("ERP UUID:", self.txt_erp_uuid)

        self.txt_api_key = QLineEdit()
        self.txt_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        left_layout.addRow("API Anahtarı:", self.txt_api_key)

        self.txt_efatura_int = QLineEdit()
        left_layout.addRow("E-Fatura Entegratör:", self.txt_efatura_int)

        self.txt_ecommerce = QLineEdit()
        left_layout.addRow("E-Ticaret ID:", self.txt_ecommerce)

        main_layout.addWidget(left_group)

        # Sağ - İletişim
        right_group = QGroupBox("İletişim Entegrasyonu")
        right_layout = QFormLayout(right_group)
        right_layout.setSpacing(10)

        self.txt_sms_sender = QLineEdit()
        right_layout.addRow("SMS Gönderici ID:", self.txt_sms_sender)

        self.txt_whatsapp = QLineEdit()
        right_layout.addRow("WhatsApp Business:", self.txt_whatsapp)

        self.txt_backup_email = QLineEdit()
        right_layout.addRow("Yedek E-posta:", self.txt_backup_email)

        main_layout.addWidget(right_group)

        return tab

    def _create_document_tab(self) -> QWidget:
        """Dökümanlar sekmesi"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setSpacing(16)

        # Üst satır - Kurumsal kimlik
        top_row = QHBoxLayout()
        top_row.setSpacing(24)

        # Logo
        logo_group = QGroupBox("Firma Logosu")
        logo_layout = QVBoxLayout(logo_group)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(200, 100)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet(
            "background: #1e293b; border: 2px dashed #475569; border-radius: 8px;"
        )
        self.logo_label.setText("Logo Yok")
        logo_layout.addWidget(self.logo_label)

        logo_btn = QPushButton("📂 Logo Yükle")
        logo_btn.clicked.connect(lambda: self._upload_document("logo"))
        logo_layout.addWidget(logo_btn)

        top_row.addWidget(logo_group)

        # Kaşe
        stamp_group = QGroupBox("Firma Kaşesi")
        stamp_layout = QVBoxLayout(stamp_group)

        self.stamp_label = QLabel()
        self.stamp_label.setFixedSize(150, 150)
        self.stamp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stamp_label.setStyleSheet(
            "background: #1e293b; border: 2px dashed #475569; border-radius: 8px;"
        )
        self.stamp_label.setText("Kaşe Yok")
        stamp_layout.addWidget(self.stamp_label)

        stamp_btn = QPushButton("📂 Kaşe Yükle")
        stamp_btn.clicked.connect(lambda: self._upload_document("stamp"))
        stamp_layout.addWidget(stamp_btn)

        top_row.addWidget(stamp_group)

        # İmza
        signature_group = QGroupBox("Yetkili İmzası")
        signature_layout = QVBoxLayout(signature_group)

        self.signature_label = QLabel()
        self.signature_label.setFixedSize(200, 80)
        self.signature_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.signature_label.setStyleSheet(
            "background: #1e293b; border: 2px dashed #475569; border-radius: 8px;"
        )
        self.signature_label.setText("İmza Yok")
        signature_layout.addWidget(self.signature_label)

        signature_btn = QPushButton("📂 İmza Yükle")
        signature_btn.clicked.connect(lambda: self._upload_document("signature"))
        signature_layout.addWidget(signature_btn)

        top_row.addWidget(signature_group)
        top_row.addStretch()

        main_layout.addLayout(top_row)

        # Alt satır - Belge Şablonları
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(24)

        # Antetli Kağıt
        letterhead_group = QGroupBox("Antetli Kağıt Şablonu")
        letterhead_layout = QVBoxLayout(letterhead_group)

        self.letterhead_label = QLabel()
        self.letterhead_label.setFixedSize(180, 250)
        self.letterhead_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.letterhead_label.setStyleSheet(
            "background: #1e293b; border: 2px dashed #475569; border-radius: 8px;"
        )
        self.letterhead_label.setText("📄\nAntetli Kağıt\nYok")
        letterhead_layout.addWidget(self.letterhead_label)

        lh_btn = QPushButton("📂 Şablon Yükle")
        lh_btn.clicked.connect(lambda: self._upload_document("letterhead"))
        letterhead_layout.addWidget(lh_btn)

        bottom_row.addWidget(letterhead_group)

        # Fatura Şablonu
        invoice_group = QGroupBox("Fatura Şablonu")
        invoice_layout = QVBoxLayout(invoice_group)

        self.invoice_template_label = QLabel()
        self.invoice_template_label.setFixedSize(180, 250)
        self.invoice_template_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.invoice_template_label.setStyleSheet(
            "background: #1e293b; border: 2px dashed #475569; border-radius: 8px;"
        )
        self.invoice_template_label.setText("📄\nFatura Şablonu\nYok")
        invoice_layout.addWidget(self.invoice_template_label)

        inv_btn = QPushButton("📂 Şablon Yükle")
        inv_btn.clicked.connect(lambda: self._upload_document("invoice_template"))
        invoice_layout.addWidget(inv_btn)

        bottom_row.addWidget(invoice_group)

        # İrsaliye Şablonu
        delivery_group = QGroupBox("İrsaliye Şablonu")
        delivery_layout = QVBoxLayout(delivery_group)

        self.delivery_template_label = QLabel()
        self.delivery_template_label.setFixedSize(180, 250)
        self.delivery_template_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.delivery_template_label.setStyleSheet(
            "background: #1e293b; border: 2px dashed #475569; border-radius: 8px;"
        )
        self.delivery_template_label.setText("📄\nİrsaliye Şablonu\nYok")
        delivery_layout.addWidget(self.delivery_template_label)

        del_btn = QPushButton("📂 Şablon Yükle")
        del_btn.clicked.connect(lambda: self._upload_document("delivery_template"))
        delivery_layout.addWidget(del_btn)

        bottom_row.addWidget(delivery_group)
        bottom_row.addStretch()

        main_layout.addLayout(bottom_row)
        main_layout.addStretch()

        return tab

    # === VERİ İŞLEMLERİ ===

    def _load_data(self):
        """Firma verilerini yükle"""
        self._load_company_list()

        if self.cmb_company.count() == 0:
            # İlk firma yok, yeni oluştur
            self.company = self.service.create_company(
                {
                    "code": "FRM001",
                    "name": "Akıllı İş A.Ş.",
                }
            )
            self._load_company_list()

        self._load_company_data()

    def _load_company_list(self):
        """Firma listesini yükle"""
        self.cmb_company.blockSignals(True)
        current_id = self.cmb_company.currentData()

        self.cmb_company.clear()
        companies = self.service.get_all_companies()

        for c in companies:
            self.cmb_company.addItem(f"{c.code} - {c.name}", c.id)

        # Önceki seçimi koru
        if current_id:
            idx = self.cmb_company.findData(current_id)
            if idx >= 0:
                self.cmb_company.setCurrentIndex(idx)

        self.cmb_company.blockSignals(False)

    def _on_company_changed(self, index):
        """Firma değiştiğinde"""
        if index >= 0:
            company_id = self.cmb_company.currentData()
            self.company = self.service.get_company(company_id)
            self._load_company_data()

    def _load_company_data(self):
        """Seçili firmanın verilerini yükle"""
        if self.cmb_company.currentIndex() >= 0 and not self.company:
            company_id = self.cmb_company.currentData()
            self.company = self.service.get_company(company_id)

        if not self.company:
            return

        self._populate_form()
        self._load_contacts()
        self._load_addresses()
        self._load_banks()
        self._load_settings()
        self._load_documents()

    def _create_new_company(self):
        """Yeni firma oluştur"""
        from PyQt6.QtWidgets import QInputDialog

        code, ok1 = QInputDialog.getText(self, "Yeni Firma", "Firma Kodu:")
        if not ok1 or not code.strip():
            return

        name, ok2 = QInputDialog.getText(self, "Yeni Firma", "Firma Adı:")
        if not ok2 or not name.strip():
            return

        try:
            new_company = self.service.create_company(
                {
                    "code": code.strip(),
                    "name": name.strip(),
                }
            )
            self._load_company_list()

            # Yeni firmayı seç
            idx = self.cmb_company.findData(new_company.id)
            if idx >= 0:
                self.cmb_company.setCurrentIndex(idx)

            QMessageBox.information(self, "Başarılı", f"'{name}' firması oluşturuldu.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Firma oluşturulamadı:\n{str(e)}")

    def _delete_company(self):
        """Firmayı sil"""
        if not self.company:
            return

        if self.cmb_company.count() <= 1:
            QMessageBox.warning(self, "Uyarı", "Son firma silinemez!")
            return

        reply = QMessageBox.question(
            self,
            "Firma Sil",
            f"'{self.company.name}' firmasını silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.session.delete(self.company)
                self.service.session.commit()
                self.company = None
                self._load_company_list()
                self._on_company_changed(0)
                QMessageBox.information(self, "Başarılı", "Firma silindi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Firma silinemedi:\n{str(e)}")

    def _populate_form(self):
        """Form alanlarını doldur"""
        if not self.company:
            return

        c = self.company

        # Temel bilgiler
        self.txt_code.setText(c.code or "")
        self.txt_name.setText(c.name or "")
        self.txt_legal_name.setText(c.legal_name or "")

        if c.company_type:
            idx = self.cmb_type.findData(c.company_type)
            if idx >= 0:
                self.cmb_type.setCurrentIndex(idx)

        if c.foundation_date:
            self.dt_foundation.setDate(
                QDate(
                    c.foundation_date.year,
                    c.foundation_date.month,
                    c.foundation_date.day,
                )
            )

        self.txt_nace.setText(c.nace_code or "")

        # Vergi
        self.txt_tax_country.setText(c.tax_country or "TR")
        self.txt_tax_office.setText(c.tax_office or "")
        self.txt_tax_number.setText(c.tax_number or "")
        self.txt_mersis.setText(c.mersis_no or "")
        self.txt_trade_reg.setText(c.trade_reg_no or "")
        self.txt_sgk.setText(c.sgk_workplace or "")
        self.txt_kep.setText(c.kep_address or "")

        # E-Dönüşüm
        self.chk_efatura.setChecked(c.is_efatura or False)
        self.chk_earsiv.setChecked(c.is_earsiv or False)
        self.chk_eirsaliye.setChecked(c.is_eirsaliye or False)
        self.chk_edefter.setChecked(c.is_edefter or False)

        # İletişim
        self.txt_phone.setText(c.phone or "")
        self.txt_phone2.setText(c.phone2 or "")
        self.txt_fax.setText(c.fax or "")
        self.txt_email.setText(c.email or "")
        self.txt_website.setText(c.website or "")

    def _load_contacts(self):
        """Yetkili kişileri yükle"""
        if not self.company:
            return

        contacts = self.service.get_contacts(self.company.id)
        self.contact_table.setRowCount(len(contacts))

        for row, c in enumerate(contacts):
            self.contact_table.setItem(row, 0, QTableWidgetItem(str(c.id)))
            self.contact_table.setItem(row, 1, QTableWidgetItem(c.name or ""))
            self.contact_table.setItem(row, 2, QTableWidgetItem(c.title or ""))
            self.contact_table.setItem(row, 3, QTableWidgetItem(c.phone or ""))
            self.contact_table.setItem(row, 4, QTableWidgetItem(c.email or ""))

    def _load_addresses(self):
        """Adresleri yükle"""
        if not self.company:
            return

        addresses = self.service.get_addresses(self.company.id)
        self.address_table.setRowCount(len(addresses))

        type_names = {
            AddressType.MERKEZ: "Merkez",
            AddressType.FATURA: "Fatura",
            AddressType.SEVKIYAT: "Sevkiyat",
            AddressType.SUBE: "Şube",
        }

        for row, a in enumerate(addresses):
            self.address_table.setItem(row, 0, QTableWidgetItem(str(a.id)))
            type_name = type_names.get(a.address_type, "-")
            self.address_table.setItem(row, 1, QTableWidgetItem(type_name))
            self.address_table.setItem(row, 2, QTableWidgetItem(a.city or ""))
            self.address_table.setItem(row, 3, QTableWidgetItem(a.district or ""))
            self.address_table.setItem(row, 4, QTableWidgetItem(a.postal_code or ""))
            self.address_table.setItem(row, 5, QTableWidgetItem(a.address or ""))
            self.address_table.setItem(
                row, 6, QTableWidgetItem("✓" if a.is_default else "")
            )

    def _load_banks(self):
        """Banka hesaplarını yükle"""
        if not self.company:
            return

        banks = self.service.get_banks(self.company.id)
        self.bank_table.setRowCount(len(banks))

        for row, b in enumerate(banks):
            self.bank_table.setItem(row, 0, QTableWidgetItem(str(b.id)))
            self.bank_table.setItem(row, 1, QTableWidgetItem(b.bank_name or ""))
            self.bank_table.setItem(row, 2, QTableWidgetItem(b.branch or ""))
            self.bank_table.setItem(row, 3, QTableWidgetItem(b.account_holder or ""))
            self.bank_table.setItem(row, 4, QTableWidgetItem(b.iban or ""))
            acc_type = b.account_type.value if b.account_type else "TRY"
            self.bank_table.setItem(row, 5, QTableWidgetItem(acc_type))
            self.bank_table.setItem(
                row, 6, QTableWidgetItem("✓" if b.is_default else "")
            )

    def _load_settings(self):
        """Ayarları yükle"""
        if not self.company:
            return

        settings = self.service.get_settings(self.company.id)
        if not settings:
            return

        s = settings

        # Finans
        self.txt_currency.setText(s.currency or "TRY")
        if s.default_vat_rate:
            self.spn_vat.setValue(float(s.default_vat_rate))
        if s.default_withholding:
            self.spn_withholding.setValue(float(s.default_withholding))
        self.spn_fiscal_start.setValue(s.fiscal_year_start or 1)
        self.spn_fiscal_end.setValue(s.fiscal_year_end or 12)

        # Numaralandırma
        self.txt_invoice_prefix.setText(s.invoice_prefix or "FTR")
        self.txt_order_prefix.setText(s.order_prefix or "SIP")
        self.txt_delivery_prefix.setText(s.delivery_prefix or "IRS")
        self.txt_purchase_prefix.setText(s.purchase_prefix or "SAT")

        # Operasyon
        self.chk_lot.setChecked(s.has_lot_tracking or False)
        self.chk_serial.setChecked(s.has_serial_tracking or False)
        self.txt_barcode.setText(s.barcode_standard or "EAN13")

        # Bölgesel
        self.txt_timezone.setText(s.timezone or "Europe/Istanbul")
        self.txt_language.setText(s.language or "tr")
        self.txt_date_format.setText(s.date_format or "DD.MM.YYYY")

        # Entegrasyon
        self.txt_erp_uuid.setText(s.erp_uuid or "")
        self.txt_api_key.setText(s.api_key or "")
        self.txt_efatura_int.setText(s.efatura_integrator or "")
        self.txt_ecommerce.setText(s.ecommerce_id or "")
        self.txt_sms_sender.setText(s.sms_sender_id or "")
        self.txt_whatsapp.setText(s.whatsapp_business or "")
        self.txt_backup_email.setText(s.backup_email or "")

    def _load_documents(self):
        """Dökümanları yükle"""
        if not self.company:
            return

        # Logo
        logo = self.service.get_document(self.company.id, "logo")
        if logo and os.path.exists(logo.file_path):
            pixmap = QPixmap(logo.file_path)
            self.logo_label.setPixmap(
                pixmap.scaled(
                    200,
                    100,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        # Kaşe
        stamp = self.service.get_document(self.company.id, "stamp")
        if stamp and os.path.exists(stamp.file_path):
            pixmap = QPixmap(stamp.file_path)
            self.stamp_label.setPixmap(
                pixmap.scaled(
                    150,
                    150,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        # İmza
        sig = self.service.get_document(self.company.id, "signature")
        if sig and os.path.exists(sig.file_path):
            pixmap = QPixmap(sig.file_path)
            self.signature_label.setPixmap(
                pixmap.scaled(
                    200,
                    80,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        # Antetli Kağıt
        lh = self.service.get_document(self.company.id, "letterhead")
        if lh and os.path.exists(lh.file_path):
            pixmap = QPixmap(lh.file_path)
            self.letterhead_label.setPixmap(
                pixmap.scaled(
                    180,
                    250,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        # Fatura Şablonu
        inv = self.service.get_document(self.company.id, "invoice_template")
        if inv and os.path.exists(inv.file_path):
            pixmap = QPixmap(inv.file_path)
            self.invoice_template_label.setPixmap(
                pixmap.scaled(
                    180,
                    250,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        # İrsaliye Şablonu
        dlv = self.service.get_document(self.company.id, "delivery_template")
        if dlv and os.path.exists(dlv.file_path):
            pixmap = QPixmap(dlv.file_path)
            self.delivery_template_label.setPixmap(
                pixmap.scaled(
                    180,
                    250,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    def _save_all(self):
        """Tüm verileri kaydet"""
        if not self.company:
            return

        try:
            # Firma bilgileri
            company_data = {
                "code": self.txt_code.text().strip(),
                "name": self.txt_name.text().strip(),
                "legal_name": self.txt_legal_name.text().strip() or None,
                "company_type": self.cmb_type.currentData(),
                "foundation_date": self.dt_foundation.date().toPyDate(),
                "nace_code": self.txt_nace.text().strip() or None,
                "tax_country": self.txt_tax_country.text().strip() or "TR",
                "tax_office": self.txt_tax_office.text().strip() or None,
                "tax_number": self.txt_tax_number.text().strip() or None,
                "mersis_no": self.txt_mersis.text().strip() or None,
                "trade_reg_no": self.txt_trade_reg.text().strip() or None,
                "sgk_workplace": self.txt_sgk.text().strip() or None,
                "kep_address": self.txt_kep.text().strip() or None,
                "is_efatura": self.chk_efatura.isChecked(),
                "is_earsiv": self.chk_earsiv.isChecked(),
                "is_eirsaliye": self.chk_eirsaliye.isChecked(),
                "is_edefter": self.chk_edefter.isChecked(),
                "phone": self.txt_phone.text().strip() or None,
                "phone2": self.txt_phone2.text().strip() or None,
                "fax": self.txt_fax.text().strip() or None,
                "email": self.txt_email.text().strip() or None,
                "website": self.txt_website.text().strip() or None,
            }
            self.service.update_company(self.company.id, company_data)

            # Ayarlar
            settings_data = {
                "currency": self.txt_currency.text().strip() or "TRY",
                "default_vat_rate": self.spn_vat.value(),
                "default_withholding": self.spn_withholding.value(),
                "fiscal_year_start": self.spn_fiscal_start.value(),
                "fiscal_year_end": self.spn_fiscal_end.value(),
                "invoice_prefix": self.txt_invoice_prefix.text().strip(),
                "order_prefix": self.txt_order_prefix.text().strip(),
                "delivery_prefix": self.txt_delivery_prefix.text().strip(),
                "purchase_prefix": self.txt_purchase_prefix.text().strip(),
                "has_lot_tracking": self.chk_lot.isChecked(),
                "has_serial_tracking": self.chk_serial.isChecked(),
                "barcode_standard": self.txt_barcode.text().strip(),
                "timezone": self.txt_timezone.text().strip(),
                "language": self.txt_language.text().strip(),
                "date_format": self.txt_date_format.text().strip(),
                "api_key": self.txt_api_key.text().strip() or None,
                "efatura_integrator": self.txt_efatura_int.text().strip() or None,
                "ecommerce_id": self.txt_ecommerce.text().strip() or None,
                "sms_sender_id": self.txt_sms_sender.text().strip() or None,
                "whatsapp_business": self.txt_whatsapp.text().strip() or None,
                "backup_email": self.txt_backup_email.text().strip() or None,
            }
            self.service.update_settings(self.company.id, settings_data)

            QMessageBox.information(self, "Başarılı", "Firma bilgileri kaydedildi.")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt sırasında hata:\n{str(e)}")

    def _add_contact(self):
        """Yetkili kişi ekle"""
        # Basit dialog ile ekle
        from PyQt6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "Yetkili Ekle", "Ad Soyad:")
        if ok and name.strip():
            self.service.add_contact(self.company.id, {"name": name.strip()})
            self._load_contacts()

    def _add_address(self):
        """Adres ekle"""
        from PyQt6.QtWidgets import QInputDialog

        city, ok = QInputDialog.getText(self, "Adres Ekle", "Şehir:")
        if ok and city.strip():
            self.service.add_address(self.company.id, {"city": city.strip()})
            self._load_addresses()

    def _add_bank(self):
        """Banka hesabı ekle"""
        from PyQt6.QtWidgets import QInputDialog

        bank_name, ok = QInputDialog.getText(self, "Banka Ekle", "Banka Adı:")
        if ok and bank_name.strip():
            self.service.add_bank(self.company.id, {"bank_name": bank_name.strip()})
            self._load_banks()

    def _upload_document(self, doc_type: str):
        """Döküman yükle"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Dosya Seç", "", "Resim Dosyaları (*.png *.jpg *.jpeg *.svg)"
        )

        if not file_path:
            return

        # Hedef klasör
        doc_dir = os.path.join("assets", "company")
        os.makedirs(doc_dir, exist_ok=True)

        # Dosyayı kopyala
        ext = os.path.splitext(file_path)[1]
        dest_name = f"{doc_type}_{self.company.id}{ext}"
        dest_path = os.path.join(doc_dir, dest_name)

        shutil.copy2(file_path, dest_path)

        # Veritabanına kaydet
        self.service.save_document(
            self.company.id, doc_type, dest_path, os.path.basename(file_path)
        )

        # UI güncelle
        self._load_documents()

        QMessageBox.information(self, "Başarılı", "Dosya yüklendi.")

    def closeEvent(self, event):
        """Kapatıldığında session temizle"""
        self.service.close()
        super().closeEvent(event)
