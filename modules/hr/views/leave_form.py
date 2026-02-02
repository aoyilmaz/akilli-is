"""
Akıllı İş - İzin Talep Formu
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
)
from PyQt6.QtCore import Qt, QDate

from modules.hr.services import HRService
from database.models.hr import LeaveType, LeaveStatus


class LeaveFormDialog(QDialog):
    """İzin talep formu dialogu"""

    def __init__(self, employee_id: int = None, parent=None):
        super().__init__(parent)
        self.employee_id = employee_id
        self.service = HRService()
        self.setup_ui()
        self.load_combos()

    def setup_ui(self):
        self.setWindowTitle("Yeni İzin Talebi")
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(12)

        self.employee_combo = QComboBox()
        form.addRow("Çalışan:", self.employee_combo)

        self.type_combo = QComboBox()
        self.type_combo.addItem("Yıllık İzin", LeaveType.ANNUAL)
        self.type_combo.addItem("Hastalık İzni", LeaveType.SICK)
        self.type_combo.addItem("Doğum İzni", LeaveType.MATERNITY)
        self.type_combo.addItem("Babalık İzni", LeaveType.PATERNITY)
        self.type_combo.addItem("Evlilik İzni", LeaveType.MARRIAGE)
        self.type_combo.addItem("Vefat İzni", LeaveType.BEREAVEMENT)
        self.type_combo.addItem("Ücretsiz İzin", LeaveType.UNPAID)
        self.type_combo.addItem("Diğer", LeaveType.OTHER)
        form.addRow("İzin Türü:", self.type_combo)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        form.addRow("Başlangıç Tarihi:", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        form.addRow("Bitiş Tarihi:", self.end_date)

        self.reason = QTextEdit()
        self.reason.setMaximumHeight(100)
        self.reason.setPlaceholderText("İzin talep nedeni...")
        form.addRow("Neden:", self.reason)

        layout.addLayout(form)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Talebi Gönder")
        save_btn.setProperty("class", "btn-primary")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def load_combos(self):
        """Çalışanları yükle"""
        try:
            self.employee_combo.addItem("Seçiniz...", None)
            employees = self.service.get_all_employees(limit=1000)
            for emp in employees:
                self.employee_combo.addItem(
                    f"{emp.full_name} ({emp.employee_no})", emp.id
                )

            if self.employee_id:
                idx = self.employee_combo.findData(self.employee_id)
                if idx >= 0:
                    self.employee_combo.setCurrentIndex(idx)
        except Exception as e:
            print(f"İzin formu yükleme hatası: {e}")

    def save(self):
        """Kaydet"""
        emp_id = self.employee_combo.currentData()
        if not emp_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir çalışan seçin.")
            return

        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()

        if start > end:
            QMessageBox.warning(
                self, "Uyarı", "Başlangıç tarihi bitiş tarihinden büyük olamaz."
            )
            return

        try:
            data = {
                "employee_id": emp_id,
                "leave_type": self.type_combo.currentData(),
                "start_date": start,
                "end_date": end,
                "reason": self.reason.toPlainText().strip(),
                "status": LeaveStatus.PENDING,
            }
            self.service.create_leave(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İzin talebi oluşturulamadı:\n{str(e)}")

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)
