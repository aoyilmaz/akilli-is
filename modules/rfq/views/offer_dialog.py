from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDateEdit,
    QPushButton,
    QComboBox,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, QDate
from database.base import get_session
from modules.rfq.services.rfq_service import RFQService
from database.models.purchasing import Supplier


class OfferDialog(QDialog):
    def __init__(self, rfq_id: int, parent=None):
        super().__init__(parent)
        self.rfq_id = rfq_id
        self.service = RFQService(get_session())
        self.rfq = self.service.get_rfq(rfq_id)

        self.setWindowTitle("Tedarikçi Teklifi Ekle")
        self.resize(800, 600)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Supplier Selection
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Tedarikçi:"))

        self.cmb_supplier = QComboBox()
        self.load_suppliers()
        form_layout.addWidget(self.cmb_supplier)

        form_layout.addWidget(QLabel("Geçerlilik:"))
        self.inp_valid_until = QDateEdit()
        self.inp_valid_until.setDate(QDate.currentDate().addDays(30))
        self.inp_valid_until.setCalendarPopup(True)
        form_layout.addWidget(self.inp_valid_until)

        layout.addLayout(form_layout)

        # Items Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Ürün/Hizmet", "Miktar", "Birim Fiyat", "KDV %", "Teslim Tarihi"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )

        layout.addWidget(self.table)

        self.load_items()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("İptal")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Kaydet")
        btn_save.clicked.connect(self.save)
        btn_save.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def load_suppliers(self):
        suppliers = self.service.db.query(Supplier).all()
        for s in suppliers:
            self.cmb_supplier.addItem(s.name, s.id)

    def load_items(self):
        if not self.rfq:
            return

        self.table.setRowCount(0)
        for item in self.rfq.items:
            row = self.table.rowCount()
            self.table.insertRow(row)

            name = item.description or (item.item.name if item.item else "")
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.item(row, 0).setFlags(Qt.ItemFlag.ItemIsEnabled)
            # Quantity
            spin_qty = QDoubleSpinBox()
            spin_qty.setRange(0, 1000000)
            spin_qty.setValue(float(item.quantity or 0))
            self.table.setCellWidget(row, 1, spin_qty)

            # Price
            spin_price = QDoubleSpinBox()
            spin_price.setRange(0, 1000000)
            spin_price.setDecimals(4)
            self.table.setCellWidget(row, 2, spin_price)

            # Tax
            spin_tax = QDoubleSpinBox()
            spin_tax.setRange(0, 100)
            spin_tax.setValue(20)
            self.table.setCellWidget(row, 3, spin_tax)

            # Delivery Date
            date_edit = QDateEdit()
            date_edit.setDate(QDate.currentDate().addDays(7))
            date_edit.setCalendarPopup(True)
            self.table.setCellWidget(row, 4, date_edit)

            # Store RFQ Item ID
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, item.id)

    def save(self):
        supplier_id = self.cmb_supplier.currentData()
        if not supplier_id:
            QMessageBox.warning(self, "Hata", "Tedarikçi seçiniz.")
            return

        items_data = []
        for row in range(self.table.rowCount()):
            rfq_item_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            qty = self.table.cellWidget(row, 1).value()
            price = self.table.cellWidget(row, 2).value()
            tax = self.table.cellWidget(row, 3).value()
            delivery_date = self.table.cellWidget(row, 4).date().toPyDate()

            if price > 0:
                items_data.append(
                    {
                        "rfq_item_id": rfq_item_id,
                        "quantity": qty,
                        "unit_price": price,
                        "tax_rate": tax,
                        "delivery_date": delivery_date,
                    }
                )

        if not items_data:
            QMessageBox.warning(self, "Hata", "En az bir kaleme fiyat giriniz.")
            return

        try:
            offer_data = {"valid_until": self.inp_valid_until.date().toPyDate()}
            self.service.add_offer(self.rfq_id, supplier_id, items_data, offer_data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
