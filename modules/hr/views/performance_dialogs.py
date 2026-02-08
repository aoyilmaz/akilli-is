"""
Performans Yönetimi Diyalogları
"""

from datetime import date
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QDialogButtonBox,
    QMessageBox,
    QTextEdit,
    QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, QDate

from database.models.performance import (
    EvaluationPeriodType,
    CompetencyCategory,
)


class EvaluationPeriodDialog(QDialog):
    """Değerlendirme Dönemi Ekleme/Düzenleme Diyaloğu"""

    def __init__(self, parent=None, period=None):
        super().__init__(parent)
        self.period = period
        self.setWindowTitle("Dönem Tanımla" if not period else "Dönemi Düzenle")
        self.setModal(True)
        self.resize(400, 350)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Örn: 2026 Yıllık Değerlendirme")
        form.addRow("Dönem Adı:", self.name_input)

        self.type_combo = QComboBox()
        for t in EvaluationPeriodType:
            self.type_combo.addItem(t.value, t)
        form.addRow("Dönem Türü:", self.type_combo)

        # Tarihler
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        form.addRow("Dönem Başlangıcı:", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addDays(365))
        form.addRow("Dönem Bitişi:", self.end_date)

        self.eval_start = QDateEdit()
        self.eval_start.setCalendarPopup(True)
        self.eval_start.setDate(QDate.currentDate())
        form.addRow("Değerlendirme Baş.:", self.eval_start)

        self.eval_end = QDateEdit()
        self.eval_end.setCalendarPopup(True)
        self.eval_end.setDate(QDate.currentDate().addDays(30))
        form.addRow("Değerlendirme Bit.:", self.eval_end)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Açıklama...")
        self.desc_input.setMaximumHeight(60)
        form.addRow("Açıklama:", self.desc_input)

        layout.addLayout(form)

        # Butonlar
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        if self.period:
            self.load_data()

    def load_data(self):
        self.name_input.setText(self.period.name)
        index = self.type_combo.findData(self.period.period_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        self.start_date.setDate(self.period.start_date)
        self.end_date.setDate(self.period.end_date)

        if self.period.evaluation_start:
            self.eval_start.setDate(self.period.evaluation_start)
        if self.period.evaluation_end:
            self.eval_end.setDate(self.period.evaluation_end)

        self.desc_input.setText(self.period.description or "")

    def validate_and_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Hata", "Dönem adı boş olamaz.")
            return

        if self.start_date.date() > self.end_date.date():
            QMessageBox.warning(
                self, "Hata", "Başlangıç tarihi bitiş tarihinden sonra olamaz."
            )
            return

        self.accept()

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "period_type": self.type_combo.currentData(),
            "start_date": self.start_date.date().toPyDate(),
            "end_date": self.end_date.date().toPyDate(),
            "evaluation_start": self.eval_start.date().toPyDate(),
            "evaluation_end": self.eval_end.date().toPyDate(),
            "description": self.desc_input.toPlainText().strip(),
        }


class CompetencyDialog(QDialog):
    """Yetkinlik Ekleme/Düzenleme Diyaloğu"""

    def __init__(self, parent=None, competency=None):
        super().__init__(parent)
        self.competency = competency
        self.setWindowTitle(
            "Yetkinlik Tanımla" if not competency else "Yetkinliği Düzenle"
        )
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Örn: Problem Çözme")
        form.addRow("Yetkinlik Adı:", self.name_input)

        self.category_combo = QComboBox()
        for c in CompetencyCategory:
            self.category_combo.addItem(c.value, c)
        form.addRow("Kategori:", self.category_combo)

        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(0.1, 10.0)
        self.weight_spin.setSingleStep(0.1)
        self.weight_spin.setValue(1.0)
        form.addRow("Ağırlık:", self.weight_spin)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Yetkinlik açıklaması ve beklentiler...")
        form.addRow("Açıklama:", self.desc_input)

        layout.addLayout(form)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        if self.competency:
            self.load_data()

    def load_data(self):
        self.name_input.setText(self.competency.name)
        index = self.category_combo.findData(self.competency.category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)

        self.weight_spin.setValue(float(self.competency.weight))
        self.desc_input.setText(self.competency.description or "")

    def validate_and_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Hata", "Yetkinlik adı boş olamaz.")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "category": self.category_combo.currentData(),
            "weight": self.weight_spin.value(),
            "description": self.desc_input.toPlainText().strip(),
        }
