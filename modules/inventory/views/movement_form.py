"""
Akıllı İş - Stok Hareket Formu (Giriş/Çıkış/Transfer)
"""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime
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
    QFormLayout,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDateTimeEdit,
    QAbstractItemView,
    QCompleter,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime, QStringListModel

from database.models import StockMovementType


class MovementFormPage(QWidget):
    """Stok hareket formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(self, movement_type: str = "entry", parent=None):
        """
        movement_type: 'entry' (giriş), 'exit' (çıkış), 'transfer'
        """
        super().__init__(parent)
        self.movement_type = movement_type
        self.items_data = []  # Stok kartları
        self.warehouses_data = []  # Depolar
        self.lines = []  # Hareket satırları
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık belirle
        titles = {
            "entry": ("📥 Stok Giriş Fişi", "#10b981"),
            "exit": ("📤 Stok Çıkış Fişi", "#ef4444"),
            "transfer": ("🔄 Depo Transfer Fişi", "#6366f1"),
        }
        title_text, title_color = titles.get(
            self.movement_type, ("Stok Hareketi", "#ffffff")
        )

        # === Başlık ===
        header_layout = QHBoxLayout()

        back_btn = QPushButton("← Geri")
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)

        title = QLabel(title_text)
        header_layout.addWidget(title)

        header_layout.addStretch()

        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(self._on_save)
        header_layout.addWidget(save_btn)

        layout.addLayout(header_layout)

        # === Fiş Bilgileri ===
        info_frame = QFrame()
        info_frame.setProperty("class", "card")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(24)

        # Belge No
        doc_layout = QVBoxLayout()
        doc_layout.addWidget(QLabel("Belge No"))
        self.document_no_input = QLineEdit()
        self.document_no_input.setPlaceholderText("Otomatik")
        doc_layout.addWidget(self.document_no_input)
        info_layout.addLayout(doc_layout)

        # Tarih
        date_layout = QVBoxLayout()
        date_layout.addWidget(QLabel("Tarih/Saat"))
        self.datetime_input = QDateTimeEdit()
        self.datetime_input.setDateTime(QDateTime.currentDateTime())
        self.datetime_input.setCalendarPopup(True)
        date_layout.addWidget(self.datetime_input)
        info_layout.addLayout(date_layout)

        # Kaynak Depo (çıkış ve transfer için)
        if self.movement_type in ["exit", "transfer"]:
            from_layout = QVBoxLayout()
            from_layout.addWidget(QLabel("Kaynak Depo *"))
            self.from_warehouse_combo = QComboBox()
            from_layout.addWidget(self.from_warehouse_combo)
            info_layout.addLayout(from_layout)

        # Hedef Depo (giriş ve transfer için)
        if self.movement_type in ["entry", "transfer"]:
            to_layout = QVBoxLayout()
            to_layout.addWidget(QLabel("Hedef Depo *"))
            self.to_warehouse_combo = QComboBox()
            to_layout.addWidget(self.to_warehouse_combo)
            info_layout.addLayout(to_layout)

        # Referans No
        ref_layout = QVBoxLayout()
        ref_layout.addWidget(QLabel("Referans No"))
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Fatura no, sipariş no vb.")
        ref_layout.addWidget(self.reference_input)
        info_layout.addLayout(ref_layout)

        info_layout.addStretch()

        layout.addWidget(info_frame)

        # === Satır Ekleme ===
        add_frame = QFrame()
        add_frame.setProperty("class", "card-secondary")
        add_layout = QHBoxLayout(add_frame)
        add_layout.setContentsMargins(16, 12, 16, 12)
        add_layout.setSpacing(12)

        # Barkod girişi
        add_layout.addWidget(QLabel("Barkod:"))
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Barkod okutun...")
        self.barcode_input.setMaximumWidth(150)
        self.barcode_input.returnPressed.connect(self._on_barcode_scan)
        self.barcode_input.setProperty("class", "barcode-input")
        add_layout.addWidget(self.barcode_input)

        # Stok seçimi
        add_layout.addWidget(QLabel("Stok:"))
        self.item_combo = QComboBox()
        self.item_combo.setEditable(True)
        self.item_combo.setMinimumWidth(300)
        add_layout.addWidget(self.item_combo)

        # Miktar
        add_layout.addWidget(QLabel("Miktar:"))
        self.qty_input = QDoubleSpinBox()
        self.qty_input.setRange(0.0001, 999999999)
        self.qty_input.setDecimals(4)
        self.qty_input.setValue(1)
        add_layout.addWidget(self.qty_input)

        # Birim Fiyat
        add_layout.addWidget(QLabel("Birim Fiyat:"))
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 999999999)
        self.price_input.setDecimals(4)
        self.price_input.setPrefix("₺ ")
        add_layout.addWidget(self.price_input)

        # Lot No
        add_layout.addWidget(QLabel("Lot:"))
        self.lot_input = QLineEdit()
        self.lot_input.setPlaceholderText("Lot no")
        self.lot_input.setMaximumWidth(100)
        add_layout.addWidget(self.lot_input)

        # === Dual-Unit (İkincil Birim) ===
        add_layout.addWidget(QLabel("İkincil Mkt:"))
        self.secondary_qty_input = QDoubleSpinBox()
        self.secondary_qty_input.setRange(0, 999999999)
        self.secondary_qty_input.setDecimals(4)
        self.secondary_qty_input.setSpecialValueText("-")
        self.secondary_qty_input.setToolTip("Örn: 10 koli = 150 kg")
        add_layout.addWidget(self.secondary_qty_input)

        add_layout.addWidget(QLabel("İkincil Birim:"))
        self.secondary_unit_combo = QComboBox()
        self.secondary_unit_combo.setMinimumWidth(80)
        add_layout.addWidget(self.secondary_unit_combo)

        # Ekle butonu
        add_btn = QPushButton("➕ Ekle")
        add_btn.clicked.connect(self._add_line)
        add_layout.addWidget(add_btn)

        layout.addWidget(add_frame)

        # === Satırlar Tablosu ===
        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table)

        # === Alt Bilgi ===
        footer_frame = QFrame()
        footer_frame.setProperty("class", "card")
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(16, 12, 16, 12)

        # Açıklama
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("Açıklama"))
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(60)
        self.description_input.setPlaceholderText("Hareket açıklaması...")
        desc_layout.addWidget(self.description_input)
        footer_layout.addLayout(desc_layout, 2)

        footer_layout.addStretch()

        # Toplam
        total_layout = QVBoxLayout()
        total_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.line_count_label = QLabel("Satır: 0")
        total_layout.addWidget(self.line_count_label)

        self.total_label = QLabel("Toplam: ₺0,00")
        total_layout.addWidget(self.total_label)

        footer_layout.addLayout(total_layout)

        layout.addWidget(footer_frame)

    def _setup_table(self):
        columns = [
            ("Stok Kodu", 100),
            ("Stok Adı", 200),
            ("Miktar", 90),
            ("Birim", 55),
            ("İkincil Mkt", 90),
            ("İkn. Birim", 70),
            ("Birim Fiyat", 100),
            ("Toplam", 110),
            ("Lot No", 90),
            ("", 50),  # Sil butonu
        ]

        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([c[0] for c in columns])

        header = self.table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 1:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                self.table.setColumnWidth(i, width)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        self.table.setProperty("class", "enhanced-table")

    def _on_barcode_scan(self):
        """Barkod okutulduğunda ürünü bul ve seç"""
        barcode = self.barcode_input.text().strip()
        if not barcode:
            return

        # Barkod ile ürün ara
        found = False
        for i in range(self.item_combo.count()):
            item_id = self.item_combo.itemData(i)
            item = self.items_data.get(item_id)
            if item:
                # Kod veya barkod eşleşmesi
                item_code = item.get("code", "")
                item_barcode = item.get("barcode", "")
                if barcode.upper() in [item_code.upper(), item_barcode]:
                    self.item_combo.setCurrentIndex(i)
                    found = True
                    break

        if found:
            self.barcode_input.clear()
            self.qty_input.setFocus()
        else:
            QMessageBox.warning(
                self, "Bulunamadı", f"'{barcode}' barkoduna ait ürün bulunamadı!"
            )
            self.barcode_input.selectAll()

    def load_items(self, items: list):
        """Stok kartlarını yükle"""
        self.items_data = {}
        self.item_combo.clear()
        for item in items:
            # Item bilgilerini dictionary olarak sakla (session bağımsız)
            self.items_data[item.id] = {
                "id": item.id,
                "code": item.code,
                "name": item.name,
                "barcode": item.barcode or "",
                "unit_code": item.unit.code if item.unit else "ADET",
                "unit_id": item.unit_id,
            }
            self.item_combo.addItem(f"{item.code} - {item.name}", item.id)

    def load_units(self, units: list):
        """Birimleri ikincil birim combo'suna yükle (Dual-Unit)"""
        self.secondary_unit_combo.clear()
        self.secondary_unit_combo.addItem("-", None)
        for unit in units:
            self.secondary_unit_combo.addItem(unit.code, unit.id)

    def load_warehouses(self, warehouses: list):
        """Depoları yükle"""
        self.warehouses_data = {wh.id: wh for wh in warehouses}

        if hasattr(self, "from_warehouse_combo"):
            self.from_warehouse_combo.clear()
            for wh in warehouses:
                self.from_warehouse_combo.addItem(f"{wh.code} - {wh.name}", wh.id)

        if hasattr(self, "to_warehouse_combo"):
            self.to_warehouse_combo.clear()
            for wh in warehouses:
                self.to_warehouse_combo.addItem(f"{wh.code} - {wh.name}", wh.id)
                if wh.is_default:
                    self.to_warehouse_combo.setCurrentIndex(
                        self.to_warehouse_combo.count() - 1
                    )

    def _add_line(self):
        """Satır ekle"""
        item_id = self.item_combo.currentData()
        if not item_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir stok kartı seçin!")
            return

        item = self.items_data.get(item_id)
        if not item:
            return

        qty = Decimal(str(self.qty_input.value()))
        price = Decimal(str(self.price_input.value()))
        lot = self.lot_input.text().strip()

        # İkincil birim (Dual-Unit)
        sec_qty_val = self.secondary_qty_input.value()
        secondary_qty = Decimal(str(sec_qty_val)) if sec_qty_val > 0 else None
        secondary_unit_id = self.secondary_unit_combo.currentData()
        secondary_unit_code = (
            self.secondary_unit_combo.currentText() if secondary_unit_id else ""
        )

        line = {
            "item_id": item_id,
            "item_code": item["code"],
            "item_name": item["name"],
            "unit_code": item["unit_code"],
            "quantity": qty,
            "unit_price": price,
            "total": qty * price,
            "lot_number": lot or None,
            # Dual-Unit
            "secondary_quantity": secondary_qty,
            "secondary_unit_id": secondary_unit_id,
            "secondary_unit_code": secondary_unit_code,
        }

        self.lines.append(line)
        self._refresh_table()

        # Alanları temizle
        self.qty_input.setValue(1)
        self.price_input.setValue(0)
        self.lot_input.clear()
        self.secondary_qty_input.setValue(0)
        self.secondary_unit_combo.setCurrentIndex(0)
        self.item_combo.setFocus()

    def _refresh_table(self):
        """Tabloyu yenile"""
        self.table.setRowCount(len(self.lines))

        total = Decimal(0)

        for row, line in enumerate(self.lines):
            # Stok Kodu
            self.table.setItem(row, 0, QTableWidgetItem(line["item_code"]))

            # Stok Adı
            self.table.setItem(row, 1, QTableWidgetItem(line["item_name"]))

            # Miktar
            qty_item = QTableWidgetItem(f"{line['quantity']:,.4f}")
            qty_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 2, qty_item)

            # Birim
            self.table.setItem(row, 3, QTableWidgetItem(line["unit_code"]))

            # İkincil Miktar (Dual-Unit)
            sec_qty = line.get("secondary_quantity")
            sec_text = f"{sec_qty:,.4f}" if sec_qty else "-"
            sec_item = QTableWidgetItem(sec_text)
            sec_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 4, sec_item)

            # İkincil Birim (Dual-Unit)
            sec_unit = line.get("secondary_unit_code", "")
            self.table.setItem(row, 5, QTableWidgetItem(sec_unit))

            # Birim Fiyat
            price_item = QTableWidgetItem(f"₺{line['unit_price']:,.4f}")
            price_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 6, price_item)

            # Toplam
            total_item = QTableWidgetItem(f"₺{line['total']:,.2f}")
            total_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 7, total_item)

            # Lot No
            self.table.setItem(row, 8, QTableWidgetItem(line["lot_number"] or ""))

            # Sil butonu
            del_btn = QPushButton("🗑")
            del_btn.clicked.connect(lambda checked, r=row: self._delete_line(r))
            self.table.setCellWidget(row, 9, del_btn)

            total += line["total"]

        self.line_count_label.setText(f"Satır: {len(self.lines)}")
        self.total_label.setText(f"Toplam: ₺{total:,.2f}")

    def _delete_line(self, row: int):
        """Satır sil"""
        if 0 <= row < len(self.lines):
            del self.lines[row]
            self._refresh_table()

    def _on_save(self):
        if not self._validate():
            return
        data = self.get_form_data()
        self.saved.emit(data)

    def _validate(self) -> bool:
        if not self.lines:
            QMessageBox.warning(self, "Uyarı", "En az bir satır eklemelisiniz!")
            return False

        if self.movement_type in ["exit", "transfer"]:
            if (
                not hasattr(self, "from_warehouse_combo")
                or not self.from_warehouse_combo.currentData()
            ):
                QMessageBox.warning(self, "Uyarı", "Kaynak depo seçmelisiniz!")
                return False

        if self.movement_type in ["entry", "transfer"]:
            if (
                not hasattr(self, "to_warehouse_combo")
                or not self.to_warehouse_combo.currentData()
            ):
                QMessageBox.warning(self, "Uyarı", "Hedef depo seçmelisiniz!")
                return False

        return True

    def get_form_data(self) -> dict:
        # Hareket türünü belirle
        if self.movement_type == "entry":
            mov_type = StockMovementType.GIRIS
        elif self.movement_type == "exit":
            mov_type = StockMovementType.CIKIS
        else:
            mov_type = StockMovementType.TRANSFER

        data = {
            "movement_type": mov_type,
            "document_no": self.document_no_input.text().strip() or None,
            "movement_date": self.datetime_input.dateTime().toPyDateTime(),
            "reference_no": self.reference_input.text().strip() or None,
            "description": self.description_input.toPlainText().strip() or None,
            "lines": self.lines,
        }

        if hasattr(self, "from_warehouse_combo"):
            data["from_warehouse_id"] = self.from_warehouse_combo.currentData()

        if hasattr(self, "to_warehouse_combo"):
            data["to_warehouse_id"] = self.to_warehouse_combo.currentData()

        return data
