from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QSpinBox,
    QTextEdit,
    QPushButton,
    QLabel,
    QGroupBox,
    QScrollArea,
    QMessageBox,
)
from PyQt6.QtCore import pyqtSignal, QDate, Qt
from database.models.crm import OpportunityStage, Lead
from modules.development import ErrorHandler


class OpportunityFormPage(QWidget):
    """Fırsat Ekleme/Düzenleme Formu"""

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
        title = "Fırsat Düzenle" if self.data else "Yeni Fırsat"
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
        group_basic = QGroupBox("Temel Bilgiler")
        form_basic = QFormLayout(group_basic)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Fırsat Adı (Örn: XYZ Yazılım Projesi)")
        form_basic.addRow("Fırsat Adı:", self.inp_name)

        # Stage (Aşama)
        self.combo_stage = QComboBox()
        for stage in OpportunityStage:
            self.combo_stage.addItem(
                stage.value, stage.name
            )  # Display value, Userdata name
        form_basic.addRow("Aşama:", self.combo_stage)

        self.form_layout.addWidget(group_basic)

        # --- Finansal Bilgiler ---
        group_finance = QGroupBox("Finansal Detaylar")
        form_finance = QFormLayout(group_finance)

        self.inp_revenue = QDoubleSpinBox()
        self.inp_revenue.setRange(0, 1000000000)
        self.inp_revenue.setPrefix("₺")
        form_finance.addRow("Beklenen Gelir:", self.inp_revenue)

        self.inp_probability = QSpinBox()
        self.inp_probability.setRange(0, 100)
        self.inp_probability.setSuffix("%")
        form_finance.addRow("Olasılık:", self.inp_probability)

        self.inp_closing_date = QDateEdit()
        self.inp_closing_date.setDate(QDate.currentDate().addDays(30))
        self.inp_closing_date.setCalendarPopup(True)
        form_finance.addRow("Tahmini Kapanış:", self.inp_closing_date)

        self.form_layout.addWidget(group_finance)

        # --- İlişkili Kişi/Kurum ---
        # Not: Basitlik için sadece combobox ile Lead seçimi yapıyoruz şimdilik.
        # Gerçek uygulamada search box olmalı.
        group_relation = QGroupBox("İlişkiler")
        form_relation = QFormLayout(group_relation)

        self.combo_lead = QComboBox()
        self.combo_lead.addItem("Seçiniz...", None)
        # Leads populated from outside or service?
        # For decoupled UI, usually controller passes list, but here we might need self-service access or pass it in init.
        # Let's keep it simple: Controller (Module) will populate this after creating the view.
        form_relation.addRow("Aday Müşteri:", self.combo_lead)

        self.form_layout.addWidget(group_relation)

        # --- Açıklama ve Notlar ---
        group_notes = QGroupBox("Açıklama & Sonraki Adım")
        form_notes = QFormLayout(group_notes)

        self.inp_next_step = QLineEdit()
        self.inp_next_step.setPlaceholderText("Örn: Telefonla arayıp teklifi sor")
        form_notes.addRow("Sonraki Adım:", self.inp_next_step)

        self.inp_description = QTextEdit()
        self.inp_description.setPlaceholderText("Fırsat detayları...")
        self.inp_description.setMaximumHeight(100)
        form_notes.addRow("Açıklama:", self.inp_description)

        self.form_layout.addWidget(group_notes)
        self.form_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def load_form_data(self):
        """Mevcut veriyi form alanlarına doldur"""
        try:
            self.inp_name.setText(self.data.get("name", ""))

            stage_name = self.data.get("stage_name")  # Enum name expected
            if stage_name:
                idx = self.combo_stage.findData(stage_name)
                if idx >= 0:
                    self.combo_stage.setCurrentIndex(idx)

            self.inp_revenue.setValue(float(self.data.get("expected_revenue", 0)))
            self.inp_probability.setValue(int(self.data.get("probability", 0)))

            closing_date = self.data.get("closing_date")
            if closing_date:
                # closing_date string ISO format or date obj?
                # Assuming string 'YYYY-MM-DD' from to_dict()
                qdate = QDate.fromString(str(closing_date)[:10], "yyyy-MM-dd")
                self.inp_closing_date.setDate(qdate)

            self.inp_next_step.setText(self.data.get("next_step", ""))
            self.inp_description.setText(self.data.get("description", ""))

            # Lead selection requires the combo to be populated first.
            # We will handle lead selection setting in the controller (OpportunityModule)

        except Exception as e:
            ErrorHandler.log_error(e, "OpportunityFormPage.load_form_data")

    def _on_save(self):
        if not self.inp_name.text().strip():
            QMessageBox.warning(self, "Hata", "Fırsat adı zorunludur.")
            return

        form_data = {
            "id": self.data.get("id"),
            "name": self.inp_name.text().strip(),
            "stage": self.combo_stage.currentData(),
            "expected_revenue": self.inp_revenue.value(),
            "probability": self.inp_probability.value(),
            "closing_date": self.inp_closing_date.date().toPyDate(),
            "description": self.inp_description.toPlainText(),
            "next_step": self.inp_next_step.text().strip(),
            "lead_id": self.combo_lead.currentData(),
        }
        self.saved.emit(form_data)
