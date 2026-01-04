"""
Akıllı İş - Mal Kabul Form Sayfası
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox,
    QFrame, QMessageBox, QGridLayout, QScrollArea, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate


class GoodsReceiptFormPage(QWidget):
    """Mal kabul formu"""
    
    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()
    
    def __init__(self, receipt_data: Optional[dict] = None,
                 suppliers: list = None, warehouses: list = None,
                 items: list = None, units: list = None,
                 parent=None):
        super().__init__(parent)
        self.receipt_data = receipt_data
        self.is_edit_mode = receipt_data is not None
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
        
        title_text = "Mal Kabul Düzenle" if self.is_edit_mode else "Yeni Mal Kabul"
        title = QLabel(f"📥 {title_text}")
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
        general_frame = self._create_section("📝 Genel Bilgiler")
        general_layout = QGridLayout()
        general_layout.setColumnMinimumWidth(0, 140)
        general_layout.setSpacing(12)
        
        row = 0
        
        # Fiş No
        general_layout.addWidget(self._create_label("Fiş No"), row, 0)
        self.receipt_no_input = QLineEdit()
        self.receipt_no_input.setPlaceholderText("Otomatik oluşturulacak")
        self.receipt_no_input.setReadOnly(True)
        self._style_input(self.receipt_no_input)
        general_layout.addWidget(self.receipt_no_input, row, 1)
        row += 1
        
        # Tarih
        general_layout.addWidget(self._create_label("Tarih *"), row, 0)
        self.receipt_date_input = QDateEdit()
        self.receipt_date_input.setDate(QDate.currentDate())
        self.receipt_date_input.setCalendarPopup(True)
        self._style_date(self.receipt_date_input)
        general_layout.addWidget(self.receipt_date_input, row, 1)
        row += 1
        
        # Tedarikçi
        general_layout.addWidget(self._create_label("Tedarikçi *"), row, 0)
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("- Tedarikçi Seçin -", None)
        for s in self.suppliers:
            self.supplier_combo.addItem(f"{s.get('code', '')} - {s.get('name', '')}", s.get("id"))
        self._style_combo(self.supplier_combo)
        general_layout.addWidget(self.supplier_combo, row, 1)
        row += 1
        
        # Depo
        general_layout.addWidget(self._create_label("Depo *"), row, 0)
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.addItem("- Depo Seçin -", None)
        for w in self.warehouses:
            self.warehouse_combo.addItem(w.get("name", ""), w.get("id"))
        self._style_combo(self.warehouse_combo)
        general_layout.addWidget(self.warehouse_combo, row, 1)
        row += 1
        
        # Tedarikçi Fatura No
        general_layout.addWidget(self._create_label("Fatura No"), row, 0)
        self.invoice_no_input = QLineEdit()
        self.invoice_no_input.setPlaceholderText("Tedarikçi fatura numarası")
        self._style_input(self.invoice_no_input)
        general_layout.addWidget(self.invoice_no_input, row, 1)
        row += 1
        
        # İrsaliye No
        general_layout.addWidget(self._create_label("İrsaliye No"), row, 0)
        self.delivery_no_input = QLineEdit()
        self.delivery_no_input.setPlaceholderText("Tedarikçi irsaliye numarası")
        self._style_input(self.delivery_no_input)
        general_layout.addWidget(self.delivery_no_input, row, 1)
        row += 1
        
        # Notlar
        general_layout.addWidget(self._create_label("Notlar"), row, 0)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Ek açıklamalar...")
        self._style_textedit(self.notes_input)
        general_layout.addWidget(self.notes_input, row, 1)
        
        general_frame.layout().addLayout(general_layout)
        scroll_layout.addWidget(general_frame)
        
        # === KALEMLER ===
        items_frame = self._create_section("📦 Mal Kabul Kalemleri")
        items_layout = QVBoxLayout()
        
        # Kalem ekleme
        add_row = QHBoxLayout()
        
        self.item_combo = QComboBox()
        self.item_combo.addItem("- Stok Kartı Seçin -", None)
        for item in self.items:
            self.item_combo.addItem(f"{item.get('code', '')} - {item.get('name', '')}", item)
        self.item_combo.setMinimumWidth(300)
        self._style_combo(self.item_combo)
        add_row.addWidget(self.item_combo)
        
        self.qty_input = QDoubleSpinBox()
        self.qty_input.setRange(0.0001, 999999999)
        self.qty_input.setDecimals(4)
        self.qty_input.setValue(1)
        self.qty_input.setPrefix("Miktar: ")
        self.qty_input.setMinimumWidth(150)
        self._style_spin(self.qty_input)
        add_row.addWidget(self.qty_input)
        
        self.lot_input = QLineEdit()
        self.lot_input.setPlaceholderText("Lot No (opsiyonel)")
        self.lot_input.setMaximumWidth(150)
        self._style_input(self.lot_input)
        add_row.addWidget(self.lot_input)
        
        add_item_btn = QPushButton("➕ Ekle")
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
        add_row.addWidget(add_item_btn)
        
        add_row.addStretch()
        items_layout.addLayout(add_row)
        
        # Tablo
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "Stok Kodu", "Stok Adı", "Miktar", "Birim",
            "Kabul", "Ret", "İşlem"
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
        self.items_table.setColumnWidth(0, 120)
        self.items_table.setColumnWidth(2, 100)
        self.items_table.setColumnWidth(3, 80)
        self.items_table.setColumnWidth(4, 100)
        self.items_table.setColumnWidth(5, 100)
        self.items_table.setColumnWidth(6, 60)
        
        items_layout.addWidget(self.items_table)
        
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
        
    def _add_item_row(self):
        """Kalem ekle"""
        item_data = self.item_combo.currentData()
        if not item_data:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir stok kartı seçin!")
            return
        
        qty = self.qty_input.value()
        lot = self.lot_input.text().strip()
        
        self._insert_item_row(item_data, qty, qty, 0, lot)
        
        # Reset
        self.item_combo.setCurrentIndex(0)
        self.qty_input.setValue(1)
        self.lot_input.clear()
        
    def _insert_item_row(self, item: dict, quantity: float, 
                        accepted: float = None, rejected: float = 0,
                        lot_number: str = ""):
        """Tabloya kalem ekle"""
        if accepted is None:
            accepted = quantity
            
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        # Stok Kodu
        code_item = QTableWidgetItem(item.get("code", ""))
        code_item.setData(Qt.ItemDataRole.UserRole, item.get("id"))
        code_item.setData(Qt.ItemDataRole.UserRole + 1, lot_number)
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
        
        # Kabul edilen
        accepted_spin = QDoubleSpinBox()
        accepted_spin.setRange(0, quantity)
        accepted_spin.setDecimals(4)
        accepted_spin.setValue(accepted)
        accepted_spin.setStyleSheet(self._spin_style_small())
        accepted_spin.valueChanged.connect(lambda v: self._on_accepted_changed(row, v, quantity))
        self.items_table.setCellWidget(row, 4, accepted_spin)
        
        # Reddedilen
        rejected_spin = QDoubleSpinBox()
        rejected_spin.setRange(0, quantity)
        rejected_spin.setDecimals(4)
        rejected_spin.setValue(rejected)
        rejected_spin.setStyleSheet(self._spin_style_small())
        rejected_spin.valueChanged.connect(lambda v: self._on_rejected_changed(row, v, quantity))
        self.items_table.setCellWidget(row, 5, rejected_spin)
        
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
        del_btn.clicked.connect(lambda: self.items_table.removeRow(row))
        self.items_table.setCellWidget(row, 6, del_btn)
        
        self.items_table.setRowHeight(row, 50)
        
    def _on_accepted_changed(self, row: int, value: float, total: float):
        """Kabul değiştiğinde red'i güncelle"""
        rejected_spin = self.items_table.cellWidget(row, 5)
        if rejected_spin:
            rejected_spin.blockSignals(True)
            rejected_spin.setValue(total - value)
            rejected_spin.blockSignals(False)
            
    def _on_rejected_changed(self, row: int, value: float, total: float):
        """Red değiştiğinde kabul'ü güncelle"""
        accepted_spin = self.items_table.cellWidget(row, 4)
        if accepted_spin:
            accepted_spin.blockSignals(True)
            accepted_spin.setValue(total - value)
            accepted_spin.blockSignals(False)
        
    def load_data(self):
        """Düzenleme modunda verileri yükle"""
        if not self.receipt_data:
            return
        
        self.receipt_no_input.setText(self.receipt_data.get("receipt_no", ""))
        
        rec_date = self.receipt_data.get("receipt_date")
        if rec_date and isinstance(rec_date, date):
            self.receipt_date_input.setDate(QDate(rec_date.year, rec_date.month, rec_date.day))
        
        # Tedarikçi
        supplier_id = self.receipt_data.get("supplier_id")
        for i in range(self.supplier_combo.count()):
            if self.supplier_combo.itemData(i) == supplier_id:
                self.supplier_combo.setCurrentIndex(i)
                break
        
        # Depo
        warehouse_id = self.receipt_data.get("warehouse_id")
        for i in range(self.warehouse_combo.count()):
            if self.warehouse_combo.itemData(i) == warehouse_id:
                self.warehouse_combo.setCurrentIndex(i)
                break
        
        self.invoice_no_input.setText(self.receipt_data.get("supplier_invoice_no", "") or "")
        self.delivery_no_input.setText(self.receipt_data.get("supplier_delivery_no", "") or "")
        self.notes_input.setPlainText(self.receipt_data.get("notes", "") or "")
        
        # Kalemleri yükle
        items_data = self.receipt_data.get("items", [])
        for item_data in items_data:
            item_id = item_data.get("item_id")
            item_info = next((i for i in self.items if i.get("id") == item_id), None)
            if item_info:
                self._insert_item_row(
                    item_info,
                    float(item_data.get("quantity", 0)),
                    float(item_data.get("accepted_quantity", 0) or 0),
                    float(item_data.get("rejected_quantity", 0) or 0),
                    item_data.get("lot_number", "")
                )
        
    def _on_save(self):
        """Kaydet"""
        # Validasyon
        supplier_id = self.supplier_combo.currentData()
        if not supplier_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen tedarikçi seçin!")
            return
        
        warehouse_id = self.warehouse_combo.currentData()
        if not warehouse_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen depo seçin!")
            return
        
        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, "Uyarı", "En az bir kalem eklemelisiniz!")
            return
        
        # Kalemleri topla
        items_data = []
        for row in range(self.items_table.rowCount()):
            code_item = self.items_table.item(row, 0)
            item_id = code_item.data(Qt.ItemDataRole.UserRole) if code_item else None
            lot_number = code_item.data(Qt.ItemDataRole.UserRole + 1) if code_item else ""
            
            qty_item = self.items_table.item(row, 2)
            quantity = float(qty_item.text()) if qty_item else 0
            
            unit_item = self.items_table.item(row, 3)
            unit_id = unit_item.data(Qt.ItemDataRole.UserRole) if unit_item else None
            
            accepted_widget = self.items_table.cellWidget(row, 4)
            accepted = accepted_widget.value() if accepted_widget else quantity
            
            rejected_widget = self.items_table.cellWidget(row, 5)
            rejected = rejected_widget.value() if rejected_widget else 0
            
            if item_id and quantity > 0:
                items_data.append({
                    "item_id": item_id,
                    "quantity": Decimal(str(quantity)),
                    "unit_id": unit_id,
                    "accepted_quantity": Decimal(str(accepted)),
                    "rejected_quantity": Decimal(str(rejected)),
                    "lot_number": lot_number or None,
                })
        
        qdate = self.receipt_date_input.date()
        
        data = {
            "receipt_date": date(qdate.year(), qdate.month(), qdate.day()),
            "supplier_id": supplier_id,
            "warehouse_id": warehouse_id,
            "supplier_invoice_no": self.invoice_no_input.text().strip() or None,
            "supplier_delivery_no": self.delivery_no_input.text().strip() or None,
            "notes": self.notes_input.toPlainText().strip() or None,
            "items": items_data,
        }
        
        if self.is_edit_mode and self.receipt_data:
            data["id"] = self.receipt_data.get("id")
        
        self.saved.emit(data)
        
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
        
    def _style_spin(self, s):
        s.setMinimumHeight(42)
        s.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 12px;
                color: #f8fafc;
                font-size: 14px;
            }
            QDoubleSpinBox:focus { border-color: #6366f1; }
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
