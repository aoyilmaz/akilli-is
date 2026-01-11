"""
Akıllı İş - Stok Kartı Form Sayfası
"""

from typing import Optional
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QFrame, QTabWidget, QCheckBox, QMessageBox, QScrollArea,
    QGridLayout, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

from database.models import Item, ItemType

class StockFormPage(QWidget):
    """Stok kartı ekleme/düzenleme formu"""
    
    saved = pyqtSignal(dict)
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
        
        # === Başlık ===
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Geri")
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)
        
        title_text = "Stok Kartı Düzenle" if self.is_edit_mode else "Yeni Stok Kartı"
        title = QLabel(title_text)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Kaydet butonu
        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(self._on_save)
        header_layout.addWidget(save_btn)
        
        layout.addLayout(header_layout)
        
        # === Tab Widget ===
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_general_tab(), "📋 Genel Bilgiler")
        self.tabs.addTab(self._create_stock_tab(), "📦 Stok Ayarları")
        self.tabs.addTab(self._create_pricing_tab(), "💰 Fiyatlandırma")
        self.tabs.addTab(self._create_tracking_tab(), "🔍 Takip")
        
        layout.addWidget(self.tabs)
        
    def _create_general_tab(self) -> QWidget:
        """Genel bilgiler sekmesi"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(24)
        
        # Sol kolon
        left_widget = QWidget()
        left_layout = QFormLayout(left_widget)
        left_layout.setSpacing(16)
        left_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Stok Kodu
        code_layout = QHBoxLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("STK000001")
        auto_btn = QPushButton("🔄")
        auto_btn.setFixedWidth(40)
        auto_btn.setToolTip("Otomatik Kod Üret")
        auto_btn.clicked.connect(self._generate_code)
        code_layout.addWidget(self.code_input)
        code_layout.addWidget(auto_btn)
        left_layout.addRow("Stok Kodu *", code_layout)
        
        # Stok Adı
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ürün adını girin")
        left_layout.addRow("Stok Adı *", self.name_input)
        
        # Kısa Ad
        self.short_name_input = QLineEdit()
        self.short_name_input.setPlaceholderText("Kısa ad (opsiyonel)")
        left_layout.addRow("Kısa Ad", self.short_name_input)
        
        # Tür
        self.type_combo = QComboBox()
        self.type_combo.addItem("🧱 Hammadde", ItemType.HAMMADDE)
        self.type_combo.addItem("📦 Mamül", ItemType.MAMUL)
        self.type_combo.addItem("⚙️ Yarı Mamül", ItemType.YARI_MAMUL)
        self.type_combo.addItem("🎁 Ambalaj", ItemType.AMBALAJ)
        self.type_combo.addItem("🔧 Sarf Malzeme", ItemType.SARF)
        self.type_combo.addItem("🏷️ Ticari Mal", ItemType.TICARI)
        self.type_combo.addItem("💼 Hizmet", ItemType.HIZMET)
        self.type_combo.addItem("📋 Diğer", ItemType.DIGER)
        left_layout.addRow("Tür *", self.type_combo)
        
        # Kategori
        self.category_combo = QComboBox()
        self.category_combo.addItem("Seçiniz...", None)
        left_layout.addRow("Kategori", self.category_combo)
        
        # Birim
        self.unit_combo = QComboBox()
        left_layout.addRow("Birim *", self.unit_combo)
        
        layout.addWidget(left_widget)
        
        # Sağ kolon
        right_widget = QWidget()
        right_layout = QFormLayout(right_widget)
        right_layout.setSpacing(16)
        right_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Barkod
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Barkod numarası")
        right_layout.addRow("Barkod", self.barcode_input)
        
        # Üretici Kodu
        self.manufacturer_code_input = QLineEdit()
        right_layout.addRow("Üretici Kodu", self.manufacturer_code_input)
        
        # Marka
        self.brand_input = QLineEdit()
        right_layout.addRow("Marka", self.brand_input)
        
        # Model
        self.model_input = QLineEdit()
        right_layout.addRow("Model", self.model_input)
        
        # Menşei
        self.origin_input = QLineEdit()
        self.origin_input.setPlaceholderText("Türkiye")
        right_layout.addRow("Menşei", self.origin_input)
        
        # Açıklama
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Ürün açıklaması...")
        self.description_input.setMaximumHeight(100)
        right_layout.addRow("Açıklama", self.description_input)
        
        layout.addWidget(right_widget)
        
        return tab
        
    def _create_stock_tab(self) -> QWidget:
        """Stok ayarları sekmesi"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(24)
        
        # Sol: Stok Limitleri
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        
        left_title = QLabel("📊 Stok Limitleri")
        left_layout.addWidget(left_title)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        self.min_stock_input = QDoubleSpinBox()
        self.min_stock_input.setRange(0, 999999999)
        self.min_stock_input.setDecimals(2)
        form.addRow("Minimum Stok", self.min_stock_input)
        
        self.max_stock_input = QDoubleSpinBox()
        self.max_stock_input.setRange(0, 999999999)
        self.max_stock_input.setDecimals(2)
        form.addRow("Maksimum Stok", self.max_stock_input)
        
        self.reorder_point_input = QDoubleSpinBox()
        self.reorder_point_input.setRange(0, 999999999)
        self.reorder_point_input.setDecimals(2)
        form.addRow("Yeniden Sipariş Noktası", self.reorder_point_input)
        
        self.reorder_qty_input = QDoubleSpinBox()
        self.reorder_qty_input.setRange(0, 999999999)
        self.reorder_qty_input.setDecimals(2)
        form.addRow("Sipariş Miktarı", self.reorder_qty_input)
        
        self.safety_stock_input = QDoubleSpinBox()
        self.safety_stock_input.setRange(0, 999999999)
        self.safety_stock_input.setDecimals(2)
        form.addRow("Emniyet Stoğu", self.safety_stock_input)
        
        self.lead_time_input = QSpinBox()
        self.lead_time_input.setRange(0, 365)
        self.lead_time_input.setSuffix(" gün")
        form.addRow("Temin Süresi", self.lead_time_input)
        
        left_layout.addLayout(form)
        left_layout.addStretch()
        layout.addWidget(left_frame)
        
        # Sağ: Fiziksel Özellikler
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        
        right_title = QLabel("📐 Fiziksel Özellikler")
        right_layout.addWidget(right_title)
        
        form2 = QFormLayout()
        form2.setSpacing(12)
        
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0, 999999)
        self.weight_input.setDecimals(4)
        self.weight_input.setSuffix(" kg")
        form2.addRow("Ağırlık", self.weight_input)
        
        self.volume_input = QDoubleSpinBox()
        self.volume_input.setRange(0, 999999)
        self.volume_input.setDecimals(4)
        self.volume_input.setSuffix(" m³")
        form2.addRow("Hacim", self.volume_input)
        
        self.width_input = QDoubleSpinBox()
        self.width_input.setRange(0, 999999)
        self.width_input.setDecimals(2)
        self.width_input.setSuffix(" cm")
        form2.addRow("Genişlik", self.width_input)
        
        self.height_input = QDoubleSpinBox()
        self.height_input.setRange(0, 999999)
        self.height_input.setDecimals(2)
        self.height_input.setSuffix(" cm")
        form2.addRow("Yükseklik", self.height_input)
        
        self.depth_input = QDoubleSpinBox()
        self.depth_input.setRange(0, 999999)
        self.depth_input.setDecimals(2)
        self.depth_input.setSuffix(" cm")
        form2.addRow("Derinlik", self.depth_input)
        
        right_layout.addLayout(form2)
        right_layout.addStretch()
        layout.addWidget(right_frame)
        
        return tab
        
    def _create_pricing_tab(self) -> QWidget:
        """Fiyatlandırma sekmesi"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(24)
        
        # Fiyatlar
        price_frame = QFrame()
        price_layout = QVBoxLayout(price_frame)
        
        price_title = QLabel("💵 Fiyat Bilgileri")
        price_layout.addWidget(price_title)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        self.purchase_price_input = QDoubleSpinBox()
        self.purchase_price_input.setRange(0, 999999999)
        self.purchase_price_input.setDecimals(4)
        self.purchase_price_input.setPrefix("₺ ")
        form.addRow("Alış Fiyatı", self.purchase_price_input)
        
        self.sale_price_input = QDoubleSpinBox()
        self.sale_price_input.setRange(0, 999999999)
        self.sale_price_input.setDecimals(4)
        self.sale_price_input.setPrefix("₺ ")
        form.addRow("Satış Fiyatı", self.sale_price_input)
        
        self.list_price_input = QDoubleSpinBox()
        self.list_price_input.setRange(0, 999999999)
        self.list_price_input.setDecimals(4)
        self.list_price_input.setPrefix("₺ ")
        form.addRow("Liste Fiyatı", self.list_price_input)
        
        self.min_sale_price_input = QDoubleSpinBox()
        self.min_sale_price_input.setRange(0, 999999999)
        self.min_sale_price_input.setDecimals(4)
        self.min_sale_price_input.setPrefix("₺ ")
        form.addRow("Min. Satış Fiyatı", self.min_sale_price_input)
        
        self.currency_combo = QComboBox()
        self.currency_combo.addItem("₺ Türk Lirası", "TRY")
        self.currency_combo.addItem("$ ABD Doları", "USD")
        self.currency_combo.addItem("€ Euro", "EUR")
        form.addRow("Para Birimi", self.currency_combo)
        
        price_layout.addLayout(form)
        price_layout.addStretch()
        layout.addWidget(price_frame)
        
        # Vergiler
        tax_frame = QFrame()
        tax_layout = QVBoxLayout(tax_frame)
        
        tax_title = QLabel("📊 Vergi Bilgileri")
        tax_layout.addWidget(tax_title)
        
        form2 = QFormLayout()
        form2.setSpacing(12)
        
        self.vat_combo = QComboBox()
        self.vat_combo.addItem("%20", 20)
        self.vat_combo.addItem("%10", 10)
        self.vat_combo.addItem("%1", 1)
        self.vat_combo.addItem("%0", 0)
        form2.addRow("KDV Oranı", self.vat_combo)
        
        self.withholding_input = QDoubleSpinBox()
        self.withholding_input.setRange(0, 100)
        self.withholding_input.setDecimals(2)
        self.withholding_input.setSuffix(" %")
        form2.addRow("Tevkifat Oranı", self.withholding_input)
        
        self.gtip_input = QLineEdit()
        self.gtip_input.setPlaceholderText("GTIP Kodu")
        form2.addRow("GTIP Kodu", self.gtip_input)
        
        tax_layout.addLayout(form2)
        tax_layout.addStretch()
        layout.addWidget(tax_frame)
        
        layout.addStretch()
        
        return tab
        
    def _create_tracking_tab(self) -> QWidget:
        """Takip sekmesi"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(24)
        
        # Takip Özellikleri
        track_frame = QFrame()
        track_layout = QVBoxLayout(track_frame)
        
        track_title = QLabel("🔍 Takip Özellikleri")
        track_layout.addWidget(track_title)
        
        self.track_lot_check = QCheckBox("Lot/Parti Takibi")
        track_layout.addWidget(self.track_lot_check)
        
        self.track_serial_check = QCheckBox("Seri Numarası Takibi")
        track_layout.addWidget(self.track_serial_check)
        
        self.track_expiry_check = QCheckBox("Son Kullanma Tarihi Takibi")
        track_layout.addWidget(self.track_expiry_check)
        
        track_layout.addSpacing(16)
        
        form = QFormLayout()
        self.shelf_life_input = QSpinBox()
        self.shelf_life_input.setRange(0, 9999)
        self.shelf_life_input.setSuffix(" gün")
        form.addRow("Raf Ömrü", self.shelf_life_input)
        
        track_layout.addLayout(form)
        track_layout.addStretch()
        layout.addWidget(track_frame)
        
        # Durum
        status_frame = QFrame()
        status_layout = QVBoxLayout(status_frame)
        
        status_title = QLabel("⚙️ Durum Ayarları")
        status_layout.addWidget(status_title)
        
        self.is_purchasable_check = QCheckBox("Satın Alınabilir")
        self.is_purchasable_check.setChecked(True)
        status_layout.addWidget(self.is_purchasable_check)
        
        self.is_saleable_check = QCheckBox("Satılabilir")
        self.is_saleable_check.setChecked(True)
        status_layout.addWidget(self.is_saleable_check)
        
        self.is_producible_check = QCheckBox("Üretilebilir")
        status_layout.addWidget(self.is_producible_check)
        
        self.is_active_check = QCheckBox("Aktif")
        self.is_active_check.setChecked(True)
        status_layout.addWidget(self.is_active_check)
        
        status_layout.addStretch()
        layout.addWidget(status_frame)
        
        layout.addStretch()
        
        return tab
    
    # === Stil Yardımcıları ===
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
        self.short_name_input.setText(self.item.short_name or "")
        self.barcode_input.setText(self.item.barcode or "")
        self.manufacturer_code_input.setText(self.item.manufacturer_code or "")
        self.brand_input.setText(self.item.brand or "")
        self.model_input.setText(self.item.model or "")
        self.origin_input.setText(self.item.origin_country or "")
        self.description_input.setPlainText(self.item.description or "")
        
        # Tür
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.item.item_type:
                self.type_combo.setCurrentIndex(i)
                break
        
        # Stok ayarları
        self.min_stock_input.setValue(float(self.item.min_stock or 0))
        self.max_stock_input.setValue(float(self.item.max_stock or 0))
        self.reorder_point_input.setValue(float(self.item.reorder_point or 0))
        self.reorder_qty_input.setValue(float(self.item.reorder_quantity or 0))
        self.safety_stock_input.setValue(float(self.item.safety_stock or 0))
        self.lead_time_input.setValue(self.item.lead_time_days or 0)
        
        # Fiziksel
        self.weight_input.setValue(float(self.item.weight or 0))
        self.volume_input.setValue(float(self.item.volume or 0))
        self.width_input.setValue(float(self.item.width or 0))
        self.height_input.setValue(float(self.item.height or 0))
        self.depth_input.setValue(float(self.item.depth or 0))
        
        # Fiyatlar
        self.purchase_price_input.setValue(float(self.item.purchase_price or 0))
        self.sale_price_input.setValue(float(self.item.sale_price or 0))
        self.list_price_input.setValue(float(self.item.list_price or 0))
        self.min_sale_price_input.setValue(float(self.item.min_sale_price or 0))
        
        # Vergiler
        self.withholding_input.setValue(float(self.item.withholding_rate or 0))
        self.gtip_input.setText(self.item.gtip_code or "")
        
        # Takip
        self.track_lot_check.setChecked(self.item.track_lot)
        self.track_serial_check.setChecked(self.item.track_serial)
        self.track_expiry_check.setChecked(self.item.track_expiry)
        self.shelf_life_input.setValue(self.item.shelf_life_days or 0)
        
        # Durum
        self.is_purchasable_check.setChecked(self.item.is_purchasable)
        self.is_saleable_check.setChecked(self.item.is_saleable)
        self.is_producible_check.setChecked(self.item.is_producible)
        self.is_active_check.setChecked(self.item.is_active)
        
    def _generate_code(self):
        """Otomatik kod üret - sinyal gönder"""
        # Bu parent'tan alınacak
        pass
        
    def set_generated_code(self, code: str):
        """Üretilen kodu ayarla"""
        self.code_input.setText(code)
        
    def _on_save(self):
        """Kaydet butonuna tıklandı"""
        if not self._validate():
            return
        
        data = self.get_form_data()
        self.saved.emit(data)
        
    def _validate(self) -> bool:
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
        """Form verilerini döndür"""
        return {
            "code": self.code_input.text().strip(),
            "name": self.name_input.text().strip(),
            "short_name": self.short_name_input.text().strip() or None,
            "item_type": self.type_combo.currentData(),
            "category_id": self.category_combo.currentData(),
            "unit_id": self.unit_combo.currentData(),
            "barcode": self.barcode_input.text().strip() or None,
            "manufacturer_code": self.manufacturer_code_input.text().strip() or None,
            "brand": self.brand_input.text().strip() or None,
            "model": self.model_input.text().strip() or None,
            "origin_country": self.origin_input.text().strip() or None,
            "description": self.description_input.toPlainText().strip() or None,
            
            "min_stock": Decimal(str(self.min_stock_input.value())),
            "max_stock": Decimal(str(self.max_stock_input.value())),
            "reorder_point": Decimal(str(self.reorder_point_input.value())),
            "reorder_quantity": Decimal(str(self.reorder_qty_input.value())),
            "safety_stock": Decimal(str(self.safety_stock_input.value())),
            "lead_time_days": self.lead_time_input.value(),
            
            "weight": Decimal(str(self.weight_input.value())) or None,
            "volume": Decimal(str(self.volume_input.value())) or None,
            "width": Decimal(str(self.width_input.value())) or None,
            "height": Decimal(str(self.height_input.value())) or None,
            "depth": Decimal(str(self.depth_input.value())) or None,
            
            "purchase_price": Decimal(str(self.purchase_price_input.value())),
            "sale_price": Decimal(str(self.sale_price_input.value())),
            "list_price": Decimal(str(self.list_price_input.value())),
            "min_sale_price": Decimal(str(self.min_sale_price_input.value())),
            "vat_rate": Decimal(str(self.vat_combo.currentData())),
            "withholding_rate": Decimal(str(self.withholding_input.value())),
            "gtip_code": self.gtip_input.text().strip() or None,
            
            "track_lot": self.track_lot_check.isChecked(),
            "track_serial": self.track_serial_check.isChecked(),
            "track_expiry": self.track_expiry_check.isChecked(),
            "shelf_life_days": self.shelf_life_input.value() or None,
            
            "is_purchasable": self.is_purchasable_check.isChecked(),
            "is_saleable": self.is_saleable_check.isChecked(),
            "is_producible": self.is_producible_check.isChecked(),
            "is_active": self.is_active_check.isChecked(),
        }
