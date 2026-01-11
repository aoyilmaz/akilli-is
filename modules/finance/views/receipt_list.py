"""
Akilli Is - Tahsilat Liste Sayfasi
VS Code Dark Theme
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QLineEdit,
    QHeaderView, QAbstractItemView, QMessageBox, QComboBox,
    QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from decimal import Decimal

from config.styles import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HOVER, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, ACCENT, SUCCESS, WARNING, ERROR,
    get_table_style, get_button_style, get_input_style
)

class ReceiptListPage(QWidget):
    """Tahsilat listesi sayfasi"""

    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.receipts = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Tahsilatlar")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara... (no, musteri)")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_input)

        # Yenile butonu
        refresh_btn = QPushButton("Yenile")
        refresh_btn.setFixedHeight(42)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)

        # Yeni ekle butonu
        add_btn = QPushButton("+ Yeni Tahsilat")
        add_btn.clicked.connect(self.add_clicked.emit)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # Filtre alani
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)

        # Tarih araligi
        date_from_label = QLabel("Baslangic:")
        filter_layout.addWidget(date_from_label)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setFixedWidth(130)
        self.date_from.setStyleSheet(self._date_style())
        filter_layout.addWidget(self.date_from)

        date_to_label = QLabel("Bitis:")
        filter_layout.addWidget(date_to_label)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setFixedWidth(130)
        self.date_to.setStyleSheet(self._date_style())
        filter_layout.addWidget(self.date_to)

        # Durum filtresi
        status_label = QLabel("Durum:")
        filter_layout.addWidget(status_label)

        self.status_combo = QComboBox()
        self.status_combo.addItem("Tumu", None)
        self.status_combo.addItem("Tamamlandi", "completed")
        self.status_combo.addItem("Beklemede", "pending")
        self.status_combo.addItem("Iptal", "cancelled")
        self.status_combo.setFixedWidth(130)
        self.status_combo.setStyleSheet(self._combo_style())
        filter_layout.addWidget(self.status_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Istatistik kartlari
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.total_card = self._create_stat_card("Toplam", "0", ACCENT)
        stats_layout.addWidget(self.total_card)

        self.completed_card = self._create_stat_card("Tamamlanan", "0", SUCCESS)
        stats_layout.addWidget(self.completed_card)

        self.amount_card = self._create_stat_card("Toplam Tutar", "0.00 TL", WARNING)
        stats_layout.addWidget(self.amount_card)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Tahsilat No", "Tarih", "Musteri", "Tutar",
            "Odeme Yontemi", "Durum", "Aciklama", "Islemler"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        # Kolon genislikleri
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(7, 120)

        self.table.doubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table)

    def _date_style(self) -> str:
        return f"""
            QDateEdit {{
                background-color: {BG_TERTIARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                color: {TEXT_PRIMARY};
                font-size: 13px;
            }}
            QDateEdit:focus {{ border-color: {ACCENT}; }}
        """

    def _combo_style(self) -> str:
        return f"""
            QComboBox {{
                background-color: {BG_TERTIARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                color: {TEXT_PRIMARY};
                font-size: 13px;
            }}
            QComboBox:focus {{ border-color: {ACCENT}; }}
            QComboBox QAbstractItemView {{
                background-color: {BG_SECONDARY};
                border: 1px solid {BORDER};
                selection-background-color: {ACCENT};
                color: {TEXT_PRIMARY};
            }}
        """

    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setFixedSize(160, 80)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        title_label = QLabel(title)
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName("value")
        layout.addWidget(value_label)

        return card

    def _update_card(self, card: QFrame, value: str):
        label = card.findChild(QLabel, "value")
        if label:
            label.setText(value)

    def load_data(self, receipts: list):
        """Verileri yukle"""
        self.receipts = receipts
        self.table.setRowCount(0)

        total = len(receipts)
        completed = 0
        total_amount = Decimal(0)

        for rec in receipts:
            if rec.get("status") == "completed":
                completed += 1
                total_amount += Decimal(str(rec.get("amount", 0) or 0))

        self._update_card(self.total_card, str(total))
        self._update_card(self.completed_card, str(completed))
        self._update_card(self.amount_card, f"{total_amount:,.2f} TL")

        for row, rec in enumerate(receipts):
            self.table.insertRow(row)

            # Tahsilat No
            no_item = QTableWidgetItem(rec.get("receipt_no", ""))
            no_item.setData(Qt.ItemDataRole.UserRole, rec.get("id"))
            self.table.setItem(row, 0, no_item)

            # Tarih
            date_val = rec.get("receipt_date")
            if hasattr(date_val, "strftime"):
                date_str = date_val.strftime("%d.%m.%Y")
            else:
                date_str = str(date_val) if date_val else ""
            self.table.setItem(row, 1, QTableWidgetItem(date_str))

            # Musteri
            self.table.setItem(row, 2, QTableWidgetItem(rec.get("customer_name", "")))

            # Tutar
            amount = rec.get("amount") or 0
            amount_item = QTableWidgetItem(f"{float(amount):,.2f} TL")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, amount_item)

            # Odeme yontemi
            method_map = {
                "cash": "Nakit",
                "bank_transfer": "Havale/EFT",
                "check": "Cek",
                "credit_card": "Kredi Karti",
                "promissory_note": "Senet",
            }
            method = rec.get("payment_method", "")
            method_display = method_map.get(method, method)
            self.table.setItem(row, 4, QTableWidgetItem(method_display))

            # Durum
            status_map = {
                "pending": ("Beklemede", WARNING),
                "completed": ("Tamamlandi", SUCCESS),
                "cancelled": ("Iptal", ERROR),
            }
            status = rec.get("status", "")
            status_text, status_color = status_map.get(status, (status, TEXT_MUTED))
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(Qt.GlobalColor.white)
            self.table.setItem(row, 5, status_item)

            # Aciklama
            self.table.setItem(row, 6, QTableWidgetItem(rec.get("description", "") or ""))

            # Islem butonlari
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            view_btn = QPushButton("Gor")
            view_btn.setFixedSize(40, 28)
            view_btn.clicked.connect(lambda checked, id=rec.get("id"): self.view_clicked.emit(id))
            btn_layout.addWidget(view_btn)

            if rec.get("status") != "cancelled":
                cancel_btn = QPushButton("Iptal")
                cancel_btn.setFixedSize(45, 28)
                cancel_btn.clicked.connect(lambda checked, id=rec.get("id"): self._confirm_cancel(id))
                btn_layout.addWidget(cancel_btn)

            self.table.setCellWidget(row, 7, btn_widget)
            self.table.setRowHeight(row, 52)

    def _action_btn_style(self, color: str) -> str:
        return f"""
            QPushButton {{
                background-color: {color}20;
                border: 1px solid {color}50;
                border-radius: 4px;
                font-size: 11px;
                color: {TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: {color}40;
            }}
        """

    def _on_search(self, text: str):
        """Arama"""
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(6):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def _on_double_click(self, index):
        """Cift tiklama"""
        row = index.row()
        item = self.table.item(row, 0)
        if item:
            receipt_id = item.data(Qt.ItemDataRole.UserRole)
            if receipt_id:
                self.view_clicked.emit(receipt_id)

    def _confirm_cancel(self, receipt_id: int):
        """Iptal onayi"""
        reply = QMessageBox.question(
            self, "Iptal Onayi",
            "Bu tahsilati iptal etmek istediginize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(receipt_id)

    def get_filter_data(self) -> dict:
        """Filtre verilerini getir"""
        return {
            "date_from": self.date_from.date().toPyDate(),
            "date_to": self.date_to.date().toPyDate(),
            "status": self.status_combo.currentData(),
        }
