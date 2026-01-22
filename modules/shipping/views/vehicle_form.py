"""
Akıllı İş - Araç Form Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QTextEdit,
    QLabel,
    QPushButton,
    QTabWidget,
    QMessageBox,
)
from PyQt6.QtCore import pyqtSignal


class VehicleFormPage(QWidget):
    """Araç ekleme/düzenleme formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(self, vehicle_data: dict = None, parent=None):
        super().__init__(parent)
        self.vehicle_data = vehicle_data
        self.is_edit = vehicle_data is not None
        self.setup_ui()
        if self.is_edit:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title_text = "🚛 Araç Düzenle" if self.is_edit else "🚛 Yeni Araç"
        title = QLabel(title_text)
        title.setObjectName("formTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        cancel_btn = QPushButton("❌ İptal")
        cancel_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(self._save)
        header_layout.addWidget(save_btn)

        layout.addLayout(header_layout)

        # Tab Widget
        self.tabs = QTabWidget()

        # Tab 1: Temel Bilgiler
        tab1 = self._create_basic_tab()
        self.tabs.addTab(tab1, "📋 Temel Bilgiler")

        # Tab 2: Kapasite
        tab2 = self._create_capacity_tab()
        self.tabs.addTab(tab2, "📦 Kapasite")

        # Tab 3: Notlar
        tab3 = self._create_notes_tab()
        self.tabs.addTab(tab3, "📝 Notlar")

        layout.addWidget(self.tabs)

    def _create_label(self, text: str) -> QLabel:
        """Standart form etiketi"""
        label = QLabel(text)
        label.setMinimumWidth(120)
        return label

    def _create_basic_tab(self) -> QWidget:
        """Temel bilgiler sekmesi"""
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.setColumnMinimumWidth(0, 150)

        row = 0

        # Plaka
        layout.addWidget(self._create_label("Plaka *"), row, 0)
        self.plate_input = QLineEdit()
        self.plate_input.setPlaceholderText("Örn: 34 ABC 123")
        self.plate_input.setMaxLength(15)
        layout.addWidget(self.plate_input, row, 1)
        row += 1

        # Araç Türü
        layout.addWidget(self._create_label("Araç Türü"), row, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItem("Tır", "tir")
        self.type_combo.addItem("Kamyon", "kamyon")
        self.type_combo.addItem("Kamyonet", "kamyonet")
        self.type_combo.addItem("Panelvan", "panelvan")
        self.type_combo.addItem("Pickup", "pickup")
        self.type_combo.addItem("Diğer", "diger")
        layout.addWidget(self.type_combo, row, 1)
        row += 1

        # Marka
        layout.addWidget(self._create_label("Marka"), row, 0)
        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("Örn: Mercedes")
        layout.addWidget(self.brand_input, row, 1)
        row += 1

        # Model
        layout.addWidget(self._create_label("Model"), row, 0)
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Örn: Actros")
        layout.addWidget(self.model_input, row, 1)
        row += 1

        # Yıl
        layout.addWidget(self._create_label("Model Yılı"), row, 0)
        self.year_input = QSpinBox()
        self.year_input.setRange(1990, 2030)
        self.year_input.setValue(2024)
        layout.addWidget(self.year_input, row, 1)
        row += 1

        # Durum
        layout.addWidget(self._create_label("Durum"), row, 0)
        self.status_combo = QComboBox()
        self.status_combo.addItem("Aktif", "aktif")
        self.status_combo.addItem("Bakımda", "bakimda")
        self.status_combo.addItem("Pasif", "pasif")
        layout.addWidget(self.status_combo, row, 1)
        row += 1

        layout.setRowStretch(row, 1)
        return tab

    def _create_capacity_tab(self) -> QWidget:
        """Kapasite bilgileri sekmesi"""
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.setColumnMinimumWidth(0, 150)

        row = 0

        # Yük kapasitesi (kg)
        layout.addWidget(self._create_label("Yük Kapasitesi"), row, 0)
        self.capacity_kg_input = QDoubleSpinBox()
        self.capacity_kg_input.setRange(0, 100000)
        self.capacity_kg_input.setDecimals(0)
        self.capacity_kg_input.setSuffix(" kg")
        layout.addWidget(self.capacity_kg_input, row, 1)
        row += 1

        # Hacim kapasitesi (m³)
        layout.addWidget(self._create_label("Hacim Kapasitesi"), row, 0)
        self.capacity_m3_input = QDoubleSpinBox()
        self.capacity_m3_input.setRange(0, 200)
        self.capacity_m3_input.setDecimals(1)
        self.capacity_m3_input.setSuffix(" m³")
        layout.addWidget(self.capacity_m3_input, row, 1)
        row += 1

        # Palet kapasitesi
        layout.addWidget(self._create_label("Palet Kapasitesi"), row, 0)
        self.pallet_input = QSpinBox()
        self.pallet_input.setRange(0, 100)
        self.pallet_input.setSuffix(" palet")
        layout.addWidget(self.pallet_input, row, 1)
        row += 1

        layout.setRowStretch(row, 1)
        return tab

    def _create_notes_tab(self) -> QWidget:
        """Notlar sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(QLabel("Araç hakkında ek notlar:"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Araç hakkında ek notlar...")
        layout.addWidget(self.notes_input)

        return tab

    def load_data(self):
        """Mevcut araç verisini forma yükle"""
        if not self.vehicle_data:
            return

        self.plate_input.setText(self.vehicle_data.get("plate_no", ""))
        self.brand_input.setText(self.vehicle_data.get("brand", ""))
        self.model_input.setText(self.vehicle_data.get("model", ""))

        year = self.vehicle_data.get("year")
        if year:
            self.year_input.setValue(year)

        # Combo box değerlerini ayarla
        vehicle_type = self.vehicle_data.get("vehicle_type", "kamyon")
        index = self.type_combo.findData(vehicle_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        status = self.vehicle_data.get("status", "aktif")
        index = self.status_combo.findData(status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)

        # Kapasite
        capacity_kg = self.vehicle_data.get("capacity_kg", 0)
        if capacity_kg:
            self.capacity_kg_input.setValue(float(capacity_kg))

        capacity_m3 = self.vehicle_data.get("capacity_m3", 0)
        if capacity_m3:
            self.capacity_m3_input.setValue(float(capacity_m3))

        pallet = self.vehicle_data.get("pallet_capacity", 0)
        if pallet:
            self.pallet_input.setValue(pallet)

        self.notes_input.setText(self.vehicle_data.get("notes", ""))

    def _save(self):
        """Form verisini kaydet"""
        plate = self.plate_input.text().strip().upper()
        if not plate:
            QMessageBox.warning(self, "Uyarı", "Plaka zorunludur.")
            return

        data = {
            "plate_no": plate,
            "vehicle_type": self.type_combo.currentData(),
            "brand": self.brand_input.text().strip() or None,
            "model": self.model_input.text().strip() or None,
            "year": self.year_input.value(),
            "status": self.status_combo.currentData(),
            "capacity_kg": self.capacity_kg_input.value() or None,
            "capacity_m3": self.capacity_m3_input.value() or None,
            "pallet_capacity": self.pallet_input.value() or None,
            "notes": self.notes_input.toPlainText().strip() or None,
        }

        if self.is_edit and self.vehicle_data:
            data["id"] = self.vehicle_data.get("id")

        self.saved.emit(data)
