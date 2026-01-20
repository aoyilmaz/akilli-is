"""
Akıllı İş - Çalışan Yönetim Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
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
    BTN_HEIGHT_NORMAL,
    ICONS,
)
from modules.hr.services import HRService
from modules.hr.views.employee_form import EmployeeFormDialog
from modules.hr.views.id_card_dialog import IdCardDialog


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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === Header - PageHeader kullanarak ===
        from ui.components.page_header import PageHeader

        self.header = PageHeader(
            title="Çalışan Listesi",
            icon="👥",
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Çalışan",
            parent=self,
        )
        self.header.add_clicked.connect(self._new_employee)
        self.header.refresh_clicked.connect(self.load_data)
        self.header.search_changed.connect(self.load_data)

        # Arama kutusuna erişim gerektiği için (search_input aslında headerdaki search bar)
        # load_data metodu `self.search_input.text()` kullanıyor.
        # Bu yüzden property olarak header search'e yönlendirebiliriz veya load_data'yı güncelleyebiliriz.
        # En temizi load_data'da self.header.search_bar.text() kullanmak.

        h_layout = self.header.header_layout()

        # Kimlik Kartı butonu
        id_card_btn = QPushButton("🪪 Kimlik Kartı")
        id_card_btn.setFixedSize(140, 36)
        id_card_btn.setProperty("class", "btn-secondary")
        id_card_btn.clicked.connect(self._show_id_card)
        h_layout.addWidget(id_card_btn)

        # Departman filtresi
        h_layout.addSpacing(16)
        h_layout.addWidget(QLabel("Departman:"))
        self.dept_combo = QComboBox()
        self.dept_combo.setFixedWidth(200)
        self.dept_combo.setFixedHeight(36)
        self.dept_combo.currentIndexChanged.connect(self.load_data)
        h_layout.addWidget(self.dept_combo)

        layout.addWidget(self.header)

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
            search = self.header.search_input.text().strip() or None
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

    def _show_id_card(self):
        """Seçili çalışanın kimlik kartını göster"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir çalışan seçin.")
            return

        emp_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        try:
            service = self._get_service()
            employee = service.get_employee_by_id(emp_id)

            if employee:
                dialog = IdCardDialog(employee, parent=self)
                dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Kimlik kartı açılamadı:\n{str(e)}")
        finally:
            self._close_service()
