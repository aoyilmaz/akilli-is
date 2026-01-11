"""
Akıllı İş - Pozisyon Yönetim Modülü
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


class PositionFormDialog(QDialog):
    """Pozisyon ekleme/düzenleme dialogu"""

    def __init__(self, pos_id: int = None, parent=None):
        super().__init__(parent)
        self.pos_id = pos_id
        self.service = HRService()
        self.setup_ui()
        self.load_combos()
        if pos_id:
            self.load_position()

    def setup_ui(self):
        self.setWindowTitle("Pozisyon Düzenle" if self.pos_id else "Yeni Pozisyon")
        self.setMinimumSize(400, 350)

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
        self.department.addItem("Seçiniz...", None)
        try:
            for dept in self.service.get_all_departments():
                self.department.addItem(dept.name, dept.id)
        except Exception:
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
                "department_id": self.department.currentData(),
            }

            if self.min_salary.text().strip():
                try:
                    data["min_salary"] = float(self.min_salary.text())
                except ValueError:
                    pass

            if self.max_salary.text().strip():
                try:
                    data["max_salary"] = float(self.max_salary.text())
                except ValueError:
                    pass

            if self.pos_id:
                self.service.update_position(self.pos_id, data)
            else:
                self.service.create_position(data)

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)


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

        # Başlık
        header = QHBoxLayout()
        title = QLabel("Pozisyon Listesi")
        header.addWidget(title)
        header.addStretch()

        new_btn = QPushButton("Yeni Pozisyon")
        new_btn.setProperty("class", "primary")
        new_btn.clicked.connect(self._new_position)
        header.addWidget(new_btn)

        layout.addLayout(header)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Kod", "Ad", "Departman", "Min Maaş", "Max Maaş"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._edit_position)
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
            positions = service.get_all_positions()

            self.table.setRowCount(len(positions))
            for row, pos in enumerate(positions):
                self.table.setItem(row, 0, QTableWidgetItem(pos.code))
                self.table.setItem(row, 1, QTableWidgetItem(pos.name))
                self.table.setItem(
                    row,
                    2,
                    QTableWidgetItem(pos.department.name if pos.department else "-"),
                )
                self.table.setItem(
                    row,
                    3,
                    QTableWidgetItem(
                        f"₺{pos.min_salary:,.2f}" if pos.min_salary else "-"
                    ),
                )
                self.table.setItem(
                    row,
                    4,
                    QTableWidgetItem(
                        f"₺{pos.max_salary:,.2f}" if pos.max_salary else "-"
                    ),
                )
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, pos.id)
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Hata: {str(e)}")
        finally:
            self._close_service()

    def _new_position(self):
        dialog = PositionFormDialog(parent=self)
        if dialog.exec():
            self.load_data()

    def _edit_position(self):
        row = self.table.currentRow()
        if row < 0:
            return
        pos_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = PositionFormDialog(pos_id=pos_id, parent=self)
        if dialog.exec():
            self.load_data()
