"""
Akilli Is - Odeme Form Sayfasi
VS Code Dark Theme
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QComboBox, QDateEdit, QTextEdit,
    QDoubleSpinBox, QMessageBox, QScrollArea, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from decimal import Decimal

from config.styles import (
    BG_PRIMARY, BG_SECONDARY, BG_HOVER, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, ACCENT, ERROR,
    get_button_style
)


class PaymentFormPage(QWidget):
    """Odeme form sayfasi"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

    supplier_balance_requested = pyqtSignal(int)  # supplier_id

    def __init__(self, payment_data: dict = None,
                 suppliers: list = None, parent=None):
        super().__init__(parent)
        self.payment_data = payment_data or {}
        self.suppliers = suppliers or []
        self.is_edit = bool(payment_data and payment_data.get("id"))
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()

        back_btn = QPushButton("<- Geri")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {ACCENT};
                font-size: 14px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ color: #1177bb; }}
        """)
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)

        title_text = "Yeni Odeme" if not self.is_edit else "Odeme Detayi"
        title = QLabel(title_text)
        title.setStyleSheet(
            f"font-size: 24px; font-weight: bold; color: {TEXT_PRIMARY};"
        )
        header_layout.addWidget(title)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Form grubu
        form_group = QGroupBox("Odeme Bilgileri")
        form_group.setStyleSheet(self._group_style())
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(16)

        # Ust satir
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        # Odeme no
        no_layout = QVBoxLayout()
        no_label = QLabel("Odeme No")
        no_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        no_layout.addWidget(no_label)
        self.payment_no = QLineEdit()
        self.payment_no.setReadOnly(True)
        self.payment_no.setStyleSheet(
            self._input_style() + f"background-color: {BG_HOVER};"
        )
        no_layout.addWidget(self.payment_no)
        row1.addLayout(no_layout)

        # Tarih
        date_layout = QVBoxLayout()
        date_label = QLabel("Tarih *")
        date_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        date_layout.addWidget(date_label)
        self.payment_date = QDateEdit()
        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDate(QDate.currentDate())
        self.payment_date.setStyleSheet(self._input_style())
        date_layout.addWidget(self.payment_date)
        row1.addLayout(date_layout)

        # Tedarikci
        supplier_layout = QVBoxLayout()
        supplier_label = QLabel("Tedarikci *")
        supplier_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        supplier_layout.addWidget(supplier_label)
        self.supplier_combo = QComboBox()
        self.supplier_combo.setStyleSheet(self._combo_style())
        self.supplier_combo.currentIndexChanged.connect(
            self._on_supplier_changed
        )
        supplier_layout.addWidget(self.supplier_combo)
        row1.addLayout(supplier_layout)

        form_layout.addLayout(row1)

        # Tedarikci borc bilgisi karti
        self.balance_card = QFrame()
        self.balance_card.setStyleSheet(f"""
            QFrame {{
                background-color: {ERROR}20;
                border: 1px solid {ERROR}50;
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        balance_card_layout = QHBoxLayout(self.balance_card)
        balance_card_layout.setContentsMargins(16, 12, 16, 12)

        balance_icon = QLabel("Tedarikci Borcu:")
        balance_icon.setStyleSheet(
            f"color: {ERROR}; font-size: 14px; "
            f"font-weight: bold; background: transparent;"
        )
        balance_card_layout.addWidget(balance_icon)

        self.balance_label = QLabel("0.00 TL")
        self.balance_label.setStyleSheet(
            f"color: {ERROR}; font-size: 18px; "
            f"font-weight: bold; background: transparent;"
        )
        balance_card_layout.addWidget(self.balance_label)

        balance_card_layout.addStretch()
        self.balance_card.setVisible(False)  # Baslangicta gizle
        form_layout.addWidget(self.balance_card)

        # Ikinci satir
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        # Tutar
        amount_layout = QVBoxLayout()
        amount_label = QLabel("Tutar *")
        amount_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
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
        method_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
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
        bank_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
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
        check_no_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        check_no_layout.addWidget(check_no_label)
        self.check_no_input = QLineEdit()
        self.check_no_input.setStyleSheet(self._input_style())
        check_no_layout.addWidget(self.check_no_input)
        self.check_row.addLayout(check_no_layout)

        # Vade tarihi
        check_date_layout = QVBoxLayout()
        check_date_label = QLabel("Vade Tarihi")
        check_date_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
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
        desc_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        desc_layout.addWidget(desc_label)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setStyleSheet(self._input_style())
        desc_layout.addWidget(self.description_input)
        form_layout.addLayout(desc_layout)

        layout.addWidget(form_group)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Iptal")
        cancel_btn.setFixedSize(120, 44)
        cancel_btn.setStyleSheet(get_button_style("secondary"))
        cancel_btn.clicked.connect(self.cancelled.emit)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.setFixedSize(120, 44)
        save_btn.setStyleSheet(get_button_style("danger"))
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
            QLineEdit:focus, QDateEdit:focus,
            QDoubleSpinBox:focus, QTextEdit:focus {{
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
        # Tedarikcileri yukle
        self.supplier_combo.clear()
        self.supplier_combo.addItem("Secin...", None)
        for sup in self.suppliers:
            self.supplier_combo.addItem(
                f"{sup.get('code', '')} - {sup.get('name', '')}",
                sup.get("id")
            )

        # Form verisi varsa doldur
        if self.payment_data:
            self.payment_no.setText(self.payment_data.get("payment_no", ""))

            if self.payment_data.get("payment_date"):
                date_val = self.payment_data["payment_date"]
                if hasattr(date_val, "year"):
                    self.payment_date.setDate(
                        QDate(date_val.year, date_val.month, date_val.day)
                    )

            # Tedarikcyi sec
            supplier_id = self.payment_data.get("supplier_id")
            if supplier_id:
                for i in range(self.supplier_combo.count()):
                    if self.supplier_combo.itemData(i) == supplier_id:
                        self.supplier_combo.setCurrentIndex(i)
                        break

            amount_val = float(self.payment_data.get("amount", 0) or 0)
            self.amount_input.setValue(amount_val)

            # Odeme yontemi
            method = self.payment_data.get("payment_method", "cash")
            for i in range(self.method_combo.count()):
                if self.method_combo.itemData(i) == method:
                    self.method_combo.setCurrentIndex(i)
                    break

            self.bank_input.setText(
                self.payment_data.get("bank_name", "") or ""
            )
            self.check_no_input.setText(
                self.payment_data.get("check_no", "") or ""
            )

            if self.payment_data.get("check_date"):
                date_val = self.payment_data["check_date"]
                if hasattr(date_val, "year"):
                    self.check_date.setDate(
                        QDate(date_val.year, date_val.month, date_val.day)
                    )

            self.description_input.setPlainText(
                self.payment_data.get("description", "") or ""
            )

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

    def _on_supplier_changed(self, index):
        """Tedarikci degistiginde"""
        supplier_id = self.supplier_combo.currentData()
        if supplier_id:
            self.supplier_balance_requested.emit(supplier_id)
            self.balance_card.setVisible(True)
        else:
            self.balance_card.setVisible(False)
            self.balance_label.setText("0.00 TL")

    def set_supplier_balance(self, balance: Decimal):
        """Tedarikci borcunu goster"""
        self.balance_label.setText(f"{balance:,.2f} TL")
        self.balance_card.setVisible(True)

    def _save(self):
        """Kaydet"""
        # Validasyon
        if not self.supplier_combo.currentData():
            QMessageBox.warning(self, "Uyari", "Lutfen tedarikci secin!")
            return

        if self.amount_input.value() <= 0:
            QMessageBox.warning(self, "Uyari", "Lutfen gecerli bir tutar girin!")
            return

        method = self.method_combo.currentData()
        check_date = None
        if method in ("check", "promissory_note"):
            check_date = self.check_date.date().toPyDate()

        data = {
            "id": self.payment_data.get("id"),
            "payment_date": self.payment_date.date().toPyDate(),
            "supplier_id": self.supplier_combo.currentData(),
            "amount": Decimal(str(self.amount_input.value())),
            "payment_method": method,
            "bank_name": self.bank_input.text().strip() or None,
            "check_no": self.check_no_input.text().strip() or None,
            "check_date": check_date,
            "description": self.description_input.toPlainText().strip() or None,
        }

        self.saved.emit(data)
