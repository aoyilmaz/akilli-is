"""
Akıllı İş - İzin Yönetim Modülü
"""

from datetime import date
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QFormLayout,
    QTextEdit,
    QMessageBox,
    QLabel,
    QComboBox,
    QDateEdit,
)
from PyQt6.QtCore import Qt, QDate

from config.styles import (
    BG_PRIMARY,
    BG_SECONDARY,
    BORDER,
    TEXT_PRIMARY,
    ACCENT,
    SUCCESS,
    WARNING,
    get_button_style,
    get_title_style,
)
from modules.hr.services import HRService
from database.models.hr import LeaveType, LeaveStatus

LEAVE_TYPE_LABELS = {
    LeaveType.ANNUAL: "Yıllık İzin",
    LeaveType.SICK: "Hastalık İzni",
    LeaveType.MATERNITY: "Doğum İzni",
    LeaveType.PATERNITY: "Babalık İzni",
    LeaveType.MARRIAGE: "Evlilik İzni",
    LeaveType.BEREAVEMENT: "Vefat İzni",
    LeaveType.UNPAID: "Ücretsiz İzin",
    LeaveType.OTHER: "Diğer",
}

LEAVE_STATUS_LABELS = {
    LeaveStatus.PENDING: "Beklemede",
    LeaveStatus.APPROVED: "Onaylandı",
    LeaveStatus.REJECTED: "Reddedildi",
    LeaveStatus.CANCELLED: "İptal",
}

class LeaveFormDialog(QDialog):
    """İzin talebi dialogu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = HRService()
        self.setup_ui()
        self.load_combos()

    def setup_ui(self):
        self.setWindowTitle("Yeni İzin Talebi")
        self.setMinimumSize(400, 350)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.employee = QComboBox()
        form.addRow("Çalışan:", self.employee)

        self.leave_type = QComboBox()
        for lt, label in LEAVE_TYPE_LABELS.items():
            self.leave_type.addItem(label, lt)
        form.addRow("İzin Türü:", self.leave_type)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        form.addRow("Başlangıç:", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        form.addRow("Bitiş:", self.end_date)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        form.addRow("Açıklama:", self.notes)

        layout.addLayout(form)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Talep Oluştur")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def load_combos(self):
        self.employee.addItem("Seçiniz...", None)
        try:
            for emp in self.service.get_all_employees(limit=500):
                self.employee.addItem(f"{emp.full_name} ({emp.employee_no})", emp.id)
        except Exception:
            pass

    def save(self):
        if not self.employee.currentData():
            QMessageBox.warning(self, "Uyarı", "Çalışan seçiniz.")

        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()

        if end < start:
            QMessageBox.warning(self, "Uyarı", "Bitiş tarihi başlangıçtan önce olamaz.")

        try:
            data = {
                "employee_id": self.employee.currentData(),
                "leave_type": self.leave_type.currentData(),
                "start_date": start,
                "end_date": end,
                "notes": self.notes.toPlainText().strip() or None,
            }

            self.service.create_leave(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)

class LeaveModule(QWidget):
    """İzin yönetim modülü"""

    page_title = "İzinler"

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
        title = QLabel("İzin Talepleri")
        header.addWidget(title)
        header.addStretch()

        new_btn = QPushButton("Yeni İzin Talebi")
        new_btn.setProperty("class", "primary")
        new_btn.clicked.connect(self._new_leave)
        header.addWidget(new_btn)

        layout.addLayout(header)

        # Filtre
        filter_row = QHBoxLayout()

        self.status_combo = QComboBox()
        self.status_combo.setFixedWidth(150)
        self.status_combo.addItem("Tüm Durumlar", None)
        for status, label in LEAVE_STATUS_LABELS.items():
            self.status_combo.addItem(label, status)
        self.status_combo.currentIndexChanged.connect(self.load_data)
        filter_row.addWidget(self.status_combo)

        filter_row.addStretch()

        layout.addLayout(filter_row)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Çalışan", "İzin Türü", "Başlangıç", "Bitiş", "Gün", "Durum", "İşlemler"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
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
            status = self.status_combo.currentData()
            leaves = service.get_leaves(status=status, limit=200)

            self.table.setRowCount(len(leaves))
            for row, leave in enumerate(leaves):
                self.table.setItem(
                    row,
                    0,
                    QTableWidgetItem(
                        leave.employee.full_name if leave.employee else "-"
                    ),
                )
                self.table.setItem(
                    row,
                    1,
                    QTableWidgetItem(LEAVE_TYPE_LABELS.get(leave.leave_type, "-")),
                )
                self.table.setItem(
                    row, 2, QTableWidgetItem(leave.start_date.strftime("%d.%m.%Y"))
                )
                self.table.setItem(
                    row, 3, QTableWidgetItem(leave.end_date.strftime("%d.%m.%Y"))
                )
                self.table.setItem(row, 4, QTableWidgetItem(str(leave.days)))

                status_text = LEAVE_STATUS_LABELS.get(leave.status, "-")
                status_item = QTableWidgetItem(status_text)
                if leave.status == LeaveStatus.APPROVED:
                    status_item.setForeground(Qt.GlobalColor.green)
                elif leave.status == LeaveStatus.REJECTED:
                    status_item.setForeground(Qt.GlobalColor.red)
                elif leave.status == LeaveStatus.PENDING:
                    status_item.setForeground(Qt.GlobalColor.yellow)
                self.table.setItem(row, 5, status_item)

                # İşlem butonu
                if leave.status == LeaveStatus.PENDING:
                    btn_widget = QWidget()
                    btn_layout = QHBoxLayout(btn_widget)
                    btn_layout.setContentsMargins(4, 4, 4, 4)
                    btn_layout.setSpacing(4)

                    approve_btn = QPushButton("Onayla")
                    approve_btn.clicked.connect(
                        lambda checked, lid=leave.id: self._approve_leave(lid)
                    )
                    btn_layout.addWidget(approve_btn)

                    reject_btn = QPushButton("Reddet")
                    reject_btn.clicked.connect(
                        lambda checked, lid=leave.id: self._reject_leave(lid)
                    )
                    btn_layout.addWidget(reject_btn)

                    self.table.setCellWidget(row, 6, btn_widget)
                else:
                    self.table.setItem(row, 6, QTableWidgetItem("-"))

                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, leave.id)

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Hata: {str(e)}")
        finally:
            self._close_service()

    def _new_leave(self):
        dialog = LeaveFormDialog(parent=self)
        if dialog.exec():
            self.load_data()

    def _approve_leave(self, leave_id: int):
        try:
            service = self._get_service()
            service.approve_leave(leave_id, approver_id=1)  # TODO: Gerçek user id
            self.load_data()
            QMessageBox.information(self, "Bilgi", "İzin onaylandı.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            self._close_service()

    def _reject_leave(self, leave_id: int):
        try:
            service = self._get_service()
            service.reject_leave(
                leave_id, approver_id=1, reason="Yönetici tarafından reddedildi"
            )
            self.load_data()
            QMessageBox.information(self, "Bilgi", "İzin reddedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
        finally:
            self._close_service()
