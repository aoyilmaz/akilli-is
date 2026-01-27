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
    QTabWidget,
    QFormLayout,
    QDialog,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QSizePolicy,
    QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from ui.components import CurrencyInput

from ui.components.toast import show_toast
from ui.components.page_header import PageHeader
from database.models.production import BOMStatus, BOMType


class SelectionDialog(QDialog):
    """Basit arama ve seçim diyaloğu"""

    def __init__(self, items, title="Seçim Yapın", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)
        self.items = items  # list of (id, text) tuples
        self.selected_id = None

        layout = QVBoxLayout(self)

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara...")
        self.search_input.textChanged.connect(self.filter_items)
        layout.addWidget(self.search_input)

        # Liste
        self.list_widget = QListWidget()
        self.populate_list(self.items)
        self.list_widget.itemDoubleClicked.connect(self.accept_selection)
        layout.addWidget(self.list_widget)

        # Butonlar
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def populate_list(self, items_to_show):
        self.list_widget.clear()
        for id_val, text in items_to_show:
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, id_val)
            self.list_widget.addItem(item)

    def filter_items(self, text):
        search_text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(search_text not in item.text().lower())

    def accept_selection(self):
        if self.list_widget.currentItem():
            self.selected_id = self.list_widget.currentItem().data(
                Qt.ItemDataRole.UserRole
            )
            self.accept()


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
        self.selected_item_id = None

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
        main_layout = QHBoxLayout(widget)
        main_layout.setSpacing(24)

        # --- Sol Kolon (Ayarlar/Parametreler) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)

        # 1. Durum
        self.status_combo = QComboBox()
        for label, val in self.STATUS_OPTS:
            self.status_combo.addItem(label, val)
        left_layout.addLayout(self._create_v_field("Durum", self.status_combo))

        # 2. Reçete Tipi
        self.type_combo = QComboBox()
        for label, val in self.TYPE_OPTS:
            self.type_combo.addItem(label, val)
        left_layout.addLayout(self._create_v_field("Reçete Tipi", self.type_combo))

        # 3. Baz Miktar
        self.base_qty_input = QDoubleSpinBox()
        self.base_qty_input.setRange(0.0001, 999999)
        self.base_qty_input.setValue(1.0)
        self.base_qty_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        left_layout.addLayout(self._create_v_field("Baz Miktar", self.base_qty_input))

        # 4. Birim
        self.unit_combo = QComboBox()
        self.unit_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        left_layout.addLayout(self._create_v_field("Birim", self.unit_combo))

        left_layout.addStretch()
        main_layout.addWidget(left_widget, stretch=1)

        # --- Sağ Kolon (Ana Bilgiler) ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)

        # 1. Reçete Kodu
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("BOM-0001")
        right_layout.addLayout(self._create_v_field("Reçete Kodu *", self.code_input))

        # 2. Versiyon ve Revizyon (Yan Yana)
        ver_rev_layout = QHBoxLayout()
        ver_rev_layout.setSpacing(16)

        self.version_input = QLineEdit("1")
        self.version_input.setReadOnly(True)
        ver_rev_layout.addLayout(self._create_v_field("Versiyon", self.version_input))

        self.revision_input = QLineEdit("A")
        ver_rev_layout.addLayout(self._create_v_field("Revizyon", self.revision_input))

        right_layout.addLayout(ver_rev_layout)

        # 3. Reçete Adı
        self.name_input = QLineEdit()
        right_layout.addLayout(self._create_v_field("Reçete Adı *", self.name_input))

        # 4. Ürün
        self.item_display = QLineEdit()
        self.item_display.setReadOnly(True)
        self.item_display.setPlaceholderText("Ürün seçiniz...")
        self.item_display.setFixedHeight(32)

        select_btn = QPushButton("🔍")
        select_btn.setFixedSize(32, 32)
        select_btn.clicked.connect(self._open_product_selection)

        prod_layout = QHBoxLayout()
        prod_layout.addWidget(self.item_display)
        prod_layout.addWidget(select_btn)
        prod_layout.setContentsMargins(0, 0, 0, 0)

        prod_container = QWidget()
        prod_container.setLayout(prod_layout)
        prod_container.setFixedHeight(32)

        right_layout.addLayout(self._create_v_field("Ürün *", prod_container))

        # 5. Açıklama
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(100)
        right_layout.addLayout(self._create_v_field("Açıklama", self.desc_input))

        right_layout.addStretch()
        main_layout.addWidget(right_widget, stretch=2)

        return widget

    def _create_v_field(self, label_text, widget, stretch=1):
        """Helper to create Label above Widget layout"""
        lay = QVBoxLayout()
        lay.setSpacing(5)
        label = QLabel(label_text)
        label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        lay.addWidget(label)
        lay.addWidget(widget)
        if isinstance(widget, QWidget):
            # Tek satırlık input'lar için sabit yükseklik (CSS ile zorla)
            if isinstance(widget, (QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox)):
                widget.setFixedHeight(32)
                widget.setStyleSheet(
                    widget.styleSheet() + " min-height: 32px; max-height: 32px;"
                )

            # Ensure widget expands horizontally if possible
            widget.setSizePolicy(
                QSizePolicy.Policy.Expanding, widget.sizePolicy().verticalPolicy()
            )

        # Container wrapper needed to return a layout? No, return layout directly is fine for addLayout
        # But addLayout doesn't take stretch easily in one go unless we wrap.
        # Ideally we return the layout and the caller uses addLayout(lay, stretch)

        # Actually simplest is to return a QVBoxLayout and let caller handle it.
        # But wait, QLayout cannot be a child of another QLayout directly with stretch easily in standard calls sometimes.
        # But addLayout(layout, stretch) works.

        # Let's verify _create_v_field usage. I am doing row_layout.addLayout(...).

        return lay

    def _open_product_selection(self):
        """Ürün seçimi için diyaloğu aç"""
        items_list = [(i.id, f"{i.code} - {i.name}") for i in self.items_map.values()]
        dialog = SelectionDialog(items_list, title="Ürün Seç", parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_id:
            self.selected_item_id = dialog.selected_id
            item = self.items_map.get(self.selected_item_id)
            if item:
                self.item_display.setText(f"{item.code} - {item.name}")
                # Birim otomatik seçilsin
                if item.unit_id:
                    idx = self.unit_combo.findData(item.unit_id)
                    if idx >= 0:
                        self.unit_combo.setCurrentIndex(idx)

    def _create_materials_tab(self) -> QWidget:
        """Malzeme listesi (BOM Lines)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Araç çubuğu
        toolbar = QHBoxLayout()
        add_line_btn = QPushButton("➕ Malzeme Ekle")
        add_line_btn.clicked.connect(lambda: self._add_material_line(None))

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
        add_op_btn.clicked.connect(lambda: self._add_operation_line(None))

        remove_op_btn = QPushButton("🗑️ Operasyon Sil")
        remove_op_btn.clicked.connect(self._remove_selected_operation)

        toolbar.addWidget(add_op_btn)
        toolbar.addWidget(remove_op_btn)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        # Tablo
        self.ops_table = QTableWidget()
        self.ops_table.setColumnCount(7)
        self.ops_table.setHorizontalHeaderLabels(
            [
                "Operasyon Adı",
                "İş İstasyonu",
                "Kurulum (dk)",
                "Birim Süre (dk)",
                "Maliyet",
                "K.K.",
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

        self.labor_cost_input = CurrencyInput()
        layout.addRow("İşçilik/Operasyon Maliyeti:", self.labor_cost_input)

        self.overhead_cost_input = CurrencyInput()
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

        self.stations_map = {s.id: s for s in stations}

        # item_combo kaldırıldı, sadece map güncelleniyor.

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

        # Ürün seçimini yükle
        if self.bom.item_id:
            self.selected_item_id = self.bom.item_id
            item = self.items_map.get(self.bom.item_id)
            if item:
                self.item_display.setText(f"{item.code} - {item.name}")

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

        selected_item_id = None

        # Eğer manuel ekleme yapılıyorsa (line_data yoksa), diyalog aç
        if line_data is None:
            items_list = [
                (i.id, f"{i.code} - {i.name}") for i in self.items_map.values()
            ]
            dialog = SelectionDialog(items_list, title="Malzeme Seç", parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_id:
                selected_item_id = dialog.selected_id
            else:
                return  # İptal edildi

        row = self.lines_table.rowCount()
        self.lines_table.insertRow(row)
        self.lines_table.setRowHeight(row, 42)  # Satır yüksekliği

        # Malzeme Seçimi (Combo)
        combo = QComboBox()
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        for item_id, item in self.items_map.items():
            combo.addItem(f"{item.code} - {item.name}", item_id)

        # Veri set et
        if line_data:
            idx = combo.findData(line_data.item_id)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        elif selected_item_id:
            idx = combo.findData(selected_item_id)
            if idx >= 0:
                combo.setCurrentIndex(idx)

        self.lines_table.setCellWidget(row, 0, combo)

        # Miktar
        qty_spin = QDoubleSpinBox()
        qty_spin.setRange(0, 999999)
        qty_spin.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        qty_spin.setValue(float(line_data.quantity) if line_data else 1.0)
        self.lines_table.setCellWidget(row, 1, qty_spin)

        # Birim (Combo)
        unit_combo = QComboBox()
        unit_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        for u_id, u_code in self.units_map.items():
            unit_combo.addItem(u_code, u_id)

        if line_data:
            idx = unit_combo.findData(line_data.unit_id)
            if idx >= 0:
                unit_combo.setCurrentIndex(idx)
        elif selected_item_id:
            # Seçilen ürünün birimini default yap
            item = self.items_map.get(selected_item_id)
            if item and item.unit_id:
                idx = unit_combo.findData(item.unit_id)
                if idx >= 0:
                    unit_combo.setCurrentIndex(idx)

        self.lines_table.setCellWidget(row, 2, unit_combo)

        # Fire
        scrap_spin = QDoubleSpinBox()
        scrap_spin.setRange(0, 100)
        scrap_spin.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        scrap_spin.setValue(float(line_data.scrap_rate) if line_data else 0.0)
        self.lines_table.setCellWidget(row, 3, scrap_spin)

        # Birim Maliyet (Readonly - Item'dan gelecek)
        cost_item = QTableWidgetItem()
        cost_val = 0.0
        if line_data:
            cost_val = float(line_data.unit_cost)
        elif selected_item_id:
            item = self.items_map.get(selected_item_id)
            cost_val = float(item.purchase_price or 0) if item else 0.0

        cost_item.setText(f"{cost_val:.2f}")
        cost_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Readonly
        self.lines_table.setItem(row, 4, cost_item)

        # Toplam Maliyet (Hesaplanan)
        total_item = QTableWidgetItem("0.00")
        total_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.lines_table.setItem(row, 5, total_item)

        # Yeni satır eklendiğinde maliyetleri güncelle
        self._calculate_totals()

    def _add_operation_line(self, op_data=None):
        """Tabloya yeni operasyon satırı ekle"""

        selected_station_id = None

        # Manuel ekleme ise dialog aç
        if op_data is None:
            stations_list = [
                (s.id, f"{s.code} - {s.name}") for s in self.stations_map.values()
            ]
            dialog = SelectionDialog(
                stations_list, title="İş İstasyonu Seç", parent=self
            )
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_id:
                selected_station_id = dialog.selected_id
            else:
                return  # İptal

        row = self.ops_table.rowCount()
        self.ops_table.insertRow(row)
        self.ops_table.setRowHeight(row, 42)

        # Operasyon Adı
        name_input = QLineEdit()
        name_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        name_input.setText(op_data.name if op_data else "")
        name_input.setPlaceholderText("Örn: Kesim, Montaj")
        self.ops_table.setCellWidget(row, 0, name_input)

        # İstasyon Seçimi
        combo = QComboBox()
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        combo.addItem("Seçiniz...", None)
        for s_id, station in self.stations_map.items():
            combo.addItem(f"{station.code} - {station.name}", s_id)

        if op_data and op_data.work_station_id:
            idx = combo.findData(op_data.work_station_id)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        elif selected_station_id:
            idx = combo.findData(selected_station_id)
            if idx >= 0:
                combo.setCurrentIndex(idx)

        self.ops_table.setCellWidget(row, 1, combo)

        # Süreler
        setup_spin = QSpinBox()  # Dakika
        setup_spin.setRange(0, 9999)
        setup_spin.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        setup_spin.setValue(int(op_data.setup_time) if op_data else 0)
        self.ops_table.setCellWidget(row, 2, setup_spin)

        run_spin = QDoubleSpinBox()  # Dakika/Birim
        run_spin.setRange(0, 9999)
        run_spin.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        run_spin.setValue(float(op_data.run_time) if op_data else 0)
        self.ops_table.setCellWidget(row, 3, run_spin)

        # Maliyet (Hesaplanan - Gösterimlik)
        cost_item = QTableWidgetItem("0.00")
        cost_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.ops_table.setItem(row, 4, cost_item)

        # QC Checkbox
        qc_widget = QWidget()
        qc_layout = QHBoxLayout(qc_widget)
        qc_layout.setContentsMargins(0, 0, 0, 0)
        qc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        qc_check = QCheckBox()
        qc_check.setChecked(bool(op_data.requires_qc) if op_data else False)
        qc_layout.addWidget(qc_check)
        self.ops_table.setCellWidget(row, 5, qc_widget)

        # Açıklama
        desc_input = QLineEdit()
        desc_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        desc_input.setText(op_data.description if op_data else "")
        self.ops_table.setCellWidget(row, 6, desc_input)

        self._calculate_totals()

    def _remove_selected_material(self):
        """Seçili malzeme satırını sil"""
        current_row = self.lines_table.currentRow()
        if current_row >= 0:
            self.lines_table.removeRow(current_row)
            self._calculate_totals()

    def _remove_selected_operation(self):
        """Seçili operasyon satırını sil"""
        current_row = self.ops_table.currentRow()
        if current_row >= 0:
            self.ops_table.removeRow(current_row)
            self._calculate_totals()

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
            if not station_combo:
                continue

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
            "item_id": self.selected_item_id,
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
            # QC Checkbox reading
            qc_widget = self.ops_table.cellWidget(row, 5)
            qc_check = qc_widget.findChild(QCheckBox)
            requires_qc = qc_check.isChecked() if qc_check else False

            op = {
                "operation_no": (row + 1) * 10,
                "name": self.ops_table.cellWidget(row, 0).text(),
                "work_station_id": self.ops_table.cellWidget(row, 1).currentData(),
                "setup_time": int(self.ops_table.cellWidget(row, 2).value()),
                "run_time": int(self.ops_table.cellWidget(row, 3).value()),
                "requires_qc": requires_qc,
                "description": self.ops_table.cellWidget(row, 6).text(),
            }
            data["operations"].append(op)

        self.saved.emit(data)
