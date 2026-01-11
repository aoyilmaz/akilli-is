"""
Akilli Is - Birim Yonetimi Sayfasi
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QAbstractItemView, QMenu, QMessageBox, QDialog,
    QFormLayout, QCheckBox, QDoubleSpinBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction

from config.styles import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HOVER, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, ACCENT, SUCCESS, WARNING, ERROR,
    get_table_style, get_button_style, get_input_style
)

class UnitDialog(QDialog):
    """Birim ekleme/duzenleme dialogu"""

    def __init__(self, unit_data: dict = None, parent=None):
        super().__init__(parent)
        self.unit_data = unit_data
        self.is_edit = unit_data is not None
        self.setup_ui()
        if self.is_edit:
            self.load_data()

    def setup_ui(self):
        self.setWindowTitle("Birim Duzenle" if self.is_edit else "Yeni Birim")
        self.setFixedWidth(400)
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(12)

        # Kod
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("KG, ADET, LT...")
        form.addRow("Birim Kodu *", self.code_input)

        # Ad
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Kilogram, Adet, Litre...")
        form.addRow("Birim Adi *", self.name_input)

        # Kisa Ad
        self.short_name_input = QLineEdit()
        self.short_name_input.setPlaceholderText("Kisa gosterim")
        form.addRow("Kisa Ad", self.short_name_input)

        # Aktif
        self.is_active_check = QCheckBox("Aktif")
        self.is_active_check.setChecked(True)
        form.addRow("", self.is_active_check)

        layout.addLayout(form)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Iptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def load_data(self):
        if not self.unit_data:
            return
        self.code_input.setText(self.unit_data.get("code", ""))
        self.name_input.setText(self.unit_data.get("name", ""))
        self.short_name_input.setText(self.unit_data.get("short_name", ""))
        self.is_active_check.setChecked(self.unit_data.get("is_active", True))

    def _on_save(self):
        if not self.code_input.text().strip():
            QMessageBox.warning(self, "Uyari", "Birim kodu zorunludur!")
            return
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Uyari", "Birim adi zorunludur!")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "code": self.code_input.text().strip().upper(),
            "name": self.name_input.text().strip(),
            "short_name": self.short_name_input.text().strip() or None,
            "is_active": self.is_active_check.isChecked(),
        }

class UnitConversionDialog(QDialog):
    """Birim donusumu dialogu"""

    def __init__(self, units: list, conversion_data: dict = None, parent=None):
        super().__init__(parent)
        self.units = units
        self.conversion_data = conversion_data
        self.is_edit = conversion_data is not None
        self.setup_ui()
        if self.is_edit:
            self.load_data()

    def setup_ui(self):
        self.setWindowTitle("Birim Donusumu")
        self.setFixedWidth(450)
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Aciklama
        info = QLabel("Ornek: 1 KUTU = 12 ADET")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(12)

        # Kaynak birim
        self.from_combo = QComboBox()
        for unit in self.units:
            self.from_combo.addItem(f"{unit['code']} - {unit['name']}", unit['id'])
        form.addRow("Kaynak Birim", self.from_combo)

        # Hedef birim
        self.to_combo = QComboBox()
        for unit in self.units:
            self.to_combo.addItem(f"{unit['code']} - {unit['name']}", unit['id'])
        form.addRow("Hedef Birim", self.to_combo)

        # Carpan
        self.factor_input = QDoubleSpinBox()
        self.factor_input.setRange(0.0001, 999999999)
        self.factor_input.setDecimals(6)
        self.factor_input.setValue(1)
        form.addRow("Carpan (1 kaynak = ? hedef)", self.factor_input)

        layout.addLayout(form)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Iptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def load_data(self):
        if not self.conversion_data:
            return
        # TODO: Verileri yukle

    def _on_save(self):
        if self.from_combo.currentData() == self.to_combo.currentData():
            QMessageBox.warning(self, "Uyari", "Kaynak ve hedef birim ayni olamaz!")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "from_unit_id": self.from_combo.currentData(),
            "to_unit_id": self.to_combo.currentData(),
            "factor": self.factor_input.value(),
        }

class UnitManagementPage(QWidget):
    """Birim yonetimi sayfasi"""

    page_title = "Birimler"
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.units_data = []
        self.conversions_data = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # === Baslik ===
        header_layout = QHBoxLayout()

        title = QLabel("Birim Yonetimi")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Yenile
        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)

        # Yeni birim
        add_btn = QPushButton("Yeni Birim")
        add_btn.clicked.connect(self._add_unit)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # === Iki Bolum ===
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        # Sol: Birimler
        units_frame = QFrame()
        units_layout = QVBoxLayout(units_frame)
        units_layout.setContentsMargins(16, 16, 16, 16)

        units_header = QLabel("Birimler")
        units_layout.addWidget(units_header)

        self.units_table = QTableWidget()
        self._setup_units_table()
        units_layout.addWidget(self.units_table)

        content_layout.addWidget(units_frame, 2)

        # Sag: Donusumler
        conv_frame = QFrame()
        conv_layout = QVBoxLayout(conv_frame)
        conv_layout.setContentsMargins(16, 16, 16, 16)

        conv_header_layout = QHBoxLayout()
        conv_header = QLabel("Birim Donusumleri")
        conv_header_layout.addWidget(conv_header)

        conv_header_layout.addStretch()

        add_conv_btn = QPushButton("+")
        add_conv_btn.setFixedSize(32, 32)
        add_conv_btn.clicked.connect(self._add_conversion)
        conv_header_layout.addWidget(add_conv_btn)

        conv_layout.addLayout(conv_header_layout)

        self.conv_table = QTableWidget()
        self._setup_conv_table()
        conv_layout.addWidget(self.conv_table)

        content_layout.addWidget(conv_frame, 1)

        layout.addLayout(content_layout)

    def _setup_units_table(self):
        columns = [("Kod", 80), ("Birim Adi", 150), ("Kisa Ad", 80), ("Durum", 80)]

        self.units_table.setColumnCount(len(columns))
        self.units_table.setHorizontalHeaderLabels([c[0] for c in columns])

        header = self.units_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i, (_, w) in enumerate(columns):
            if i != 1:
                self.units_table.setColumnWidth(i, w)

        self.units_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.units_table.verticalHeader().setVisible(False)
        self.units_table.setShowGrid(False)
        self.units_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.units_table.customContextMenuRequested.connect(self._show_unit_menu)

    def _setup_conv_table(self):
        columns = [("Kaynak", 80), ("Hedef", 80), ("Carpan", 100)]

        self.conv_table.setColumnCount(len(columns))
        self.conv_table.setHorizontalHeaderLabels([c[0] for c in columns])

        header = self.conv_table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self.conv_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.conv_table.verticalHeader().setVisible(False)
        self.conv_table.setShowGrid(False)
    def load_units(self, units: list):
        """Birimleri yukle"""
        self.units_data = []
        self.units_table.setRowCount(len(units))

        for row, unit in enumerate(units):
            unit_dict = {
                "id": unit.id,
                "code": unit.code,
                "name": unit.name,
                "short_name": unit.short_name,
                "is_active": unit.is_active,
            }
            self.units_data.append(unit_dict)

            code_item = QTableWidgetItem(unit.code)
            code_item.setData(Qt.ItemDataRole.UserRole, unit.id)
            code_item.setForeground(QColor(ACCENT))
            self.units_table.setItem(row, 0, code_item)

            self.units_table.setItem(row, 1, QTableWidgetItem(unit.name))
            self.units_table.setItem(row, 2, QTableWidgetItem(unit.short_name or ""))

            status = "Aktif" if unit.is_active else "Pasif"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor(SUCCESS if unit.is_active else ERROR))
            self.units_table.setItem(row, 3, status_item)

    def load_conversions(self, conversions: list):
        """Birim donusumlerini yukle"""
        self.conversions_data = conversions
        self.conv_table.setRowCount(len(conversions))

        for row, conv in enumerate(conversions):
            self.conv_table.setItem(row, 0, QTableWidgetItem(conv.get("from_code", "")))
            self.conv_table.setItem(row, 1, QTableWidgetItem(conv.get("to_code", "")))

            factor = conv.get("factor", 1)
            factor_item = QTableWidgetItem(f"{factor:,.6f}")
            factor_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.conv_table.setItem(row, 2, factor_item)

    def _add_unit(self):
        dialog = UnitDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            # TODO: Servise kaydet
            QMessageBox.information(self, "Bilgi", f"Birim '{data['code']}' eklendi!")
            self.refresh_requested.emit()

    def _add_conversion(self):
        if not self.units_data:
            QMessageBox.warning(self, "Uyari", "Once birim eklemelisiniz!")
            return
        dialog = UnitConversionDialog(self.units_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            # TODO: Servise kaydet
            QMessageBox.information(self, "Bilgi", "Birim donusumu eklendi!")
            self.refresh_requested.emit()

    def _show_unit_menu(self, position):
        row = self.units_table.rowAt(position.y())
        if row < 0:
            return

        unit_id = self.units_table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)
        edit_action = QAction("Duzenle", self)
        edit_action.triggered.connect(lambda: self._edit_unit(unit_id))
        menu.addAction(edit_action)

        menu.exec(self.units_table.viewport().mapToGlobal(position))

    def _edit_unit(self, unit_id: int):
        unit_data = next((u for u in self.units_data if u["id"] == unit_id), None)
        if unit_data:
            dialog = UnitDialog(unit_data, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                # TODO: Servise kaydet
                self.refresh_requested.emit()
