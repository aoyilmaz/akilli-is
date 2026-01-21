"""
Akıllı İş - Satınalma Faturası Form Sayfası
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
    QSplitter,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QSize
from ui.components import (
    PageHeader,
    create_save_button,
    create_cancel_button,
)


class PurchaseInvoiceFormPage(QWidget):
    """Satınalma faturası formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(
        self,
        invoice_data: Optional[dict] = None,
        suppliers: list = None,
        items: list = None,
        parent=None,
    ):
        super().__init__(parent)
        self.invoice_data = invoice_data
        self.is_edit_mode = invoice_data is not None
        self.suppliers = suppliers or []
        self.suppliers = suppliers or []
        self.items = items or []
        self.currency_symbol = "₺"
        self.CURRENCY_SYMBOLS = {"TRY": "₺", "USD": "$", "EUR": "€", "GBP": "£"}
        self.setup_ui()
        if self.is_edit_mode:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === HEADER ===
        title = "Fatura Düzenle" if self.is_edit_mode else "Yeni Satınalma Faturası"

        self.header = PageHeader(
            title=title,
            icon="📄",
            show_search=False,
            show_refresh=False,
            show_add=False,
            parent=self,
        )

        # Header Butonları
        cancel_btn = create_cancel_button()
        cancel_btn.setText("Vazgeç")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setMinimumHeight(30)
        cancel_btn.setMaximumWidth(200)
        # Fixed size'ı kaldırmak için (action_buttons içinden geliyor)
        cancel_btn.setFixedSize(QSize(16777215, 30))
        cancel_btn.setProperty("class", "btn-secondary")
        cancel_btn.clicked.connect(self.cancelled.emit)
        self.header.add_action_button(cancel_btn)

        save_btn = create_save_button()
        save_btn.setText("Kaydet")
        save_btn.setMinimumWidth(100)
        save_btn.setMinimumHeight(30)
        save_btn.setMaximumWidth(200)
        save_btn.setFixedSize(QSize(16777215, 30))
        save_btn.setProperty("class", "btn-primary")
        save_btn.clicked.connect(self._on_save)
        self.header.add_action_button(save_btn)

        layout.addWidget(self.header)

        # === CONTENT (SPLIT VIEW) ===
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background-color: #334155; }")

        # --- SOL PANEL: FATURA BİLGİLERİ ---
        left_widget = QWidget()
        left_widget.setMinimumWidth(450)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(24, 24, 24, 24)
        left_layout.setSpacing(16)

        # Scroll Area for Left Panel
        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setFrameShape(QFrame.Shape.NoFrame)
        form_content = QWidget()
        form_layout = QVBoxLayout(form_content)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(24)

        # Kart: Fatura Bilgileri
        info_card = QFrame()
        info_card.setProperty("class", "card")
        info_layout = QGridLayout(info_card)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(16)

        # Başlık
        card_title = QLabel("Fatura Bilgileri")
        card_title.setProperty("class", "h3")
        info_layout.addWidget(card_title, 0, 0, 1, 2)

        row = 1
        # Fatura No
        info_layout.addWidget(self._create_label("Fatura No"), row, 0)
        self.invoice_no_input = QLineEdit()
        self.invoice_no_input.setPlaceholderText("Otomatik")
        self.invoice_no_input.setReadOnly(True)
        info_layout.addWidget(self.invoice_no_input, row, 1)
        row += 1

        # Fatura Tarihi
        info_layout.addWidget(self._create_label("Fatura Tarihi *"), row, 0)
        self.invoice_date_input = QDateEdit()
        self.invoice_date_input.setDate(QDate.currentDate())
        self.invoice_date_input.setCalendarPopup(True)
        info_layout.addWidget(self.invoice_date_input, row, 1)
        row += 1

        # Vade Tarihi
        info_layout.addWidget(self._create_label("Vade Tarihi"), row, 0)
        self.due_date_input = QDateEdit()
        self.due_date_input.setDate(QDate.currentDate().addDays(30))
        self.due_date_input.setCalendarPopup(True)
        info_layout.addWidget(self.due_date_input, row, 1)
        row += 1

        # Para Birimi
        info_layout.addWidget(self._create_label("Para Birimi"), row, 0)
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["TRY", "USD", "EUR", "GBP"])
        self.currency_combo.currentTextChanged.connect(self._on_currency_changed)
        info_layout.addWidget(self.currency_combo, row, 1)
        row += 1

        # Tedarikçi
        info_layout.addWidget(self._create_label("Tedarikçi *"), row, 0)
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("- Seçiniz -", None)
        for s in self.suppliers:
            self.supplier_combo.addItem(f"{s.get('name', '')}", s.get("id"))
        info_layout.addWidget(self.supplier_combo, row, 1)
        row += 1

        # Tedarikçi Belge No/Tarih
        info_layout.addWidget(self._create_label("Ted. Fatura No"), row, 0)
        self.supplier_invoice_no_input = QLineEdit()
        self.supplier_invoice_no_input.setPlaceholderText("Örn: ABC2024...")
        info_layout.addWidget(self.supplier_invoice_no_input, row, 1)
        row += 1

        info_layout.addWidget(self._create_label("Ted. Fatura Tarihi"), row, 0)
        self.supplier_invoice_date_input = QDateEdit()
        self.supplier_invoice_date_input.setDate(QDate.currentDate())
        self.supplier_invoice_date_input.setCalendarPopup(True)
        info_layout.addWidget(self.supplier_invoice_date_input, row, 1)
        row += 1

        # Notlar
        info_layout.addWidget(self._create_label("Notlar"), row, 0)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Açıklama giriniz...")
        info_layout.addWidget(self.notes_input, row, 1)

        form_layout.addWidget(info_card)
        form_layout.addStretch()

        form_scroll.setWidget(form_content)
        left_layout.addWidget(form_scroll)

        # --- SAĞ PANEL: KALEMLER ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(24, 24, 24, 24)
        right_layout.setSpacing(16)

        # Kalem Ekleme Kartı
        add_card = QFrame()
        add_card.setProperty("class", "card")
        add_layout = QHBoxLayout(add_card)
        add_layout.setContentsMargins(12, 12, 12, 12)
        add_layout.setSpacing(12)

        self.item_combo = QComboBox()
        self.item_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.item_combo.addItem("- Stok Kartı Ekle -", None)
        for item in self.items:
            self.item_combo.addItem(
                f"{item.get('code', '')} - {item.get('name', '')}", item
            )
        add_layout.addWidget(self.item_combo, 2)

        self.qty_input = QDoubleSpinBox()
        self.qty_input.setRange(0, 999999)
        self.qty_input.setValue(1)
        self.qty_input.setPrefix("Miktar: ")
        self.qty_input.setMinimumWidth(120)
        add_layout.addWidget(self.qty_input)

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 999999999)
        self.price_input.setValue(0)
        self.price_input.setPrefix(f"{self.currency_symbol}")
        self.price_input.setMinimumWidth(120)
        add_layout.addWidget(self.price_input)

        self.tax_input = QDoubleSpinBox()
        self.tax_input.setRange(0, 100)
        self.tax_input.setValue(18)
        self.tax_input.setPrefix("KDV: %")
        self.tax_input.setMinimumWidth(90)
        add_layout.addWidget(self.tax_input)

        add_btn = QPushButton("Ekle")
        add_btn.setProperty("class", "btn-primary")
        add_btn.clicked.connect(self._add_item_row)
        add_layout.addWidget(add_btn)

        right_layout.addWidget(add_card)

        # Tablo
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(8)
        self.items_table.setHorizontalHeaderLabels(
            ["Kod", "Stok Adı", "Miktar", "Birim", "Birim Fiyat", "KDV", "Toplam", ""]
        )
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setShowGrid(False)
        self.items_table.setAlternatingRowColors(True)
        # Modern Tablo Stili (Global CSS ile desteklenmeli ama garanti olsun)
        self.items_table.setStyleSheet(
            """
            QTableWidget {
                background-color: transparent;
                border: 1px solid #334155;
                border-radius: 6px;
                gridline-color: #334155;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #e2e8f0;
                padding: 8px;
                border: none;
                font-weight: 600;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #1e293b;
            }
        """
        )

        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.items_table.setColumnWidth(0, 100)
        self.items_table.setColumnWidth(2, 80)
        self.items_table.setColumnWidth(3, 70)
        self.items_table.setColumnWidth(4, 100)
        self.items_table.setColumnWidth(5, 60)
        self.items_table.setColumnWidth(6, 100)
        self.items_table.setColumnWidth(7, 40)

        right_layout.addWidget(self.items_table)

        # Toplam Kartı
        total_card = QFrame()
        total_card.setProperty("class", "card")
        total_layout = QHBoxLayout(total_card)
        total_layout.setContentsMargins(16, 16, 16, 16)

        total_layout.addStretch()

        totals_grid = QGridLayout()
        totals_grid.setHorizontalSpacing(24)

        lbl_sub = QLabel("Ara Toplam")
        lbl_sub.setProperty("class", "text-muted")
        totals_grid.addWidget(lbl_sub, 0, 0)
        self.subtotal_label = QLabel(f"{self.currency_symbol}0.00")
        self.subtotal_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_grid.addWidget(self.subtotal_label, 0, 1)

        lbl_tax = QLabel("KDV Toplam")
        lbl_tax.setProperty("class", "text-muted")
        totals_grid.addWidget(lbl_tax, 1, 0)
        self.tax_total_label = QLabel(f"{self.currency_symbol}0.00")
        self.tax_total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_grid.addWidget(self.tax_total_label, 1, 1)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #334155;")
        totals_grid.addWidget(line, 2, 0, 1, 2)

        lbl_tot = QLabel("GENEL TOPLAM")
        lbl_tot.setProperty("class", "h3")
        totals_grid.addWidget(lbl_tot, 3, 0)
        self.total_label = QLabel(f"{self.currency_symbol}0.00")
        self.total_label.setProperty("class", "h2 text-primary")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_grid.addWidget(self.total_label, 3, 1)

        total_layout.addLayout(totals_grid)
        right_layout.addWidget(total_card)

        # Splitter Ekleme
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)  # Sol panel
        splitter.setStretchFactor(1, 2)  # Sağ panel

        layout.addWidget(splitter)

    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setProperty("class", "form-label")
        return label

    def _on_currency_changed(self, currency_code):
        """Para birimi değiştiğinde arayüzü güncelle"""
        self.currency_symbol = self.CURRENCY_SYMBOLS.get(currency_code, currency_code)

        # Input alanını güncelle
        self.price_input.setPrefix(f"{self.currency_symbol}")

        # Tabloyu güncelle (yeniden populate etmeye gerek yok, hücreleri güncelle)
        for row in range(self.items_table.rowCount()):
            # Birim Fiyat
            price_item = self.items_table.item(row, 4)
            if price_item:
                price = float(price_item.data(Qt.ItemDataRole.UserRole) or 0)
                price_item.setText(f"{self.currency_symbol}{price:,.2f}")

            # Toplam
            total_item = self.items_table.item(row, 6)
            if total_item:
                qty_item = self.items_table.item(row, 2)
                if qty_item:
                    try:
                        qty = float(qty_item.text().replace(",", ""))
                        line_total = qty * price
                        total_item.setText(f"{self.currency_symbol}{line_total:,.2f}")
                    except ValueError:
                        pass

        # Toplam etiketlerini güncelle
        self._update_totals()

    def _add_item_row(self):
        """Kalem ekle"""
        item_data = self.item_combo.currentData()
        if not item_data:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir stok kartı seçin!")
            return

        qty = self.qty_input.value()
        price = self.price_input.value()
        tax_rate = self.tax_input.value()

        if qty <= 0:
            QMessageBox.warning(self, "Uyarı", "Miktar sıfırdan büyük olmalıdır!")
            return

        self._insert_item_row(item_data, qty, price, tax_rate)

        # Reset
        self.item_combo.setCurrentIndex(0)
        self.qty_input.setValue(1)
        self.price_input.setValue(0)
        self.tax_input.setValue(18)

    def _insert_item_row(
        self, item: dict, quantity: float, unit_price: float, tax_rate: float
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
        qty_item = QTableWidgetItem(f"{quantity:,.4f}")
        qty_item.setFlags(qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        qty_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.items_table.setItem(row, 2, qty_item)

        # Birim
        unit_name = item.get("unit_name", "")
        unit_item = QTableWidgetItem(unit_name)
        unit_item.setData(Qt.ItemDataRole.UserRole, item.get("unit_id"))
        unit_item.setFlags(unit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        unit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.items_table.setItem(row, 3, unit_item)

        # Birim Fiyat
        price_item = QTableWidgetItem(f"{self.currency_symbol}{unit_price:,.2f}")
        price_item.setData(Qt.ItemDataRole.UserRole, unit_price)
        price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        price_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.items_table.setItem(row, 4, price_item)

        # KDV
        tax_item = QTableWidgetItem(f"%{tax_rate:.0f}")
        tax_item.setData(Qt.ItemDataRole.UserRole, tax_rate)
        tax_item.setFlags(tax_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        tax_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.items_table.setItem(row, 5, tax_item)

        # Toplam
        line_total = quantity * unit_price
        total_item = QTableWidgetItem(f"{self.currency_symbol}{line_total:,.2f}")
        total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        total_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.items_table.setItem(row, 6, total_item)

        # Sil butonu
        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(32, 32)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: none;
                color: #ef4444;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.1);
                border-radius: 4px;
            }
        """
        )
        del_btn.clicked.connect(lambda: self._remove_row(row))
        self.items_table.setCellWidget(row, 7, del_btn)

        self.items_table.setRowHeight(row, 44)
        self._update_totals()

    def _remove_row(self, row: int):
        """Satır sil ve toplamları güncelle"""
        self.items_table.removeRow(row)

        # Yeniden bağlama
        for r in range(self.items_table.rowCount()):
            btn = self.items_table.cellWidget(r, 7)
            if btn:
                new_btn = QPushButton("🗑")
                new_btn.setFixedSize(32, 32)
                new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                new_btn.setStyleSheet(btn.styleSheet())
                new_btn.clicked.connect(
                    lambda checked, r_idx=r: self._remove_row(r_idx)
                )
                self.items_table.setCellWidget(r, 7, new_btn)

        self._update_totals()

    def _update_totals(self):
        """Toplamları hesapla"""
        subtotal = Decimal("0")
        tax_total = Decimal("0")

        for row in range(self.items_table.rowCount()):
            qty_item = self.items_table.item(row, 2)
            price_item = self.items_table.item(row, 4)
            tax_item = self.items_table.item(row, 5)

            if qty_item and price_item and tax_item:
                try:
                    qty_text = qty_item.text().replace(",", "")
                    qty = Decimal(qty_text)

                    price = Decimal(str(price_item.data(Qt.ItemDataRole.UserRole) or 0))
                    tax_rate = Decimal(
                        str(tax_item.data(Qt.ItemDataRole.UserRole) or 0)
                    )

                    line_subtotal = qty * price
                    line_tax = line_subtotal * tax_rate / 100

                    subtotal += line_subtotal
                    tax_total += line_tax
                except:
                    pass

        total = subtotal + tax_total

        self.subtotal_label.setText(f"{self.currency_symbol}{float(subtotal):,.2f}")
        self.tax_total_label.setText(f"{self.currency_symbol}{float(tax_total):,.2f}")
        self.total_label.setText(f"{self.currency_symbol}{float(total):,.2f}")

    def load_data(self):
        """Düzenleme modunda verileri yükle"""
        if not self.invoice_data:
            return

        self.invoice_no_input.setText(self.invoice_data.get("invoice_no", ""))

        inv_date = self.invoice_data.get("invoice_date")
        if inv_date and isinstance(inv_date, date):
            self.invoice_date_input.setDate(
                QDate(inv_date.year, inv_date.month, inv_date.day)
            )

        due = self.invoice_data.get("due_date")
        if due and isinstance(due, date):
            self.due_date_input.setDate(QDate(due.year, due.month, due.day))

        # Para Birimi
        currency = self.invoice_data.get("currency", "TRY")
        self.currency_combo.setCurrentText(currency)
        # _on_currency_changed otomatik tetiklenir mi? Emin olmak için manuel çağırabiliriz
        # ancak setCurrentText genelde sinyal tetikler. Yine de manuel set edelim:
        self._on_currency_changed(currency)

        # Tedarikçi
        supplier_id = self.invoice_data.get("supplier_id")
        for i in range(self.supplier_combo.count()):
            if self.supplier_combo.itemData(i) == supplier_id:
                self.supplier_combo.setCurrentIndex(i)
                break

        self.supplier_invoice_no_input.setText(
            self.invoice_data.get("supplier_invoice_no", "") or ""
        )

        sup_date = self.invoice_data.get("supplier_invoice_date")
        if sup_date and isinstance(sup_date, date):
            self.supplier_invoice_date_input.setDate(
                QDate(sup_date.year, sup_date.month, sup_date.day)
            )

        self.notes_input.setPlainText(self.invoice_data.get("notes", "") or "")

        # Kalemleri yükle
        self.items_table.setRowCount(0)  # Temizle
        items_data = self.invoice_data.get("items", [])
        for item_data in items_data:
            item_id = item_data.get("item_id")
            # item_info bul
            item_info = next((i for i in self.items if i.get("id") == item_id), None)

            # Eğer listede yoksa manuel dict oluştur
            if not item_info and item_id:
                item_info = {
                    "id": item_id,
                    "code": "???",
                    "name": "Bilinmeyen Stok",
                    "unit_name": "-",
                }

            if item_info:
                self._insert_item_row(
                    item_info,
                    float(item_data.get("quantity", 0)),
                    float(item_data.get("unit_price", 0) or 0),
                    float(item_data.get("tax_rate", 18) or 18),
                )

    def _on_save(self):
        """Kaydet"""
        # Validasyon
        supplier_id = self.supplier_combo.currentData()
        if not supplier_id:
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

            qty_item = self.items_table.item(row, 2)
            # Text parse
            try:
                quantity = float(qty_item.text().replace(",", "")) if qty_item else 0
            except:
                quantity = 0

            unit_item = self.items_table.item(row, 3)
            unit_id = unit_item.data(Qt.ItemDataRole.UserRole) if unit_item else None

            price_item = self.items_table.item(row, 4)
            unit_price = price_item.data(Qt.ItemDataRole.UserRole) if price_item else 0

            tax_item = self.items_table.item(row, 5)
            tax_rate = tax_item.data(Qt.ItemDataRole.UserRole) if tax_item else 18

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

        q_inv_date = self.invoice_date_input.date()
        q_due_date = self.due_date_input.date()
        q_sup_date = self.supplier_invoice_date_input.date()

        data = {
            "invoice_date": date(
                q_inv_date.year(), q_inv_date.month(), q_inv_date.day()
            ),
            "due_date": date(q_due_date.year(), q_due_date.month(), q_due_date.day()),
            "supplier_id": supplier_id,
            "supplier_invoice_no": (
                self.supplier_invoice_no_input.text().strip() or None
            ),
            "supplier_invoice_date": date(
                q_sup_date.year(), q_sup_date.month(), q_sup_date.day()
            ),
            "currency": self.currency_combo.currentText(),
            "exchange_rate": 1.0,  # Şimdilik sabit 1
            "notes": self.notes_input.toPlainText().strip() or None,
            "items": items_data,
        }

        if self.is_edit_mode and self.invoice_data:
            data["id"] = self.invoice_data.get("id")

        self.saved.emit(data)
