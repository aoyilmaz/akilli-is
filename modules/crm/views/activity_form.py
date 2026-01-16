from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDateTimeEdit,
    QTextEdit,
    QCheckBox,
    QPushButton,
    QLabel,
    QGroupBox,
    QScrollArea,
    QMessageBox,
)
from PyQt6.QtCore import pyqtSignal, QDateTime
from database.models.crm import ActivityType
from modules.development import ErrorHandler


class ActivityFormPage(QWidget):
    """Aktivite Ekleme/Düzenleme Formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(self, data=None):
        super().__init__()
        self.data = data or {}
        self.setup_ui()
        if self.data:
            self.load_form_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Başlık ve Butonlar
        header_layout = QHBoxLayout()
        title = "Aktivite Düzenle" if self.data else "Yeni Aktivite"
        header_label = QLabel(title)
        header_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #cccccc;"
        )
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        self.btn_cancel = QPushButton("İptal")
        self.btn_cancel.clicked.connect(self.cancelled.emit)

        self.btn_save = QPushButton("Kaydet")
        self.btn_save.setStyleSheet("background-color: #007acc; color: white;")
        self.btn_save.clicked.connect(self._on_save)

        header_layout.addWidget(self.btn_cancel)
        header_layout.addWidget(self.btn_save)
        layout.addLayout(header_layout)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        self.form_layout = QVBoxLayout(content)

        # --- Temel Bilgiler ---
        group_basic = QGroupBox("Aktivite Detayları")
        form_basic = QFormLayout(group_basic)

        self.inp_subject = QLineEdit()
        self.inp_subject.setPlaceholderText("Konu (Örn: Tanışma Toplantısı)")
        form_basic.addRow("Konu:", self.inp_subject)

        # Type
        self.combo_type = QComboBox()
        for act_type in ActivityType:
            self.combo_type.addItem(act_type.value, act_type.name)
        form_basic.addRow("Tip:", self.combo_type)

        # Date
        self.inp_due_date = QDateTimeEdit()
        self.inp_due_date.setDateTime(
            QDateTime.currentDateTime().addSecs(3600)
        )  # +1 hour default
        self.inp_due_date.setCalendarPopup(True)
        form_basic.addRow("Tarih/Saat:", self.inp_due_date)

        self.form_layout.addWidget(group_basic)

        # --- İlişki ---
        group_relation = QGroupBox("İlişkili Kayıt")
        form_relation = QFormLayout(group_relation)

        self.combo_lead = QComboBox()
        self.combo_lead.addItem("Seçiniz...", None)
        form_relation.addRow("Aday Müşteri:", self.combo_lead)

        # Opportunity selection could be added here later

        self.form_layout.addWidget(group_relation)

        # --- Durum ve Notlar ---
        group_status = QGroupBox("Durum ve Sonuç")
        form_status = QFormLayout(group_status)

        self.chk_completed = QCheckBox("Tamamlandı")
        form_status.addRow("Durum:", self.chk_completed)

        self.inp_description = QTextEdit()
        self.inp_description.setPlaceholderText("Açıklama...")
        self.inp_description.setMaximumHeight(80)
        form_status.addRow("Açıklama:", self.inp_description)

        self.inp_result = QTextEdit()
        self.inp_result.setPlaceholderText("Sonuç notları (Tamamlandıysa)...")
        self.inp_result.setMaximumHeight(80)
        form_status.addRow("Sonuç:", self.inp_result)

        self.form_layout.addWidget(group_status)
        self.form_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def load_form_data(self):
        try:
            self.inp_subject.setText(self.data.get("subject", ""))

            type_name = self.data.get("activity_type_name")
            if type_name:
                idx = self.combo_type.findData(type_name)
                if idx >= 0:
                    self.combo_type.setCurrentIndex(idx)

            due_date = self.data.get("due_date")
            if due_date:
                # due_date string ISO format assumed
                qdt = QDateTime.fromString(str(due_date)[:19], "yyyy-MM-ddTHH:mm:ss")
                self.inp_due_date.setDateTime(qdt)

            self.chk_completed.setChecked(self.data.get("is_completed", False))
            self.inp_description.setText(self.data.get("description", ""))
            self.inp_result.setText(self.data.get("result", ""))

            # Lead selection handled by controller

        except Exception as e:
            ErrorHandler.log_error(e, "ActivityFormPage.load_form_data")

    def _on_save(self):
        if not self.inp_subject.text().strip():
            QMessageBox.warning(self, "Hata", "Konu alanı zorunludur.")
            return

        form_data = {
            "id": self.data.get("id"),
            "subject": self.inp_subject.text().strip(),
            "activity_type": self.combo_type.currentData(),  # Enum Name
            "due_date": self.inp_due_date.dateTime().toPyDateTime(),
            "is_completed": self.chk_completed.isChecked(),
            "description": self.inp_description.toPlainText(),
            "result": self.inp_result.toPlainText(),
            "lead_id": self.combo_lead.currentData(),
        }

        if self.chk_completed.isChecked() and not self.data.get("completed_at"):
            # Eğer yeni tamamlandıysa, şu anı completed_at yapabiliriz.
            # Service tarafında halledilmesi daha iyi, ama burada da gönderebiliriz.
            pass

        self.saved.emit(form_data)
