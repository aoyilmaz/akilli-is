"""
Akıllı İş - Çalışan Form Dialogu
"""

from datetime import date
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
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
    QFileDialog,
    QFrame,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QPixmap

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
        self.photo_path = None  # Seçilen fotoğraf dosyası
        self.setup_ui()
        self.load_combos()
        if employee_id:
            self.load_employee()

    def setup_ui(self):
        self.setWindowTitle("Çalışan Düzenle" if self.employee_id else "Yeni Çalışan")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet(
            """
            QTabWidget::pane { border: 1px solid #3e3e42; border-radius: 4px; }
            QTabBar::tab { height: 32px; padding: 0 16px; min-width: 100px; }
        """
        )

        # --- Temel Bilgiler Tab ---
        basic_tab = QWidget()
        basic_layout = QHBoxLayout(basic_tab)
        basic_layout.setSpacing(24)
        basic_layout.setContentsMargins(16, 16, 16, 16)

        # Sol Kolon (Kişisel Bilgiler)
        left_col = QVBoxLayout()
        left_col.setSpacing(16)

        # Grup: Kimlik Bilgileri
        id_group = QGroupBox("Kimlik Bilgileri")
        id_layout = QGridLayout(id_group)
        id_layout.setSpacing(12)
        id_layout.setColumnStretch(1, 1)

        self.employee_no = QLineEdit()
        self.employee_no.setPlaceholderText("Otomatik")
        self.employee_no.setFixedHeight(32)
        id_layout.addWidget(QLabel("Sicil No:"), 0, 0)
        id_layout.addWidget(self.employee_no, 0, 1)

        self.first_name = QLineEdit()
        self.first_name.setFixedHeight(32)
        id_layout.addWidget(QLabel("Ad:"), 1, 0)
        id_layout.addWidget(self.first_name, 1, 1)

        self.last_name = QLineEdit()
        self.last_name.setFixedHeight(32)
        id_layout.addWidget(QLabel("Soyad:"), 2, 0)
        id_layout.addWidget(self.last_name, 2, 1)

        self.tc_no = QLineEdit()
        self.tc_no.setMaxLength(11)
        self.tc_no.setFixedHeight(32)
        id_layout.addWidget(QLabel("TC No:"), 3, 0)
        id_layout.addWidget(self.tc_no, 3, 1)

        self.gender = QComboBox()
        self.gender.setFixedHeight(32)
        self.gender.addItems(["Erkek", "Kadın", "Diğer"])
        self.gender.setItemData(0, Gender.MALE)
        self.gender.setItemData(1, Gender.FEMALE)
        self.gender.setItemData(2, Gender.OTHER)
        id_layout.addWidget(QLabel("Cinsiyet:"), 4, 0)
        id_layout.addWidget(self.gender, 4, 1)

        self.birth_date = QDateEdit()
        self.birth_date.setCalendarPopup(True)
        self.birth_date.setDate(QDate(1990, 1, 1))
        self.birth_date.setFixedHeight(32)
        id_layout.addWidget(QLabel("Doğum Tarihi:"), 5, 0)
        id_layout.addWidget(self.birth_date, 5, 1)

        left_col.addWidget(id_group)
        basic_layout.addLayout(left_col, stretch=2)

        # Sağ Kolon (Fotoğraf ve İletişim Özeti)
        right_col = QVBoxLayout()
        right_col.setSpacing(16)

        # Grup: Fotoğraf
        photo_group = QGroupBox("Fotoğraf")
        photo_layout = QVBoxLayout(photo_group)
        photo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.photo_label = QLabel()
        self.photo_label.setFixedSize(140, 160)
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setStyleSheet(
            """
            QLabel {
                background-color: #1e1e1e;
                border: 2px dashed #3e3e42;
                border-radius: 8px;
                color: #64748b;
            }
        """
        )
        self.photo_label.setText("👤\nFotoğraf")
        photo_layout.addWidget(self.photo_label)

        btn_row = QHBoxLayout()
        select_photo_btn = QPushButton("📂 Seç")
        select_photo_btn.setFixedHeight(30)
        select_photo_btn.clicked.connect(self._select_photo)
        btn_row.addWidget(select_photo_btn)

        clear_photo_btn = QPushButton("🗑 Kaldır")
        clear_photo_btn.setFixedHeight(30)
        clear_photo_btn.clicked.connect(self._clear_photo)
        btn_row.addWidget(clear_photo_btn)
        photo_layout.addLayout(btn_row)

        right_col.addWidget(photo_group)
        right_col.addStretch()
        basic_layout.addLayout(right_col, stretch=1)

        tabs.addTab(basic_tab, "Temel Bilgiler")

        # --- İş Bilgileri Tab ---
        work_tab = QWidget()
        work_layout = QVBoxLayout(work_tab)
        work_layout.setContentsMargins(16, 16, 16, 16)
        work_layout.setSpacing(16)

        # Grup: Organizasyon
        org_group = QGroupBox("Organizasyon")
        org_grid = QGridLayout(org_group)
        org_grid.setSpacing(12)
        org_grid.setColumnStretch(1, 1)
        org_grid.setColumnStretch(3, 1)

        self.department = QComboBox()
        self.department.setFixedHeight(32)
        org_grid.addWidget(QLabel("Departman:"), 0, 0)
        org_grid.addWidget(self.department, 0, 1)

        self.position = QComboBox()
        self.position.setFixedHeight(32)
        org_grid.addWidget(QLabel("Pozisyon:"), 0, 2)
        org_grid.addWidget(self.position, 0, 3)

        self.manager = QComboBox()
        self.manager.setFixedHeight(32)
        org_grid.addWidget(QLabel("Yönetici:"), 1, 0)
        org_grid.addWidget(self.manager, 1, 1)

        self.shift_team = QComboBox()
        self.shift_team.setFixedHeight(32)
        org_grid.addWidget(QLabel("Vardiya Ekibi:"), 1, 2)
        org_grid.addWidget(self.shift_team, 1, 3)

        work_layout.addWidget(org_group)

        # Grup: İstihdam Detayları
        emp_group = QGroupBox("İstihdam Detayları")
        emp_grid = QGridLayout(emp_group)
        emp_grid.setSpacing(12)
        emp_grid.setColumnStretch(1, 1)
        emp_grid.setColumnStretch(3, 1)

        self.hire_date = QDateEdit()
        self.hire_date.setCalendarPopup(True)
        self.hire_date.setDate(QDate.currentDate())
        self.hire_date.setFixedHeight(32)
        emp_grid.addWidget(QLabel("İşe Giriş:"), 0, 0)
        emp_grid.addWidget(self.hire_date, 0, 1)

        self.employment_type = QComboBox()
        self.employment_type.setFixedHeight(32)
        self.employment_type.addItem("Tam Zamanlı", EmploymentType.FULL_TIME)
        self.employment_type.addItem("Yarı Zamanlı", EmploymentType.PART_TIME)
        self.employment_type.addItem("Sözleşmeli", EmploymentType.CONTRACT)
        self.employment_type.addItem("Stajyer", EmploymentType.INTERN)
        self.employment_type.addItem("Geçici", EmploymentType.TEMPORARY)
        emp_grid.addWidget(QLabel("Çalışma Şekli:"), 0, 2)
        emp_grid.addWidget(self.employment_type, 0, 3)

        self.salary = QLineEdit()
        self.salary.setPlaceholderText("0.00")
        self.salary.setFixedHeight(32)
        emp_grid.addWidget(QLabel("Maaş (TL):"), 1, 0)
        emp_grid.addWidget(self.salary, 1, 1)

        work_layout.addWidget(emp_group)
        work_layout.addStretch()

        tabs.addTab(work_tab, "İş Bilgileri")

        # --- İletişim Tab ---
        contact_tab = QWidget()
        contact_layout = QVBoxLayout(contact_tab)
        contact_layout.setContentsMargins(16, 16, 16, 16)
        contact_layout.setSpacing(16)

        contact_group = QGroupBox("İletişim")
        contact_grid = QGridLayout(contact_group)
        contact_grid.setSpacing(12)
        contact_grid.setColumnStretch(1, 1)

        self.email = QLineEdit()
        self.email.setFixedHeight(32)
        contact_grid.addWidget(QLabel("E-Posta:"), 0, 0)
        contact_grid.addWidget(self.email, 0, 1)

        self.phone = QLineEdit()
        self.phone.setFixedHeight(32)
        contact_grid.addWidget(QLabel("Telefon:"), 1, 0)
        contact_grid.addWidget(self.phone, 1, 1)

        self.mobile = QLineEdit()
        self.mobile.setFixedHeight(32)
        contact_grid.addWidget(QLabel("Cep Telefonu:"), 2, 0)
        contact_grid.addWidget(self.mobile, 2, 1)

        self.address = QTextEdit()
        self.address.setPlaceholderText("Açık adres...")
        contact_grid.addWidget(QLabel("Adres:"), 3, 0, 1, 2)
        contact_grid.addWidget(self.address, 4, 0, 1, 2)

        contact_layout.addWidget(contact_group)
        contact_layout.addStretch()

        tabs.addTab(contact_tab, "İletişim")

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

                # Mevcut fotoğrafı yükle
                if emp.photo:
                    self._load_existing_photo(emp.photo)

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
                emp = self.service.update_employee(self.employee_id, data)
            else:
                emp = self.service.create_employee(data)

            # Fotoğrafı kaydet
            if self.photo_path and emp:
                self._save_photo(emp.employee_no)

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt sırasında hata: {str(e)}")

    def _select_photo(self):
        """Fotoğraf dosyası seç"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Fotoğraf Seç", "", "Resim Dosyaları (*.jpg *.jpeg *.png *.bmp)"
        )

        if file_path:
            self.photo_path = file_path
            self._show_photo_preview(file_path)

    def _show_photo_preview(self, path: str):
        """Fotoğraf önizlemesini göster"""
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                120,
                150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.photo_label.setPixmap(scaled)

    def _clear_photo(self):
        """Fotoğrafı kaldır"""
        self.photo_path = None
        self.photo_label.clear()
        self.photo_label.setText("👤\nFotoğraf")

    def _save_photo(self, employee_no: str):
        """Fotoğrafı kaydet"""
        import os
        import shutil

        # Hedef klasör
        photo_dir = os.path.join("assets", "photos", "employees")
        os.makedirs(photo_dir, exist_ok=True)

        # Uzantıyı al
        ext = os.path.splitext(self.photo_path)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png"]:
            ext = ".jpg"

        # Hedef dosya
        filename = f"{employee_no}{ext}"
        dest_path = os.path.join(photo_dir, filename)

        # Kopyala
        shutil.copy2(self.photo_path, dest_path)

        # Veritabanını güncelle
        if self.employee_id:
            self.service.update_employee(self.employee_id, {"photo": filename})

    def _load_existing_photo(self, photo_filename: str):
        """Mevcut fotoğrafı yükle"""
        import os

        if not photo_filename:
            return

        photo_path = os.path.join("assets", "photos", "employees", photo_filename)
        if os.path.exists(photo_path):
            self._show_photo_preview(photo_path)

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)
