"""
Bakım Modülü - Raporlar ve KPI Dashboard
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QDateEdit,
    QTabWidget,
    QFrame,
    QGridLayout,
)
from PyQt6.QtCore import Qt, QDate
import qtawesome as qta

from config.icons import ICONS
from modules.maintenance.views.base import MaintenanceBaseWidget
from ui.components.page_header import PageHeader
from ui.components.stat_cards import MiniStatCard
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


class ReportingWidget(MaintenanceBaseWidget):
    """Bakım Raporları Ana Widget'ı"""

    def __init__(self, parent=None):
        super().__init__("Bakım Raporları", parent)
        self.setup_ui()

    def setup_ui(self):
        # Header
        self.header = PageHeader(
            title="Bakım Raporları",
            icon=ICONS.CHART,
            show_search=False,
            show_refresh=False,
            show_add=False,
            parent=self,
        )

        h_layout = self.header.header_layout()
        h_layout.addStretch()

        h_layout.addWidget(QLabel("Başlangıç:"))
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate().addMonths(-1))
        self.date_start.setFixedHeight(36)
        h_layout.addWidget(self.date_start)

        h_layout.addSpacing(10)
        h_layout.addWidget(QLabel("Bitiş:"))
        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setFixedHeight(36)
        h_layout.addWidget(self.date_end)

        h_layout.addSpacing(10)
        btn_refresh = QPushButton("Güncelle")
        btn_refresh.setIcon(qta.icon(ICONS.REFRESH, color="#ffffff"))
        btn_refresh.setProperty("class", "btn-primary")
        btn_refresh.setFixedHeight(36)
        btn_refresh.clicked.connect(self.refresh_data)
        h_layout.addWidget(btn_refresh)

        self.layout.addWidget(self.header)

        # Tab widget
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Tab 1: Özet
        self.tab_summary = QWidget()
        self.setup_summary_tab()
        self.tabs.addTab(self.tab_summary, "Özet")

        # Tab 2: Maliyet Analizi
        self.tab_cost = QWidget()
        self.setup_cost_tab()
        self.tabs.addTab(self.tab_cost, "Maliyet Analizi")

        # Tab 3: Teknisyen Performansı
        self.tab_technician = QWidget()
        self.setup_technician_tab()
        self.tabs.addTab(self.tab_technician, "Teknisyen Performansı")

        # Tab 4: Geciken Bakımlar
        self.tab_overdue = QWidget()
        self.setup_overdue_tab()
        self.tabs.addTab(self.tab_overdue, "Geciken Bakımlar")

        self.refresh_data()

    def setup_summary_tab(self):
        layout = QVBoxLayout(self.tab_summary)
        layout.setContentsMargins(16, 16, 16, 16)

        self.summary_stats_layout = QHBoxLayout()
        self.summary_stats = {
            "total": MiniStatCard("Toplam İş Emri", "0", "info", icon=ICONS.INVOICE),
            "completed": MiniStatCard("Tamamlanan", "0", "success", icon=ICONS.CHECK),
            "in_progress": MiniStatCard("Devam Eden", "0", "warning", icon=ICONS.TIME),
            "cost": MiniStatCard("Toplam Maliyet", "₺0.00", "error", icon=ICONS.MONEY),
        }
        for card in self.summary_stats.values():
            self.summary_stats_layout.addWidget(card)
        layout.addLayout(self.summary_stats_layout)

        cols = [
            ColumnConfig("metric", "Metrik", width=200, stretch=True),
            ColumnConfig("total", "Toplam", width=120),
            ColumnConfig("completed", "Tamamlanan", width=120),
            ColumnConfig("in_progress", "Devam Eden", width=120),
            ColumnConfig("cancelled", "İptal", width=120),
        ]
        self.summary_table = EnhancedTableWidget(
            table_id="maint_summary", columns=cols, parent=self
        )
        layout.addWidget(self.summary_table)

    def setup_cost_tab(self):
        layout = QVBoxLayout(self.tab_cost)
        layout.setContentsMargins(16, 16, 16, 16)

        cols = [
            ColumnConfig("equipment", "Ekipman", width=250, stretch=True),
            ColumnConfig("material", "Malzeme", width=120),
            ColumnConfig("labor", "İşçilik", width=120),
            ColumnConfig("total", "Toplam", width=120),
            ColumnConfig("count", "İş Emri Sayısı", width=120),
        ]
        self.cost_table = EnhancedTableWidget(
            table_id="maint_cost", columns=cols, parent=self
        )
        layout.addWidget(self.cost_table)

    def setup_technician_tab(self):
        layout = QVBoxLayout(self.tab_technician)
        layout.setContentsMargins(16, 16, 16, 16)

        cols = [
            ColumnConfig("name", "Teknisyen", width=200, stretch=True),
            ColumnConfig("completed", "Tamamlanan İş", width=120),
            ColumnConfig("hours", "Toplam Saat", width=120),
            ColumnConfig("avg", "Ort. Süre", width=120),
            ColumnConfig("rate", "Başarı Oranı", width=120),
        ]
        self.tech_table = EnhancedTableWidget(
            table_id="maint_tech", columns=cols, parent=self
        )
        layout.addWidget(self.tech_table)

    def setup_overdue_tab(self):
        layout = QVBoxLayout(self.tab_overdue)
        layout.setContentsMargins(16, 16, 16, 16)

        cols = [
            ColumnConfig("equipment", "Ekipman", width=200, stretch=True),
            ColumnConfig("plan", "Plan Adı", width=200),
            ColumnConfig("date", "Planlanan Tarih", width=120),
            ColumnConfig("delay", "Gecikme (Gün)", width=120),
            ColumnConfig("criticality", "Kritiklik", width=120),
        ]
        self.overdue_table = EnhancedTableWidget(
            table_id="maint_overdue", columns=cols, parent=self
        )
        layout.addWidget(self.overdue_table)

    def refresh_data(self):
        start = self.date_start.date().toPyDate()
        end = self.date_end.date().toPyDate()
        self._refresh_summary(start, end)
        self._refresh_cost(start, end)
        self._refresh_technician(start, end)
        self._refresh_overdue()

    def _refresh_summary(self, start, end):
        stats = self.service.get_work_order_stats(start, end)
        self.summary_stats["total"].update_value(str(stats.get("total", 0)))
        self.summary_stats["completed"].update_value(str(stats.get("completed", 0)))
        self.summary_stats["in_progress"].update_value(str(stats.get("in_progress", 0)))
        self.summary_stats["cost"].update_value(f"₺{stats.get('total_cost', 0):,.2f}")

        data = [
            {
                "metric": "İş Emirleri",
                "total": stats.get("total", 0),
                "completed": stats.get("completed", 0),
                "in_progress": stats.get("in_progress", 0),
                "cancelled": stats.get("cancelled", 0),
            },
            {
                "metric": "Arıza Talepleri",
                "total": stats.get("requests_total", 0),
                "completed": stats.get("requests_resolved", 0),
                "in_progress": stats.get("requests_pending", 0),
                "cancelled": 0,
            },
            {
                "metric": "Periyodik Bakımlar",
                "total": stats.get("preventive_total", 0),
                "completed": stats.get("preventive_done", 0),
                "in_progress": stats.get("preventive_pending", 0),
                "cancelled": 0,
            },
        ]
        self.summary_table.setRowCount(len(data))
        cols = self.summary_table.get_visible_columns()
        for r, row in enumerate(data):
            for c, key in enumerate(cols):
                self.summary_table.setItem(
                    r, c, QTableWidgetItem(str(row.get(key, "")))
                )

    def _refresh_cost(self, start, end):
        costs = self.service.get_equipment_cost_report(start, end)
        self.cost_table.setRowCount(len(costs))
        cols = self.cost_table.get_visible_columns()
        for i, cost in enumerate(costs):
            for c, key in enumerate(cols):
                if key == "equipment":
                    val = cost.get("equipment_name", "-")
                elif key == "material":
                    val = f"₺{cost.get('material_cost', 0):,.2f}"
                elif key == "labor":
                    val = f"₺{cost.get('labor_cost', 0):,.2f}"
                elif key == "total":
                    val = f"₺{cost.get('total_cost', 0):,.2f}"
                elif key == "count":
                    val = str(cost.get("work_order_count", 0))
                self.cost_table.setItem(i, c, QTableWidgetItem(val))

    def _refresh_technician(self, start, end):
        techs = self.service.get_technician_performance(start, end)
        self.tech_table.setRowCount(len(techs))
        cols = self.tech_table.get_visible_columns()
        for i, tech in enumerate(techs):
            for c, key in enumerate(cols):
                if key == "name":
                    val = tech.get("name", "-")
                elif key == "completed":
                    val = str(tech.get("completed_count", 0))
                elif key == "hours":
                    val = f"{tech.get('total_hours', 0):.1f}"
                elif key == "avg":
                    val = f"{tech.get('avg_hours', 0):.1f}"
                elif key == "rate":
                    val = f"{tech.get('success_rate', 0):.1f}%"
                self.tech_table.setItem(i, c, QTableWidgetItem(val))

    def _refresh_overdue(self):
        overdue = self.service.get_overdue_maintenance_plans()
        self.overdue_table.setRowCount(len(overdue))
        today = datetime.now().date()
        cols = self.overdue_table.get_visible_columns()
        for i, plan in enumerate(overdue):
            for c, key in enumerate(cols):
                if key == "equipment":
                    val = plan.equipment.name if plan.equipment else "-"
                elif key == "plan":
                    val = plan.name
                elif key == "date":
                    dt = plan.next_maintenance_date
                    val = dt.strftime("%d.%m.%Y") if dt else "-"
                elif key == "delay":
                    dt = plan.next_maintenance_date
                    if dt:
                        days = (today - dt.date()).days
                        item = QTableWidgetItem(str(days))
                        item.setForeground(Qt.GlobalColor.red)
                        self.overdue_table.setItem(i, c, item)
                        continue
                    else:
                        val = "-"
                elif key == "criticality":
                    val = (
                        plan.equipment.criticality.value
                        if plan.equipment and plan.equipment.criticality
                        else "-"
                    )
                self.overdue_table.setItem(i, c, QTableWidgetItem(val))


class KPIDashboardWidget(MaintenanceBaseWidget):
    """KPI Dashboard Widget'ı - MTBF, MTTR, Kullanılabilirlik"""

    def __init__(self, parent=None):
        super().__init__("Bakım KPI Dashboard", parent)
        self.setup_ui()

    def setup_ui(self):
        # Header
        self.header = PageHeader(
            title="Bakım KPI Dashboard",
            icon=ICONS.CHART,
            show_search=False,
            show_refresh=True,
            show_add=False,
            parent=self,
        )
        self.header.refresh_clicked.connect(self.refresh_data)

        h_layout = self.header.header_layout()
        h_layout.addWidget(QLabel("Ekipman:"))
        self.cmb_equipment = QComboBox()
        self.cmb_equipment.addItem("- Tüm Ekipmanlar -", None)
        equipments = self.service.get_equipment_list(active_only=True)
        for eq in equipments:
            self.cmb_equipment.addItem(f"{eq.code} - {eq.name}", eq.id)
        self.cmb_equipment.setFixedHeight(36)
        self.cmb_equipment.currentIndexChanged.connect(self.refresh_data)
        h_layout.addWidget(self.cmb_equipment)

        h_layout.addSpacing(16)
        h_layout.addWidget(QLabel("Dönem:"))
        self.cmb_period = QComboBox()
        self.cmb_period.addItem("Son 30 Gün", 30)
        self.cmb_period.addItem("Son 90 Gün", 90)
        self.cmb_period.addItem("Son 1 Yıl", 365)
        self.cmb_period.setFixedHeight(36)
        self.cmb_period.currentIndexChanged.connect(self.refresh_data)
        h_layout.addWidget(self.cmb_period)

        h_layout.addStretch()
        self.layout.addWidget(self.header)

        # KPI Summary
        self.kpi_layout = QHBoxLayout()
        self.kpi_cards = {
            "mtbf": MiniStatCard("Ort. MTBF", "0 saat", "info", icon=ICONS.TIME),
            "mttr": MiniStatCard("Ort. MTTR", "0 saat", "warning", icon=ICONS.TIME),
            "availability": MiniStatCard(
                "Kullanılabilirlik", "100%", "success", icon=ICONS.CHECK
            ),
            "failures": MiniStatCard("Toplam Arıza", "0", "error", icon=ICONS.CLOSE),
        }
        for card in self.kpi_cards.values():
            self.kpi_layout.addWidget(card)
        self.layout.addLayout(self.kpi_layout)

        # Tablo
        cols = [
            ColumnConfig("equipment", "Ekipman", width=200, stretch=True),
            ColumnConfig("mtbf", "MTBF (saat)", width=120),
            ColumnConfig("mttr", "MTTR (saat)", width=120),
            ColumnConfig("avail", "Kullanılabilirlik (%)", width=150),
            ColumnConfig("count", "Arıza Sayısı", width=120),
            ColumnConfig("downtime", "Toplam Duruş (saat)", width=150),
        ]
        self.detail_table = EnhancedTableWidget(
            table_id="maint_kpi_detail", columns=cols, parent=self
        )
        self.layout.addWidget(self.detail_table)

        self.refresh_data()

    def refresh_data(self):
        eq_id = self.cmb_equipment.currentData()
        period = self.cmb_period.currentData()
        if eq_id:
            kpis = self.service.get_equipment_kpis(eq_id, period)
            self._update_kpi_cards([kpis])
            self._update_table([kpis])
        else:
            all_kpis = self.service.get_all_equipment_kpis(period)
            self._update_kpi_cards(all_kpis)
            self._update_table(all_kpis)

    def _update_kpi_cards(self, kpi_list):
        if not kpi_list:
            return
        mtbf = sum(k.get("mtbf", 0) for k in kpi_list) / len(kpi_list)
        mttr = sum(k.get("mttr", 0) for k in kpi_list) / len(kpi_list)
        avail = sum(k.get("availability", 100) for k in kpi_list) / len(kpi_list)
        fails = sum(k.get("failure_count", 0) for k in kpi_list)

        self.kpi_cards["mtbf"].update_value(f"{mtbf:.1f} saat")
        self.kpi_cards["mttr"].update_value(f"{mttr:.1f} saat")
        self.kpi_cards["availability"].update_value(f"{avail:.1f}%")
        self.kpi_cards["failures"].update_value(str(fails))

    def _update_table(self, kpis):
        self.detail_table.setRowCount(len(kpis))
        cols = self.detail_table.get_visible_columns()
        for i, kpi in enumerate(kpis):
            for c, key in enumerate(cols):
                if key == "equipment":
                    val = kpi.get("equipment_name", "-")
                elif key == "mtbf":
                    val = f"{kpi.get('mtbf', 0):.1f}"
                elif key == "mttr":
                    val = f"{kpi.get('mttr', 0):.1f}"
                elif key == "avail":
                    v = kpi.get("availability", 100)
                    item = QTableWidgetItem(f"{v:.1f}")
                    if v < 90:
                        item.setForeground(Qt.GlobalColor.red)
                    elif v < 95:
                        item.setForeground(Qt.GlobalColor.darkYellow)
                    self.detail_table.setItem(i, c, item)
                    continue
                elif key == "count":
                    val = str(kpi.get("failure_count", 0))
                elif key == "downtime":
                    val = f"{kpi.get('total_downtime', 0):.1f}"
                self.detail_table.setItem(i, c, QTableWidgetItem(val))


class CostAnalysisWidget(MaintenanceBaseWidget):
    """Maliyet Analizi Widget'ı"""

    def __init__(self, parent=None):
        super().__init__("Bakım Maliyet Analizi", parent)
        self.setup_ui()

    def setup_ui(self):
        # Header
        self.header = PageHeader(
            title="Bakım Maliyet Analizi",
            icon=ICONS.MONEY,
            show_search=False,
            show_refresh=False,
            show_add=False,
            parent=self,
        )
        self.layout.addWidget(self.header)
        info = QLabel(
            "Detaylı maliyet analizi için Raporlar > Maliyet Analizi sekmesini kullanın."
        )
        info.setStyleSheet("color: #6b7280; font-size: 14px; margin: 20px;")
        self.layout.addWidget(info)
