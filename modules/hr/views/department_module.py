"""
Akıllı İş - Departman Yönetim Modülü
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
    QDialog,
    QFormLayout,
    QTextEdit,
    QMessageBox,
    QComboBox,
)
from PyQt6.QtCore import Qt
import qtawesome as qta

from config.icons import ICONS
from modules.hr.services import HRService
from ui.components.page_header import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


class DepartmentFormDialog(QDialog):
    """Departman ekleme/düzenleme dialogu"""

    def __init__(self, dept_id: int = None, parent=None):
        super().__init__(parent)
        self.dept_id = dept_id
        self.service = HRService()
        self.setup_ui()
        self.load_combos()
        if dept_id:
            self.load_department()

    def setup_ui(self):
        self.setWindowTitle("Departman Düzenle" if self.dept_id else "Yeni Departman")
        self.setMinimumSize(400, 350)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.code = QLineEdit()
        form.addRow("Kod:", self.code)

        self.name = QLineEdit()
        form.addRow("Ad:", self.name)

        self.parent_combo = QComboBox()
        form.addRow("Üst Departman:", self.parent_combo)

        self.description = QTextEdit()
        self.description.setMaximumHeight(100)
        form.addRow("Açıklama:", self.description)

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

    def load_combos(self):
        self.parent_combo.addItem("Yok (Ana Departman)", None)
        try:
            for dept in self.service.get_all_departments():
                if dept.id != self.dept_id:
                    self.parent_combo.addItem(dept.name, dept.id)
        except Exception:
            pass

    def load_department(self):
        try:
            dept = self.service.get_department_by_id(self.dept_id)
            if dept:
                self.code.setText(dept.code)
                self.name.setText(dept.name)
                self.description.setPlainText(dept.description or "")
                if dept.parent_id:
                    idx = self.parent_combo.findData(dept.parent_id)
                    if idx >= 0:
                        self.parent_combo.setCurrentIndex(idx)
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Yükleme hatası: {str(e)}")

    def save(self):
        if not self.code.text().strip() or not self.name.text().strip():
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad alanları zorunludur.")
            return

        try:
            data = {
                "code": self.code.text().strip(),
                "name": self.name.text().strip(),
                "description": self.description.toPlainText().strip() or None,
                "parent_id": self.parent_combo.currentData(),
            }
            if self.dept_id:
                self.service.update_department(self.dept_id, data)
            else:
                self.service.create_department(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)


class DepartmentModule(QWidget):
    """Departman yönetim modülü"""

    page_title = "Departmanlar"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Departman Listesi",
            icon=ICONS.BUILDING,
            show_search=False,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Departman",
            parent=self,
        )
        self.header.add_clicked.connect(self._new_department)
        self.header.refresh_clicked.connect(self.load_data)
        layout.addWidget(self.header)

        # Tablo
        columns = [
            ColumnConfig("code", "Kod", width=120),
            ColumnConfig("name", "Ad", width=250, stretch=True),
            ColumnConfig("parent", "Üst Departman", width=200),
            ColumnConfig("emp_count", "Çalışan Sayısı", width=120),
        ]
        self.table = EnhancedTableWidget(
            table_id="hr_departments", columns=columns, parent=self
        )
        self.table.row_double_clicked.connect(self._edit_department)
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
        try:
            service = self._get_service()
            departments = service.get_all_departments()
            emp_counts = {
                d["department"]: d["count"]
                for d in service.get_employee_count_by_department()
            }

            self.table.setRowCount(len(departments))
            visible_cols = self.table.get_visible_columns()
            for row, dept in enumerate(departments):
                self._populate_row(row, dept, emp_counts, visible_cols)
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Hata: {str(e)}")
        finally:
            self._close_service()

    def _populate_row(self, row, dept, emp_counts, visible_cols):
        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "code":
                item = QTableWidgetItem(dept.code)
                item.setData(Qt.ItemDataRole.UserRole, dept.id)
                self.table.setItem(row, col_idx, item)
            elif col_key == "name":
                self.table.setItem(row, col_idx, QTableWidgetItem(dept.name))
            elif col_key == "parent":
                p_text = dept.parent.name if dept.parent else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(p_text))
            elif col_key == "emp_count":
                count = emp_counts.get(dept.name, 0)
                self.table.setItem(row, col_idx, QTableWidgetItem(str(count)))

    def _new_department(self):
        dialog = DepartmentFormDialog(parent=self)
        if dialog.exec():
            self.load_data()

    def _edit_department(self, dept_id):
        dialog = DepartmentFormDialog(dept_id=dept_id, parent=self)
        if dialog.exec():
            self.load_data()
