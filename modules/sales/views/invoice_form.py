"""
Akıllı İş - Fatura Formu
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QMessageBox,
    QGridLayout,
    QScrollArea,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate


class CustomerSelectorDialog(QDialog):
    """Müşteri seçim dialogu"""

    def __init__(self, customers: list, parent=None):
        super().__init__(parent)
        self.customers = customers
        self.selected_customer = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Müşteri Seç")
        self.setMinimumSize(600, 400)
        self.setStyleSheet("QDialog { background-color: #1e293b; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara... (kod, ad)")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                color: #f8fafc;
            }
        """)
        self.search_input.textChanged.connect(self._on_search)
        layout.addWidget(self.search_input)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Kod", "Ad", "Telefon", "E-posta"]
        )
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #f8fafc;
            }
            QTableWidget::item { padding: 8px; }
            QTableWidget::item:selected { background-color: #6366f140; }
            QHeaderView::section {
                background-color: #1e293b;
                color: #94a3b8;
                padding: 10px;
                border: none;
            }
        """)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.doubleClicked.connect(self._on_double_click)

        self._load_customers()
        layout.addWidget(self.table)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #f8fafc;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _load_customers(self):
        self.table.setRowCount(0)
        for row, customer in enumerate(self.customers):
            self.table.insertRow(row)
            code_item = QTableWidgetItem(customer.get("code", ""))
            code_item.setData(Qt.ItemDataRole.UserRole, customer)
            self.table.setItem(row, 0, code_item)
            self.table.setItem(
                row, 1, QTableWidgetItem(customer.get("name", ""))
            )
            self.table.setItem(
                row, 2, QTableWidgetItem(customer.get("phone", "") or "-")
            )
            self.table.setItem(
                row, 3, QTableWidgetItem(customer.get("email", "") or "-")
            )

    def _on_search(self, text: str):
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = any(
                self.table.item(row, col) and
                text in self.table.item(row, col).text().lower()
                for col in range(2)
            )
            self.table.setRowHidden(row, not match)

    def _on_double_click(self, index):
        self._on_accept()

    def _on_accept(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                self.selected_customer = item.data(Qt.ItemDataRole.UserRole)
                self.accept()


class ItemSelectorDialog(QDialog):
    """Stok kartı seçim dialogu"""

    def __init__(self, items: list, parent=None):
        super().__init__(parent)
        self.items = items
        self.selected_item = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Stok Kartı Seç")
        self.setMinimumSize(600, 400)
        self.setStyleSheet("QDialog { background-color: #1e293b; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara... (kod, ad)")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                color: #f8fafc;
            }
        """)
        self.search_input.textChanged.connect(self._on_search)
        layout.addWidget(self.search_input)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Kod", "Ad", "Birim", "Stok"])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #f8fafc;
            }
            QTableWidget::item { padding: 8px; }
            QTableWidget::item:selected { background-color: #6366f140; }
            QHeaderView::section {
                background-color: #1e293b;
                color: #94a3b8;
                padding: 10px;
                border: none;
            }
        """)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.doubleClicked.connect(self._on_double_click)

        self._load_items()
        layout.addWidget(self.table)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #f8fafc;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _load_items(self):
        self.table.setRowCount(0)
        for row, item in enumerate(self.items):
            self.table.insertRow(row)
            code_item = QTableWidgetItem(item.get("code", ""))
            code_item.setData(Qt.ItemDataRole.UserRole, item)
            self.table.setItem(row, 0, code_item)
            self.table.setItem(row, 1, QTableWidgetItem(item.get("name", "")))
            self.table.setItem(
                row, 2, QTableWidgetItem(item.get("unit_name", ""))
            )
            self.table.setItem(
                row, 3, QTableWidgetItem(str(item.get("stock", 0)))
            )

    def _on_search(self, text: str):
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = any(
                self.table.item(row, col) and
                text in self.table.item(row, col).text().lower()
                for col in range(2)
            )
            self.table.setRowHidden(row, not match)

    def _on_double_click(self, index):
        self._on_accept()

    def _on_accept(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                self.selected_item = item.data(Qt.ItemDataRole.UserRole)
                self.accept()


class InvoiceFormPage(QWidget):
    """Fatura formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()
    issue_invoice = pyqtSignal(int)

    def __init__(
        self,
        invoice_data: Optional[dict] = None,
        items: list = None,
        customers: list = None,
        units: list = None,
        currencies: list = None,
        parent=None,
    ):
        super().__init__(parent)
        self.invoice_data = invoice_data
        self.is_edit_mode = invoice_data is not None
        self.items = items or []
        self.customers = customers or []
        self.units = units or []
        self.currencies = currencies or [
            {"id": 1, "code": "TRY", "name": "Türk Lirası"},
            {"id": 2, "code": "USD", "name": "ABD Doları"},
            {"id": 3, "code": "EUR", "name": "Euro"},
        ]
        self.selected_customer = None
        self.setup_ui()
        if self.is_edit_mode:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        back_btn = QPushButton("← Geri")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #334155;
                color: #94a3b8;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #f8fafc;
            }
        """)
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)

        title_text = (
            "Fatura Düzenle" if self.is_edit_mode else "Yeni Fatura"
        )
        title = QLabel(f"📄 {title_text}")
        title.setStyleSheet(
            "font-size: 24px; font-weight: bold; "
            "color: #f8fafc; margin-left: 16px;"
        )
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Fatura Kes butonu (sadece düzenlemede ve taslak ise)
        if self.is_edit_mode and self.invoice_data.get("status") == "draft":
            issue_btn = QPushButton("📤 Fatura Kes")
            issue_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    border: none;
                    color: white;
                    font-weight: 600;
                    padding: 12px 24px;
                    border-radius: 12px;
                }
                QPushButton:hover { background-color: #2563eb; }
            """)
            issue_btn.clicked.connect(self._on_issue)
            header_layout.addWidget(issue_btn)

        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a855f7
                );
                border: none;
                color: white;
                font-weight: 600;
                padding: 12px 24px;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5, stop:1 #9333ea
                );
            }
        """)
        save_btn.clicked.connect(self._on_save)
        header_layout.addWidget(save_btn)

        layout.addLayout(header_layout)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)

        # === GENEL BİLGİLER ===
        general_frame = self._create_section("📝 Genel Bilgiler")
        general_layout = QGridLayout()
        general_layout.setColumnMinimumWidth(0, 140)
        general_layout.setSpacing(12)

        row = 0

        # Fatura No
        general_layout.addWidget(self._create_label("Fatura No"), row, 0)
        self.invoice_no_input = QLineEdit()
        self.invoice_no_input.setPlaceholderText("Otomatik oluşturulacak")
        self.invoice_no_input.setReadOnly(True)
        self._style_input(self.invoice_no_input)
        general_layout.addWidget(self.invoice_no_input, row, 1)
        row += 1

        # Fatura Tarihi
        general_layout.addWidget(
            self._create_label("Fatura Tarihi *"), row, 0
        )
        self.invoice_date_input = QDateEdit()
        self.invoice_date_input.setDate(QDate.currentDate())
        self.invoice_date_input.setCalendarPopup(True)
        self._style_date(self.invoice_date_input)
        general_layout.addWidget(self.invoice_date_input, row, 1)
        row += 1

        # Müşteri
        general_layout.addWidget(self._create_label("Müşteri *"), row, 0)
        customer_layout = QHBoxLayout()
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Müşteri seçin...")
        self.customer_input.setReadOnly(True)
        self._style_input(self.customer_input)
        customer_layout.addWidget(self.customer_input)

        select_customer_btn = QPushButton("🔍")
        select_customer_btn.setFixedSize(42, 42)
        select_customer_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        select_customer_btn.clicked.connect(self._select_customer)
        customer_layout.addWidget(select_customer_btn)
        general_layout.addLayout(customer_layout, row, 1)
        row += 1

        # Vade Tarihi
        general_layout.addWidget(self._create_label("Vade Tarihi"), row, 0)
        self.due_date_input = QDateEdit()
        self.due_date_input.setDate(QDate.currentDate().addDays(30))
        self.due_date_input.setCalendarPopup(True)
        self._style_date(self.due_date_input)
        general_layout.addWidget(self.due_date_input, row, 1)
        row += 1

        # Para Birimi
        general_layout.addWidget(self._create_label("Para Birimi"), row, 0)
        self.currency_input = QComboBox()
        for c in self.currencies:
            self.currency_input.addItem(f"{c['code']} - {c['name']}", c['id'])
        self._style_combo(self.currency_input)
        general_layout.addWidget(self.currency_input, row, 1)
        row += 1

        # Notlar
        general_layout.addWidget(self._create_label("Notlar"), row, 0)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("Ek açıklamalar...")
        self._style_textedit(self.notes_input)
        general_layout.addWidget(self.notes_input, row, 1)

        general_frame.layout().addLayout(general_layout)
        scroll_layout.addWidget(general_frame)

        # === FATURA KALEMLERİ ===
        items_frame = self._create_section("📦 Fatura Kalemleri")
        items_layout = QVBoxLayout()

        add_item_btn = QPushButton("➕ Kalem Ekle")
        add_item_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                color: white;
                font-weight: 600;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        add_item_btn.clicked.connect(self._add_item_row)
        items_layout.addWidget(
            add_item_btn, alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(8)
        self.items_table.setHorizontalHeaderLabels([
            "Stok Kodu", "Stok Adı", "Miktar", "Birim",
            "Birim Fiyat", "İskonto %", "Tutar", "İşlem"
        ])
        self.items_table.setStyleSheet("""
            QTableWidget {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #f8fafc;
            }
            QTableWidget::item { padding: 8px; }
            QHeaderView::section {
                background-color: #1e293b;
                color: #94a3b8;
                padding: 10px;
                border: none;
                font-weight: 600;
            }
        """)
        self.items_table.setMinimumHeight(200)
        self.items_table.verticalHeader().setVisible(False)

        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.items_table.setColumnWidth(0, 100)
        self.items_table.setColumnWidth(2, 80)
        self.items_table.setColumnWidth(3, 80)
        self.items_table.setColumnWidth(4, 100)
        self.items_table.setColumnWidth(5, 80)
        self.items_table.setColumnWidth(6, 100)
        self.items_table.setColumnWidth(7, 60)

        items_layout.addWidget(self.items_table)

        # Toplam
        total_layout = QHBoxLayout()
        total_layout.addStretch()

        total_frame = QFrame()
        total_frame.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        total_inner = QGridLayout(total_frame)

        total_inner.addWidget(QLabel("Ara Toplam:"), 0, 0)
        self.subtotal_label = QLabel("0.00")
        self.subtotal_label.setStyleSheet(
            "color: #f8fafc; font-weight: bold;"
        )
        total_inner.addWidget(self.subtotal_label, 0, 1)

        total_inner.addWidget(QLabel("İskonto:"), 1, 0)
        self.discount_label = QLabel("0.00")
        self.discount_label.setStyleSheet(
            "color: #ef4444; font-weight: bold;"
        )
        total_inner.addWidget(self.discount_label, 1, 1)

        total_inner.addWidget(QLabel("KDV (%18):"), 2, 0)
        self.tax_label = QLabel("0.00")
        self.tax_label.setStyleSheet("color: #f8fafc; font-weight: bold;")
        total_inner.addWidget(self.tax_label, 2, 1)

        total_inner.addWidget(QLabel("Genel Toplam:"), 3, 0)
        self.total_label = QLabel("0.00")
        self.total_label.setStyleSheet(
            "color: #10b981; font-size: 18px; font-weight: bold;"
        )
        total_inner.addWidget(self.total_label, 3, 1)

        total_layout.addWidget(total_frame)
        items_layout.addLayout(total_layout)

        items_frame.layout().addLayout(items_layout)
        scroll_layout.addWidget(items_frame)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def _create_section(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.5);
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; "
            "color: #f8fafc; background: transparent; border: none;"
        )
        layout.addWidget(title_label)

        return frame

    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(
            "color: #e2e8f0; background: transparent; "
            "font-size: 14px; border: none;"
        )
        label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        return label

    def _select_customer(self):
        if not self.customers:
            QMessageBox.warning(
                self, "Uyarı", "Önce müşteri kaydı oluşturmalısınız!"
            )
            return

        dialog = CustomerSelectorDialog(self.customers, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.selected_customer:
                self.selected_customer = dialog.selected_customer
                self.customer_input.setText(
                    f"{dialog.selected_customer['code']} - "
                    f"{dialog.selected_customer['name']}"
                )

    def _add_item_row(self):
        if not self.items:
            QMessageBox.warning(
                self, "Uyarı", "Önce stok kartları yüklenmelidir!"
            )
            return

        dialog = ItemSelectorDialog(self.items, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.selected_item:
                self._insert_item_row(dialog.selected_item)

    def _insert_item_row(
        self,
        item: dict,
        quantity: float = 1,
        unit_price: float = 0,
        discount_rate: float = 0,
    ):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        code_item = QTableWidgetItem(item.get("code", ""))
        code_item.setData(Qt.ItemDataRole.UserRole, item.get("id"))
        code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.items_table.setItem(row, 0, code_item)

        name_item = QTableWidgetItem(item.get("name", ""))
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.items_table.setItem(row, 1, name_item)

        qty_spin = QDoubleSpinBox()
        qty_spin.setRange(0.0001, 999999999)
        qty_spin.setDecimals(4)
        qty_spin.setValue(quantity)
        qty_spin.setStyleSheet(self._spin_style())
        qty_spin.valueChanged.connect(self._update_totals)
        self.items_table.setCellWidget(row, 2, qty_spin)

        unit_combo = QComboBox()
        for u in self.units:
            unit_combo.addItem(u.get("name", ""), u.get("id"))
        unit_id = item.get("unit_id")
        for i in range(unit_combo.count()):
            if unit_combo.itemData(i) == unit_id:
                unit_combo.setCurrentIndex(i)
                break
        unit_combo.setStyleSheet(self._combo_style_small())
        self.items_table.setCellWidget(row, 3, unit_combo)

        price_spin = QDoubleSpinBox()
        price_spin.setRange(0, 999999999)
        price_spin.setDecimals(4)
        price_spin.setValue(unit_price)
        price_spin.setStyleSheet(self._spin_style())
        price_spin.valueChanged.connect(self._update_totals)
        self.items_table.setCellWidget(row, 4, price_spin)

        discount_spin = QDoubleSpinBox()
        discount_spin.setRange(0, 100)
        discount_spin.setDecimals(2)
        discount_spin.setSuffix(" %")
        discount_spin.setValue(discount_rate)
        discount_spin.setStyleSheet(self._spin_style())
        discount_spin.valueChanged.connect(self._update_totals)
        self.items_table.setCellWidget(row, 5, discount_spin)

        amount_item = QTableWidgetItem("0.00")
        amount_item.setFlags(amount_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.items_table.setItem(row, 6, amount_item)

        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(32, 32)
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef444420;
                border: 1px solid #ef444450;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #ef444440; }
        """)
        del_btn.clicked.connect(lambda: self._remove_item_row(row))
        self.items_table.setCellWidget(row, 7, del_btn)

        self.items_table.setRowHeight(row, 50)
        self._update_totals()

    def _remove_item_row(self, row: int):
        self.items_table.removeRow(row)
        self._update_totals()

    def _update_totals(self):
        subtotal = Decimal("0")
        total_discount = Decimal("0")

        for row in range(self.items_table.rowCount()):
            qty_widget = self.items_table.cellWidget(row, 2)
            price_widget = self.items_table.cellWidget(row, 4)
            discount_widget = self.items_table.cellWidget(row, 5)

            if qty_widget and price_widget:
                qty = Decimal(str(qty_widget.value()))
                price = Decimal(str(price_widget.value()))
                discount_rate = Decimal("0")
                if discount_widget:
                    discount_rate = Decimal(str(discount_widget.value()))

                line_total = qty * price
                line_discount = line_total * discount_rate / 100
                line_amount = line_total - line_discount

                subtotal += line_total
                total_discount += line_discount

                amount_item = self.items_table.item(row, 6)
                if amount_item:
                    amount_item.setText(f"{line_amount:,.2f}")

        taxable = subtotal - total_discount
        tax = taxable * Decimal("0.18")
        total = taxable + tax

        self.subtotal_label.setText(f"{subtotal:,.2f}")
        self.discount_label.setText(f"-{total_discount:,.2f}")
        self.tax_label.setText(f"{tax:,.2f}")
        self.total_label.setText(f"{total:,.2f}")

    def load_data(self):
        if not self.invoice_data:
            return

        self.invoice_no_input.setText(self.invoice_data.get("invoice_no", ""))

        inv_date = self.invoice_data.get("invoice_date")
        if inv_date and isinstance(inv_date, date):
            self.invoice_date_input.setDate(
                QDate(inv_date.year, inv_date.month, inv_date.day)
            )

        customer_id = self.invoice_data.get("customer_id")
        customer_name = self.invoice_data.get("customer_name", "")
        customer_code = self.invoice_data.get("customer_code", "")
        if customer_id:
            self.selected_customer = {
                "id": customer_id,
                "name": customer_name,
                "code": customer_code
            }
            self.customer_input.setText(f"{customer_code} - {customer_name}")

        due_date = self.invoice_data.get("due_date")
        if due_date and isinstance(due_date, date):
            self.due_date_input.setDate(
                QDate(due_date.year, due_date.month, due_date.day)
            )

        currency = self.invoice_data.get("currency")
        if currency:
            for i in range(self.currency_input.count()):
                # ComboBox item text "TRY - Türk Lirası" formatında
                if self.currency_input.itemText(i).startswith(currency):
                    self.currency_input.setCurrentIndex(i)
                    break

        self.notes_input.setPlainText(
            self.invoice_data.get("notes", "") or ""
        )

        items_data = self.invoice_data.get("items", [])
        for item_data in items_data:
            item_id = item_data.get("item_id")
            item_info = next(
                (i for i in self.items if i.get("id") == item_id), None
            )
            if item_info:
                self._insert_item_row(
                    item_info,
                    float(item_data.get("quantity", 1)),
                    float(item_data.get("unit_price", 0) or 0),
                    float(item_data.get("discount_rate", 0) or 0),
                )

    def _on_save(self):
        if not self.selected_customer:
            QMessageBox.warning(self, "Uyarı", "Lütfen müşteri seçin!")
            return

        if self.items_table.rowCount() == 0:
            QMessageBox.warning(
                self, "Uyarı", "En az bir kalem eklemelisiniz!"
            )
            return

        items_data = []
        for row in range(self.items_table.rowCount()):
            code_item = self.items_table.item(row, 0)
            item_id = None
            if code_item:
                item_id = code_item.data(Qt.ItemDataRole.UserRole)

            qty_widget = self.items_table.cellWidget(row, 2)
            quantity = qty_widget.value() if qty_widget else 0

            unit_widget = self.items_table.cellWidget(row, 3)
            unit_id = unit_widget.currentData() if unit_widget else None

            price_widget = self.items_table.cellWidget(row, 4)
            unit_price = price_widget.value() if price_widget else 0

            discount_widget = self.items_table.cellWidget(row, 5)
            discount_rate = discount_widget.value() if discount_widget else 0

            if item_id and quantity > 0:
                items_data.append({
                    "item_id": item_id,
                    "quantity": Decimal(str(quantity)),
                    "unit_id": unit_id,
                    "unit_price": Decimal(str(unit_price)),
                    "discount_rate": Decimal(str(discount_rate)),
                })

        if not items_data:
            QMessageBox.warning(self, "Uyarı", "Geçerli kalem bulunamadı!")
            return

        qdate = self.invoice_date_input.date()
        due_qdate = self.due_date_input.date()

        # Currency enum değerini al (TRY, USD, EUR)
        currency_code = self.currency_input.currentText().split(" - ")[0]

        data = {
            "invoice_date": date(qdate.year(), qdate.month(), qdate.day()),
            "customer_id": self.selected_customer.get("id"),
            "due_date": date(
                due_qdate.year(), due_qdate.month(), due_qdate.day()
            ),
            "currency": currency_code,
            "notes": self.notes_input.toPlainText().strip() or None,
            "items": items_data,
        }

        if self.is_edit_mode and self.invoice_data:
            data["id"] = self.invoice_data.get("id")

        self.saved.emit(data)

    def _on_issue(self):
        if self.invoice_data:
            reply = QMessageBox.question(
                self,
                "Fatura Kes",
                "Bu faturayı kesmek istediğinize emin misiniz?\n\n"
                "Kesilen fatura düzenlenemez.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.issue_invoice.emit(self.invoice_data.get("id"))

    def _style_input(self, w):
        w.setMinimumHeight(42)
        w.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 12px;
                color: #f8fafc;
                font-size: 14px;
            }
            QLineEdit:focus { border-color: #6366f1; }
            QLineEdit:read-only {
                background-color: #1e293b;
                color: #94a3b8;
            }
        """)

    def _style_combo(self, c):
        c.setMinimumHeight(42)
        c.setStyleSheet("""
            QComboBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 12px;
                color: #f8fafc;
                font-size: 14px;
            }
            QComboBox:hover { border-color: #475569; }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #94a3b8;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #f8fafc;
                selection-background-color: #334155;
            }
        """)

    def _style_date(self, d):
        d.setMinimumHeight(42)
        d.setStyleSheet("""
            QDateEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 12px;
                color: #f8fafc;
                font-size: 14px;
            }
            QDateEdit:focus { border-color: #6366f1; }
            QDateEdit::drop-down { border: none; width: 30px; }
        """)

    def _style_textedit(self, t):
        t.setStyleSheet("""
            QTextEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 12px;
                color: #f8fafc;
                font-size: 14px;
            }
            QTextEdit:focus { border-color: #6366f1; }
        """)

    def _spin_style(self):
        return """
            QDoubleSpinBox, QSpinBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 4px 8px;
                color: #f8fafc;
                font-size: 12px;
            }
        """

    def _combo_style_small(self):
        return """
            QComboBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 4px 8px;
                color: #f8fafc;
                font-size: 12px;
            }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #f8fafc;
            }
        """
