"""
Bakım Modülü - Periyodik Bakım Planları
"""

from typing import Optional
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QSpinBox,
    QCheckBox,
    QGroupBox,
    QCalendarWidget,
    QSplitter,
    QListWidget,
    QListWidgetItem,
    QMenu,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QTextCharFormat, QColor, QAction
import qtawesome as qta

from config.icons import ICONS
from ui.components.base_list_page import BaseListPage
from ui.components.page_header import PageHeader
from ui.components.enhanced_table import ColumnConfig
from database.base import get_session
from modules.maintenance.services import MaintenanceService
from modules.maintenance.views.base import MaintenanceBaseWidget


class MaintenancePlanWidget(BaseListPage):
    """Periyodik Bakım Planları Widget'ı"""

    def __init__(self, parent=None):
        self.db_session = get_session()
        self.service = MaintenanceService(self.db_session)

        columns = [
            ColumnConfig(
                "equipment", "Ekipman", width=200, filterable=True, stretch=True
            ),
            ColumnConfig("name", "Plan Adı", width=200, filterable=True),
            ColumnConfig("frequency", "Sıklık", width=120),
            ColumnConfig("last", "Son Bakım", width=120),
            ColumnConfig("next", "Sonraki Bakım", width=120),
            ColumnConfig("auto", "Otomatik", width=100, filter_type="enum"),
            ColumnConfig("status", "Durum", width=100, filter_type="enum"),
            ColumnConfig("remaining", "Kalan Gün", width=120),
        ]

        super().__init__(
            title="Periyodik Bakım Planları",
            icon=ICONS.CALENDAR,
            table_id="maintenance_plans",
            columns=columns,
            show_add=True,
            add_text="Yeni Plan Oluştur",
            parent=parent,
        )

        self._setup_extra_ui()
        self.add_clicked.connect(self.create_plan)
        self.refresh_requested.connect(self.refresh_data)

    def closeEvent(self, event):
        if hasattr(self, "db_session") and self.db_session:
            self.db_session.close()
        super().closeEvent(event)

    def _setup_extra_ui(self):
        h_layout = self.header.header_layout()

        self.chk_active = QCheckBox("Sadece Aktifler")
        self.chk_active.setChecked(True)
        self.chk_active.stateChanged.connect(self.refresh_data)
        self.chk_active.setFixedHeight(32)
        h_layout.addWidget(self.chk_active)

        h_layout.addStretch()

        # Context Menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        self.table.set_filter_options("status", ["Aktif", "Pasif"])
        self.table.set_filter_options("auto", ["Evet", "Hayır"])

    def refresh_data(self):
        plans = self.service.get_maintenance_plans(
            active_only=self.chk_active.isChecked()
        )
        self.load_data(plans)

    def load_data(self, plans):
        self.table.setRowCount(len(plans))
        today = datetime.now().date()

        for i, p in enumerate(plans):
            # Equipment
            it = QTableWidgetItem(p.equipment.name if p.equipment else "-")
            it.setData(Qt.ItemDataRole.UserRole, p.id)
            self.table.setItem(i, 0, it)

            # Name
            self.table.setItem(i, 1, QTableWidgetItem(p.name))

            # Frequency
            self.table.setItem(
                i, 2, QTableWidgetItem(f"Her {p.frequency_value} {p.frequency_type}")
            )

            # Last Maintenance
            last_date = (
                p.last_maintenance_date.strftime("%d.%m.%Y")
                if p.last_maintenance_date
                else "-"
            )
            self.table.setItem(i, 3, QTableWidgetItem(last_date))

            # Next Maintenance
            dt = p.next_maintenance_date
            it = QTableWidgetItem(dt.strftime("%d.%m.%Y") if dt else "-")
            if dt and dt.date() < today:
                it.setForeground(Qt.GlobalColor.red)
            elif dt and dt.date() <= today + timedelta(days=7):
                it.setForeground(Qt.GlobalColor.darkYellow)
            self.table.setItem(i, 4, it)

            # Auto
            self.table.setItem(
                i,
                5,
                QTableWidgetItem("Evet" if p.auto_generate_work_order else "Hayır"),
            )

            # Status
            it = QTableWidgetItem("Aktif" if p.is_active else "Pasif")
            it.setForeground(QColor("#10b981" if p.is_active else "#6b7280"))
            self.table.setItem(i, 6, it)

            # Remaining
            if dt:
                days = (dt.date() - today).days
                it = QTableWidgetItem(
                    f"{days} gün" if days >= 0 else f"{abs(days)} gün gecikti!"
                )
                it.setForeground(
                    Qt.GlobalColor.red
                    if days < 0
                    else (
                        Qt.GlobalColor.darkYellow
                        if days <= 7
                        else Qt.GlobalColor.white  # Assuming dark theme or high contrast needed, using default enhanced table color logic would be better but this matches previous logic
                    )
                )
                self.table.setItem(i, 7, it)
            else:
                self.table.setItem(i, 7, QTableWidgetItem("-"))

        self.update_count(len(plans))

    def get_selected_plan_id(self) -> Optional[int]:
        return self.table.get_selected_id()

    def _show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        menu = QMenu(self)

        edit_action = QAction(qta.icon(ICONS.EDIT, color="#f59e0b"), "Düzenle", self)
        edit_action.triggered.connect(self.edit_plan)
        menu.addAction(edit_action)

        generate_action = QAction(
            qta.icon(ICONS.ADD, color="#22c55e"), "İş Emri Oluştur", self
        )
        generate_action.triggered.connect(self.generate_work_order)
        menu.addAction(generate_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def create_plan(self):
        if PlanDialog(self.service, self).exec():
            self.refresh_data()

    def edit_plan(self):
        pid = self.get_selected_plan_id()
        if not pid:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir plan seçin.")
            return
        p = self.service.get_maintenance_plan_by_id(pid)
        if PlanDialog(self.service, self, plan=p).exec():
            self.refresh_data()

    def generate_work_order(self):
        pid = self.get_selected_plan_id()
        if not pid:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir plan seçin.")
            return
        try:
            wo = self.service.generate_work_order_from_plan(pid)
            QMessageBox.information(
                self, "Başarılı", f"İş emri oluşturuldu: {wo.order_no}"
            )
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    # Interface Implementation
    def get_filters(self) -> dict:
        return {
            "status": (
                "active" if self.chk_active.isChecked() else "all"
            ),  # Simplified representation
        }

    def get_search_text(self) -> str:
        return self.header.get_search_text()


class PlanDialog(QDialog):
    """Bakım Planı Ekleme/Düzenleme Dialogu"""

    def __init__(self, service, parent=None, plan=None):
        super().__init__(parent)
        self.service, self.plan = service, plan
        self.setWindowTitle("Plan Düzenle" if plan else "Yeni Bakım Planı")
        self.setMinimumSize(500, 550)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.cmb_eq = QComboBox()
        for eq in self.service.get_equipment_list(active_only=True):
            self.cmb_eq.addItem(f"{eq.code} - {eq.name}", eq.id)
        form.addRow("Ekipman*:", self.cmb_eq)
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Örn: Yağ Değişimi, Kayış Kontrolü")
        form.addRow("Plan Adı*:", self.inp_name)
        self.txt_desc = QTextEdit()
        self.txt_desc.setMaximumHeight(80)
        self.txt_desc.setPlaceholderText("Plan açıklaması...")
        form.addRow("Açıklama:", self.txt_desc)
        layout.addLayout(form)

        freq_group = QGroupBox("Bakım Sıklığı")
        freq_layout = QFormLayout(freq_group)
        freq_row = QHBoxLayout()
        self.spin_freq = QSpinBox()
        self.spin_freq.setRange(1, 365)
        self.spin_freq.setValue(1)
        freq_row.addWidget(QLabel("Her"))
        freq_row.addWidget(self.spin_freq)
        self.cmb_freq_type = QComboBox()
        for l, c in [
            ("Gün", "daily"),
            ("Hafta", "weekly"),
            ("Ay", "monthly"),
            ("Yıl", "yearly"),
        ]:
            self.cmb_freq_type.addItem(l, c)
        self.cmb_freq_type.setCurrentIndex(2)
        freq_row.addWidget(self.cmb_freq_type)
        freq_row.addStretch()
        freq_layout.addRow("Periyot:", freq_row)
        self.chk_counter = QCheckBox("Sayaç/Çalışma Saati Bazlı")
        freq_layout.addRow("", self.chk_counter)
        counter_row = QHBoxLayout()
        self.spin_counter = QSpinBox()
        self.spin_counter.setRange(1, 99999)
        self.spin_counter.setValue(500)
        self.spin_counter.setEnabled(False)
        counter_row.addWidget(QLabel("Her"))
        counter_row.addWidget(self.spin_counter)
        counter_row.addWidget(QLabel("saat çalışmada"))
        counter_row.addStretch()
        freq_layout.addRow("Sayaç Aralığı:", counter_row)
        self.chk_counter.stateChanged.connect(
            lambda s: self.spin_counter.setEnabled(s == Qt.CheckState.Checked.value)
        )
        layout.addWidget(freq_group)

        auto_group = QGroupBox("Otomatik İş Emri")
        auto_layout = QFormLayout(auto_group)
        self.chk_auto = QCheckBox("Otomatik iş emri oluştur")
        self.chk_auto.setChecked(True)
        auto_layout.addRow("", self.chk_auto)
        self.spin_lead = QSpinBox()
        self.spin_lead.setRange(0, 30)
        self.spin_lead.setValue(7)
        auto_layout.addRow("Kaç gün önce:", self.spin_lead)
        self.cmb_checklist = QComboBox()
        self.cmb_checklist.addItem("- Kontrol Listesi Yok -", None)
        for cl in self.service.get_all_checklists():
            self.cmb_checklist.addItem(cl.name, cl.id)
        auto_layout.addRow("Kontrol Listesi:", self.cmb_checklist)
        layout.addWidget(auto_group)

        if self.plan:
            self.load_data()
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def load_data(self):
        p = self.plan
        self.cmb_eq.setCurrentIndex(self.cmb_eq.findData(p.equipment_id))
        self.inp_name.setText(p.name)
        self.txt_desc.setPlainText(p.description or "")
        self.spin_freq.setValue(p.frequency_value)
        self.cmb_freq_type.setCurrentIndex(
            self.cmb_freq_type.findData(p.frequency_type)
        )
        self.chk_counter.setChecked(p.is_counter_based or False)
        self.spin_counter.setValue(p.counter_interval or 500)
        self.chk_auto.setChecked(p.auto_generate_work_order or False)
        self.spin_lead.setValue(p.lead_days or 7)
        if p.checklist_id:
            self.cmb_checklist.setCurrentIndex(
                self.cmb_checklist.findData(p.checklist_id)
            )

    def accept(self):
        eid, name = self.cmb_eq.currentData(), self.inp_name.text().strip()
        if not eid or not name:
            QMessageBox.warning(self, "Uyarı", "Ekipman ve Plan Adı zorunludur.")
            return
        try:
            data = {
                "equipment_id": eid,
                "name": name,
                "description": self.txt_desc.toPlainText().strip() or None,
                "frequency_type": self.cmb_freq_type.currentData(),
                "frequency_value": self.spin_freq.value(),
                "is_counter_based": self.chk_counter.isChecked(),
                "counter_interval": (
                    self.spin_counter.value() if self.chk_counter.isChecked() else None
                ),
                "auto_generate_work_order": self.chk_auto.isChecked(),
                "lead_days": self.spin_lead.value(),
                "checklist_id": self.cmb_checklist.currentData(),
            }
            if self.plan:
                self.service.update_maintenance_plan(self.plan.id, **data)
            else:
                self.service.create_maintenance_plan(**data)
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class MaintenanceCalendarWidget(MaintenanceBaseWidget):
    """Bakım Takvimi Widget'ı"""

    def __init__(self, parent=None):
        super().__init__("Bakım Takvimi", parent)
        self.setup_ui()

    def setup_ui(self):
        self.header = PageHeader(
            title="Bakım Takvimi",
            icon=ICONS.CALENDAR,
            show_search=False,
            show_add=False,
            parent=self,
        )
        self.header.refresh_clicked.connect(self.mark_calendar)
        self.layout.addWidget(self.header)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.layout.addWidget(splitter)
        left = QWidget()
        l_layout = QVBoxLayout(left)
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.on_date_selected)
        l_layout.addWidget(self.calendar)
        splitter.addWidget(left)
        right = QWidget()
        r_layout = QVBoxLayout(right)
        self.lbl_selected = QLabel("Tarih seçin")
        self.lbl_selected.setStyleSheet("font-size: 16px; font-weight: bold;")
        r_layout.addWidget(self.lbl_selected)
        self.day_list = QListWidget()
        r_layout.addWidget(self.day_list)
        splitter.addWidget(right)
        splitter.setSizes([400, 300])
        self.mark_calendar()

    def mark_calendar(self):
        plans = self.service.get_maintenance_plans(active_only=True)
        fmt_ovr, fmt_upc, fmt_nrm = (
            QTextCharFormat(),
            QTextCharFormat(),
            QTextCharFormat(),
        )
        fmt_ovr.setBackground(QColor("#fee2e2"))
        fmt_upc.setBackground(QColor("#fef3c7"))
        fmt_nrm.setBackground(QColor("#dcfce7"))
        today = QDate.currentDate()
        for p in plans:
            if p.next_maintenance_date:
                nd = QDate(
                    p.next_maintenance_date.year,
                    p.next_maintenance_date.month,
                    p.next_maintenance_date.day,
                )
                if nd < today:
                    self.calendar.setDateTextFormat(nd, fmt_ovr)
                elif nd <= today.addDays(7):
                    self.calendar.setDateTextFormat(nd, fmt_upc)
                else:
                    self.calendar.setDateTextFormat(nd, fmt_nrm)

    def on_date_selected(self, date: QDate):
        self.lbl_selected.setText(date.toString("dd.MM.yyyy"))
        self.day_list.clear()
        py_date = datetime(date.year(), date.month(), date.day())
        plans = self.service.get_plans_by_date(py_date)
        if not plans:
            it = QListWidgetItem("Bu tarihte planlanmış bakım yok.")
            it.setForeground(Qt.GlobalColor.gray)
            self.day_list.addItem(it)
        else:
            for p in plans:
                self.day_list.addItem(QListWidgetItem(f"[{p.equipment.code}] {p.name}"))
