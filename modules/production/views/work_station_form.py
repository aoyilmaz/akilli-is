"""
Akıllı İş - İş İstasyonu Form Sayfası
"""

from typing import Optional
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QFrame, QMessageBox, QGridLayout, QCheckBox
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
        back_btn.setStyleSheet("""
            QPushButton { background-color: transparent; border: 1px solid #334155;
                color: #94a3b8; padding: 8px 16px; border-radius: 8px; }
            QPushButton:hover { background-color: #334155; color: #f8fafc; }
        """)
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)
        
        title_text = "İstasyon Düzenle" if self.is_edit_mode else "Yeni İş İstasyonu"
        title = QLabel(f"🏭 {title_text}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc; margin-left: 16px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #a855f7);
                border: none; color: white; font-weight: 600; padding: 12px 24px; border-radius: 12px; }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #9333ea); }
        """)
        save_btn.clicked.connect(self._on_save)
        header_layout.addWidget(save_btn)
        
        layout.addLayout(header_layout)
        
        # Form Frame
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.3);
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(24, 24, 24, 24)
        form_layout.setSpacing(16)
        form_layout.setColumnMinimumWidth(0, 150)
        
        row = 0
        
        # === TEMEL BİLGİLER ===
        section1 = QLabel("📋 Temel Bilgiler")
        section1.setStyleSheet("color: #818cf8; font-size: 16px; font-weight: bold; background: transparent;")
        form_layout.addWidget(section1, row, 0, 1, 2)
        row += 1
        
        # Kod
        form_layout.addWidget(self._create_label("İstasyon Kodu *"), row, 0)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Örn: MCH001, WS001")
        self._style_input(self.code_input)
        form_layout.addWidget(self.code_input, row, 1)
        row += 1
        
        # Ad
        form_layout.addWidget(self._create_label("İstasyon Adı *"), row, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Örn: Ekstrüzyon Makinesi 1")
        self._style_input(self.name_input)
        form_layout.addWidget(self.name_input, row, 1)
        row += 1
        
        # Tür
        form_layout.addWidget(self._create_label("İstasyon Türü *"), row, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItem("⚙️ Makine", "machine")
        self.type_combo.addItem("🔧 İş İstasyonu", "workstation")
        self.type_combo.addItem("🔩 Montaj Hattı", "assembly")
        self.type_combo.addItem("✋ Manuel İşlem", "manual")
        self._style_combo(self.type_combo)
        form_layout.addWidget(self.type_combo, row, 1)
        row += 1
        
        # Açıklama
        form_layout.addWidget(self._create_label("Açıklama"), row, 0)
        self.description_input = QTextEdit()
        self.description_input.setMinimumHeight(80)
        self.description_input.setMaximumHeight(100)
        self.description_input.setPlaceholderText("İstasyon hakkında notlar...")
        self._style_textedit(self.description_input)
        form_layout.addWidget(self.description_input, row, 1)
        row += 1
        
        # === KAPASİTE BİLGİLERİ ===
        section2 = QLabel("📊 Kapasite Bilgileri")
        section2.setStyleSheet("color: #818cf8; font-size: 16px; font-weight: bold; background: transparent; margin-top: 16px;")
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
        self._style_spinbox(self.capacity_input)
        capacity_layout.addWidget(self.capacity_input)
        unit_label = QLabel("birim/saat")
        unit_label.setStyleSheet("color: #94a3b8; background: transparent;")
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
        self._style_spinbox(self.efficiency_input)
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
        self._style_spinbox(self.working_hours_input)
        hours_layout.addWidget(self.working_hours_input)
        hours_layout.addStretch()
        form_layout.addLayout(hours_layout, row, 1)
        row += 1
        
        # === MALİYET BİLGİLERİ ===
        section3 = QLabel("💰 Maliyet Bilgileri")
        section3.setStyleSheet("color: #818cf8; font-size: 16px; font-weight: bold; background: transparent; margin-top: 16px;")
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
        self._style_spinbox(self.hourly_rate_input)
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
        self._style_spinbox(self.setup_cost_input)
        setup_layout.addWidget(self.setup_cost_input)
        setup_layout.addStretch()
        form_layout.addLayout(setup_layout, row, 1)
        row += 1
        
        # === KONUM BİLGİLERİ ===
        section4 = QLabel("📍 Konum Bilgileri")
        section4.setStyleSheet("color: #818cf8; font-size: 16px; font-weight: bold; background: transparent; margin-top: 16px;")
        form_layout.addWidget(section4, row, 0, 1, 2)
        row += 1
        
        # Depo
        form_layout.addWidget(self._create_label("Depo/Tesis"), row, 0)
        self.warehouse_combo = QComboBox()
        self._style_combo(self.warehouse_combo)
        form_layout.addWidget(self.warehouse_combo, row, 1)
        row += 1
        
        # Konum Detayı
        form_layout.addWidget(self._create_label("Konum Detayı"), row, 0)
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Örn: A Blok, 2. Kat, Hücre 15")
        self._style_input(self.location_input)
        form_layout.addWidget(self.location_input, row, 1)
        row += 1
        
        # Aktif
        form_layout.addWidget(self._create_label("Durum"), row, 0)
        self.active_check = QCheckBox("Aktif")
        self.active_check.setChecked(True)
        self.active_check.setStyleSheet("""
            QCheckBox { 
                color: #f8fafc; 
                background: transparent; 
                spacing: 8px;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #334155;
                background-color: #1e293b;
            }
            QCheckBox::indicator:checked {
                background-color: #6366f1;
                border-color: #6366f1;
            }
        """)
        form_layout.addWidget(self.active_check, row, 1)
        row += 1
        
        layout.addWidget(form_frame)
        layout.addStretch()
        
    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("color: #e2e8f0; background: transparent; font-size: 14px;")
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
            "capacity_per_hour": Decimal(str(self.capacity_input.value())),
            "efficiency_rate": Decimal(str(self.efficiency_input.value())),
            "working_hours_per_day": Decimal(str(self.working_hours_input.value())),
            "hourly_rate": Decimal(str(self.hourly_rate_input.value())),
            "setup_cost": Decimal(str(self.setup_cost_input.value())),
            "warehouse_id": self.warehouse_combo.currentData(),
            "location": self.location_input.text().strip(),
            "is_active": self.active_check.isChecked(),
        }
        
        if self.is_edit_mode and self.station_data:
            data["id"] = self.station_data.get("id")
        
        self.saved.emit(data)
        
    def _style_input(self, w):
        w.setMinimumHeight(42)
        w.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b; 
                border: 1px solid #334155;
                border-radius: 8px; 
                padding: 10px 12px; 
                color: #f8fafc;
                font-size: 14px;
            }
            QLineEdit:focus { border-color: #6366f1; }
            QLineEdit::placeholder { color: #64748b; }
        """)
        
    def _style_combo(self, c):
        c.setMinimumHeight(42)
        c.setStyleSheet("""
            QComboBox {
                background-color: #1e293b; 
                border: 1px solid #334155;
                border-radius: 8px; 
                padding: 10px 12px; 
                color: #f8fafc;
                font-size: 14px;
            }
            QComboBox:hover { border-color: #475569; }
            QComboBox::drop-down { 
                border: none; 
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #94a3b8;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b; 
                border: 1px solid #334155;
                color: #f8fafc; 
                selection-background-color: #334155;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                min-height: 32px;
            }
        """)
        
    def _style_spinbox(self, s):
        s.setMinimumHeight(42)
        s.setStyleSheet("""
            QDoubleSpinBox, QSpinBox {
                background-color: #1e293b; 
                border: 1px solid #334155;
                border-radius: 8px; 
                padding: 10px 12px; 
                color: #f8fafc;
                font-size: 14px;
            }
            QDoubleSpinBox:focus, QSpinBox:focus { border-color: #6366f1; }
            QDoubleSpinBox::up-button, QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid #334155;
                border-top-right-radius: 7px;
                background-color: #334155;
            }
            QDoubleSpinBox::down-button, QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 24px;
                border-left: 1px solid #334155;
                border-bottom-right-radius: 7px;
                background-color: #334155;
            }
            QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover,
            QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {
                background-color: #475569;
            }
            QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid #94a3b8;
                width: 0; height: 0;
            }
            QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #94a3b8;
                width: 0; height: 0;
            }
        """)
        
    def _style_textedit(self, t):
        t.setStyleSheet("""
            QTextEdit {
                background-color: #1e293b; 
                border: 1px solid #334155;
                border-radius: 8px; 
                padding: 10px 12px; 
                color: #f8fafc;
                font-size: 14px;
            }
            QTextEdit:focus { border-color: #6366f1; }
        """)
