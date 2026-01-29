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
import qtawesome as qta

from config.icons import ICONS
from ui.components import (
    PageHeader,
    create_save_button,
    create_cancel_button,
    CurrencyInput,
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

        # Header
        title = "Fatura Düzenle" if self.is_edit_mode else "Yeni Satınalma Faturası"
        self.header = PageHeader(
            title=title,
            icon=ICONS.INVOICE,
            show_search=False,
            show_refresh=False,
            show_add=False,
            parent=self,
        )

        cancel_btn = create_cancel_button()
        cancel_btn.setText("Vazgeç")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setFixedHeight(30)
        cancel_btn.setProperty("class", "btn-secondary")
        cancel_btn.clicked.connect(self.cancelled.emit)
        self.header.add_action_button(cancel_btn)

        save_btn = create_save_button()
        save_btn.setText("Kaydet")
        save_btn.setMinimumWidth(100)
        save_btn.setFixedHeight(30)
        save_btn.setProperty("class", "btn-primary")
        save_btn.clicked.connect(self._on_save)
        self.header.add_action_button(save_btn)

        layout.addWidget(self.header)

        # Content (SPLIT VIEW)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background-color: #334155; }")

        # SOL PANEL: FATURA BİLGİLERİ
        left_widget = QWidget()
        left_widget.setMinimumWidth(450)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(24, 24, 24, 24)
        left_layout.setSpacing(16)

        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setFrameShape(QFrame.Shape.NoFrame)
        form_content = QWidget()
        form_layout = QVBoxLayout(form_content)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(24)

        info_card = QFrame()
        info_card.setProperty("class", "card")
        info_layout = QGridLayout(info_card)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(16)

        card_title = QLabel("Fatura Bilgileri")
        card_title.setProperty("class", "h3")
        info_layout.addWidget(card_title, 0, 0, 1, 2)

        row = 1
        info_layout.addWidget(self._create_label("Fatura No"), row, 0)
        self.invoice_no_input = QLineEdit()
        self.invoice_no_input.setPlaceholderText("Otomatik")
        self.invoice_no_input.setReadOnly(True)
        info_layout.addWidget(self.invoice_no_input, row, 1)
        row += 1

        info_layout.addWidget(self._create_label("Fatura Tarihi *"), row, 0)
        self.invoice_date_input = QDateEdit()
        self.invoice_date_input.setDate(QDate.currentDate())
        self.invoice_date_input.setCalendarPopup(True)
        info_layout.addWidget(self.invoice_date_input, row, 1)
        row += 1

        info_layout.addWidget(self._create_label("Vade Tarihi"), row, 0)
        self.due_date_input = QDateEdit()
        self.due_date_input.setDate(QDate.currentDate().addDays(30))
        self.due_date_input.setCalendarPopup(True)
        info_layout.addWidget(self.due_date_input, row, 1)
        row += 1

        info_layout.addWidget(self._create_label("Para Birimi"), row, 0)
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["TRY", "USD", "EUR", "GBP"])
        self.currency_combo.currentTextChanged.connect(self._on_currency_changed)
        info_layout.addWidget(self.currency_combo, row, 1)
        row += 1

        info_layout.addWidget(self._create_label("Tedarikçi *"), row, 0)
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("- Seçiniz -", None)
        for s in self.suppliers:
            self.supplier_combo.addItem(f"{s.get('name', '')}", s.get("id"))
        info_layout.addWidget(self.supplier_combo, row, 1)
        row += 1

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

        info_layout.addWidget(self._create_label("Notlar"), row, 0)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Açıklama giriniz...")
        info_layout.addWidget(self.notes_input, row, 1)

        form_layout.addWidget(info_card)
        form_layout.addStretch()
        form_scroll.setWidget(form_content)
        left_layout.addWidget(form_scroll)

        # SAĞ PANEL: KALEMLER
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(24, 24, 24, 24)
        right_layout.setSpacing(16)

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

        self.price_input = CurrencyInput()
        self.price_input.setValue(0)
        self.price_input.setMinimumWidth(120)
        add_layout.addWidget(self.price_input)

        self.tax_input = QDoubleSpinBox()
        self.tax_input.setRange(0, 100)
        self.tax_input.setValue(18)
        self.tax_input.setPrefix("KDV: %")
        self.tax_input.setMinimumWidth(90)
        add_layout.addWidget(self.tax_input)

        add_btn = QPushButton("Ekle")
        add_btn.setIcon(qta.icon(ICONS.ADD, color="#ffffff"))
        add_btn.setProperty("class", "btn-primary")
        add_btn.clicked.connect(self._add_item_row)
        add_layout.addWidget(add_btn)

        right_layout.addWidget(add_card)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(8)
        self.items_table.setHorizontalHeaderLabels(
            ["Kod", "Stok Adı", "Miktar", "Birim", "Birim Fiyat", "KDV", "Toplam", ""]
        )
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setShowGrid(False)
        self.items_table.setAlternatingRowColors(True)

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

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setProperty("class", "form-label")
        return label

    def _on_currency_changed(self, currency_code):
        self.currency_symbol = self.CURRENCY_SYMBOLS.get(currency_code, currency_code)
        self.price_input.setPrefix(f"{self.currency_symbol}")
        for row in range(self.items_table.rowCount()):
            price_item = self.items_table.item(row, 4)
            if price_item:
                price = float(price_item.data(Qt.ItemDataRole.UserRole) or 0)
                price_item.setText(f"{self.currency_symbol}{price:,.2f}")
            total_item = self.items_table.item(row, 6)
            if total_item:
                qty_item = self.items_table.item(row, 2)
                if qty_item:
                    try:
                        qty = float(qty_item.text().replace(",", ""))
                        total_item.setText(f"{self.currency_symbol}{qty * price:,.2f}")
                    except ValueError:
                        pass
        self._update_totals()

    def _add_item_row(self):
        item_data = self.item_combo.currentData()
        if not item_data:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir stok kartı seçin!")
            return
        qty, price, tax = (
            self.qty_input.value(),
            self.price_input.value(),
            self.tax_input.value(),
        )
        if qty <= 0:
            QMessageBox.warning(self, "Uyarı", "Miktar sıfırdan büyük olmalıdır!")
            return
        self._insert_item_row(item_data, qty, price, tax)
        self.item_combo.setCurrentIndex(0)
        self.qty_input.setValue(1)
        self.price_input.setValue(0)
        self.tax_input.setValue(18)

    def _insert_item_row(
        self, item: dict, quantity: float, unit_price: float, tax_rate: float
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

        qty_item = QTableWidgetItem(f"{quantity:,.4f}")
        qty_item.setFlags(qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        qty_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.items_table.setItem(row, 2, qty_item)

        unit_item = QTableWidgetItem(item.get("unit_name", ""))
        unit_item.setData(Qt.ItemDataRole.UserRole, item.get("unit_id"))
        unit_item.setFlags(unit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        unit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.items_table.setItem(row, 3, unit_item)

        p_item = QTableWidgetItem(f"{self.currency_symbol}{unit_price:,.2f}")
        p_item.setData(Qt.ItemDataRole.UserRole, unit_price)
        p_item.setFlags(p_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        p_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.items_table.setItem(row, 4, p_item)

        tax_item = QTableWidgetItem(f"%{tax_rate:.0f}")
        tax_item.setData(Qt.ItemDataRole.UserRole, tax_rate)
        tax_item.setFlags(tax_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        tax_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.items_table.setItem(row, 5, tax_item)

        tot_item = QTableWidgetItem(
            f"{self.currency_symbol}{quantity * unit_price:,.2f}"
        )
        tot_item.setFlags(tot_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        tot_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.items_table.setItem(row, 6, tot_item)

        del_btn = QPushButton()
        del_btn.setIcon(qta.icon(ICONS.DELETE, color="#ef4444"))
        del_btn.setFixedSize(32, 32)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
        del_btn.clicked.connect(lambda: self._remove_row(row))
        self.items_table.setCellWidget(row, 7, del_btn)
        self.items_table.setRowHeight(row, 44)
        self._update_totals()

    def _remove_row(self, row: int):
        self.items_table.removeRow(row)
        for r in range(self.items_table.rowCount()):
            btn = self.items_table.cellWidget(r, 7)
            if btn:
                btn.clicked.disconnect()
                btn.clicked.connect(lambda checked, r_idx=r: self._remove_row(r_idx))
        self._update_totals()

    def _update_totals(self):
        sub, tax = Decimal("0"), Decimal("0")
        for row in range(self.items_table.rowCount()):
            qi, pi, ti = (
                self.items_table.item(row, 2),
                self.items_table.item(row, 4),
                self.items_table.item(row, 5),
            )
            if qi and pi and ti:
                try:
                    q = Decimal(qi.text().replace(",", ""))
                    p = Decimal(str(pi.data(Qt.ItemDataRole.UserRole) or 0))
                    t = Decimal(str(ti.data(Qt.ItemDataRole.UserRole) or 0))
                    sub += q * p
                    tax += q * p * t / 100
                except:
                    pass
        self.subtotal_label.setText(f"{self.currency_symbol}{float(sub):,.2f}")
        self.tax_total_label.setText(f"{self.currency_symbol}{float(tax):,.2f}")
        self.total_label.setText(f"{self.currency_symbol}{float(sub + tax):,.2f}")

    def load_data(self):
        if not self.invoice_data:
            return
        self.invoice_no_input.setText(self.invoice_data.get("invoice_no", ""))
        for d_key, d_input in [
            ("invoice_date", self.invoice_date_input),
            ("due_date", self.due_date_input),
            ("supplier_invoice_date", self.supplier_invoice_date_input),
        ]:
            val = self.invoice_data.get(d_key)
            if val and isinstance(val, date):
                d_input.setDate(QDate(val.year, val.month, val.day))
        curr = self.invoice_data.get("currency", "TRY")
        self.currency_combo.setCurrentText(curr)
        self._on_currency_changed(curr)
        sid = self.invoice_data.get("supplier_id")
        for i in range(self.supplier_combo.count()):
            if self.supplier_combo.itemData(i) == sid:
                self.supplier_combo.setCurrentIndex(i)
                break
        self.supplier_invoice_no_input.setText(
            self.invoice_data.get("supplier_invoice_no", "") or ""
        )
        self.notes_input.setPlainText(self.invoice_data.get("notes", "") or "")
        self.items_table.setRowCount(0)
        for item_data in self.invoice_data.get("items", []):
            iid = item_data.get("item_id")
            info = next(
                (i for i in self.items if i.get("id") == iid),
                {"id": iid, "code": "???", "name": "Bilinmeyen Stok", "unit_name": "-"},
            )
            self._insert_item_row(
                info,
                float(item_data.get("quantity", 0)),
                float(item_data.get("unit_price", 0) or 0),
                float(item_data.get("tax_rate", 18) or 18),
            )

    def _on_save(self):
        sid = self.supplier_combo.currentData()
        if not sid or self.items_table.rowCount() == 0:
            QMessageBox.warning(
                self, "Uyarı", "Lütfen tedarikçi seçin ve en az bir kalem ekleyin!"
            )
            return
        items = []
        for r in range(self.items_table.rowCount()):
            iid = self.items_table.item(r, 0).data(Qt.ItemDataRole.UserRole)
            try:
                q = float(self.items_table.item(r, 2).text().replace(",", ""))
            except:
                q = 0
            uid = self.items_table.item(r, 3).data(Qt.ItemDataRole.UserRole)
            p = self.items_table.item(r, 4).data(Qt.ItemDataRole.UserRole)
            t = self.items_table.item(r, 5).data(Qt.ItemDataRole.UserRole)
            if iid and q > 0:
                items.append(
                    {
                        "item_id": iid,
                        "quantity": Decimal(str(q)),
                        "unit_id": uid,
                        "unit_price": Decimal(str(p)),
                        "tax_rate": Decimal(str(t)),
                    }
                )
        idat, ddat, sdat = (
            self.invoice_date_input.date(),
            self.due_date_input.date(),
            self.supplier_invoice_date_input.date(),
        )
        data = {
            "invoice_date": date(idat.year(), idat.month(), idat.day()),
            "due_date": date(ddat.year(), ddat.month(), ddat.day()),
            "supplier_id": sid,
            "supplier_invoice_no": self.supplier_invoice_no_input.text().strip()
            or None,
            "supplier_invoice_date": date(sdat.year(), sdat.month(), sdat.day()),
            "currency": self.currency_combo.currentText(),
            "exchange_rate": 1.0,
            "notes": self.notes_input.toPlainText().strip() or None,
            "items": items,
        }
        if self.is_edit_mode and self.invoice_data:
            data["id"] = self.invoice_data.get("id")
        self.saved.emit(data)
