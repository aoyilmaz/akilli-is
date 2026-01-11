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
    QLabel,
    QComboBox,
)
from PyQt6.QtCore import Qt

from config.styles import (
    BG_PRIMARY,
    BG_SECONDARY,
    BORDER,
    TEXT_PRIMARY,
    ACCENT,
    get_button_style,
    get_title_style,
)
from modules.hr.services import HRService


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
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.code = QLineEdit()
        form.addRow("Kod:", self.code)

        self.name = QLineEdit()
        form.addRow("Ad:", self.name)

        self.parent = QComboBox()
        form.addRow("Üst Departman:", self.parent)

        self.description = QTextEdit()
        self.description.setMaximumHeight(80)
        form.addRow("Açıklama:", self.description)

        layout.addLayout(form)

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
        self.parent.addItem("Yok (Ana Departman)", None)
        try:
            for dept in self.service.get_all_departments():
                if dept.id != self.dept_id:
                    self.parent.addItem(dept.name, dept.id)
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
                    idx = self.parent.findData(dept.parent_id)
                    if idx >= 0:
                        self.parent.setCurrentIndex(idx)
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Yükleme hatası: {str(e)}")

    def save(self):
        if not self.code.text().strip():
            QMessageBox.warning(self, "Uyarı", "Kod alanı zorunludur.")
        if not self.name.text().strip():
            QMessageBox.warning(self, "Uyarı", "Ad alanı zorunludur.")

        try:
            data = {
                "code": self.code.text().strip(),
                "name": self.name.text().strip(),
                "description": self.description.toPlainText().strip() or None,
                "parent_id": self.parent.currentData(),
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

        # Başlık
        header = QHBoxLayout()
        title = QLabel("Departman Listesi")
        header.addWidget(title)
        header.addStretch()

        new_btn = QPushButton("Yeni Departman")
        new_btn.setProperty("class", "primary")
        new_btn.clicked.connect(self._new_department)
        header.addWidget(new_btn)

        layout.addLayout(header)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Kod", "Ad", "Üst Departman", "Çalışan Sayısı"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._edit_department)
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
            for row, dept in enumerate(departments):
                self.table.setItem(row, 0, QTableWidgetItem(dept.code))
                self.table.setItem(row, 1, QTableWidgetItem(dept.name))
                self.table.setItem(
                    row, 2, QTableWidgetItem(dept.parent.name if dept.parent else "-")
                )
                count = emp_counts.get(dept.name, 0)
                self.table.setItem(row, 3, QTableWidgetItem(str(count)))
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, dept.id)
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Hata: {str(e)}")
        finally:
            self._close_service()

    def _new_department(self):
        dialog = DepartmentFormDialog(parent=self)
        if dialog.exec():
            self.load_data()

    def _edit_department(self):
        row = self.table.currentRow()
        if row < 0:
            return
        dept_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = DepartmentFormDialog(dept_id=dept_id, parent=self)
        if dialog.exec():
            self.load_data()
