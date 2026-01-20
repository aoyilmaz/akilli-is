"""
Akıllı İş - SSCC (Taşıma Birimi) Form Sayfası
"""

from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QMessageBox,
    QTextEdit,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon

from config import COLORS
from database.models import TransportUnitType, TransportUnitStatus
from ui.components import PageHeader


class SSCCFormPage(QWidget):
    """Taşıma Birimi (SSCC) Ekleme/Düzenleme Formu"""

    # Sinyaller
    save_clicked = pyqtSignal(dict)  # Kayıt verisi döner
    cancel_clicked = pyqtSignal()
    add_item_clicked = pyqtSignal(dict)  # Ürün ekleme isteği
    remove_item_clicked = pyqtSignal(int)  # Ürün çıkarma isteği (item_id veya index)
    close_unit_clicked = pyqtSignal(int)  # Birimi kapatma isteği

    def __init__(self, parent=None):
        super().__init__(parent)
        self.unit_id = None
        self.current_unit_data = None
        self.unit_items = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Yeni Taşıma Birimi",
            icon="📦",
            show_back=True,
            parent=self,
        )
        self.header.back_clicked.connect(self.cancel_clicked.emit)
        layout.addWidget(self.header)

        # Ana içerik (Splitter yerine HBoxLayout kullanalım şimdilik)
        content_layout = QHBoxLayout()

        # Sol Taraf: Birim Bilgileri
        left_layout = QVBoxLayout()

        # Kart bilgileri grubu
        info_group = QGroupBox("Birim Bilgileri")
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.sscc_label = QLabel("-")
        self.sscc_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #6366f1;"
        )
        form_layout.addRow("SSCC:", self.sscc_label)

        self.type_combo = QComboBox()
        for t in TransportUnitType:
            self.type_combo.addItem(t.value, t)
        form_layout.addRow("Tip:", self.type_combo)

        # Depo Seçimi
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.addItem("Seçiniz...", None)
        form_layout.addRow("Depo:", self.warehouse_combo)

        # Lokasyon Seçimi
        self.location_combo = QComboBox()
        self.location_combo.addItem("-", None)
        self.location_combo.setEnabled(False)
        form_layout.addRow("Konum:", self.location_combo)

        # Notlar
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Notlar...")
        form_layout.addRow("Notlar:", self.notes_input)

        info_group.setLayout(form_layout)
        left_layout.addWidget(info_group)

        # Boyut Bilgileri (Opsiyonel)
        dim_group = QGroupBox("Fiziksel Özellikler")
        dim_layout = QFormLayout()

        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0, 10000)
        self.weight_input.setSuffix(" kg")
        dim_layout.addRow("Brüt Ağırlık:", self.weight_input)

        # H x W x L
        dims_h_layout = QHBoxLayout()
        self.length_input = QDoubleSpinBox()
        self.length_input.setSuffix(" cm")
        self.length_input.setPrefix("L: ")
        dims_h_layout.addWidget(self.length_input)

        self.width_input = QDoubleSpinBox()
        self.width_input.setSuffix(" cm")
        self.width_input.setPrefix("W: ")
        dims_h_layout.addWidget(self.width_input)

        self.height_input = QDoubleSpinBox()
        self.height_input.setSuffix(" cm")
        self.height_input.setPrefix("H: ")
        dims_h_layout.addWidget(self.height_input)

        dim_layout.addRow("Boyutlar:", dims_h_layout)
        dim_group.setLayout(dim_layout)
        left_layout.addWidget(dim_group)

        left_layout.addStretch()

        # Kaydet Butonu
        self.save_btn = QPushButton("💾 Kaydet")
        self.save_btn.setProperty("class", "primary")
        self.save_btn.clicked.connect(self._on_save)
        left_layout.addWidget(self.save_btn)

        # Birimi Kapat Butonu (Sadece düzenlemede görünür)
        self.close_unit_btn = QPushButton("🔒 Birimi Kapat / Paketle")
        self.close_unit_btn.setProperty("class", "warning")
        self.close_unit_btn.clicked.connect(self._on_close_unit)
        self.close_unit_btn.setVisible(False)
        left_layout.addWidget(self.close_unit_btn)

        content_layout.addLayout(left_layout, 1)

        # Sağ Taraf: İçerik Listesi ve Ekleme
        right_layout = QVBoxLayout()

        # Ürün Ekleme Paneli
        add_frame = QFrame()
        add_frame.setProperty("class", "card")
        add_layout = QHBoxLayout(add_frame)
        add_layout.setContentsMargins(12, 12, 12, 12)

        # Stok Seçimi
        add_layout.addWidget(QLabel("Ürün:"))
        self.item_combo = QComboBox()
        self.item_combo.setEditable(True)
        self.item_combo.setMinimumWidth(200)
        add_layout.addWidget(self.item_combo, 1)

        # Miktar
        add_layout.addWidget(QLabel("Miktar:"))
        self.qty_input = QDoubleSpinBox()
        self.qty_input.setRange(0.0001, 999999)
        self.qty_input.setDecimals(2)
        self.qty_input.setValue(1)
        add_layout.addWidget(self.qty_input)

        self.add_item_btn = QPushButton("➕ Ekle")
        self.add_item_btn.clicked.connect(self._on_add_item)
        add_layout.addWidget(self.add_item_btn)

        right_layout.addWidget(add_frame)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Ürün Kodu", "Ürün Adı", "Miktar", "Birim", "Lot No", ""]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        right_layout.addWidget(self.table)

        content_layout.addLayout(right_layout, 2)
        layout.addLayout(content_layout)

    def set_warehouses(self, warehouses):
        self.warehouse_combo.clear()
        self.warehouse_combo.addItem("Seçiniz...", None)
        for w in warehouses:
            self.warehouse_combo.addItem(w.name, w.id)

    def set_items(self, items):
        self.item_combo.clear()
        self.item_combo.addItem("Ürün seçiniz...", None)
        for item in items:
            self.item_combo.addItem(f"{item.code} - {item.name}", item.id)

    def load_unit(self, unit=None, items=None):
        """Formu yükle"""
        if unit:
            self.unit_id = unit.id
            self.current_unit_data = unit
            self.header.set_title(f"Düzenle: {unit.sscc}")
            self.sscc_label.setText(unit.sscc)

            idx = self.type_combo.findData(unit.unit_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)

            idx = self.warehouse_combo.findData(unit.warehouse_id)
            if idx >= 0:
                self.warehouse_combo.setCurrentIndex(idx)

            self.notes_input.setText(unit.notes or "")
            self.weight_input.setValue(float(unit.gross_weight_kg or 0))
            self.length_input.setValue(float(unit.length_cm or 0))
            self.width_input.setValue(float(unit.width_cm or 0))
            self.height_input.setValue(float(unit.height_cm or 0))

            # Duruma göre butonları ayarla
            if unit.status == TransportUnitStatus.ACIK:
                self.close_unit_btn.setVisible(True)
                self.add_item_btn.setEnabled(True)
                self.save_btn.setEnabled(True)
            else:
                self.close_unit_btn.setVisible(False)
                self.add_item_btn.setEnabled(False)
                self.save_btn.setEnabled(False)  # Kapalı birim düzenlenemez (şimdilik)

            self.unit_items = items or []
            self._refresh_table()

        else:
            # Yeni kayıt
            self.unit_id = None
            self.current_unit_data = None
            self.header.set_title("Yeni Taşıma Birimi")
            self.sscc_label.setText("(Otomatik Oluşturulacak)")
            self.type_combo.setCurrentIndex(0)
            self.warehouse_combo.setCurrentIndex(0)
            self.notes_input.clear()
            self.weight_input.setValue(0)
            self.length_input.setValue(0)
            self.width_input.setValue(0)
            self.height_input.setValue(0)

            self.close_unit_btn.setVisible(False)
            self.add_item_btn.setEnabled(False)  # Önce kaydedilmeli
            self.save_btn.setEnabled(True)
            self.unit_items = []
            self._refresh_table()

    def _refresh_table(self):
        self.table.setRowCount(0)
        for i, item in enumerate(self.unit_items):
            self.table.insertRow(i)

            # Ürün bilgileri item.item üzerinden veya dict ise ona göre
            # item bir model objesi ise:
            code = item.item.code if item.item else "-"
            name = item.item.name if item.item else "-"
            unit_name = item.unit.code if item.unit else "-"

            self.table.setItem(i, 0, QTableWidgetItem(code))
            self.table.setItem(i, 1, QTableWidgetItem(name))
            self.table.setItem(i, 2, QTableWidgetItem(f"{item.quantity:.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(unit_name))
            self.table.setItem(i, 4, QTableWidgetItem(item.lot_number or "-"))

            # Sil butonu (Sadece açık ise)
            if (
                self.current_unit_data
                and self.current_unit_data.status == TransportUnitStatus.ACIK
            ):
                del_btn = QPushButton("🗑")
                del_btn.setFixedSize(30, 24)
                del_btn.setStyleSheet("color: red; border: none;")
                del_btn.clicked.connect(
                    lambda checked, row=i: self._on_remove_item(row)
                )
                self.table.setCellWidget(i, 5, del_btn)

    def _on_save(self):
        data = {
            "unit_type": self.type_combo.currentData(),
            "warehouse_id": self.warehouse_combo.currentData(),
            "notes": self.notes_input.toPlainText(),
            "gross_weight_kg": Decimal(str(self.weight_input.value())),
            "length_cm": Decimal(str(self.length_input.value())),
            "width_cm": Decimal(str(self.width_input.value())),
            "height_cm": Decimal(str(self.height_input.value())),
        }
        self.save_clicked.emit(data)

    def _on_add_item(self):
        item_id = self.item_combo.currentData()
        if not item_id:
            QMessageBox.warning(self, "Hata", "Lütfen bir ürün seçin.")
            return

        qty = self.qty_input.value()
        if qty <= 0:
            QMessageBox.warning(self, "Hata", "Miktar 0'dan büyük olmalı.")
            return

        # Ürün ekleme isteği gönder
        data = {
            "item_id": item_id,
            "quantity": Decimal(str(qty)),
            # Lot, birim vs. eklenebilir
        }
        self.add_item_clicked.emit(data)

        # Formu temizle
        self.qty_input.setValue(1)

    def _on_remove_item(self, row):
        if row < 0 or row >= len(self.unit_items):
            return

        item = self.unit_items[row]
        reply = QMessageBox.question(
            self,
            "Onay",
            "Bu kalemi paletten çıkarmak istiyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.remove_item_clicked.emit(item.id)

    def _on_close_unit(self):
        if not self.unit_id:
            return

        reply = QMessageBox.question(
            self,
            "Onay",
            "Bu taşıma birimini kapatmak/paketlemek istiyor musunuz?\nBirim kapatıldıktan sonra içerik değiştirilemez.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.close_unit_clicked.emit(self.unit_id)
