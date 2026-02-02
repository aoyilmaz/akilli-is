"""
Akıllı İş - MPS (Master Production Scheduling) Sayfası

Ana Üretim Planı sayfası. Satış siparişlerinden plan oluşturma,
backward scheduling ve iş emirlerine dönüştürme işlemlerini yönetir.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QDialog,
    QFormLayout,
    QDateEdit,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QMessageBox,
    QProgressBar,
    QGroupBox,
    QSplitter,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QFont
import qtawesome as qta

from config.icons import ICONS
from ui.components.page_header import PageHeader
from core.threads.worker_manager import WorkerManager
from modules.planning.services import MPSService
from database.models.production import ProductionPlanStatus


class NewPlanDialog(QDialog):
    """Yeni plan oluşturma diyaloğu."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Üretim Planı")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        # Dönem başlangıç
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        layout.addRow("Dönem Başlangıç:", self.start_date)

        # Dönem bitiş
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate().addDays(30))
        self.end_date.setCalendarPopup(True)
        layout.addRow("Dönem Bitiş:", self.end_date)

        # Plan adı
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Otomatik oluşturulur")
        layout.addRow("Plan Adı:", self.name_edit)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        create_btn = QPushButton("Oluştur")
        create_btn.setDefault(True)
        create_btn.clicked.connect(self.accept)
        btn_layout.addWidget(create_btn)

        layout.addRow("", btn_layout)

    def get_values(self):
        return {
            "period_start": self.start_date.date().toPyDate(),
            "period_end": self.end_date.date().toPyDate(),
            "name": self.name_edit.text() or None,
        }


class GenerateFromOrdersDialog(QDialog):
    """Siparişlerden plan oluşturma diyaloğu."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Siparişlerden Plan Oluştur")
        self.setMinimumWidth(450)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        # Dönem
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        layout.addRow("Dönem Başlangıç:", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate().addDays(30))
        self.end_date.setCalendarPopup(True)
        layout.addRow("Dönem Bitiş:", self.end_date)

        # Önceliklendirme ağırlıkları
        weights_group = QGroupBox("Önceliklendirme Ağırlıkları")
        weights_layout = QFormLayout(weights_group)

        self.customer_weight = QDoubleSpinBox()
        self.customer_weight.setRange(0, 1)
        self.customer_weight.setSingleStep(0.1)
        self.customer_weight.setValue(0.5)
        weights_layout.addRow("Müşteri Skoru:", self.customer_weight)

        self.delay_weight = QDoubleSpinBox()
        self.delay_weight.setRange(0, 1)
        self.delay_weight.setSingleStep(0.1)
        self.delay_weight.setValue(0.5)
        weights_layout.addRow("Gecikme Riski:", self.delay_weight)

        layout.addRow(weights_group)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        create_btn = QPushButton("Oluştur")
        create_btn.setDefault(True)
        create_btn.clicked.connect(self.accept)
        btn_layout.addWidget(create_btn)

        layout.addRow("", btn_layout)

    def get_values(self):
        return {
            "period_start": self.start_date.date().toPyDate(),
            "period_end": self.end_date.date().toPyDate(),
            "customer_weight": self.customer_weight.value(),
            "delay_weight": self.delay_weight.value(),
        }


class MPSPlanListPage(QWidget):
    """
    Ana Üretim Planı (MPS) Sayfası
    """

    page_title = "Ana Üretim Planı"

    plan_created = pyqtSignal(int)  # plan_id
    plan_released = pyqtSignal(int, list)  # plan_id, work_order_ids

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mps_service = MPSService()
        self.current_plan = None
        self.plans = []

        self.setup_ui()
        self.load_plans()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Ana Üretim Planı (MPS)",
            icon=ICONS.PRODUCTION,
            show_search=False,
            show_add=False,
            parent=self,
        )
        self.header.refresh_clicked.connect(self.load_plans)

        # Header'a butonlar ekle
        h_layout = self.header.header_layout()

        new_btn = QPushButton("Yeni Plan")
        new_btn.setIcon(qta.icon(ICONS.ADD, color="#ffffff"))
        new_btn.clicked.connect(self._create_new_plan)
        h_layout.addWidget(new_btn)

        generate_btn = QPushButton("Siparişlerden Oluştur")
        generate_btn.setIcon(qta.icon(ICONS.INVENTORY, color="#ffffff"))
        generate_btn.clicked.connect(self._generate_from_orders)
        h_layout.addWidget(generate_btn)

        layout.addWidget(self.header)

        # Splitter: Sol plan listesi, sağ detaylar
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sol panel: Plan listesi
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_header = QLabel("Planlar")
        left_header.setFont(QFont("", 11, QFont.Weight.Bold))
        left_layout.addWidget(left_header)

        self.plan_list = QTableWidget()
        self.plan_list.setColumnCount(4)
        self.plan_list.setHorizontalHeaderLabels(["No", "Dönem", "Durum", "Satır"])
        self.plan_list.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.plan_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.plan_list.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.plan_list.cellClicked.connect(self._on_plan_selected)
        left_layout.addWidget(self.plan_list)

        splitter.addWidget(left_panel)

        # Sağ panel: Plan detayları
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Detay header
        detail_header = QHBoxLayout()
        self.detail_title = QLabel("Plan seçin")
        self.detail_title.setFont(QFont("", 11, QFont.Weight.Bold))
        detail_header.addWidget(self.detail_title)

        detail_header.addStretch()

        self.schedule_btn = QPushButton("Çizelgele")
        self.schedule_btn.setIcon(qta.icon(ICONS.TIME, color="#ffffff"))
        self.schedule_btn.setEnabled(False)
        self.schedule_btn.clicked.connect(self._run_backward_schedule)
        detail_header.addWidget(self.schedule_btn)

        self.approve_btn = QPushButton("Onayla")
        self.approve_btn.setIcon(qta.icon(ICONS.CHECK, color="#ffffff"))
        self.approve_btn.setEnabled(False)
        self.approve_btn.clicked.connect(self._approve_plan)
        detail_header.addWidget(self.approve_btn)

        self.release_btn = QPushButton("İş Emirlerine Dönüştür")
        self.release_btn.setIcon(qta.icon(ICONS.WORK_ORDER, color="#ffffff"))
        self.release_btn.setEnabled(False)
        self.release_btn.clicked.connect(self._release_plan)
        detail_header.addWidget(self.release_btn)

        right_layout.addLayout(detail_header)

        # Plan satırları tablosu
        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(8)
        self.lines_table.setHorizontalHeaderLabels(
            [
                "Sipariş",
                "Ürün",
                "Miktar",
                "Talep Tarihi",
                "Plan Başlangıç",
                "Plan Bitiş",
                "Öncelik",
                "İş Emri",
            ]
        )
        self.lines_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.lines_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        right_layout.addWidget(self.lines_table)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)

    def load_plans(self):
        """Planları yükle."""

        def fetch():
            return self.mps_service.get_all()

        def on_result(plans):
            self.plans = plans
            self._update_plan_list()

        WorkerManager().run_task(fetch, on_result=on_result)

    def _update_plan_list(self):
        """Plan listesini güncelle."""
        self.plan_list.setRowCount(len(self.plans))

        status_colors = {
            ProductionPlanStatus.DRAFT: "#64748b",
            ProductionPlanStatus.APPROVED: "#3b82f6",
            ProductionPlanStatus.RELEASED: "#10b981",
            ProductionPlanStatus.COMPLETED: "#6b7280",
            ProductionPlanStatus.CANCELLED: "#ef4444",
        }

        status_names = {
            ProductionPlanStatus.DRAFT: "Taslak",
            ProductionPlanStatus.APPROVED: "Onaylı",
            ProductionPlanStatus.RELEASED: "Üretimde",
            ProductionPlanStatus.COMPLETED: "Tamamlandı",
            ProductionPlanStatus.CANCELLED: "İptal",
        }

        for row, plan in enumerate(self.plans):
            self.plan_list.setItem(row, 0, QTableWidgetItem(plan.plan_no))
            p_start = plan.period_start.strftime("%d.%m")
            p_end = plan.period_end.strftime("%d.%m.%Y")
            self.plan_list.setItem(row, 1, QTableWidgetItem(f"{p_start} - {p_end}"))
            status_item = QTableWidgetItem(status_names.get(plan.status, ""))
            status_item.setForeground(QColor(status_colors.get(plan.status, "#000")))
            self.plan_list.setItem(row, 2, status_item)
            l_count = len(plan.lines) if plan.lines else 0
            self.plan_list.setItem(row, 3, QTableWidgetItem(str(l_count)))

    def _on_plan_selected(self, row, col):
        """Plan seçildiğinde."""
        if row < 0 or row >= len(self.plans):
            return
        self.current_plan = self.plans[row]
        self._update_detail_view()

    def _update_detail_view(self):
        """Detay görünümünü güncelle."""
        plan = self.current_plan
        if not plan:
            self.detail_title.setText("Plan seçin")
            self.lines_table.setRowCount(0)
            self.schedule_btn.setEnabled(False)
            self.approve_btn.setEnabled(False)
            self.release_btn.setEnabled(False)
            return

        self.detail_title.setText(f"{plan.plan_no} - {plan.name}")
        is_draft = plan.status == ProductionPlanStatus.DRAFT
        is_approved = plan.status == ProductionPlanStatus.APPROVED
        self.schedule_btn.setEnabled(is_draft)
        self.approve_btn.setEnabled(is_draft)
        self.release_btn.setEnabled(is_approved)

        self.lines_table.setRowCount(len(plan.lines))
        for row, line in enumerate(plan.lines):
            so_no = line.sales_order.order_no if line.sales_order else "-"
            self.lines_table.setItem(row, 0, QTableWidgetItem(so_no))
            i_name = line.item.name if line.item else "-"
            self.lines_table.setItem(row, 1, QTableWidgetItem(i_name))
            qty = f"{float(line.planned_quantity):,.2f}"
            self.lines_table.setItem(row, 2, QTableWidgetItem(qty))
            demand = line.demand_date.strftime("%d.%m.%Y") if line.demand_date else "-"
            self.lines_table.setItem(row, 3, QTableWidgetItem(demand))
            p_start = (
                line.planned_start.strftime("%d.%m.%Y %H:%M")
                if line.planned_start
                else "-"
            )
            self.lines_table.setItem(row, 4, QTableWidgetItem(p_start))
            p_end = (
                line.planned_end.strftime("%d.%m.%Y %H:%M") if line.planned_end else "-"
            )
            self.lines_table.setItem(row, 5, QTableWidgetItem(p_end))
            p_score = f"{float(line.priority_score or 0):.0f}"
            priority_item = QTableWidgetItem(p_score)
            priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            priority = float(line.priority_score or 0)
            if priority >= 80:
                priority_item.setBackground(QColor("#fee2e2"))
            elif priority >= 60:
                priority_item.setBackground(QColor("#fef3c7"))
            self.lines_table.setItem(row, 6, priority_item)
            wo_no = line.work_order.order_no if line.work_order else "-"
            self.lines_table.setItem(row, 7, QTableWidgetItem(wo_no))

    def _create_new_plan(self):
        """Yeni plan oluştur."""
        dialog = NewPlanDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()

            def create():
                return self.mps_service.create_plan(**values)

            def on_result(plan):
                self.load_plans()
                QMessageBox.information(
                    self, "Plan Oluşturuldu", f"Plan {plan.plan_no} oluşturuldu."
                )
                self.plan_created.emit(plan.id)

            WorkerManager().run_task(create, on_result=on_result)

    def _generate_from_orders(self):
        """Siparişlerden plan oluştur."""
        dialog = GenerateFromOrdersDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()

            def generate():
                return self.mps_service.generate_from_sales_orders(**values)

            def on_result(plan):
                self.load_plans()
                l_count = len(plan.lines) if plan.lines else 0
                QMessageBox.information(
                    self,
                    "Plan Oluşturuldu",
                    f"Plan {plan.plan_no} oluşturuldu.\n"
                    f"{l_count} satış siparişi satırı eklendi.",
                )
                self.plan_created.emit(plan.id)

            WorkerManager().run_task(generate, on_result=on_result)

    def _run_backward_schedule(self):
        """Backward scheduling çalıştır."""
        if not self.current_plan:
            return

        def schedule():
            return self.mps_service.backward_schedule_all(
                self.current_plan.id, check_capacity=True
            )

        def on_result(plan):
            self.current_plan = plan
            self._update_detail_view()
            QMessageBox.information(
                self,
                "Çizelgeleme Tamamlandı",
                "Tüm satırlar için backward scheduling tamamlandı.",
            )

        WorkerManager().run_task(schedule, on_result=on_result)

    def _approve_plan(self):
        """Planı onayla."""
        if not self.current_plan:
            return
        reply = QMessageBox.question(
            self,
            "Plan Onayı",
            f"{self.current_plan.plan_no} planını onaylamak istiyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        def approve():
            return self.mps_service.approve_plan(self.current_plan.id, user_id=1)

        def on_result(plan):
            self.current_plan = plan
            self.load_plans()
            QMessageBox.information(
                self, "Plan Onaylandı", f"{plan.plan_no} planı onaylandı."
            )

        WorkerManager().run_task(approve, on_result=on_result)

    def _release_plan(self):
        """Planı iş emirlerine dönüştür."""
        if not self.current_plan:
            return
        msg = f"{self.current_plan.plan_no} planını iş emirlerine dönüştürmek istiyor musunuz?\nBu işlem geri alınamaz."
        reply = QMessageBox.question(
            self,
            "İş Emirlerine Dönüştür",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        def release():
            return self.mps_service.release_plan(self.current_plan.id)

        def on_result(work_orders):
            self.load_plans()
            QMessageBox.information(
                self,
                "Dönüştürme Tamamlandı",
                f"{len(work_orders)} iş emri oluşturuldu.",
            )
            self.plan_released.emit(self.current_plan.id, [wo.id for wo in work_orders])

        def on_error(error):
            QMessageBox.warning(self, "Hata", f"Dönüştürme başarısız: {str(error)}")

        WorkerManager().run_task(release, on_result=on_result, on_error=on_error)

    def closeEvent(self, event):
        """Sayfa kapatılırken."""
        if self.mps_service:
            self.mps_service.close()
        super().closeEvent(event)
