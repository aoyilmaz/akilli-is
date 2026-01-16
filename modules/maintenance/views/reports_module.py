"""
Bakım Modülü - Raporlar ve KPI Dashboard
"""

from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QGroupBox,
    QFormLayout,
    QDateEdit,
    QTabWidget,
    QFrame,
    QGridLayout,
    QScrollArea,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from modules.maintenance.views.base import MaintenanceBaseWidget


class ReportingWidget(MaintenanceBaseWidget):
    """Bakım Raporları Ana Widget'ı"""

    def __init__(self, parent=None):
        super().__init__("Bakım Raporları", parent)
        self.setup_ui()

    def setup_ui(self):
        # Filtreler
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Başlangıç:"))
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.date_start)

        filter_layout.addWidget(QLabel("Bitiş:"))
        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(QDate.currentDate())
        filter_layout.addWidget(self.date_end)

        btn_refresh = QPushButton("Raporu Güncelle")
        btn_refresh.setStyleSheet("background-color: #007acc; color: white; padding: 8px;")
        btn_refresh.clicked.connect(self.refresh_data)
        filter_layout.addWidget(btn_refresh)

        filter_layout.addStretch()
        self.layout.addLayout(filter_layout)

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

        # KPI Kartları
        self.kpi_layout = QHBoxLayout()
        layout.addLayout(self.kpi_layout)

        # İş emri tablosu
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(5)
        self.summary_table.setHorizontalHeaderLabels([
            "Metrik", "Toplam", "Tamamlanan", "Devam Eden", "İptal"
        ])
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.summary_table)

    def setup_cost_tab(self):
        layout = QVBoxLayout(self.tab_cost)

        # Ekipman bazlı maliyet tablosu
        self.cost_table = QTableWidget()
        self.cost_table.setColumnCount(5)
        self.cost_table.setHorizontalHeaderLabels([
            "Ekipman", "Malzeme", "İşçilik", "Toplam", "İş Emri Sayısı"
        ])
        self.cost_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.cost_table)

    def setup_technician_tab(self):
        layout = QVBoxLayout(self.tab_technician)

        self.tech_table = QTableWidget()
        self.tech_table.setColumnCount(5)
        self.tech_table.setHorizontalHeaderLabels([
            "Teknisyen", "Tamamlanan İş", "Toplam Saat", "Ort. Süre", "Başarı Oranı"
        ])
        self.tech_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tech_table)

    def setup_overdue_tab(self):
        layout = QVBoxLayout(self.tab_overdue)

        self.overdue_table = QTableWidget()
        self.overdue_table.setColumnCount(5)
        self.overdue_table.setHorizontalHeaderLabels([
            "Ekipman", "Plan Adı", "Planlanan Tarih", "Gecikme (Gün)", "Kritiklik"
        ])
        self.overdue_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.overdue_table)

    def refresh_data(self):
        start_date = self.date_start.date().toPyDate()
        end_date = self.date_end.date().toPyDate()

        self._refresh_summary(start_date, end_date)
        self._refresh_cost(start_date, end_date)
        self._refresh_technician(start_date, end_date)
        self._refresh_overdue()

    def _refresh_summary(self, start_date, end_date):
        # KPI kartlarını temizle ve yeniden oluştur
        while self.kpi_layout.count():
            item = self.kpi_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        stats = self.service.get_work_order_stats(start_date, end_date)

        self.kpi_layout.addWidget(self._create_kpi_card(
            "Toplam İş Emri", str(stats.get('total', 0)), "#3b82f6"
        ))
        self.kpi_layout.addWidget(self._create_kpi_card(
            "Tamamlanan", str(stats.get('completed', 0)), "#22c55e"
        ))
        self.kpi_layout.addWidget(self._create_kpi_card(
            "Devam Eden", str(stats.get('in_progress', 0)), "#f97316"
        ))
        self.kpi_layout.addWidget(self._create_kpi_card(
            "Toplam Maliyet", f"₺{stats.get('total_cost', 0):,.2f}", "#8b5cf6"
        ))

        # Özet tablo
        self.summary_table.setRowCount(3)
        rows = [
            ("İş Emirleri", stats.get('total', 0), stats.get('completed', 0),
             stats.get('in_progress', 0), stats.get('cancelled', 0)),
            ("Arıza Talepleri", stats.get('requests_total', 0), stats.get('requests_resolved', 0),
             stats.get('requests_pending', 0), 0),
            ("Periyodik Bakımlar", stats.get('preventive_total', 0), stats.get('preventive_done', 0),
             stats.get('preventive_pending', 0), 0),
        ]
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.summary_table.setItem(i, j, QTableWidgetItem(str(val)))

    def _refresh_cost(self, start_date, end_date):
        costs = self.service.get_equipment_cost_report(start_date, end_date)

        self.cost_table.setRowCount(len(costs))
        for i, cost in enumerate(costs):
            self.cost_table.setItem(i, 0, QTableWidgetItem(cost.get('equipment_name', '-')))
            self.cost_table.setItem(i, 1, QTableWidgetItem(f"₺{cost.get('material_cost', 0):,.2f}"))
            self.cost_table.setItem(i, 2, QTableWidgetItem(f"₺{cost.get('labor_cost', 0):,.2f}"))
            self.cost_table.setItem(i, 3, QTableWidgetItem(f"₺{cost.get('total_cost', 0):,.2f}"))
            self.cost_table.setItem(i, 4, QTableWidgetItem(str(cost.get('work_order_count', 0))))

    def _refresh_technician(self, start_date, end_date):
        techs = self.service.get_technician_performance(start_date, end_date)

        self.tech_table.setRowCount(len(techs))
        for i, tech in enumerate(techs):
            self.tech_table.setItem(i, 0, QTableWidgetItem(tech.get('name', '-')))
            self.tech_table.setItem(i, 1, QTableWidgetItem(str(tech.get('completed_count', 0))))
            self.tech_table.setItem(i, 2, QTableWidgetItem(f"{tech.get('total_hours', 0):.1f}"))
            self.tech_table.setItem(i, 3, QTableWidgetItem(f"{tech.get('avg_hours', 0):.1f}"))
            self.tech_table.setItem(i, 4, QTableWidgetItem(f"{tech.get('success_rate', 0):.1f}%"))

    def _refresh_overdue(self):
        overdue = self.service.get_overdue_maintenance_plans()

        self.overdue_table.setRowCount(len(overdue))
        today = datetime.now().date()

        for i, plan in enumerate(overdue):
            self.overdue_table.setItem(i, 0, QTableWidgetItem(
                plan.equipment.name if plan.equipment else '-'
            ))
            self.overdue_table.setItem(i, 1, QTableWidgetItem(plan.name))

            next_date = plan.next_maintenance_date
            self.overdue_table.setItem(i, 2, QTableWidgetItem(
                next_date.strftime("%d.%m.%Y") if next_date else '-'
            ))

            if next_date:
                days_overdue = (today - next_date.date()).days
                overdue_item = QTableWidgetItem(str(days_overdue))
                overdue_item.setForeground(Qt.GlobalColor.red)
                self.overdue_table.setItem(i, 3, overdue_item)
            else:
                self.overdue_table.setItem(i, 3, QTableWidgetItem('-'))

            self.overdue_table.setItem(i, 4, QTableWidgetItem(
                plan.equipment.criticality.value if plan.equipment and plan.equipment.criticality else '-'
            ))

    def _create_kpi_card(self, title: str, value: str, color: str) -> QWidget:
        """KPI kartı widget'ı oluşturur"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #6b7280; font-size: 12px;")
        card_layout.addWidget(lbl_title)

        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        card_layout.addWidget(lbl_value)

        return card


class KPIDashboardWidget(MaintenanceBaseWidget):
    """KPI Dashboard Widget'ı - MTBF, MTTR, Kullanılabilirlik"""

    def __init__(self, parent=None):
        super().__init__("Bakım KPI Dashboard", parent)
        self.setup_ui()

    def setup_ui(self):
        # Ekipman seçimi
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Ekipman:"))

        self.cmb_equipment = QComboBox()
        self.cmb_equipment.addItem("- Tüm Ekipmanlar -", None)
        equipments = self.service.get_equipment_list(active_only=True)
        for eq in equipments:
            self.cmb_equipment.addItem(f"{eq.code} - {eq.name}", eq.id)
        self.cmb_equipment.currentIndexChanged.connect(self.refresh_data)
        filter_layout.addWidget(self.cmb_equipment)

        filter_layout.addWidget(QLabel("Dönem:"))
        self.cmb_period = QComboBox()
        self.cmb_period.addItem("Son 30 Gün", 30)
        self.cmb_period.addItem("Son 90 Gün", 90)
        self.cmb_period.addItem("Son 1 Yıl", 365)
        self.cmb_period.currentIndexChanged.connect(self.refresh_data)
        filter_layout.addWidget(self.cmb_period)

        filter_layout.addStretch()
        self.layout.addLayout(filter_layout)

        # KPI Grid
        self.kpi_grid = QGridLayout()
        self.layout.addLayout(self.kpi_grid)

        # Alt detay tablosu
        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(6)
        self.detail_table.setHorizontalHeaderLabels([
            "Ekipman", "MTBF (saat)", "MTTR (saat)", "Kullanılabilirlik (%)",
            "Arıza Sayısı", "Toplam Duruş (saat)"
        ])
        self.detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.layout.addWidget(self.detail_table)

        self.refresh_data()

    def refresh_data(self):
        equipment_id = self.cmb_equipment.currentData()
        period_days = self.cmb_period.currentData()

        # KPI grid temizle
        while self.kpi_grid.count():
            item = self.kpi_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if equipment_id:
            # Tek ekipman KPI'ları
            kpis = self.service.get_equipment_kpis(equipment_id, period_days)
            self._display_single_equipment_kpis(kpis)
        else:
            # Tüm ekipmanlar özet
            all_kpis = self.service.get_all_equipment_kpis(period_days)
            self._display_all_equipment_kpis(all_kpis)

    def _display_single_equipment_kpis(self, kpis: dict):
        self.kpi_grid.addWidget(self._create_big_kpi_card(
            "MTBF", f"{kpis.get('mtbf', 0):.1f} saat",
            "Arızalar Arası Ortalama Süre", "#3b82f6"
        ), 0, 0)

        self.kpi_grid.addWidget(self._create_big_kpi_card(
            "MTTR", f"{kpis.get('mttr', 0):.1f} saat",
            "Ortalama Onarım Süresi", "#f97316"
        ), 0, 1)

        self.kpi_grid.addWidget(self._create_big_kpi_card(
            "Kullanılabilirlik", f"{kpis.get('availability', 100):.1f}%",
            "Çalışma Süresi Oranı", "#22c55e"
        ), 0, 2)

        self.kpi_grid.addWidget(self._create_big_kpi_card(
            "Arıza Sayısı", str(kpis.get('failure_count', 0)),
            "Dönem İçi Toplam", "#ef4444"
        ), 0, 3)

        # Tablo tek satır
        self.detail_table.setRowCount(0)

    def _display_all_equipment_kpis(self, all_kpis: list):
        # Ortalamalar
        avg_mtbf = sum(k.get('mtbf', 0) for k in all_kpis) / len(all_kpis) if all_kpis else 0
        avg_mttr = sum(k.get('mttr', 0) for k in all_kpis) / len(all_kpis) if all_kpis else 0
        avg_avail = sum(k.get('availability', 100) for k in all_kpis) / len(all_kpis) if all_kpis else 100
        total_failures = sum(k.get('failure_count', 0) for k in all_kpis)

        self.kpi_grid.addWidget(self._create_big_kpi_card(
            "Ort. MTBF", f"{avg_mtbf:.1f} saat", "Tüm Ekipmanlar", "#3b82f6"
        ), 0, 0)

        self.kpi_grid.addWidget(self._create_big_kpi_card(
            "Ort. MTTR", f"{avg_mttr:.1f} saat", "Tüm Ekipmanlar", "#f97316"
        ), 0, 1)

        self.kpi_grid.addWidget(self._create_big_kpi_card(
            "Ort. Kullanılabilirlik", f"{avg_avail:.1f}%", "Tüm Ekipmanlar", "#22c55e"
        ), 0, 2)

        self.kpi_grid.addWidget(self._create_big_kpi_card(
            "Toplam Arıza", str(total_failures), "Tüm Ekipmanlar", "#ef4444"
        ), 0, 3)

        # Detay tablosu
        self.detail_table.setRowCount(len(all_kpis))
        for i, kpi in enumerate(all_kpis):
            self.detail_table.setItem(i, 0, QTableWidgetItem(kpi.get('equipment_name', '-')))
            self.detail_table.setItem(i, 1, QTableWidgetItem(f"{kpi.get('mtbf', 0):.1f}"))
            self.detail_table.setItem(i, 2, QTableWidgetItem(f"{kpi.get('mttr', 0):.1f}"))

            avail_item = QTableWidgetItem(f"{kpi.get('availability', 100):.1f}")
            if kpi.get('availability', 100) < 90:
                avail_item.setForeground(Qt.GlobalColor.red)
            elif kpi.get('availability', 100) < 95:
                avail_item.setForeground(Qt.GlobalColor.darkYellow)
            self.detail_table.setItem(i, 3, avail_item)

            self.detail_table.setItem(i, 4, QTableWidgetItem(str(kpi.get('failure_count', 0))))
            self.detail_table.setItem(i, 5, QTableWidgetItem(f"{kpi.get('total_downtime', 0):.1f}"))

    def _create_big_kpi_card(self, title: str, value: str, subtitle: str, color: str) -> QWidget:
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setMinimumHeight(120)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 12px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #6b7280; font-size: 14px;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_title)

        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: bold;")
        lbl_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_value)

        lbl_subtitle = QLabel(subtitle)
        lbl_subtitle.setStyleSheet("color: #9ca3af; font-size: 11px;")
        lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_subtitle)

        return card


class CostAnalysisWidget(MaintenanceBaseWidget):
    """Maliyet Analizi Widget'ı"""

    def __init__(self, parent=None):
        super().__init__("Bakım Maliyet Analizi", parent)
        self.setup_ui()

    def setup_ui(self):
        # Bu widget ReportingWidget'ın maliyet tab'ına benzer
        # ama daha detaylı analiz için ayrı bir ekran olarak tasarlanabilir
        info_label = QLabel("Detaylı maliyet analizi için Raporlar > Maliyet Analizi sekmesini kullanın.")
        info_label.setStyleSheet("color: #6b7280; font-size: 14px;")
        self.layout.addWidget(info_label)
