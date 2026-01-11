"""
Akıllı İş - Satış Sipariş Formu
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara... (kod, ad)")
        self.search_input.textChanged.connect(self._on_search)
        layout.addWidget(self.search_input)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Kod", "Ad", "Birim", "Stok"])
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

        # Butonlar
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
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
            match = False
            for col in range(2):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara... (kod, ad)")
        self.search_input.textChanged.connect(self._on_search)
        layout.addWidget(self.search_input)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Kod", "Ad", "Telefon", "E-posta"]
        )
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

        # Butonlar
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
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
            match = False
            for col in range(2):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
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

class SalesOrderFormPage(QWidget):
    """Satış sipariş formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()
    confirm_order = pyqtSignal(int)

    def __init__(
        self,
        order_data: Optional[dict] = None,
        items: list = None,
        customers: list = None,
        units: list = None,
        currencies: list = None,
        parent=None,
    ):
        super().__init__(parent)
        self.order_data = order_data
        self.is_edit_mode = order_data is not None
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
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)

        title_text = (
            "Sipariş Düzenle" if self.is_edit_mode else "Yeni Satış Siparişi"
        )
        title = QLabel(f"🛒 {title_text}")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Onayla butonu (sadece düzenlemede ve taslak ise)
        if self.is_edit_mode and self.order_data.get("status") == "draft":
            confirm_btn = QPushButton("✅ Siparişi Onayla")
            confirm_btn.clicked.connect(self._on_confirm_order)
            header_layout.addWidget(confirm_btn)

        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(self._on_save)
        header_layout.addWidget(save_btn)

        layout.addLayout(header_layout)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)

        # === GENEL BİLGİLER ===
        general_frame = self._create_section("📝 Genel Bilgiler")
        general_layout = QGridLayout()
        general_layout.setColumnMinimumWidth(0, 140)
        general_layout.setSpacing(12)

        row = 0

        # Sipariş No
        general_layout.addWidget(self._create_label("Sipariş No"), row, 0)
        self.order_no_input = QLineEdit()
        self.order_no_input.setPlaceholderText("Otomatik oluşturulacak")
        self.order_no_input.setReadOnly(True)
        general_layout.addWidget(self.order_no_input, row, 1)
        row += 1

        # Sipariş Tarihi
        general_layout.addWidget(self._create_label("Sipariş Tarihi *"), row, 0)
        self.order_date_input = QDateEdit()
        self.order_date_input.setDate(QDate.currentDate())
        self.order_date_input.setCalendarPopup(True)
        general_layout.addWidget(self.order_date_input, row, 1)
        row += 1

        # Müşteri
        general_layout.addWidget(self._create_label("Müşteri *"), row, 0)
        customer_layout = QHBoxLayout()
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Müşteri seçin...")
        self.customer_input.setReadOnly(True)
        customer_layout.addWidget(self.customer_input)

        select_customer_btn = QPushButton("🔍")
        select_customer_btn.setFixedSize(42, 42)
        select_customer_btn.clicked.connect(self._select_customer)
        customer_layout.addWidget(select_customer_btn)
        general_layout.addLayout(customer_layout, row, 1)
        row += 1

        # Teslim Tarihi
        general_layout.addWidget(self._create_label("Teslim Tarihi"), row, 0)
        self.delivery_date_input = QDateEdit()
        self.delivery_date_input.setDate(QDate.currentDate().addDays(7))
        self.delivery_date_input.setCalendarPopup(True)
        general_layout.addWidget(self.delivery_date_input, row, 1)
        row += 1

        # Para Birimi
        general_layout.addWidget(self._create_label("Para Birimi"), row, 0)
        self.currency_input = QComboBox()
        for c in self.currencies:
            self.currency_input.addItem(f"{c['code']} - {c['name']}", c['id'])
        general_layout.addWidget(self.currency_input, row, 1)
        row += 1

        # Notlar
        general_layout.addWidget(self._create_label("Notlar"), row, 0)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Ek açıklamalar...")
        general_layout.addWidget(self.notes_input, row, 1)

        general_frame.layout().addLayout(general_layout)
        scroll_layout.addWidget(general_frame)

        # === SİPARİŞ KALEMLERİ ===
        items_frame = self._create_section("📦 Sipariş Kalemleri")
        items_layout = QVBoxLayout()

        # Kalem ekleme butonu
        add_item_btn = QPushButton("➕ Kalem Ekle")
        add_item_btn.clicked.connect(self._add_item_row)
        items_layout.addWidget(
            add_item_btn, alignment=Qt.AlignmentFlag.AlignLeft
        )

        # Kalemler tablosu
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(8)
        self.items_table.setHorizontalHeaderLabels([
            "Stok Kodu", "Stok Adı", "Miktar", "Birim",
            "Birim Fiyat", "İskonto %", "Tutar", "İşlem"
        ])
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
        total_inner = QGridLayout(total_frame)

        total_inner.addWidget(QLabel("Ara Toplam:"), 0, 0)
        self.subtotal_label = QLabel("0.00")
        total_inner.addWidget(self.subtotal_label, 0, 1)

        total_inner.addWidget(QLabel("İskonto:"), 1, 0)
        self.discount_label = QLabel("0.00")
        total_inner.addWidget(self.discount_label, 1, 1)

        total_inner.addWidget(QLabel("KDV (%18):"), 2, 0)
        self.tax_label = QLabel("0.00")
        total_inner.addWidget(self.tax_label, 2, 1)

        total_inner.addWidget(QLabel("Genel Toplam:"), 3, 0)
        self.total_label = QLabel("0.00")
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
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title_label = QLabel(title)
        layout.addWidget(title_label)

        return frame

    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        return label

    def _select_customer(self):
        """Müşteri seç"""
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
        """Yeni kalem satırı ekle"""
        if not self.items:
            QMessageBox.warning(
                self, "Uyarı", "Önce stok kartları yüklenmelidir!"
            )
            return

        dialog = ItemSelectorDialog(self.items, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.selected_item:
                item = dialog.selected_item
                self._insert_item_row(item)

    def _insert_item_row(
        self,
        item: dict,
        quantity: float = 1,
        unit_price: float = 0,
        discount_rate: float = 0,
    ):
        """Tabloya kalem ekle"""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        # Stok Kodu
        code_item = QTableWidgetItem(item.get("code", ""))
        code_item.setData(Qt.ItemDataRole.UserRole, item.get("id"))
        code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.items_table.setItem(row, 0, code_item)

        # Stok Adı
        name_item = QTableWidgetItem(item.get("name", ""))
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.items_table.setItem(row, 1, name_item)

        # Miktar
        qty_spin = QDoubleSpinBox()
        qty_spin.setRange(0.0001, 999999999)
        qty_spin.setDecimals(4)
        qty_spin.setValue(quantity)
        qty_spin.setStyleSheet(self._spin_style())
        qty_spin.valueChanged.connect(self._update_totals)
        self.items_table.setCellWidget(row, 2, qty_spin)

        # Birim
        unit_combo = QComboBox()
        for u in self.units:
            unit_combo.addItem(u.get("name", ""), u.get("id"))
        # Varsayılan birim
        unit_id = item.get("unit_id")
        for i in range(unit_combo.count()):
            if unit_combo.itemData(i) == unit_id:
                unit_combo.setCurrentIndex(i)
                break
        unit_combo.setStyleSheet(self._combo_style_small())
        self.items_table.setCellWidget(row, 3, unit_combo)

        # Birim Fiyat
        price_spin = QDoubleSpinBox()
        price_spin.setRange(0, 999999999)
        price_spin.setDecimals(4)
        price_spin.setValue(unit_price)
        price_spin.setStyleSheet(self._spin_style())
        price_spin.valueChanged.connect(self._update_totals)
        self.items_table.setCellWidget(row, 4, price_spin)

        # İskonto %
        discount_spin = QDoubleSpinBox()
        discount_spin.setRange(0, 100)
        discount_spin.setDecimals(2)
        discount_spin.setSuffix(" %")
        discount_spin.setValue(discount_rate)
        discount_spin.setStyleSheet(self._spin_style())
        discount_spin.valueChanged.connect(self._update_totals)
        self.items_table.setCellWidget(row, 5, discount_spin)

        # Tutar (hesaplanır)
        amount_item = QTableWidgetItem("0.00")
        amount_item.setFlags(amount_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.items_table.setItem(row, 6, amount_item)

        # Sil butonu
        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(32, 32)
        del_btn.clicked.connect(lambda: self._remove_item_row(row))
        self.items_table.setCellWidget(row, 7, del_btn)

        self.items_table.setRowHeight(row, 50)
        self._update_totals()

    def _remove_item_row(self, row: int):
        """Kalem satırını sil"""
        self.items_table.removeRow(row)
        self._update_totals()

    def _update_totals(self):
        """Toplamları güncelle"""
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

                # Satır tutarını güncelle
                amount_item = self.items_table.item(row, 6)
                if amount_item:
                    amount_item.setText(f"{line_amount:,.2f}")

        # KDV hesapla
        taxable = subtotal - total_discount
        tax = taxable * Decimal("0.18")
        total = taxable + tax

        self.subtotal_label.setText(f"{subtotal:,.2f}")
        self.discount_label.setText(f"-{total_discount:,.2f}")
        self.tax_label.setText(f"{tax:,.2f}")
        self.total_label.setText(f"{total:,.2f}")

    def load_data(self):
        """Düzenleme modunda verileri yükle"""
        if not self.order_data:
            return

        self.order_no_input.setText(self.order_data.get("order_no", ""))

        order_date = self.order_data.get("order_date")
        if order_date:
            if isinstance(order_date, date):
                self.order_date_input.setDate(
                    QDate(order_date.year, order_date.month, order_date.day)
                )

        # Müşteri
        customer_id = self.order_data.get("customer_id")
        customer_name = self.order_data.get("customer_name", "")
        customer_code = self.order_data.get("customer_code", "")
        if customer_id:
            self.selected_customer = {
                "id": customer_id,
                "name": customer_name,
                "code": customer_code
            }
            self.customer_input.setText(f"{customer_code} - {customer_name}")

        delivery_date = self.order_data.get("delivery_date")
        if delivery_date:
            if isinstance(delivery_date, date):
                self.delivery_date_input.setDate(
                    QDate(
                        delivery_date.year,
                        delivery_date.month,
                        delivery_date.day
                    )
                )

        currency = self.order_data.get("currency")
        if currency:
            for i in range(self.currency_input.count()):
                # ComboBox item text "TRY - Türk Lirası" formatında
                if self.currency_input.itemText(i).startswith(currency):
                    self.currency_input.setCurrentIndex(i)
                    break

        self.notes_input.setPlainText(self.order_data.get("notes", "") or "")

        # Kalemleri yükle
        items_data = self.order_data.get("items", [])
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
        """Kaydet"""
        # Validasyon
        if not self.selected_customer:
            QMessageBox.warning(self, "Uyarı", "Lütfen müşteri seçin!")
            return

        if self.items_table.rowCount() == 0:
            QMessageBox.warning(
                self, "Uyarı", "En az bir kalem eklemelisiniz!"
            )
            return

        # Kalemleri topla
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

        qdate = self.order_date_input.date()
        delivery_qdate = self.delivery_date_input.date()

        # Currency enum değerini al (TRY, USD, EUR)
        currency_code = self.currency_input.currentText().split(" - ")[0]

        data = {
            "order_date": date(qdate.year(), qdate.month(), qdate.day()),
            "customer_id": self.selected_customer.get("id"),
            "delivery_date": date(
                delivery_qdate.year(),
                delivery_qdate.month(),
                delivery_qdate.day()
            ),
            "currency": currency_code,
            "notes": self.notes_input.toPlainText().strip() or None,
            "items": items_data,
        }

        if self.is_edit_mode and self.order_data:
            data["id"] = self.order_data.get("id")

        self.saved.emit(data)

    def _on_confirm_order(self):
        """Siparişi onayla"""
        if self.order_data:
            reply = QMessageBox.question(
                self,
                "Sipariş Onayla",
                "Bu siparişi onaylamak istediğinize emin misiniz?\n\n"
                "Onayladıktan sonra düzenleme yapılamaz.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.confirm_order.emit(self.order_data.get("id"))

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
