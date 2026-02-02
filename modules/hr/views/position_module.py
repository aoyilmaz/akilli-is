"""
Akıllı İş - Pozisyon Yönetim Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidgetItem,
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


class PositionFormDialog(QDialog):
    """Pozisyon ekleme/düzenleme dialogu"""

    def __init__(self, pos_id: int = None, parent=None):
        super().__init__(parent)
        self.pos_id, self.service = pos_id, HRService()
        self.setWindowTitle("Pozisyon Düzenle" if pos_id else "Yeni Pozisyon")
        self.setMinimumSize(400, 350)
        self.setup_ui()
        self.load_combos()
        if pos_id:
            self.load_position()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)
        self.code = QLineEdit()
        form.addRow("Kod:", self.code)
        self.name = QLineEdit()
        form.addRow("Ad:", self.name)
        self.department = QComboBox()
        form.addRow("Departman:", self.department)
        self.min_salary = QLineEdit()
        self.min_salary.setPlaceholderText("0.00")
        form.addRow("Min Maaş:", self.min_salary)
        self.max_salary = QLineEdit()
        self.max_salary.setPlaceholderText("0.00")
        form.addRow("Max Maaş:", self.max_salary)
        self.description = QTextEdit()
        self.description.setMaximumHeight(80)
        form.addRow("Açıklama:", self.description)
        layout.addLayout(form)

        b_layout = QHBoxLayout()
        b_layout.addStretch()
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        b_layout.addWidget(cancel_btn)
        save_btn = QPushButton("Kaydet")
        save_btn.setIcon(qta.icon(ICONS.SAVE, color="#ffffff"))
        save_btn.setProperty("class", "btn-primary")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self.save)
        b_layout.addWidget(save_btn)
        layout.addLayout(b_layout)

    def load_combos(self):
        self.department.addItem("Seçiniz...", None)
        try:
            for d in self.service.get_all_departments():
                self.department.addItem(d.name, d.id)
        except:
            pass

    def load_position(self):
        try:
            pos = self.service.get_position_by_id(self.pos_id)
            if pos:
                self.code.setText(pos.code)
                self.name.setText(pos.name)
                self.description.setPlainText(pos.description or "")
                if pos.min_salary:
                    self.min_salary.setText(str(pos.min_salary))
                if pos.max_salary:
                    self.max_salary.setText(str(pos.max_salary))
                if pos.department_id:
                    idx = self.department.findData(pos.department_id)
                    if idx >= 0:
                        self.department.setCurrentIndex(idx)
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def save(self):
        c, n = self.code.text().strip(), self.name.text().strip()
        if not c or not n:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad zorunludur.")
            return
        try:
            data = {
                "code": c,
                "name": n,
                "description": self.description.toPlainText().strip() or None,
                "department_id": self.department.currentData(),
            }
            if self.min_salary.text().strip():
                try:
                    data["min_salary"] = float(self.min_salary.text())
                except:
                    pass
            if self.max_salary.text().strip():
                try:
                    data["max_salary"] = float(self.max_salary.text())
                except:
                    pass
            if self.pos_id:
                self.service.update_position(self.pos_id, data)
            else:
                self.service.create_position(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, e):
        self.service.close()
        super().closeEvent(e)


class PositionModule(QWidget):
    """Pozisyon yönetim modülü"""

    page_title = "Pozisyonlar"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # === Header ===
        self.header = PageHeader(
            title="Pozisyon Listesi",
            icon=ICONS.POSITION,
            show_search=True,
            show_add=True,
            add_text="Yeni Pozisyon",
            parent=self,
        )
        self.header.add_clicked.connect(self._add_position)
        self.header.refresh_clicked.connect(self.load_data)
        self.header.search_changed.connect(self.load_data)
        layout.addWidget(self.header)

        # === Tablo ===
        columns = [
            ColumnConfig("name", "Pozisyon Adı", width=250, stretch=True),
            ColumnConfig("department", "Departman", width=200),
            ColumnConfig("level", "Kademe/Seviye", width=120),
            ColumnConfig("employee_count", "Çalışan Sayısı", width=120),
            ColumnConfig("status", "Durum", width=100),
        ]

        self.table = EnhancedTableWidget(
            table_id="hr_positions",
            columns=columns,
            parent=self,
        )
        self.table.row_double_clicked.connect(self._edit_position)
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
            emp_counts = {
                p["position"]: p["count"]
                for p in self._get_service().get_employee_count_by_position()
            }

            positions = self._get_service().get_all_positions()
            self.table.setRowCount(len(positions))
            vcols = self.table.get_visible_columns()
            for r, pos in enumerate(positions):
                for c, key in enumerate(vcols):
                    if key == "name":
                        it = QTableWidgetItem(pos.name)
                        it.setData(Qt.ItemDataRole.UserRole, pos.id)
                        self.table.setItem(r, c, it)
                    elif key == "department":
                        d_text = pos.department.name if pos.department else "-"
                        self.table.setItem(r, c, QTableWidgetItem(d_text))
                    elif key == "level":
                        self.table.setItem(
                            r, c, QTableWidgetItem("-")
                        )  # Henüz modelde yok
                    elif key == "employee_count":
                        count = emp_counts.get(pos.name, 0)
                        self.table.setItem(r, c, QTableWidgetItem(str(count)))
                    elif key == "status":
                        status = "Aktif" if pos.is_active else "Pasif"
                        item = QTableWidgetItem(status)
                        item.setForeground(
                            Qt.GlobalColor.green
                            if pos.is_active
                            else Qt.GlobalColor.red
                        )
                        self.table.setItem(r, c, item)
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", str(e))
        finally:
            self._close_service()

    def _add_position(self):
        if PositionFormDialog(parent=self).exec():
            self.load_data()

    def _edit_position(self, pos_id=None):
        if pos_id is None:
            r = self.table.currentRow()
            if r < 0:
                return
            pos_id = self.table.item(r, 0).data(Qt.ItemDataRole.UserRole)
        if PositionFormDialog(pos_id=pos_id, parent=self).exec():
            self.load_data()
