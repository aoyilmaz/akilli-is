"""
Akıllı İş - İş İstasyonu Form Sayfası
Varsayılan Operasyon Değerleri Eklendi
"""

from typing import Optional
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QFrame, QMessageBox, QGridLayout, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal

class WorkStationFormPage(QWidget):
    """İş istasyonu formu"""
    
    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()
    
    def __init__(self, station_data: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.station_data = station_data
        self.is_edit_mode = station_data is not None
        self.setup_ui()
        if self.is_edit_mode:
            self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Başlık
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Geri")
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)
        
        title_text = "İstasyon Düzenle" if self.is_edit_mode else "Yeni İş İstasyonu"
        title = QLabel(f"🏭 {title_text}")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(self._on_save)
        header_layout.addWidget(save_btn)
        
        layout.addLayout(header_layout)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(16)
        
        # Form Frame
        form_frame = QFrame()
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(24, 24, 24, 24)
        form_layout.setSpacing(16)
        form_layout.setColumnMinimumWidth(0, 180)
        
        row = 0
        
        # === TEMEL BİLGİLER ===
        section1 = QLabel("📋 Temel Bilgiler")
        form_layout.addWidget(section1, row, 0, 1, 2)
        row += 1
        
        # Kod
        form_layout.addWidget(self._create_label("İstasyon Kodu *"), row, 0)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Örn: MCH001, WS001")
        form_layout.addWidget(self.code_input, row, 1)
        row += 1
        
        # Ad
        form_layout.addWidget(self._create_label("İstasyon Adı *"), row, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Örn: Ekstrüzyon Makinesi 1")
        form_layout.addWidget(self.name_input, row, 1)
        row += 1
        
        # Tür
        form_layout.addWidget(self._create_label("İstasyon Türü *"), row, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItem("⚙️ Makine", "machine")
        self.type_combo.addItem("🔧 İş İstasyonu", "workstation")
        self.type_combo.addItem("🔩 Montaj Hattı", "assembly")
        self.type_combo.addItem("✋ Manuel İşlem", "manual")
        form_layout.addWidget(self.type_combo, row, 1)
        row += 1
        
        # Açıklama
        form_layout.addWidget(self._create_label("Açıklama"), row, 0)
        self.description_input = QTextEdit()
        self.description_input.setMinimumHeight(80)
        self.description_input.setMaximumHeight(100)
        self.description_input.setPlaceholderText("İstasyon hakkında notlar...")
        form_layout.addWidget(self.description_input, row, 1)
        row += 1
        
        # === VARSAYILAN OPERASYON DEĞERLERİ (YENİ) ===
        section_op = QLabel("⚡ Varsayılan Operasyon Değerleri")
        form_layout.addWidget(section_op, row, 0, 1, 2)
        row += 1
        
        # Bilgi notu
        op_info = QLabel("ℹ️ Bu değerler, iş emrine operasyon eklerken otomatik doldurulur")
        form_layout.addWidget(op_info, row, 0, 1, 2)
        row += 1
        
        # Varsayılan Operasyon Adı
        form_layout.addWidget(self._create_label("Varsayılan Operasyon Adı"), row, 0)
        self.default_op_name_input = QLineEdit()
        self.default_op_name_input.setPlaceholderText("Örn: Ekstrüzyon, Kesim, Montaj")
        form_layout.addWidget(self.default_op_name_input, row, 1)
        row += 1
        
        # Varsayılan Kurulum Süresi
        form_layout.addWidget(self._create_label("Varsayılan Kurulum Süresi"), row, 0)
        setup_time_layout = QHBoxLayout()
        setup_time_layout.setSpacing(8)
        self.default_setup_time_input = QSpinBox()
        self.default_setup_time_input.setRange(0, 9999)
        self.default_setup_time_input.setValue(0)
        self.default_setup_time_input.setMinimumWidth(150)
        setup_time_layout.addWidget(self.default_setup_time_input)
        setup_label = QLabel("dakika")
        setup_time_layout.addWidget(setup_label)
        setup_info = QLabel("(Makineyi hazırlama süresi)")
        setup_time_layout.addWidget(setup_info)
        setup_time_layout.addStretch()
        form_layout.addLayout(setup_time_layout, row, 1)
        row += 1
        
        # Varsayılan Birim Çalışma Süresi
        form_layout.addWidget(self._create_label("Varsayılan Birim Süresi"), row, 0)
        run_time_layout = QHBoxLayout()
        run_time_layout.setSpacing(8)
        self.default_run_time_input = QDoubleSpinBox()
        self.default_run_time_input.setRange(0, 9999)
        self.default_run_time_input.setDecimals(4)
        self.default_run_time_input.setValue(0)
        self.default_run_time_input.setMinimumWidth(150)
        run_time_layout.addWidget(self.default_run_time_input)
        run_label = QLabel("dk/birim")
        run_time_layout.addWidget(run_label)
        run_info = QLabel("(1 birim üretmek için gereken süre)")
        run_time_layout.addWidget(run_info)
        run_time_layout.addStretch()
        form_layout.addLayout(run_time_layout, row, 1)
        row += 1
        
        # Hesaplama örneği
        calc_example = QFrame()
        calc_layout = QVBoxLayout(calc_example)
        calc_layout.setContentsMargins(12, 8, 12, 8)
        calc_layout.setSpacing(4)
        
        calc_title = QLabel("📊 Süre Hesaplama Örneği:")
        calc_layout.addWidget(calc_title)
        
        calc_text = QLabel("Kurulum: 60 dk + (Birim Süre: 0.27 dk × Miktar: 1000) = 330 dk = 5.5 saat")
        calc_layout.addWidget(calc_text)
        
        form_layout.addWidget(calc_example, row, 0, 1, 2)
        row += 1
        
        # === KAPASİTE BİLGİLERİ ===
        section2 = QLabel("📊 Kapasite Bilgileri")
        form_layout.addWidget(section2, row, 0, 1, 2)
        row += 1
        
        # Saatlik Kapasite
        form_layout.addWidget(self._create_label("Saatlik Kapasite"), row, 0)
        capacity_layout = QHBoxLayout()
        capacity_layout.setSpacing(8)
        self.capacity_input = QDoubleSpinBox()
        self.capacity_input.setRange(0, 999999)
        self.capacity_input.setDecimals(2)
        self.capacity_input.setMinimumWidth(150)
        capacity_layout.addWidget(self.capacity_input)
        unit_label = QLabel("birim/saat")
        capacity_layout.addWidget(unit_label)
        capacity_layout.addStretch()
        form_layout.addLayout(capacity_layout, row, 1)
        row += 1
        
        # Verimlilik
        form_layout.addWidget(self._create_label("Verimlilik Oranı"), row, 0)
        efficiency_layout = QHBoxLayout()
        efficiency_layout.setSpacing(8)
        self.efficiency_input = QDoubleSpinBox()
        self.efficiency_input.setRange(0, 100)
        self.efficiency_input.setDecimals(1)
        self.efficiency_input.setValue(100)
        self.efficiency_input.setSuffix(" %")
        self.efficiency_input.setMinimumWidth(150)
        efficiency_layout.addWidget(self.efficiency_input)
        efficiency_layout.addStretch()
        form_layout.addLayout(efficiency_layout, row, 1)
        row += 1
        
        # Günlük Çalışma Saati
        form_layout.addWidget(self._create_label("Günlük Çalışma"), row, 0)
        hours_layout = QHBoxLayout()
        hours_layout.setSpacing(8)
        self.working_hours_input = QDoubleSpinBox()
        self.working_hours_input.setRange(0, 24)
        self.working_hours_input.setDecimals(1)
        self.working_hours_input.setValue(8)
        self.working_hours_input.setSuffix(" saat")
        self.working_hours_input.setMinimumWidth(150)
        hours_layout.addWidget(self.working_hours_input)
        hours_layout.addStretch()
        form_layout.addLayout(hours_layout, row, 1)
        row += 1
        
        # === MALİYET BİLGİLERİ ===
        section3 = QLabel("💰 Maliyet Bilgileri")
        form_layout.addWidget(section3, row, 0, 1, 2)
        row += 1
        
        # Saatlik Maliyet
        form_layout.addWidget(self._create_label("Saatlik Maliyet"), row, 0)
        hourly_layout = QHBoxLayout()
        hourly_layout.setSpacing(8)
        self.hourly_rate_input = QDoubleSpinBox()
        self.hourly_rate_input.setRange(0, 999999)
        self.hourly_rate_input.setDecimals(2)
        self.hourly_rate_input.setPrefix("₺ ")
        self.hourly_rate_input.setMinimumWidth(150)
        hourly_layout.addWidget(self.hourly_rate_input)
        hourly_layout.addStretch()
        form_layout.addLayout(hourly_layout, row, 1)
        row += 1
        
        # Hazırlık Maliyeti
        form_layout.addWidget(self._create_label("Hazırlık Maliyeti"), row, 0)
        setup_layout = QHBoxLayout()
        setup_layout.setSpacing(8)
        self.setup_cost_input = QDoubleSpinBox()
        self.setup_cost_input.setRange(0, 999999)
        self.setup_cost_input.setDecimals(2)
        self.setup_cost_input.setPrefix("₺ ")
        self.setup_cost_input.setMinimumWidth(150)
        setup_layout.addWidget(self.setup_cost_input)
        setup_layout.addStretch()
        form_layout.addLayout(setup_layout, row, 1)
        row += 1
        
        # === KONUM BİLGİLERİ ===
        section4 = QLabel("📍 Konum Bilgileri")
        form_layout.addWidget(section4, row, 0, 1, 2)
        row += 1
        
        # Depo
        form_layout.addWidget(self._create_label("Depo/Tesis"), row, 0)
        self.warehouse_combo = QComboBox()
        form_layout.addWidget(self.warehouse_combo, row, 1)
        row += 1
        
        # Konum Detayı
        form_layout.addWidget(self._create_label("Konum Detayı"), row, 0)
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Örn: A Blok, 2. Kat, Hücre 15")
        form_layout.addWidget(self.location_input, row, 1)
        row += 1
        
        # Aktif
        form_layout.addWidget(self._create_label("Durum"), row, 0)
        self.active_check = QCheckBox("Aktif")
        self.active_check.setChecked(True)
        form_layout.addWidget(self.active_check, row, 1)
        row += 1
        
        scroll_layout.addWidget(form_frame)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return label
        
    def set_warehouses(self, warehouses: list):
        """Depo listesini ayarla"""
        self.warehouse_combo.clear()
        self.warehouse_combo.addItem("Seçiniz...", None)
        for w in warehouses:
            self.warehouse_combo.addItem(f"{w.code} - {w.name}", w.id)
            
    def load_data(self):
        """Düzenleme modunda verileri yükle"""
        if not self.station_data:
            return
        
        self.code_input.setText(self.station_data.get("code", ""))
        self.name_input.setText(self.station_data.get("name", ""))
        self.description_input.setPlainText(self.station_data.get("description", ""))
        
        # Tür
        station_type = self.station_data.get("station_type", "machine")
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == station_type:
                self.type_combo.setCurrentIndex(i)
                break
        
        # Varsayılan operasyon değerleri
        self.default_op_name_input.setText(self.station_data.get("default_operation_name", "") or "")
        self.default_setup_time_input.setValue(int(self.station_data.get("default_setup_time", 0) or 0))
        self.default_run_time_input.setValue(float(self.station_data.get("default_run_time_per_unit", 0) or 0))
        
        # Kapasite
        self.capacity_input.setValue(float(self.station_data.get("capacity_per_hour", 0) or 0))
        self.efficiency_input.setValue(float(self.station_data.get("efficiency_rate", 100) or 100))
        self.working_hours_input.setValue(float(self.station_data.get("working_hours_per_day", 8) or 8))
        
        # Maliyet
        self.hourly_rate_input.setValue(float(self.station_data.get("hourly_rate", 0) or 0))
        self.setup_cost_input.setValue(float(self.station_data.get("setup_cost", 0) or 0))
        
        # Konum
        self.location_input.setText(self.station_data.get("location", ""))
        
        # Depo
        warehouse_id = self.station_data.get("warehouse_id")
        if warehouse_id:
            for i in range(self.warehouse_combo.count()):
                if self.warehouse_combo.itemData(i) == warehouse_id:
                    self.warehouse_combo.setCurrentIndex(i)
                    break
        
        # Aktif
        self.active_check.setChecked(self.station_data.get("is_active", True))
        
    def _on_save(self):
        """Kaydet"""
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()
        
        if not code:
            QMessageBox.warning(self, "Uyarı", "İstasyon kodu zorunludur!")
            self.code_input.setFocus()
            return
            
        if not name:
            QMessageBox.warning(self, "Uyarı", "İstasyon adı zorunludur!")
            self.name_input.setFocus()
            return
        
        data = {
            "code": code,
            "name": name,
            "description": self.description_input.toPlainText().strip(),
            "station_type": self.type_combo.currentData(),
            # Varsayılan operasyon değerleri
            "default_operation_name": self.default_op_name_input.text().strip(),
            "default_setup_time": self.default_setup_time_input.value(),
            "default_run_time_per_unit": Decimal(str(self.default_run_time_input.value())),
            # Kapasite
            "capacity_per_hour": Decimal(str(self.capacity_input.value())),
            "efficiency_rate": Decimal(str(self.efficiency_input.value())),
            "working_hours_per_day": Decimal(str(self.working_hours_input.value())),
            # Maliyet
            "hourly_rate": Decimal(str(self.hourly_rate_input.value())),
            "setup_cost": Decimal(str(self.setup_cost_input.value())),
            # Konum
            "warehouse_id": self.warehouse_combo.currentData(),
            "location": self.location_input.text().strip(),
            "is_active": self.active_check.isChecked(),
        }
        
        if self.is_edit_mode and self.station_data:
            data["id"] = self.station_data.get("id")
        
        self.saved.emit(data)
        