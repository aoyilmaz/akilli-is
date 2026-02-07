from datetime import date
from decimal import Decimal

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QDateEdit,
    QComboBox,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QMessageBox,
    QLabel,
    QDialog,
    QSpinBox,
    QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QSize
import qtawesome as qta

from config.icons import ICONS
from config.styles import get_button_style, BTN_HEIGHT_NORMAL
from database.models.accounting import (
    Budget,
    BudgetLine,
    BudgetStatus,
    Account,
    AccountType,
)
from modules.accounting.budget_service import BudgetService


class BudgetForm(QWidget):
    """Bütçe Ekleme/Düzenleme Formu"""

    saved = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, budget_id=None):
        super().__init__()
        self.budget_id = budget_id
        self.service = BudgetService()
        self.setup_ui()

        if self.budget_id:
            self.load_data()
        else:
            self.lines = []  # Temporary storage for new budget lines

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header_layout = QHBoxLayout()

        icon_lbl = QLabel()
        icon_icon = ICONS.EDIT if self.budget_id else ICONS.ADD
        icon_lbl.setPixmap(qta.icon(icon_icon, color="#475569").pixmap(24, 24))
        header_layout.addWidget(icon_lbl)

        title = QLabel("Bütçe Detayı" if self.budget_id else "Yeni Bütçe")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Form
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        form_layout.addRow("Bütçe Adı:", self.name_edit)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2030)
        self.year_spin.setValue(date.today().year)
        form_layout.addRow("Yıl:", self.year_spin)

        date_layout = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate(date.today().year, 1, 1))

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate(date.today().year, 12, 31))

        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("-"))
        date_layout.addWidget(self.end_date)
        form_layout.addRow("Dönem:", date_layout)

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(60)
        form_layout.addRow("Açıklama:", self.desc_edit)

        layout.addLayout(form_layout)

        # Lines Section
        lines_header = QHBoxLayout()
        lines_header.addWidget(QLabel("Bütçe Kalemleri"))
        lines_header.addStretch()

        add_line_btn = QPushButton(" Kalem Ekle")
        add_line_btn.setIcon(qta.icon(ICONS.ADD, color="#475569"))
        add_line_btn.clicked.connect(self.add_line_dialog)
        lines_header.addWidget(add_line_btn)

        layout.addLayout(lines_header)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Hesap Kodu", "Hesap Adı", "Planlanan Tutar", "İşlem"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Footer Actions
        footer = QHBoxLayout()
        footer.addStretch()

        cancel_btn = QPushButton(" İptal")
        cancel_btn.setIcon(qta.icon(ICONS.CANCEL, color="#64748b"))
        cancel_btn.clicked.connect(self.cancelled.emit)
        footer.addWidget(cancel_btn)

        save_btn = QPushButton(" Kaydet")
        save_btn.setIcon(qta.icon(ICONS.SAVE, color="#ffffff"))
        save_btn.setStyleSheet(get_button_style("primary"))
        save_btn.clicked.connect(self.save_budget)
        footer.addWidget(save_btn)

        layout.addLayout(footer)

    def load_data(self):
        budget = self.service.session.query(Budget).get(self.budget_id)
        if not budget:
            return

        self.name_edit.setText(budget.name)
        self.year_spin.setValue(budget.period_year)
        self.start_date.setDate(budget.start_date)
        self.end_date.setDate(budget.end_date)
        self.desc_edit.setText(budget.description)

        self.lines = []
        for line in budget.lines:
            self.lines.append(
                {
                    "account_id": line.account_id,
                    "account_code": line.account.code,
                    "account_name": line.account.name,
                    "planned_amount": line.planned_amount,
                }
            )
        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(len(self.lines))
        for i, line in enumerate(self.lines):
            self.table.setItem(i, 0, QTableWidgetItem(line["account_code"]))
            self.table.setItem(i, 1, QTableWidgetItem(line["account_name"]))

            amount_item = QTableWidgetItem(f"₺{line['planned_amount']:,.2f}")
            amount_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(i, 2, amount_item)

            # Remove Button
            btn = QPushButton()
            btn.setIcon(qta.icon(ICONS.DELETE, color="#ffffff"))
            btn.setFixedSize(30, 30)
            btn.setStyleSheet(
                "background-color: #fca5a5; border: none; border-radius: 4px;"
            )
            btn.clicked.connect(lambda ch, idx=i: self.remove_line(idx))
            self.table.setCellWidget(i, 3, btn)

    def remove_line(self, index):
        if 0 <= index < len(self.lines):
            self.lines.pop(index)
            self.refresh_table()

    def add_line_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Hesap Seç")
        dialog.setFixedSize(400, 200)

        layout = QVBoxLayout(dialog)

        # Account Combo
        combo = QComboBox()
        accounts = self.service.session.query(Account).filter_by(is_detail=True).all()
        # Filter usually for Expenses (7xx, 6xx)
        # But allow all for flexibility

        for acc in accounts:
            combo.addItem(f"{acc.code} - {acc.name}", acc.id)

        layout.addWidget(QLabel("Hesap:"))
        layout.addWidget(combo)

        # Amount
        amount = QDoubleSpinBox()
        amount.setRange(0, 1000000000)
        amount.setPrefix("₺")
        layout.addWidget(QLabel("Tutar:"))
        layout.addWidget(amount)

        btn_box = QHBoxLayout()
        ok_btn = QPushButton("Ekle")
        ok_btn.clicked.connect(dialog.accept)
        btn_box.addWidget(ok_btn)
        layout.addLayout(btn_box)

        if dialog.exec():
            acc_id = combo.currentData()
            amt = Decimal(amount.value())

            # Check duplicate
            for line in self.lines:
                if line["account_id"] == acc_id:
                    line["planned_amount"] = amt
                    self.refresh_table()
                    return

            # New Line
            acc = self.service.session.query(Account).get(acc_id)
            self.lines.append(
                {
                    "account_id": acc.id,
                    "account_code": acc.code,
                    "account_name": acc.name,
                    "planned_amount": amt,
                }
            )
            self.refresh_table()

    def save_budget(self):
        try:
            name = self.name_edit.text()
            if not name:
                QMessageBox.warning(self, "Hata", "Bütçe adı zorunludur.")
                return

            start = self.start_date.date().toPyDate()
            end = self.end_date.date().toPyDate()
            year = self.year_spin.value()
            desc = self.desc_edit.toPlainText()

            if self.budget_id:
                budget = self.service.session.query(Budget).get(self.budget_id)
                budget.name = name
                budget.period_year = year
                budget.start_date = start
                budget.end_date = end
                budget.description = desc
                # Clear old lines? Or update smartly?
                # Simple approach: Delete all and re-create (or update matching)
                # But cascade delete is set on BudgetLine.
                # Let's use service method to update total.
            else:
                budget = self.service.create_budget(name, year, start, end, desc)
                self.budget_id = budget.id

            # Process lines
            # First, get creating budget or existing.
            # If creating, we have budget object.

            # Simple way: just iterate lines and call service.update_budget_line
            # But what about deleted lines?
            # If editing, we need to know which ones to delete.

            current_line_ids = [line["account_id"] for line in self.lines]

            if self.budget_id:
                # Remove lines not in current list
                self.service.session.query(BudgetLine).filter(
                    BudgetLine.budget_id == self.budget_id,
                    BudgetLine.account_id.notin_(current_line_ids),
                ).delete(synchronize_session=False)

            for line in self.lines:
                self.service.update_budget_line(
                    self.budget_id, line["account_id"], line["planned_amount"]
                )

            self.service.session.commit()
            self.saved.emit()

        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)
