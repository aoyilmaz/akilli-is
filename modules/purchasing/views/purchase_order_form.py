"""
Akıllı İş - Satın Alma Sipariş Formu
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QFrame, QMessageBox, QGridLayout, QScrollArea, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QAbstractItemView
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
        self.setStyleSheet("QDialog { background-color: #1e293b; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara...")
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
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Kod", "Ad", "Birim"])
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
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self._on_select)
        
        self._load_items()
        layout.addWidget(self.table)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #f8fafc;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        select_btn = QPushButton("Seç")
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
            }
        """)
        select_btn.clicked.connect(self._on_select)
        btn_layout.addWidget(select_btn)
        
        layout.addLayout(btn_layout)
        
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
            match = any(
                text in (self.table.item(row, col).text().lower() if self.table.item(row, col) else "")
                for col in range(2)
            )
            self.table.setRowHidden(row, not match)
            
    def _on_select(self):
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
    
    def __init__(self, order_data: Optional[dict] = None,
                 suppliers: list = None, warehouses: list = None,
                 items: list = None, units: list = None,
                 parent=None):
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
            QPushButton:hover { background-color: #334155; color: #f8fafc; }
        """)
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)
        
        title_text = "Sipariş Düzenle" if self.is_edit_mode else "Yeni Satın Alma Siparişi"
        title = QLabel(f"📦 {title_text}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc; margin-left: 16px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #a855f7);
                border: none;
                color: white;
                font-weight: 600;
                padding: 12px 24px;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #9333ea);
            }
        """)
        save_btn.clicked.connect(self._on_save)
        header_layout.addWidget(save_btn)
        
        layout.addLayout(header_layout)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        
        # === GENEL BİLGİLER ===
        general_frame = self._create_section("📝 Sipariş Bilgileri")
        general_layout = QGridLayout()
        general_layout.setColumnMinimumWidth(0, 140)
        general_layout.setSpacing(12)
        
        row = 0
        
        # Sipariş No
        general_layout.addWidget(self._create_label("Sipariş No"), row, 0)
        self.order_no_input = QLineEdit()
        self.order_no_input.setPlaceholderText("Otomatik")
        self.order_no_input.setReadOnly(True)
        self._style_input(self.order_no_input)
        general_layout.addWidget(self.order_no_input, row, 1)
        
        # Sipariş Tarihi
        general_layout.addWidget(self._create_label("Tarih *"), row, 2)
        self.order_date_input = QDateEdit()
        self.order_date_input.setDate(QDate.currentDate())
        self.order_date_input.setCalendarPopup(True)
        self._style_date(self.order_date_input)
        general_layout.addWidget(self.order_date_input, row, 3)
        row += 1
        
        # Tedarikçi
        general_layout.addWidget(self._create_label("Tedarikçi *"), row, 0)
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("- Tedarikçi Seçin -", None)
        for s in self.suppliers:
            self.supplier_combo.addItem(f"{s.get('code', '')} - {s.get('name', '')}", s)
        self.supplier_combo.currentIndexChanged.connect(self._on_supplier_changed)
        self._style_combo(self.supplier_combo)
        general_layout.addWidget(self.supplier_combo, row, 1)
        
        # Teslim Tarihi
        general_layout.addWidget(self._create_label("Teslim Tarihi"), row, 2)
        self.delivery_date_input = QDateEdit()
        self.delivery_date_input.setDate(QDate.currentDate().addDays(7))
        self.delivery_date_input.setCalendarPopup(True)
        self._style_date(self.delivery_date_input)
        general_layout.addWidget(self.delivery_date_input, row, 3)
        row += 1
        
        # Depo
        general_layout.addWidget(self._create_label("Teslimat Deposu"), row, 0)
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.addItem("- Depo Seçin -", None)
        for w in self.warehouses:
            self.warehouse_combo.addItem(w.get("name", ""), w.get("id"))
        self._style_combo(self.warehouse_combo)
        general_layout.addWidget(self.warehouse_combo, row, 1)
        
        # Ödeme Vadesi
        general_layout.addWidget(self._create_label("Ödeme Vadesi"), row, 2)
        vade_layout = QHBoxLayout()
        self.payment_term_input = QSpinBox()
        self.payment_term_input.setRange(0, 365)
        self.payment_term_input.setValue(30)
        self.payment_term_input.setSuffix(" gün")
        self._style_spin(self.payment_term_input)
        vade_layout.addWidget(self.payment_term_input)
        vade_layout.addStretch()
        general_layout.addLayout(vade_layout, row, 3)
        row += 1
        
        # Para Birimi
        general_layout.addWidget(self._create_label("Para Birimi"), row, 0)
        self.currency_combo = QComboBox()
        self.currency_combo.addItem("🇹🇷 TRY", "TRY")
        self.currency_combo.addItem("🇺🇸 USD", "USD")
        self.currency_combo.addItem("🇪🇺 EUR", "EUR")
        self.currency_combo.addItem("🇬🇧 GBP", "GBP")
        self._style_combo(self.currency_combo)
        general_layout.addWidget(self.currency_combo, row, 1)
        
        # Kur
        general_layout.addWidget(self._create_label("Döviz Kuru"), row, 2)
        self.exchange_rate_input = QDoubleSpinBox()
        self.exchange_rate_input.setRange(0.0001, 9999)
        self.exchange_rate_input.setDecimals(4)
        self.exchange_rate_input.setValue(1)
        self._style_spin(self.exchange_rate_input)
        general_layout.addWidget(self.exchange_rate_input, row, 3)
        row += 1
        
        # Notlar
        general_layout.addWidget(self._create_label("Notlar"), row, 0)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self._style_textedit(self.notes_input)
        general_layout.addWidget(self.notes_input, row, 1, 1, 3)
        
        general_frame.layout().addLayout(general_layout)
        scroll_layout.addWidget(general_frame)
        
        # === KALEMLER ===
        items_frame = self._create_section("📦 Sipariş Kalemleri")
        items_layout = QVBoxLayout()
        
        # Kalem ekleme butonu
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
        items_layout.addWidget(add_item_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # Tablo
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(8)
        self.items_table.setHorizontalHeaderLabels([
            "Stok Kodu", "Stok Adı", "Miktar", "Birim",
            "Birim Fiyat", "KDV %", "Satır Toplamı", "İşlem"
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
        self.items_table.setColumnWidth(2, 90)
        self.items_table.setColumnWidth(3, 70)
        self.items_table.setColumnWidth(4, 100)
        self.items_table.setColumnWidth(5, 70)
        self.items_table.setColumnWidth(6, 110)
        self.items_table.setColumnWidth(7, 50)
        
        items_layout.addWidget(self.items_table)
        
        # Toplamlar
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()
        
        totals_frame = QFrame()
        totals_frame.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        totals_inner = QGridLayout(totals_frame)
        totals_inner.setSpacing(8)
        
        totals_inner.addWidget(QLabel("Ara Toplam:"), 0, 0)
        self.subtotal_label = QLabel("₺0.00")
        self.subtotal_label.setStyleSheet("color: #f8fafc; font-weight: bold;")
        totals_inner.addWidget(self.subtotal_label, 0, 1)
        
        totals_inner.addWidget(QLabel("KDV:"), 1, 0)
        self.tax_label = QLabel("₺0.00")
        self.tax_label.setStyleSheet("color: #f8fafc; font-weight: bold;")
        totals_inner.addWidget(self.tax_label, 1, 1)
        
        totals_inner.addWidget(QLabel("Genel Toplam:"), 2, 0)
        self.total_label = QLabel("₺0.00")
        self.total_label.setStyleSheet("color: #10b981; font-size: 18px; font-weight: bold;")
        totals_inner.addWidget(self.total_label, 2, 1)
        
        for label in totals_frame.findChildren(QLabel):
            label.setStyleSheet(label.styleSheet() + "background: transparent;")
        
        totals_layout.addWidget(totals_frame)
        items_layout.addLayout(totals_layout)
        
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
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc; background: transparent; border: none;")
        layout.addWidget(title_label)
        
        return frame
        
    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("color: #e2e8f0; background: transparent; font-size: 14px; border: none;")
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return label
        
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
                    
    def _add_item_row(self):
        """Kalem ekle"""
        if not self.items:
            QMessageBox.warning(self, "Uyarı", "Stok kartı bulunamadı!")
            return
            
        dialog = ItemSelectorDialog(self.items, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_item:
            self._insert_item_row(dialog.selected_item)
            
    def _insert_item_row(self, item: dict, quantity: float = 1, 
                        unit_price: float = 0, tax_rate: float = 20):
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
        qty_spin.setStyleSheet(self._spin_style_small())
        qty_spin.valueChanged.connect(lambda: self._calculate_line_total(row))
        self.items_table.setCellWidget(row, 2, qty_spin)
        
        # Birim
        unit_item = QTableWidgetItem(item.get("unit_name", ""))
        unit_item.setData(Qt.ItemDataRole.UserRole, item.get("unit_id"))
        unit_item.setFlags(unit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.items_table.setItem(row, 3, unit_item)
        
        # Birim Fiyat
        price_spin = QDoubleSpinBox()
        price_spin.setRange(0, 999999999)
        price_spin.setDecimals(4)
        price_spin.setValue(unit_price)
        price_spin.setStyleSheet(self._spin_style_small())
        price_spin.valueChanged.connect(lambda: self._calculate_line_total(row))
        self.items_table.setCellWidget(row, 4, price_spin)
        
        # KDV %
        tax_spin = QDoubleSpinBox()
        tax_spin.setRange(0, 100)
        tax_spin.setDecimals(2)
        tax_spin.setValue(tax_rate)
        tax_spin.setSuffix("%")
        tax_spin.setStyleSheet(self._spin_style_small())
        tax_spin.valueChanged.connect(lambda: self._calculate_line_total(row))
        self.items_table.setCellWidget(row, 5, tax_spin)
        
        # Satır Toplamı
        total_item = QTableWidgetItem("₺0.00")
        total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.items_table.setItem(row, 6, total_item)
        
        # Sil butonu
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
        self._calculate_line_total(row)
        
    def _remove_item_row(self, row: int):
        self.items_table.removeRow(row)
        self._calculate_totals()
        
    def _calculate_line_total(self, row: int):
        """Satır toplamını hesapla"""
        qty_widget = self.items_table.cellWidget(row, 2)
        price_widget = self.items_table.cellWidget(row, 4)
        
        if qty_widget and price_widget:
            qty = qty_widget.value()
            price = price_widget.value()
            line_total = qty * price
            
            total_item = self.items_table.item(row, 6)
            if total_item:
                total_item.setText(f"₺{line_total:,.2f}")
        
        self._calculate_totals()
        
    def _calculate_totals(self):
        """Genel toplamları hesapla"""
        subtotal = 0
        tax_total = 0
        
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
        
        self.subtotal_label.setText(f"₺{subtotal:,.2f}")
        self.tax_label.setText(f"₺{tax_total:,.2f}")
        self.total_label.setText(f"₺{total:,.2f}")
        
    def load_data(self):
        """Düzenleme modunda verileri yükle"""
        if not self.order_data:
            return
        
        self.order_no_input.setText(self.order_data.get("order_no", ""))
        
        order_date = self.order_data.get("order_date")
        if order_date and isinstance(order_date, date):
            self.order_date_input.setDate(QDate(order_date.year, order_date.month, order_date.day))
        
        # Tedarikçi
        supplier_id = self.order_data.get("supplier_id")
        for i in range(self.supplier_combo.count()):
            data = self.supplier_combo.itemData(i)
            if data and data.get("id") == supplier_id:
                self.supplier_combo.setCurrentIndex(i)
                break
        
        delivery_date = self.order_data.get("delivery_date")
        if delivery_date and isinstance(delivery_date, date):
            self.delivery_date_input.setDate(QDate(delivery_date.year, delivery_date.month, delivery_date.day))
        
        # Depo
        warehouse_id = self.order_data.get("delivery_warehouse_id")
        for i in range(self.warehouse_combo.count()):
            if self.warehouse_combo.itemData(i) == warehouse_id:
                self.warehouse_combo.setCurrentIndex(i)
                break
        
        self.payment_term_input.setValue(self.order_data.get("payment_term_days", 30) or 30)
        
        currency = self.order_data.get("currency", "TRY")
        for i in range(self.currency_combo.count()):
            if self.currency_combo.itemData(i) == currency:
                self.currency_combo.setCurrentIndex(i)
                break
        
        self.exchange_rate_input.setValue(float(self.order_data.get("exchange_rate", 1) or 1))
        self.notes_input.setPlainText(self.order_data.get("notes", "") or "")
        
        # Kalemleri yükle
        for item_data in self.order_data.get("items", []):
            item_id = item_data.get("item_id")
            item_info = next((i for i in self.items if i.get("id") == item_id), None)
            if item_info:
                self._insert_item_row(
                    item_info,
                    float(item_data.get("quantity", 1)),
                    float(item_data.get("unit_price", 0) or 0),
                    float(item_data.get("tax_rate", 20) or 20)
                )
        
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
            
            unit_item = self.items_table.item(row, 3)
            unit_id = unit_item.data(Qt.ItemDataRole.UserRole) if unit_item else None
            
            qty_widget = self.items_table.cellWidget(row, 2)
            quantity = qty_widget.value() if qty_widget else 0
            
            price_widget = self.items_table.cellWidget(row, 4)
            unit_price = price_widget.value() if price_widget else 0
            
            tax_widget = self.items_table.cellWidget(row, 5)
            tax_rate = tax_widget.value() if tax_widget else 20
            
            if item_id and quantity > 0:
                items_data.append({
                    "item_id": item_id,
                    "quantity": Decimal(str(quantity)),
                    "unit_id": unit_id,
                    "unit_price": Decimal(str(unit_price)),
                    "tax_rate": Decimal(str(tax_rate)),
                })
        
        order_qdate = self.order_date_input.date()
        delivery_qdate = self.delivery_date_input.date()
        
        data = {
            "order_date": date(order_qdate.year(), order_qdate.month(), order_qdate.day()),
            "supplier_id": supplier.get("id"),
            "delivery_date": date(delivery_qdate.year(), delivery_qdate.month(), delivery_qdate.day()),
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
        
    # Style helpers
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
            QLineEdit:read-only { background-color: #1e293b; color: #94a3b8; }
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
        
    def _style_spin(self, s):
        s.setMinimumHeight(42)
        s.setStyleSheet("""
            QSpinBox, QDoubleSpinBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 12px;
                color: #f8fafc;
                font-size: 14px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus { border-color: #6366f1; }
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
        
    def _spin_style_small(self):
        return """
            QDoubleSpinBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 4px 8px;
                color: #f8fafc;
                font-size: 12px;
            }
        """
