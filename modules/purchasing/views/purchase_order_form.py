"""
Akıllı İş - Satın Alma Sipariş Formu
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
    QSpinBox,
    QFrame,
    QMessageBox,
    QGridLayout,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QAbstractItemView,
    QDialogButtonBox,
    QFormLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from ui.components.page_header import PageHeader


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
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Kod", "Ad", "Birim"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.doubleClicked.connect(self._on_double_click)

        self._load_items()
        layout.addWidget(self.table)

        # Butonlar
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
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
            self.table.setItem(row, 2, QTableWidgetItem(item.get("unit_name", "")))

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


class PurchaseOrderFormPage(QWidget):
    """Satın alma sipariş formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(
        self,
        order_data: Optional[dict] = None,
        suppliers: list = None,
        warehouses: list = None,
        items: list = None,
        units: list = None,
        parent=None,
    ):
        super().__init__(parent)
        self.order_data = order_data
        self.is_edit_mode = order_data is not None
        self.suppliers = suppliers or []
        self.warehouses = warehouses or []
        self.items = items or []
        self.units = units or []
        self.setup_ui()
        if self.is_edit_mode:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # === Header ===
        title_text = (
            "Sipariş Düzenle" if self.is_edit_mode else "Yeni Satın Alma Siparişi"
        )
        self.header = PageHeader(
            title=title_text,
            show_back=True,
            show_search=False,
            show_refresh=False,
            show_add=False,
            parent=self,
        )
        self.header.back_clicked.connect(self.cancelled.emit)

        # Header butonları
        h_layout = self.header.header_layout()

        # Kaydet
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setProperty("class", "btn-primary")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._on_save)
        h_layout.addWidget(save_btn)

        layout.addWidget(self.header)

        # === Main Content (Split View) ===
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)

        # --- LEFT: Genel Bilgiler ---
        left_frame = QFrame()
        left_frame.setProperty("class", "card")
        left_frame.setFixedWidth(350)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(16, 16, 16, 16)

        left_title = QLabel("📝 Sipariş Bilgileri")
        left_layout.addWidget(left_title)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Sipariş No
        self.order_no_input = QLineEdit()
        self.order_no_input.setPlaceholderText("Otomatik")
        self.order_no_input.setReadOnly(True)
        form_layout.addRow("Sipariş No", self.order_no_input)

        # Tarih
        self.order_date_input = QDateEdit()
        self.order_date_input.setDate(QDate.currentDate())
        self.order_date_input.setCalendarPopup(True)
        form_layout.addRow("Tarih *", self.order_date_input)

        # Tedarikçi
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("- Tedarikçi Seçin -", None)
        for s in self.suppliers:
            self.supplier_combo.addItem(f"{s.get('code', '')} - {s.get('name', '')}", s)
        self.supplier_combo.currentIndexChanged.connect(self._on_supplier_changed)
        form_layout.addRow("Tedarikçi *", self.supplier_combo)

        # Teslim Tarihi
        self.delivery_date_input = QDateEdit()
        self.delivery_date_input.setDate(QDate.currentDate().addDays(7))
        self.delivery_date_input.setCalendarPopup(True)
        form_layout.addRow("Teslim Tarihi", self.delivery_date_input)

        # Depo
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.addItem("- Depo Seçin -", None)
        for w in self.warehouses:
            self.warehouse_combo.addItem(w.get("name", ""), w.get("id"))
        form_layout.addRow("Teslimat Deposu", self.warehouse_combo)

        # Ödeme Vadesi
        self.payment_term_input = QSpinBox()
        self.payment_term_input.setRange(0, 365)
        self.payment_term_input.setValue(30)
        self.payment_term_input.setSuffix(" gün")
        form_layout.addRow("Ödeme Vadesi", self.payment_term_input)

        # Para Birimi
        self.currency_combo = QComboBox()
        self.currency_combo.addItem("🇹🇷 TRY", "TRY")
        self.currency_combo.addItem("🇺🇸 USD", "USD")
        self.currency_combo.addItem("🇪🇺 EUR", "EUR")
        self.currency_combo.addItem("🇬🇧 GBP", "GBP")
        self.currency_combo.currentIndexChanged.connect(self._on_currency_changed)
        form_layout.addRow("Para Birimi", self.currency_combo)

        # Döviz Kuru
        self.exchange_rate_input = QDoubleSpinBox()
        self.exchange_rate_input.setRange(0.0001, 9999)
        self.exchange_rate_input.setDecimals(4)
        self.exchange_rate_input.setValue(1)
        # Kur değişimi için gerekirse:
        # self.exchange_rate_input.valueChanged.connect(self._on_currency_changed)
        form_layout.addRow("Döviz Kuru", self.exchange_rate_input)

        # Notlar
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Açıklama...")
        form_layout.addRow("Notlar", self.notes_input)

        left_layout.addLayout(form_layout)
        left_layout.addStretch()
        content_layout.addWidget(left_frame)

        # --- RIGHT: Sipariş Kalemleri ---
        right_frame = QFrame()
        right_frame.setProperty("class", "card")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)

        # Başlık ve Buton
        items_header = QHBoxLayout()
        items_header.addWidget(QLabel("📦 Sipariş Kalemleri"))
        items_header.addStretch()

        add_item_btn = QPushButton("➕ Kalem Ekle")
        add_item_btn.clicked.connect(self._add_item_row)
        items_header.addWidget(add_item_btn)

        right_layout.addLayout(items_header)

        # Tablo
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(8)
        self.items_table.setHorizontalHeaderLabels(
            [
                "Stok Kodu",
                "Stok Adı",
                "Miktar",
                "Birim",
                "Birim Fiyat",
                "KDV %",
                "Satır Toplamı",
                "",  # İşlem
            ]
        )
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setProperty("class", "enhanced-table")

        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Adı genişlet
        self.items_table.setColumnWidth(0, 100)
        self.items_table.setColumnWidth(2, 90)
        self.items_table.setColumnWidth(3, 85)  # Birim combo
        self.items_table.setColumnWidth(4, 110)
        self.items_table.setColumnWidth(5, 80)
        self.items_table.setColumnWidth(6, 110)
        self.items_table.setColumnWidth(7, 60)  # İşlem sütunu genişletildi

        right_layout.addWidget(self.items_table)

        # Toplamlar (Alt kısım)
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()

        totals_frame = QFrame()
        totals_frame.setProperty(
            "class", "totals-panel"
        )  # Özel stil gerekebilir yada inline
        totals_inner = QGridLayout(totals_frame)
        totals_inner.setSpacing(8)
        totals_inner.setContentsMargins(12, 12, 12, 12)

        totals_inner.addWidget(QLabel("Ara Toplam:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.subtotal_label = QLabel("₺0.00")
        self.subtotal_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_inner.addWidget(self.subtotal_label, 0, 1)

        totals_inner.addWidget(QLabel("KDV:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.tax_label = QLabel("₺0.00")
        self.tax_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_inner.addWidget(self.tax_label, 1, 1)

        totals_inner.addWidget(
            QLabel("Genel Toplam:"), 2, 0, Qt.AlignmentFlag.AlignRight
        )
        self.total_label = QLabel("₺0.00")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.total_label.setProperty("class", "h4 text-primary")
        totals_inner.addWidget(self.total_label, 2, 1)

        totals_layout.addWidget(totals_frame)
        right_layout.addLayout(totals_layout)

        content_layout.addWidget(right_frame)
        layout.addLayout(content_layout)

    def _add_item_row(self):
        """Kalem ekle"""
        if not self.items:
            QMessageBox.warning(self, "Uyarı", "Stok kartı bulunamadı!")
            return

        dialog = ItemSelectorDialog(self.items, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_item:
            # Seçilen stoğun varsayılan birimi ile ekle
            self._insert_item_row(
                dialog.selected_item, unit_id=dialog.selected_item.get("unit_id")
            )

    def _insert_item_row(
        self,
        item: dict,
        quantity: float = 1,
        unit_price: float = 0,
        tax_rate: float = 20,
        unit_id: int = None,
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
        qty_spin.setDecimals(2)
        qty_spin.setValue(quantity)
        qty_spin.valueChanged.connect(lambda: self._calculate_line_total(row))
        self.items_table.setCellWidget(row, 2, qty_spin)

        # Birim (ComboBox)
        unit_combo = QComboBox()
        for u in self.units:
            unit_combo.addItem(u.get("name", ""), u.get("id"))

        # Varsayılan birim seçimi
        selected_unit_id = unit_id or item.get("unit_id")
        if selected_unit_id:
            for i in range(unit_combo.count()):
                if unit_combo.itemData(i) == selected_unit_id:
                    unit_combo.setCurrentIndex(i)
                    break
        self.items_table.setCellWidget(row, 3, unit_combo)

        # Birim Fiyat
        price_spin = QDoubleSpinBox()
        price_spin.setRange(0, 999999999)
        price_spin.setDecimals(2)
        price_spin.setValue(unit_price)
        price_spin.valueChanged.connect(lambda: self._calculate_line_total(row))
        self.items_table.setCellWidget(row, 4, price_spin)

        # KDV %
        tax_spin = QDoubleSpinBox()
        tax_spin.setRange(0, 100)
        tax_spin.setDecimals(2)
        tax_spin.setValue(tax_rate)
        tax_spin.setSuffix("%")
        tax_spin.valueChanged.connect(lambda: self._calculate_line_total(row))
        self.items_table.setCellWidget(row, 5, tax_spin)

        # Satır Toplamı
        total_item = QTableWidgetItem("₺0.00")
        total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        total_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.items_table.setItem(row, 6, total_item)

        # Sil butonu
        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(30, 30)
        del_btn.setProperty("class", "btn-danger")
        del_btn.clicked.connect(lambda: self._remove_item_row(row))
        self.items_table.setCellWidget(row, 7, del_btn)

        self.items_table.setRowHeight(row, 44)
        self._calculate_line_total(row)

    def _remove_item_row(self, row: int):
        self.items_table.removeRow(row)
        self._calculate_totals()

    def _calculate_line_total(self, row: int):
        """Satır toplamını hesapla"""
        qty_widget = self.items_table.cellWidget(row, 2)
        price_widget = self.items_table.cellWidget(row, 4)

        symbol = self._get_currency_symbol()

        if qty_widget and price_widget:
            qty = qty_widget.value()
            price = price_widget.value()
            line_total = qty * price

            total_item = self.items_table.item(row, 6)
            if total_item:
                total_item.setText(f"{symbol}{line_total:,.2f}")

        self._calculate_totals()

    def _calculate_totals(self):
        """Genel toplamları hesapla"""
        subtotal = 0
        tax_total = 0
        symbol = self._get_currency_symbol()

        for row in range(self.items_table.rowCount()):
            qty_widget = self.items_table.cellWidget(row, 2)
            price_widget = self.items_table.cellWidget(row, 4)
            tax_widget = self.items_table.cellWidget(row, 5)

            if qty_widget and price_widget and tax_widget:
                qty = qty_widget.value()
                price = price_widget.value()
                tax_rate = tax_widget.value()

                line_subtotal = qty * price
                line_tax = line_subtotal * tax_rate / 100

                subtotal += line_subtotal
                tax_total += line_tax

        total = subtotal + tax_total

        self.subtotal_label.setText(f"{symbol}{subtotal:,.2f}")
        self.tax_label.setText(f"{symbol}{tax_total:,.2f}")
        self.total_label.setText(f"{symbol}{total:,.2f}")

    def load_data(self):
        """Düzenleme modunda verileri yükle"""
        if not self.order_data:
            return

        self.order_no_input.setText(self.order_data.get("order_no", ""))

        order_date = self.order_data.get("order_date")
        if order_date and isinstance(order_date, date):
            self.order_date_input.setDate(
                QDate(order_date.year, order_date.month, order_date.day)
            )

        # Tedarikçi
        supplier_id = self.order_data.get("supplier_id")
        for i in range(self.supplier_combo.count()):
            data = self.supplier_combo.itemData(i)
            if data and data.get("id") == supplier_id:
                self.supplier_combo.setCurrentIndex(i)
                break

        delivery_date = self.order_data.get("delivery_date")
        if delivery_date and isinstance(delivery_date, date):
            self.delivery_date_input.setDate(
                QDate(delivery_date.year, delivery_date.month, delivery_date.day)
            )

        # Depo
        warehouse_id = self.order_data.get("delivery_warehouse_id")
        for i in range(self.warehouse_combo.count()):
            if self.warehouse_combo.itemData(i) == warehouse_id:
                self.warehouse_combo.setCurrentIndex(i)
                break

        self.payment_term_input.setValue(
            self.order_data.get("payment_term_days", 30) or 30
        )

        currency = self.order_data.get("currency", "TRY")
        for i in range(self.currency_combo.count()):
            if self.currency_combo.itemData(i) == currency:
                self.currency_combo.setCurrentIndex(i)
                break

        self.exchange_rate_input.setValue(
            float(self.order_data.get("exchange_rate", 1) or 1)
        )
        self.notes_input.setPlainText(self.order_data.get("notes", "") or "")

        # Kalemleri yükle
        for item_data in self.order_data.get("items", []):
            item_id = item_data.get("item_id")

            # Stok bilgilerini bul
            item_info = next((i for i in self.items if i.get("id") == item_id), None)

            if item_info:
                # Birim bilgisini item_data'dan, yoksa stok kartından al
                unit_id = item_data.get("unit_id")

                self._insert_item_row(
                    item_info,
                    quantity=float(item_data.get("quantity", 1)),
                    unit_price=float(item_data.get("unit_price", 0) or 0),
                    tax_rate=float(item_data.get("tax_rate", 20) or 20),
                    unit_id=unit_id,
                )

    def _on_supplier_changed(self):
        """Tedarikçi seçildiğinde varsayılan değerleri doldur"""
        supplier = self.supplier_combo.currentData()
        if supplier:
            # Ödeme vadesi
            payment_term = supplier.get("payment_term_days", 30) or 30
            self.payment_term_input.setValue(payment_term)

            # Para birimi
            currency = supplier.get("currency", "TRY")
            for i in range(self.currency_combo.count()):
                if self.currency_combo.itemData(i) == currency:
                    self.currency_combo.setCurrentIndex(i)
                    break

    def _get_currency_symbol(self) -> str:
        """Seçili para birimine göre simge döndür"""
        currency = self.currency_combo.currentData()
        if currency == "USD":
            return "$"
        elif currency == "EUR":
            return "€"
        elif currency == "GBP":
            return "£"
        return "₺"

    def _on_currency_changed(self):
        """Para birimi değiştiğinde"""
        # Tüm satırları yeniden hesapla (simgeleri güncellemek için)
        for row in range(self.items_table.rowCount()):
            self._calculate_line_total(row)
        self._calculate_totals()

    def _on_save(self):
        """Kaydet"""
        supplier = self.supplier_combo.currentData()
        if not supplier:
            QMessageBox.warning(self, "Uyarı", "Lütfen tedarikçi seçin!")
            return

        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, "Uyarı", "En az bir kalem eklemelisiniz!")
            return

        # Kalemleri topla
        items_data = []
        for row in range(self.items_table.rowCount()):
            code_item = self.items_table.item(row, 0)
            item_id = code_item.data(Qt.ItemDataRole.UserRole) if code_item else None

            unit_widget = self.items_table.cellWidget(row, 3)
            unit_id = unit_widget.currentData() if unit_widget else None

            qty_widget = self.items_table.cellWidget(row, 2)
            quantity = qty_widget.value() if qty_widget else 0

            price_widget = self.items_table.cellWidget(row, 4)
            unit_price = price_widget.value() if price_widget else 0

            tax_widget = self.items_table.cellWidget(row, 5)
            tax_rate = tax_widget.value() if tax_widget else 20

            if item_id and quantity > 0:
                items_data.append(
                    {
                        "item_id": item_id,
                        "quantity": Decimal(str(quantity)),
                        "unit_id": unit_id,
                        "unit_price": Decimal(str(unit_price)),
                        "tax_rate": Decimal(str(tax_rate)),
                    }
                )

        order_qdate = self.order_date_input.date()
        delivery_qdate = self.delivery_date_input.date()

        data = {
            "order_date": date(
                order_qdate.year(), order_qdate.month(), order_qdate.day()
            ),
            "supplier_id": supplier.get("id"),
            "delivery_date": date(
                delivery_qdate.year(), delivery_qdate.month(), delivery_qdate.day()
            ),
            "delivery_warehouse_id": self.warehouse_combo.currentData(),
            "payment_term_days": self.payment_term_input.value(),
            "currency": self.currency_combo.currentData(),
            "exchange_rate": Decimal(str(self.exchange_rate_input.value())),
            "notes": self.notes_input.toPlainText().strip() or None,
            "items": items_data,
        }

        if self.is_edit_mode and self.order_data:
            data["id"] = self.order_data.get("id")

        self.saved.emit(data)
