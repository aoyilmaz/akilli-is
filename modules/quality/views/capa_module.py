"""
Akıllı İş - CAPA Modülü
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
    QTextEdit,
    QDateEdit,
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
from database.models.quality import CAPAType, CAPASource, CAPAStatus

TYPE_LABELS = {
    CAPAType.CORRECTIVE: "Düzeltici",
    CAPAType.PREVENTIVE: "Önleyici",
}

SOURCE_LABELS = {
    CAPASource.NCR: "NCR",
    CAPASource.AUDIT: "Denetim",
    CAPASource.CUSTOMER_COMPLAINT: "Müşteri Şikayeti",
    CAPASource.INTERNAL: "İç Kaynak",
}

STATUS_LABELS = {
    CAPAStatus.OPEN: "Açık",
    CAPAStatus.IN_PROGRESS: "Devam Ediyor",
    CAPAStatus.VERIFICATION: "Doğrulama",
    CAPAStatus.CLOSED: "Kapalı",
}

class CAPAFormDialog(QDialog):
    """Yeni CAPA dialogu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = QualityService()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Yeni CAPA")
        self.setMinimumSize(450, 400)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.capa_type = QComboBox()
        for t, label in TYPE_LABELS.items():
            self.capa_type.addItem(label, t)
        form.addRow("CAPA Türü:", self.capa_type)

        self.source = QComboBox()
        for s, label in SOURCE_LABELS.items():
            self.source.addItem(label, s)
        self.source.setCurrentIndex(3)  # İç Kaynak
        form.addRow("Kaynak:", self.source)

        self.description = QTextEdit()
        self.description.setMaximumHeight(100)
        form.addRow("Açıklama:", self.description)

        self.action_plan = QTextEdit()
        self.action_plan.setMaximumHeight(80)
        form.addRow("Aksiyon Planı:", self.action_plan)

        self.target_date = QDateEdit()
        self.target_date.setCalendarPopup(True)
        self.target_date.setDate(QDate.currentDate().addDays(30))
        form.addRow("Hedef Tarih:", self.target_date)

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
        if not self.description.toPlainText().strip():
            QMessageBox.warning(self, "Uyarı", "Açıklama zorunludur.")

        try:
            data = {
                "capa_type": self.capa_type.currentData(),
                "source": self.source.currentData(),
                "description": self.description.toPlainText().strip(),
                "action_plan": self.action_plan.toPlainText().strip() or None,
                "target_date": self.target_date.date().toPyDate(),
            }
            self.service.create_capa(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)

class CAPAModule(QWidget):
    """CAPA yönetim modülü"""

    page_title = "CAPA"

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
        title = QLabel("Düzeltici/Önleyici Faaliyetler (CAPA)")
        header.addWidget(title)
        header.addStretch()

        new_btn = QPushButton("Yeni CAPA")
        new_btn.setProperty("class", "primary")
        new_btn.clicked.connect(self._new_capa)
        header.addWidget(new_btn)

        layout.addLayout(header)

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
            ["CAPA No", "Tür", "Kaynak", "Açıklama", "Hedef", "Durum"]
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
            capas = service.get_all_capas(status=status)

            self.table.setRowCount(len(capas))
            for row, capa in enumerate(capas):
                self.table.setItem(row, 0, QTableWidgetItem(capa.capa_no))
                self.table.setItem(
                    row, 1, QTableWidgetItem(TYPE_LABELS.get(capa.capa_type, "-"))
                )
                self.table.setItem(
                    row, 2, QTableWidgetItem(SOURCE_LABELS.get(capa.source, "-"))
                )

                desc = (
                    capa.description[:40] + "..."
                    if len(capa.description) > 40
                    else capa.description
                )
                self.table.setItem(row, 3, QTableWidgetItem(desc))

                self.table.setItem(
                    row,
                    4,
                    QTableWidgetItem(
                        capa.target_date.strftime("%d.%m.%Y")
                        if capa.target_date
                        else "-"
                    ),
                )

                status_text = STATUS_LABELS.get(capa.status, "-")
                status_item = QTableWidgetItem(status_text)
                if capa.status == CAPAStatus.CLOSED:
                    status_item.setForeground(Qt.GlobalColor.green)
                self.table.setItem(row, 5, status_item)

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Hata: {str(e)}")
        finally:
            self._close_service()

    def _new_capa(self):
        dialog = CAPAFormDialog(parent=self)
        if dialog.exec():
            self.load_data()
