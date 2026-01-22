"""
Akıllı İş - Sürücü Form Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QTextEdit,
    QLabel,
    QPushButton,
    QTabWidget,
    QMessageBox,
)
from PyQt6.QtCore import pyqtSignal, QDate


class DriverFormPage(QWidget):
    """Sürücü ekleme/düzenleme formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(self, driver_data: dict = None, vehicles: list = None, parent=None):
        super().__init__(parent)
        self.driver_data = driver_data
        self.vehicles = vehicles or []
        self.is_edit = driver_data is not None
        self.setup_ui()
        if self.is_edit:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title_text = "👤 Sürücü Düzenle" if self.is_edit else "👤 Yeni Sürücü"
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

        # Tab 1: Kişisel Bilgiler
        tab1 = self._create_personal_tab()
        self.tabs.addTab(tab1, "📋 Kişisel Bilgiler")

        # Tab 2: Belge Bilgileri
        tab2 = self._create_license_tab()
        self.tabs.addTab(tab2, "📄 Belgeler")

        # Tab 3: Notlar
        tab3 = self._create_notes_tab()
        self.tabs.addTab(tab3, "📝 Notlar")

        layout.addWidget(self.tabs)

    def _create_label(self, text: str) -> QLabel:
        """Standart form etiketi"""
        label = QLabel(text)
        label.setMinimumWidth(140)
        return label

    def _create_personal_tab(self) -> QWidget:
        """Kişisel bilgiler sekmesi"""
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.setColumnMinimumWidth(0, 150)

        row = 0

        # Kod
        layout.addWidget(self._create_label("Sürücü Kodu"), row, 0)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Otomatik oluşturulur")
        self.code_input.setEnabled(False)
        layout.addWidget(self.code_input, row, 1)
        row += 1

        # Ad Soyad
        layout.addWidget(self._create_label("Ad Soyad *"), row, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Sürücü adı soyadı")
        layout.addWidget(self.name_input, row, 1)
        row += 1

        # TC Kimlik No
        layout.addWidget(self._create_label("TC Kimlik No"), row, 0)
        self.tc_input = QLineEdit()
        self.tc_input.setPlaceholderText("11 haneli TC kimlik numarası")
        self.tc_input.setMaxLength(11)
        layout.addWidget(self.tc_input, row, 1)
        row += 1

        # Telefon
        layout.addWidget(self._create_label("Telefon"), row, 0)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Örn: 0532 123 45 67")
        layout.addWidget(self.phone_input, row, 1)
        row += 1

        # Durum
        layout.addWidget(self._create_label("Durum"), row, 0)
        self.status_combo = QComboBox()
        self.status_combo.addItem("Müsait", "musait")
        self.status_combo.addItem("Görevde", "gorevde")
        self.status_combo.addItem("İzinli", "izinli")
        self.status_combo.addItem("Pasif", "pasif")
        layout.addWidget(self.status_combo, row, 1)
        row += 1

        # Varsayılan araç
        layout.addWidget(self._create_label("Varsayılan Araç"), row, 0)
        self.vehicle_combo = QComboBox()
        self.vehicle_combo.addItem("-- Seçiniz --", None)
        for v in self.vehicles:
            self.vehicle_combo.addItem(v.get("display_name", v.get("plate_no")), v.get("id"))
        layout.addWidget(self.vehicle_combo, row, 1)
        row += 1

        layout.setRowStretch(row, 1)
        return tab

    def _create_license_tab(self) -> QWidget:
        """Belge bilgileri sekmesi"""
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.setColumnMinimumWidth(0, 150)

        row = 0

        # Ehliyet tipi
        layout.addWidget(self._create_label("Ehliyet Tipi"), row, 0)
        self.license_type_input = QLineEdit()
        self.license_type_input.setPlaceholderText("Örn: E")
        self.license_type_input.setMaxLength(10)
        layout.addWidget(self.license_type_input, row, 1)
        row += 1

        # Ehliyet bitiş tarihi
        layout.addWidget(self._create_label("Ehliyet Bitiş"), row, 0)
        self.license_expiry_input = QDateEdit()
        self.license_expiry_input.setCalendarPopup(True)
        self.license_expiry_input.setDisplayFormat("dd.MM.yyyy")
        self.license_expiry_input.setDate(QDate.currentDate().addYears(5))
        layout.addWidget(self.license_expiry_input, row, 1)
        row += 1

        # SRC numarası
        layout.addWidget(self._create_label("SRC Belge No"), row, 0)
        self.src_no_input = QLineEdit()
        self.src_no_input.setPlaceholderText("SRC belge numarası")
        layout.addWidget(self.src_no_input, row, 1)
        row += 1

        # SRC bitiş tarihi
        layout.addWidget(self._create_label("SRC Bitiş"), row, 0)
        self.src_expiry_input = QDateEdit()
        self.src_expiry_input.setCalendarPopup(True)
        self.src_expiry_input.setDisplayFormat("dd.MM.yyyy")
        self.src_expiry_input.setDate(QDate.currentDate().addYears(5))
        layout.addWidget(self.src_expiry_input, row, 1)
        row += 1

        layout.setRowStretch(row, 1)
        return tab

    def _create_notes_tab(self) -> QWidget:
        """Notlar sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(QLabel("Sürücü hakkında ek notlar:"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Sürücü hakkında ek notlar...")
        layout.addWidget(self.notes_input)

        return tab

    def load_data(self):
        """Mevcut sürücü verisini forma yükle"""
        if not self.driver_data:
            return

        self.code_input.setText(self.driver_data.get("code", ""))
        self.name_input.setText(self.driver_data.get("name", ""))
        self.tc_input.setText(self.driver_data.get("tc_no", ""))
        self.phone_input.setText(self.driver_data.get("phone", ""))

        # Durum
        status = self.driver_data.get("status", "musait")
        index = self.status_combo.findData(status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)

        # Varsayılan araç
        vehicle_id = self.driver_data.get("default_vehicle_id")
        if vehicle_id:
            index = self.vehicle_combo.findData(vehicle_id)
            if index >= 0:
                self.vehicle_combo.setCurrentIndex(index)

        # Ehliyet
        self.license_type_input.setText(self.driver_data.get("license_type", ""))
        license_expiry = self.driver_data.get("license_expiry")
        if license_expiry:
            self.license_expiry_input.setDate(QDate.fromString(license_expiry, "yyyy-MM-dd"))

        # SRC
        self.src_no_input.setText(self.driver_data.get("src_no", ""))
        src_expiry = self.driver_data.get("src_expiry")
        if src_expiry:
            self.src_expiry_input.setDate(QDate.fromString(src_expiry, "yyyy-MM-dd"))

        self.notes_input.setText(self.driver_data.get("notes", ""))

    def _save(self):
        """Form verisini kaydet"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Uyarı", "Ad Soyad zorunludur.")
            return

        data = {
            "name": name,
            "tc_no": self.tc_input.text().strip() or None,
            "phone": self.phone_input.text().strip() or None,
            "status": self.status_combo.currentData(),
            "default_vehicle_id": self.vehicle_combo.currentData(),
            "license_type": self.license_type_input.text().strip() or None,
            "license_expiry": self.license_expiry_input.date().toString("yyyy-MM-dd"),
            "src_no": self.src_no_input.text().strip() or None,
            "src_expiry": self.src_expiry_input.date().toString("yyyy-MM-dd"),
            "notes": self.notes_input.toPlainText().strip() or None,
        }

        if self.is_edit and self.driver_data:
            data["id"] = self.driver_data.get("id")
            data["code"] = self.driver_data.get("code")

        self.saved.emit(data)
