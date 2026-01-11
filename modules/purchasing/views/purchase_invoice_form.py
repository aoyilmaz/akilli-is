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
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate

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
            "Fatura Düzenle" if self.is_edit_mode else "Yeni Satınalma Faturası"
        )
        title = QLabel(f"📄 {title_text}")
        header_layout.addWidget(title)
        header_layout.addStretch()

        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet(
            """
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
        """
        )
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
        general_frame = self._create_section("📝 Fatura Bilgileri")
        general_layout = QGridLayout()
        general_layout.setColumnMinimumWidth(0, 160)
        general_layout.setSpacing(12)

        row = 0

        # Fatura No
        general_layout.addWidget(self._create_label("Fatura No"), row, 0)
        self.invoice_no_input = QLineEdit()
        self.invoice_no_input.setPlaceholderText("Otomatik oluşturulacak")
        self.invoice_no_input.setReadOnly(True)
        general_layout.addWidget(self.invoice_no_input, row, 1)
        row += 1

        # Fatura Tarihi
        general_layout.addWidget(self._create_label("Fatura Tarihi *"), row, 0)
        self.invoice_date_input = QDateEdit()
        self.invoice_date_input.setDate(QDate.currentDate())
        self.invoice_date_input.setCalendarPopup(True)
        general_layout.addWidget(self.invoice_date_input, row, 1)
        row += 1

        # Vade Tarihi
        general_layout.addWidget(self._create_label("Vade Tarihi"), row, 0)
        self.due_date_input = QDateEdit()
        self.due_date_input.setDate(QDate.currentDate().addDays(30))
        self.due_date_input.setCalendarPopup(True)
        general_layout.addWidget(self.due_date_input, row, 1)
        row += 1

        # Tedarikçi
        general_layout.addWidget(self._create_label("Tedarikçi *"), row, 0)
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("- Tedarikçi Seçin -", None)
        for s in self.suppliers:
            self.supplier_combo.addItem(
                f"{s.get('code', '')} - {s.get('name', '')}", s.get("id")
            )
        general_layout.addWidget(self.supplier_combo, row, 1)
        row += 1

        # Tedarikçi Fatura No
        general_layout.addWidget(self._create_label("Tedarikçi Fatura No"), row, 0)
        self.supplier_invoice_no_input = QLineEdit()
        self.supplier_invoice_no_input.setPlaceholderText(
            "Tedarikçiden gelen fatura numarası"
        )
        general_layout.addWidget(self.supplier_invoice_no_input, row, 1)
        row += 1

        # Tedarikçi Fatura Tarihi
        general_layout.addWidget(self._create_label("Tedarikçi Fatura Tarihi"), row, 0)
        self.supplier_invoice_date_input = QDateEdit()
        self.supplier_invoice_date_input.setDate(QDate.currentDate())
        self.supplier_invoice_date_input.setCalendarPopup(True)
        general_layout.addWidget(self.supplier_invoice_date_input, row, 1)
        row += 1

        # Notlar
        general_layout.addWidget(self._create_label("Notlar"), row, 0)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Ek açıklamalar...")
        general_layout.addWidget(self.notes_input, row, 1)

        general_frame.layout().addLayout(general_layout)
        scroll_layout.addWidget(general_frame)

        # === KALEMLER ===
        items_frame = self._create_section("📦 Fatura Kalemleri")
        items_layout = QVBoxLayout()

        # Kalem ekleme
        add_row = QHBoxLayout()

        self.item_combo = QComboBox()
        self.item_combo.addItem("- Stok Kartı Seçin -", None)
        for item in self.items:
            self.item_combo.addItem(
                f"{item.get('code', '')} - {item.get('name', '')}", item
            )
        self.item_combo.setMinimumWidth(300)
        add_row.addWidget(self.item_combo)

        self.qty_input = QDoubleSpinBox()
        self.qty_input.setRange(0.0001, 999999999)
        self.qty_input.setDecimals(4)
        self.qty_input.setValue(1)
        self.qty_input.setPrefix("Miktar: ")
        self.qty_input.setMinimumWidth(130)
        add_row.addWidget(self.qty_input)

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 999999999)
        self.price_input.setDecimals(4)
        self.price_input.setValue(0)
        self.price_input.setPrefix("Fiyat: ₺")
        self.price_input.setMinimumWidth(140)
        add_row.addWidget(self.price_input)

        self.tax_input = QDoubleSpinBox()
        self.tax_input.setRange(0, 100)
        self.tax_input.setDecimals(2)
        self.tax_input.setValue(18)
        self.tax_input.setPrefix("KDV: %")
        self.tax_input.setMinimumWidth(100)
        add_row.addWidget(self.tax_input)

        add_item_btn = QPushButton("➕ Ekle")
        add_item_btn.clicked.connect(self._add_item_row)
        add_row.addWidget(add_item_btn)

        add_row.addStretch()
        items_layout.addLayout(add_row)

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
                "Toplam",
                "İşlem",
            ]
        )
        self.items_table.setMinimumHeight(200)
        self.items_table.verticalHeader().setVisible(False)

        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.items_table.setColumnWidth(0, 100)
        self.items_table.setColumnWidth(2, 80)
        self.items_table.setColumnWidth(3, 70)
        self.items_table.setColumnWidth(4, 100)
        self.items_table.setColumnWidth(5, 70)
        self.items_table.setColumnWidth(6, 100)
        self.items_table.setColumnWidth(7, 50)

        items_layout.addWidget(self.items_table)

        # Toplamlar
        totals_row = QHBoxLayout()
        totals_row.addStretch()

        self.subtotal_label = QLabel("Ara Toplam: ₺0.00")
        totals_row.addWidget(self.subtotal_label)

        self.tax_total_label = QLabel("KDV: ₺0.00")
        totals_row.addWidget(self.tax_total_label)

        self.total_label = QLabel("Genel Toplam: ₺0.00")
        totals_row.addWidget(self.total_label)

        items_layout.addLayout(totals_row)

        items_frame.layout().addLayout(items_layout)
        scroll_layout.addWidget(items_frame)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def _create_section(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            """
            QFrame {
                background-color: rgba(30, 41, 59, 0.5);
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """
        )

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title_label = QLabel(title)
        layout.addWidget(title_label)

        return frame

    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return label

    def _add_item_row(self):
        """Kalem ekle"""
        item_data = self.item_combo.currentData()
        if not item_data:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir stok kartı seçin!")
            return

        qty = self.qty_input.value()
        price = self.price_input.value()
        tax_rate = self.tax_input.value()

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
        qty_item = QTableWidgetItem(f"{quantity:.4f}")
        qty_item.setFlags(qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.items_table.setItem(row, 2, qty_item)

        # Birim
        unit_name = item.get("unit_name", "")
        unit_item = QTableWidgetItem(unit_name)
        unit_item.setData(Qt.ItemDataRole.UserRole, item.get("unit_id"))
        unit_item.setFlags(unit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.items_table.setItem(row, 3, unit_item)

        # Birim Fiyat
        price_item = QTableWidgetItem(f"₺{unit_price:,.2f}")
        price_item.setData(Qt.ItemDataRole.UserRole, unit_price)
        price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.items_table.setItem(row, 4, price_item)

        # KDV
        tax_item = QTableWidgetItem(f"%{tax_rate:.0f}")
        tax_item.setData(Qt.ItemDataRole.UserRole, tax_rate)
        tax_item.setFlags(tax_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.items_table.setItem(row, 5, tax_item)

        # Toplam
        line_total = quantity * unit_price
        total_item = QTableWidgetItem(f"₺{line_total:,.2f}")
        total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.items_table.setItem(row, 6, total_item)

        # Sil butonu
        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(32, 32)
        del_btn.clicked.connect(lambda: self._remove_row(row))
        self.items_table.setCellWidget(row, 7, del_btn)

        self.items_table.setRowHeight(row, 50)
        self._update_totals()

    def _remove_row(self, row: int):
        """Satır sil ve toplamları güncelle"""
        self.items_table.removeRow(row)
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
                qty = Decimal(qty_item.text())
                price = Decimal(str(price_item.data(Qt.ItemDataRole.UserRole)))
                tax_rate = Decimal(str(tax_item.data(Qt.ItemDataRole.UserRole)))

                line_subtotal = qty * price
                line_tax = line_subtotal * tax_rate / 100

                subtotal += line_subtotal
                tax_total += line_tax

        total = subtotal + tax_total

        self.subtotal_label.setText(f"Ara Toplam: ₺{float(subtotal):,.2f}")
        self.tax_total_label.setText(f"KDV: ₺{float(tax_total):,.2f}")
        self.total_label.setText(f"Genel Toplam: ₺{float(total):,.2f}")

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
        items_data = self.invoice_data.get("items", [])
        for item_data in items_data:
            item_id = item_data.get("item_id")
            item_info = next((i for i in self.items if i.get("id") == item_id), None)
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
            quantity = float(qty_item.text()) if qty_item else 0

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
            "notes": self.notes_input.toPlainText().strip() or None,
            "items": items_data,
        }

        if self.is_edit_mode and self.invoice_data:
            data["id"] = self.invoice_data.get("id")

        self.saved.emit(data)
