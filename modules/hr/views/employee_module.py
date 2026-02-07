from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTableWidgetItem,
    QComboBox,
    QMessageBox,
    QLabel,
    QStackedWidget,
)
from PyQt6.QtCore import Qt
import qtawesome as qta

from config.icons import ICONS
from modules.hr.services import HRService
from modules.hr.views.employee_form import EmployeeFormDialog
from modules.hr.views.id_card_dialog import IdCardDialog


class EmployeeModule(QWidget):
    """Çalışan yönetim modülü"""

    page_title = "Çalışanlar"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.stacked_widget = QStackedWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked_widget)

        # Liste Sayfası
        self.list_widget = QWidget()
        self.setup_list_ui()
        self.stacked_widget.addWidget(self.list_widget)

        # Form Sayfası (Dinamik oluşturulacak)
        self.form_container = QWidget()
        self.form_layout = QVBoxLayout(self.form_container)
        self.form_layout.setContentsMargins(24, 24, 24, 24)
        self.form_layout.setSpacing(16)
        self.stacked_widget.addWidget(self.form_container)

        self.load_data()

    def setup_list_ui(self):
        layout = QVBoxLayout(self.list_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # === Header ===
        from ui.components.page_header import PageHeader

        self.header = PageHeader(
            title="Çalışan Listesi",
            icon=ICONS.EMPLOYEE,
            show_search=True,
            show_add=True,
            add_text="Yeni Çalışan",
            parent=self,
        )
        self.header.add_clicked.connect(self._new_employee)
        self.header.refresh_clicked.connect(self.load_data)
        self.header.search_changed.connect(self.load_data)

        h_layout = self.header.header_layout()

        # Kimlik Kartı butonu
        id_card_btn = QPushButton("Kimlik Kartı")
        id_card_btn.setIcon(qta.icon(ICONS.STOCK_CARD))
        id_card_btn.setFixedSize(140, 36)
        id_card_btn.setProperty("class", "btn-secondary")
        id_card_btn.clicked.connect(self._show_id_card)
        h_layout.addWidget(id_card_btn)

        # Departman filtresi kaldırıldı (Tablodan yapılabilir)

        layout.addWidget(self.header)

        # Tablo
        from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig

        columns = [
            ColumnConfig("employee_no", "Sicil No", width=100),
            ColumnConfig("full_name", "Ad Soyad", width=200, stretch=True),
            ColumnConfig("department", "Departman", width=150),
            ColumnConfig("position", "Pozisyon", width=150),
            ColumnConfig("hire_date", "İşe Giriş", width=120),
            ColumnConfig("email", "Email", width=200),
            ColumnConfig("status", "Durum", width=100),
        ]

        self.table = EnhancedTableWidget(
            table_id="hr_employees",
            columns=columns,
            parent=self,
        )
        self.table.row_double_clicked.connect(self._edit_employee)
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

            # Filtreler
            search = self.header.search_input.text().strip() or None

            employees = service.get_all_employees(search=search, limit=500)

            self.table.setRowCount(len(employees))
            visible_cols = self.table.get_visible_columns()

            for row, emp in enumerate(employees):
                self._populate_row(row, emp, visible_cols)

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Veriler yüklenirken hata:\n{str(e)}")
        finally:
            self._close_service()

    def _populate_row(self, row, emp, visible_cols):
        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "employee_no":
                item = QTableWidgetItem(emp.employee_no)
                item.setData(Qt.ItemDataRole.UserRole, emp.id)
                self.table.setItem(row, col_idx, item)
            elif col_key == "full_name":
                self.table.setItem(row, col_idx, QTableWidgetItem(emp.full_name))
            elif col_key == "department":
                dept_name = emp.department.name if emp.department else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(dept_name))
            elif col_key == "position":
                pos_name = emp.position.name if emp.position else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(pos_name))
            elif col_key == "hire_date":
                h_date = emp.hire_date.strftime("%d.%m.%Y") if emp.hire_date else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(h_date))
            elif col_key == "email":
                self.table.setItem(row, col_idx, QTableWidgetItem(emp.email or "-"))
            elif col_key == "status":
                status = "Aktif" if emp.is_employed else "Ayrıldı"
                status_item = QTableWidgetItem(status)
                if emp.is_employed:
                    status_item.setForeground(Qt.GlobalColor.green)
                else:
                    status_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, col_idx, status_item)

    def _new_employee(self):
        """Yeni çalışan - Sayfa içinde aç"""
        self._show_form()

    def _edit_employee(self):
        """Çalışan düzenle - Sayfa içinde aç"""
        row = self.table.currentRow()
        if row < 0:
            return
        emp_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self._show_form(emp_id)

    def _show_form(self, employee_id=None):
        """Form widget'ını oluştur ve göster"""
        from ui.components.page_header import PageHeader

        # Temizle
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Header (Geri butonu ile)
        title = "Çalışan Düzenle" if employee_id else "Yeni Çalışan"
        form_header = PageHeader(
            title=title,
            icon=ICONS.EMPLOYEE,
            show_back=True,
            show_search=False,
            show_add=False,
            parent=self,
        )
        form_header.back_clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.form_layout.addWidget(form_header)

        # Dialog sınıfını widget olarak kullan
        # Dialog.setup_ui(form_content) yapabiliriz ama Dialog QDialog'dan türer.
        # Bu yüzden dialogu sarmalayan bir yapı kuralım:
        dialog = EmployeeFormDialog(employee_id=employee_id, parent=self)
        dialog.setWindowFlags(Qt.WindowType.Widget)
        # Dialog'daki butonları gizleyip header'a taşıyabiliriz ama şimdilik dialogun layout'unu alalım
        self.form_layout.addWidget(dialog)

        # Dialog'dan gelen finished sinyalini bağla
        dialog.finished.connect(lambda r: self._on_form_finished(r))

        self.stacked_widget.setCurrentIndex(1)

    def _on_form_finished(self, result):
        if result == 1:  # Accepted
            self.load_data()
        self.stacked_widget.setCurrentIndex(0)

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
