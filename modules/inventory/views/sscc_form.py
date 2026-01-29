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
    QTableWidgetItem,
    QFrame,
    QMessageBox,
    QTextEdit,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta

from config.icons import ICONS
from database.models import TransportUnitType, TransportUnitStatus
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
)


class SSCCFormPage(QWidget):
    """Taşıma Birimi (SSCC) Ekleme/Düzenleme Formu"""

    save_clicked = pyqtSignal(dict)
    cancel_clicked = pyqtSignal()
    add_item_clicked = pyqtSignal(dict)
    remove_item_clicked = pyqtSignal(int)
    close_unit_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.unit_id = None
        self.unit_data = None
        self.unit_items = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self.header = PageHeader(
            title="Yeni Taşıma Birimi",
            icon=ICONS.INVENTORY,
            show_back=True,
            parent=self,
        )
        self.header.back_clicked.connect(self.cancel_clicked.emit)
        layout.addWidget(self.header)

        cl = QHBoxLayout()
        ll = QVBoxLayout()
        ig = QGroupBox("Birim Bilgileri")
        fl = QFormLayout()
        fl.setSpacing(12)
        self.sscc_lbl = QLabel("-")
        self.sscc_lbl.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #818cf8;"
        )
        fl.addRow("SSCC:", self.sscc_lbl)
        self.type_combo = QComboBox()
        for t in TransportUnitType:
            self.type_combo.addItem(t.value, t)
        fl.addRow("Tip:", self.type_combo)
        self.wh_combo = QComboBox()
        self.wh_combo.addItem("Seçiniz...", None)
        fl.addRow("Depo:", self.wh_combo)
        self.loc_combo = QComboBox()
        self.loc_combo.addItem("-", None)
        self.loc_combo.setEnabled(False)
        fl.addRow("Konum:", self.loc_combo)
        self.notes_in = QTextEdit()
        self.notes_in.setMaximumHeight(80)
        self.notes_in.setPlaceholderText("Notlar...")
        fl.addRow("Notlar:", self.notes_in)
        ig.setLayout(fl)
        ll.addWidget(ig)
        dg = QGroupBox("Fiziksel Özellikler")
        dl = QFormLayout()
        self.weight_in = QDoubleSpinBox()
        self.weight_in.setRange(0, 10000)
        self.weight_in.setSuffix(" kg")
        dl.addRow("Brüt Ağırlık:", self.weight_in)
        dhl = QHBoxLayout()
        self.len_in = QDoubleSpinBox()
        self.len_in.setSuffix(" cm")
        self.len_in.setPrefix("L: ")
        dhl.addWidget(self.len_in)
        self.wid_in = QDoubleSpinBox()
        self.wid_in.setSuffix(" cm")
        self.wid_in.setPrefix("W: ")
        dhl.addWidget(self.wid_in)
        self.hei_in = QDoubleSpinBox()
        self.hei_in.setSuffix(" cm")
        self.hei_in.setPrefix("H: ")
        dhl.addWidget(self.hei_in)
        dl.addRow("Boyutlar:", dhl)
        dg.setLayout(dl)
        ll.addWidget(dg)
        ll.addStretch()
        self.save_btn = QPushButton("Kaydet")
        self.save_btn.setProperty("class", "btn-primary")
        self.save_btn.setIcon(qta.icon(ICONS.SAVE, color="#ffffff"))
        self.save_btn.clicked.connect(self._on_save)
        ll.addWidget(self.save_btn)
        self.close_btn = QPushButton("Birimi Kapat / Paketle")
        self.close_btn.setProperty("class", "btn-warning")
        self.close_btn.setIcon(qta.icon(ICONS.LOCKED, color="#ffffff"))
        self.close_btn.clicked.connect(self._on_close_unit)
        self.close_btn.setVisible(False)
        ll.addWidget(self.close_btn)
        cl.addLayout(ll, 1)
        rl = QVBoxLayout()
        af = QFrame()
        af.setProperty("class", "card")
        al = QHBoxLayout(af)
        al.setContentsMargins(12, 12, 12, 12)
        al.addWidget(QLabel("Ürün:"))
        self.item_combo = QComboBox()
        self.item_combo.setEditable(True)
        self.item_combo.setMinimumWidth(200)
        al.addWidget(self.item_combo, 1)
        al.addWidget(QLabel("Miktar:"))
        self.qty_in = QDoubleSpinBox()
        self.qty_in.setRange(0.0001, 999999)
        self.qty_in.setDecimals(2)
        self.qty_in.setValue(1)
        al.addWidget(self.qty_in)
        self.add_btn = QPushButton("Ekle")
        self.add_btn.setIcon(qta.icon(ICONS.ADD, color="#ffffff"))
        self.add_btn.setProperty("class", "btn-add")
        self.add_btn.clicked.connect(self._on_add_item)
        al.addWidget(self.add_btn)
        rl.addWidget(af)

        cols = [
            ColumnConfig("code", "Ürün Kodu", width=120),
            ColumnConfig("name", "Ürün Adı", stretch=True),
            ColumnConfig("qty", "Miktar", width=100),
            ColumnConfig("unit", "Birim", width=70),
            ColumnConfig("lot", "Lot No", width=120),
            ColumnConfig("actions", "İşlem", width=60),
        ]
        self.table = EnhancedTableWidget(
            table_id="sscc_items", columns=cols, parent=self
        )
        rl.addWidget(self.table)
        cl.addLayout(rl, 2)
        layout.addLayout(cl)

    def set_warehouses(self, whs):
        self.wh_combo.clear()
        self.wh_combo.addItem("Seçiniz...", None)
        for w in whs:
            self.wh_combo.addItem(w.name, w.id)

    def set_items(self, items):
        self.item_combo.clear()
        self.item_combo.addItem("Ürün seçiniz...", None)
        for itm in items:
            self.item_combo.addItem(f"{itm.code} - {itm.name}", itm.id)

    def load_unit(self, unit=None, items=None):
        if unit:
            self.unit_id = unit.id
            self.unit_data = unit
            self.header.set_title(f"Düzenle: {unit.sscc}")
            self.sscc_lbl.setText(unit.sscc)
            idx = self.type_combo.findData(unit.unit_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
            idx = self.wh_combo.findData(unit.warehouse_id)
            if idx >= 0:
                self.wh_combo.setCurrentIndex(idx)
            self.notes_in.setText(unit.notes or "")
            self.weight_in.setValue(float(unit.gross_weight_kg or 0))
            self.len_in.setValue(float(unit.length_cm or 0))
            self.wid_in.setValue(float(unit.width_cm or 0))
            self.hei_in.setValue(float(unit.height_cm or 0))
            if unit.status == TransportUnitStatus.ACIK:
                self.close_btn.setVisible(True)
                self.add_btn.setEnabled(True)
                self.save_btn.setEnabled(True)
            else:
                self.close_btn.setVisible(False)
                self.add_btn.setEnabled(False)
                self.save_btn.setEnabled(False)
            self.unit_items = items or []
            self._refresh_table()
        else:
            self.unit_id = None
            self.unit_data = None
            self.header.set_title("Yeni Taşıma Birimi")
            self.sscc_lbl.setText("(Otomatik Oluşturulacak)")
            self.type_combo.setCurrentIndex(0)
            self.wh_combo.setCurrentIndex(0)
            self.notes_in.clear()
            self.weight_in.setValue(0)
            self.len_in.setValue(0)
            self.wid_in.setValue(0)
            self.hei_in.setValue(0)
            self.close_btn.setVisible(False)
            self.add_btn.setEnabled(False)
            self.save_btn.setEnabled(True)
            self.unit_items = []
            self._refresh_table()

    def _refresh_table(self):
        self.table.setRowCount(len(self.unit_items))
        vc = self.table.get_visible_columns()
        for r, itm in enumerate(self.unit_items):
            for c, k in enumerate(vc):
                if k == "code":
                    self.table.setItem(
                        r, c, QTableWidgetItem(itm.item.code if itm.item else "-")
                    )
                elif k == "name":
                    self.table.setItem(
                        r, c, QTableWidgetItem(itm.item.name if itm.item else "-")
                    )
                elif k == "qty":
                    it = QTableWidgetItem(f"{itm.quantity:.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.table.setItem(r, c, it)
                elif k == "unit":
                    self.table.setItem(
                        r, c, QTableWidgetItem(itm.unit.code if itm.unit else "-")
                    )
                elif k == "lot":
                    self.table.setItem(r, c, QTableWidgetItem(itm.lot_number or "-"))
                elif k == "actions":
                    if (
                        self.unit_data
                        and self.unit_data.status == TransportUnitStatus.ACIK
                    ):
                        btn = QPushButton()
                        btn.setIcon(qta.icon(ICONS.DELETE, color="#ef4444"))
                        btn.setProperty("class", "btn-icon-only")
                        btn.setToolTip("Çıkar")
                        btn.clicked.connect(
                            lambda checked, row=r: self._on_remove_item(row)
                        )
                        self.table.setCellWidget(r, c, btn)

    def _on_save(self):
        data = {
            "unit_type": self.type_combo.currentData(),
            "warehouse_id": self.wh_combo.currentData(),
            "notes": self.notes_in.toPlainText(),
            "gross_weight_kg": Decimal(str(self.weight_in.value())),
            "length_cm": Decimal(str(self.len_in.value())),
            "width_cm": Decimal(str(self.wid_in.value())),
            "height_cm": Decimal(str(self.hei_in.value())),
        }
        self.save_clicked.emit(data)

    def _on_add_item(self):
        iid = self.item_combo.currentData()
        if not iid:
            QMessageBox.warning(self, "Hata", "Lütfen bir ürün seçin.")
            return
        qty = self.qty_in.value()
        if qty <= 0:
            QMessageBox.warning(self, "Hata", "Miktar 0'dan büyük olmalı.")
            return
        self.add_item_clicked.emit({"item_id": iid, "quantity": Decimal(str(qty))})
        self.qty_in.setValue(1)

    def _on_remove_item(self, row):
        if row < 0 or row >= len(self.unit_items):
            return
        if (
            QMessageBox.question(
                self,
                "Onay",
                "Bu kalemi paletten çıkarmak istiyor musunuz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.remove_item_clicked.emit(self.unit_items[row].id)

    def _on_close_unit(self):
        if not self.unit_id:
            return
        msg = "Bu taşıma birimini kapatmak/paketlemek istiyor musunuz?\nBirim kapatıldıktan sonra içerik değiştirilemez."
        if (
            QMessageBox.question(
                self,
                "Onay",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.close_unit_clicked.emit(self.unit_id)
