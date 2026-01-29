"""
Akıllı İş - Puantaj Yönetim Modülü

PDKS verilerini görüntüler, import eder ve yönetir.
"""

from datetime import date, datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QFormLayout,
    QMessageBox,
    QLabel,
    QComboBox,
    QSpinBox,
    QFileDialog,
    QTabWidget,
    QGroupBox,
    QLineEdit,
    QProgressDialog,
    QDateEdit,
    QTimeEdit,
)
from PyQt6.QtCore import Qt, QDate, QTime
import qtawesome as qta

from config.icons import ICONS
from modules.hr.services import HRService
from modules.hr.services.pdks_service import PDKSService, PDKSSource
from database.models.hr import AttendanceStatus
from ui.components.page_header import PageHeader
from ui.components.stat_cards import MiniStatCard
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


ATTENDANCE_STATUS_LABELS = {
    AttendanceStatus.PRESENT: ("Mevcut", "#10b981"),
    AttendanceStatus.ABSENT: ("Yok", "#ef4444"),
    AttendanceStatus.LATE: ("Geç Kaldı", "#f59e0b"),
    AttendanceStatus.EARLY_LEAVE: ("Erken Çıktı", "#f59e0b"),
    AttendanceStatus.ON_LEAVE: ("İzinli", "#3b82f6"),
    AttendanceStatus.HOLIDAY: ("Tatil", "#3b82f6"),
}


class PDKSImportDialog(QDialog):
    """PDKS import dialogu - CSV, Excel veya ZKTeco"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("PDKS Verileri Import")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        tabs = QTabWidget()

        # CSV Tab
        csv_tab = QWidget()
        csv_layout = QVBoxLayout(csv_tab)
        csv_info = QLabel(
            "CSV dosyasından puantaj verilerini import edin.\n"
            "Gerekli kolonlar: sicil_no/employee_no, tarih/date\n"
            "Opsiyonel: giris/check_in, cikis/check_out"
        )
        csv_info.setWordWrap(True)
        csv_layout.addWidget(csv_info)

        csv_file_row = QHBoxLayout()
        self.csv_path = QLineEdit()
        self.csv_path.setPlaceholderText("CSV dosyası seçiniz...")
        self.csv_path.setReadOnly(True)
        csv_file_row.addWidget(self.csv_path)

        csv_browse = QPushButton("Gözat")
        csv_browse.setIcon(qta.icon(ICONS.SEARCH))
        csv_browse.clicked.connect(self._browse_csv)
        csv_file_row.addWidget(csv_browse)
        csv_layout.addLayout(csv_file_row)

        csv_layout.addStretch()
        tabs.addTab(csv_tab, "CSV")

        # Excel Tab
        excel_tab = QWidget()
        excel_layout = QVBoxLayout(excel_tab)
        excel_info = QLabel(
            "Excel dosyasından (.xlsx) puantaj verilerini import edin.\n"
            "Gerekli kolonlar: sicil_no/employee_no, tarih/date\n"
            "Opsiyonel: giris/check_in, cikis/check_out"
        )
        excel_info.setWordWrap(True)
        excel_layout.addWidget(excel_info)

        excel_file_row = QHBoxLayout()
        self.excel_path = QLineEdit()
        self.excel_path.setPlaceholderText("Excel dosyası seçiniz...")
        self.excel_path.setReadOnly(True)
        excel_file_row.addWidget(self.excel_path)

        excel_browse = QPushButton("Gözat")
        excel_browse.setIcon(qta.icon(ICONS.SEARCH))
        excel_browse.clicked.connect(self._browse_excel)
        excel_file_row.addWidget(excel_browse)
        excel_layout.addLayout(excel_file_row)

        excel_layout.addStretch()
        tabs.addTab(excel_tab, "Excel")

        # ZKTeco Tab
        zk_tab = QWidget()
        zk_layout = QVBoxLayout(zk_tab)
        zk_info = QLabel(
            "ZKTeco PDKS cihazından verileri çekin.\n"
            "Cihazın ağa bağlı ve API'nin aktif olması gerekir."
        )
        zk_info.setWordWrap(True)
        zk_layout.addWidget(zk_info)

        zk_form = QFormLayout()
        self.zk_host = QLineEdit()
        self.zk_host.setPlaceholderText("192.168.1.100")
        zk_form.addRow("Cihaz IP:", self.zk_host)

        self.zk_port = QSpinBox()
        self.zk_port.setRange(1, 65535)
        self.zk_port.setValue(80)
        zk_form.addRow("Port:", self.zk_port)

        self.zk_api_key = QLineEdit()
        self.zk_api_key.setPlaceholderText("Opsiyonel")
        zk_form.addRow("API Anahtarı:", self.zk_api_key)

        dates_row = QHBoxLayout()
        self.zk_start = QDateEdit()
        self.zk_start.setCalendarPopup(True)
        self.zk_start.setDate(QDate.currentDate().addDays(-30))
        dates_row.addWidget(QLabel("Başlangıç:"))
        dates_row.addWidget(self.zk_start)

        self.zk_end = QDateEdit()
        self.zk_end.setCalendarPopup(True)
        self.zk_end.setDate(QDate.currentDate())
        dates_row.addWidget(QLabel("Bitiş:"))
        dates_row.addWidget(self.zk_end)

        zk_layout.addLayout(zk_form)
        zk_layout.addLayout(dates_row)
        zk_layout.addStretch()
        tabs.addTab(zk_tab, "ZKTeco")

        layout.addWidget(tabs)
        self.tabs = tabs

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        import_btn = QPushButton("Import Et")
        import_btn.setProperty("class", "btn-primary")
        import_btn.clicked.connect(self._do_import)
        btn_layout.addWidget(import_btn)

        layout.addLayout(btn_layout)

    def _browse_csv(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "CSV Dosyası Seç", "", "CSV Dosyaları (*.csv);;Tüm Dosyalar (*)"
        )
        if fname:
            self.csv_path.setText(fname)

    def _browse_excel(self):
        fname, _ = QFileDialog.getOpenFileName(
            self,
            "Excel Dosyası Seç",
            "",
            "Excel Dosyaları (*.xlsx *.xls);;Tüm Dosyalar (*)",
        )
        if fname:
            self.excel_path.setText(fname)

    def _do_import(self):
        c_tab = self.tabs.currentIndex()
        service = PDKSService()
        try:
            if c_tab == 0:  # CSV
                path = self.csv_path.text()
                if not path:
                    QMessageBox.warning(self, "Uyarı", "CSV dosyası seçiniz.")
                    return
                with open(path, "r", encoding="utf-8") as f:
                    suc, fai, errs = service.import_from_csv(f)
            elif c_tab == 1:  # Excel
                path = self.excel_path.text()
                if not path:
                    QMessageBox.warning(self, "Uyarı", "Excel dosyası seçiniz.")
                    return
                suc, fai, errs = service.import_from_excel(path)
            elif c_tab == 2:  # ZKTeco
                host = self.zk_host.text().strip()
                if not host:
                    QMessageBox.warning(self, "Uyarı", "Cihaz IP adresi giriniz.")
                    return
                suc, fai, errs = service.import_from_zkteco(
                    host=host,
                    port=self.zk_port.value(),
                    api_key=self.zk_api_key.text().strip() or None,
                    start_date=self.zk_start.date().toPyDate(),
                    end_date=self.zk_end.date().toPyDate(),
                )

            msg = f"Import tamamlandı!\n\nBaşarılı: {suc}\nHatalı: {fai}"
            if errs:
                msg += f"\n\nHatalar:\n" + "\n".join(errs[:10])
                if len(errs) > 10:
                    msg += f"\n... ve {len(errs) - 10} hata daha"

            if fai > 0:
                QMessageBox.warning(self, "Import Sonucu", msg)
            else:
                QMessageBox.information(self, "Import Sonucu", msg)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Import hatası: {str(e)}")
        finally:
            service.close()


class AttendanceEditDialog(QDialog):
    """Puantaj düzenleme dialogu"""

    def __init__(self, attendance_data: dict = None, parent=None):
        super().__init__(parent)
        self.attendance_data = attendance_data or {}
        self.service = HRService()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.setWindowTitle(
            "Puantaj Düzenle" if self.attendance_data else "Yeni Puantaj"
        )
        self.setMinimumSize(400, 350)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.employee = QComboBox()
        form.addRow("Çalışan:", self.employee)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("Tarih:", self.date_edit)

        self.check_in = QTimeEdit()
        self.check_in.setDisplayFormat("HH:mm")
        self.check_in.setTime(QTime(8, 0))
        form.addRow("Giriş Saati:", self.check_in)

        self.check_out = QTimeEdit()
        self.check_out.setDisplayFormat("HH:mm")
        self.check_out.setTime(QTime(17, 0))
        form.addRow("Çıkış Saati:", self.check_out)

        self.status = QComboBox()
        for status, (label, _) in ATTENDANCE_STATUS_LABELS.items():
            self.status.addItem(label, status)
        form.addRow("Durum:", self.status)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.setProperty("class", "btn-primary")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def load_data(self):
        self.employee.addItem("Seçiniz...", None)
        try:
            for emp in self.service.get_all_employees(limit=500):
                self.employee.addItem(f"{emp.full_name} ({emp.employee_no})", emp.id)
        except Exception:
            pass

        if self.attendance_data:
            e_id = self.attendance_data.get("employee_id")
            if e_id:
                idx = self.employee.findData(e_id)
                if idx >= 0:
                    self.employee.setCurrentIndex(idx)
            a_date = self.attendance_data.get("date")
            if a_date:
                self.date_edit.setDate(QDate(a_date.year, a_date.month, a_date.day))
            c_in = self.attendance_data.get("check_in")
            if c_in:
                self.check_in.setTime(QTime(c_in.hour, c_in.minute))
            c_out = self.attendance_data.get("check_out")
            if c_out:
                self.check_out.setTime(QTime(c_out.hour, c_out.minute))
            st = self.attendance_data.get("status")
            if st:
                idx = self.status.findData(st)
                if idx >= 0:
                    self.status.setCurrentIndex(idx)

    def save(self):
        if not self.employee.currentData():
            QMessageBox.warning(self, "Uyarı", "Çalışan seçiniz.")
            return
        try:
            a_dt = self.date_edit.date().toPyDate()
            ci_t = self.check_in.time().toPyTime()
            co_t = self.check_out.time().toPyTime()
            ci_dt = datetime.combine(a_dt, ci_t)
            co_dt = datetime.combine(a_dt, co_t)

            self.service.record_attendance(
                employee_id=self.employee.currentData(),
                attendance_date=a_dt,
                check_in=ci_dt,
                check_out=co_dt,
                status=self.status.currentData(),
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)


class AttendanceModule(QWidget):
    """Puantaj yönetim modülü"""

    page_title = "Puantaj"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.pdks_service = None
        self.current_year = date.today().year
        self.current_month = date.today().month
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Puantaj Yönetimi",
            icon=ICONS.CALENDAR,
            show_search=False,
            show_refresh=True,
            show_add=False,
            parent=self,
        )
        self.header.refresh_clicked.connect(self.load_data)

        h_layout = self.header.header_layout()

        h_layout.addWidget(QLabel("Dönem:"))
        self.month_combo = QComboBox()
        self.month_combo.setFixedWidth(100)
        self.month_combo.setFixedHeight(36)
        months = [
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
        for i, m in enumerate(months, 1):
            self.month_combo.addItem(m, i)
        self.month_combo.setCurrentIndex(self.current_month - 1)
        self.month_combo.currentIndexChanged.connect(self.load_data)
        h_layout.addWidget(self.month_combo)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2050)
        self.year_spin.setValue(self.current_year)
        self.year_spin.setFixedHeight(36)
        self.year_spin.valueChanged.connect(self.load_data)
        h_layout.addWidget(self.year_spin)

        h_layout.addSpacing(16)
        h_layout.addWidget(QLabel("Departman:"))
        self.dept_combo = QComboBox()
        self.dept_combo.setFixedWidth(150)
        self.dept_combo.setFixedHeight(36)
        self.dept_combo.currentIndexChanged.connect(self.load_data)
        h_layout.addWidget(self.dept_combo)

        h_layout.addStretch()

        import_btn = QPushButton("PDKS Import")
        import_btn.setIcon(qta.icon(ICONS.ADD, color="#ffffff"))
        import_btn.setFixedHeight(36)
        import_btn.setProperty("class", "btn-primary")
        import_btn.clicked.connect(self._show_import_dialog)
        h_layout.addWidget(import_btn)

        manual_btn = QPushButton("Manuel Giriş")
        manual_btn.setIcon(qta.icon(ICONS.EDIT, color="#ffffff"))
        manual_btn.setFixedHeight(36)
        manual_btn.setProperty("class", "btn-secondary")
        manual_btn.clicked.connect(self._add_manual)
        h_layout.addWidget(manual_btn)

        report_btn = QPushButton("Aylık Rapor")
        report_btn.setIcon(qta.icon(ICONS.REPORT, color="#ffffff"))
        report_btn.setFixedHeight(36)
        report_btn.clicked.connect(self._show_monthly_report)
        h_layout.addWidget(report_btn)

        layout.addWidget(self.header)

        # Özet kartları
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(16)
        self.stat_cards = {
            "present": MiniStatCard("Mevcut", "0", "success", icon=ICONS.CHECK),
            "late": MiniStatCard("Geç Kalan", "0", "warning", icon=ICONS.TIME),
            "absent": MiniStatCard("Devamsız", "0", "error", icon=ICONS.CLOSE),
            "leave": MiniStatCard("İzinli", "0", "info", icon=ICONS.CALENDAR),
        }
        for card in self.stat_cards.values():
            summary_layout.addWidget(card)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Tablo
        columns = [
            ColumnConfig("employee_no", "Sicil No", width=100),
            ColumnConfig("employee_name", "Çalışan", width=200, stretch=True),
            ColumnConfig("department", "Departman", width=150),
            ColumnConfig("present_days", "Mevcut", width=80),
            ColumnConfig("late_days", "Geç", width=80),
            ColumnConfig("absent_days", "Devamsız", width=80),
            ColumnConfig("leave_days", "İzin", width=80),
            ColumnConfig("total_hours", "Toplam Saat", width=100),
        ]
        self.table = EnhancedTableWidget(
            table_id="attendance_summary", columns=columns, parent=self
        )
        layout.addWidget(self.table)

    def _get_service(self):
        if self.service is None:
            self.service = HRService()
        return self.service

    def _get_pdks_service(self):
        if self.pdks_service is None:
            self.pdks_service = PDKSService()
        return self.pdks_service

    def _close_services(self):
        if self.service:
            self.service.close()
            self.service = None
        if self.pdks_service:
            self.pdks_service.close()
            self.pdks_service = None

    def load_data(self):
        """Puantaj verilerini yükle"""
        try:
            if self.dept_combo.count() == 0:
                service = self._get_service()
                self.dept_combo.addItem("Tümü", None)
                for dept in service.get_all_departments():
                    self.dept_combo.addItem(dept.name, dept.id)

            pdks = self._get_pdks_service()
            year = self.year_spin.value()
            month = self.month_combo.currentData()
            dept_id = self.dept_combo.currentData()

            summary = pdks.get_monthly_summary(year, month, dept_id)
            self.table.setRowCount(len(summary))

            t_pres, t_late, t_abs, t_leav = 0, 0, 0, 0
            visible_cols = self.table.get_visible_columns()

            for row, data in enumerate(summary):
                self._populate_row(row, data, visible_cols)
                t_pres += data["present_days"]
                t_late += data["late_days"]
                t_abs += data["absent_days"]
                t_leav += data["leave_days"]

            self.stat_cards["present"].update_value(str(t_pres))
            self.stat_cards["late"].update_value(str(t_late))
            self.stat_cards["absent"].update_value(str(t_abs))
            self.stat_cards["leave"].update_value(str(t_leav))

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Hata: {str(e)}")
        finally:
            self._close_services()

    def _populate_row(self, row, data, visible_cols):
        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "employee_no":
                self.table.setItem(row, col_idx, QTableWidgetItem(data["employee_no"]))
            elif col_key == "employee_name":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(data["employee_name"])
                )
            elif col_key == "department":
                self.table.setItem(row, col_idx, QTableWidgetItem(data["department"]))
            elif col_key == "present_days":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(str(data["present_days"]))
                )
            elif col_key == "late_days":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(str(data["late_days"]))
                )
            elif col_key == "absent_days":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(str(data["absent_days"]))
                )
            elif col_key == "leave_days":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(str(data["leave_days"]))
                )
            elif col_key == "total_hours":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(f"{data['total_work_hours']:.1f}")
                )

    def _show_import_dialog(self):
        dialog = PDKSImportDialog(parent=self)
        if dialog.exec():
            self.load_data()

    def _add_manual(self):
        dialog = AttendanceEditDialog(parent=self)
        if dialog.exec():
            self.load_data()

    def _show_monthly_report(self):
        try:
            pdks = self._get_pdks_service()
            y, m = self.year_spin.value(), self.month_combo.currentData()
            summary = pdks.get_monthly_summary(y, m)

            rep = f"AYLIK PUANTAJ RAPORU - {self.month_combo.currentText()} {y}\n"
            rep += "=" * 60 + "\n\n"
            for d in summary:
                rep += f"{d['employee_no']} - {d['employee_name']}\n"
                rep += f"  Mevcut: {d['present_days']}, Geç: {d['late_days']}, "
                rep += f"Devamsız: {d['absent_days']}, İzin: {d['leave_days']}\n"
                rep += f"  Toplam Saat: {d['total_work_hours']:.1f}, "
                rep += f"Fazla Mesai: {d['overtime_hours']:.1f}\n\n"
            QMessageBox.information(self, "Aylık Rapor", rep[:2000])
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Hata: {str(e)}")
        finally:
            self._close_services()
