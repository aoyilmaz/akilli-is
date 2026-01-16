"""
Akıllı İş - Ürün Reçetesi (BOM) Form Sayfası
"""

from typing import Optional
from decimal import Decimal
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
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QTabWidget,
    QDialog,
    QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor


class MaterialSelectDialog(QDialog):
    """Malzeme seçim dialogu"""

    def __init__(self, items: list, parent=None):
        super().__init__(parent)
        self.items = items
        self.selected_item = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Malzeme Seç")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Arama
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Malzeme ara...")
        self.search_input.textChanged.connect(self._filter_items)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Kod", "Malzeme Adı", "Birim", "Stok"])
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(self._on_select)
        self._load_items()
        layout.addWidget(self.table)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        select_btn = QPushButton("Seç")
        select_btn.clicked.connect(self._on_select)
        btn_layout.addWidget(select_btn)

        layout.addLayout(btn_layout)

    def _load_items(self):
        self.table.setRowCount(len(self.items))
        for row, item in enumerate(self.items):
            code_item = QTableWidgetItem(item.get("code", ""))
            code_item.setData(Qt.ItemDataRole.UserRole, item)
            code_item.setForeground(QColor("#818cf8"))
            self.table.setItem(row, 0, code_item)
            self.table.setItem(row, 1, QTableWidgetItem(item.get("name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(item.get("unit_code", "ADET")))
            stock = item.get("total_stock", 0)
            stock_item = QTableWidgetItem(f"{stock:,.2f}")
            stock_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 3, stock_item)

    def _filter_items(self, text: str):
        for row in range(self.table.rowCount()):
            match = any(
                text.lower()
                in (
                    self.table.item(row, col).text().lower()
                    if self.table.item(row, col)
                    else ""
                )
                for col in range(2)
            )
            self.table.setRowHidden(row, not match)

    def _on_select(self):
        row = self.table.currentRow()
        if row >= 0:
            self.selected_item = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.accept()

    def get_selected(self) -> Optional[dict]:
        return self.selected_item


class BOMFormPage(QWidget):
    """Ürün reçetesi formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()
    code_requested = pyqtSignal()

    def __init__(self, bom_data: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.bom_data = bom_data
        self.is_edit_mode = bom_data is not None
        self.bom_data = bom_data
        self.is_edit_mode = bom_data is not None
        self.lines = []
        self.by_products = []
        self.available_items = []
        self.available_products = []
        self.setup_ui()
        if self.is_edit_mode:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        header_layout = QHBoxLayout()

        back_btn = QPushButton("← Geri")
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)

        title_text = "Reçete Düzenle" if self.is_edit_mode else "Yeni Ürün Reçetesi"
        title = QLabel(f"📋 {title_text}")
        header_layout.addWidget(title)
        header_layout.addStretch()

        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(self._on_save)
        header_layout.addWidget(save_btn)

        layout.addLayout(header_layout)

        # Tab Widget
        tabs = QTabWidget()
        tabs.addTab(self._create_general_tab(), "📝 Genel Bilgiler")
        tabs.addTab(self._create_materials_tab(), "📦 Malzemeler")
        tabs.addTab(self._create_by_products_tab(), "♻️ Yan Ürünler")
        tabs.addTab(self._create_cost_tab(), "💰 Maliyet")

        layout.addWidget(tabs)

    def _create_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        form_frame = QFrame()
        form_frame.setStyleSheet(
            "QFrame { background-color: rgba(30, 41, 59, 0.3); border: 1px solid #334155; border-radius: 12px; }"
        )
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(16)

        # Reçete Kodu
        form_layout.addWidget(QLabel("Reçete Kodu *"), 0, 0)
        code_layout = QHBoxLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("BOM000001")
        code_layout.addWidget(self.code_input)

        auto_btn = QPushButton("🔄")
        auto_btn.setFixedSize(40, 40)
        auto_btn.clicked.connect(self.code_requested.emit)
        code_layout.addWidget(auto_btn)
        form_layout.addLayout(code_layout, 0, 1)

        # Reçete Adı
        form_layout.addWidget(QLabel("Reçete Adı *"), 1, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Örn: PVC Film 500mm Standart")
        form_layout.addWidget(self.name_input, 1, 1)

        # Mamul
        form_layout.addWidget(QLabel("Mamul *"), 2, 0)
        self.product_combo = QComboBox()
        form_layout.addWidget(self.product_combo, 2, 1)

        # Temel Üretim Miktarı
        form_layout.addWidget(QLabel("Temel Üretim Miktarı"), 3, 0)
        qty_layout = QHBoxLayout()
        self.base_qty_input = QDoubleSpinBox()
        self.base_qty_input.setRange(0.0001, 999999999)
        self.base_qty_input.setDecimals(4)
        self.base_qty_input.setValue(1)
        qty_layout.addWidget(self.base_qty_input)

        self.unit_combo = QComboBox()
        self.unit_combo.setFixedWidth(100)
        qty_layout.addWidget(self.unit_combo)
        form_layout.addLayout(qty_layout, 3, 1)

        # Versiyon
        form_layout.addWidget(QLabel("Versiyon"), 4, 0)
        version_layout = QHBoxLayout()
        self.version_input = QSpinBox()
        self.version_input.setRange(1, 999)
        self.version_input.setValue(1)
        version_layout.addWidget(self.version_input)
        version_layout.addWidget(QLabel("Rev:"))
        self.revision_input = QLineEdit("A")
        self.revision_input.setMaximumWidth(60)
        version_layout.addWidget(self.revision_input)
        version_layout.addStretch()
        form_layout.addLayout(version_layout, 4, 1)

        # Durum
        form_layout.addWidget(QLabel("Durum"), 5, 0)
        self.status_combo = QComboBox()
        self.status_combo.addItem("🟡 Taslak", "draft")
        self.status_combo.addItem("✅ Aktif", "active")
        form_layout.addWidget(self.status_combo, 5, 1)

        # Açıklama
        form_layout.addWidget(QLabel("Açıklama"), 6, 0)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        form_layout.addWidget(self.description_input, 6, 1)

        layout.addWidget(form_frame)
        layout.addStretch()
        return tab

    def _create_materials_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Toolbar
        toolbar = QHBoxLayout()

        add_btn = QPushButton("➕ Malzeme Ekle")
        add_btn.clicked.connect(self._add_material)
        toolbar.addWidget(add_btn)

        remove_btn = QPushButton("🗑 Seçileni Kaldır")
        remove_btn.clicked.connect(self._remove_material)
        toolbar.addWidget(remove_btn)
        toolbar.addStretch()

        self.total_label = QLabel("Toplam: 0 malzeme")
        toolbar.addWidget(self.total_label)
        layout.addLayout(toolbar)

        # Tablo
        self.materials_table = QTableWidget()
        self._setup_materials_table()
        layout.addWidget(self.materials_table)

        return tab

    def _setup_materials_table(self):
        columns = [
            ("Sıra", 50),
            ("Malzeme Kodu", 120),
            ("Malzeme Adı", 200),
            ("Miktar", 100),
            ("Birim", 80),
            ("Fire %", 80),
            ("Net Miktar", 100),
            ("Birim Maliyet", 110),
            ("Satır Maliyeti", 110),
        ]

        self.materials_table.setColumnCount(len(columns))
        self.materials_table.setHorizontalHeaderLabels([c[0] for c in columns])

        header = self.materials_table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 2:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                self.materials_table.setColumnWidth(i, width)

        self.materials_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.materials_table.verticalHeader().setVisible(False)

    def _create_by_products_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Toolbar
        toolbar = QHBoxLayout()

        add_btn = QPushButton("➕ Yan Ürün Ekle")
        add_btn.clicked.connect(self._add_by_product)
        toolbar.addWidget(add_btn)

        remove_btn = QPushButton("🗑 Seçileni Kaldır")
        remove_btn.clicked.connect(self._remove_by_product)
        toolbar.addWidget(remove_btn)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        # Tablo
        self.by_products_table = QTableWidget()
        self._setup_by_products_table()
        layout.addWidget(self.by_products_table)

        return tab

    def _setup_by_products_table(self):
        columns = [
            ("Sıra", 50),
            ("Malzeme Kodu", 120),
            ("Malzeme Adı", 200),
            ("Miktar", 100),
            ("Birim", 80),
            ("Maliyet Payı %", 100),
            ("Notlar", 150),
        ]

        self.by_products_table.setColumnCount(len(columns))
        self.by_products_table.setHorizontalHeaderLabels([c[0] for c in columns])

        header = self.by_products_table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 2:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                self.by_products_table.setColumnWidth(i, width)

        self.by_products_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.by_products_table.verticalHeader().setVisible(False)

    def _add_by_product(self):
        if not self.available_items:
            QMessageBox.warning(self, "Uyarı", "Malzeme listesi yüklenmedi!")
            return

        dialog = MaterialSelectDialog(self.available_items, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            item = dialog.get_selected()
            if item:
                self.by_products.append(
                    {
                        "item_id": item["id"],
                        "item_code": item["code"],
                        "item_name": item["name"],
                        "quantity": Decimal("1"),
                        "unit_code": item["unit_code"],
                        "unit_id": item.get("unit_id"),
                        "cost_share_rate": Decimal("0"),
                        "notes": "",
                    }
                )
                self._refresh_by_products_table()

    def _remove_by_product(self):
        row = self.by_products_table.currentRow()
        if 0 <= row < len(self.by_products):
            self.by_products.pop(row)
            self._refresh_by_products_table()

    def _refresh_by_products_table(self):
        self.by_products_table.setRowCount(len(self.by_products))

        for row, line in enumerate(self.by_products):
            self.by_products_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))

            code_item = QTableWidgetItem(line["item_code"])
            code_item.setForeground(QColor("#818cf8"))
            self.by_products_table.setItem(row, 1, code_item)
            self.by_products_table.setItem(row, 2, QTableWidgetItem(line["item_name"]))

            # Miktar
            qty_spin = QDoubleSpinBox()
            qty_spin.setRange(0.0001, 999999999)
            qty_spin.setDecimals(4)
            qty_spin.setValue(float(line["quantity"]))
            qty_spin.valueChanged.connect(
                lambda val, r=row: self._on_bp_qty_changed(r, val)
            )
            self.by_products_table.setCellWidget(row, 3, qty_spin)

            self.by_products_table.setItem(row, 4, QTableWidgetItem(line["unit_code"]))

            # Maliyet Payı
            share_spin = QDoubleSpinBox()
            share_spin.setRange(0, 100)
            share_spin.setDecimals(2)
            share_spin.setSuffix("%")
            share_spin.setValue(float(line.get("cost_share_rate", 0)))
            share_spin.valueChanged.connect(
                lambda val, r=row: self._on_bp_share_changed(r, val)
            )
            self.by_products_table.setCellWidget(row, 5, share_spin)

            # Notlar
            note_edit = QLineEdit(line.get("notes", ""))
            note_edit.textChanged.connect(
                lambda val, r=row: self._on_bp_note_changed(r, val)
            )
            self.by_products_table.setCellWidget(row, 6, note_edit)

    def _on_bp_qty_changed(self, row: int, value: float):
        if 0 <= row < len(self.by_products):
            self.by_products[row]["quantity"] = Decimal(str(value))

    def _on_bp_share_changed(self, row: int, value: float):
        if 0 <= row < len(self.by_products):
            self.by_products[row]["cost_share_rate"] = Decimal(str(value))

    def _on_bp_note_changed(self, row: int, value: str):
        if 0 <= row < len(self.by_products):
            self.by_products[row]["notes"] = value

    def _create_cost_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        cost_frame = QFrame()
        cost_frame.setStyleSheet(
            "QFrame { background-color: rgba(30, 41, 59, 0.3); border: 1px solid #334155; border-radius: 12px; }"
        )
        cost_layout = QGridLayout(cost_frame)
        cost_layout.setContentsMargins(20, 20, 20, 20)
        cost_layout.setSpacing(16)

        cost_layout.addWidget(QLabel("Malzeme Maliyeti"), 0, 0)
        self.material_cost_label = QLabel("₺0,00")
        cost_layout.addWidget(self.material_cost_label, 0, 1)

        cost_layout.addWidget(QLabel("İşçilik Maliyeti"), 1, 0)
        self.labor_cost_input = QDoubleSpinBox()
        self.labor_cost_input.setRange(0, 999999999)
        self.labor_cost_input.setDecimals(2)
        self.labor_cost_input.setPrefix("₺")
        self.labor_cost_input.valueChanged.connect(self._update_total_cost)
        cost_layout.addWidget(self.labor_cost_input, 1, 1)

        cost_layout.addWidget(QLabel("Genel Giderler"), 2, 0)
        self.overhead_cost_input = QDoubleSpinBox()
        self.overhead_cost_input.setRange(0, 999999999)
        self.overhead_cost_input.setDecimals(2)
        self.overhead_cost_input.setPrefix("₺")
        self.overhead_cost_input.valueChanged.connect(self._update_total_cost)
        cost_layout.addWidget(self.overhead_cost_input, 2, 1)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        cost_layout.addWidget(separator, 3, 0, 1, 2)

        cost_layout.addWidget(QLabel("TOPLAM MALİYET"), 4, 0)
        self.total_cost_label = QLabel("₺0,00")
        cost_layout.addWidget(self.total_cost_label, 4, 1)

        cost_layout.addWidget(QLabel("Birim Başı Maliyet"), 5, 0)
        self.unit_cost_label = QLabel("₺0,00")
        cost_layout.addWidget(self.unit_cost_label, 5, 1)

        layout.addWidget(cost_frame)
        layout.addStretch()
        return tab

    def set_products(self, products: list):
        self.available_products = products
        self.product_combo.clear()
        self.product_combo.addItem("Seçiniz...", None)
        for p in products:
            self.product_combo.addItem(f"{p.code} - {p.name}", p.id)

    def set_items(self, items: list):
        self.available_items = []
        for item in items:
            self.available_items.append(
                {
                    "id": item.id,
                    "code": item.code,
                    "name": item.name,
                    "unit_code": item.unit.code if item.unit else "ADET",
                    "unit_id": item.unit_id,
                    "purchase_price": float(item.purchase_price or 0),
                    "total_stock": float(item.total_stock or 0),
                }
            )

    def set_units(self, units: list):
        self.unit_combo.clear()
        for u in units:
            self.unit_combo.addItem(u.code, u.id)

    def set_generated_code(self, code: str):
        self.code_input.setText(code)

    def _add_material(self):
        if not self.available_items:
            QMessageBox.warning(self, "Uyarı", "Malzeme listesi yüklenmedi!")
            return

        dialog = MaterialSelectDialog(self.available_items, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            item = dialog.get_selected()
            if item:
                self.lines.append(
                    {
                        "item_id": item["id"],
                        "item_code": item["code"],
                        "item_name": item["name"],
                        "quantity": Decimal("1"),
                        "unit_code": item["unit_code"],
                        "unit_id": item.get("unit_id"),
                        "scrap_rate": Decimal("0"),
                        "unit_cost": Decimal(str(item["purchase_price"])),
                    }
                )
                self._refresh_materials_table()

    def _remove_material(self):
        row = self.materials_table.currentRow()
        if 0 <= row < len(self.lines):
            self.lines.pop(row)
            self._refresh_materials_table()

    def _refresh_materials_table(self):
        self.materials_table.setRowCount(len(self.lines))
        total_cost = Decimal(0)

        for row, line in enumerate(self.lines):
            self.materials_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))

            code_item = QTableWidgetItem(line["item_code"])
            code_item.setForeground(QColor("#818cf8"))
            self.materials_table.setItem(row, 1, code_item)
            self.materials_table.setItem(row, 2, QTableWidgetItem(line["item_name"]))

            qty_spin = QDoubleSpinBox()
            qty_spin.setRange(0.0001, 999999999)
            qty_spin.setDecimals(4)
            qty_spin.setValue(float(line["quantity"]))
            qty_spin.valueChanged.connect(
                lambda val, r=row: self._on_qty_changed(r, val)
            )
            self.materials_table.setCellWidget(row, 3, qty_spin)

            self.materials_table.setItem(row, 4, QTableWidgetItem(line["unit_code"]))

            scrap_spin = QDoubleSpinBox()
            scrap_spin.setRange(0, 100)
            scrap_spin.setDecimals(2)
            scrap_spin.setSuffix("%")
            scrap_spin.setValue(float(line.get("scrap_rate", 0)))
            scrap_spin.valueChanged.connect(
                lambda val, r=row: self._on_scrap_changed(r, val)
            )
            self.materials_table.setCellWidget(row, 5, scrap_spin)

            qty = line["quantity"]
            scrap = line.get("scrap_rate", Decimal(0))
            net_qty = qty * (1 + scrap / 100)
            self.materials_table.setItem(row, 6, QTableWidgetItem(f"{net_qty:,.4f}"))

            unit_cost = line.get("unit_cost", Decimal(0))
            self.materials_table.setItem(row, 7, QTableWidgetItem(f"₺{unit_cost:,.2f}"))

            line_cost = net_qty * unit_cost
            line["line_cost"] = line_cost
            total_cost += line_cost
            line_cost_item = QTableWidgetItem(f"₺{line_cost:,.2f}")
            line_cost_item.setForeground(QColor("#10b981"))
            self.materials_table.setItem(row, 8, line_cost_item)

        self.total_label.setText(f"Toplam: {len(self.lines)} malzeme")
        self.material_cost_label.setText(f"₺{total_cost:,.2f}")
        self._update_total_cost()

    def _on_qty_changed(self, row: int, value: float):
        if 0 <= row < len(self.lines):
            self.lines[row]["quantity"] = Decimal(str(value))
            self._refresh_materials_table()

    def _on_scrap_changed(self, row: int, value: float):
        if 0 <= row < len(self.lines):
            self.lines[row]["scrap_rate"] = Decimal(str(value))
            self._refresh_materials_table()

    def _update_total_cost(self):
        material_cost = sum(line.get("line_cost", Decimal(0)) for line in self.lines)
        labor_cost = Decimal(str(self.labor_cost_input.value()))
        overhead_cost = Decimal(str(self.overhead_cost_input.value()))
        total = material_cost + labor_cost + overhead_cost
        self.total_cost_label.setText(f"₺{total:,.2f}")

        base_qty = Decimal(str(self.base_qty_input.value()))
        if base_qty > 0:
            self.unit_cost_label.setText(f"₺{total / base_qty:,.2f}")

    def load_data(self):
        if not self.bom_data:
            return
        self.code_input.setText(self.bom_data.get("code", ""))
        self.name_input.setText(self.bom_data.get("name", ""))
        self.description_input.setPlainText(self.bom_data.get("description", ""))
        self.base_qty_input.setValue(float(self.bom_data.get("base_quantity", 1)))
        self.version_input.setValue(self.bom_data.get("version", 1))
        self.revision_input.setText(self.bom_data.get("revision", "A"))
        self.lines = self.bom_data.get("lines", [])
        self._refresh_materials_table()

        self.by_products = self.bom_data.get("by_products", [])
        self._refresh_by_products_table()

        self.labor_cost_input.setValue(float(self.bom_data.get("labor_cost", 0)))
        self.overhead_cost_input.setValue(float(self.bom_data.get("overhead_cost", 0)))

    def _on_save(self):
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()

        if not code:
            QMessageBox.warning(self, "Uyarı", "Reçete kodu zorunludur!")
            return
        if not name:
            QMessageBox.warning(self, "Uyarı", "Reçete adı zorunludur!")
            return
        product_id = self.product_combo.currentData()
        if not product_id:
            QMessageBox.warning(self, "Uyarı", "Mamul seçimi zorunludur!")
            return
        if not self.lines:
            QMessageBox.warning(self, "Uyarı", "En az bir malzeme eklemelisiniz!")
            return

        data = {
            "code": code,
            "name": name,
            "description": self.description_input.toPlainText().strip(),
            "item_id": product_id,
            "base_quantity": Decimal(str(self.base_qty_input.value())),
            "unit_id": self.unit_combo.currentData(),
            "version": self.version_input.value(),
            "revision": self.revision_input.text().strip() or "A",
            "status": self.status_combo.currentData(),
            "labor_cost": Decimal(str(self.labor_cost_input.value())),
            "overhead_cost": Decimal(str(self.overhead_cost_input.value())),
            "lines": [
                {
                    "item_id": l["item_id"],
                    "quantity": l["quantity"],
                    "unit_id": l.get("unit_id"),
                    "scrap_rate": l.get("scrap_rate", Decimal(0)),
                    "unit_cost": l.get("unit_cost", Decimal(0)),
                    "line_cost": l.get("line_cost", Decimal(0)),
                }
                for l in self.lines
            ],
            "by_products": [
                {
                    "item_id": b["item_id"],
                    "quantity": b["quantity"],
                    "unit_id": b.get("unit_id"),
                    "cost_share_rate": b.get("cost_share_rate", Decimal(0)),
                    "notes": b.get("notes", ""),
                }
                for b in self.by_products
            ],
        }
        if self.is_edit_mode and self.bom_data:
            data["id"] = self.bom_data.get("id")
        self.saved.emit(data)
