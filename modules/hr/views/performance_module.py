"""
Akıllı İş - Performans Değerlendirme Modülü

Çalışan performans değerlendirme UI bileşeni.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QTabWidget,
    QMessageBox,
)
from PyQt6.QtCore import Qt
import qtawesome as qta

from config.icons import ICONS
from modules.hr.services import PerformanceService
from ui.components import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig
from modules.hr.views.performance_dialogs import (
    EvaluationPeriodDialog,
    CompetencyDialog,
)

# from modules.hr.views.evaluation_form import PerformanceEvaluationForm


class PerformanceModule(QWidget):
    """Performans Değerlendirme Modülü"""

    page_title = "Performans"

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
            title="Performans Yönetimi",
            icon=ICONS.CHART,
            show_search=True,
            show_add=True,
            add_text="Yeni Dönem",
            parent=self,
        )
        self.header.add_clicked.connect(self._add_period)
        self.header.refresh_clicked.connect(self.load_data)
        self.header.search_changed.connect(self.load_data)
        layout.addWidget(self.header)

        # === Tabs ===
        self.tabs = QTabWidget()
        self._setup_periods_tab()
        self._setup_competencies_tab()
        self._setup_evals_tab()
        layout.addWidget(self.tabs)

    def _setup_periods_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)

        cols = [
            ColumnConfig("name", "Dönem Adı", stretch=True),
            ColumnConfig("type", "Tür", width=120),
            ColumnConfig("start", "Başlangıç", width=100),
            ColumnConfig("end", "Bitiş", width=100),
            ColumnConfig("status", "Durum", width=100),
        ]
        self.periods_table = EnhancedTableWidget(
            table_id="perf_periods", columns=cols, parent=tab
        )
        layout.addWidget(self.periods_table)
        self.tabs.addTab(tab, "📅 Dönemler")

    def _setup_competencies_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)

        cols = [
            ColumnConfig("name", "Yetkinlik", stretch=True),
            ColumnConfig("category", "Kategori", width=150),
            ColumnConfig("weight", "Ağırlık", width=100),
            ColumnConfig("status", "Durum", width=100),
        ]
        self.comp_table = EnhancedTableWidget(
            table_id="perf_comp", columns=cols, parent=tab
        )
        layout.addWidget(self.comp_table)
        self.tabs.addTab(tab, "⭐ Yetkinlikler")

        # Yetkinlik Ekle Butonu
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Yetkinlik Ekle")
        add_btn.setIcon(qta.icon("ph.plus"))
        add_btn.clicked.connect(self._add_competency)
        btn_layout.addStretch()
        btn_layout.addWidget(add_btn)
        layout.addLayout(btn_layout)

    def _setup_evals_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)

        cols = [
            ColumnConfig("emp", "Çalışan", stretch=True),
            ColumnConfig("period", "Dönem", width=150),
            ColumnConfig("score", "Skor", width=100),
            ColumnConfig("status", "Durum", width=120),
        ]
        self.eval_table = EnhancedTableWidget(
            table_id="perf_eval", columns=cols, parent=tab
        )
        layout.addWidget(self.eval_table)
        self.tabs.addTab(tab, "📊 Değerlendirmeler")

        # Çift tıklama ile form açma
        self.eval_table.itemDoubleClicked.connect(self._open_evaluation)

    def _get_service(self):
        if self.service is None:
            self.service = PerformanceService()
        return self.service

    def _close_service(self):
        if self.service:
            self.service.close()
            self.service = None

    def load_data(self):
        try:
            service = self._get_service()
            # Placeholder data loading logic
            self._load_periods(service)
            self._load_competencies(service)
        except Exception as e:
            print(f"Performance load error: {e}")
        finally:
            self._close_service()

    def _load_periods(self, service):
        periods = service.get_active_periods()
        self.periods_table.setRowCount(len(periods))
        for row, p in enumerate(periods):
            self.periods_table.setItem(row, 0, QTableWidgetItem(p.name))
            self.periods_table.setItem(row, 1, QTableWidgetItem(str(p.period_type)))
            self.periods_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    p.start_date.strftime("%d.%m.%y") if p.start_date else ""
                ),
            )
            self.periods_table.setItem(
                row,
                3,
                QTableWidgetItem(p.end_date.strftime("%d.%m.%y") if p.end_date else ""),
            )
            self.periods_table.setItem(
                row, 4, QTableWidgetItem("Aktif" if p.is_active else "Pasif")
            )

    def _load_competencies(self, service):
        comps = service.get_competencies()
        self.comp_table.setRowCount(len(comps))
        for row, c in enumerate(comps):
            self.comp_table.setItem(row, 0, QTableWidgetItem(c.name))
            self.comp_table.setItem(row, 1, QTableWidgetItem(str(c.category)))
            self.comp_table.setItem(row, 2, QTableWidgetItem(str(c.weight)))
            self.comp_table.setItem(
                row, 3, QTableWidgetItem("Aktif" if c.is_active else "Pasif")
            )

    def _add_period(self):
        try:
            service = self._get_service()
            dialog = EvaluationPeriodDialog(self)
            if dialog.exec():
                data = dialog.get_data()
                service.create_period(**data)
                self.load_data()
                QMessageBox.information(self, "Başarılı", "Dönem oluşturuldu.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            self._close_service()

    def _add_competency(self):
        try:
            service = self._get_service()
            dialog = CompetencyDialog(self)
            if dialog.exec():
                data = dialog.get_data()
                service.create_competency(**data)
                self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            self._close_service()

    def _open_evaluation(self, item):
        # Placeholder: Evaluation ID'yi satırdan al
        QMessageBox.information(self, "Bilgi", "Değerlendirme formu açılıyor...")
        # form = PerformanceEvaluationForm(
        #     self, evaluation_id=1, service=self._get_service()
        # )
        # form.exec()
