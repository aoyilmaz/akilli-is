"""
Akıllı İş - Müşteri Şikayeti Modülü
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
    SUCCESS,
    get_button_style,
    get_title_style,
)
from modules.quality.services import QualityService
from database.models.quality import (
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
)

CATEGORY_LABELS = {
    ComplaintCategory.QUALITY: "Kalite",
    ComplaintCategory.DELIVERY: "Teslimat",
    ComplaintCategory.SERVICE: "Servis",
    ComplaintCategory.DOCUMENTATION: "Dokümantasyon",
    ComplaintCategory.OTHER: "Diğer",
}

PRIORITY_LABELS = {
    ComplaintPriority.LOW: "Düşük",
    ComplaintPriority.MEDIUM: "Orta",
    ComplaintPriority.HIGH: "Yüksek",
    ComplaintPriority.CRITICAL: "Kritik",
}

STATUS_LABELS = {
    ComplaintStatus.OPEN: "Açık",
    ComplaintStatus.INVESTIGATION: "İnceleme",
    ComplaintStatus.RESOLUTION: "Çözüm",
    ComplaintStatus.CLOSED: "Kapalı",
}

class ComplaintFormDialog(QDialog):
    """Yeni şikayet dialogu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = QualityService()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Yeni Müşteri Şikayeti")
        self.setMinimumSize(450, 400)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.category = QComboBox()
        for c, label in CATEGORY_LABELS.items():
            self.category.addItem(label, c)
        form.addRow("Kategori:", self.category)

        self.priority = QComboBox()
        for p, label in PRIORITY_LABELS.items():
            self.priority.addItem(label, p)
        self.priority.setCurrentIndex(1)  # Orta
        form.addRow("Öncelik:", self.priority)

        self.product_info = QLineEdit()
        form.addRow("Ürün Bilgisi:", self.product_info)

        self.lot_no = QLineEdit()
        form.addRow("Parti No:", self.lot_no)

        self.description = QTextEdit()
        self.description.setMaximumHeight(100)
        form.addRow("Şikayet Açıklaması:", self.description)

        self.immediate_action = QTextEdit()
        self.immediate_action.setMaximumHeight(80)
        form.addRow("Acil Aksiyon:", self.immediate_action)

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
            QMessageBox.warning(self, "Uyarı", "Şikayet açıklaması zorunludur.")

        try:
            data = {
                "category": self.category.currentData(),
                "priority": self.priority.currentData(),
                "product_info": self.product_info.text().strip() or None,
                "lot_no": self.lot_no.text().strip() or None,
                "description": self.description.toPlainText().strip(),
                "immediate_action": self.immediate_action.toPlainText().strip() or None,
            }
            self.service.create_complaint(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)

class ComplaintModule(QWidget):
    """Müşteri şikayetleri modülü"""

    page_title = "Müşteri Şikayetleri"

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
        title = QLabel("Müşteri Şikayetleri")
        header.addWidget(title)
        header.addStretch()

        new_btn = QPushButton("Yeni Şikayet")
        new_btn.setProperty("class", "primary")
        new_btn.clicked.connect(self._new_complaint)
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
            ["Şikayet No", "Kategori", "Öncelik", "Açıklama", "Durum", "Tarih"]
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
            complaints = service.get_all_complaints(status=status)

            self.table.setRowCount(len(complaints))
            for row, c in enumerate(complaints):
                self.table.setItem(row, 0, QTableWidgetItem(c.complaint_no))
                self.table.setItem(
                    row, 1, QTableWidgetItem(CATEGORY_LABELS.get(c.category, "-"))
                )

                pri_text = PRIORITY_LABELS.get(c.priority, "-")
                pri_item = QTableWidgetItem(pri_text)
                if c.priority == ComplaintPriority.CRITICAL:
                    pri_item.setForeground(Qt.GlobalColor.red)
                elif c.priority == ComplaintPriority.HIGH:
                    pri_item.setForeground(Qt.GlobalColor.yellow)
                self.table.setItem(row, 2, pri_item)

                desc = (
                    c.description[:40] + "..."
                    if len(c.description) > 40
                    else c.description
                )
                self.table.setItem(row, 3, QTableWidgetItem(desc))

                status_text = STATUS_LABELS.get(c.status, "-")
                status_item = QTableWidgetItem(status_text)
                if c.status == ComplaintStatus.CLOSED:
                    status_item.setForeground(Qt.GlobalColor.green)
                self.table.setItem(row, 4, status_item)

                self.table.setItem(
                    row,
                    5,
                    QTableWidgetItem(
                        c.complaint_date.strftime("%d.%m.%Y")
                        if c.complaint_date
                        else "-"
                    ),
                )

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Hata: {str(e)}")
        finally:
            self._close_service()

    def _new_complaint(self):
        dialog = ComplaintFormDialog(parent=self)
        if dialog.exec():
            self.load_data()
