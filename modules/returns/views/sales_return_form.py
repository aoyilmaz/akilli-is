"""
Akıllı İş - Satış İade Formu
"""

from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any
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

from database.models.returns import ReturnReason, ReturnStatus


class SalesOrderSelectorDialog(QDialog):
    """Satış Siparişi Seçim Dialogu"""

    def __init__(self, orders: list, parent=None):
        super().__init__(parent)
        self.orders = orders
        self.selected_order = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("İade Edilecek Siparişi Seç")
        self.setMinimumSize(700, 450)
        layout = QVBoxLayout(self)

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara... (sipariş no, müşteri)")
        self.search_input.textChanged.connect(self._on_search)
        layout.addWidget(self.search_input)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Sipariş No", "Tarih", "Müşteri", "Tutar"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.table.doubleClicked.connect(self._on_double_click)

        self._load_orders()
        layout.addWidget(self.table)

        # Butonlar
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _load_orders(self):
        self.table.setRowCount(0)
        for row, order in enumerate(self.orders):
            self.table.insertRow(row)

            item_no = QTableWidgetItem(order.get("order_no", ""))
            item_no.setData(Qt.ItemDataRole.UserRole, order)
            self.table.setItem(row, 0, item_no)

            dt = order.get("order_date")
            if isinstance(dt, date):
                dt = dt.strftime("%d.%m.%Y")
            self.table.setItem(row, 1, QTableWidgetItem(str(dt)))

            self.table.setItem(
                row, 2, QTableWidgetItem(order.get("customer_name", "") or "-")
            )

            total = order.get("total_amount", 0)
            self.table.setItem(row, 3, QTableWidgetItem(f"{total:,.2f}"))

    def _on_search(self, text: str):
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(3):
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
                self.selected_order = item.data(Qt.ItemDataRole.UserRole)
                self.accept()


class SalesReturnFormPage(QWidget):
    """Satış İade Formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()
    approve_clicked = pyqtSignal(int)

    def __init__(
        self,
        return_data: Optional[dict] = None,
        orders: list = None,  # List of selectable sales orders
        items: list = None,
        customers: list = None,
        warehouses: list = None,
        parent=None,
    ):
        super().__init__(parent)
        self.return_data = return_data
        self.is_edit_mode = return_data is not None
        self.orders = orders or []
        self.items = items or []
        self.customers = customers or []
        self.warehouses = warehouses or []
        self.selected_order = None

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

        title_text = "İade Düzenle" if self.is_edit_mode else "Yeni Satış İadesi"
        title = QLabel(f"↩️ {title_text}")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        if self.is_edit_mode and self.return_data.get("status") == ReturnStatus.DRAFT:
            approve_btn = QPushButton("✅ İadeyi Onayla")
            approve_btn.clicked.connect(self._on_approve)
            header_layout.addWidget(approve_btn)

        save_btn = QPushButton("💾 Kaydet")
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

        # İade No
        general_layout.addWidget(self._create_label("İade No"), row, 0)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Otomatik")
        self.code_input.setReadOnly(True)
        general_layout.addWidget(self.code_input, row, 1)
        row += 1

        # Tarih
        general_layout.addWidget(self._create_label("İade Tarihi *"), row, 0)
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        general_layout.addWidget(self.date_input, row, 1)
        row += 1

        # Kaynak Sipariş Seçimi (Sadece Yeni Kayıtta aktif olabilir)
        general_layout.addWidget(self._create_label("Kaynak Sipariş"), row, 0)
        order_layout = QHBoxLayout()
        self.order_input = QLineEdit()
        self.order_input.setPlaceholderText("Sipariş seçin...")
        self.order_input.setReadOnly(True)
        order_layout.addWidget(self.order_input)

        select_order_btn = QPushButton("🔍")
        select_order_btn.clicked.connect(self._select_order)
        # Edit modunda sipariş değiştirilemez
        if self.is_edit_mode:
            select_order_btn.setEnabled(False)
        order_layout.addWidget(select_order_btn)
        general_layout.addLayout(order_layout, row, 1)
        row += 1

        # Müşteri (Otomatik gelir siparişten)
        general_layout.addWidget(self._create_label("Müşteri"), row, 0)
        self.customer_input = QLineEdit()
        self.customer_input.setReadOnly(True)
        general_layout.addWidget(self.customer_input, row, 1)
        row += 1

        # Açıklama
        general_layout.addWidget(self._create_label("Açıklama"), row, 0)
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(60)
        general_layout.addWidget(self.desc_input, row, 1)

        general_frame.layout().addLayout(general_layout)
        scroll_layout.addWidget(general_frame)

        # === İADE KALEMLERİ ===
        items_frame = self._create_section("📦 İade Kalemleri")
        items_layout = QVBoxLayout()

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(8)
        self.items_table.setHorizontalHeaderLabels(
            [
                "Stok Kodu",
                "Stok Adı",
                "İade Miktarı",
                "Birim",
                "Birim Fiyat",
                "İade Nedeni",
                "Durum",
                "İşlem",
            ]
        )
        self.items_table.verticalHeader().setVisible(False)
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        items_layout.addWidget(self.items_table)
        items_frame.layout().addLayout(items_layout)
        scroll_layout.addWidget(items_frame)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def _create_section(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("background-color: #1e293b; border-radius: 8px;")
        layout = QVBoxLayout(frame)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #bae6fd;")
        layout.addWidget(title_label)
        return frame

    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return label

    def _select_order(self):
        """Sipariş seç ve kalemleri doldur"""
        if not self.orders:
            QMessageBox.warning(self, "Uyarı", "Seçilebilir sipariş bulunamadı.")
            return

        dialog = SalesOrderSelectorDialog(self.orders, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_order:
            self.selected_order = dialog.selected_order
            self._populate_from_order(self.selected_order)

    def _populate_from_order(self, order: dict):
        """Sipariş bilgilerini ve kalemlerini forma doldur"""
        self.order_input.setText(f"{order.get('order_no')} - {order.get('date', '')}")
        self.customer_input.setText(order.get("customer_name", ""))

        # Customer ID sakla
        self.selected_order["customer_id"] = order.get("customer_id")

        # Kalemleri temizle ve doldur
        self.items_table.setRowCount(0)
        items = order.get("items", [])  # Sipariş kalemleri gelmeli

        for item in items:
            self._add_item_row(item)

    def _add_item_row(self, item_data: dict):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        # Stok Kodu
        self.items_table.setItem(row, 0, QTableWidgetItem(item_data.get("code", "")))

        # Stok Adı
        name_item = QTableWidgetItem(item_data.get("name", ""))
        name_item.setData(
            Qt.ItemDataRole.UserRole, item_data.get("item_id")
        )  # Item ID sakla
        self.items_table.setItem(row, 1, name_item)

        # Miktar (Editable)
        qty = float(item_data.get("quantity", 0))
        qty_spin = QDoubleSpinBox()
        qty_spin.setRange(0, qty)  # Sipariş miktarından fazla iade edilemez
        qty_spin.setValue(qty)
        self.items_table.setCellWidget(row, 2, qty_spin)

        # Birim
        self.items_table.setItem(
            row, 3, QTableWidgetItem(item_data.get("unit_name", ""))
        )

        # Fiyat (Read-only from order)
        price = float(item_data.get("unit_price", 0))
        self.items_table.setItem(row, 4, QTableWidgetItem(f"{price:,.2f}"))

        # İade Nedeni
        reason_combo = QComboBox()
        # Enum değerlerini doldur (hardcoded for now or from ReturnReason)
        # Assuming ReturnReason is available or just strings
        reasons = ["DEFECTIVE", "WRONG_ITEM", "DAMAGED_IN_TRANSIT", "OTHER"]
        reason_combo.addItems(reasons)
        self.items_table.setCellWidget(row, 5, reason_combo)

        # Durum
        condition_combo = QComboBox()
        conditions = ["DAMAGED", "OPENED", "UNOPENED"]
        condition_combo.addItems(conditions)
        self.items_table.setCellWidget(row, 6, condition_combo)

        # Sil Butonu
        del_btn = QPushButton("🗑")
        del_btn.clicked.connect(lambda: self.items_table.removeRow(row))
        self.items_table.setCellWidget(row, 7, del_btn)

    def load_data(self):
        """Mevcut iade verisini yükle"""
        if not self.return_data:
            return

        self.code_input.setText(self.return_data.get("code"))
        # Date, Customer, Desc populate...
        # Items populate loop...
        # TODO: Implement proper edit loading logic similar above
        pass

    def _on_save(self):
        """Form verilerini topla ve sinyal gönder"""
        if not self.selected_order and not self.is_edit_mode:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir kaynak sipariş seçin.")
            return

        items_data = []
        for row in range(self.items_table.rowCount()):
            qty_widget = self.items_table.cellWidget(row, 2)
            qty = qty_widget.value()

            if qty > 0:
                name_item = self.items_table.item(row, 1)
                item_id = name_item.data(Qt.ItemDataRole.UserRole)

                reason_widget = self.items_table.cellWidget(row, 5)
                condition_widget = self.items_table.cellWidget(row, 6)

                items_data.append(
                    {
                        "item_id": item_id,
                        "quantity": qty,
                        "reason": reason_widget.currentText(),
                        "condition": condition_widget.currentText(),
                        "warehouse_id": 1,  # Varsayılan depo ID, TODO: Depo seçimi ekle
                    }
                )

        if not items_data:
            QMessageBox.warning(self, "Uyarı", "En az bir kalem iade edilmeli.")
            return

        data = {
            "return_date": self.date_input.date().toPyDate(),
            "description": self.desc_input.toPlainText(),
            "lines": items_data,
        }

        if not self.is_edit_mode:
            data["order_id"] = self.selected_order.get("id")

        self.saved.emit(data)

    def _on_approve(self):
        if self.return_data:
            reply = QMessageBox.question(
                self, "Onay", "İadeyi onaylamak istiyor musunuz?"
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.approve_clicked.emit(self.return_data.get("id"))
