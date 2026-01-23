"""
Akıllı İş - Ürün Reçetesi (BOM) Form Sayfası
"""

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
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QTabWidget,
    QFormLayout,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ui.components.toast import show_toast
from ui.components.page_header import PageHeader
from database.models.production import BOMStatus, BOMType


class BOMFormPage(QWidget):
    """Ürün reçetesi ekleme/düzenleme formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

    STATUS_OPTS = [
        ("Taslak", BOMStatus.DRAFT),
        ("Aktif", BOMStatus.ACTIVE),
        ("Revizyon", BOMStatus.REVISION),
        ("İptal", BOMStatus.OBSOLETE),
    ]

    TYPE_OPTS = [
        ("Standart Üretim", BOMType.STANDARD),
        ("Formül/Proses", BOMType.FORMULA),
    ]

    def __init__(self, bom=None, parent=None):
        super().__init__(parent)
        self.bom = bom
        self.is_edit = bom is not None

        self.items_map = {}  # id -> item obj
        self.units_map = {}  # id -> code
        self.stations_map = {}  # id -> station obj

        self._setup_ui()

        if self.is_edit:
            self.load_bom_data()
        else:
            self._init_defaults()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        title = "Reçete Düzenle" if self.is_edit else "Yeni Reçete"
        self.header = PageHeader(
            title=title, show_back=True, show_add=False, parent=self
        )
        self.header.back_clicked.connect(self.cancelled.emit)

        # Kaydet Butonu
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setProperty("class", "btn-primary")
        save_btn.clicked.connect(self._on_save)
        self.header.header_layout().addWidget(save_btn)

        layout.addWidget(self.header)

        # Ana Tab Widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_general_tab(), "📋 Genel Bilgiler")
        self.tabs.addTab(self._create_materials_tab(), "📦 Malzemeler")
        self.tabs.addTab(self._create_operations_tab(), "⚙️ Operasyonlar")
        self.tabs.addTab(self._create_cost_tab(), "💰 Maliyet Analizi")

        layout.addWidget(self.tabs)

    def _create_general_tab(self) -> QWidget:
        """Genel bilgiler ve başlık bilgileri"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Üst Bilgiler Formu
        form_frame = QFrame()
        form_layout = QHBoxLayout(form_frame)

        # Sol Kolon
        left_form = QFormLayout()

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("BOM-0001")
        left_form.addRow("Reçete Kodu *", self.code_input)

        self.name_input = QLineEdit()
        left_form.addRow("Reçete Adı *", self.name_input)

        self.item_combo = QComboBox()  # Üretilen Ürün
        left_form.addRow("Ürün *", self.item_combo)

        self.status_combo = QComboBox()
        for label, val in self.STATUS_OPTS:
            self.status_combo.addItem(label, val)
        left_form.addRow("Durum", self.status_combo)

        self.type_combo = QComboBox()
        for label, val in self.TYPE_OPTS:
            self.type_combo.addItem(label, val)
        left_form.addRow("Reçete Tipi", self.type_combo)

        form_layout.addLayout(left_form)

        # Sağ Kolon
        right_form = QFormLayout()

        self.base_qty_input = QDoubleSpinBox()
        self.base_qty_input.setRange(0.0001, 999999)
        self.base_qty_input.setValue(1.0)
        right_form.addRow("Baz Miktar", self.base_qty_input)

        self.unit_combo = QComboBox()
        right_form.addRow("Birim", self.unit_combo)

        self.version_input = QLineEdit("1")
        self.version_input.setReadOnly(True)
        right_form.addRow("Versiyon", self.version_input)

        self.revision_input = QLineEdit("A")
        right_form.addRow("Revizyon", self.revision_input)

        form_layout.addLayout(right_form)
        layout.addWidget(form_frame)

        # Açıklama
        layout.addWidget(QLabel("Açıklama"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(100)
        layout.addWidget(self.desc_input)

        layout.addStretch()
        return widget

    def _create_materials_tab(self) -> QWidget:
        """Malzeme listesi (BOM Lines)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Araç çubuğu
        toolbar = QHBoxLayout()
        add_line_btn = QPushButton("➕ Satır Ekle")
        add_line_btn.clicked.connect(self._add_material_line)

        remove_line_btn = QPushButton("🗑️ Satır Sil")
        remove_line_btn.clicked.connect(self._remove_selected_material)

        toolbar.addWidget(add_line_btn)
        toolbar.addWidget(remove_line_btn)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        # Tablo
        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(6)
        self.lines_table.setHorizontalHeaderLabels(
            [
                "Malzeme (Item)",
                "Miktar",
                "Birim",
                "Fire %",
                "Birim Maliyet",
                "Toplam Maliyet",
            ]
        )

        header = self.lines_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.lines_table)

        return widget

    def _create_operations_tab(self) -> QWidget:
        """Operasyon listesi (Routing)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Araç çubuğu
        toolbar = QHBoxLayout()
        add_op_btn = QPushButton("➕ Operasyon Ekle")
        add_op_btn.clicked.connect(self._add_operation_line)

        remove_op_btn = QPushButton("🗑️ Operasyon Sil")
        remove_op_btn.clicked.connect(self._remove_selected_operation)

        toolbar.addWidget(add_op_btn)
        toolbar.addWidget(remove_op_btn)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        # Tablo
        self.ops_table = QTableWidget()
        self.ops_table.setColumnCount(6)
        self.ops_table.setHorizontalHeaderLabels(
            [
                "Operasyon Adı",
                "İş İstasyonu",
                "Kurulum (dk)",
                "Birim Süre (dk)",
                "Maliyet",
                "Açıklama",
            ]
        )

        header = self.ops_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Ad
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # İstasyon

        layout.addWidget(self.ops_table)

        # Bilgi notu
        info_lbl = QLabel(
            "ℹ️ Maliyet = (Kurulum/60 * Saatlik Ücret) + (Birim Süre/60 * Miktar * Saatlik Ücret) + Sabit Kurulum Maliyeti"
        )
        info_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(info_lbl)

        return widget

    def _create_cost_tab(self) -> QWidget:
        """Maliyet özeti"""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.total_material_cost_lbl = QLabel("₺0.00")
        self.total_material_cost_lbl.setStyleSheet(
            "font-weight: bold; font-size: 14px;"
        )
        layout.addRow("Toplam Malzeme Maliyeti:", self.total_material_cost_lbl)

        self.labor_cost_input = QDoubleSpinBox()
        self.labor_cost_input.setRange(0, 9999999)
        self.labor_cost_input.setPrefix("₺")
        layout.addRow("İşçilik/Operasyon Maliyeti:", self.labor_cost_input)

        self.overhead_cost_input = QDoubleSpinBox()
        self.overhead_cost_input.setRange(0, 9999999)
        self.overhead_cost_input.setPrefix("₺")
        layout.addRow("Genel Giderler:", self.overhead_cost_input)

        self.total_cost_lbl = QLabel("₺0.00")
        self.total_cost_lbl.setStyleSheet(
            "font-weight: bold; font-size: 16px; color: #10b981;"
        )
        layout.addRow("TOPLAM MALİYET:", self.total_cost_lbl)

        # Hesapla butonu
        calc_btn = QPushButton("🔄 Maliyet Hesapla")
        calc_btn.clicked.connect(self._calculate_totals)
        layout.addRow("", calc_btn)

        return widget

    def _init_defaults(self):
        """Varsayılan değerler"""
        self.code_input.setText("")

    def load_data_sources(self, items: list, units: list, stations: list):
        """Form için gerekli combo verilerini yükle"""
        self.items_map = {i.id: i for i in items}
        self.units_map = {u.id: u.code for u in units}
        self.stations_map = {s.id: s for s in stations}

        # Ürün Combo
        self.item_combo.clear()
        for item in items:
            self.item_combo.addItem(f"{item.code} - {item.name}", item.id)

        # Birim Combo
        self.unit_combo.clear()
        for unit in units:
            self.unit_combo.addItem(f"{unit.code}", unit.id)

    def load_bom_data(self):
        """Mevcut BOM verisini forma yükle"""
        if not self.bom:
            return

        self.code_input.setText(self.bom.code)
        self.name_input.setText(self.bom.name)
        self.desc_input.setText(self.bom.description)
        self.base_qty_input.setValue(float(self.bom.base_quantity))
        self.version_input.setText(str(self.bom.version))
        self.revision_input.setText(self.bom.revision)

        # Comboları set et
        idx = self.item_combo.findData(self.bom.item_id)
        if idx >= 0:
            self.item_combo.setCurrentIndex(idx)

        idx = self.unit_combo.findData(self.bom.unit_id)
        if idx >= 0:
            self.unit_combo.setCurrentIndex(idx)

        # Status
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == self.bom.status:
                self.status_combo.setCurrentIndex(i)
                break

        # Type
        if hasattr(self.bom, "bom_type"):
            for i in range(self.type_combo.count()):
                if self.type_combo.itemData(i) == self.bom.bom_type:
                    self.type_combo.setCurrentIndex(i)
                    break

        # Maliyetler
        self.labor_cost_input.setValue(float(self.bom.labor_cost or 0))
        self.overhead_cost_input.setValue(float(self.bom.overhead_cost or 0))

        # Satırları yükle
        self.lines_table.setRowCount(0)
        for line in self.bom.lines:
            self._add_material_line(line)

        # Operasyonları yükle
        self.ops_table.setRowCount(0)
        if self.bom.operations:
            # operation_no sırasına göre
            sorted_ops = sorted(self.bom.operations, key=lambda x: x.operation_no)
            for op in sorted_ops:
                self._add_operation_line(op)

        self._calculate_totals()

    def _add_material_line(self, line_data=None):
        """Tabloya yeni malzeme satırı ekle"""
        row = self.lines_table.rowCount()
        self.lines_table.insertRow(row)

        # Malzeme Seçimi (Combo)
        combo = QComboBox()
        for item_id, item in self.items_map.items():
            combo.addItem(f"{item.code} - {item.name}", item_id)

        if line_data:
            idx = combo.findData(line_data.item_id)
            if idx >= 0:
                combo.setCurrentIndex(idx)

        self.lines_table.setCellWidget(row, 0, combo)

        # Miktar
        qty_spin = QDoubleSpinBox()
        qty_spin.setRange(0, 999999)
        qty_spin.setValue(float(line_data.quantity) if line_data else 1.0)
        self.lines_table.setCellWidget(row, 1, qty_spin)

        # Birim (Combo)
        unit_combo = QComboBox()
        for u_id, u_code in self.units_map.items():
            unit_combo.addItem(u_code, u_id)

        if line_data:
            idx = unit_combo.findData(line_data.unit_id)
            if idx >= 0:
                unit_combo.setCurrentIndex(idx)

        self.lines_table.setCellWidget(row, 2, unit_combo)

        # Fire
        scrap_spin = QDoubleSpinBox()
        scrap_spin.setRange(0, 100)
        scrap_spin.setValue(float(line_data.scrap_rate) if line_data else 0.0)
        self.lines_table.setCellWidget(row, 3, scrap_spin)

        # Birim Maliyet (Readonly - Item'dan gelecek)
        cost_item = QTableWidgetItem()
        cost_val = float(line_data.unit_cost) if line_data else 0.0
        cost_item.setText(f"{cost_val:.2f}")
        cost_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Readonly
        self.lines_table.setItem(row, 4, cost_item)

        # Toplam Maliyet (Hesaplanan)
        total_item = QTableWidgetItem("0.00")
        total_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.lines_table.setItem(row, 5, total_item)

    def _add_operation_line(self, op_data=None):
        """Tabloya yeni operasyon satırı ekle"""
        row = self.ops_table.rowCount()
        self.ops_table.insertRow(row)

        # Operasyon Adı
        name_input = QLineEdit()
        name_input.setText(op_data.name if op_data else "")
        name_input.setPlaceholderText("Örn: Kesim, Montaj")
        self.ops_table.setCellWidget(row, 0, name_input)

        # İstasyon Seçimi
        combo = QComboBox()
        combo.addItem("Seçiniz...", None)
        for s_id, station in self.stations_map.items():
            combo.addItem(f"{station.code} - {station.name}", s_id)

        if op_data and op_data.work_station_id:
            idx = combo.findData(op_data.work_station_id)
            if idx >= 0:
                combo.setCurrentIndex(idx)

        self.ops_table.setCellWidget(row, 1, combo)

        # Süreler
        setup_spin = QSpinBox()  # Dakika
        setup_spin.setRange(0, 9999)
        setup_spin.setValue(int(op_data.setup_time) if op_data else 0)
        self.ops_table.setCellWidget(row, 2, setup_spin)

        run_spin = QDoubleSpinBox()  # Dakika/Birim
        run_spin.setRange(0, 9999)
        run_spin.setValue(float(op_data.run_time) if op_data else 0)
        self.ops_table.setCellWidget(row, 3, run_spin)

        # Maliyet (Hesaplanan - Gösterimlik)
        cost_item = QTableWidgetItem("0.00")
        cost_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.ops_table.setItem(row, 4, cost_item)

        # Açıklama
        desc_input = QLineEdit()
        desc_input.setText(op_data.description if op_data else "")
        self.ops_table.setCellWidget(row, 5, desc_input)

    def _remove_selected_material(self):
        """Seçili malzeme satırını sil"""
        current_row = self.lines_table.currentRow()
        if current_row >= 0:
            self.lines_table.removeRow(current_row)

    def _remove_selected_operation(self):
        """Seçili operasyon satırını sil"""
        current_row = self.ops_table.currentRow()
        if current_row >= 0:
            self.ops_table.removeRow(current_row)

    def _calculate_totals(self):
        """Tüm maliyetleri hesapla"""
        bom_qty = self.base_qty_input.value()

        # --- Malzeme Maliyeti ---
        total_mat_cost = 0.0
        for row in range(self.lines_table.rowCount()):
            item_combo = self.lines_table.cellWidget(row, 0)
            item_id = item_combo.currentData()
            item = self.items_map.get(item_id)

            qty_spin = self.lines_table.cellWidget(row, 1)
            qty = qty_spin.value()

            scrap_spin = self.lines_table.cellWidget(row, 3)
            scrap = scrap_spin.value()

            unit_cost = float(item.purchase_price or 0) if item else 0.0
            self.lines_table.item(row, 4).setText(f"{unit_cost:.2f}")

            line_cost = qty * (1 + scrap / 100) * unit_cost
            self.lines_table.item(row, 5).setText(f"{line_cost:.2f}")
            total_mat_cost += line_cost

        self.total_material_cost_lbl.setText(f"₺{total_mat_cost:,.2f}")

        # --- Operasyon (İşçilik) Maliyeti ---
        total_op_cost = 0.0
        for row in range(self.ops_table.rowCount()):
            # İstasyon verilerini al
            station_combo = self.ops_table.cellWidget(row, 1)
            station_id = station_combo.currentData()
            station = self.stations_map.get(station_id)

            setup_min = self.ops_table.cellWidget(row, 2).value()
            run_min = self.ops_table.cellWidget(row, 3).value()

            op_cost = 0.0
            if station:
                hourly_rate = float(station.hourly_rate or 0)
                setup_cost_fixed = float(station.setup_cost or 0)

                # Maliyet = (Kurulum Süresi / 60 * Saatlik Ücret) + Sabit Kurulum + (Birim Süre * BOM Miktarı / 60 * Saatlik Ücret)
                # Not: Genelde BOM Miktarı için hesaplanır. BOM 1 adet ise 1 birim için.

                setup_part = (setup_min / 60.0) * hourly_rate
                run_part = (run_min / 60.0) * bom_qty * hourly_rate

                op_cost = setup_part + setup_cost_fixed + run_part

            self.ops_table.item(row, 4).setText(f"{op_cost:.2f}")
            total_op_cost += op_cost

        # İşçilik maliyetini güncelle
        self.labor_cost_input.setValue(total_op_cost)

        # --- Toplam ---
        overhead = self.overhead_cost_input.value()
        grand_total = total_mat_cost + total_op_cost + overhead
        self.total_cost_lbl.setText(f"₺{grand_total:,.2f}")

    def _on_save(self):
        """Kaydet"""
        if not self.code_input.text():
            show_toast("Reçete kodu zorunludur!", "WARNING")
            return

        # Genel veriler
        data = {
            "code": self.code_input.text(),
            "name": self.name_input.text(),
            "description": self.desc_input.toPlainText(),
            "item_id": self.item_combo.currentData(),
            "status": self.status_combo.currentData(),
            "bom_type": self.type_combo.currentData(),
            "base_quantity": Decimal(str(self.base_qty_input.value())),
            "unit_id": self.unit_combo.currentData(),
            "revision": self.revision_input.text(),
            "labor_cost": Decimal(str(self.labor_cost_input.value())),
            "overhead_cost": Decimal(str(self.overhead_cost_input.value())),
            "lines": [],
            "operations": [],
        }

        # Satırlar
        for row in range(self.lines_table.rowCount()):
            line = {
                "item_id": self.lines_table.cellWidget(row, 0).currentData(),
                "quantity": Decimal(str(self.lines_table.cellWidget(row, 1).value())),
                "unit_id": self.lines_table.cellWidget(row, 2).currentData(),
                "scrap_rate": Decimal(str(self.lines_table.cellWidget(row, 3).value())),
                "unit_cost": Decimal(self.lines_table.item(row, 4).text()),
                "line_cost": Decimal(self.lines_table.item(row, 5).text()),
            }
            data["lines"].append(line)

        # Operasyonlar
        for row in range(self.ops_table.rowCount()):
            op = {
                "operation_no": (row + 1) * 10,
                "name": self.ops_table.cellWidget(row, 0).text(),
                "work_station_id": self.ops_table.cellWidget(row, 1).currentData(),
                "setup_time": int(self.ops_table.cellWidget(row, 2).value()),
                "run_time": int(self.ops_table.cellWidget(row, 3).value()),
                "description": self.ops_table.cellWidget(row, 5).text(),
            }
            data["operations"].append(op)

        self.saved.emit(data)
