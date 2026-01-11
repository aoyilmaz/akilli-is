"""
Akilli Is - Tahsilat Form Sayfasi
VS Code Dark Theme
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QComboBox, QDateEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDoubleSpinBox, QMessageBox, QScrollArea, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from decimal import Decimal

from config.styles import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HOVER, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, ACCENT, SUCCESS, WARNING, ERROR,
    get_table_style, get_button_style, get_input_style
)

class ReceiptFormPage(QWidget):
    """Tahsilat form sayfasi"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(self, receipt_data: dict = None, customers: list = None,
                 open_invoices: list = None, parent=None):
        super().__init__(parent)
        self.receipt_data = receipt_data or {}
        self.customers = customers or []
        self.open_invoices = open_invoices or []
        self.is_edit = bool(receipt_data and receipt_data.get("id"))
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()

        back_btn = QPushButton("<- Geri")
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)

        title = QLabel("Yeni Tahsilat" if not self.is_edit else "Tahsilat Detayi")
        header_layout.addWidget(title)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Form grubu
        form_group = QGroupBox("Tahsilat Bilgileri")
        form_group.setStyleSheet(self._group_style())
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(16)

        # Ust satir
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        # Tahsilat no
        no_layout = QVBoxLayout()
        no_label = QLabel("Tahsilat No")
        no_layout.addWidget(no_label)
        self.receipt_no = QLineEdit()
        self.receipt_no.setReadOnly(True)
        self.receipt_no.setStyleSheet(self._input_style() + f"background-color: {BG_HOVER};")
        no_layout.addWidget(self.receipt_no)
        row1.addLayout(no_layout)

        # Tarih
        date_layout = QVBoxLayout()
        date_label = QLabel("Tarih *")
        date_layout.addWidget(date_label)
        self.receipt_date = QDateEdit()
        self.receipt_date.setCalendarPopup(True)
        self.receipt_date.setDate(QDate.currentDate())
        self.receipt_date.setStyleSheet(self._input_style())
        date_layout.addWidget(self.receipt_date)
        row1.addLayout(date_layout)

        # Musteri
        customer_layout = QVBoxLayout()
        customer_label = QLabel("Musteri *")
        customer_layout.addWidget(customer_label)
        self.customer_combo = QComboBox()
        self.customer_combo.setStyleSheet(self._combo_style())
        self.customer_combo.currentIndexChanged.connect(self._on_customer_changed)
        customer_layout.addWidget(self.customer_combo)
        row1.addLayout(customer_layout)

        form_layout.addLayout(row1)

        # Ikinci satir
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        # Tutar
        amount_layout = QVBoxLayout()
        amount_label = QLabel("Tutar *")
        amount_layout.addWidget(amount_label)
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 999999999)
        self.amount_input.setDecimals(2)
        self.amount_input.setSuffix(" TL")
        self.amount_input.setStyleSheet(self._input_style())
        amount_layout.addWidget(self.amount_input)
        row2.addLayout(amount_layout)

        # Odeme yontemi
        method_layout = QVBoxLayout()
        method_label = QLabel("Odeme Yontemi *")
        method_layout.addWidget(method_label)
        self.method_combo = QComboBox()
        self.method_combo.addItem("Nakit", "cash")
        self.method_combo.addItem("Havale/EFT", "bank_transfer")
        self.method_combo.addItem("Cek", "check")
        self.method_combo.addItem("Kredi Karti", "credit_card")
        self.method_combo.addItem("Senet", "promissory_note")
        self.method_combo.setStyleSheet(self._combo_style())
        self.method_combo.currentIndexChanged.connect(self._on_method_changed)
        method_layout.addWidget(self.method_combo)
        row2.addLayout(method_layout)

        # Banka adi
        bank_layout = QVBoxLayout()
        bank_label = QLabel("Banka")
        bank_layout.addWidget(bank_label)
        self.bank_input = QLineEdit()
        self.bank_input.setStyleSheet(self._input_style())
        bank_layout.addWidget(self.bank_input)
        row2.addLayout(bank_layout)

        form_layout.addLayout(row2)

        # Ucuncu satir (Cek/Senet bilgileri)
        self.check_row = QHBoxLayout()
        self.check_row.setSpacing(16)

        # Cek/Senet No
        check_no_layout = QVBoxLayout()
        check_no_label = QLabel("Cek/Senet No")
        check_no_layout.addWidget(check_no_label)
        self.check_no_input = QLineEdit()
        self.check_no_input.setStyleSheet(self._input_style())
        check_no_layout.addWidget(self.check_no_input)
        self.check_row.addLayout(check_no_layout)

        # Vade tarihi
        check_date_layout = QVBoxLayout()
        check_date_label = QLabel("Vade Tarihi")
        check_date_layout.addWidget(check_date_label)
        self.check_date = QDateEdit()
        self.check_date.setCalendarPopup(True)
        self.check_date.setDate(QDate.currentDate().addMonths(1))
        self.check_date.setStyleSheet(self._input_style())
        check_date_layout.addWidget(self.check_date)
        self.check_row.addLayout(check_date_layout)

        self.check_row.addStretch()
        form_layout.addLayout(self.check_row)

        # Aciklama
        desc_layout = QVBoxLayout()
        desc_label = QLabel("Aciklama")
        desc_layout.addWidget(desc_label)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setStyleSheet(self._input_style())
        desc_layout.addWidget(self.description_input)
        form_layout.addLayout(desc_layout)

        layout.addWidget(form_group)

        # Fatura dagilimi grubu
        invoice_group = QGroupBox("Fatura Dagilimi")
        invoice_group.setStyleSheet(self._group_style())
        invoice_layout = QVBoxLayout(invoice_group)

        # Fatura tablosu
        self.invoice_table = QTableWidget()
        self.invoice_table.setColumnCount(6)
        self.invoice_table.setHorizontalHeaderLabels([
            "Sec", "Fatura No", "Tarih", "Toplam", "Kalan", "Bu Tahsilat"
        ])
        self.invoice_table.setAlternatingRowColors(True)
        self.invoice_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.invoice_table.verticalHeader().setVisible(False)
        self.invoice_table.setMinimumHeight(200)

        header = self.invoice_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)

        self.invoice_table.setColumnWidth(0, 50)
        self.invoice_table.setColumnWidth(2, 100)
        self.invoice_table.setColumnWidth(3, 120)
        self.invoice_table.setColumnWidth(4, 120)
        self.invoice_table.setColumnWidth(5, 120)

        invoice_layout.addWidget(self.invoice_table)

        # Otomatik dagitim
        auto_layout = QHBoxLayout()
        auto_btn = QPushButton("Otomatik Dagit")
        auto_btn.clicked.connect(self._auto_allocate)
        auto_layout.addWidget(auto_btn)

        self.allocated_label = QLabel("Dagitilan: 0.00 TL")
        auto_layout.addWidget(self.allocated_label)

        auto_layout.addStretch()
        invoice_layout.addLayout(auto_layout)

        layout.addWidget(invoice_group)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Iptal")
        cancel_btn.setFixedSize(120, 44)
        cancel_btn.clicked.connect(self.cancelled.emit)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.setFixedSize(120, 44)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Ilk yukleme
        self._on_method_changed(0)

    def _group_style(self) -> str:
        return f"""
            QGroupBox {{
                background-color: {BG_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 12px;
                padding: 20px;
                margin-top: 12px;
                color: {TEXT_PRIMARY};
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }}
        """

    def _input_style(self) -> str:
        return f"""
            QLineEdit, QDateEdit, QDoubleSpinBox, QTextEdit {{
                background-color: {BG_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                color: {TEXT_PRIMARY};
                font-size: 14px;
            }}
            QLineEdit:focus, QDateEdit:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
                border-color: {ACCENT};
            }}
        """

    def _combo_style(self) -> str:
        return f"""
            QComboBox {{
                background-color: {BG_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                color: {TEXT_PRIMARY};
                font-size: 14px;
            }}
            QComboBox:focus {{ border-color: {ACCENT}; }}
            QComboBox QAbstractItemView {{
                background-color: {BG_SECONDARY};
                border: 1px solid {BORDER};
                selection-background-color: {ACCENT};
                color: {TEXT_PRIMARY};
            }}
        """

    def load_data(self):
        """Verileri yukle"""
        # Musterileri yukle
        self.customer_combo.clear()
        self.customer_combo.addItem("Secin...", None)
        for cust in self.customers:
            self.customer_combo.addItem(
                f"{cust.get('code', '')} - {cust.get('name', '')}",
                cust.get("id")
            )

        # Form verisi varsa doldur
        if self.receipt_data:
            self.receipt_no.setText(self.receipt_data.get("receipt_no", ""))

            if self.receipt_data.get("receipt_date"):
                date_val = self.receipt_data["receipt_date"]
                if hasattr(date_val, "year"):
                    self.receipt_date.setDate(QDate(date_val.year, date_val.month, date_val.day))

            # Musteriyi sec
            customer_id = self.receipt_data.get("customer_id")
            if customer_id:
                for i in range(self.customer_combo.count()):
                    if self.customer_combo.itemData(i) == customer_id:
                        self.customer_combo.setCurrentIndex(i)
                        break

            self.amount_input.setValue(float(self.receipt_data.get("amount", 0) or 0))

            # Odeme yontemi
            method = self.receipt_data.get("payment_method", "cash")
            for i in range(self.method_combo.count()):
                if self.method_combo.itemData(i) == method:
                    self.method_combo.setCurrentIndex(i)
                    break

            self.bank_input.setText(self.receipt_data.get("bank_name", "") or "")
            self.check_no_input.setText(self.receipt_data.get("check_no", "") or "")

            if self.receipt_data.get("check_date"):
                date_val = self.receipt_data["check_date"]
                if hasattr(date_val, "year"):
                    self.check_date.setDate(QDate(date_val.year, date_val.month, date_val.day))

            self.description_input.setPlainText(self.receipt_data.get("description", "") or "")

    def _on_customer_changed(self, index):
        """Musteri degistiginde faturalari yukle"""
        self._load_invoices()

    def _load_invoices(self):
        """Acik faturalari yukle"""
        self.invoice_table.setRowCount(0)

        customer_id = self.customer_combo.currentData()
        if not customer_id:
            return

        # Filtrele: sadece bu musterinin faturalari
        invoices = [inv for inv in self.open_invoices if inv.get("customer_id") == customer_id]

        for row, inv in enumerate(invoices):
            self.invoice_table.insertRow(row)

            # Secim checkbox
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self._update_allocated)
            self.invoice_table.setCellWidget(row, 0, checkbox)

            # Fatura no
            no_item = QTableWidgetItem(inv.get("invoice_no", ""))
            no_item.setData(Qt.ItemDataRole.UserRole, inv.get("id"))
            self.invoice_table.setItem(row, 1, no_item)

            # Tarih
            date_val = inv.get("invoice_date")
            if hasattr(date_val, "strftime"):
                date_str = date_val.strftime("%d.%m.%Y")
            else:
                date_str = str(date_val) if date_val else ""
            self.invoice_table.setItem(row, 2, QTableWidgetItem(date_str))

            # Toplam
            total = inv.get("total_amount") or Decimal(0)
            total_item = QTableWidgetItem(f"{float(total):,.2f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.invoice_table.setItem(row, 3, total_item)

            # Kalan
            paid = inv.get("paid_amount") or Decimal(0)
            remaining = float(total) - float(paid)
            remaining_item = QTableWidgetItem(f"{remaining:,.2f}")
            remaining_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            remaining_item.setData(Qt.ItemDataRole.UserRole, remaining)
            self.invoice_table.setItem(row, 4, remaining_item)

            # Bu tahsilat tutari
            alloc_spin = QDoubleSpinBox()
            alloc_spin.setRange(0, remaining)
            alloc_spin.setDecimals(2)
            alloc_spin.valueChanged.connect(self._update_allocated)
            self.invoice_table.setCellWidget(row, 5, alloc_spin)

            self.invoice_table.setRowHeight(row, 44)

    def _on_method_changed(self, index):
        """Odeme yontemi degistiginde"""
        method = self.method_combo.currentData()
        is_check = method in ("check", "promissory_note")

        # Cek/Senet alanlarini goster/gizle
        for i in range(self.check_row.count()):
            item = self.check_row.itemAt(i)
            if item and item.layout():
                for j in range(item.layout().count()):
                    widget = item.layout().itemAt(j).widget()
                    if widget:
                        widget.setVisible(is_check)

    def _update_allocated(self):
        """Dagitilan tutari guncelle"""
        total_allocated = Decimal(0)

        for row in range(self.invoice_table.rowCount()):
            checkbox = self.invoice_table.cellWidget(row, 0)
            spin = self.invoice_table.cellWidget(row, 5)

            if checkbox and checkbox.isChecked() and spin:
                total_allocated += Decimal(str(spin.value()))

        self.allocated_label.setText(f"Dagitilan: {total_allocated:,.2f} TL")

    def _auto_allocate(self):
        """Otomatik fatura dagilimi"""
        amount = Decimal(str(self.amount_input.value()))
        remaining_amount = amount

        for row in range(self.invoice_table.rowCount()):
            checkbox = self.invoice_table.cellWidget(row, 0)
            spin = self.invoice_table.cellWidget(row, 5)
            remaining_item = self.invoice_table.item(row, 4)

            if checkbox and spin and remaining_item:
                invoice_remaining = Decimal(str(remaining_item.data(Qt.ItemDataRole.UserRole) or 0))

                if remaining_amount > 0 and invoice_remaining > 0:
                    alloc = min(remaining_amount, invoice_remaining)
                    checkbox.setChecked(True)
                    spin.setValue(float(alloc))
                    remaining_amount -= alloc
                else:
                    checkbox.setChecked(False)
                    spin.setValue(0)

        self._update_allocated()

    def _save(self):
        """Kaydet"""
        # Validasyon
        if not self.customer_combo.currentData():
            QMessageBox.warning(self, "Uyari", "Lutfen musteri secin!")
            return

        if self.amount_input.value() <= 0:
            QMessageBox.warning(self, "Uyari", "Lutfen gecerli bir tutar girin!")
            return

        # Fatura dagilimlarini topla
        allocations = []
        for row in range(self.invoice_table.rowCount()):
            checkbox = self.invoice_table.cellWidget(row, 0)
            spin = self.invoice_table.cellWidget(row, 5)
            no_item = self.invoice_table.item(row, 1)

            if checkbox and checkbox.isChecked() and spin and spin.value() > 0:
                allocations.append({
                    "invoice_id": no_item.data(Qt.ItemDataRole.UserRole),
                    "amount": Decimal(str(spin.value()))
                })

        data = {
            "id": self.receipt_data.get("id"),
            "receipt_date": self.receipt_date.date().toPyDate(),
            "customer_id": self.customer_combo.currentData(),
            "amount": Decimal(str(self.amount_input.value())),
            "payment_method": self.method_combo.currentData(),
            "bank_name": self.bank_input.text().strip() or None,
            "check_no": self.check_no_input.text().strip() or None,
            "check_date": self.check_date.date().toPyDate() if self.method_combo.currentData() in ("check", "promissory_note") else None,
            "description": self.description_input.toPlainText().strip() or None,
            "allocations": allocations,
        }

        self.saved.emit(data)

    def set_open_invoices(self, invoices: list):
        """Acik faturalari ayarla"""
        self.open_invoices = invoices
        self._load_invoices()
