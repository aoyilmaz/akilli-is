"""
Akıllı İş - Stok Kartı Form Sayfası
"""

from typing import Optional
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QFrame, QTabWidget, QFormLayout, QCheckBox, QMessageBox,
    QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

from database.models import Item, ItemType, Unit, ItemCategory, Warehouse


class StockFormPage(QWidget):
    """Stok kartı ekleme/düzenleme formu"""
    
    # Sinyaller
    saved = pyqtSignal(int)  # item_id
    cancelled = pyqtSignal()
    
    def __init__(self, item: Optional[Item] = None, parent=None):
        super().__init__(parent)
        self.item = item
        self.is_edit_mode = item is not None
        self.setup_ui()
        if self.is_edit_mode:
            self.load_item_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Başlık satırı
        header_layout = QHBoxLayout()
        
        # Geri butonu
        back_btn = QPushButton("← Geri")
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)
        
        # Başlık
        title = QLabel("Yeni Stok Kartı" if not self.is_edit_mode else "Stok Kartı Düzenle")
        title.setObjectName("title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Kaydet butonu
        save_btn = QPushButton("  Kaydet")
        save_btn.setProperty("primary", True)
        save_btn.clicked.connect(self.save)
        header_layout.addWidget(save_btn)
        
        layout.addLayout(header_layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setObjectName("formTabs")
        
        # Tab 1: Genel Bilgiler
        self.tabs.addTab(self.create_general_tab(), "Genel Bilgiler")
        
        # Tab 2: Stok Bilgileri
        self.tabs.addTab(self.create_stock_tab(), "Stok Bilgileri")
        
        # Tab 3: Fiyatlandırma
        self.tabs.addTab(self.create_pricing_tab(), "Fiyatlandırma")
        
        layout.addWidget(self.tabs)
        
    def create_general_tab(self) -> QWidget:
        """Genel bilgiler sekmesi"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        layout = QHBoxLayout(content)
        layout.setSpacing(24)
        
        # Sol kolon
        left_layout = QVBoxLayout()
        left_layout.setSpacing(16)
        
        # Stok Kodu
        code_layout = QHBoxLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("STK001")
        
        auto_code_btn = QPushButton("Otomatik")
        auto_code_btn.clicked.connect(self.generate_code)
        
        code_layout.addWidget(self.code_input)
        code_layout.addWidget(auto_code_btn)
        
        left_layout.addWidget(QLabel("Stok Kodu *"))
        left_layout.addLayout(code_layout)
        
        # Stok Adı
        left_layout.addWidget(QLabel("Stok Adı *"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ürün adını girin")
        left_layout.addWidget(self.name_input)
        
        # Tür
        left_layout.addWidget(QLabel("Tür *"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("Hammadde", ItemType.HAMMADDE)
        self.type_combo.addItem("Mamül", ItemType.MAMUL)
        self.type_combo.addItem("Yarı Mamül", ItemType.YARI_MAMUL)
        self.type_combo.addItem("Ambalaj", ItemType.AMBALAJ)
        self.type_combo.addItem("Sarf Malzeme", ItemType.SARF)
        self.type_combo.addItem("Diğer", ItemType.DIGER)
        left_layout.addWidget(self.type_combo)
        
        # Kategori
        left_layout.addWidget(QLabel("Kategori"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("Seçiniz...", None)
        # Kategoriler dışarıdan yüklenecek
        left_layout.addWidget(self.category_combo)
        
        # Birim
        left_layout.addWidget(QLabel("Birim *"))
        self.unit_combo = QComboBox()
        # Birimler dışarıdan yüklenecek
        left_layout.addWidget(self.unit_combo)
        
        left_layout.addStretch()
        layout.addLayout(left_layout)
        
        # Sağ kolon
        right_layout = QVBoxLayout()
        right_layout.setSpacing(16)
        
        # Barkod
        right_layout.addWidget(QLabel("Barkod"))
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Barkod numarası")
        right_layout.addWidget(self.barcode_input)
        
        # Üretici Kodu
        right_layout.addWidget(QLabel("Üretici Kodu"))
        self.manufacturer_code_input = QLineEdit()
        right_layout.addWidget(self.manufacturer_code_input)
        
        # Marka
        right_layout.addWidget(QLabel("Marka"))
        self.brand_input = QLineEdit()
        right_layout.addWidget(self.brand_input)
        
        # Model
        right_layout.addWidget(QLabel("Model"))
        self.model_input = QLineEdit()
        right_layout.addWidget(self.model_input)
        
        # Açıklama
        right_layout.addWidget(QLabel("Açıklama"))
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.description_input.setPlaceholderText("Ürün açıklaması...")
        right_layout.addWidget(self.description_input)
        
        right_layout.addStretch()
        layout.addLayout(right_layout)
        
        scroll.setWidget(content)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        
        return tab
        
    def create_stock_tab(self) -> QWidget:
        """Stok bilgileri sekmesi"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(24)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Sol kolon - Stok limitleri
        left_frame = QFrame()
        left_frame.setObjectName("card")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setSpacing(16)
        
        left_title = QLabel("Stok Limitleri")
        left_title.setObjectName("sectionTitle")
        left_layout.addWidget(left_title)
        
        # Minimum stok
        left_layout.addWidget(QLabel("Minimum Stok"))
        self.min_stock_input = QDoubleSpinBox()
        self.min_stock_input.setRange(0, 999999999)
        self.min_stock_input.setDecimals(2)
        left_layout.addWidget(self.min_stock_input)
        
        # Maksimum stok
        left_layout.addWidget(QLabel("Maksimum Stok"))
        self.max_stock_input = QDoubleSpinBox()
        self.max_stock_input.setRange(0, 999999999)
        self.max_stock_input.setDecimals(2)
        left_layout.addWidget(self.max_stock_input)
        
        # Yeniden sipariş noktası
        left_layout.addWidget(QLabel("Yeniden Sipariş Noktası"))
        self.reorder_point_input = QDoubleSpinBox()
        self.reorder_point_input.setRange(0, 999999999)
        self.reorder_point_input.setDecimals(2)
        left_layout.addWidget(self.reorder_point_input)
        
        # Temin süresi
        left_layout.addWidget(QLabel("Temin Süresi (Gün)"))
        self.lead_time_input = QSpinBox()
        self.lead_time_input.setRange(0, 365)
        left_layout.addWidget(self.lead_time_input)
        
        left_layout.addStretch()
        layout.addWidget(left_frame)
        
        # Sağ kolon - Takip özellikleri
        right_frame = QFrame()
        right_frame.setObjectName("card")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setSpacing(16)
        
        right_title = QLabel("Takip Özellikleri")
        right_title.setObjectName("sectionTitle")
        right_layout.addWidget(right_title)
        
        # Lot takibi
        self.track_lot_check = QCheckBox("Lot/Parti Takibi")
        right_layout.addWidget(self.track_lot_check)
        
        # Seri no takibi
        self.track_serial_check = QCheckBox("Seri Numarası Takibi")
        right_layout.addWidget(self.track_serial_check)
        
        # Son kullanma tarihi takibi
        self.track_expiry_check = QCheckBox("Son Kullanma Tarihi Takibi")
        right_layout.addWidget(self.track_expiry_check)
        
        right_layout.addSpacing(20)
        
        # Fiziksel özellikler
        phys_title = QLabel("Fiziksel Özellikler")
        phys_title.setObjectName("sectionTitle")
        right_layout.addWidget(phys_title)
        
        # Ağırlık
        right_layout.addWidget(QLabel("Ağırlık (kg)"))
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0, 999999)
        self.weight_input.setDecimals(4)
        right_layout.addWidget(self.weight_input)
        
        # Hacim
        right_layout.addWidget(QLabel("Hacim (m³)"))
        self.volume_input = QDoubleSpinBox()
        self.volume_input.setRange(0, 999999)
        self.volume_input.setDecimals(4)
        right_layout.addWidget(self.volume_input)
        
        right_layout.addStretch()
        layout.addWidget(right_frame)
        
        return tab
        
    def create_pricing_tab(self) -> QWidget:
        """Fiyatlandırma sekmesi"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(24)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Fiyat bilgileri
        price_frame = QFrame()
        price_frame.setObjectName("card")
        price_layout = QVBoxLayout(price_frame)
        price_layout.setSpacing(16)
        
        price_title = QLabel("Fiyat Bilgileri")
        price_title.setObjectName("sectionTitle")
        price_layout.addWidget(price_title)
        
        # Alış fiyatı
        price_layout.addWidget(QLabel("Alış Fiyatı"))
        self.purchase_price_input = QDoubleSpinBox()
        self.purchase_price_input.setRange(0, 999999999)
        self.purchase_price_input.setDecimals(4)
        self.purchase_price_input.setPrefix("₺ ")
        price_layout.addWidget(self.purchase_price_input)
        
        # Satış fiyatı
        price_layout.addWidget(QLabel("Satış Fiyatı"))
        self.sale_price_input = QDoubleSpinBox()
        self.sale_price_input.setRange(0, 999999999)
        self.sale_price_input.setDecimals(4)
        self.sale_price_input.setPrefix("₺ ")
        price_layout.addWidget(self.sale_price_input)
        
        # Para birimi
        price_layout.addWidget(QLabel("Para Birimi"))
        self.currency_combo = QComboBox()
        self.currency_combo.addItem("Türk Lirası (₺)", "TRY")
        self.currency_combo.addItem("ABD Doları ($)", "USD")
        self.currency_combo.addItem("Euro (€)", "EUR")
        price_layout.addWidget(self.currency_combo)
        
        # KDV oranı
        price_layout.addWidget(QLabel("KDV Oranı"))
        self.vat_combo = QComboBox()
        self.vat_combo.addItem("%20", 20)
        self.vat_combo.addItem("%10", 10)
        self.vat_combo.addItem("%1", 1)
        self.vat_combo.addItem("%0", 0)
        price_layout.addWidget(self.vat_combo)
        
        price_layout.addStretch()
        layout.addWidget(price_frame)
        
        layout.addStretch()
        
        return tab
        
    def load_units(self, units: list):
        """Birimleri yükle"""
        self.unit_combo.clear()
        for unit in units:
            self.unit_combo.addItem(f"{unit.code} - {unit.name}", unit.id)
            
    def load_categories(self, categories: list):
        """Kategorileri yükle"""
        self.category_combo.clear()
        self.category_combo.addItem("Seçiniz...", None)
        for cat in categories:
            self.category_combo.addItem(cat.name, cat.id)
            
    def load_item_data(self):
        """Düzenleme modunda verileri yükle"""
        if not self.item:
            return
            
        self.code_input.setText(self.item.code)
        self.name_input.setText(self.item.name)
        self.barcode_input.setText(self.item.barcode or "")
        self.manufacturer_code_input.setText(self.item.manufacturer_code or "")
        self.brand_input.setText(self.item.brand or "")
        self.model_input.setText(self.item.model or "")
        self.description_input.setPlainText(self.item.description or "")
        
        # Tür
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.item.item_type:
                self.type_combo.setCurrentIndex(i)
                break
                
        # Stok bilgileri
        self.min_stock_input.setValue(float(self.item.min_stock or 0))
        self.max_stock_input.setValue(float(self.item.max_stock or 0))
        self.reorder_point_input.setValue(float(self.item.reorder_point or 0))
        self.lead_time_input.setValue(self.item.lead_time_days or 0)
        
        self.track_lot_check.setChecked(self.item.track_lot)
        self.track_serial_check.setChecked(self.item.track_serial)
        self.track_expiry_check.setChecked(self.item.track_expiry)
        
        self.weight_input.setValue(float(self.item.weight or 0))
        self.volume_input.setValue(float(self.item.volume or 0))
        
        # Fiyatlar
        self.purchase_price_input.setValue(float(self.item.purchase_price or 0))
        self.sale_price_input.setValue(float(self.item.sale_price or 0))
        
    def generate_code(self):
        """Otomatik kod üret"""
        # Basit örnek, gerçekte servis üzerinden üretilmeli
        import random
        code = f"STK{random.randint(1000, 9999)}"
        self.code_input.setText(code)
        
    def validate(self) -> bool:
        """Form doğrulama"""
        if not self.code_input.text().strip():
            QMessageBox.warning(self, "Uyarı", "Stok kodu zorunludur!")
            self.tabs.setCurrentIndex(0)
            self.code_input.setFocus()
            return False
            
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Uyarı", "Stok adı zorunludur!")
            self.tabs.setCurrentIndex(0)
            self.name_input.setFocus()
            return False
            
        if self.unit_combo.currentData() is None:
            QMessageBox.warning(self, "Uyarı", "Birim seçimi zorunludur!")
            self.tabs.setCurrentIndex(0)
            self.unit_combo.setFocus()
            return False
            
        return True
        
    def get_form_data(self) -> dict:
        """Form verilerini dictionary olarak döndür"""
        return {
            "code": self.code_input.text().strip(),
            "name": self.name_input.text().strip(),
            "item_type": self.type_combo.currentData(),
            "category_id": self.category_combo.currentData(),
            "unit_id": self.unit_combo.currentData(),
            "barcode": self.barcode_input.text().strip() or None,
            "manufacturer_code": self.manufacturer_code_input.text().strip() or None,
            "brand": self.brand_input.text().strip() or None,
            "model": self.model_input.text().strip() or None,
            "description": self.description_input.toPlainText().strip() or None,
            "min_stock": Decimal(str(self.min_stock_input.value())),
            "max_stock": Decimal(str(self.max_stock_input.value())),
            "reorder_point": Decimal(str(self.reorder_point_input.value())),
            "lead_time_days": self.lead_time_input.value(),
            "track_lot": self.track_lot_check.isChecked(),
            "track_serial": self.track_serial_check.isChecked(),
            "track_expiry": self.track_expiry_check.isChecked(),
            "weight": Decimal(str(self.weight_input.value())) if self.weight_input.value() > 0 else None,
            "volume": Decimal(str(self.volume_input.value())) if self.volume_input.value() > 0 else None,
            "purchase_price": Decimal(str(self.purchase_price_input.value())),
            "sale_price": Decimal(str(self.sale_price_input.value())),
            "currency": self.currency_combo.currentData(),
            "vat_rate": Decimal(str(self.vat_combo.currentData())),
        }
        
    def save(self):
        """Formu kaydet"""
        if not self.validate():
            return
            
        # Kaydetme işlemi parent widget'ta yapılacak
        # Bu sinyal ile veriyi iletiyoruz
        self.saved.emit(self.item.id if self.item else 0)
