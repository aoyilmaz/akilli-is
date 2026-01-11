"""
Akıllı İş - Kontrol Şablonu Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QMessageBox,
    QLabel,
    QDialog,
    QFormLayout,
    QLineEdit,
    QTextEdit,
)
from PyQt6.QtCore import Qt

from config.styles import (
    BG_SECONDARY,
    BORDER,
    TEXT_PRIMARY,
    ACCENT,
    get_button_style,
    get_title_style,
)
from modules.quality.services import QualityService
from database.models.quality import InspectionType

TYPE_LABELS = {
    InspectionType.INCOMING: "Giriş Kontrolü",
    InspectionType.IN_PROCESS: "Proses Kontrolü",
    InspectionType.FINAL: "Final Kontrol",
    InspectionType.PERIODIC: "Periyodik Kontrol",
}

class TemplateFormDialog(QDialog):
    """Yeni şablon dialogu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = QualityService()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Yeni Kontrol Şablonu")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.code = QLineEdit()
        form.addRow("Kod:", self.code)

        self.name = QLineEdit()
        form.addRow("Ad:", self.name)

        self.inspection_type = QComboBox()
        for t, label in TYPE_LABELS.items():
            self.inspection_type.addItem(label, t)
        form.addRow("Kontrol Türü:", self.inspection_type)

        self.description = QTextEdit()
        self.description.setMaximumHeight(80)
        form.addRow("Açıklama:", self.description)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def save(self):
        if not self.code.text().strip():
            QMessageBox.warning(self, "Uyarı", "Kod zorunludur.")
        if not self.name.text().strip():
            QMessageBox.warning(self, "Uyarı", "Ad zorunludur.")

        try:
            data = {
                "code": self.code.text().strip(),
                "name": self.name.text().strip(),
                "inspection_type": self.inspection_type.currentData(),
                "description": self.description.toPlainText().strip() or None,
            }
            self.service.create_template(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)

class TemplateModule(QWidget):
    """Kontrol şablonu modülü"""

    page_title = "Kontrol Şablonları"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Kontrol Şablonları")
        header.addWidget(title)
        header.addStretch()

        new_btn = QPushButton("Yeni Şablon")
        new_btn.setProperty("class", "primary")
        new_btn.clicked.connect(self._new_template)
        header.addWidget(new_btn)

        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Kod", "Ad", "Tür", "Açıklama"])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def _get_service(self):
        if self.service is None:
            self.service = QualityService()
        return self.service

    def _close_service(self):
        if self.service:
            self.service.close()
            self.service = None

    def load_data(self):
        try:
            service = self._get_service()
            templates = service.get_all_templates()

            self.table.setRowCount(len(templates))
            for row, t in enumerate(templates):
                self.table.setItem(row, 0, QTableWidgetItem(t.code))
                self.table.setItem(row, 1, QTableWidgetItem(t.name))
                self.table.setItem(
                    row, 2, QTableWidgetItem(TYPE_LABELS.get(t.inspection_type, "-"))
                )
                self.table.setItem(row, 3, QTableWidgetItem(t.description or "-"))

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Hata: {str(e)}")
        finally:
            self._close_service()

    def _new_template(self):
        dialog = TemplateFormDialog(parent=self)
        if dialog.exec():
            self.load_data()
