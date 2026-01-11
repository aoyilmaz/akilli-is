"""
Akıllı İş - Depo Form Sayfası
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QCheckBox, QFrame,
    QFormLayout, QMessageBox, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal

from database.models import Warehouse

class WarehouseFormPage(QWidget):
    """Depo ekleme/düzenleme formu"""
    
    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()
    
    def __init__(self, warehouse: Optional[Warehouse] = None, parent=None):
        super().__init__(parent)
        self.warehouse = warehouse
        self.is_edit_mode = warehouse is not None
        self.setup_ui()
        if self.is_edit_mode:
            self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # === Başlık ===
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Geri")
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)
        
        title_text = "Depo Düzenle" if self.is_edit_mode else "Yeni Depo"
        title = QLabel(title_text)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(self._on_save)
        header_layout.addWidget(save_btn)
        
        layout.addLayout(header_layout)
        
        # === Tab Widget ===
        tabs = QTabWidget()
        tabs.addTab(self._create_general_tab(), "📋 Genel Bilgiler")
        tabs.addTab(self._create_address_tab(), "📍 Adres Bilgileri")
        tabs.addTab(self._create_settings_tab(), "⚙️ Ayarlar")
        
        layout.addWidget(tabs)
        
    def _create_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(24)
        
        # Sol
        left_widget = QWidget()
        left_layout = QFormLayout(left_widget)
        left_layout.setSpacing(16)
        
        # Depo Kodu
        code_layout = QHBoxLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("DP001")
        auto_btn = QPushButton("🔄")
        auto_btn.setFixedWidth(40)
        auto_btn.setToolTip("Otomatik Kod Üret")
        auto_btn.clicked.connect(self._generate_code)
        code_layout.addWidget(self.code_input)
        code_layout.addWidget(auto_btn)
        left_layout.addRow("Depo Kodu *", code_layout)
        
        # Depo Adı
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ana Depo")
        left_layout.addRow("Depo Adı *", self.name_input)
        
        # Kısa Ad
        self.short_name_input = QLineEdit()
        self.short_name_input.setPlaceholderText("Kısa ad")
        left_layout.addRow("Kısa Ad", self.short_name_input)
        
        # Depo Türü
        self.type_combo = QComboBox()
        self.type_combo.addItem("🏭 Genel Depo", "general")
        self.type_combo.addItem("🧱 Hammadde Deposu", "raw")
        self.type_combo.addItem("📦 Mamul Deposu", "finished")
        self.type_combo.addItem("❄️ Soğuk Hava Deposu", "cold")
        self.type_combo.addItem("🔒 Antrepo", "bonded")
        left_layout.addRow("Depo Türü", self.type_combo)
        
        layout.addWidget(left_widget)
        
        # Sağ
        right_widget = QWidget()
        right_layout = QFormLayout(right_widget)
        right_layout.setSpacing(16)
        
        # Yetkili
        self.manager_input = QLineEdit()
        self.manager_input.setPlaceholderText("Depo sorumlusu")
        right_layout.addRow("Yetkili", self.manager_input)
        
        # Telefon
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+90 xxx xxx xx xx")
        right_layout.addRow("Telefon", self.phone_input)
        
        # E-posta
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("depo@firma.com")
        right_layout.addRow("E-posta", self.email_input)
        
        # Açıklama
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Depo açıklaması...")
        self.description_input.setMaximumHeight(100)
        right_layout.addRow("Açıklama", self.description_input)
        
        layout.addWidget(right_widget)
        
        return tab
        
    def _create_address_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        frame = QFrame()
        form = QFormLayout(frame)
        form.setSpacing(16)
        
        # Adres
        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Sokak, mahalle, bina no...")
        self.address_input.setMaximumHeight(80)
        form.addRow("Adres", self.address_input)
        
        # Şehir
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("İstanbul")
        form.addRow("Şehir", self.city_input)
        
        # İlçe
        self.district_input = QLineEdit()
        self.district_input.setPlaceholderText("Kadıköy")
        form.addRow("İlçe", self.district_input)
        
        # Posta Kodu
        self.postal_input = QLineEdit()
        self.postal_input.setPlaceholderText("34000")
        form.addRow("Posta Kodu", self.postal_input)
        
        # Ülke
        self.country_input = QLineEdit()
        self.country_input.setText("Türkiye")
        form.addRow("Ülke", self.country_input)
        
        layout.addWidget(frame)
        layout.addStretch()
        
        return tab
        
    def _create_settings_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        frame = QFrame()
        form_layout = QVBoxLayout(frame)
        form_layout.setSpacing(16)
        
        title = QLabel("⚙️ Depo Ayarları")
        form_layout.addWidget(title)
        
        self.is_default_check = QCheckBox("Varsayılan Depo")
        form_layout.addWidget(self.is_default_check)
        
        self.is_production_check = QCheckBox("Üretim Deposu")
        form_layout.addWidget(self.is_production_check)
        
        self.allow_negative_check = QCheckBox("Negatif Stoka İzin Ver")
        form_layout.addWidget(self.allow_negative_check)
        
        self.is_active_check = QCheckBox("Aktif")
        self.is_active_check.setChecked(True)
        form_layout.addWidget(self.is_active_check)
        
        form_layout.addStretch()
        
        layout.addWidget(frame)
        layout.addStretch()
        
        return tab
        
    def load_data(self):
        """Düzenleme modunda verileri yükle"""
        if not self.warehouse:
            return
        
        self.code_input.setText(self.warehouse.code)
        self.name_input.setText(self.warehouse.name)
        self.short_name_input.setText(self.warehouse.short_name or "")
        self.manager_input.setText(self.warehouse.manager_name or "")
        self.phone_input.setText(self.warehouse.phone or "")
        self.email_input.setText(self.warehouse.email or "")
        self.description_input.setPlainText(self.warehouse.description or "")
        
        # Tür
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.warehouse.warehouse_type:
                self.type_combo.setCurrentIndex(i)
                break
        
        # Adres
        self.address_input.setPlainText(self.warehouse.address or "")
        self.city_input.setText(self.warehouse.city or "")
        self.district_input.setText(self.warehouse.district or "")
        self.postal_input.setText(self.warehouse.postal_code or "")
        self.country_input.setText(self.warehouse.country or "Türkiye")
        
        # Ayarlar
        self.is_default_check.setChecked(self.warehouse.is_default)
        self.is_production_check.setChecked(self.warehouse.is_production)
        self.allow_negative_check.setChecked(self.warehouse.allow_negative)
        self.is_active_check.setChecked(self.warehouse.is_active)
        
    def _generate_code(self):
        import random
        code = f"DP{random.randint(100, 999)}"
        self.code_input.setText(code)
        
    def _on_save(self):
        if not self._validate():
            return
        data = self.get_form_data()
        self.saved.emit(data)
        
    def _validate(self) -> bool:
        if not self.code_input.text().strip():
            QMessageBox.warning(self, "Uyarı", "Depo kodu zorunludur!")
            self.code_input.setFocus()
            return False
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Uyarı", "Depo adı zorunludur!")
            self.name_input.setFocus()
            return False
        return True
        
    def get_form_data(self) -> dict:
        return {
            "code": self.code_input.text().strip(),
            "name": self.name_input.text().strip(),
            "short_name": self.short_name_input.text().strip() or None,
            "warehouse_type": self.type_combo.currentData(),
            "manager_name": self.manager_input.text().strip() or None,
            "phone": self.phone_input.text().strip() or None,
            "email": self.email_input.text().strip() or None,
            "description": self.description_input.toPlainText().strip() or None,
            "address": self.address_input.toPlainText().strip() or None,
            "city": self.city_input.text().strip() or None,
            "district": self.district_input.text().strip() or None,
            "postal_code": self.postal_input.text().strip() or None,
            "country": self.country_input.text().strip() or "Türkiye",
            "is_default": self.is_default_check.isChecked(),
            "is_production": self.is_production_check.isChecked(),
            "allow_negative": self.allow_negative_check.isChecked(),
            "is_active": self.is_active_check.isChecked(),
        }
    