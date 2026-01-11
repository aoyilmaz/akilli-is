"""
Akilli Is - Cari Hesap Ekstresi Liste Sayfasi
VS Code Dark Theme
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame,
    QHeaderView, QAbstractItemView, QComboBox, QDateEdit,
    QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from decimal import Decimal

from config.styles import (
    BG_PRIMARY, BG_SECONDARY, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, ACCENT, SUCCESS, WARNING, ERROR,
    get_table_style, get_button_style
)

class AccountStatementListPage(QWidget):
    """Cari hesap ekstresi liste sayfasi"""

    refresh_requested = pyqtSignal()
    export_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.statements = []
        self.current_entity_type = "customer"
        self.current_entity_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Cari Hesap Ekstresi")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Yenile butonu
        refresh_btn = QPushButton("Yenile")
        refresh_btn.setFixedHeight(42)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)

        # Excel'e aktar
        export_btn = QPushButton("Excel'e Aktar")
        export_btn.setFixedHeight(42)
        export_btn.clicked.connect(self._on_export)
        header_layout.addWidget(export_btn)

        layout.addLayout(header_layout)

        # Filtre alani
        filter_group = QGroupBox("Filtreler")
        filter_group.setStyleSheet(self._group_style())

        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(16)

        # Cari tipi
        type_layout = QVBoxLayout()
        type_label = QLabel("Cari Tipi")
        type_layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.addItem("Musteri", "customer")
        self.type_combo.addItem("Tedarikci", "supplier")
        self.type_combo.setFixedWidth(150)
        self.type_combo.setStyleSheet(self._combo_style())
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        filter_layout.addLayout(type_layout)

        # Cari secimi
        entity_layout = QVBoxLayout()
        entity_label = QLabel("Cari Hesap")
        entity_layout.addWidget(entity_label)

        self.entity_combo = QComboBox()
        self.entity_combo.setFixedWidth(250)
        self.entity_combo.setStyleSheet(self._combo_style())
        self.entity_combo.currentIndexChanged.connect(self._on_entity_changed)
        entity_layout.addWidget(self.entity_combo)
        filter_layout.addLayout(entity_layout)

        # Tarih araligi
        date_from_layout = QVBoxLayout()
        date_from_label = QLabel("Baslangic Tarihi")
        date_from_layout.addWidget(date_from_label)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setFixedWidth(140)
        self.date_from.setStyleSheet(self._date_style())
        date_from_layout.addWidget(self.date_from)
        filter_layout.addLayout(date_from_layout)

        date_to_layout = QVBoxLayout()
        date_to_label = QLabel("Bitis Tarihi")
        date_to_layout.addWidget(date_to_label)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setFixedWidth(140)
        self.date_to.setStyleSheet(self._date_style())
        date_to_layout.addWidget(self.date_to)
        filter_layout.addLayout(date_to_layout)

        # Filtrele butonu
        filter_btn = QPushButton("Filtrele")
        filter_btn.setFixedSize(100, 42)
        filter_btn.clicked.connect(self.refresh_requested.emit)
        filter_layout.addWidget(
            filter_btn, alignment=Qt.AlignmentFlag.AlignBottom
        )

        filter_layout.addStretch()
        layout.addWidget(filter_group)

        # Ozet kartlari
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(12)

        self.opening_card = self._create_stat_card("Acilis", "0.00 TL", ACCENT)
        summary_layout.addWidget(self.opening_card)

        self.debit_card = self._create_stat_card(
            "Toplam Borc", "0.00 TL", ERROR
        )
        summary_layout.addWidget(self.debit_card)

        self.credit_card = self._create_stat_card(
            "Toplam Alacak", "0.00 TL", SUCCESS
        )
        summary_layout.addWidget(self.credit_card)

        self.balance_card = self._create_stat_card(
            "Bakiye", "0.00 TL", WARNING
        )
        summary_layout.addWidget(self.balance_card)

        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Hareket tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Tarih", "Hareket No", "Tur", "Aciklama",
            "Borc", "Alacak", "Bakiye"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        # Kolon genislikleri
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 120)

        layout.addWidget(self.table)

    def _group_style(self) -> str:
        return f"""
            QGroupBox {{
                background-color: {BG_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 12px;
                padding: 16px;
                margin-top: 8px;
                color: {TEXT_PRIMARY};
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }}
        """

    def _combo_style(self) -> str:
        return f"""
            QComboBox {{
                background-color: {BG_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                color: {TEXT_PRIMARY};
                font-size: 14px;
            }}
            QComboBox:focus {{ border-color: {ACCENT}; }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 10px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {BG_SECONDARY};
                border: 1px solid {BORDER};
                selection-background-color: {ACCENT};
                color: {TEXT_PRIMARY};
            }}
        """

    def _date_style(self) -> str:
        return f"""
            QDateEdit {{
                background-color: {BG_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 10px 14px;
                color: {TEXT_PRIMARY};
                font-size: 14px;
            }}
            QDateEdit:focus {{ border-color: {ACCENT}; }}
            QDateEdit::drop-down {{
                border: none;
                padding-right: 10px;
            }}
        """

    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setFixedSize(180, 80)
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

    def load_entities(self, entity_type: str, entities: list):
        """Cari listesini yukle"""
        self.entity_combo.clear()
        self.entity_combo.addItem("Secin...", None)

        for entity in entities:
            display = f"{entity.get('code', '')} - {entity.get('name', '')}"
            self.entity_combo.addItem(display, entity.get("id"))

    def load_data(self, movements: list, summary: dict = None):
        """Hareket verilerini yukle"""
        self.statements = movements
        self.table.setRowCount(0)

        for row, mov in enumerate(movements):
            self.table.insertRow(row)

            # Tarih
            date_val = mov.get("date")
            if hasattr(date_val, "strftime"):
                date_str = date_val.strftime("%d.%m.%Y")
            else:
                date_str = str(date_val) if date_val else ""
            self.table.setItem(row, 0, QTableWidgetItem(date_str))

            # Hareket No
            self.table.setItem(
                row, 1, QTableWidgetItem(mov.get("transaction_no", ""))
            )

            # Tur
            type_map = {
                "invoice": "Fatura",
                "payment": "Odeme",
                "receipt": "Tahsilat",
                "opening": "Acilis",
                "adjustment": "Duzeltme",
            }
            type_val = mov.get("type", "")
            type_display = type_map.get(type_val, type_val)
            type_item = QTableWidgetItem(type_display)
            self.table.setItem(row, 2, type_item)

            # Aciklama
            self.table.setItem(
                row, 3, QTableWidgetItem(mov.get("description", ""))
            )

            # Borc
            debit = mov.get("debit") or Decimal(0)
            debit_item = QTableWidgetItem(f"{debit:,.2f}" if debit else "")
            debit_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            if debit:
                debit_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 4, debit_item)

            # Alacak
            credit = mov.get("credit") or Decimal(0)
            credit_item = QTableWidgetItem(f"{credit:,.2f}" if credit else "")
            credit_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            if credit:
                credit_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row, 5, credit_item)

            # Bakiye
            balance = mov.get("balance") or Decimal(0)
            balance_item = QTableWidgetItem(f"{balance:,.2f}")
            balance_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 6, balance_item)

            self.table.setRowHeight(row, 48)

        # Ozet kartlarini guncelle
        if summary:
            self._update_card(
                self.debit_card, f"{summary.get('total_debit', 0):,.2f} TL"
            )
            self._update_card(
                self.credit_card, f"{summary.get('total_credit', 0):,.2f} TL"
            )
            self._update_card(
                self.balance_card,
                f"{summary.get('closing_balance', 0):,.2f} TL"
            )

    def _on_type_changed(self, index):
        """Cari tipi degistiginde"""
        self.current_entity_type = self.type_combo.currentData()
        self.refresh_requested.emit()

    def _on_entity_changed(self, index):
        """Cari secimi degistiginde"""
        self.current_entity_id = self.entity_combo.currentData()

    def _on_export(self):
        """Excel'e aktar"""
        self.export_requested.emit({
            "entity_type": self.current_entity_type,
            "entity_id": self.current_entity_id,
            "date_from": self.date_from.date().toPyDate(),
            "date_to": self.date_to.date().toPyDate(),
        })

    def get_filter_data(self) -> dict:
        """Filtre verilerini getir"""
        return {
            "entity_type": self.type_combo.currentData(),
            "entity_id": self.entity_combo.currentData(),
            "date_from": self.date_from.date().toPyDate(),
            "date_to": self.date_to.date().toPyDate(),
        }
