from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from database.base import get_session
from modules.rfq.services.rfq_service import RFQService
from database.models.rfq import SupplierOffer


class CompareDialog(QDialog):
    def __init__(self, rfq_id: int, parent=None):
        super().__init__(parent)
        self.rfq_id = rfq_id
        self.service = RFQService(get_session())

        self.setWindowTitle("Teklif Karşılaştırma")
        self.resize(1000, 600)

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.lbl_info = QLabel(
            "En uygun teklifi seçmek için tablodaki başlığa tıklayıp"
            " 'Siparişe Dönüştür' diyebilirsiniz."
        )
        layout.addWidget(self.lbl_info)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectColumns
        )
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

        # Actions
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_create_po = QPushButton("Seçili Teklifi Siparişe Dönüştür")
        self.btn_create_po.clicked.connect(self.create_po)
        self.btn_create_po.setEnabled(False)
        self.btn_create_po.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 10px;"
        )
        btn_layout.addWidget(self.btn_create_po)

        layout.addLayout(btn_layout)

        self.table.itemSelectionChanged.connect(self.on_selection_changed)

    def load_data(self):
        data = self.service.compare_offers(self.rfq_id)
        if not data:
            return

        items = data["items"]
        suppliers = data["suppliers"]
        self.suppliers = suppliers

        # Headers: Item, Qty, [Sup1 Price, Sup1 Total], [Sup2 Price, Sup2 Total]...
        headers = ["Ürün/Hizmet", "Miktar"]
        for sup in suppliers:
            headers.append(f"{sup['name']}\n(Birim)")
            headers.append(f"{sup['name']}\n(Toplam)")

        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(items))

        for i, item in enumerate(items):
            self.table.setItem(i, 0, QTableWidgetItem(item["description"]))
            self.table.setItem(i, 1, QTableWidgetItem(f"{item['quantity']:.2f}"))

            # Find best price for highlighting
            best_price = float("inf")
            for sup in suppliers:
                offer = item["offers"].get(sup["id"])
                if offer:
                    price = float(offer["unit_price"])
                    if price < best_price:
                        best_price = price

            col_idx = 2
            for sup in suppliers:
                offer = item["offers"].get(sup["id"])
                if offer:
                    price_item = QTableWidgetItem(f"{offer['unit_price']:.2f}")
                    total_item = QTableWidgetItem(f"{offer['line_total']:.2f}")

                    if float(offer["unit_price"]) == best_price:
                        price_item.setBackground(QColor("#e8f5e9"))  # Light Green
                        total_item.setBackground(QColor("#e8f5e9"))

                    self.table.setItem(i, col_idx, price_item)
                    self.table.setItem(i, col_idx + 1, total_item)
                else:
                    self.table.setItem(i, col_idx, QTableWidgetItem("-"))
                    self.table.setItem(i, col_idx + 1, QTableWidgetItem("-"))

                col_idx += 2

    def on_selection_changed(self):
        indexes = self.table.selectedIndexes()
        if not indexes:
            self.btn_create_po.setEnabled(False)
            return

        col = indexes[0].column()
        if col < 2:
            self.btn_create_po.setEnabled(False)
            return

        supplier_idx = (col - 2) // 2
        if 0 <= supplier_idx < len(self.suppliers):
            self.selected_supplier = self.suppliers[supplier_idx]
            self.btn_create_po.setText(
                f"{self.selected_supplier['name']} İçin Sipariş Oluştur"
            )
            self.btn_create_po.setEnabled(True)
        else:
            self.btn_create_po.setEnabled(False)

    def create_po(self):
        if not hasattr(self, "selected_supplier"):
            return

        supplier_id = self.selected_supplier["id"]

        # Find Offer
        offer = (
            self.service.db.query(SupplierOffer)
            .filter_by(rfq_id=self.rfq_id, supplier_id=supplier_id)
            .first()
        )

        if not offer:
            QMessageBox.critical(self, "Hata", "Teklif bulunamadı")
            return

        try:
            self.service.convert_to_order(offer.id)
            QMessageBox.information(
                self, "Başarılı", "Satın alma siparişi oluşturuldu."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
