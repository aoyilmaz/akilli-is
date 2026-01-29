"""
Akıllı İş - İzin Yönetim Modülü
"""

from datetime import date
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidgetItem,
    QDialog,
    QFormLayout,
    QTextEdit,
    QMessageBox,
    QLabel,
    QComboBox,
    QDateEdit,
)
from PyQt6.QtCore import Qt, QDate
import qtawesome as qta

from config.icons import ICONS
from modules.hr.services import HRService
from database.models.hr import LeaveType, LeaveStatus
from ui.components.page_header import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


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
        self.setWindowTitle("Yeni İzin Talebi")
        self.setMinimumSize(400, 350)
        self.setup_ui()
        self.load_combos()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)
        self.employee = QComboBox()
        form.addRow("Çalışan:", self.employee)
        self.leave_type = QComboBox()
        for lt, lbl in LEAVE_TYPE_LABELS.items():
            self.leave_type.addItem(lbl, lt)
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

        b_layout = QHBoxLayout()
        b_layout.addStretch()
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        b_layout.addWidget(cancel_btn)
        save_btn = QPushButton("Talep Oluştur")
        save_btn.setIcon(qta.icon(ICONS.ADD, color="#ffffff"))
        save_btn.setProperty("class", "btn-primary")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self.save)
        b_layout.addWidget(save_btn)
        layout.addLayout(b_layout)

    def load_combos(self):
        self.employee.addItem("Seçiniz...", None)
        try:
            for emp in self.service.get_all_employees(limit=500):
                self.employee.addItem(f"{emp.full_name} ({emp.employee_no})", emp.id)
        except:
            pass

    def save(self):
        eid = self.employee.currentData()
        if not eid:
            QMessageBox.warning(self, "Uyarı", "Çalışan seçiniz.")
            return
        start, end = self.start_date.date().toPyDate(), self.end_date.date().toPyDate()
        if end < start:
            QMessageBox.warning(self, "Uyarı", "Bitiş tarihi başlangıçtan önce olamaz.")
            return
        try:
            data = {
                "employee_id": eid,
                "leave_type": self.leave_type.currentData(),
                "start_date": start,
                "end_date": end,
                "notes": self.notes.toPlainText().strip() or None,
            }
            self.service.create_leave(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, e):
        self.service.close()
        super().closeEvent(e)


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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.header = PageHeader(
            title="İzin Talepleri",
            icon=ICONS.CALENDAR,
            show_search=False,
            show_refresh=True,
            show_add=True,
            add_text="Yeni İzin Talebi",
            parent=self,
        )
        self.header.add_clicked.connect(self._new_leave)
        self.header.refresh_clicked.connect(self.load_data)
        h_layout = self.header.header_layout()
        h_layout.addSpacing(16)
        h_layout.addWidget(QLabel("Durum:"))
        self.status_combo = QComboBox()
        self.status_combo.setFixedWidth(150)
        self.status_combo.setFixedHeight(36)
        self.status_combo.addItem("Tüm Durumlar", None)
        for s, lbl in LEAVE_STATUS_LABELS.items():
            self.status_combo.addItem(lbl, s)
        self.status_combo.currentIndexChanged.connect(self.load_data)
        h_layout.addWidget(self.status_combo)
        layout.addWidget(self.header)

        cols = [
            ColumnConfig("emp", "Çalışan", stretch=True),
            ColumnConfig("type", "İzin Türü", width=140),
            ColumnConfig("start", "Başlangıç", width=100),
            ColumnConfig("end", "Bitiş", width=100),
            ColumnConfig("days", "Gün", width=60),
            ColumnConfig("stat", "Durum", width=120),
            ColumnConfig("actions", "İşlemler", width=200),
        ]
        self.table = EnhancedTableWidget(
            table_id="hr_leaves", columns=cols, parent=self
        )
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
            leaves = self._get_service().get_leaves(
                status=self.status_combo.currentData(), limit=200
            )
            self.table.setRowCount(len(leaves))
            vcols = self.table.get_visible_columns()
            for r, leave in enumerate(leaves):
                for c, key in enumerate(vcols):
                    if key == "emp":
                        it = QTableWidgetItem(
                            leave.employee.full_name if leave.employee else "-"
                        )
                        it.setData(Qt.ItemDataRole.UserRole, leave.id)
                        self.table.setItem(r, c, it)
                    elif key == "type":
                        self.table.setItem(
                            r,
                            c,
                            QTableWidgetItem(
                                LEAVE_TYPE_LABELS.get(leave.leave_type, "-")
                            ),
                        )
                    elif key == "start":
                        self.table.setItem(
                            r,
                            c,
                            QTableWidgetItem(leave.start_date.strftime("%d.%m.%Y")),
                        )
                    elif key == "end":
                        self.table.setItem(
                            r, c, QTableWidgetItem(leave.end_date.strftime("%d.%m.%Y"))
                        )
                    elif key == "days":
                        self.table.setItem(r, c, QTableWidgetItem(str(leave.days)))
                    elif key == "stat":
                        it = QTableWidgetItem(
                            LEAVE_STATUS_LABELS.get(leave.status, "-")
                        )
                        if leave.status == LeaveStatus.APPROVED:
                            it.setForeground(Qt.GlobalColor.green)
                        elif leave.status == LeaveStatus.REJECTED:
                            it.setForeground(Qt.GlobalColor.red)
                        elif leave.status == LeaveStatus.PENDING:
                            it.setForeground(Qt.GlobalColor.yellow)
                        self.table.setItem(r, c, it)
                    elif key == "actions":
                        if leave.status == LeaveStatus.PENDING:
                            w = QWidget()
                            l = QHBoxLayout(w)
                            l.setContentsMargins(4, 4, 4, 4)
                            l.setSpacing(4)
                            ok = QPushButton("Onayla")
                            ok.setIcon(qta.icon(ICONS.CHECK, color="#ffffff"))
                            ok.setProperty("class", "btn-success")
                            ok.setFixedHeight(28)
                            ok.clicked.connect(
                                lambda _, lid=leave.id: self._approve_leave(lid)
                            )
                            no = QPushButton("Reddet")
                            no.setIcon(qta.icon(ICONS.CLOSE, color="#ffffff"))
                            no.setProperty("class", "btn-danger")
                            no.setFixedHeight(28)
                            no.clicked.connect(
                                lambda _, lid=leave.id: self._reject_leave(lid)
                            )
                            l.addWidget(ok)
                            l.addWidget(no)
                            self.table.setCellWidget(r, c, w)
                        else:
                            self.table.removeCellWidget(r, c)
                            self.table.setItem(r, c, QTableWidgetItem("-"))
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", str(e))
        finally:
            self._close_service()

    def _new_leave(self):
        if LeaveFormDialog(parent=self).exec():
            self.load_data()

    def _get_default_approver_id(self) -> int:
        """Varsayılan onaylayıcı employee_id'sini getir"""
        # TODO: Mevcut kullanıcının employee_id'sini kullan
        # Şimdilik ilk aktif yönetici/çalışanı bul
        try:
            from database.models.hr import Employee

            emp = (
                self._get_service()
                .session.query(Employee)
                .filter(Employee.is_active == True)
                .order_by(Employee.id)
                .first()
            )
            return emp.id if emp else 471  # Fallback
        except Exception:
            return 471  # Varsayılan: ilk aktif çalışan

    def _approve_leave(self, lid: int):
        try:
            approver_id = self._get_default_approver_id()
            self._get_service().approve_leave(lid, approver_id=approver_id)
            self._close_service()  # Session cache'i temizle
            self.load_data()
            QMessageBox.information(self, "Bilgi", "İzin onaylandı.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
            self._close_service()

    def _reject_leave(self, lid: int):
        try:
            approver_id = self._get_default_approver_id()
            self._get_service().reject_leave(
                lid, approver_id=approver_id, reason="Yönetici tarafından reddedildi"
            )
            self._close_service()  # Session cache'i temizle
            self.load_data()
            QMessageBox.information(self, "Bilgi", "İzin reddedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
            self._close_service()
