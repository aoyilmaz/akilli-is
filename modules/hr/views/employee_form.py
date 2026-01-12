"""
Akıllı İş - Çalışan Form Dialogu
"""

from datetime import date
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QPushButton,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QTextEdit,
    QMessageBox,
    QLabel,
    QTabWidget,
    QWidget,
    QGroupBox,
)
from PyQt6.QtCore import Qt, QDate

from config.styles import (
    BG_PRIMARY,
    BG_SECONDARY,
    BORDER,
    TEXT_PRIMARY,
    ACCENT,
    get_button_style,
)
from modules.hr.services import HRService
from database.models.hr import EmploymentType, Gender


class EmployeeFormDialog(QDialog):
    """Çalışan ekleme/düzenleme dialogu"""

    def __init__(self, employee_id: int = None, parent=None):
        super().__init__(parent)
        self.employee_id = employee_id
        self.service = HRService()
        self.setup_ui()
        self.load_combos()
        if employee_id:
            self.load_employee()

    def setup_ui(self):
        self.setWindowTitle("Çalışan Düzenle" if self.employee_id else "Yeni Çalışan")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Tab widget
        tabs = QTabWidget()

        # Temel Bilgiler Tab
        basic_tab = QWidget()
        basic_layout = QFormLayout(basic_tab)
        basic_layout.setSpacing(12)

        self.employee_no = QLineEdit()
        self.employee_no.setPlaceholderText("Otomatik oluşturulur")
        basic_layout.addRow("Sicil No:", self.employee_no)

        self.first_name = QLineEdit()
        basic_layout.addRow("Ad:", self.first_name)

        self.last_name = QLineEdit()
        basic_layout.addRow("Soyad:", self.last_name)

        self.email = QLineEdit()
        basic_layout.addRow("Email:", self.email)

        self.phone = QLineEdit()
        basic_layout.addRow("Telefon:", self.phone)

        self.tc_no = QLineEdit()
        self.tc_no.setMaxLength(11)
        basic_layout.addRow("TC Kimlik No:", self.tc_no)

        self.birth_date = QDateEdit()
        self.birth_date.setCalendarPopup(True)
        self.birth_date.setDate(QDate(1990, 1, 1))
        basic_layout.addRow("Doğum Tarihi:", self.birth_date)

        self.gender = QComboBox()
        self.gender.addItem("Erkek", Gender.MALE)
        self.gender.addItem("Kadın", Gender.FEMALE)
        self.gender.addItem("Diğer", Gender.OTHER)
        basic_layout.addRow("Cinsiyet:", self.gender)

        tabs.addTab(basic_tab, "Temel Bilgiler")

        # İş Bilgileri Tab
        work_tab = QWidget()
        work_layout = QFormLayout(work_tab)
        work_layout.setSpacing(12)

        self.department = QComboBox()
        work_layout.addRow("Departman:", self.department)

        self.position = QComboBox()
        work_layout.addRow("Pozisyon:", self.position)

        self.manager = QComboBox()
        work_layout.addRow("Yönetici:", self.manager)

        self.hire_date = QDateEdit()
        self.hire_date.setCalendarPopup(True)
        self.hire_date.setDate(QDate.currentDate())
        work_layout.addRow("İşe Giriş:", self.hire_date)

        self.employment_type = QComboBox()
        self.employment_type.addItem("Tam Zamanlı", EmploymentType.FULL_TIME)
        self.employment_type.addItem("Yarı Zamanlı", EmploymentType.PART_TIME)
        self.employment_type.addItem("Sözleşmeli", EmploymentType.CONTRACT)
        self.employment_type.addItem("Stajyer", EmploymentType.INTERN)
        self.employment_type.addItem("Geçici", EmploymentType.TEMPORARY)
        work_layout.addRow("İstihdam Türü:", self.employment_type)

        self.shift_team = QComboBox()
        work_layout.addRow("Vardiya Ekibi:", self.shift_team)

        self.salary = QLineEdit()
        self.salary.setPlaceholderText("0.00")
        work_layout.addRow("Maaş:", self.salary)

        tabs.addTab(work_tab, "İş Bilgileri")

        # Adres Tab
        address_tab = QWidget()
        address_layout = QFormLayout(address_tab)
        address_layout.setSpacing(12)

        self.mobile = QLineEdit()
        address_layout.addRow("Cep Telefonu:", self.mobile)

        self.address = QTextEdit()
        self.address.setMaximumHeight(100)
        address_layout.addRow("Adres:", self.address)

        tabs.addTab(address_tab, "İletişim")

        layout.addWidget(tabs)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def load_combos(self):
        """Combo box'ları doldur"""
        try:
            # Departmanlar
            self.department.addItem("Seçiniz...", None)
            for dept in self.service.get_all_departments():
                self.department.addItem(dept.name, dept.id)
            self.department.currentIndexChanged.connect(self._on_dept_changed)

            # Pozisyonlar
            self.position.addItem("Seçiniz...", None)
            for pos in self.service.get_all_positions():
                self.position.addItem(pos.name, pos.id)

            # Yöneticiler
            self.manager.addItem("Seçiniz...", None)
            for emp in self.service.get_all_employees(limit=500):
                if emp.id != self.employee_id:
                    self.manager.addItem(f"{emp.full_name} ({emp.employee_no})", emp.id)

            # Vardiya Ekipleri
            self.shift_team.addItem("Seçiniz...", None)
            try:
                from modules.production.calendar_services import ShiftTeamService

                team_service = ShiftTeamService()
                for team in team_service.get_all():
                    self.shift_team.addItem(f"{team.code} - {team.name}", team.id)
            except Exception:
                pass
        except Exception as e:
            print(f"Combo yükleme hatası: {e}")

    def _on_dept_changed(self, index):
        """Departman değiştiğinde pozisyonları filtrele"""
        dept_id = self.department.currentData()
        self.position.clear()
        self.position.addItem("Seçiniz...", None)
        try:
            if dept_id:
                positions = self.service.get_positions_by_department(dept_id)
            else:
                positions = self.service.get_all_positions()
            for pos in positions:
                self.position.addItem(pos.name, pos.id)
        except Exception:
            pass

    def load_employee(self):
        """Mevcut çalışanı yükle"""
        try:
            emp = self.service.get_employee_by_id(self.employee_id)
            if emp:
                self.employee_no.setText(emp.employee_no)
                self.employee_no.setReadOnly(True)
                self.first_name.setText(emp.first_name)
                self.last_name.setText(emp.last_name)
                self.email.setText(emp.email or "")
                self.phone.setText(emp.phone or "")
                self.tc_no.setText(emp.tc_no or "")
                self.mobile.setText(emp.mobile or "")
                self.address.setPlainText(emp.address or "")

                if emp.birth_date:
                    self.birth_date.setDate(
                        QDate(
                            emp.birth_date.year,
                            emp.birth_date.month,
                            emp.birth_date.day,
                        )
                    )

                if emp.hire_date:
                    self.hire_date.setDate(
                        QDate(
                            emp.hire_date.year, emp.hire_date.month, emp.hire_date.day
                        )
                    )

                if emp.gender:
                    idx = self.gender.findData(emp.gender)
                    if idx >= 0:
                        self.gender.setCurrentIndex(idx)

                if emp.employment_type:
                    idx = self.employment_type.findData(emp.employment_type)
                    if idx >= 0:
                        self.employment_type.setCurrentIndex(idx)

                if emp.department_id:
                    idx = self.department.findData(emp.department_id)
                    if idx >= 0:
                        self.department.setCurrentIndex(idx)

                if emp.position_id:
                    idx = self.position.findData(emp.position_id)
                    if idx >= 0:
                        self.position.setCurrentIndex(idx)

                if emp.manager_id:
                    idx = self.manager.findData(emp.manager_id)
                    if idx >= 0:
                        self.manager.setCurrentIndex(idx)

                if emp.salary:
                    self.salary.setText(str(emp.salary))

                if emp.shift_team_id:
                    idx = self.shift_team.findData(emp.shift_team_id)
                    if idx >= 0:
                        self.shift_team.setCurrentIndex(idx)

        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Çalışan yüklenirken hata: {str(e)}")

    def save(self):
        """Kaydet"""
        # Validasyon
        if not self.first_name.text().strip():
            QMessageBox.warning(self, "Uyarı", "Ad alanı zorunludur.")
        if not self.last_name.text().strip():
            QMessageBox.warning(self, "Uyarı", "Soyad alanı zorunludur.")

        try:
            data = {
                "first_name": self.first_name.text().strip(),
                "last_name": self.last_name.text().strip(),
                "email": self.email.text().strip() or None,
                "phone": self.phone.text().strip() or None,
                "mobile": self.mobile.text().strip() or None,
                "tc_no": self.tc_no.text().strip() or None,
                "address": self.address.toPlainText().strip() or None,
                "birth_date": self.birth_date.date().toPyDate(),
                "hire_date": self.hire_date.date().toPyDate(),
                "gender": self.gender.currentData(),
                "employment_type": self.employment_type.currentData(),
                "department_id": self.department.currentData(),
                "position_id": self.position.currentData(),
                "manager_id": self.manager.currentData(),
                "shift_team_id": self.shift_team.currentData(),
            }

            if self.salary.text().strip():
                try:
                    data["salary"] = float(self.salary.text().strip())
                except ValueError:
                    pass

            if self.employee_no.text().strip() and not self.employee_id:
                data["employee_no"] = self.employee_no.text().strip()

            if self.employee_id:
                self.service.update_employee(self.employee_id, data)
            else:
                self.service.create_employee(data)

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt sırasında hata: {str(e)}")

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)
