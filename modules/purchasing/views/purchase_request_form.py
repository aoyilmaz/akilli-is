"""
Akıllı İş - Satın Alma Talep Formu
"""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QSpinBox,
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
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get("stock", 0))))

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

class PurchaseRequestFormPage(QWidget):
    """Satın alma talep formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()
    submit_for_approval = pyqtSignal(int)

    def __init__(
        self,
        request_data: Optional[dict] = None,
        items: list = None,
        suppliers: list = None,
        units: list = None,
        parent=None,
    ):
        super().__init__(parent)
        self.request_data = request_data
        self.is_edit_mode = request_data is not None
        self.items = items or []
        self.suppliers = suppliers or []
        self.units = units or []
        self.line_items = []  # Talep kalemleri
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

        title_text = "Talep Düzenle" if self.is_edit_mode else "Yeni Satın Alma Talebi"
        title = QLabel(f"📋 {title_text}")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Onaya Gönder butonu (sadece düzenlemede ve taslak ise)
        if self.is_edit_mode and self.request_data.get("status") == "draft":
            submit_btn = QPushButton("📤 Onaya Gönder")
            submit_btn.clicked.connect(self._on_submit_for_approval)
            header_layout.addWidget(submit_btn)

        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet(
            """
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
        general_frame = self._create_section("📝 Genel Bilgiler")
        general_layout = QGridLayout()
        general_layout.setColumnMinimumWidth(0, 140)
        general_layout.setSpacing(12)

        row = 0

        # Talep No
        general_layout.addWidget(self._create_label("Talep No"), row, 0)
        self.request_no_input = QLineEdit()
        self.request_no_input.setPlaceholderText("Otomatik oluşturulacak")
        self.request_no_input.setReadOnly(True)
        general_layout.addWidget(self.request_no_input, row, 1)
        row += 1

        # Talep Tarihi
        general_layout.addWidget(self._create_label("Talep Tarihi *"), row, 0)
        self.request_date_input = QDateEdit()
        self.request_date_input.setDate(QDate.currentDate())
        self.request_date_input.setCalendarPopup(True)
        general_layout.addWidget(self.request_date_input, row, 1)
        row += 1

        # Talep Eden
        general_layout.addWidget(self._create_label("Talep Eden"), row, 0)
        self.requested_by_input = QLineEdit()
        self.requested_by_input.setPlaceholderText("Ad Soyad")
        general_layout.addWidget(self.requested_by_input, row, 1)
        row += 1

        # Departman
        general_layout.addWidget(self._create_label("Departman"), row, 0)
        self.department_input = QComboBox()
        self.department_input.setEditable(True)
        self.department_input.addItems(
            ["", "Üretim", "Satış", "Satın Alma", "Depo", "Kalite", "Bakım", "İdari"]
        )
        general_layout.addWidget(self.department_input, row, 1)
        row += 1

        # Öncelik
        general_layout.addWidget(self._create_label("Öncelik"), row, 0)
        self.priority_input = QComboBox()
        self.priority_input.addItem("⬇️ Düşük", 1)
        self.priority_input.addItem("➡️ Normal", 2)
        self.priority_input.addItem("⬆️ Yüksek", 3)
        self.priority_input.addItem("🔥 Acil", 4)
        self.priority_input.setCurrentIndex(1)  # Normal
        general_layout.addWidget(self.priority_input, row, 1)
        row += 1

        # Termin Tarihi
        general_layout.addWidget(self._create_label("Termin Tarihi"), row, 0)
        self.required_date_input = QDateEdit()
        self.required_date_input.setDate(QDate.currentDate().addDays(7))
        self.required_date_input.setCalendarPopup(True)
        general_layout.addWidget(self.required_date_input, row, 1)
        row += 1

        # Notlar
        general_layout.addWidget(self._create_label("Notlar"), row, 0)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Ek açıklamalar...")
        general_layout.addWidget(self.notes_input, row, 1)

        general_frame.layout().addLayout(general_layout)
        scroll_layout.addWidget(general_frame)

        # === TALEP KALEMLERİ ===
        items_frame = self._create_section("📦 Talep Kalemleri")
        items_layout = QVBoxLayout()

        # Kalem ekleme butonu
        add_item_btn = QPushButton("➕ Kalem Ekle")
        add_item_btn.clicked.connect(self._add_item_row)
        items_layout.addWidget(add_item_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # Kalemler tablosu
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels(
            [
                "Stok Kodu",
                "Stok Adı",
                "Miktar",
                "Birim",
                "Tahmini Fiyat",
                "Önerilen Tedarikçi",
                "İşlem",
            ]
        )
        self.items_table.setMinimumHeight(200)
        self.items_table.verticalHeader().setVisible(False)

        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.items_table.setColumnWidth(0, 120)
        self.items_table.setColumnWidth(2, 100)
        self.items_table.setColumnWidth(3, 80)
        self.items_table.setColumnWidth(4, 120)
        self.items_table.setColumnWidth(5, 150)
        self.items_table.setColumnWidth(6, 60)

        items_layout.addWidget(self.items_table)

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
        """Yeni kalem satırı ekle"""
        # Stok kartı seçimi
        if not self.items:
            QMessageBox.warning(self, "Uyarı", "Önce stok kartları yüklenmelidir!")
            return

        dialog = ItemSelectorDialog(self.items, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_item:
            item = dialog.selected_item
            self._insert_item_row(item)

    def _insert_item_row(
        self,
        item: dict,
        quantity: float = 1,
        estimated_price: float = 0,
        supplier_id: int = None,
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

        # Tahmini Fiyat
        price_spin = QDoubleSpinBox()
        price_spin.setRange(0, 999999999)
        price_spin.setDecimals(4)
        price_spin.setPrefix("₺ ")
        price_spin.setValue(estimated_price)
        price_spin.setStyleSheet(self._spin_style())
        self.items_table.setCellWidget(row, 4, price_spin)

        # Önerilen Tedarikçi
        supplier_combo = QComboBox()
        supplier_combo.addItem("- Seçiniz -", None)
        for s in self.suppliers:
            supplier_combo.addItem(s.get("name", ""), s.get("id"))
        if supplier_id:
            for i in range(supplier_combo.count()):
                if supplier_combo.itemData(i) == supplier_id:
                    supplier_combo.setCurrentIndex(i)
                    break
        supplier_combo.setStyleSheet(self._combo_style_small())
        self.items_table.setCellWidget(row, 5, supplier_combo)

        # Sil butonu
        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(32, 32)
        del_btn.clicked.connect(lambda: self._remove_item_row(row))
        self.items_table.setCellWidget(row, 6, del_btn)

        self.items_table.setRowHeight(row, 50)

    def _remove_item_row(self, row: int):
        """Kalem satırını sil"""
        self.items_table.removeRow(row)

    def load_data(self):
        """Düzenleme modunda verileri yükle"""
        if not self.request_data:
            return

        self.request_no_input.setText(self.request_data.get("request_no", ""))

        req_date = self.request_data.get("request_date")
        if req_date:
            if isinstance(req_date, date):
                self.request_date_input.setDate(
                    QDate(req_date.year, req_date.month, req_date.day)
                )

        self.requested_by_input.setText(self.request_data.get("requested_by", "") or "")

        dept = self.request_data.get("department", "")
        idx = self.department_input.findText(dept)
        if idx >= 0:
            self.department_input.setCurrentIndex(idx)
        else:
            self.department_input.setCurrentText(dept)

        priority = self.request_data.get("priority", 2)
        for i in range(self.priority_input.count()):
            if self.priority_input.itemData(i) == priority:
                self.priority_input.setCurrentIndex(i)
                break

        req_required = self.request_data.get("required_date")
        if req_required:
            if isinstance(req_required, date):
                self.required_date_input.setDate(
                    QDate(req_required.year, req_required.month, req_required.day)
                )

        self.notes_input.setPlainText(self.request_data.get("notes", "") or "")

        # Kalemleri yükle
        items_data = self.request_data.get("items", [])
        for item_data in items_data:
            # Item bilgisini bul
            item_id = item_data.get("item_id")
            item_info = next((i for i in self.items if i.get("id") == item_id), None)
            if item_info:
                self._insert_item_row(
                    item_info,
                    float(item_data.get("quantity", 1)),
                    float(item_data.get("estimated_price", 0) or 0),
                    item_data.get("suggested_supplier_id"),
                )

    def _on_save(self):
        """Kaydet"""
        # Validasyon
        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, "Uyarı", "En az bir kalem eklemelisiniz!")
            return

        # Kalemleri topla
        items_data = []
        for row in range(self.items_table.rowCount()):
            code_item = self.items_table.item(row, 0)
            item_id = code_item.data(Qt.ItemDataRole.UserRole) if code_item else None

            qty_widget = self.items_table.cellWidget(row, 2)
            quantity = qty_widget.value() if qty_widget else 0

            unit_widget = self.items_table.cellWidget(row, 3)
            unit_id = unit_widget.currentData() if unit_widget else None

            price_widget = self.items_table.cellWidget(row, 4)
            estimated_price = price_widget.value() if price_widget else 0

            supplier_widget = self.items_table.cellWidget(row, 5)
            supplier_id = supplier_widget.currentData() if supplier_widget else None

            if item_id and quantity > 0:
                items_data.append(
                    {
                        "item_id": item_id,
                        "quantity": Decimal(str(quantity)),
                        "unit_id": unit_id,
                        "estimated_price": (
                            Decimal(str(estimated_price)) if estimated_price else None
                        ),
                        "suggested_supplier_id": supplier_id,
                    }
                )

        if not items_data:
            QMessageBox.warning(self, "Uyarı", "Geçerli kalem bulunamadı!")
            return

        qdate = self.request_date_input.date()
        req_qdate = self.required_date_input.date()

        data = {
            "request_date": date(qdate.year(), qdate.month(), qdate.day()),
            "requested_by": self.requested_by_input.text().strip() or None,
            "department": self.department_input.currentText().strip() or None,
            "priority": self.priority_input.currentData(),
            "required_date": date(req_qdate.year(), req_qdate.month(), req_qdate.day()),
            "notes": self.notes_input.toPlainText().strip() or None,
            "items": items_data,
        }

        if self.is_edit_mode and self.request_data:
            data["id"] = self.request_data.get("id")

        self.saved.emit(data)

    def _on_submit_for_approval(self):
        """Onaya gönder"""
        if self.request_data:
            reply = QMessageBox.question(
                self,
                "Onaya Gönder",
                "Bu talebi onaya göndermek istediğinize emin misiniz?\n\nOnaya gönderdikten sonra düzenleme yapılamaz.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.submit_for_approval.emit(self.request_data.get("id"))

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
