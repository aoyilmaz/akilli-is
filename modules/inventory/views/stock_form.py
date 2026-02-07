"""
Akıllı İş - Stok Kartı Form Sayfası
"""

from typing import Optional
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QFrame,
    QTabWidget,
    QCheckBox,
    QFormLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta
from ui.components.toast import show_toast
from ui.components import CurrencyInput
from config.icons import ICONS

from database.models import (
    Item,
    ItemType,
    LotSizingProcedure,
    MrpType,
    LotSizePolicy,
    ValuationMethod,
)


class StockFormPage(QWidget):
    """Stok kartı ekleme/düzenleme formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()
    generate_code_requested = pyqtSignal()

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

        # === Header - PageHeader kullanarak ===
        from ui.components.page_header import PageHeader

        title_text = "Stok Kartı Düzenle" if self.is_edit_mode else "Yeni Stok Kartı"

        self.header = PageHeader(
            title=title_text,
            show_back=True,
            show_search=False,
            show_refresh=False,
            show_add=False,  # Add butonu yerine Kaydet kullanacağız
            parent=self,
        )

        # Kaydet butonu
        save_btn = QPushButton("Kaydet")
        save_btn.setIcon(qta.icon(ICONS.SAVE, color="white"))
        save_btn.setProperty("class", "btn-primary")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._on_save)

        # Header'a kaydet butonunu ekle
        h_layout = self.header.header_layout()
        h_layout.addWidget(save_btn)

        # Sinyalleri bağla
        self.header.back_clicked.connect(self.cancelled.emit)

        layout.addWidget(self.header)

        # === Tab Widget ===
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_general_tab(), "Genel Bilgiler")
        self.tabs.addTab(self._create_stock_tab(), "Stok Ayarları")
        self.tabs.addTab(self._create_pricing_tab(), "Fiyatlandırma")
        self.tabs.addTab(self._create_mrp_tab(), "MRP")
        self.tabs.addTab(self._create_tracking_tab(), "Takip")

        layout.addWidget(self.tabs)

    def _create_general_tab(self) -> QWidget:
        """Genel bilgiler sekmesi"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(24)

        # Sol: Temel Bilgiler
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)

        left_title = QLabel("Temel Ürün Bilgileri")
        left_layout.addWidget(left_title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        # 1. Referans
        ref_layout = QHBoxLayout()
        self.ref_stock_info = QLineEdit()
        self.ref_stock_info.setPlaceholderText("Referans seç...")
        self.ref_stock_info.setReadOnly(True)
        ref_btn = QPushButton()
        ref_btn.setIcon(qta.icon(ICONS.FOLDER_OPEN, color="#475569"))
        ref_btn.setFixedSize(30, 30)
        ref_btn.clicked.connect(self._select_reference_stock)
        ref_layout.addWidget(self.ref_stock_info)
        ref_layout.addWidget(ref_btn)
        form.addRow("Referans Kayıt", ref_layout)

        # 2. Stok Kodu
        code_layout = QHBoxLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Otomatik...")
        auto_btn = QPushButton()
        auto_btn.setIcon(qta.icon(ICONS.REFRESH, color="#475569"))
        auto_btn.setFixedSize(30, 30)
        auto_btn.clicked.connect(self._generate_code)
        code_layout.addWidget(self.code_input)
        code_layout.addWidget(auto_btn)
        form.addRow("Stok Kodu *", code_layout)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ürün tam adını giriniz")
        form.addRow("Stok Adı *", self.name_input)

        self.short_name_input = QLineEdit()
        form.addRow("Kısa Ad / Teknik Ad", self.short_name_input)

        self.type_combo = QComboBox()
        # Türleri ekle
        types = [
            (ICONS.TYPE_RAW, "Hammadde", ItemType.HAMMADDE),
            (ICONS.TYPE_PRODUCT, "Mamül", ItemType.MAMUL),
            (ICONS.TYPE_SEMI, "Yarı Mamül", ItemType.YARI_MAMUL),
            (ICONS.TYPE_PACKAGE, "Ambalaj", ItemType.AMBALAJ),
            (ICONS.TYPE_CONSUMABLE, "Sarf Malzeme", ItemType.SARF),
            (ICONS.TYPE_COMMERCIAL, "Ticari Mal", ItemType.TICARI),
            (ICONS.TYPE_SERVICE, "Hizmet", ItemType.HIZMET),
            (ICONS.TYPE_OTHER, "Diğer", ItemType.DIGER),
        ]
        for ico, lbl, val in types:
            self.type_combo.addItem(qta.icon(ico), lbl, val)
        form.addRow("Stok Türü *", self.type_combo)

        self.category_combo = QComboBox()
        self.category_combo.addItem("Seçiniz...", None)
        form.addRow("Kategori", self.category_combo)

        self.unit_combo = QComboBox()
        form.addRow("Birim *", self.unit_combo)

        left_layout.addLayout(form)
        left_layout.addStretch()
        layout.addWidget(left_frame)

        # Sağ: Ek Bilgiler
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)

        right_title = QLabel("Tanımlayıcı Bilgiler ve Açıklama")
        right_layout.addWidget(right_title)

        form2 = QFormLayout()
        form2.setSpacing(12)
        form2.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form2.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.barcode_input = QLineEdit()
        form2.addRow("Barkod", self.barcode_input)

        self.barcode_ean_input = QLineEdit()
        self.barcode_ean_input.setPlaceholderText("EAN-13 / GTIN")
        form2.addRow("EAN Barkod", self.barcode_ean_input)

        self.manufacturer_code_input = QLineEdit()
        form2.addRow("Üretici / Tedarikçi Kodu", self.manufacturer_code_input)

        self.brand_input = QLineEdit()
        form2.addRow("Marka", self.brand_input)

        self.model_input = QLineEdit()
        form2.addRow("Model", self.model_input)

        self.origin_input = QLineEdit()
        self.origin_input.setPlaceholderText("Türkiye")
        form2.addRow("Menşei Ülke", self.origin_input)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Ürünle ilgili detaylı notlar...")
        self.description_input.setMaximumHeight(80)
        form2.addRow("Ağırlık / Notlar", self.description_input)

        right_layout.addLayout(form2)
        right_layout.addStretch()
        layout.addWidget(right_frame)

        return tab

    def _create_stock_tab(self) -> QWidget:
        """Stok ayarları sekmesi"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(24)

        # Sol: Stok Limitleri
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)

        left_title = QLabel("Stok Limitleri")
        left_layout.addWidget(left_title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

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

        right_title = QLabel("Fiziksel Özellikler")
        right_layout.addWidget(right_title)

        form2 = QFormLayout()
        form2.setSpacing(12)
        form2.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form2.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0, 999999)
        self.weight_input.setDecimals(4)
        self.weight_input.setSuffix(" kg")
        form2.addRow("Ağırlık (Genel)", self.weight_input)

        self.net_weight_input = QDoubleSpinBox()
        self.net_weight_input.setRange(0, 999999)
        self.net_weight_input.setDecimals(4)
        self.net_weight_input.setSuffix(" kg")
        form2.addRow("Net Ağırlık", self.net_weight_input)

        self.gross_weight_input = QDoubleSpinBox()
        self.gross_weight_input.setRange(0, 999999)
        self.gross_weight_input.setDecimals(4)
        self.gross_weight_input.setSuffix(" kg")
        form2.addRow("Brüt Ağırlık", self.gross_weight_input)

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

        price_title = QLabel("Fiyat Bilgileri")
        price_layout.addWidget(price_title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.currency_combo = QComboBox()
        self.currency_combo.addItem("₺ Türk Lirası", "TRY")
        self.currency_combo.addItem("$ ABD Doları", "USD")
        self.currency_combo.addItem("€ Euro", "EUR")
        self.currency_combo.currentIndexChanged.connect(self._update_currency_symbols)
        form.addRow("Para Birimi", self.currency_combo)

        # Alış Fiyatı (Butonlu)
        purchase_layout = QHBoxLayout()
        self.purchase_price_input = CurrencyInput()
        self.purchase_price_input.setDecimals(4)
        self.purchase_price_input.setToolTip("Standart alış fiyatı.")

        update_btn = QPushButton()
        update_btn.setIcon(qta.icon(ICONS.REFRESH, color="#475569"))
        update_btn.setToolTip("Son satınalmadan güncelle")
        update_btn.setFixedSize(30, 30)
        update_btn.clicked.connect(self._update_from_last_purchase)

        purchase_layout.addWidget(self.purchase_price_input)
        purchase_layout.addWidget(update_btn)

        form.addRow("Alış Fiyatı", purchase_layout)

        self.sale_price_input = CurrencyInput()
        self.sale_price_input.setDecimals(4)
        form.addRow("Satış Fiyatı", self.sale_price_input)

        self.list_price_input = CurrencyInput()
        self.list_price_input.setDecimals(4)
        form.addRow("Liste Fiyatı", self.list_price_input)

        self.min_sale_price_input = CurrencyInput()
        self.min_sale_price_input.setDecimals(4)

        form.addRow("Min. Satış Fiyatı", self.min_sale_price_input)

        self.valuation_combo = QComboBox()
        self.valuation_combo.addItem("Ağırlıklı Ortalama", ValuationMethod.AVERAGE)
        self.valuation_combo.addItem("Standart Maliyet", ValuationMethod.STANDARD)
        form.addRow("Değerleme Yöntemi", self.valuation_combo)

        price_layout.addLayout(form)
        price_layout.addStretch()
        layout.addWidget(price_frame)

        # Vergiler
        tax_frame = QFrame()
        tax_layout = QVBoxLayout(tax_frame)

        tax_title = QLabel("Vergi Bilgileri")
        tax_layout.addWidget(tax_title)

        form2 = QFormLayout()
        form2.setSpacing(12)
        form2.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form2.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.vat_combo = QComboBox()
        self.vat_combo.addItem("%20", 20)
        self.vat_combo.addItem("%10", 10)
        self.vat_combo.addItem("%1", 1)
        self.vat_combo.addItem("%0", 0)
        self.vat_combo.addItem("%0", 0)
        form2.addRow("KDV Oranı", self.vat_combo)

        self.tax_rate_buy_input = QDoubleSpinBox()
        self.tax_rate_buy_input.setRange(0, 100)
        self.tax_rate_buy_input.setSuffix(" %")
        form2.addRow("Alış KDV", self.tax_rate_buy_input)

        self.tax_rate_sell_input = QDoubleSpinBox()
        self.tax_rate_sell_input.setRange(0, 100)
        self.tax_rate_sell_input.setSuffix(" %")
        form2.addRow("Satış KDV", self.tax_rate_sell_input)

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

    def _create_mrp_tab(self) -> QWidget:
        """MRP ayarları sekmesi"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(24)

        # Sol: Planlama Parametreleri
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)

        left_title = QLabel("Planlama Parametreleri")
        left_layout.addWidget(left_title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.procurement_combo = QComboBox()
        self.procurement_combo.addItem("Satınalma", "purchase")
        self.procurement_combo.addItem("Üretim", "manufacture")

        form.addRow("Tedarik Tipi", self.procurement_combo)

        self.mrp_type_combo = QComboBox()
        self.mrp_type_combo.addItem("Otomatik (AUTO)", MrpType.AUTO)
        self.mrp_type_combo.addItem("Manuel", MrpType.MANUAL)
        self.mrp_type_combo.addItem("Yeniden Sipariş (ROP)", MrpType.ROP)
        form.addRow("MRP Türü", self.mrp_type_combo)

        self.lot_sizing_combo = QComboBox()
        self.lot_sizing_combo.addItem("Tam Miktar (L4L)", LotSizingProcedure.EXACT)
        self.lot_sizing_combo.addItem("Sabit Miktar", LotSizingProcedure.FIXED)
        self.lot_sizing_combo.addItem("Periyodik", LotSizingProcedure.PERIOD)

        form.addRow("Lotlama Prosedürü", self.lot_sizing_combo)

        self.lot_size_policy_combo = QComboBox()
        self.lot_size_policy_combo.addItem(
            "Lot-for-Lot (İhtiyaç Kadar)", LotSizePolicy.LFL
        )
        self.lot_size_policy_combo.addItem("Sabit Miktar", LotSizePolicy.FIXED)
        form.addRow("Lot Büyüklüğü Politikası", self.lot_size_policy_combo)

        self.planning_fence_input = QSpinBox()
        self.planning_fence_input.setRange(0, 999)
        self.planning_fence_input.setSuffix(" gün")
        form.addRow("Planlama Zaman Sınırı", self.planning_fence_input)

        left_layout.addLayout(form)
        left_layout.addStretch()
        layout.addWidget(left_frame)

        # Sağ: Miktar Parametreleri
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)

        right_title = QLabel("Miktar Parametreleri")
        right_layout.addWidget(right_title)

        form2 = QFormLayout()
        form2.setSpacing(12)
        form2.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form2.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.min_order_qty_input = QDoubleSpinBox()
        self.min_order_qty_input.setRange(0, 999999)
        self.min_order_qty_input.setDecimals(2)
        form2.addRow("Min. Sipariş Miktarı", self.min_order_qty_input)

        self.order_multiple_input = QDoubleSpinBox()
        self.order_multiple_input.setRange(0, 999999)
        self.order_multiple_input.setDecimals(2)

        form2.addRow("Sipariş Katı", self.order_multiple_input)

        self.rounding_value_input = QDoubleSpinBox()
        self.rounding_value_input.setRange(0, 999999)
        self.rounding_value_input.setDecimals(2)
        form2.addRow("Yuvarlama Değeri", self.rounding_value_input)

        right_layout.addLayout(form2)
        right_layout.addStretch()
        layout.addWidget(right_frame)

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

        track_title = QLabel("Takip Özellikleri")
        track_layout.addWidget(track_title)

        self.track_lot_check = QCheckBox("Lot/Parti Takibi")
        track_layout.addWidget(self.track_lot_check)

        self.track_serial_check = QCheckBox("Seri Numarası Takibi")
        track_layout.addWidget(self.track_serial_check)

        self.track_expiry_check = QCheckBox("Son Kullanma Tarihi Takibi")

        track_layout.addWidget(self.track_expiry_check)

        self.is_batch_managed_check = QCheckBox("Parti (Batch) Yönetimi")
        track_layout.addWidget(self.is_batch_managed_check)

        self.is_serial_managed_check = QCheckBox("Seri No Yönetimi")
        track_layout.addWidget(self.is_serial_managed_check)

        track_layout.addSpacing(16)

        form = QFormLayout()
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
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

        status_title = QLabel("Durum Ayarları")
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

    def _update_currency_symbols(self):
        """Para birimi değişince sembolleri güncelle"""
        symbol = "₺"
        text = self.currency_combo.currentText()
        if "$" in text:
            symbol = "$"
        elif "€" in text:
            symbol = "€"

        self.purchase_price_input.setSuffix(f" {symbol}")
        self.sale_price_input.setSuffix(f" {symbol}")
        self.list_price_input.setSuffix(f" {symbol}")
        self.min_sale_price_input.setSuffix(f" {symbol}")

    def _update_from_last_purchase(self):
        """Son satınalma fiyatını getir"""
        if not self.item:
            return

        from modules.inventory.services.base import ItemService

        try:
            with ItemService() as service:
                price = service.get_last_purchase_price(self.item.id)
                if price:
                    self.purchase_price_input.setValue(float(price))
                    show_toast("Alış fiyatı güncellendi.", "SUCCESS")
                else:
                    show_toast("Satınalma geçmişi bulunamadı.", "INFO")
        except Exception as e:
            print(f"Error updating price: {e}")
            show_toast("Fiyat güncellenirken hata oluştu.", "ERROR")

    def load_item_data(self):
        """Düzenleme modunda verileri yükle"""
        if not self.item:
            return

        self.code_input.setText(self.item.code)
        self.name_input.setText(self.item.name)
        self.short_name_input.setText(self.item.short_name or "")
        self.barcode_input.setText(self.item.barcode or "")
        self.barcode_ean_input.setText(self.item.barcode_ean or "")
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
        self.net_weight_input.setValue(float(self.item.net_weight or 0))
        self.gross_weight_input.setValue(float(self.item.gross_weight or 0))
        self.volume_input.setValue(float(self.item.volume or 0))
        self.width_input.setValue(float(self.item.width or 0))
        self.height_input.setValue(float(self.item.height or 0))
        self.depth_input.setValue(float(self.item.depth or 0))

        # Fiyatlar
        self.purchase_price_input.setValue(float(self.item.purchase_price or 0))
        self.sale_price_input.setValue(float(self.item.sale_price or 0))
        self.list_price_input.setValue(float(self.item.list_price or 0))
        self.min_sale_price_input.setValue(float(self.item.min_sale_price or 0))

        # Para Birimi
        if self.item.currency:
            code = self.item.currency.code
            for i in range(self.currency_combo.count()):
                if self.currency_combo.itemData(i) == code:
                    self.currency_combo.setCurrentIndex(i)
                    break

        # Sembolleri güncelle
        self._update_currency_symbols()

        # Vergiler
        # Vergiler
        self.withholding_input.setValue(float(self.item.withholding_rate or 0))
        self.tax_rate_buy_input.setValue(float(self.item.tax_rate_buy or 0))
        self.tax_rate_sell_input.setValue(float(self.item.tax_rate_sell or 0))

        # Değerleme Yöntemi
        for i in range(self.valuation_combo.count()):
            if self.valuation_combo.itemData(i) == self.item.valuation_method:
                self.valuation_combo.setCurrentIndex(i)
                break
        self.gtip_input.setText(self.item.gtip_code or "")

        # Takip
        self.track_lot_check.setChecked(bool(self.item.track_lot))
        self.track_serial_check.setChecked(bool(self.item.track_serial))
        self.track_expiry_check.setChecked(bool(self.item.track_expiry))
        self.is_batch_managed_check.setChecked(bool(self.item.is_batch_managed))
        self.is_serial_managed_check.setChecked(bool(self.item.is_serial_managed))
        self.shelf_life_input.setValue(self.item.shelf_life_days or 0)

        # MRP
        for i in range(self.procurement_combo.count()):
            if self.procurement_combo.itemData(i) == self.item.procurement_type:
                self.procurement_combo.setCurrentIndex(i)
                break

        for i in range(self.lot_sizing_combo.count()):
            if self.lot_sizing_combo.itemData(i) == self.item.lot_sizing_procedure:
                self.lot_sizing_combo.setCurrentIndex(i)
                break

        self.planning_fence_input.setValue(self.item.planning_time_fence or 0)
        self.min_order_qty_input.setValue(float(self.item.min_order_qty or 0))
        self.order_multiple_input.setValue(float(self.item.order_multiple or 0))
        self.rounding_value_input.setValue(float(self.item.rounding_value or 0))

        for i in range(self.mrp_type_combo.count()):
            if self.mrp_type_combo.itemData(i) == self.item.mrp_type:
                self.mrp_type_combo.setCurrentIndex(i)
                break

        for i in range(self.lot_size_policy_combo.count()):
            if self.lot_size_policy_combo.itemData(i) == self.item.lot_size_policy:
                self.lot_size_policy_combo.setCurrentIndex(i)
                break

        # Durum
        self.is_purchasable_check.setChecked(bool(self.item.is_purchasable))
        self.is_saleable_check.setChecked(bool(self.item.is_saleable))
        self.is_producible_check.setChecked(bool(self.item.is_producible))
        self.is_active_check.setChecked(bool(self.item.is_active))

    def set_duplicate_mode(self):
        """Formu kopyalama moduna ayarla"""
        self.item = None
        self.is_edit_mode = False
        self.header.title_label.setText("Stok Kartı Kopyala")

        # ID ve kod alanlarını temizle
        self.code_input.clear()
        self.code_input.clear()
        self.barcode_input.clear()
        self.barcode_ean_input.clear()

    def _generate_code(self):
        """Otomatik kod üret - sinyal gönder"""
        self.generate_code_requested.emit()

    def set_items(self, items: list):
        """Referans seçimi için stok listesini ayarla"""
        self.items = items

    def _select_reference_stock(self):
        """Referans stok seçimi"""
        if not hasattr(self, "items") or not self.items:
            show_toast("Seçilebilecek stok bulunamadı.", "WARNING")
            return

        from .item_selector import ItemSelectorDialog

        dialog = ItemSelectorDialog(self.items, self)

        # DialogCode.Accepted yerine 1 kullanabiliriz veya QDialog'u import edip kullanabiliriz.
        # QDialog zaten import edilmiş.
        if dialog.exec() == 1 and dialog.selected_item:  # 1 = Accepted
            item = dialog.selected_item
            self.ref_stock_info.setText(f"{item.code} - {item.name}")
            self._prefill_from_reference(item)

    def _prefill_from_reference(self, item):
        """Form alanlarını referans stoktan doldur"""
        # Adı ve kodu kopyalamıyoruz (Kullanıcı girmeli)

        # Tür
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == item.item_type:
                self.type_combo.setCurrentIndex(i)
                break

        # Kategori
        if item.category_id:
            for i in range(self.category_combo.count()):
                if self.category_combo.itemData(i) == item.category_id:
                    self.category_combo.setCurrentIndex(i)
                    break

        # Birim
        if item.unit_id:
            for i in range(self.unit_combo.count()):
                if self.unit_combo.itemData(i) == item.unit_id:
                    self.unit_combo.setCurrentIndex(i)
                    break

        # Stok ayarları
        self.min_stock_input.setValue(float(item.min_stock or 0))
        self.max_stock_input.setValue(float(item.max_stock or 0))
        self.reorder_point_input.setValue(float(item.reorder_point or 0))

        # Fiziksel ve Fiyatlar
        self.purchase_price_input.setValue(float(item.purchase_price or 0))
        self.sale_price_input.setValue(float(item.sale_price or 0))
        self.vat_combo.setCurrentText(f"%{int(item.vat_rate or 0)}")

        show_toast("Bilgiler şablondan kopyalandı.", "SUCCESS")

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
            show_toast("Stok kodu zorunludur!", "WARNING")
            self.tabs.setCurrentIndex(0)
            self.code_input.setFocus()
            return False

        if not self.name_input.text().strip():
            show_toast("Stok adı zorunludur!", "WARNING")
            self.tabs.setCurrentIndex(0)
            self.name_input.setFocus()
            return False

        if self.unit_combo.currentData() is None:
            show_toast("Birim seçimi zorunludur!", "WARNING")
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
            "net_weight": Decimal(str(self.net_weight_input.value())) or None,
            "gross_weight": Decimal(str(self.gross_weight_input.value())) or None,
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
            "procurement_type": self.procurement_combo.currentData(),
            "lot_sizing_procedure": self.lot_sizing_combo.currentData(),
            "planning_time_fence": self.planning_fence_input.value(),
            "min_order_qty": Decimal(str(self.min_order_qty_input.value())),
            "order_multiple": Decimal(str(self.order_multiple_input.value())),
            "rounding_value": Decimal(str(self.rounding_value_input.value())),
            "barcode_ean": self.barcode_ean_input.text().strip() or None,
            "mrp_type": self.mrp_type_combo.currentData(),
            "lot_size_policy": self.lot_size_policy_combo.currentData(),
            "is_batch_managed": self.is_batch_managed_check.isChecked(),
            "is_serial_managed": self.is_serial_managed_check.isChecked(),
            "tax_rate_buy": Decimal(str(self.tax_rate_buy_input.value())),
            "tax_rate_sell": Decimal(str(self.tax_rate_sell_input.value())),
            "valuation_method": self.valuation_combo.currentData(),
        }
