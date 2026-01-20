"""
Akıllı İş - Eğitim Takibi Modülü

Eğitim planlaması, katılım takibi ve sertifika yönetimi UI.
"""

from datetime import date

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
    QDialog,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QDateEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QDate

from config.styles import ICONS
from modules.hr.services import TrainingService
from database.models.training import TrainingType, TrainingStatus


class TrainingDialog(QDialog):
    """Eğitim ekleme/düzenleme dialogu"""

    def __init__(self, training_data: dict = None, parent=None):
        super().__init__(parent)
        self.training_data = training_data
        self.setWindowTitle("Eğitim Ekle" if not training_data else "Eğitim Düzenle")
        self.setMinimumWidth(450)
        self.setup_ui()
        if training_data:
            self.load_data()

    def setup_ui(self):
        layout = QFormLayout(self)

        # Eğitim adı
        self.name_edit = QLineEdit()
        layout.addRow("Eğitim Adı:", self.name_edit)

        # Tür
        self.type_combo = QComboBox()
        self.type_combo.addItem("İç Eğitim", TrainingType.INTERNAL)
        self.type_combo.addItem("Dış Eğitim", TrainingType.EXTERNAL)
        self.type_combo.addItem("Çevrimiçi", TrainingType.ONLINE)
        self.type_combo.addItem("İş Başı", TrainingType.ON_THE_JOB)
        self.type_combo.addItem("Sertifikalı", TrainingType.CERTIFICATION)
        layout.addRow("Eğitim Türü:", self.type_combo)

        # Süre
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.5, 1000)
        self.duration_spin.setValue(8)
        self.duration_spin.setSuffix(" saat")
        layout.addRow("Süre:", self.duration_spin)

        # Eğitmen
        self.trainer_edit = QLineEdit()
        layout.addRow("Eğitmen:", self.trainer_edit)

        # Maliyet
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0, 1000000)
        self.cost_spin.setSuffix(" ₺")
        layout.addRow("Maliyet:", self.cost_spin)

        # Sertifikalı mı
        self.has_cert_check = QCheckBox("Bu eğitim sertifikalıdır")
        layout.addRow("", self.has_cert_check)

        # Sertifika geçerlilik
        self.validity_spin = QSpinBox()
        self.validity_spin.setRange(0, 120)
        self.validity_spin.setSuffix(" ay")
        layout.addRow("Sertifika Geçerliliği:", self.validity_spin)

        # Açıklama
        self.description = QTextEdit()
        self.description.setMaximumHeight(80)
        layout.addRow("Açıklama:", self.description)

        # Butonlar
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(f"{ICONS['add']} Kaydet")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def load_data(self):
        if self.training_data:
            self.name_edit.setText(self.training_data.get("name", ""))

    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text(),
            "training_type": self.type_combo.currentData(),
            "duration_hours": self.duration_spin.value(),
            "trainer_name": self.trainer_edit.text(),
            "cost": self.cost_spin.value() if self.cost_spin.value() > 0 else None,
            "has_certificate": self.has_cert_check.isChecked(),
            "certificate_validity_months": (
                self.validity_spin.value() if self.has_cert_check.isChecked() else None
            ),
            "description": self.description.toPlainText(),
        }


class SessionDialog(QDialog):
    """Eğitim oturumu ekleme dialogu"""

    def __init__(self, trainings: list, parent=None):
        super().__init__(parent)
        self.trainings = trainings
        self.setWindowTitle("Oturum Planla")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        # Eğitim seçimi
        self.training_combo = QComboBox()
        for t in self.trainings:
            self.training_combo.addItem(t.name, t.id)
        layout.addRow("Eğitim:", self.training_combo)

        # Tarih
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate().addDays(7))
        layout.addRow("Planlanan Tarih:", self.date_edit)

        # Lokasyon
        self.location_edit = QLineEdit()
        layout.addRow("Lokasyon:", self.location_edit)

        # Çevrimiçi mi
        self.online_check = QCheckBox("Çevrimiçi eğitim")
        layout.addRow("", self.online_check)

        # Max katılımcı
        self.max_spin = QSpinBox()
        self.max_spin.setRange(0, 100)
        self.max_spin.setValue(20)
        layout.addRow("Maks. Katılımcı:", self.max_spin)

        # Butonlar
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(f"{ICONS['add']} Planla")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def get_data(self) -> dict:
        return {
            "training_id": self.training_combo.currentData(),
            "planned_date": self.date_edit.date().toPyDate(),
            "location": self.location_edit.text() or None,
            "is_online": self.online_check.isChecked(),
            "max_participants": (
                self.max_spin.value() if self.max_spin.value() > 0 else None
            ),
        }


class TrainingModule(QWidget):
    """Eğitim Takibi Modülü"""

    page_title = "Eğitim Takibi"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Sekme widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_trainings_tab(), "📚 Eğitimler")
        self.tabs.addTab(self._create_sessions_tab(), "📅 Oturumlar")
        self.tabs.addTab(self._create_certificates_tab(), "🏆 Sertifikalar")
        layout.addWidget(self.tabs)

    def _create_trainings_tab(self) -> QWidget:
        """Eğitimler sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Toolbar
        toolbar = QHBoxLayout()
        add_btn = QPushButton(f"{ICONS['add']} Yeni Eğitim")
        add_btn.clicked.connect(self._add_training)
        toolbar.addWidget(add_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Tablo
        self.trainings_table = QTableWidget()
        self.trainings_table.setColumnCount(6)
        self.trainings_table.setHorizontalHeaderLabels(
            ["Eğitim Adı", "Tür", "Süre", "Eğitmen", "Sertifikalı", "Maliyet"]
        )
        self.trainings_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.trainings_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.trainings_table)

        return widget

    def _create_sessions_tab(self) -> QWidget:
        """Oturumlar sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Toolbar
        toolbar = QHBoxLayout()
        add_btn = QPushButton(f"{ICONS['add']} Oturum Planla")
        add_btn.clicked.connect(self._add_session)
        toolbar.addWidget(add_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Tablo
        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(6)
        self.sessions_table.setHorizontalHeaderLabels(
            ["Eğitim", "Tarih", "Lokasyon", "Katılımcı", "Durum", "İşlemler"]
        )
        self.sessions_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.sessions_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.sessions_table)

        return widget

    def _create_certificates_tab(self) -> QWidget:
        """Sertifikalar sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filtre
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Durum:"))
        self.cert_filter = QComboBox()
        self.cert_filter.addItem("Tümü", None)
        self.cert_filter.addItem("Geçerli", "valid")
        self.cert_filter.addItem("Yakında Dolacak", "expiring")
        self.cert_filter.addItem("Süresi Dolmuş", "expired")
        self.cert_filter.currentIndexChanged.connect(self._load_certificates)
        filter_layout.addWidget(self.cert_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Tablo
        self.certificates_table = QTableWidget()
        self.certificates_table.setColumnCount(6)
        self.certificates_table.setHorizontalHeaderLabels(
            ["Çalışan", "Sertifika", "Veren Kurum", "Verilme", "Bitiş", "Durum"]
        )
        self.certificates_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.certificates_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.certificates_table)

        return widget

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_service()
        self._load_data()

    def _ensure_service(self):
        if not self.service:
            self.service = TrainingService()

    def _load_data(self):
        self._load_trainings()
        self._load_sessions()
        self._load_certificates()

    def _load_trainings(self):
        self._ensure_service()
        trainings = self.service.get_trainings()

        self.trainings_table.setRowCount(len(trainings))

        type_names = {
            TrainingType.INTERNAL: "İç Eğitim",
            TrainingType.EXTERNAL: "Dış Eğitim",
            TrainingType.ONLINE: "Çevrimiçi",
            TrainingType.ON_THE_JOB: "İş Başı",
            TrainingType.CERTIFICATION: "Sertifikalı",
        }

        for i, t in enumerate(trainings):
            self.trainings_table.setItem(i, 0, QTableWidgetItem(t.name))
            self.trainings_table.setItem(
                i, 1, QTableWidgetItem(type_names.get(t.training_type, ""))
            )
            self.trainings_table.setItem(
                i,
                2,
                QTableWidgetItem(
                    f"{float(t.duration_hours):.1f} saat" if t.duration_hours else ""
                ),
            )
            self.trainings_table.setItem(i, 3, QTableWidgetItem(t.trainer_name or ""))
            self.trainings_table.setItem(
                i, 4, QTableWidgetItem("✅" if t.has_certificate else "")
            )
            self.trainings_table.setItem(
                i, 5, QTableWidgetItem(f"{float(t.cost):,.0f} ₺" if t.cost else "")
            )

    def _load_sessions(self):
        self._ensure_service()
        sessions = self.service.get_upcoming_sessions(days_ahead=90)

        self.sessions_table.setRowCount(len(sessions))

        status_names = {
            TrainingStatus.PLANNED: "📅 Planlandı",
            TrainingStatus.IN_PROGRESS: "▶️ Devam",
            TrainingStatus.COMPLETED: "✅ Tamamlandı",
            TrainingStatus.CANCELLED: "❌ İptal",
        }

        for i, s in enumerate(sessions):
            self.sessions_table.setItem(i, 0, QTableWidgetItem(s.training.name))
            self.sessions_table.setItem(
                i, 1, QTableWidgetItem(s.planned_date.strftime("%d.%m.%Y"))
            )
            self.sessions_table.setItem(
                i,
                2,
                QTableWidgetItem(s.location or ("🌐 Çevrimiçi" if s.is_online else "")),
            )
            self.sessions_table.setItem(
                i, 3, QTableWidgetItem(str(len(s.participants)))
            )
            self.sessions_table.setItem(
                i, 4, QTableWidgetItem(status_names.get(s.status, ""))
            )

    def _load_certificates(self):
        # Sertifikalar yüklenecek
        pass

    def _add_training(self):
        dialog = TrainingDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self._ensure_service()
                self.service.create_training(**data)
                self._load_trainings()
                QMessageBox.information(
                    self, "Başarılı", "Eğitim başarıyla oluşturuldu."
                )
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def _add_session(self):
        self._ensure_service()
        trainings = self.service.get_trainings()
        if not trainings:
            QMessageBox.warning(self, "Uyarı", "Önce eğitim tanımlamanız gerekiyor.")
            return

        dialog = SessionDialog(trainings, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.service.create_session(**data)
                self._load_sessions()
                QMessageBox.information(self, "Başarılı", "Oturum başarıyla planlandı.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
