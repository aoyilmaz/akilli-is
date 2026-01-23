from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QMessageBox,
    QDialog,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from database.models.quality import InspectionType, CriteriaType
from modules.quality.services import QualityService
from modules.inventory.services import ItemService


class CriteriaDialog(QDialog):
    def __init__(self, parent=None, criteria_data=None):
        super().__init__(parent)
        self.setWindowTitle("Kriter Ekle/Düzenle")
        self.setMinimumWidth(400)
        self.criteria_data = criteria_data
        self.setup_ui()
        if criteria_data:
            self.load_data()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        layout.addRow("Kriter Adı *", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems([t.value for t in CriteriaType])
        layout.addRow("Tip *", self.type_combo)

        self.min_input = QDoubleSpinBox()
        self.min_input.setRange(-999999, 999999)
        layout.addRow("Min Tolerans", self.min_input)

        self.max_input = QDoubleSpinBox()
        self.max_input.setRange(-999999, 999999)
        layout.addRow("Max Tolerans", self.max_input)

        self.unit_input = QLineEdit()
        layout.addRow("Birim", self.unit_input)

        self.required_check = QCheckBox("Zorunlu")
        self.required_check.setChecked(True)
        layout.addRow("", self.required_check)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def load_data(self):
        self.name_input.setText(self.criteria_data.get("name", ""))
        # Set combo index logic...
        self.min_input.setValue(float(self.criteria_data.get("tolerance_min") or 0))
        self.max_input.setValue(float(self.criteria_data.get("tolerance_max") or 0))
        self.unit_input.setText(self.criteria_data.get("unit", ""))
        self.required_check.setChecked(self.criteria_data.get("is_required", True))

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "criteria_type": self.type_combo.currentText(),
            "tolerance_min": self.min_input.value(),
            "tolerance_max": self.max_input.value(),
            "unit": self.unit_input.text(),
            "is_required": self.required_check.isChecked(),
        }


class TemplateFormPage(QWidget):
    saved = pyqtSignal(object)
    cancelled = pyqtSignal()

    def __init__(self, template=None):
        super().__init__()
        self.template = template
        self.service = QualityService()
        self.inventory_service = ItemService()
        self.criteria_list = []
        self.setup_ui()
        if template:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header Fields
        form_layout = QHBoxLayout()

        # Left Side
        left_layout = QFormLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Şablon Kodu")
        left_layout.addRow("Kod *", self.code_input)

        self.name_input = QLineEdit()
        left_layout.addRow("Ad *", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems([t.value for t in InspectionType])
        left_layout.addRow("Kontrol Tipi", self.type_combo)

        self.item_combo = QComboBox()
        self.item_combo.addItem("Seçiniz...", None)
        # Load Items (simplified)
        items = self.inventory_service.get_all()
        for item in items:
            self.item_combo.addItem(f"{item.code} - {item.name}", item.id)
        left_layout.addRow("Stok Kartı", self.item_combo)

        form_layout.addLayout(left_layout)

        # Description
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("Açıklama"))
        self.desc_input = QTextEdit()
        desc_layout.addWidget(self.desc_input)
        form_layout.addLayout(desc_layout)

        layout.addLayout(form_layout)

        # Criteria Table
        layout.addWidget(QLabel("Kontrol Kriterleri"))
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Sıra", "Ad", "Tip", "Tolerans", "Birim"])
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Kriter Ekle")
        add_btn.clicked.connect(self.add_criteria)
        btn_layout.addWidget(add_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def load_data(self):
        self.code_input.setText(self.template.code)
        self.name_input.setText(self.template.name)
        self.desc_input.setPlainText(self.template.description or "")

        # Set Item
        idx = self.item_combo.findData(self.template.item_id)
        if idx >= 0:
            self.item_combo.setCurrentIndex(idx)

        # Load Criteria
        self.criteria_list = [
            {
                "name": c.name,
                "criteria_type": (
                    c.criteria_type.value
                    if hasattr(c.criteria_type, "value")
                    else c.criteria_type
                ),
                "tolerance_min": c.tolerance_min,
                "tolerance_max": c.tolerance_max,
                "unit": c.unit,
                "is_required": c.is_required,
            }
            for c in self.template.criteria
        ]
        self.refresh_table()

    def add_criteria(self):
        dialog = CriteriaDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.criteria_list.append(data)
            self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(len(self.criteria_list))
        for row, data in enumerate(self.criteria_list):
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(data["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(data["criteria_type"])))

            tol = f"{data['tolerance_min']} - {data['tolerance_max']}"
            self.table.setItem(row, 3, QTableWidgetItem(tol))
            self.table.setItem(row, 4, QTableWidgetItem(data["unit"]))

    def save(self):
        data = {
            "code": self.code_input.text(),
            "name": self.name_input.text(),
            "description": self.desc_input.toPlainText(),
            "inspection_type": self.type_combo.currentText(),
            "item_id": self.item_combo.currentData(),
        }

        if not data["code"] or not data["name"]:
            QMessageBox.warning(self, "Hata", "Kod ve Ad zorunludur!")
            return

        try:
            if self.template:
                # Update logic (skipped for brevity, focusing on new)
                pass
            else:
                tmpl = self.service.create_template(data)
                self.service.add_criteria_to_template(tmpl.id, self.criteria_list)
                self.saved.emit(tmpl)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
