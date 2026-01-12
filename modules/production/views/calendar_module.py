"""
Akıllı İş - Üretim Takvimi Modülü
"""

from datetime import date, time, datetime
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
    QAbstractItemView,
    QTabWidget,
    QMessageBox,
    QDialog,
    QGridLayout,
    QLineEdit,
    QTimeEdit,
    QSpinBox,
    QDateEdit,
    QCheckBox,
    QComboBox,
    QScrollArea,
    QColorDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTime, QDate
from PyQt6.QtGui import QColor


class ShiftDialog(QDialog):
    """Vardiya ekleme/düzenleme dialogu"""

    def __init__(self, shift_data: dict = None, parent=None):
        super().__init__(parent)
        self.shift_data = shift_data
        self.setWindowTitle("Vardiya Ekle" if not shift_data else "Vardiya Düzenle")
        self.setMinimumWidth(400)
        self.setup_ui()
        if shift_data:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QGridLayout()
        form.setSpacing(12)

        # Kod
        form.addWidget(QLabel("Kod *"), 0, 0)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("SABAH")
        form.addWidget(self.code_input, 0, 1)

        # Ad
        form.addWidget(QLabel("Ad *"), 1, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Sabah Vardiyası")
        form.addWidget(self.name_input, 1, 1)

        # Başlangıç
        form.addWidget(QLabel("Başlangıç *"), 2, 0)
        self.start_time_input = QTimeEdit()
        self.start_time_input.setDisplayFormat("HH:mm")
        self.start_time_input.setTime(QTime(8, 0))
        form.addWidget(self.start_time_input, 2, 1)

        # Bitiş
        form.addWidget(QLabel("Bitiş *"), 3, 0)
        self.end_time_input = QTimeEdit()
        self.end_time_input.setDisplayFormat("HH:mm")
        self.end_time_input.setTime(QTime(17, 0))
        form.addWidget(self.end_time_input, 3, 1)

        # Mola
        form.addWidget(QLabel("Mola (dk)"), 4, 0)
        self.break_input = QSpinBox()
        self.break_input.setRange(0, 120)
        self.break_input.setValue(60)
        form.addWidget(self.break_input, 4, 1)

        layout.addLayout(form)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def load_data(self):
        if not self.shift_data:
            return
        self.code_input.setText(self.shift_data.get("code", ""))
        self.name_input.setText(self.shift_data.get("name", ""))
        if self.shift_data.get("start_time"):
            st = self.shift_data["start_time"]
            if isinstance(st, time):
                self.start_time_input.setTime(QTime(st.hour, st.minute))
        if self.shift_data.get("end_time"):
            et = self.shift_data["end_time"]
            if isinstance(et, time):
                self.end_time_input.setTime(QTime(et.hour, et.minute))
        self.break_input.setValue(self.shift_data.get("break_minutes", 0))

    def _on_save(self):
        if not self.code_input.text().strip():
            QMessageBox.warning(self, "Uyarı", "Kod zorunludur!")
            return
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Uyarı", "Ad zorunludur!")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "code": self.code_input.text().strip().upper(),
            "name": self.name_input.text().strip(),
            "start_time": self.start_time_input.time().toPyTime(),
            "end_time": self.end_time_input.time().toPyTime(),
            "break_minutes": self.break_input.value(),
        }


class HolidayDialog(QDialog):
    """Tatil ekleme/düzenleme dialogu"""

    def __init__(self, holiday_data: dict = None, parent=None):
        super().__init__(parent)
        self.holiday_data = holiday_data
        self.setWindowTitle("Tatil Ekle" if not holiday_data else "Tatil Düzenle")
        self.setMinimumWidth(400)
        self.setup_ui()
        if holiday_data:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QGridLayout()
        form.setSpacing(12)

        # Tarih
        form.addWidget(QLabel("Tarih *"), 0, 0)
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        form.addWidget(self.date_input, 0, 1)

        # Ad
        form.addWidget(QLabel("Tatil Adı *"), 1, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Yılbaşı")
        form.addWidget(self.name_input, 1, 1)

        # Yarım gün mü?
        form.addWidget(QLabel("Yarım Gün"), 2, 0)
        self.half_day_check = QCheckBox()
        form.addWidget(self.half_day_check, 2, 1)

        layout.addLayout(form)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def load_data(self):
        if not self.holiday_data:
            return
        if self.holiday_data.get("date"):
            d = self.holiday_data["date"]
            self.date_input.setDate(QDate(d.year, d.month, d.day))
        self.name_input.setText(self.holiday_data.get("name", ""))
        self.half_day_check.setChecked(self.holiday_data.get("is_half_day", False))

    def _on_save(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Uyarı", "Tatil adı zorunludur!")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "date": self.date_input.date().toPyDate(),
            "name": self.name_input.text().strip(),
            "is_half_day": self.half_day_check.isChecked(),
            "applies_to_all": True,
        }


class TeamDialog(QDialog):
    """Vardiya ekibi ekleme/düzenleme dialogu"""

    def __init__(self, team_data: dict = None, parent=None):
        super().__init__(parent)
        self.team_data = team_data
        self.selected_color = "#6366f1"
        self.setWindowTitle("Ekip Ekle" if not team_data else "Ekip Düzenle")
        self.setMinimumWidth(400)
        self.setup_ui()
        if team_data:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QGridLayout()
        form.setSpacing(12)

        # Kod
        form.addWidget(QLabel("Kod *"), 0, 0)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("A, B, C")
        self.code_input.setMaxLength(10)
        form.addWidget(self.code_input, 0, 1)

        # Ad
        form.addWidget(QLabel("Ad *"), 1, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("A Ekibi")
        form.addWidget(self.name_input, 1, 1)

        # Renk
        form.addWidget(QLabel("Renk"), 2, 0)
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(60, 30)
        self._update_color_button()
        self.color_btn.clicked.connect(self._pick_color)
        color_layout.addWidget(self.color_btn)
        self.color_label = QLabel(self.selected_color)
        color_layout.addWidget(self.color_label)
        color_layout.addStretch()
        form.addLayout(color_layout, 2, 1)

        # Açıklama
        form.addWidget(QLabel("Açıklama"), 3, 0)
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("İsteğe bağlı")
        form.addWidget(self.desc_input, 3, 1)

        layout.addLayout(form)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _update_color_button(self):
        self.color_btn.setStyleSheet(
            f"background-color: {self.selected_color}; "
            f"border: none; border-radius: 4px;"
        )

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self.selected_color), self)
        if color.isValid():
            self.selected_color = color.name()
            self._update_color_button()
            self.color_label.setText(self.selected_color)

    def load_data(self):
        if not self.team_data:
            return
        self.code_input.setText(self.team_data.get("code", ""))
        self.name_input.setText(self.team_data.get("name", ""))
        self.selected_color = self.team_data.get("color", "#6366f1")
        self._update_color_button()
        self.color_label.setText(self.selected_color)
        self.desc_input.setText(self.team_data.get("description", "") or "")

    def _on_save(self):
        if not self.code_input.text().strip():
            QMessageBox.warning(self, "Uyarı", "Kod zorunludur!")
            return
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Uyarı", "Ad zorunludur!")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "code": self.code_input.text().strip().upper(),
            "name": self.name_input.text().strip(),
            "color": self.selected_color,
            "description": self.desc_input.text().strip() or None,
        }


class CalendarModule(QWidget):
    """Üretim Takvimi Modülü"""

    page_title = "Üretim Takvimi"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.shift_service = None
        self.holiday_service = None
        self.schedule_service = None
        self.team_service = None
        self.rotation_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        header = QHBoxLayout()
        title = QLabel("📅 Üretim Takvimi")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_shifts_tab(), "⏰ Vardiyalar")
        self.tabs.addTab(self._create_teams_tab(), "👥 Ekipler")
        self.tabs.addTab(self._create_rotation_tab(), "🔄 Rotasyon")
        self.tabs.addTab(self._create_holidays_tab(), "🎉 Tatiller")
        self.tabs.addTab(self._create_schedule_tab(), "📋 İstasyon Takvimi")

        layout.addWidget(self.tabs)

    def _create_shifts_tab(self) -> QWidget:
        """Vardiyalar sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        # Toolbar
        toolbar = QHBoxLayout()

        add_btn = QPushButton("➕ Vardiya Ekle")
        add_btn.clicked.connect(self._add_shift)
        toolbar.addWidget(add_btn)

        toolbar.addStretch()

        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self._load_shifts)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        # Tablo
        self.shifts_table = QTableWidget()
        self.shifts_table.setColumnCount(6)
        self.shifts_table.setHorizontalHeaderLabels(
            ["Kod", "Ad", "Başlangıç", "Bitiş", "Mola (dk)", "İşlem"]
        )
        self.shifts_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.shifts_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.shifts_table.verticalHeader().setVisible(False)
        layout.addWidget(self.shifts_table)

        return tab

    def _create_teams_tab(self) -> QWidget:
        """Vardiya ekipleri sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        # Toolbar
        toolbar = QHBoxLayout()

        add_btn = QPushButton("➕ Ekip Ekle")
        add_btn.clicked.connect(self._add_team)
        toolbar.addWidget(add_btn)

        toolbar.addStretch()

        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self._load_teams)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        # Tablo
        self.teams_table = QTableWidget()
        self.teams_table.setColumnCount(5)
        self.teams_table.setHorizontalHeaderLabels(
            ["Kod", "Ad", "Renk", "Açıklama", "İşlem"]
        )
        self.teams_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self.teams_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.teams_table.verticalHeader().setVisible(False)
        layout.addWidget(self.teams_table)

        return tab

    def _create_rotation_tab(self) -> QWidget:
        """Rotasyon şablonu sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        # Şablon seçimi ve oluşturma
        toolbar = QHBoxLayout()

        toolbar.addWidget(QLabel("Şablon:"))
        self.rotation_pattern_combo = QComboBox()
        self.rotation_pattern_combo.setMinimumWidth(200)
        self.rotation_pattern_combo.currentIndexChanged.connect(
            self._load_rotation_schedule
        )
        toolbar.addWidget(self.rotation_pattern_combo)

        add_pattern_btn = QPushButton("➕ Yeni Şablon")
        add_pattern_btn.clicked.connect(self._add_rotation_pattern)
        toolbar.addWidget(add_pattern_btn)

        toolbar.addStretch()

        save_rotation_btn = QPushButton("💾 Kaydet")
        save_rotation_btn.clicked.connect(self._save_rotation_schedule)
        toolbar.addWidget(save_rotation_btn)

        layout.addLayout(toolbar)

        # Döngü bilgisi
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Döngü Gün Sayısı:"))
        self.cycle_days_spin = QSpinBox()
        self.cycle_days_spin.setRange(1, 30)
        self.cycle_days_spin.setValue(6)
        self.cycle_days_spin.valueChanged.connect(self._rebuild_rotation_grid)
        info_layout.addWidget(self.cycle_days_spin)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Rotasyon grid (Gün x Vardiya -> Ekip)
        self.rotation_frame = QFrame()
        self.rotation_grid = QGridLayout(self.rotation_frame)
        self.rotation_grid.setSpacing(8)
        layout.addWidget(self.rotation_frame)

        # Combo dizileri
        self.rotation_combos = {}  # {(day, shift_id): QComboBox}

        # Bilgi
        info = QLabel(
            "ℹ️ Her döngü günü için hangi ekibin hangi vardiyada " "çalışacağını seçin"
        )
        layout.addWidget(info)

        layout.addStretch()
        return tab

    def _create_holidays_tab(self) -> QWidget:
        """Tatiller sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        # Toolbar
        toolbar = QHBoxLayout()

        add_btn = QPushButton("➕ Tatil Ekle")
        add_btn.clicked.connect(self._add_holiday)
        toolbar.addWidget(add_btn)

        toolbar.addStretch()

        # Yıl filtresi
        self.year_combo = QComboBox()
        current_year = date.today().year
        for y in range(current_year - 1, current_year + 3):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentIndexChanged.connect(self._load_holidays)
        toolbar.addWidget(self.year_combo)

        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self._load_holidays)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        # Tablo
        self.holidays_table = QTableWidget()
        self.holidays_table.setColumnCount(5)
        self.holidays_table.setHorizontalHeaderLabels(
            ["Tarih", "Gün", "Tatil Adı", "Yarım Gün", "İşlem"]
        )
        self.holidays_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.holidays_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.holidays_table.verticalHeader().setVisible(False)
        layout.addWidget(self.holidays_table)

        return tab

    def _create_schedule_tab(self) -> QWidget:
        """İstasyon takvimi sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        # Toolbar
        toolbar = QHBoxLayout()

        toolbar.addWidget(QLabel("İş İstasyonu:"))
        self.station_combo = QComboBox()
        self.station_combo.setMinimumWidth(200)
        self.station_combo.currentIndexChanged.connect(self._load_station_schedule)
        toolbar.addWidget(self.station_combo)

        toolbar.addStretch()

        save_btn = QPushButton("💾 Takvimi Kaydet")
        save_btn.clicked.connect(self._save_station_schedule)
        toolbar.addWidget(save_btn)

        layout.addLayout(toolbar)

        # Haftalık takvim grid
        schedule_frame = QFrame()
        schedule_layout = QGridLayout(schedule_frame)
        schedule_layout.setContentsMargins(16, 16, 16, 16)
        schedule_layout.setSpacing(12)

        days = [
            "Pazartesi",
            "Salı",
            "Çarşamba",
            "Perşembe",
            "Cuma",
            "Cumartesi",
            "Pazar",
        ]
        self.day_checkboxes = {}  # {day_index: {shift_id: checkbox}}

        # Başlık satırı
        schedule_layout.addWidget(QLabel("Gün"), 0, 0)
        # Vardiya başlıkları dinamik eklenecek
        self.shift_headers = []

        # Gün satırları
        for i, day in enumerate(days):
            day_label = QLabel(day)
            schedule_layout.addWidget(day_label, i + 1, 0)
            self.day_checkboxes[i] = {}

        self.schedule_layout = schedule_layout
        self.schedule_frame = schedule_frame
        layout.addWidget(schedule_frame)

        # Bilgi
        info = QLabel("ℹ️ Her gün için çalışılacak vardiyaları işaretleyin")
        layout.addWidget(info)

        layout.addStretch()

        return tab

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_shifts()
        self._load_teams()
        self._load_rotation_patterns()
        self._load_holidays()
        self._load_stations()

    def _ensure_services(self):
        if not self.shift_service:
            try:
                from modules.production.calendar_services import (
                    ShiftService,
                    HolidayService,
                    WorkstationScheduleService,
                    ShiftTeamService,
                    RotationPatternService,
                )

                self.shift_service = ShiftService()
                self.holiday_service = HolidayService()
                self.schedule_service = WorkstationScheduleService()
                self.team_service = ShiftTeamService()
                self.rotation_service = RotationPatternService()
            except Exception as e:
                print(f"Servis yükleme hatası: {e}")

    def _load_shifts(self):
        """Vardiyaları yükle"""
        if not self.shift_service:
            return

        try:
            shifts = self.shift_service.get_all(active_only=False)
            self.shifts_table.setRowCount(len(shifts))

            for row, shift in enumerate(shifts):
                # Kod
                code_item = QTableWidgetItem(shift.code)
                code_item.setForeground(QColor("#818cf8"))
                code_item.setData(Qt.ItemDataRole.UserRole, shift.id)
                self.shifts_table.setItem(row, 0, code_item)

                # Ad
                self.shifts_table.setItem(row, 1, QTableWidgetItem(shift.name))

                # Başlangıç
                start_str = (
                    shift.start_time.strftime("%H:%M") if shift.start_time else "-"
                )
                self.shifts_table.setItem(row, 2, QTableWidgetItem(start_str))

                # Bitiş
                end_str = shift.end_time.strftime("%H:%M") if shift.end_time else "-"
                self.shifts_table.setItem(row, 3, QTableWidgetItem(end_str))

                # Mola
                self.shifts_table.setItem(
                    row, 4, QTableWidgetItem(str(shift.break_minutes or 0))
                )

                # İşlem butonları
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(4, 4, 4, 4)
                btn_layout.setSpacing(4)

                edit_btn = QPushButton("✏️")
                edit_btn.setFixedSize(28, 28)
                edit_btn.clicked.connect(lambda checked, s=shift: self._edit_shift(s))
                btn_layout.addWidget(edit_btn)

                del_btn = QPushButton("🗑")
                del_btn.setFixedSize(28, 28)
                del_btn.clicked.connect(lambda checked, s=shift: self._delete_shift(s))
                btn_layout.addWidget(del_btn)

                self.shifts_table.setCellWidget(row, 5, btn_widget)

            # Takvim sekmesindeki vardiya checkboxlarını güncelle
            self._update_schedule_checkboxes(shifts)

        except Exception as e:
            print(f"Vardiya yükleme hatası: {e}")

    def _update_schedule_checkboxes(self, shifts):
        """Takvim sekmesindeki vardiya checkbox'larını güncelle"""
        # Mevcut başlıkları temizle
        for header in self.shift_headers:
            header.deleteLater()
        self.shift_headers.clear()

        # Mevcut checkbox'ları temizle
        for day_checks in self.day_checkboxes.values():
            for cb in day_checks.values():
                cb.deleteLater()
            day_checks.clear()

        # Yeni başlıklar ve checkbox'lar ekle
        for col, shift in enumerate(shifts):
            # Başlık
            header = QLabel(
                f"{shift.code}\n{shift.start_time.strftime('%H:%M')}-{shift.end_time.strftime('%H:%M')}"
            )
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.schedule_layout.addWidget(header, 0, col + 1)
            self.shift_headers.append(header)

            # Her gün için checkbox
            for day in range(7):
                cb = QCheckBox()
                cb.setProperty("shift_id", shift.id)
                cb.setProperty("day", day)
                self.schedule_layout.addWidget(
                    cb, day + 1, col + 1, Qt.AlignmentFlag.AlignCenter
                )
                self.day_checkboxes[day][shift.id] = cb

    def _load_holidays(self):
        """Tatilleri yükle"""
        if not self.holiday_service:
            return

        try:
            year = self.year_combo.currentData()
            holidays = self.holiday_service.get_all(year=year)
            self.holidays_table.setRowCount(len(holidays))

            days_tr = [
                "Pazartesi",
                "Salı",
                "Çarşamba",
                "Perşembe",
                "Cuma",
                "Cumartesi",
                "Pazar",
            ]

            for row, holiday in enumerate(holidays):
                # Tarih
                date_str = holiday.date.strftime("%d.%m.%Y") if holiday.date else "-"
                date_item = QTableWidgetItem(date_str)
                date_item.setForeground(QColor("#818cf8"))
                date_item.setData(Qt.ItemDataRole.UserRole, holiday.id)
                self.holidays_table.setItem(row, 0, date_item)

                # Gün
                day_name = days_tr[holiday.date.weekday()] if holiday.date else "-"
                self.holidays_table.setItem(row, 1, QTableWidgetItem(day_name))

                # Ad
                self.holidays_table.setItem(row, 2, QTableWidgetItem(holiday.name))

                # Yarım gün
                half_str = "✓" if holiday.is_half_day else ""
                self.holidays_table.setItem(row, 3, QTableWidgetItem(half_str))

                # İşlem butonları
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(4, 4, 4, 4)
                btn_layout.setSpacing(4)

                edit_btn = QPushButton("✏️")
                edit_btn.setFixedSize(28, 28)
                edit_btn.clicked.connect(
                    lambda checked, h=holiday: self._edit_holiday(h)
                )
                btn_layout.addWidget(edit_btn)

                del_btn = QPushButton("🗑")
                del_btn.setFixedSize(28, 28)
                del_btn.clicked.connect(
                    lambda checked, h=holiday: self._delete_holiday(h)
                )
                btn_layout.addWidget(del_btn)

                self.holidays_table.setCellWidget(row, 4, btn_widget)

        except Exception as e:
            print(f"Tatil yükleme hatası: {e}")

    def _load_stations(self):
        """İş istasyonlarını yükle"""
        try:
            from modules.production.services import WorkStationService

            ws_service = WorkStationService()
            stations = ws_service.get_all(active_only=True)

            self.station_combo.clear()
            self.station_combo.addItem("Seçiniz...", None)
            for ws in stations:
                self.station_combo.addItem(f"{ws.code} - {ws.name}", ws.id)
        except Exception as e:
            print(f"İstasyon yükleme hatası: {e}")

    def _load_station_schedule(self):
        """Seçili istasyonun takvimini yükle"""
        if not self.schedule_service:
            return

        station_id = self.station_combo.currentData()
        if not station_id:
            # Tüm checkbox'ları temizle
            for day_checks in self.day_checkboxes.values():
                for cb in day_checks.values():
                    cb.setChecked(False)
            return

        try:
            schedules = self.schedule_service.get_by_workstation(station_id)

            # Önce hepsini temizle
            for day_checks in self.day_checkboxes.values():
                for cb in day_checks.values():
                    cb.setChecked(False)

            # Kayıtlı olanları işaretle
            for schedule in schedules:
                if schedule.is_working and schedule.shift_id:
                    day = schedule.day_of_week
                    if (
                        day in self.day_checkboxes
                        and schedule.shift_id in self.day_checkboxes[day]
                    ):
                        self.day_checkboxes[day][schedule.shift_id].setChecked(True)

        except Exception as e:
            print(f"İstasyon takvimi yükleme hatası: {e}")

    def _save_station_schedule(self):
        """İstasyon takvimini kaydet"""
        if not self.schedule_service:
            return

        station_id = self.station_combo.currentData()
        if not station_id:
            QMessageBox.warning(self, "Uyarı", "Önce bir iş istasyonu seçin!")
            return

        try:
            # Her gün için seçili vardiyaları topla
            schedule = {}
            for day, checks in self.day_checkboxes.items():
                shift_ids = []
                for shift_id, cb in checks.items():
                    if cb.isChecked():
                        shift_ids.append(shift_id)
                schedule[day] = shift_ids

            # Kaydet
            self.schedule_service.set_weekly_schedule(station_id, schedule)
            QMessageBox.information(self, "Başarılı", "Takvim kaydedildi!")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")

    def _add_shift(self):
        """Yeni vardiya ekle"""
        dialog = ShiftDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.shift_service.create(**data)
                self._load_shifts()
                QMessageBox.information(self, "Başarılı", "Vardiya eklendi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Ekleme hatası: {str(e)}")

    def _edit_shift(self, shift):
        """Vardiya düzenle"""
        data = {
            "code": shift.code,
            "name": shift.name,
            "start_time": shift.start_time,
            "end_time": shift.end_time,
            "break_minutes": shift.break_minutes,
        }
        dialog = ShiftDialog(data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            try:
                self.shift_service.update(shift.id, **new_data)
                self._load_shifts()
                QMessageBox.information(self, "Başarılı", "Vardiya güncellendi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Güncelleme hatası: {str(e)}")

    def _delete_shift(self, shift):
        """Vardiya sil"""
        reply = QMessageBox.question(
            self,
            "Onay",
            f"'{shift.name}' vardiyasını silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.shift_service.delete(shift.id)
                self._load_shifts()
                QMessageBox.information(self, "Başarılı", "Vardiya silindi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")

    def _add_holiday(self):
        """Yeni tatil ekle"""
        dialog = HolidayDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.holiday_service.create(**data)
                self._load_holidays()
                QMessageBox.information(self, "Başarılı", "Tatil eklendi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Ekleme hatası: {str(e)}")

    def _edit_holiday(self, holiday):
        """Tatil düzenle"""
        data = {
            "date": holiday.date,
            "name": holiday.name,
            "is_half_day": holiday.is_half_day,
        }
        dialog = HolidayDialog(data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            try:
                self.holiday_service.update(holiday.id, **new_data)
                self._load_holidays()
                QMessageBox.information(self, "Başarılı", "Tatil güncellendi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Güncelleme hatası: {str(e)}")

    def _delete_holiday(self, holiday):
        """Tatil sil"""
        reply = QMessageBox.question(
            self,
            "Onay",
            f"'{holiday.name}' tatilini silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.holiday_service.delete(holiday.id)
                self._load_holidays()
                QMessageBox.information(self, "Başarılı", "Tatil silindi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")

    def _load_teams(self):
        """Vardiya ekiplerini yükle"""
        if not self.team_service:
            return

        try:
            teams = self.team_service.get_all(active_only=False)
            self.teams_table.setRowCount(len(teams))

            for row, team in enumerate(teams):
                # Kod
                code_item = QTableWidgetItem(team.code)
                code_item.setForeground(QColor(team.color or "#6366f1"))
                code_item.setData(Qt.ItemDataRole.UserRole, team.id)
                self.teams_table.setItem(row, 0, code_item)

                # Ad
                self.teams_table.setItem(row, 1, QTableWidgetItem(team.name))

                # Renk
                color_item = QTableWidgetItem(team.color or "#6366f1")
                color_item.setBackground(QColor(team.color or "#6366f1"))
                color_item.setForeground(QColor("#ffffff"))
                self.teams_table.setItem(row, 2, color_item)

                # Açıklama
                desc = team.description or ""
                self.teams_table.setItem(row, 3, QTableWidgetItem(desc))

                # İşlem butonları
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(4, 4, 4, 4)
                btn_layout.setSpacing(4)

                edit_btn = QPushButton("✏️")
                edit_btn.setFixedSize(28, 28)
                edit_btn.clicked.connect(lambda checked, t=team: self._edit_team(t))
                btn_layout.addWidget(edit_btn)

                del_btn = QPushButton("🗑")
                del_btn.setFixedSize(28, 28)
                del_btn.clicked.connect(lambda checked, t=team: self._delete_team(t))
                btn_layout.addWidget(del_btn)

                self.teams_table.setCellWidget(row, 4, btn_widget)

        except Exception as e:
            print(f"Ekip yükleme hatası: {e}")

    def _add_team(self):
        """Yeni ekip ekle"""
        dialog = TeamDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.team_service.create(**data)
                self._load_teams()
                QMessageBox.information(self, "Başarılı", "Ekip eklendi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Ekleme hatası: {str(e)}")

    def _edit_team(self, team):
        """Ekip düzenle"""
        data = {
            "code": team.code,
            "name": team.name,
            "color": team.color,
            "description": team.description,
        }
        dialog = TeamDialog(data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            try:
                self.team_service.update(team.id, **new_data)
                self._load_teams()
                QMessageBox.information(self, "Başarılı", "Ekip güncellendi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Güncelleme hatası: {str(e)}")

    def _delete_team(self, team):
        """Ekip sil"""
        reply = QMessageBox.question(
            self,
            "Onay",
            f"'{team.name}' ekibini silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.team_service.delete(team.id)
                self._load_teams()
                QMessageBox.information(self, "Başarılı", "Ekip silindi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")

    def _load_rotation_patterns(self):
        """Rotasyon şablonlarını yükle"""
        if not self.rotation_service:
            return

        try:
            self.rotation_pattern_combo.clear()
            self.rotation_pattern_combo.addItem("Seçiniz...", None)
            patterns = self.rotation_service.get_all()
            for pattern in patterns:
                self.rotation_pattern_combo.addItem(
                    f"{pattern.code} - {pattern.name}", pattern.id
                )
        except Exception as e:
            print(f"Rotasyon şablon yükleme hatası: {e}")

    def _load_rotation_schedule(self):
        """Seçili şablonun rotasyon takvimini yükle"""
        pattern_id = self.rotation_pattern_combo.currentData()
        if not pattern_id or not self.rotation_service:
            return

        try:
            pattern = self.rotation_service.get_by_id(pattern_id)
            if pattern:
                self.cycle_days_spin.blockSignals(True)
                self.cycle_days_spin.setValue(pattern.cycle_days)
                self.cycle_days_spin.blockSignals(False)
                self._rebuild_rotation_grid()

                # Mevcut schedule'ları yükle
                schedules = self.rotation_service.get_schedules(pattern_id)
                for schedule in schedules:
                    key = (schedule.day_in_cycle, schedule.shift_id)
                    if key in self.rotation_combos:
                        combo = self.rotation_combos[key]
                        idx = combo.findData(schedule.team_id)
                        if idx >= 0:
                            combo.setCurrentIndex(idx)
        except Exception as e:
            print(f"Rotasyon takvimi yükleme hatası: {e}")

    def _rebuild_rotation_grid(self):
        """Rotasyon grid'ini yeniden oluştur"""
        # Mevcut widget'ları temizle
        while self.rotation_grid.count():
            item = self.rotation_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.rotation_combos.clear()

        if not self.shift_service or not self.team_service:
            return

        try:
            shifts = self.shift_service.get_all()
            teams = self.team_service.get_all()
            cycle_days = self.cycle_days_spin.value()

            # Başlık: Vardiyalar
            self.rotation_grid.addWidget(QLabel("Gün"), 0, 0)
            for col, shift in enumerate(shifts):
                lbl = QLabel(f"{shift.code}\n{shift.start_time.strftime('%H:%M')}")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.rotation_grid.addWidget(lbl, 0, col + 1)

            # Satırlar: Her döngü günü
            for day in range(1, cycle_days + 1):
                self.rotation_grid.addWidget(QLabel(f"Gün {day}"), day, 0)

                for col, shift in enumerate(shifts):
                    combo = QComboBox()
                    combo.addItem("Dinleniyor", None)
                    for team in teams:
                        combo.addItem(f"{team.code}", team.id)
                    self.rotation_grid.addWidget(combo, day, col + 1)
                    self.rotation_combos[(day, shift.id)] = combo

        except Exception as e:
            print(f"Rotasyon grid oluşturma hatası: {e}")

    def _add_rotation_pattern(self):
        """Yeni rotasyon şablonu ekle"""
        from PyQt6.QtWidgets import QInputDialog

        code, ok = QInputDialog.getText(self, "Yeni Şablon", "Şablon Kodu (örn: 2X12):")
        if not ok or not code.strip():
            return

        name, ok = QInputDialog.getText(
            self, "Yeni Şablon", "Şablon Adı (örn: 2 Vardiya 12 Saat):"
        )
        if not ok or not name.strip():
            return

        try:
            cycle_days = self.cycle_days_spin.value()
            self.rotation_service.create(
                code=code.strip().upper(),
                name=name.strip(),
                cycle_days=cycle_days,
                shifts_per_day=2,
            )
            self._load_rotation_patterns()
            # Son eklenen şablonu seç
            self.rotation_pattern_combo.setCurrentIndex(
                self.rotation_pattern_combo.count() - 1
            )
            QMessageBox.information(self, "Başarılı", "Şablon oluşturuldu!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Oluşturma hatası: {str(e)}")

    def _save_rotation_schedule(self):
        """Rotasyon takvimini kaydet"""
        pattern_id = self.rotation_pattern_combo.currentData()
        if not pattern_id:
            QMessageBox.warning(self, "Uyarı", "Önce bir şablon seçin!")
            return

        try:
            # Önce mevcut schedule'ları temizle
            self.rotation_service.clear_schedules(pattern_id)

            # Cycle days güncelle
            cycle_days = self.cycle_days_spin.value()
            self.rotation_service.update(pattern_id, cycle_days=cycle_days)

            # Yeni schedule'ları kaydet
            for (day, shift_id), combo in self.rotation_combos.items():
                team_id = combo.currentData()
                if team_id:  # Sadece ekip seçilmişse kaydet
                    self.rotation_service.set_schedule(
                        pattern_id, day, shift_id, team_id
                    )

            QMessageBox.information(self, "Başarılı", "Rotasyon kaydedildi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")
