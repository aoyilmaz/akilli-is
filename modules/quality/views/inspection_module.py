"""
Akıllı İş - Kalite Kontrol Modülü
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
    QDateEdit,
    QTextEdit,
)
from PyQt6.QtCore import Qt, QDate

from config.styles import (
    BG_SECONDARY,
    BORDER,
    TEXT_PRIMARY,
    ACCENT,
    get_button_style,
    get_title_style,
)
from modules.quality.services import QualityService
from database.models.quality import InspectionStatus

STATUS_LABELS = {
    InspectionStatus.PENDING: "Beklemede",
    InspectionStatus.PASSED: "Geçti",
    InspectionStatus.FAILED: "Kaldı",
    InspectionStatus.CONDITIONAL: "Şartlı",
}

class InspectionFormDialog(QDialog):
    """Yeni kontrol dialogu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = QualityService()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Yeni Kalite Kontrol")
        self.setMinimumSize(450, 400)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.template = QComboBox()
        self.template.addItem("Şablon Seçiniz...", None)
        for t in self.service.get_all_templates():
            self.template.addItem(f"{t.code} - {t.name}", t.id)
        form.addRow("Kontrol Şablonu:", self.template)

        self.lot_no = QLineEdit()
        form.addRow("Parti No:", self.lot_no)

        self.quantity = QLineEdit()
        self.quantity.setPlaceholderText("0")
        form.addRow("Miktar:", self.quantity)

        self.sample_size = QLineEdit()
        self.sample_size.setPlaceholderText("0")
        form.addRow("Numune:", self.sample_size)

        self.inspection_date = QDateEdit()
        self.inspection_date.setCalendarPopup(True)
        self.inspection_date.setDate(QDate.currentDate())
        form.addRow("Kontrol Tarihi:", self.inspection_date)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        form.addRow("Notlar:", self.notes)

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
        try:
            data = {
                "template_id": self.template.currentData(),
                "lot_no": self.lot_no.text().strip() or None,
                "inspection_date": self.inspection_date.date().toPyDate(),
            }

            if self.quantity.text().strip():
                data["quantity"] = float(self.quantity.text())
            if self.sample_size.text().strip():
                data["sample_size"] = float(self.sample_size.text())

            self.service.create_inspection(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)

class InspectionModule(QWidget):
    """Kalite kontrol modülü"""

    page_title = "Kalite Kontroller"

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
        title = QLabel("Kalite Kontrol Listesi")
        header.addWidget(title)
        header.addStretch()

        new_btn = QPushButton("Yeni Kontrol")
        new_btn.setProperty("class", "primary")
        new_btn.clicked.connect(self._new_inspection)
        header.addWidget(new_btn)

        layout.addLayout(header)

        # Filtre
        filter_row = QHBoxLayout()
        self.status_combo = QComboBox()
        self.status_combo.setFixedWidth(150)
        self.status_combo.addItem("Tüm Durumlar", None)
        for s, label in STATUS_LABELS.items():
            self.status_combo.addItem(label, s)
        self.status_combo.currentIndexChanged.connect(self.load_data)
        filter_row.addWidget(self.status_combo)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Kontrol No", "Şablon", "Parti No", "Tarih", "Miktar", "Durum"]
        )
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
            status = self.status_combo.currentData()
            inspections = service.get_all_inspections(status=status)

            self.table.setRowCount(len(inspections))
            for row, ins in enumerate(inspections):
                self.table.setItem(row, 0, QTableWidgetItem(ins.inspection_no))
                self.table.setItem(
                    row, 1, QTableWidgetItem(ins.template.name if ins.template else "-")
                )
                self.table.setItem(row, 2, QTableWidgetItem(ins.lot_no or "-"))
                self.table.setItem(
                    row,
                    3,
                    QTableWidgetItem(
                        ins.inspection_date.strftime("%d.%m.%Y")
                        if ins.inspection_date
                        else "-"
                    ),
                )
                self.table.setItem(
                    row, 4, QTableWidgetItem(str(ins.quantity) if ins.quantity else "-")
                )

                status_text = STATUS_LABELS.get(ins.status, "-")
                status_item = QTableWidgetItem(status_text)
                if ins.status == InspectionStatus.PASSED:
                    status_item.setForeground(Qt.GlobalColor.green)
                elif ins.status == InspectionStatus.FAILED:
                    status_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, 5, status_item)

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Hata: {str(e)}")
        finally:
            self._close_service()

    def _new_inspection(self):
        dialog = InspectionFormDialog(parent=self)
        if dialog.exec():
            self.load_data()
