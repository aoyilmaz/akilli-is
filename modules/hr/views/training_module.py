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
    QTableWidgetItem,
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
    QFrame,
)
from PyQt6.QtCore import Qt, QDate
import qtawesome as qta

from config.icons import ICONS
from config import COLORS
from modules.hr.services import TrainingService
from database.models.training import TrainingType, TrainingStatus
from ui.components import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


class TrainingModule(QWidget):
    """Eğitim Takibi Modülü"""

    page_title = "Eğitim"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # === Header ===
        self.header = PageHeader(
            title="Eğitim Yönetimi",
            icon=ICONS.CHART,  # BOOK or TRAINING icon would be better if available
            show_search=True,
            show_add=True,
            add_text="Yeni Eğitim",
            parent=self,
        )
        self.header.add_clicked.connect(self._add_training)
        self.header.refresh_clicked.connect(self.load_data)
        self.header.search_changed.connect(self.load_data)
        layout.addWidget(self.header)

        # === Tabs ===
        self.tabs = QTabWidget()
        self._setup_trainings_tab()
        self._setup_sessions_tab()
        self._setup_certs_tab()
        layout.addWidget(self.tabs)

    def _setup_trainings_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(12, 12, 12, 12)

        cols = [
            ColumnConfig("name", "Eğitim Adı", stretch=True),
            ColumnConfig("type", "Tür", width=120),
            ColumnConfig("duration", "Süre", width=100),
            ColumnConfig("trainer", "Eğitmen", width=150),
            ColumnConfig("cert", "Sertifikalı", width=100),
        ]
        self.trainings_table = EnhancedTableWidget(
            table_id="hr_trainings", columns=cols, parent=tab
        )
        l.addWidget(self.trainings_table)
        self.tabs.addTab(tab, "📚 Eğitimler")

    def _setup_sessions_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(12, 12, 12, 12)

        cols = [
            ColumnConfig("training", "Eğitim", stretch=True),
            ColumnConfig("date", "Tarih", width=120),
            ColumnConfig("location", "Lokasyon", width=150),
            ColumnConfig("participants", "Katılımcı", width=100),
            ColumnConfig("status", "Durum", width=120),
        ]
        self.sessions_table = EnhancedTableWidget(
            table_id="hr_training_sessions", columns=cols, parent=tab
        )
        l.addWidget(self.sessions_table)
        self.tabs.addTab(tab, "📅 Oturumlar")

    def _setup_certs_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(12, 12, 12, 12)

        cols = [
            ColumnConfig("emp", "Çalışan", stretch=True),
            ColumnConfig("cert", "Sertifika", width=200),
            ColumnConfig("issue", "Verilme", width=100),
            ColumnConfig("expiry", "Bitiş", width=100),
            ColumnConfig("status", "Durum", width=100),
        ]
        self.cert_table = EnhancedTableWidget(
            table_id="hr_certs", columns=cols, parent=tab
        )
        l.addWidget(self.cert_table)
        self.tabs.addTab(tab, "🏆 Sertifikalar")

    def _get_service(self):
        if self.service is None:
            self.service = TrainingService()
        return self.service

    def _close_service(self):
        if self.service:
            self.service.close()
            self.service = None

    def load_data(self):
        try:
            service = self._get_service()
            self._load_trainings(service)
            self._load_sessions(service)
        except Exception as e:
            print(f"Training load error: {e}")
        finally:
            self._close_service()

    def _load_trainings(self, service):
        trainings = service.get_trainings()
        self.trainings_table.setRowCount(len(trainings))
        for row, t in enumerate(trainings):
            self.trainings_table.setItem(row, 0, QTableWidgetItem(t.name))
            self.trainings_table.setItem(row, 1, QTableWidgetItem(str(t.training_type)))
            self.trainings_table.setItem(
                row, 2, QTableWidgetItem(f"{t.duration_hours} s")
            )
            self.trainings_table.setItem(
                row, 3, QTableWidgetItem(t.trainer_name or "-")
            )
            self.trainings_table.setItem(
                row, 4, QTableWidgetItem("Evet" if t.has_certificate else "Hayır")
            )

    def _load_sessions(self, service):
        sessions = service.get_upcoming_sessions()
        self.sessions_table.setRowCount(len(sessions))
        for row, s in enumerate(sessions):
            self.sessions_table.setItem(
                row, 0, QTableWidgetItem(s.training.name if s.training else "-")
            )
            self.sessions_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    s.planned_date.strftime("%d.%m.%y") if s.planned_date else ""
                ),
            )
            self.sessions_table.setItem(row, 2, QTableWidgetItem(s.location or "-"))
            self.sessions_table.setItem(
                row, 3, QTableWidgetItem(str(len(s.participants)))
            )
            self.sessions_table.setItem(row, 4, QTableWidgetItem(str(s.status)))

    def _add_training(self):
        QMessageBox.information(
            self, "Bilgi", "Yeni Eğitim formu yakında eklenecektir."
        )
