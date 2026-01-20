"""
Akıllı İş - Performans Değerlendirme Modülü

Çalışan performans değerlendirme UI bileşeni.
"""

from datetime import date
from decimal import Decimal

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
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
    QMessageBox,
    QGroupBox,
    QScrollArea,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from config.styles import COLORS, ICONS
from modules.hr.services import PerformanceService
from database.models.performance import (
    EvaluationPeriodType,
    EvaluationStatus,
    CompetencyCategory,
    PerformanceRating,
)


class PeriodDialog(QDialog):
    """Değerlendirme dönemi ekleme/düzenleme dialogu"""

    def __init__(self, period_data: dict = None, parent=None):
        super().__init__(parent)
        self.period_data = period_data
        self.setWindowTitle("Dönem Ekle" if not period_data else "Dönem Düzenle")
        self.setMinimumWidth(450)
        self.setup_ui()
        if period_data:
            self.load_data()

    def setup_ui(self):
        layout = QFormLayout(self)

        # Dönem adı
        self.name_edit = QLineEdit()
        layout.addRow("Dönem Adı:", self.name_edit)

        # Dönem türü
        self.type_combo = QComboBox()
        self.type_combo.addItem("Yıllık", EvaluationPeriodType.ANNUAL)
        self.type_combo.addItem("6 Aylık", EvaluationPeriodType.SEMI_ANNUAL)
        self.type_combo.addItem("Çeyreklik", EvaluationPeriodType.QUARTERLY)
        self.type_combo.addItem("Aylık", EvaluationPeriodType.MONTHLY)
        self.type_combo.addItem("Deneme", EvaluationPeriodType.PROBATION)
        layout.addRow("Dönem Türü:", self.type_combo)

        # Tarihler
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        layout.addRow("Başlangıç:", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addMonths(12))
        layout.addRow("Bitiş:", self.end_date)

        # Değerlendirme tarihleri
        self.eval_start = QDateEdit()
        self.eval_start.setCalendarPopup(True)
        layout.addRow("Değerlendirme Başlangıcı:", self.eval_start)

        self.eval_end = QDateEdit()
        self.eval_end.setCalendarPopup(True)
        layout.addRow("Değerlendirme Bitişi:", self.eval_end)

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
        if self.period_data:
            self.name_edit.setText(self.period_data.get("name", ""))

    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text(),
            "period_type": self.type_combo.currentData(),
            "start_date": self.start_date.date().toPyDate(),
            "end_date": self.end_date.date().toPyDate(),
            "evaluation_start": self.eval_start.date().toPyDate(),
            "evaluation_end": self.eval_end.date().toPyDate(),
            "description": self.description.toPlainText(),
        }


class CompetencyDialog(QDialog):
    """Yetkinlik ekleme/düzenleme dialogu"""

    def __init__(self, competency_data: dict = None, parent=None):
        super().__init__(parent)
        self.competency_data = competency_data
        self.setWindowTitle(
            "Yetkinlik Ekle" if not competency_data else "Yetkinlik Düzenle"
        )
        self.setMinimumWidth(400)
        self.setup_ui()
        if competency_data:
            self.load_data()

    def setup_ui(self):
        layout = QFormLayout(self)

        # Ad
        self.name_edit = QLineEdit()
        layout.addRow("Yetkinlik Adı:", self.name_edit)

        # Kategori
        self.category_combo = QComboBox()
        self.category_combo.addItem("Teknik", CompetencyCategory.TECHNICAL)
        self.category_combo.addItem("Davranışsal", CompetencyCategory.BEHAVIORAL)
        self.category_combo.addItem("Liderlik", CompetencyCategory.LEADERSHIP)
        self.category_combo.addItem("İletişim", CompetencyCategory.COMMUNICATION)
        self.category_combo.addItem("Takım Çalışması", CompetencyCategory.TEAMWORK)
        layout.addRow("Kategori:", self.category_combo)

        # Ağırlık
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(0.1, 2.0)
        self.weight_spin.setValue(1.0)
        self.weight_spin.setSingleStep(0.1)
        layout.addRow("Ağırlık:", self.weight_spin)

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
        if self.competency_data:
            self.name_edit.setText(self.competency_data.get("name", ""))

    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text(),
            "category": self.category_combo.currentData(),
            "weight": self.weight_spin.value(),
            "description": self.description.toPlainText(),
        }


class PerformanceModule(QWidget):
    """Performans Değerlendirme Modülü"""

    page_title = "Performans Değerlendirme"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Sekme widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_periods_tab(), "📅 Dönemler")
        self.tabs.addTab(self._create_competencies_tab(), "⭐ Yetkinlikler")
        self.tabs.addTab(self._create_evaluations_tab(), "📊 Değerlendirmeler")
        layout.addWidget(self.tabs)

    def _create_periods_tab(self) -> QWidget:
        """Dönemler sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Toolbar
        toolbar = QHBoxLayout()
        add_btn = QPushButton(f"{ICONS['add']} Yeni Dönem")
        add_btn.clicked.connect(self._add_period)
        toolbar.addWidget(add_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Tablo
        self.periods_table = QTableWidget()
        self.periods_table.setColumnCount(6)
        self.periods_table.setHorizontalHeaderLabels(
            ["Dönem Adı", "Tür", "Başlangıç", "Bitiş", "Değerlendirme", "Durum"]
        )
        self.periods_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.periods_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.periods_table)

        return widget

    def _create_competencies_tab(self) -> QWidget:
        """Yetkinlikler sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Toolbar
        toolbar = QHBoxLayout()
        add_btn = QPushButton(f"{ICONS['add']} Yeni Yetkinlik")
        add_btn.clicked.connect(self._add_competency)
        toolbar.addWidget(add_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Tablo
        self.competencies_table = QTableWidget()
        self.competencies_table.setColumnCount(4)
        self.competencies_table.setHorizontalHeaderLabels(
            ["Yetkinlik", "Kategori", "Ağırlık", "Durum"]
        )
        self.competencies_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.competencies_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.competencies_table)

        return widget

    def _create_evaluations_tab(self) -> QWidget:
        """Değerlendirmeler sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filtre
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Dönem:"))
        self.period_filter = QComboBox()
        self.period_filter.addItem("Tüm Dönemler", None)
        self.period_filter.currentIndexChanged.connect(self._load_evaluations)
        filter_layout.addWidget(self.period_filter)

        filter_layout.addWidget(QLabel("Durum:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tümü", None)
        self.status_filter.addItem("Beklemede", EvaluationStatus.PENDING_SELF)
        self.status_filter.addItem("Tamamlandı", EvaluationStatus.COMPLETED)
        self.status_filter.currentIndexChanged.connect(self._load_evaluations)
        filter_layout.addWidget(self.status_filter)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Tablo
        self.evaluations_table = QTableWidget()
        self.evaluations_table.setColumnCount(7)
        self.evaluations_table.setHorizontalHeaderLabels(
            [
                "Çalışan",
                "Dönem",
                "Durum",
                "Özdeğerlendirme",
                "Yönetici",
                "Final",
                "Sonuç",
            ]
        )
        self.evaluations_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.evaluations_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.evaluations_table)

        return widget

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_service()
        self._load_data()

    def _ensure_service(self):
        if not self.service:
            self.service = PerformanceService()

    def _load_data(self):
        self._load_periods()
        self._load_competencies()
        self._load_evaluations()

    def _load_periods(self):
        self._ensure_service()
        periods = self.service.get_active_periods()

        self.periods_table.setRowCount(len(periods))
        self.period_filter.clear()
        self.period_filter.addItem("Tüm Dönemler", None)

        type_names = {
            EvaluationPeriodType.ANNUAL: "Yıllık",
            EvaluationPeriodType.SEMI_ANNUAL: "6 Aylık",
            EvaluationPeriodType.QUARTERLY: "Çeyreklik",
            EvaluationPeriodType.MONTHLY: "Aylık",
            EvaluationPeriodType.PROBATION: "Deneme",
        }

        for i, period in enumerate(periods):
            self.periods_table.setItem(i, 0, QTableWidgetItem(period.name))
            self.periods_table.setItem(
                i, 1, QTableWidgetItem(type_names.get(period.period_type, ""))
            )
            self.periods_table.setItem(
                i,
                2,
                QTableWidgetItem(
                    period.start_date.strftime("%d.%m.%Y") if period.start_date else ""
                ),
            )
            self.periods_table.setItem(
                i,
                3,
                QTableWidgetItem(
                    period.end_date.strftime("%d.%m.%Y") if period.end_date else ""
                ),
            )
            eval_dates = ""
            if period.evaluation_start and period.evaluation_end:
                eval_dates = (
                    f"{period.evaluation_start.strftime('%d.%m')} - "
                    f"{period.evaluation_end.strftime('%d.%m')}"
                )
            self.periods_table.setItem(i, 4, QTableWidgetItem(eval_dates))
            self.periods_table.setItem(
                i, 5, QTableWidgetItem("✅ Aktif" if period.is_active else "❌")
            )

            # Filtre combo'ya ekle
            self.period_filter.addItem(period.name, period.id)

    def _load_competencies(self):
        self._ensure_service()
        competencies = self.service.get_competencies()

        self.competencies_table.setRowCount(len(competencies))

        category_names = {
            CompetencyCategory.TECHNICAL: "Teknik",
            CompetencyCategory.BEHAVIORAL: "Davranışsal",
            CompetencyCategory.LEADERSHIP: "Liderlik",
            CompetencyCategory.COMMUNICATION: "İletişim",
            CompetencyCategory.TEAMWORK: "Takım",
        }

        for i, comp in enumerate(competencies):
            self.competencies_table.setItem(i, 0, QTableWidgetItem(comp.name))
            self.competencies_table.setItem(
                i, 1, QTableWidgetItem(category_names.get(comp.category, ""))
            )
            self.competencies_table.setItem(
                i, 2, QTableWidgetItem(f"{float(comp.weight):.1f}")
            )
            self.competencies_table.setItem(
                i, 3, QTableWidgetItem("✅ Aktif" if comp.is_active else "❌")
            )

    def _load_evaluations(self):
        # Değerlendirmeler yüklenecek
        pass

    def _add_period(self):
        dialog = PeriodDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self._ensure_service()
                self.service.create_period(**data)
                self._load_periods()
                QMessageBox.information(
                    self, "Başarılı", "Dönem başarıyla oluşturuldu."
                )
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def _add_competency(self):
        dialog = CompetencyDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self._ensure_service()
                self.service.create_competency(**data)
                self._load_competencies()
                QMessageBox.information(
                    self, "Başarılı", "Yetkinlik başarıyla oluşturuldu."
                )
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
