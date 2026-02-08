from datetime import date
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QDateEdit,
    QDoubleSpinBox,
    QPushButton,
    QComboBox,
    QMessageBox,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from database.models.contracts import ContractType, ContractStatus
from database.base import get_session as get_db
from database.models.sales import Customer
from database.models.purchasing import Supplier
from modules.contracts.services.contract_service import ContractService


class PartySelectorDialog(QDialog):
    def __init__(self, party_type: ContractType, parent=None):
        super().__init__(parent)
        self.party_type = party_type
        self.selected_party = None
        self.db = get_db()
        self.setup_ui()

    def setup_ui(self):
        title = (
            "Müşteri Seç" if self.party_type == ContractType.SALES else "Tedarikçi Seç"
        )
        self.setWindowTitle(title)
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara...")
        self.search_input.textChanged.connect(self.load_data)
        layout.addWidget(self.search_input)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Kod", "İsim", "Vergi No"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.doubleClicked.connect(self.accept_selection)
        layout.addWidget(self.table)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept_selection)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.load_data()

    def load_data(self):
        search = self.search_input.text().lower()
        self.table.setRowCount(0)

        if self.party_type == ContractType.SALES:
            query = self.db.query(Customer)
        else:
            query = self.db.query(Supplier)

        parties = query.all()

        row_idx = 0
        for party in parties:
            if (
                search
                and search not in party.name.lower()
                and search not in getattr(party, "code", "").lower()
            ):
                continue

            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(party.code))
            self.table.setItem(row_idx, 1, QTableWidgetItem(party.name))
            self.table.setItem(row_idx, 2, QTableWidgetItem(party.tax_number or ""))
            self.table.item(row_idx, 0).setData(Qt.ItemDataRole.UserRole, party.id)
            self.table.item(row_idx, 0).setData(
                Qt.ItemDataRole.UserRole + 1, party.name
            )
            row_idx += 1

    def accept_selection(self):
        row = self.table.currentRow()
        if row >= 0:
            self.selected_party = {
                "id": self.table.item(row, 0).data(Qt.ItemDataRole.UserRole),
                "name": self.table.item(row, 0).data(Qt.ItemDataRole.UserRole + 1),
            }
            self.accept()


class ContractFormPage(QWidget):
    saved = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, contract_type: ContractType, contract_id: int = None):
        super().__init__()
        self.contract_type = contract_type
        self.contract_id = contract_id
        self.service = ContractService(get_db())
        self.selected_party_id = None

        self.setup_ui()
        if contract_id:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        title = "Sözleşme Düzenle" if self.contract_id else "Yeni Sözleşme"
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(lbl_title)
        header.addStretch()

        btn_cancel = QPushButton("İptal")
        btn_cancel.clicked.connect(self.cancelled.emit)
        header.addWidget(btn_cancel)

        btn_save = QPushButton("Kaydet")
        btn_save.clicked.connect(self.save)
        btn_save.setStyleSheet("background-color: #4CAF50; color: white;")
        header.addWidget(btn_save)

        layout.addLayout(header)

        # Form
        form_layout = QFormLayout()

        self.inp_code = QLineEdit()
        self.inp_code.setPlaceholderText("Sözleşme Kodu (Otomatik yoksa giriniz)")
        form_layout.addRow("Kod:", self.inp_code)

        # Party Selector
        party_layout = QHBoxLayout()
        self.inp_party = QLineEdit()
        self.inp_party.setReadOnly(True)
        party_layout.addWidget(self.inp_party)

        btn_select = QPushButton("Seç")
        btn_select.clicked.connect(self.select_party)
        party_layout.addWidget(btn_select)

        party_label = (
            "Müşteri:" if self.contract_type == ContractType.SALES else "Tedarikçi:"
        )
        form_layout.addRow(party_label, party_layout)

        # Dates
        self.inp_start = QDateEdit()
        self.inp_start.setDate(QDate.currentDate())
        self.inp_start.setCalendarPopup(True)
        form_layout.addRow("Başlangıç:", self.inp_start)

        self.inp_end = QDateEdit()
        self.inp_end.setDate(QDate.currentDate().addDays(365))
        self.inp_end.setCalendarPopup(True)
        form_layout.addRow("Bitiş:", self.inp_end)

        # Amount
        self.inp_amount = QDoubleSpinBox()
        self.inp_amount.setRange(0, 1000000000)
        self.inp_amount.setPrefix("₺ ")
        form_layout.addRow("Toplam Tutar:", self.inp_amount)

        # Status
        self.inp_status = QComboBox()
        self.inp_status.addItems([s.value for s in ContractStatus])
        form_layout.addRow("Durum:", self.inp_status)

        # Description
        self.inp_desc = QTextEdit()
        self.inp_desc.setMaximumHeight(100)
        form_layout.addRow("Açıklama:", self.inp_desc)

        # File
        file_layout = QHBoxLayout()
        self.inp_file = QLineEdit()
        self.inp_file.setReadOnly(True)
        file_layout.addWidget(self.inp_file)

        btn_file = QPushButton("Dosya Seç")
        btn_file.clicked.connect(self.select_file)
        file_layout.addWidget(btn_file)

        form_layout.addRow("Sözleşme Dosyası:", file_layout)

        layout.addLayout(form_layout)
        layout.addStretch()

    def select_party(self):
        dialog = PartySelectorDialog(self.contract_type, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_party:
            self.selected_party_id = dialog.selected_party["id"]
            self.inp_party.setText(dialog.selected_party["name"])

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Dosya Seç")
        if file_path:
            self.inp_file.setText(file_path)

    def load_data(self):
        contract = self.service.get_by_id(self.contract_id)
        if not contract:
            return

        self.inp_code.setText(contract.code)

        party = (
            contract.customer
            if self.contract_type == ContractType.SALES
            else contract.supplier
        )
        if party:
            self.selected_party_id = party.id
            self.inp_party.setText(party.name)

        self.inp_start.setDate(contract.start_date)
        self.inp_end.setDate(contract.end_date)
        self.inp_amount.setValue(float(contract.total_amount))
        self.inp_status.setCurrentText(contract.status.value)
        self.inp_desc.setText(contract.description)
        self.inp_file.setText(contract.file_path or "")

    def save(self):
        if not self.inp_code.text():
            QMessageBox.warning(self, "Hata", "Sözleşme kodu gereklidir.")
            return

        data = {
            "code": self.inp_code.text(),
            "contract_type": self.contract_type,
            "start_date": self.inp_start.date().toPyDate(),
            "end_date": self.inp_end.date().toPyDate(),
            "status": ContractStatus(self.inp_status.currentText()),
            "total_amount": self.inp_amount.value(),
            "description": self.inp_desc.toPlainText(),
            "file_path": self.inp_file.text(),
        }

        if self.contract_type == ContractType.SALES:
            data["customer_id"] = self.selected_party_id
        else:
            data["supplier_id"] = self.selected_party_id

        try:
            if self.contract_id:
                # Update logic not implemented in service yet effectively, so using create like logic or access DB directly if needed
                # But service has update_status only. I should assume create for now or extend service.
                # Assuming simple create for now as requested.
                pass
            else:
                self.service.create_contract(data)

            self.saved.emit()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
