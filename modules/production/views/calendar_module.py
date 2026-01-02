"""
Akıllı İş - Üretim Takvimi Modülü
"""

from datetime import date, time, datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QTabWidget, QMessageBox, QDialog,
    QGridLayout, QLineEdit, QTimeEdit, QSpinBox, QDateEdit,
    QCheckBox, QComboBox, QScrollArea
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
        self.setStyleSheet("""
            QDialog { background-color: #0f172a; }
            QLabel { color: #e2e8f0; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        form = QGridLayout()
        form.setSpacing(12)
        
        # Kod
        form.addWidget(QLabel("Kod *"), 0, 0)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("SABAH")
        self._style_input(self.code_input)
        form.addWidget(self.code_input, 0, 1)
        
        # Ad
        form.addWidget(QLabel("Ad *"), 1, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Sabah Vardiyası")
        self._style_input(self.name_input)
        form.addWidget(self.name_input, 1, 1)
        
        # Başlangıç
        form.addWidget(QLabel("Başlangıç *"), 2, 0)
        self.start_time_input = QTimeEdit()
        self.start_time_input.setDisplayFormat("HH:mm")
        self.start_time_input.setTime(QTime(8, 0))
        self._style_time(self.start_time_input)
        form.addWidget(self.start_time_input, 2, 1)
        
        # Bitiş
        form.addWidget(QLabel("Bitiş *"), 3, 0)
        self.end_time_input = QTimeEdit()
        self.end_time_input.setDisplayFormat("HH:mm")
        self.end_time_input.setTime(QTime(17, 0))
        self._style_time(self.end_time_input)
        form.addWidget(self.end_time_input, 3, 1)
        
        # Mola
        form.addWidget(QLabel("Mola (dk)"), 4, 0)
        self.break_input = QSpinBox()
        self.break_input.setRange(0, 120)
        self.break_input.setValue(60)
        self._style_spin(self.break_input)
        form.addWidget(self.break_input, 4, 1)
        
        layout.addLayout(form)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet("""
            QPushButton { background-color: #334155; border: none; color: #f8fafc;
                padding: 10px 24px; border-radius: 8px; }
            QPushButton:hover { background-color: #475569; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet("""
            QPushButton { background-color: #6366f1; border: none; color: white;
                font-weight: 600; padding: 10px 24px; border-radius: 8px; }
            QPushButton:hover { background-color: #4f46e5; }
        """)
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
    
    def _style_input(self, w):
        w.setStyleSheet("""
            QLineEdit { background-color: #1e293b; border: 1px solid #334155;
                border-radius: 8px; padding: 10px; color: #f8fafc; }
            QLineEdit:focus { border-color: #6366f1; }
        """)
    
    def _style_time(self, w):
        w.setStyleSheet("""
            QTimeEdit { background-color: #1e293b; border: 1px solid #334155;
                border-radius: 8px; padding: 10px; color: #f8fafc; }
            QTimeEdit:focus { border-color: #6366f1; }
        """)
    
    def _style_spin(self, w):
        w.setStyleSheet("""
            QSpinBox { background-color: #1e293b; border: 1px solid #334155;
                border-radius: 8px; padding: 10px; color: #f8fafc; }
            QSpinBox:focus { border-color: #6366f1; }
        """)


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
        self.setStyleSheet("""
            QDialog { background-color: #0f172a; }
            QLabel { color: #e2e8f0; }
        """)
        
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
        self._style_date(self.date_input)
        form.addWidget(self.date_input, 0, 1)
        
        # Ad
        form.addWidget(QLabel("Tatil Adı *"), 1, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Yılbaşı")
        self._style_input(self.name_input)
        form.addWidget(self.name_input, 1, 1)
        
        # Yarım gün mü?
        form.addWidget(QLabel("Yarım Gün"), 2, 0)
        self.half_day_check = QCheckBox()
        self.half_day_check.setStyleSheet("QCheckBox { color: #f8fafc; }")
        form.addWidget(self.half_day_check, 2, 1)
        
        layout.addLayout(form)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet("""
            QPushButton { background-color: #334155; border: none; color: #f8fafc;
                padding: 10px 24px; border-radius: 8px; }
            QPushButton:hover { background-color: #475569; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet("""
            QPushButton { background-color: #6366f1; border: none; color: white;
                font-weight: 600; padding: 10px 24px; border-radius: 8px; }
            QPushButton:hover { background-color: #4f46e5; }
        """)
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
    
    def _style_input(self, w):
        w.setStyleSheet("""
            QLineEdit { background-color: #1e293b; border: 1px solid #334155;
                border-radius: 8px; padding: 10px; color: #f8fafc; }
            QLineEdit:focus { border-color: #6366f1; }
        """)
    
    def _style_date(self, w):
        w.setStyleSheet("""
            QDateEdit { background-color: #1e293b; border: 1px solid #334155;
                border-radius: 8px; padding: 10px; color: #f8fafc; }
            QDateEdit:focus { border-color: #6366f1; }
        """)


class CalendarModule(QWidget):
    """Üretim Takvimi Modülü"""
    
    page_title = "Üretim Takvimi"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.shift_service = None
        self.holiday_service = None
        self.schedule_service = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Başlık
        header = QHBoxLayout()
        title = QLabel("📅 Üretim Takvimi")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #334155; border-radius: 12px; 
                background-color: rgba(30, 41, 59, 0.5); }
            QTabBar::tab { background-color: #1e293b; color: #94a3b8; padding: 12px 24px; 
                margin-right: 4px; border-top-left-radius: 8px; border-top-right-radius: 8px; }
            QTabBar::tab:selected { background-color: #334155; color: #f8fafc; }
        """)
        
        tabs.addTab(self._create_shifts_tab(), "⏰ Vardiyalar")
        tabs.addTab(self._create_holidays_tab(), "🎉 Tatiller")
        tabs.addTab(self._create_schedule_tab(), "📋 İstasyon Takvimi")
        
        layout.addWidget(tabs)
    
    def _create_shifts_tab(self) -> QWidget:
        """Vardiyalar sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton("➕ Vardiya Ekle")
        add_btn.setStyleSheet("""
            QPushButton { background-color: #6366f1; border: none; color: white;
                font-weight: 600; padding: 10px 20px; border-radius: 8px; }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        add_btn.clicked.connect(self._add_shift)
        toolbar.addWidget(add_btn)
        
        toolbar.addStretch()
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet("""
            QPushButton { background-color: #334155; border: none; color: #f8fafc;
                padding: 10px 20px; border-radius: 8px; }
            QPushButton:hover { background-color: #475569; }
        """)
        refresh_btn.clicked.connect(self._load_shifts)
        toolbar.addWidget(refresh_btn)
        
        layout.addLayout(toolbar)
        
        # Tablo
        self.shifts_table = QTableWidget()
        self.shifts_table.setColumnCount(6)
        self.shifts_table.setHorizontalHeaderLabels([
            "Kod", "Ad", "Başlangıç", "Bitiş", "Mola (dk)", "İşlem"
        ])
        self.shifts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.shifts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.shifts_table.verticalHeader().setVisible(False)
        self.shifts_table.setStyleSheet("""
            QTableWidget { background-color: rgba(15, 23, 42, 0.5); border: 1px solid #334155; border-radius: 8px; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #334155; }
            QHeaderView::section { background-color: #1e293b; color: #94a3b8; font-weight: 600; padding: 8px; border: none; }
        """)
        layout.addWidget(self.shifts_table)
        
        return tab
    
    def _create_holidays_tab(self) -> QWidget:
        """Tatiller sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton("➕ Tatil Ekle")
        add_btn.setStyleSheet("""
            QPushButton { background-color: #6366f1; border: none; color: white;
                font-weight: 600; padding: 10px 20px; border-radius: 8px; }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        add_btn.clicked.connect(self._add_holiday)
        toolbar.addWidget(add_btn)
        
        toolbar.addStretch()
        
        # Yıl filtresi
        self.year_combo = QComboBox()
        current_year = date.today().year
        for y in range(current_year - 1, current_year + 3):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.setStyleSheet("""
            QComboBox { background-color: #1e293b; border: 1px solid #334155;
                border-radius: 8px; padding: 8px 12px; color: #f8fafc; min-width: 100px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #1e293b; border: 1px solid #334155;
                color: #f8fafc; selection-background-color: #334155; }
        """)
        self.year_combo.currentIndexChanged.connect(self._load_holidays)
        toolbar.addWidget(self.year_combo)
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet("""
            QPushButton { background-color: #334155; border: none; color: #f8fafc;
                padding: 10px 20px; border-radius: 8px; }
            QPushButton:hover { background-color: #475569; }
        """)
        refresh_btn.clicked.connect(self._load_holidays)
        toolbar.addWidget(refresh_btn)
        
        layout.addLayout(toolbar)
        
        # Tablo
        self.holidays_table = QTableWidget()
        self.holidays_table.setColumnCount(5)
        self.holidays_table.setHorizontalHeaderLabels([
            "Tarih", "Gün", "Tatil Adı", "Yarım Gün", "İşlem"
        ])
        self.holidays_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.holidays_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.holidays_table.verticalHeader().setVisible(False)
        self.holidays_table.setStyleSheet("""
            QTableWidget { background-color: rgba(15, 23, 42, 0.5); border: 1px solid #334155; border-radius: 8px; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #334155; }
            QHeaderView::section { background-color: #1e293b; color: #94a3b8; font-weight: 600; padding: 8px; border: none; }
        """)
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
        self.station_combo.setStyleSheet("""
            QComboBox { background-color: #1e293b; border: 1px solid #334155;
                border-radius: 8px; padding: 8px 12px; color: #f8fafc; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #1e293b; border: 1px solid #334155;
                color: #f8fafc; selection-background-color: #334155; }
        """)
        self.station_combo.currentIndexChanged.connect(self._load_station_schedule)
        toolbar.addWidget(self.station_combo)
        
        toolbar.addStretch()
        
        save_btn = QPushButton("💾 Takvimi Kaydet")
        save_btn.setStyleSheet("""
            QPushButton { background-color: #6366f1; border: none; color: white;
                font-weight: 600; padding: 10px 20px; border-radius: 8px; }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        save_btn.clicked.connect(self._save_station_schedule)
        toolbar.addWidget(save_btn)
        
        layout.addLayout(toolbar)
        
        # Haftalık takvim grid
        schedule_frame = QFrame()
        schedule_frame.setStyleSheet("""
            QFrame { background-color: rgba(30, 41, 59, 0.3); border: 1px solid #334155; border-radius: 12px; }
        """)
        schedule_layout = QGridLayout(schedule_frame)
        schedule_layout.setContentsMargins(16, 16, 16, 16)
        schedule_layout.setSpacing(12)
        
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        self.day_checkboxes = {}  # {day_index: {shift_id: checkbox}}
        
        # Başlık satırı
        schedule_layout.addWidget(QLabel("Gün"), 0, 0)
        # Vardiya başlıkları dinamik eklenecek
        self.shift_headers = []
        
        # Gün satırları
        for i, day in enumerate(days):
            day_label = QLabel(day)
            day_label.setStyleSheet("color: #f8fafc; font-weight: 600;")
            schedule_layout.addWidget(day_label, i + 1, 0)
            self.day_checkboxes[i] = {}
        
        self.schedule_layout = schedule_layout
        self.schedule_frame = schedule_frame
        layout.addWidget(schedule_frame)
        
        # Bilgi
        info = QLabel("ℹ️ Her gün için çalışılacak vardiyaları işaretleyin")
        info.setStyleSheet("color: #64748b; margin-top: 8px;")
        layout.addWidget(info)
        
        layout.addStretch()
        
        return tab
    
    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_shifts()
        self._load_holidays()
        self._load_stations()
    
    def _ensure_services(self):
        if not self.shift_service:
            try:
                from database.models.calendar import ProductionShift, ProductionHoliday, WorkstationSchedule
                from modules.production.calendar_services import ShiftService, HolidayService, WorkstationScheduleService
                self.shift_service = ShiftService()
                self.holiday_service = HolidayService()
                self.schedule_service = WorkstationScheduleService()
            except Exception as e:
                print(f"Servis yükleme hatası: {e}")
                # Alternatif import
                try:
                    from database.base import get_session
                    # Servisleri doğrudan oluştur
                except:
                    pass
    
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
                start_str = shift.start_time.strftime("%H:%M") if shift.start_time else "-"
                self.shifts_table.setItem(row, 2, QTableWidgetItem(start_str))
                
                # Bitiş
                end_str = shift.end_time.strftime("%H:%M") if shift.end_time else "-"
                self.shifts_table.setItem(row, 3, QTableWidgetItem(end_str))
                
                # Mola
                self.shifts_table.setItem(row, 4, QTableWidgetItem(str(shift.break_minutes or 0)))
                
                # İşlem butonları
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(4, 4, 4, 4)
                btn_layout.setSpacing(4)
                
                edit_btn = QPushButton("✏️")
                edit_btn.setFixedSize(28, 28)
                edit_btn.setStyleSheet("QPushButton { background-color: #334155; border: none; border-radius: 4px; } QPushButton:hover { background-color: #475569; }")
                edit_btn.clicked.connect(lambda checked, s=shift: self._edit_shift(s))
                btn_layout.addWidget(edit_btn)
                
                del_btn = QPushButton("🗑")
                del_btn.setFixedSize(28, 28)
                del_btn.setStyleSheet("QPushButton { background-color: #7f1d1d; border: none; border-radius: 4px; } QPushButton:hover { background-color: #991b1b; }")
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
            header = QLabel(f"{shift.code}\n{shift.start_time.strftime('%H:%M')}-{shift.end_time.strftime('%H:%M')}")
            header.setStyleSheet("color: #94a3b8; font-size: 11px;")
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.schedule_layout.addWidget(header, 0, col + 1)
            self.shift_headers.append(header)
            
            # Her gün için checkbox
            for day in range(7):
                cb = QCheckBox()
                cb.setStyleSheet("QCheckBox { color: #f8fafc; }")
                cb.setProperty("shift_id", shift.id)
                cb.setProperty("day", day)
                self.schedule_layout.addWidget(cb, day + 1, col + 1, Qt.AlignmentFlag.AlignCenter)
                self.day_checkboxes[day][shift.id] = cb
    
    def _load_holidays(self):
        """Tatilleri yükle"""
        if not self.holiday_service:
            return
        
        try:
            year = self.year_combo.currentData()
            holidays = self.holiday_service.get_all(year=year)
            self.holidays_table.setRowCount(len(holidays))
            
            days_tr = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
            
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
                edit_btn.setStyleSheet("QPushButton { background-color: #334155; border: none; border-radius: 4px; } QPushButton:hover { background-color: #475569; }")
                edit_btn.clicked.connect(lambda checked, h=holiday: self._edit_holiday(h))
                btn_layout.addWidget(edit_btn)
                
                del_btn = QPushButton("🗑")
                del_btn.setFixedSize(28, 28)
                del_btn.setStyleSheet("QPushButton { background-color: #7f1d1d; border: none; border-radius: 4px; } QPushButton:hover { background-color: #991b1b; }")
                del_btn.clicked.connect(lambda checked, h=holiday: self._delete_holiday(h))
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
                    if day in self.day_checkboxes and schedule.shift_id in self.day_checkboxes[day]:
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
            self, "Onay",
            f"'{shift.name}' vardiyasını silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
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
            self, "Onay",
            f"'{holiday.name}' tatilini silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.holiday_service.delete(holiday.id)
                self._load_holidays()
                QMessageBox.information(self, "Başarılı", "Tatil silindi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
