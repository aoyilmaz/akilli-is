"""
Akıllı İş - Çalışan Yönetim Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QLabel,
    QFrame,
)
from PyQt6.QtCore import Qt

from config.styles import (
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    BG_HOVER,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    ACCENT,
    SUCCESS,
    WARNING,
    get_button_style,
    get_title_style,
)
from modules.hr.services import HRService
from modules.hr.views.employee_form import EmployeeFormDialog


class EmployeeModule(QWidget):
    """Çalışan yönetim modülü"""

    page_title = "Çalışanlar"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        header = QHBoxLayout()

        title = QLabel("Çalışan Listesi")
        header.addWidget(title)

        header.addStretch()

        # Yeni çalışan
        new_btn = QPushButton("Yeni Çalışan")
        new_btn.setProperty("class", "primary")
        new_btn.clicked.connect(self._new_employee)
        header.addWidget(new_btn)

        layout.addLayout(header)

        # Filtre satırı
        filter_row = QHBoxLayout()

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara (isim, sicil no, email)...")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self.load_data)
        filter_row.addWidget(self.search_input)

        # Departman filtresi
        self.dept_combo = QComboBox()
        self.dept_combo.setFixedWidth(200)
        self.dept_combo.currentIndexChanged.connect(self.load_data)
        filter_row.addWidget(self.dept_combo)

        filter_row.addStretch()

        # Yenile butonu
        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self.load_data)
        filter_row.addWidget(refresh_btn)

        layout.addLayout(filter_row)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "Sicil No",
                "Ad Soyad",
                "Departman",
                "Pozisyon",
                "İşe Giriş",
                "Email",
                "Durum",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._edit_employee)
        layout.addWidget(self.table)

    def _get_service(self):
        if self.service is None:
            self.service = HRService()
        return self.service

    def _close_service(self):
        if self.service:
            self.service.close()
            self.service = None

    def load_data(self):
        """Verileri yükle"""
        try:
            service = self._get_service()

            # Departman combobox'ı doldur (ilk yüklemede)
            if self.dept_combo.count() == 0:
                self.dept_combo.addItem("Tüm Departmanlar", None)
                for dept in service.get_all_departments():
                    self.dept_combo.addItem(dept.name, dept.id)

            # Filtreler
            search = self.search_input.text().strip() or None
            dept_id = self.dept_combo.currentData()

            employees = service.get_all_employees(
                search=search, department_id=dept_id, limit=500
            )

            self.table.setRowCount(len(employees))
            for row, emp in enumerate(employees):
                self.table.setItem(row, 0, QTableWidgetItem(emp.employee_no))
                self.table.setItem(row, 1, QTableWidgetItem(emp.full_name))
                self.table.setItem(
                    row,
                    2,
                    QTableWidgetItem(emp.department.name if emp.department else "-"),
                )
                self.table.setItem(
                    row, 3, QTableWidgetItem(emp.position.name if emp.position else "-")
                )
                self.table.setItem(
                    row,
                    4,
                    QTableWidgetItem(
                        emp.hire_date.strftime("%d.%m.%Y") if emp.hire_date else "-"
                    ),
                )
                self.table.setItem(row, 5, QTableWidgetItem(emp.email or "-"))

                status = "Aktif" if emp.is_employed else "Ayrıldı"
                status_item = QTableWidgetItem(status)
                if emp.is_employed:
                    status_item.setForeground(Qt.GlobalColor.green)
                else:
                    status_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, 6, status_item)

                # ID'yi sakla
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, emp.id)

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Veriler yüklenirken hata:\n{str(e)}")
        finally:
            self._close_service()

    def _new_employee(self):
        """Yeni çalışan"""
        dialog = EmployeeFormDialog(parent=self)
        if dialog.exec():
            self.load_data()

    def _edit_employee(self):
        """Çalışan düzenle"""
        row = self.table.currentRow()
        if row < 0:
            return
        emp_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = EmployeeFormDialog(employee_id=emp_id, parent=self)
        if dialog.exec():
            self.load_data()
