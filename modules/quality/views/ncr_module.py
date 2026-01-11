"""
Akıllı İş - Uygunsuzluk (NCR) Modülü
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
from database.models.quality import NCRSeverity, NCRStatus

SEVERITY_LABELS = {
    NCRSeverity.MINOR: "Küçük",
    NCRSeverity.MAJOR: "Büyük",
    NCRSeverity.CRITICAL: "Kritik",
}

STATUS_LABELS = {
    NCRStatus.OPEN: "Açık",
    NCRStatus.ANALYSIS: "Analiz",
    NCRStatus.ACTION: "Aksiyon",
    NCRStatus.VERIFICATION: "Doğrulama",
    NCRStatus.CLOSED: "Kapalı",
}

class NCRFormDialog(QDialog):
    """Yeni NCR dialogu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = QualityService()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Yeni Uygunsuzluk Kaydı")
        self.setMinimumSize(450, 350)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.severity = QComboBox()
        for s, label in SEVERITY_LABELS.items():
            self.severity.addItem(label, s)
        form.addRow("Şiddet:", self.severity)

        self.description = QTextEdit()
        self.description.setMaximumHeight(100)
        form.addRow("Açıklama:", self.description)

        self.root_cause = QTextEdit()
        self.root_cause.setMaximumHeight(80)
        form.addRow("Kök Neden:", self.root_cause)

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
                "severity": self.severity.currentData(),
                "description": self.description.toPlainText().strip(),
                "root_cause": self.root_cause.toPlainText().strip() or None,
            }
            self.service.create_ncr(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)

class NCRModule(QWidget):
    """NCR yönetim modülü"""

    page_title = "Uygunsuzluklar"

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
        title = QLabel("Uygunsuzluk Kayıtları (NCR)")
        header.addWidget(title)
        header.addStretch()

        new_btn = QPushButton("Yeni NCR")
        new_btn.setProperty("class", "primary")
        new_btn.clicked.connect(self._new_ncr)
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
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["NCR No", "Şiddet", "Açıklama", "Durum", "Tarih"]
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
            ncrs = service.get_all_ncrs(status=status)

            self.table.setRowCount(len(ncrs))
            for row, ncr in enumerate(ncrs):
                self.table.setItem(row, 0, QTableWidgetItem(ncr.ncr_no))

                sev_text = SEVERITY_LABELS.get(ncr.severity, "-")
                sev_item = QTableWidgetItem(sev_text)
                if ncr.severity == NCRSeverity.CRITICAL:
                    sev_item.setForeground(Qt.GlobalColor.red)
                elif ncr.severity == NCRSeverity.MAJOR:
                    sev_item.setForeground(Qt.GlobalColor.yellow)
                self.table.setItem(row, 1, sev_item)

                desc = (
                    ncr.description[:50] + "..."
                    if len(ncr.description) > 50
                    else ncr.description
                )
                self.table.setItem(row, 2, QTableWidgetItem(desc))
                self.table.setItem(
                    row, 3, QTableWidgetItem(STATUS_LABELS.get(ncr.status, "-"))
                )
                self.table.setItem(
                    row,
                    4,
                    QTableWidgetItem(
                        ncr.created_at.strftime("%d.%m.%Y") if ncr.created_at else "-"
                    ),
                )

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Hata: {str(e)}")
        finally:
            self._close_service()

    def _new_ncr(self):
        dialog = NCRFormDialog(parent=self)
        if dialog.exec():
            self.load_data()
