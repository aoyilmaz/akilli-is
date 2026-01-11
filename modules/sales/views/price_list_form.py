"""
Akilli Is - Fiyat Listesi Form Sayfasi
"""

from datetime import date
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QDateEdit, QCheckBox,
    QFrame, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QSpinBox, QDoubleSpinBox,
    QDialog, QDialogButtonBox, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate

class ItemSelectDialog(QDialog):
    """Stok karti secim dialogu"""

    def __init__(self, items: list, parent=None):
        super().__init__(parent)
        self.items = items
        self.selected_item = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Stok Karti Sec")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara... (kod, ad)")
        self.search_input.textChanged.connect(self._on_search)
        layout.addWidget(self.search_input)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Kod", "Stok Adi", "Birim", "Satis Fiyati"
        ])
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
        self.table.doubleClicked.connect(self._on_select)
        layout.addWidget(self.table)

        # Butonlar
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self._load_items()

    def _load_items(self):
        self.table.setRowCount(0)
        for row, item in enumerate(self.items):
            self.table.insertRow(row)

            code_item = QTableWidgetItem(item.get("code", ""))
            code_item.setData(Qt.ItemDataRole.UserRole, item)
            self.table.setItem(row, 0, code_item)

            self.table.setItem(
                row, 1, QTableWidgetItem(item.get("name", ""))
            )
            self.table.setItem(
                row, 2, QTableWidgetItem(item.get("unit_name", ""))
            )

            price = item.get("sale_price", 0) or 0
            self.table.setItem(
                row, 3, QTableWidgetItem(f"{float(price):,.2f}")
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

    def _on_select(self, index):
        self._on_accept()

    def _on_accept(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                self.selected_item = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def get_selected(self):
        return self.selected_item

class PriceListFormPage(QWidget):
    """Fiyat listesi form sayfasi"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(
        self,
        price_list_data: dict = None,
        items: list = None,
        parent=None
    ):
        super().__init__(parent)
        self.price_list_data = price_list_data or {}
        self.items = items or []
        self.list_items = []
        self.is_edit = bool(price_list_data and price_list_data.get("id"))
        self.setup_ui()
        if self.is_edit:
            self._load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title_text = (
            "Fiyat Listesi Duzenle"
            if self.is_edit else "Yeni Fiyat Listesi"
        )
        title = QLabel(title_text)
        header_layout.addWidget(title)

        header_layout.addStretch()

        cancel_btn = QPushButton("Iptal")
        cancel_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self._save)
        header_layout.addWidget(save_btn)

        layout.addLayout(header_layout)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)

        # Temel bilgiler
        basic_frame = self._create_section("Temel Bilgiler")
        basic_layout = QFormLayout()
        basic_layout.setSpacing(12)

        # Kod
        self.code_input = QLineEdit()
        self.code_input.setStyleSheet(self._input_style())
        basic_layout.addRow("Kod:", self.code_input)

        # Ad
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(self._input_style())
        basic_layout.addRow("Liste Adi:", self.name_input)

        # Aciklama
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setStyleSheet(self._input_style())
        basic_layout.addRow("Aciklama:", self.desc_input)

        # Tur
        self.type_combo = QComboBox()
        self.type_combo.addItem("Satis Fiyat Listesi", "sales")
        self.type_combo.addItem("Alis Fiyat Listesi", "purchase")
        self.type_combo.setStyleSheet(self._input_style())
        basic_layout.addRow("Liste Turu:", self.type_combo)

        # Para birimi
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["TRY", "USD", "EUR", "GBP"])
        self.currency_combo.setStyleSheet(self._input_style())
        basic_layout.addRow("Para Birimi:", self.currency_combo)

        # Oncelik
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 100)
        self.priority_spin.setValue(10)
        self.priority_spin.setStyleSheet(self._input_style())
        basic_layout.addRow("Oncelik:", self.priority_spin)

        # Varsayilan
        self.default_check = QCheckBox("Varsayilan liste olarak ayarla")
        basic_layout.addRow("", self.default_check)

        basic_frame.layout().addLayout(basic_layout)
        content_layout.addWidget(basic_frame)

        # Gecerlilik
        validity_frame = self._create_section("Gecerlilik Suresi")
        validity_layout = QHBoxLayout()

        validity_layout.addWidget(QLabel("Baslangic:"))
        self.valid_from = QDateEdit()
        self.valid_from.setCalendarPopup(True)
        self.valid_from.setStyleSheet(self._input_style())
        self.valid_from.setSpecialValueText("Belirtilmemis")
        validity_layout.addWidget(self.valid_from)

        validity_layout.addWidget(QLabel("Bitis:"))
        self.valid_until = QDateEdit()
        self.valid_until.setCalendarPopup(True)
        self.valid_until.setStyleSheet(self._input_style())
        self.valid_until.setSpecialValueText("Belirtilmemis")
        validity_layout.addWidget(self.valid_until)

        validity_layout.addStretch()
        validity_frame.layout().addLayout(validity_layout)
        content_layout.addWidget(validity_frame)

        # Fiyat kalemleri
        items_frame = self._create_section("Fiyat Kalemleri")

        # Kalem ekleme butonu
        item_btn_layout = QHBoxLayout()
        add_item_btn = QPushButton("+ Kalem Ekle")
        add_item_btn.clicked.connect(self._add_item)
        item_btn_layout.addWidget(add_item_btn)
        item_btn_layout.addStretch()
        items_frame.layout().addLayout(item_btn_layout)

        # Kalemler tablosu
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "Stok Kodu", "Stok Adi", "Birim Fiyat",
            "Min. Miktar", "Iskonto %", "Sil"
        ])
        self.items_table.setMinimumHeight(200)
        self.items_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.items_table.setColumnWidth(0, 120)
        self.items_table.setColumnWidth(2, 120)
        self.items_table.setColumnWidth(3, 100)
        self.items_table.setColumnWidth(4, 80)
        self.items_table.setColumnWidth(5, 60)
        items_frame.layout().addWidget(self.items_table)

        content_layout.addWidget(items_frame)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_section(self, title: str) -> QFrame:
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title_label = QLabel(title)
        layout.addWidget(title_label)

        return frame

    def _input_style(self) -> str:
        return """
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox,
            QDoubleSpinBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                color: #f8fafc;
                min-width: 200px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
            QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #6366f1;
            }
        """

    def _load_data(self):
        """Mevcut veriyi yukle"""
        data = self.price_list_data

        self.code_input.setText(data.get("code", ""))
        self.name_input.setText(data.get("name", ""))
        self.desc_input.setPlainText(data.get("description", "") or "")

        # Tur
        list_type = data.get("list_type", "sales")
        idx = self.type_combo.findData(list_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)

        # Para birimi
        currency = data.get("currency", "TRY")
        idx = self.currency_combo.findText(currency)
        if idx >= 0:
            self.currency_combo.setCurrentIndex(idx)

        # Oncelik
        self.priority_spin.setValue(data.get("priority", 10) or 10)

        # Varsayilan
        self.default_check.setChecked(data.get("is_default", False))

        # Gecerlilik
        if data.get("valid_from"):
            self.valid_from.setDate(
                QDate.fromString(str(data["valid_from"]), "yyyy-MM-dd")
            )
        if data.get("valid_until"):
            self.valid_until.setDate(
                QDate.fromString(str(data["valid_until"]), "yyyy-MM-dd")
            )

        # Kalemler
        items = data.get("items", [])
        for item in items:
            self._add_item_row(item)

    def _add_item(self):
        """Yeni kalem ekle"""
        dialog = ItemSelectDialog(self.items, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected()
            if selected:
                item_data = {
                    "item_id": selected.get("id"),
                    "item_code": selected.get("code"),
                    "item_name": selected.get("name"),
                    "unit_price": selected.get("sale_price", 0) or 0,
                    "min_quantity": 0,
                    "discount_rate": 0,
                }
                self._add_item_row(item_data)

    def _add_item_row(self, item_data: dict):
        """Tabloya kalem satiri ekle"""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        # Stok kodu
        code_item = QTableWidgetItem(item_data.get("item_code", ""))
        code_item.setData(Qt.ItemDataRole.UserRole, item_data.get("item_id"))
        code_item.setFlags(
            code_item.flags() & ~Qt.ItemFlag.ItemIsEditable
        )
        self.items_table.setItem(row, 0, code_item)

        # Stok adi
        name_item = QTableWidgetItem(item_data.get("item_name", ""))
        name_item.setFlags(
            name_item.flags() & ~Qt.ItemFlag.ItemIsEditable
        )
        self.items_table.setItem(row, 1, name_item)

        # Birim fiyat
        price_spin = QDoubleSpinBox()
        price_spin.setRange(0, 999999999)
        price_spin.setDecimals(4)
        price_spin.setValue(float(item_data.get("unit_price", 0) or 0))
        self.items_table.setCellWidget(row, 2, price_spin)

        # Min miktar
        min_spin = QDoubleSpinBox()
        min_spin.setRange(0, 999999999)
        min_spin.setDecimals(2)
        min_spin.setValue(float(item_data.get("min_quantity", 0) or 0))
        self.items_table.setCellWidget(row, 3, min_spin)

        # Iskonto
        disc_spin = QDoubleSpinBox()
        disc_spin.setRange(0, 100)
        disc_spin.setDecimals(2)
        disc_spin.setValue(float(item_data.get("discount_rate", 0) or 0))
        self.items_table.setCellWidget(row, 4, disc_spin)

        # Sil butonu
        del_btn = QPushButton("X")
        del_btn.clicked.connect(lambda: self._remove_item_row(row))
        self.items_table.setCellWidget(row, 5, del_btn)

        self.items_table.setRowHeight(row, 40)

    def _remove_item_row(self, row: int):
        """Kalem satirini kaldir"""
        self.items_table.removeRow(row)

    def _save(self):
        """Kaydet"""
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()

        if not code:
            QMessageBox.warning(self, "Uyari", "Kod zorunludur!")
            return
        if not name:
            QMessageBox.warning(self, "Uyari", "Liste adi zorunludur!")
            return

        # Kalemleri topla
        items_data = []
        for row in range(self.items_table.rowCount()):
            code_item = self.items_table.item(row, 0)
            item_id = code_item.data(Qt.ItemDataRole.UserRole)

            price_widget = self.items_table.cellWidget(row, 2)
            min_widget = self.items_table.cellWidget(row, 3)
            disc_widget = self.items_table.cellWidget(row, 4)

            items_data.append({
                "item_id": item_id,
                "unit_price": Decimal(str(price_widget.value())),
                "min_quantity": Decimal(str(min_widget.value())),
                "discount_rate": Decimal(str(disc_widget.value())),
            })

        data = {
            "id": self.price_list_data.get("id") if self.is_edit else None,
            "code": code,
            "name": name,
            "description": self.desc_input.toPlainText().strip() or None,
            "list_type": self.type_combo.currentData(),
            "currency": self.currency_combo.currentText(),
            "priority": self.priority_spin.value(),
            "is_default": self.default_check.isChecked(),
            "valid_from": (
                self.valid_from.date().toPyDate()
                if self.valid_from.date().isValid()
                and self.valid_from.date() != self.valid_from.minimumDate()
                else None
            ),
            "valid_until": (
                self.valid_until.date().toPyDate()
                if self.valid_until.date().isValid()
                and self.valid_until.date() != self.valid_until.minimumDate()
                else None
            ),
            "items": items_data,
        }

        self.saved.emit(data)
