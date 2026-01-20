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

from config.styles import (
    BG_PRIMARY,
    BG_SECONDARY,
    BORDER,
    TEXT_PRIMARY,
    ACCENT,
    SUCCESS,
    WARNING,
    ERROR,
    get_button_style,
    BTN_HEIGHT_NORMAL,
    ICONS,
)
from modules.hr.services import HRService
from modules.hr.services.pdks_service import PDKSService, PDKSSource
from database.models.hr import AttendanceStatus


ATTENDANCE_STATUS_LABELS = {
    AttendanceStatus.PRESENT: ("Mevcut", SUCCESS),
    AttendanceStatus.ABSENT: ("Yok", ERROR),
    AttendanceStatus.LATE: ("Geç Kaldı", WARNING),
    AttendanceStatus.EARLY_LEAVE: ("Erken Çıktı", WARNING),
    AttendanceStatus.ON_LEAVE: ("İzinli", ACCENT),
    AttendanceStatus.HOLIDAY: ("Tatil", ACCENT),
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

        # Tab widget - farklı import yöntemleri
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

        csv_browse = QPushButton(f"{ICONS['search']} Gözat")
        csv_browse.clicked.connect(self._browse_csv)
        csv_file_row.addWidget(csv_browse)
        csv_layout.addLayout(csv_file_row)

        csv_layout.addStretch()
        tabs.addTab(csv_tab, f"{ICONS['report']} CSV")

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

        excel_browse = QPushButton(f"{ICONS['search']} Gözat")
        excel_browse.clicked.connect(self._browse_excel)
        excel_file_row.addWidget(excel_browse)
        excel_layout.addLayout(excel_file_row)

        excel_layout.addStretch()
        tabs.addTab(excel_tab, f"{ICONS['report']} Excel")

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
        tabs.addTab(zk_tab, f"{ICONS['filter']} ZKTeco")

        layout.addWidget(tabs)
        self.tabs = tabs

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton(f"{ICONS['cancel']} İptal")
        cancel_btn.setStyleSheet(get_button_style("cancel"))
        cancel_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        import_btn = QPushButton(f"{ICONS['add']} Import Et")
        import_btn.setStyleSheet(get_button_style("add"))
        import_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        import_btn.clicked.connect(self._do_import)
        btn_layout.addWidget(import_btn)

        layout.addLayout(btn_layout)

    def _browse_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "CSV Dosyası Seç", "", "CSV Dosyaları (*.csv);;Tüm Dosyalar (*)"
        )
        if path:
            self.csv_path.setText(path)

    def _browse_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Excel Dosyası Seç",
            "",
            "Excel Dosyaları (*.xlsx *.xls);;Tüm Dosyalar (*)",
        )
        if path:
            self.excel_path.setText(path)

    def _do_import(self):
        current_tab = self.tabs.currentIndex()
        service = PDKSService()

        try:
            if current_tab == 0:  # CSV
                path = self.csv_path.text()
                if not path:
                    QMessageBox.warning(self, "Uyarı", "CSV dosyası seçiniz.")
                    return

                with open(path, "r", encoding="utf-8") as f:
                    success, failed, errors = service.import_from_csv(f)

            elif current_tab == 1:  # Excel
                path = self.excel_path.text()
                if not path:
                    QMessageBox.warning(self, "Uyarı", "Excel dosyası seçiniz.")
                    return

                success, failed, errors = service.import_from_excel(path)

            elif current_tab == 2:  # ZKTeco
                host = self.zk_host.text().strip()
                if not host:
                    QMessageBox.warning(self, "Uyarı", "Cihaz IP adresi giriniz.")
                    return

                success, failed, errors = service.import_from_zkteco(
                    host=host,
                    port=self.zk_port.value(),
                    api_key=self.zk_api_key.text().strip() or None,
                    start_date=self.zk_start.date().toPyDate(),
                    end_date=self.zk_end.date().toPyDate(),
                )

            # Sonuç göster
            msg = f"Import tamamlandı!\n\nBaşarılı: {success}\nHatalı: {failed}"
            if errors:
                msg += f"\n\nHatalar:\n" + "\n".join(errors[:10])
                if len(errors) > 10:
                    msg += f"\n... ve {len(errors) - 10} hata daha"

            if failed > 0:
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
        self.setMinimumSize(400, 300)

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

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton(f"{ICONS['cancel']} İptal")
        cancel_btn.setStyleSheet(get_button_style("cancel"))
        cancel_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton(f"{ICONS['save']} Kaydet")
        save_btn.setStyleSheet(get_button_style("confirm"))
        save_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def load_data(self):
        # Çalışanları yükle
        self.employee.addItem("Seçiniz...", None)
        try:
            for emp in self.service.get_all_employees(limit=500):
                self.employee.addItem(f"{emp.full_name} ({emp.employee_no})", emp.id)
        except Exception:
            pass

        # Mevcut veriyi yükle
        if self.attendance_data:
            # Employee
            emp_id = self.attendance_data.get("employee_id")
            if emp_id:
                idx = self.employee.findData(emp_id)
                if idx >= 0:
                    self.employee.setCurrentIndex(idx)

            # Date
            att_date = self.attendance_data.get("date")
            if att_date:
                self.date_edit.setDate(
                    QDate(att_date.year, att_date.month, att_date.day)
                )

            # Check in/out
            check_in = self.attendance_data.get("check_in")
            if check_in:
                self.check_in.setTime(QTime(check_in.hour, check_in.minute))

            check_out = self.attendance_data.get("check_out")
            if check_out:
                self.check_out.setTime(QTime(check_out.hour, check_out.minute))

            # Status
            status = self.attendance_data.get("status")
            if status:
                idx = self.status.findData(status)
                if idx >= 0:
                    self.status.setCurrentIndex(idx)

    def save(self):
        if not self.employee.currentData():
            QMessageBox.warning(self, "Uyarı", "Çalışan seçiniz.")
            return

        try:
            att_date = self.date_edit.date().toPyDate()
            check_in_time = self.check_in.time().toPyTime()
            check_out_time = self.check_out.time().toPyTime()

            check_in_dt = datetime.combine(att_date, check_in_time)
            check_out_dt = datetime.combine(att_date, check_out_time)

            self.service.record_attendance(
                employee_id=self.employee.currentData(),
                attendance_date=att_date,
                check_in=check_in_dt,
                check_out=check_out_dt,
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # === Header - PageHeader kullanarak ===
        from ui.components.page_header import PageHeader

        self.header = PageHeader(
            title="Puantaj Yönetimi",
            icon="📅",
            show_search=False,
            show_refresh=True,  # Yenile butonu yerine bunu kullanabiliriz ama özel logic var
            show_add=False,
            parent=self,
        )
        self.header.refresh_clicked.connect(self.load_data)

        # Header Layout - Butonlar ve Filtreler
        h_layout = self.header.header_layout()

        # Filtreler
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

        # Custom Butonlar
        # PDKS Import
        import_btn = QPushButton(f"{ICONS['add']} PDKS Import")
        import_btn.setStyleSheet(get_button_style("add"))
        import_btn.setFixedHeight(36)
        import_btn.clicked.connect(self._show_import_dialog)
        h_layout.addWidget(import_btn)

        # Manuel Giriş
        manual_btn = QPushButton(f"{ICONS['edit']} Manuel Giriş")
        manual_btn.setStyleSheet(get_button_style("edit"))
        manual_btn.setFixedHeight(36)
        manual_btn.clicked.connect(self._add_manual)
        h_layout.addWidget(manual_btn)

        # Rapor
        report_btn = QPushButton(f"{ICONS['report']} Aylık Rapor")
        report_btn.setStyleSheet(get_button_style("default"))
        report_btn.setFixedHeight(36)
        report_btn.clicked.connect(self._show_monthly_report)
        h_layout.addWidget(report_btn)

        layout.addWidget(self.header)

        # Filtreler
        filter_row = QHBoxLayout()

        # Ay seçici
        filter_row.addWidget(QLabel("Dönem:"))

        self.month_combo = QComboBox()
        self.month_combo.setFixedWidth(120)
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
        filter_row.addWidget(self.month_combo)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2050)
        self.year_spin.setValue(self.current_year)
        self.year_spin.valueChanged.connect(self.load_data)
        filter_row.addWidget(self.year_spin)

        # Departman filtresi
        filter_row.addWidget(QLabel("Departman:"))
        self.dept_combo = QComboBox()
        self.dept_combo.setFixedWidth(150)
        self.dept_combo.currentIndexChanged.connect(self.load_data)
        filter_row.addWidget(self.dept_combo)

        filter_row.addStretch()

        layout.addLayout(filter_row)

        # Özet kartları
        summary_row = QHBoxLayout()
        summary_row.setSpacing(16)

        self.present_card = self._create_summary_card("Mevcut", "0", SUCCESS)
        summary_row.addWidget(self.present_card)

        self.late_card = self._create_summary_card("Geç Kalan", "0", WARNING)
        summary_row.addWidget(self.late_card)

        self.absent_card = self._create_summary_card("Devamsız", "0", ERROR)
        summary_row.addWidget(self.absent_card)

        self.leave_card = self._create_summary_card("İzinli", "0", ACCENT)
        summary_row.addWidget(self.leave_card)

        layout.addLayout(summary_row)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "Sicil No",
                "Çalışan",
                "Departman",
                "Mevcut",
                "Geç",
                "Devamsız",
                "İzin",
                "Toplam Saat",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def _create_summary_card(self, label: str, value: str, color: str) -> QGroupBox:
        """Özet kartı oluştur"""
        card = QGroupBox()
        card.setStyleSheet(
            f"""
            QGroupBox {{
                background: {BG_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 12px;
            }}
        """
        )

        layout = QVBoxLayout(card)
        layout.setSpacing(4)

        value_label = QLabel(value)
        value_label.setStyleSheet(
            f"font-size: 24px; font-weight: bold; color: {color};"
        )
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setObjectName("value")
        layout.addWidget(value_label)

        text_label = QLabel(label)
        text_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)

        return card

    def _update_summary_card(self, card: QGroupBox, value: str):
        """Özet kartı değerini güncelle"""
        value_label = card.findChild(QLabel, "value")
        if value_label:
            value_label.setText(value)

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
            # Departmanları yükle (ilk yüklemede)
            if self.dept_combo.count() == 0:
                service = self._get_service()
                self.dept_combo.addItem("Tümü", None)
                for dept in service.get_all_departments():
                    self.dept_combo.addItem(dept.name, dept.id)

            # Aylık özeti al
            pdks = self._get_pdks_service()
            year = self.year_spin.value()
            month = self.month_combo.currentData()
            dept_id = self.dept_combo.currentData()

            summary = pdks.get_monthly_summary(year, month, dept_id)

            # Tabloyu doldur
            self.table.setRowCount(len(summary))

            total_present = 0
            total_late = 0
            total_absent = 0
            total_leave = 0

            for row, data in enumerate(summary):
                self.table.setItem(row, 0, QTableWidgetItem(data["employee_no"]))
                self.table.setItem(row, 1, QTableWidgetItem(data["employee_name"]))
                self.table.setItem(row, 2, QTableWidgetItem(data["department"]))
                self.table.setItem(row, 3, QTableWidgetItem(str(data["present_days"])))
                self.table.setItem(row, 4, QTableWidgetItem(str(data["late_days"])))
                self.table.setItem(row, 5, QTableWidgetItem(str(data["absent_days"])))
                self.table.setItem(row, 6, QTableWidgetItem(str(data["leave_days"])))
                self.table.setItem(
                    row, 7, QTableWidgetItem(f"{data['total_work_hours']:.1f}")
                )

                total_present += data["present_days"]
                total_late += data["late_days"]
                total_absent += data["absent_days"]
                total_leave += data["leave_days"]

            # Özet kartlarını güncelle
            self._update_summary_card(self.present_card, str(total_present))
            self._update_summary_card(self.late_card, str(total_late))
            self._update_summary_card(self.absent_card, str(total_absent))
            self._update_summary_card(self.leave_card, str(total_leave))

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Hata: {str(e)}")
        finally:
            self._close_services()

    def _show_import_dialog(self):
        """PDKS import dialogunu göster"""
        dialog = PDKSImportDialog(parent=self)
        if dialog.exec():
            self.load_data()

    def _add_manual(self):
        """Manuel puantaj girişi"""
        dialog = AttendanceEditDialog(parent=self)
        if dialog.exec():
            self.load_data()

    def _show_monthly_report(self):
        """Aylık rapor göster/dışa aktar"""
        try:
            pdks = self._get_pdks_service()
            year = self.year_spin.value()
            month = self.month_combo.currentData()

            summary = pdks.get_monthly_summary(year, month)

            # Basit rapor dialogu
            report_text = (
                f"AYLIK PUANTAJ RAPORU - {self.month_combo.currentText()} {year}\n"
            )
            report_text += "=" * 60 + "\n\n"

            for data in summary:
                report_text += f"{data['employee_no']} - {data['employee_name']}\n"
                report_text += (
                    f"  Mevcut: {data['present_days']}, Geç: {data['late_days']}, "
                )
                report_text += (
                    f"Devamsız: {data['absent_days']}, İzin: {data['leave_days']}\n"
                )
                report_text += f"  Toplam Saat: {data['total_work_hours']:.1f}, "
                report_text += f"Fazla Mesai: {data['overtime_hours']:.1f}\n\n"

            QMessageBox.information(self, "Aylık Rapor", report_text[:2000])

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Hata: {str(e)}")
        finally:
            self._close_services()
