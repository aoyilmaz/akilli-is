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
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
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
    QFrame,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QTextCharFormat, QColor

from modules.maintenance.views.base import MaintenanceBaseWidget


class MaintenancePlanWidget(MaintenanceBaseWidget):
    """Periyodik Bakım Planları Widget'ı"""

    def __init__(self, parent=None):
        super().__init__("Periyodik Bakım Planları", parent)
        self.setup_ui()

    def setup_ui(self):
        # Üst Butonlar
        btn_layout = QHBoxLayout()

        self.btn_new = QPushButton("Yeni Plan Oluştur")
        self.btn_new.setStyleSheet(
            "background-color: #007acc; color: white; padding: 8px 16px; border-radius: 4px;"
        )
        self.btn_new.clicked.connect(self.create_plan)
        btn_layout.addWidget(self.btn_new)

        self.btn_edit = QPushButton("Düzenle")
        self.btn_edit.clicked.connect(self.edit_plan)
        btn_layout.addWidget(self.btn_edit)

        self.btn_generate = QPushButton("Seçili Plandan İş Emri Oluştur")
        self.btn_generate.setStyleSheet(
            "background-color: #22c55e; color: white; padding: 8px 16px; border-radius: 4px;"
        )
        self.btn_generate.clicked.connect(self.generate_work_order)
        btn_layout.addWidget(self.btn_generate)

        btn_layout.addStretch()

        # Filtre
        self.chk_active = QCheckBox("Sadece Aktifler")
        self.chk_active.setChecked(True)
        self.chk_active.stateChanged.connect(self.refresh_data)
        btn_layout.addWidget(self.chk_active)

        self.layout.addLayout(btn_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Ekipman", "Plan Adı", "Sıklık", "Son Bakım", "Sonraki Bakım",
            "Otomatik İş Emri", "Durum", "Kalan Gün"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.layout.addWidget(self.table)

        self.refresh_data()

    def refresh_data(self):
        active_only = self.chk_active.isChecked()
        plans = self.service.get_maintenance_plans(active_only=active_only)

        self.table.setRowCount(len(plans))
        today = datetime.now().date()

        for i, plan in enumerate(plans):
            self.table.setItem(i, 0, QTableWidgetItem(
                plan.equipment.name if plan.equipment else "-"
            ))
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, plan.id)

            self.table.setItem(i, 1, QTableWidgetItem(plan.name))

            # Sıklık
            freq_text = self._format_frequency(plan.frequency_type, plan.frequency_value)
            self.table.setItem(i, 2, QTableWidgetItem(freq_text))

            # Son bakım
            self.table.setItem(i, 3, QTableWidgetItem(
                plan.last_maintenance_date.strftime("%d.%m.%Y") if plan.last_maintenance_date else "-"
            ))

            # Sonraki bakım
            next_date = plan.next_maintenance_date
            next_item = QTableWidgetItem(
                next_date.strftime("%d.%m.%Y") if next_date else "-"
            )
            if next_date and next_date.date() < today:
                next_item.setForeground(Qt.GlobalColor.red)
            elif next_date and next_date.date() <= today + timedelta(days=7):
                next_item.setForeground(Qt.GlobalColor.darkYellow)
            self.table.setItem(i, 4, next_item)

            # Otomatik
            self.table.setItem(i, 5, QTableWidgetItem(
                "Evet" if plan.auto_generate_work_order else "Hayır"
            ))

            # Durum
            status_item = QTableWidgetItem("Aktif" if plan.is_active else "Pasif")
            if not plan.is_active:
                status_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(i, 6, status_item)

            # Kalan gün
            if next_date:
                days_left = (next_date.date() - today).days
                days_item = QTableWidgetItem(f"{days_left} gün")
                if days_left < 0:
                    days_item.setForeground(Qt.GlobalColor.red)
                    days_item.setText(f"{abs(days_left)} gün gecikti!")
                elif days_left <= 7:
                    days_item.setForeground(Qt.GlobalColor.darkYellow)
                self.table.setItem(i, 7, days_item)
            else:
                self.table.setItem(i, 7, QTableWidgetItem("-"))

    def _format_frequency(self, freq_type: str, freq_value: int) -> str:
        """Sıklık metnini formatla"""
        freq_labels = {
            "daily": "gün",
            "weekly": "hafta",
            "monthly": "ay",
            "yearly": "yıl",
        }
        unit = freq_labels.get(freq_type, freq_type)
        return f"Her {freq_value} {unit}"

    def get_selected_plan_id(self) -> Optional[int]:
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        return self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

    def create_plan(self):
        dialog = PlanDialog(self.service, self)
        if dialog.exec():
            self.refresh_data()

    def edit_plan(self):
        plan_id = self.get_selected_plan_id()
        if not plan_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir plan seçin.")
            return

        plan = self.service.get_maintenance_plan_by_id(plan_id)
        dialog = PlanDialog(self.service, self, plan=plan)
        if dialog.exec():
            self.refresh_data()

    def generate_work_order(self):
        plan_id = self.get_selected_plan_id()
        if not plan_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir plan seçin.")
            return

        try:
            wo = self.service.generate_work_order_from_plan(plan_id)
            QMessageBox.information(
                self, "Başarılı",
                f"İş emri oluşturuldu: {wo.order_no}"
            )
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class PlanDialog(QDialog):
    """Bakım Planı Ekleme/Düzenleme Dialogu"""

    def __init__(self, service, parent=None, plan=None):
        super().__init__(parent)
        self.service = service
        self.plan = plan

        self.setWindowTitle("Plan Düzenle" if plan else "Yeni Bakım Planı")
        self.setMinimumSize(500, 550)

        main_layout = QVBoxLayout(self)

        # Form
        form = QFormLayout()

        self.cmb_equipment = QComboBox()
        equipments = self.service.get_equipment_list(active_only=True)
        for eq in equipments:
            self.cmb_equipment.addItem(f"{eq.code} - {eq.name}", eq.id)
        form.addRow("Ekipman*:", self.cmb_equipment)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Örn: Yağ Değişimi, Kayış Kontrolü")
        form.addRow("Plan Adı*:", self.inp_name)

        self.txt_desc = QTextEdit()
        self.txt_desc.setMaximumHeight(80)
        self.txt_desc.setPlaceholderText("Plan açıklaması...")
        form.addRow("Açıklama:", self.txt_desc)

        main_layout.addLayout(form)

        # Sıklık grubu
        freq_group = QGroupBox("Bakım Sıklığı")
        freq_layout = QFormLayout(freq_group)

        freq_row = QHBoxLayout()
        self.spin_freq = QSpinBox()
        self.spin_freq.setRange(1, 365)
        self.spin_freq.setValue(1)
        freq_row.addWidget(QLabel("Her"))
        freq_row.addWidget(self.spin_freq)

        self.cmb_freq_type = QComboBox()
        self.cmb_freq_type.addItem("Gün", "daily")
        self.cmb_freq_type.addItem("Hafta", "weekly")
        self.cmb_freq_type.addItem("Ay", "monthly")
        self.cmb_freq_type.addItem("Yıl", "yearly")
        self.cmb_freq_type.setCurrentIndex(2)  # Ay seçili
        freq_row.addWidget(self.cmb_freq_type)
        freq_row.addStretch()

        freq_layout.addRow("Periyot:", freq_row)

        # Sayaç bazlı
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
            lambda state: self.spin_counter.setEnabled(state == Qt.CheckState.Checked.value)
        )

        main_layout.addWidget(freq_group)

        # Otomasyon grubu
        auto_group = QGroupBox("Otomatik İş Emri")
        auto_layout = QFormLayout(auto_group)

        self.chk_auto = QCheckBox("Otomatik iş emri oluştur")
        self.chk_auto.setChecked(True)
        auto_layout.addRow("", self.chk_auto)

        self.spin_lead_days = QSpinBox()
        self.spin_lead_days.setRange(0, 30)
        self.spin_lead_days.setValue(7)
        auto_layout.addRow("Kaç gün önce:", self.spin_lead_days)

        # Kontrol listesi
        self.cmb_checklist = QComboBox()
        self.cmb_checklist.addItem("- Kontrol Listesi Yok -", None)
        checklists = self.service.get_all_checklists()
        for cl in checklists:
            self.cmb_checklist.addItem(cl.name, cl.id)
        auto_layout.addRow("Kontrol Listesi:", self.cmb_checklist)

        main_layout.addWidget(auto_group)

        # Mevcut veriyi yükle
        if self.plan:
            self.load_plan_data()

        # Buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)

    def load_plan_data(self):
        """Mevcut plan verilerini forma yükle"""
        p = self.plan

        idx = self.cmb_equipment.findData(p.equipment_id)
        if idx >= 0:
            self.cmb_equipment.setCurrentIndex(idx)

        self.inp_name.setText(p.name)
        self.txt_desc.setPlainText(p.description or "")

        self.spin_freq.setValue(p.frequency_value)
        idx = self.cmb_freq_type.findData(p.frequency_type)
        if idx >= 0:
            self.cmb_freq_type.setCurrentIndex(idx)

        self.chk_counter.setChecked(p.is_counter_based or False)
        if p.counter_interval:
            self.spin_counter.setValue(p.counter_interval)

        self.chk_auto.setChecked(p.auto_generate_work_order or False)
        self.spin_lead_days.setValue(p.lead_days or 7)

        if p.checklist_id:
            idx = self.cmb_checklist.findData(p.checklist_id)
            if idx >= 0:
                self.cmb_checklist.setCurrentIndex(idx)

    def accept(self):
        equipment_id = self.cmb_equipment.currentData()
        name = self.inp_name.text().strip()

        if not equipment_id or not name:
            QMessageBox.warning(self, "Uyarı", "Ekipman ve plan adı zorunludur.")
            return

        try:
            data = {
                "equipment_id": equipment_id,
                "name": name,
                "description": self.txt_desc.toPlainText().strip() or None,
                "frequency_type": self.cmb_freq_type.currentData(),
                "frequency_value": self.spin_freq.value(),
                "is_counter_based": self.chk_counter.isChecked(),
                "counter_interval": self.spin_counter.value() if self.chk_counter.isChecked() else None,
                "auto_generate_work_order": self.chk_auto.isChecked(),
                "lead_days": self.spin_lead_days.value(),
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
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.layout.addWidget(splitter)

        # Sol: Takvim
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.on_date_selected)
        left_layout.addWidget(self.calendar)

        splitter.addWidget(left_widget)

        # Sağ: Seçili günün bakımları
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.lbl_selected_date = QLabel("Tarih seçin")
        self.lbl_selected_date.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(self.lbl_selected_date)

        self.day_list = QListWidget()
        right_layout.addWidget(self.day_list)

        splitter.addWidget(right_widget)
        splitter.setSizes([400, 300])

        # Takvimi işaretle
        self.mark_calendar()

    def mark_calendar(self):
        """Bakım planlarını takvimde işaretle"""
        plans = self.service.get_maintenance_plans(active_only=True)

        # Kırmızı: Gecikmiş, Sarı: Yaklaşan, Yeşil: Normal
        format_overdue = QTextCharFormat()
        format_overdue.setBackground(QColor("#fee2e2"))

        format_upcoming = QTextCharFormat()
        format_upcoming.setBackground(QColor("#fef3c7"))

        format_normal = QTextCharFormat()
        format_normal.setBackground(QColor("#dcfce7"))

        today = QDate.currentDate()

        for plan in plans:
            if plan.next_maintenance_date:
                next_date = QDate(
                    plan.next_maintenance_date.year,
                    plan.next_maintenance_date.month,
                    plan.next_maintenance_date.day
                )

                if next_date < today:
                    self.calendar.setDateTextFormat(next_date, format_overdue)
                elif next_date <= today.addDays(7):
                    self.calendar.setDateTextFormat(next_date, format_upcoming)
                else:
                    self.calendar.setDateTextFormat(next_date, format_normal)

    def on_date_selected(self, date: QDate):
        """Tarih seçildiğinde o günün bakımlarını göster"""
        self.lbl_selected_date.setText(date.toString("dd.MM.yyyy"))
        self.day_list.clear()

        # Seçili tarihteki bakımları getir
        py_date = datetime(date.year(), date.month(), date.day())
        plans = self.service.get_plans_by_date(py_date)

        if not plans:
            item = QListWidgetItem("Bu tarihte planlanmış bakım yok.")
            item.setForeground(Qt.GlobalColor.gray)
            self.day_list.addItem(item)
            return

        for plan in plans:
            item = QListWidgetItem(
                f"[{plan.equipment.code}] {plan.name}"
            )
            self.day_list.addItem(item)
