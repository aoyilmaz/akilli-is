from datetime import date
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDialogButtonBox,
    QDateEdit,
    QSpinBox,
    QMessageBox,
    QTextEdit,
)
from PyQt6.QtCore import QDate
from ui.components.input_fields import CurrencyInput
from database.models.fixed_asset import AssetCategory, AssetStatus, DepreciationMethod


class FixedAssetDialog(QDialog):
    def __init__(self, parent=None, asset_data=None):
        super().__init__(parent)
        self.asset_data = asset_data
        self.setWindowTitle(
            "Sabit Kıymet Kartı" if not asset_data else "Sabit Kıymet Düzenle"
        )
        self.setMinimumWidth(450)
        self.setup_ui()
        if asset_data:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Adı
        self.name_input = QLineEdit()
        form.addRow("Demirbaş Adı:", self.name_input)

        # Kategori
        self.category_input = QComboBox()
        for cat in AssetCategory:
            self.category_input.addItem(cat.value, cat)  # Store enum as userdata
        form.addRow("Kategori:", self.category_input)

        # Durum
        self.status_input = QComboBox()
        for status in AssetStatus:
            self.status_input.addItem(status.value, status)
        form.addRow("Durum:", self.status_input)

        # Alım Tarihi
        self.purchase_date_input = QDateEdit()
        self.purchase_date_input.setCalendarPopup(True)
        self.purchase_date_input.setDate(QDate.currentDate())
        form.addRow("Alım Tarihi:", self.purchase_date_input)

        # Alış Fiyatı
        self.price_input = CurrencyInput()
        form.addRow("Alış Fiyatı:", self.price_input)

        # Amortisman Yöntemi
        self.method_input = QComboBox()
        for method in DepreciationMethod:
            self.method_input.addItem(method.value, method)
        form.addRow("Amortisman Yöntemi:", self.method_input)

        # Faydalı Ömür
        self.life_input = QSpinBox()
        self.life_input.setRange(0, 100)
        self.life_input.setValue(5)
        self.life_input.setSuffix(" Yıl")
        form.addRow("Faydalı Ömür:", self.life_input)

        # Hurda Değeri
        self.salvage_input = CurrencyInput()
        form.addRow("Hurda Değeri:", self.salvage_input)

        # Açıklama
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(60)
        form.addRow("Açıklama:", self.description_input)

        layout.addLayout(form)

        # Butonlar
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_data(self):
        """Mevcut veriyi yükle"""
        data = self.asset_data
        self.name_input.setText(data.get("name", ""))
        self.description_input.setText(data.get("description") or "")

        # Set Combos
        self._set_combo(self.category_input, data.get("category"))
        self._set_combo(self.status_input, data.get("status"))
        self._set_combo(self.method_input, data.get("depreciation_method"))

        # Set Date
        p_date = data.get("purchase_date")
        if p_date:
            if isinstance(p_date, str):
                try:
                    qdate = QDate.fromString(p_date, "yyyy-MM-dd")  # ISO might differ
                    if not qdate.isValid():
                        from datetime import datetime

                        d = datetime.fromisoformat(p_date)
                        qdate = QDate(d.year, d.month, d.day)
                    self.purchase_date_input.setDate(qdate)
                except:
                    pass
            elif hasattr(p_date, "year"):
                self.purchase_date_input.setDate(
                    QDate(p_date.year, p_date.month, p_date.day)
                )

        # Set Numbers
        self.price_input.setValue(float(data.get("purchase_price") or 0))
        self.salvage_input.setValue(float(data.get("salvage_value") or 0))
        self.life_input.setValue(int(data.get("useful_life_years") or 5))

    def _set_combo(self, combo, value):
        if not value:
            return
        # Value might be enum or string
        val_str = value.value if hasattr(value, "value") else str(value)
        # However, userData stores the Enum member
        idx = combo.findData(value)
        if idx == -1:
            # Try matching by text if data fails
            idx = combo.findText(val_str)
        if idx != -1:
            combo.setCurrentIndex(idx)

    def get_data(self):
        """Form verisini döndür"""
        # Validate properties
        if not self.name_input.text():
            QMessageBox.warning(self, "Hata", "Lütfen demirbaş adını giriniz.")
            return None

        return {
            "name": self.name_input.text(),
            "description": self.description_input.toPlainText(),
            "category": self.category_input.currentData(),
            "status": self.status_input.currentData(),
            "purchase_date": self.purchase_date_input.date().toPyDate(),
            "purchase_price": self.price_input.value(),
            "currency": "TRY",  # Default for now
            "depreciation_method": self.method_input.currentData(),
            "useful_life_years": self.life_input.value(),
            "salvage_value": self.salvage_input.value(),
            # Initial current value same as purchase price for new assets
            "current_value": (
                self.price_input.value()
                if not self.asset_data
                else self.asset_data.get("current_value")
            ),
        }

    def accept(self):
        # Validate data before closing
        data = self.get_data()
        if data:
            self._result_data = data
            super().accept()
        else:
            # Validation failed, don't close
            pass

    def get_result(self):
        return getattr(self, "_result_data", None)
