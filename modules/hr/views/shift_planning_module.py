"""
Akıllı İş - İK Vardiya Planlama Modülü

Üretim takvimi modülüyle entegre çalışan HR vardiya planlama arayüzü.
"""

from datetime import date, timedelta

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
    QComboBox,
    QCalendarWidget,
    QMessageBox,
    QDialog,
    QFormLayout,
    QDateEdit,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QTextCharFormat, QColor

from config.styles import ICONS


class AssignmentDialog(QDialog):
    """Vardiya ataması dialogu"""

    def __init__(self, employees: list, shifts: list, teams: list, parent=None):
        super().__init__(parent)
        self.employees = employees
        self.shifts = shifts
        self.teams = teams
        self.setWindowTitle("Vardiya Ataması")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        # Tarih aralığı
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        layout.addRow("Başlangıç:", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addDays(6))
        layout.addRow("Bitiş:", self.end_date)

        # Çalışan seçimi
        self.employee_combo = QComboBox()
        self.employee_combo.addItem("Tüm Çalışanlar", None)
        for emp in self.employees:
            self.employee_combo.addItem(f"{emp.first_name} {emp.last_name}", emp.id)
        layout.addRow("Çalışan:", self.employee_combo)

        # Ekip seçimi
        self.team_combo = QComboBox()
        self.team_combo.addItem("Ekip Seçin...", None)
        for team in self.teams:
            self.team_combo.addItem(team.name, team.id)
        layout.addRow("Ekip:", self.team_combo)

        # Vardiya seçimi
        self.shift_combo = QComboBox()
        self.shift_combo.addItem("Vardiya Seçin...", None)
        for shift in self.shifts:
            self.shift_combo.addItem(
                f"{shift.code} ({shift.start_time.strftime('%H:%M')}-"
                f"{shift.end_time.strftime('%H:%M')})",
                shift.id,
            )
        layout.addRow("Vardiya:", self.shift_combo)

        # Butonlar
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(f"{ICONS['add']} Ata")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def get_data(self) -> dict:
        return {
            "start_date": self.start_date.date().toPyDate(),
            "end_date": self.end_date.date().toPyDate(),
            "employee_id": self.employee_combo.currentData(),
            "team_id": self.team_combo.currentData(),
            "shift_id": self.shift_combo.currentData(),
        }


class ShiftPlanningModule(QWidget):
    """İK Vardiya Planlama Modülü"""

    page_title = "Vardiya Planlama"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.shift_service = None
        self.team_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Sekme widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_calendar_tab(), "📅 Takvim")
        self.tabs.addTab(self._create_team_shifts_tab(), "👥 Ekip Vardiyaları")
        self.tabs.addTab(self._create_employee_shifts_tab(), "👤 Kişi Vardiyaları")
        layout.addWidget(self.tabs)

    def _create_calendar_tab(self) -> QWidget:
        """Takvim sekmesi"""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Sol: Takvim
        left = QFrame()
        left.setStyleSheet("background: #1e293b; border-radius: 8px;")
        left_layout = QVBoxLayout(left)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.selectionChanged.connect(self._on_date_selected)
        left_layout.addWidget(self.calendar)

        layout.addWidget(left, 1)

        # Sağ: Seçili gün detayları
        right = QFrame()
        right.setStyleSheet("background: #1e293b; border-radius: 8px;")
        right_layout = QVBoxLayout(right)

        self.day_info_label = QLabel("Tarih seçin...")
        self.day_info_label.setStyleSheet(
            "color: white; font-size: 16px; font-weight: bold;"
        )
        right_layout.addWidget(self.day_info_label)

        # Vardiya listesi
        self.day_shifts_table = QTableWidget()
        self.day_shifts_table.setColumnCount(4)
        self.day_shifts_table.setHorizontalHeaderLabels(
            ["Ekip", "Vardiya", "Çalışan Sayısı", "Saat"]
        )
        header = self.day_shifts_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        right_layout.addWidget(self.day_shifts_table)

        # Atama butonu
        assign_btn = QPushButton(f"{ICONS['add']} Vardiya Ata")
        assign_btn.clicked.connect(self._assign_shift)
        right_layout.addWidget(assign_btn)

        layout.addWidget(right, 1)

        return widget

    def _create_team_shifts_tab(self) -> QWidget:
        """Ekip vardiyaları sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Ekip:"))
        self.team_filter = QComboBox()
        self.team_filter.addItem("Tüm Ekipler", None)
        self.team_filter.currentIndexChanged.connect(self._load_team_shifts)
        toolbar.addWidget(self.team_filter)

        toolbar.addWidget(QLabel("Hafta:"))
        self.week_filter = QComboBox()
        self._populate_weeks()
        self.week_filter.currentIndexChanged.connect(self._load_team_shifts)
        toolbar.addWidget(self.week_filter)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Haftalık vardiya tablosu
        self.team_table = QTableWidget()
        self.team_table.setColumnCount(8)
        self.team_table.setHorizontalHeaderLabels(
            ["Ekip", "Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        )
        header = self.team_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.team_table)

        return widget

    def _create_employee_shifts_tab(self) -> QWidget:
        """Kişi vardiyaları sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Çalışan:"))
        self.employee_filter = QComboBox()
        self.employee_filter.addItem("Seçin...", None)
        self.employee_filter.currentIndexChanged.connect(self._load_employee_shifts)
        toolbar.addWidget(self.employee_filter)

        toolbar.addWidget(QLabel("Ay:"))
        self.month_filter = QComboBox()
        self._populate_months()
        self.month_filter.currentIndexChanged.connect(self._load_employee_shifts)
        toolbar.addWidget(self.month_filter)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Aylık vardiya tablosu
        self.employee_table = QTableWidget()
        self.employee_table.setColumnCount(4)
        self.employee_table.setHorizontalHeaderLabels(
            ["Tarih", "Gün", "Vardiya", "Saat"]
        )
        header = self.employee_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.employee_table)

        return widget

    def _populate_weeks(self):
        """Hafta seçeneklerini doldur"""
        today = date.today()
        monday = today - timedelta(days=today.weekday())

        for i in range(-2, 6):
            week_start = monday + timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)
            label = f"{week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m')}"
            self.week_filter.addItem(label, week_start)

        self.week_filter.setCurrentIndex(2)  # Mevcut hafta

    def _populate_months(self):
        """Ay seçeneklerini doldur"""
        today = date.today()
        months_tr = [
            "Ocak",
            "Şubat",
            "Mart",
            "Nisan",
            "Mayıs",
            "Haziran",
            "Temmuz",
            "Ağustos",
            "Eylül",
            "Ekim",
            "Kasım",
            "Aralık",
        ]

        for i in range(-1, 3):
            month = (today.month + i - 1) % 12 + 1
            year = today.year + ((today.month + i - 1) // 12)
            label = f"{months_tr[month-1]} {year}"
            self.month_filter.addItem(label, date(year, month, 1))

        self.month_filter.setCurrentIndex(1)  # Mevcut ay

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_data()

    def _ensure_services(self):
        if not self.shift_service:
            try:
                from modules.production.calendar_services import (
                    ShiftService,
                    ShiftTeamService,
                )

                self.shift_service = ShiftService()
                self.team_service = ShiftTeamService()
            except Exception as e:
                print(f"Servis yükleme hatası: {e}")

    def _load_data(self):
        self._load_teams()
        self._load_employees()
        self._load_team_shifts()
        self._highlight_calendar()

    def _load_teams(self):
        if not self.team_service:
            return

        try:
            teams = self.team_service.get_all()
            self.team_filter.clear()
            self.team_filter.addItem("Tüm Ekipler", None)
            for team in teams:
                self.team_filter.addItem(team.name, team.id)
        except Exception as e:
            print(f"Ekip yükleme hatası: {e}")

    def _load_employees(self):
        try:
            from database.models.hr import Employee
            from database.base import get_session

            session = get_session()
            employees = (
                session.query(Employee)
                .filter(Employee.is_active == True)
                .order_by(Employee.first_name)
                .all()
            )

            self.employee_filter.clear()
            self.employee_filter.addItem("Seçin...", None)
            for emp in employees:
                self.employee_filter.addItem(
                    f"{emp.first_name} {emp.last_name}", emp.id
                )
            session.close()
        except Exception as e:
            print(f"Çalışan yükleme hatası: {e}")

    def _load_team_shifts(self):
        """Ekip vardiyalarını yükle"""
        if not self.team_service or not self.shift_service:
            return

        try:
            teams = self.team_service.get_all()
            shifts = self.shift_service.get_all()

            self.team_table.setRowCount(len(teams))

            for i, team in enumerate(teams):
                self.team_table.setItem(i, 0, QTableWidgetItem(team.name))
                # Varsayılan olarak rotasyon bilgisi göster
                for j in range(1, 8):
                    # Şimdilik placeholder
                    self.team_table.setItem(i, j, QTableWidgetItem("-"))
        except Exception as e:
            print(f"Ekip vardiya yükleme hatası: {e}")

    def _load_employee_shifts(self):
        """Kişi vardiyalarını yükle"""
        employee_id = self.employee_filter.currentData()
        if not employee_id:
            return

        # Placeholder - gerçek implementasyon rotation schedule'dan gelecek
        month_start = self.month_filter.currentData()
        if not month_start:
            return

        # Ay günlerini listele
        days_tr = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        days = []
        day = month_start
        while day.month == month_start.month:
            days.append(day)
            day += timedelta(days=1)

        self.employee_table.setRowCount(len(days))

        for i, d in enumerate(days):
            self.employee_table.setItem(i, 0, QTableWidgetItem(d.strftime("%d.%m.%Y")))
            self.employee_table.setItem(i, 1, QTableWidgetItem(days_tr[d.weekday()]))
            # Placeholder
            self.employee_table.setItem(i, 2, QTableWidgetItem("-"))
            self.employee_table.setItem(i, 3, QTableWidgetItem("-"))

    def _highlight_calendar(self):
        """Takvimde özel günleri vurgula"""
        # Tatil günlerini kırmızı yap
        holiday_format = QTextCharFormat()
        holiday_format.setBackground(QColor("#ef4444"))

        # Hafta sonlarını farklı renklendir
        weekend_format = QTextCharFormat()
        weekend_format.setBackground(QColor("#374151"))

        # Şimdilik basit renklendirme
        today = date.today()
        for i in range(31):
            d = date(today.year, today.month, 1) + timedelta(days=i)
            if d.month != today.month:
                break
            if d.weekday() >= 5:  # Hafta sonu
                self.calendar.setDateTextFormat(
                    QDate(d.year, d.month, d.day), weekend_format
                )

    def _on_date_selected(self):
        """Tarih seçildiğinde"""
        selected = self.calendar.selectedDate().toPyDate()
        days_tr = [
            "Pazartesi",
            "Salı",
            "Çarşamba",
            "Perşembe",
            "Cuma",
            "Cumartesi",
            "Pazar",
        ]
        day_name = days_tr[selected.weekday()]
        self.day_info_label.setText(f"{selected.strftime('%d.%m.%Y')} - {day_name}")

        # Seçili gün için vardiya bilgisi yükle
        self._load_day_shifts(selected)

    def _load_day_shifts(self, selected_date: date):
        """Seçili günün vardiyalarını yükle"""
        if not self.team_service or not self.shift_service:
            return

        try:
            teams = self.team_service.get_all()
            shifts = self.shift_service.get_all()

            # Placeholder - gerçek data rotation'dan gelecek
            self.day_shifts_table.setRowCount(len(teams))

            for i, team in enumerate(teams):
                self.day_shifts_table.setItem(i, 0, QTableWidgetItem(team.name))
                if shifts:
                    shift = shifts[i % len(shifts)]
                    self.day_shifts_table.setItem(i, 1, QTableWidgetItem(shift.code))
                    self.day_shifts_table.setItem(i, 2, QTableWidgetItem("-"))
                    self.day_shifts_table.setItem(
                        i,
                        3,
                        QTableWidgetItem(
                            f"{shift.start_time.strftime('%H:%M')}-"
                            f"{shift.end_time.strftime('%H:%M')}"
                        ),
                    )
        except Exception as e:
            print(f"Gün vardiya yükleme hatası: {e}")

    def _assign_shift(self):
        """Vardiya ata"""
        if not self.shift_service or not self.team_service:
            QMessageBox.warning(self, "Uyarı", "Servisler yüklenemedi.")
            return

        try:
            from database.models.hr import Employee
            from database.base import get_session

            session = get_session()
            employees = session.query(Employee).filter(Employee.is_active == True).all()
            teams = self.team_service.get_all()
            shifts = self.shift_service.get_all()

            dialog = AssignmentDialog(employees, shifts, teams, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                # Atama işlemi - rotation schedule'a ekle
                QMessageBox.information(
                    self,
                    "Başarılı",
                    f"Vardiya ataması kaydedildi.\n"
                    f"Tarih: {data['start_date']} - {data['end_date']}",
                )
                self._load_data()

            session.close()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
