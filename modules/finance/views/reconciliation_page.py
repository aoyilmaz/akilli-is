"""
Akilli Is - Mutabakat Sayfasi
VS Code Dark Theme
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QFrame,
    QComboBox,
    QHeaderView,
    QAbstractItemView,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from decimal import Decimal

from config.styles import (
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    ACCENT,
    SUCCESS,
    WARNING,
    ERROR,
    get_table_style,
    get_button_style,
)


class ReconciliationPage(QWidget):
    """Mutabakat sayfasi"""

    refresh_requested = pyqtSignal()
    print_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_entity_type = "customer"
        self.current_entity_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Mutabakat")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Yazdir butonu
        print_btn = QPushButton("🖨️ Yazdir")
        print_btn.setFixedHeight(42)
        print_btn.setStyleSheet(get_button_style("print"))
        print_btn.clicked.connect(self._on_print)
        header_layout.addWidget(print_btn)

        layout.addLayout(header_layout)

        # Filtre alani
        filter_group = QGroupBox("Cari Secimi")
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
        self.entity_combo.setFixedWidth(300)
        self.entity_combo.setStyleSheet(self._combo_style())
        self.entity_combo.currentIndexChanged.connect(self._on_entity_changed)
        entity_layout.addWidget(self.entity_combo)
        filter_layout.addLayout(entity_layout)

        # Sorgula butonu
        query_btn = QPushButton("🔍 Sorgula")
        query_btn.setFixedSize(110, 42)
        query_btn.setStyleSheet(get_button_style("search"))
        query_btn.clicked.connect(self.refresh_requested.emit)
        filter_layout.addWidget(query_btn, alignment=Qt.AlignmentFlag.AlignBottom)

        filter_layout.addStretch()
        layout.addWidget(filter_group)

        # Ozet kartlari
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(12)

        self.balance_card = self._create_stat_card("Bakiye", "0.00 TL", ACCENT)
        summary_layout.addWidget(self.balance_card)

        self.open_count_card = self._create_stat_card("Acik Kalem", "0", WARNING)
        summary_layout.addWidget(self.open_count_card)

        self.open_amount_card = self._create_stat_card("Acik Tutar", "0.00 TL", ERROR)
        summary_layout.addWidget(self.open_amount_card)

        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Acik kalemler tablosu
        open_group = QGroupBox("Acik Kalemler")
        open_group.setStyleSheet(self._group_style())

        open_layout = QVBoxLayout(open_group)

        self.open_table = QTableWidget()
        self.open_table.setColumnCount(6)
        self.open_table.setHorizontalHeaderLabels(
            ["Fatura No", "Tarih", "Vade", "Toplam", "Odenen", "Kalan"]
        )
        self.open_table.setAlternatingRowColors(True)
        self.open_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.open_table.verticalHeader().setVisible(False)
        self.open_table.setMinimumHeight(200)

        header = self.open_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)

        self.open_table.setColumnWidth(1, 100)
        self.open_table.setColumnWidth(2, 100)
        self.open_table.setColumnWidth(3, 120)
        self.open_table.setColumnWidth(4, 120)
        self.open_table.setColumnWidth(5, 120)

        open_layout.addWidget(self.open_table)
        layout.addWidget(open_group)

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
            QComboBox QAbstractItemView {{
                background-color: {BG_SECONDARY};
                border: 1px solid {BORDER};
                selection-background-color: {ACCENT};
                color: {TEXT_PRIMARY};
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

    def load_data(self, data: dict):
        """Mutabakat verilerini yukle"""
        # Ozet kartlari guncelle
        balance = data.get("balance", Decimal(0))
        self._update_card(self.balance_card, f"{balance:,.2f} TL")

        open_invoices = data.get("open_invoices", [])
        self._update_card(self.open_count_card, str(len(open_invoices)))

        total_open = data.get("total_open_amount", Decimal(0))
        self._update_card(self.open_amount_card, f"{total_open:,.2f} TL")

        # Acik kalemler tablosu
        self.open_table.setRowCount(0)

        for row, inv in enumerate(open_invoices):
            self.open_table.insertRow(row)

            # Fatura no
            self.open_table.setItem(row, 0, QTableWidgetItem(inv.get("invoice_no", "")))

            # Tarih
            date_val = inv.get("invoice_date")
            if hasattr(date_val, "strftime"):
                date_str = date_val.strftime("%d.%m.%Y")
            else:
                date_str = str(date_val) if date_val else ""
            self.open_table.setItem(row, 1, QTableWidgetItem(date_str))

            # Vade
            due_date = inv.get("due_date")
            if hasattr(due_date, "strftime"):
                due_str = due_date.strftime("%d.%m.%Y")
            else:
                due_str = str(due_date) if due_date else ""
            self.open_table.setItem(row, 2, QTableWidgetItem(due_str))

            # Toplam
            total = inv.get("total_amount") or Decimal(0)
            total_item = QTableWidgetItem(f"{float(total):,.2f}")
            total_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.open_table.setItem(row, 3, total_item)

            # Odenen
            paid = inv.get("paid_amount") or Decimal(0)
            paid_item = QTableWidgetItem(f"{float(paid):,.2f}")
            paid_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.open_table.setItem(row, 4, paid_item)

            # Kalan
            remaining = inv.get("remaining_amount") or Decimal(0)
            remaining_item = QTableWidgetItem(f"{float(remaining):,.2f}")
            remaining_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            remaining_item.setForeground(Qt.GlobalColor.red)
            self.open_table.setItem(row, 5, remaining_item)

            self.open_table.setRowHeight(row, 44)

    def _on_type_changed(self, index):
        """Cari tipi degistiginde"""
        self.current_entity_type = self.type_combo.currentData()
        self.refresh_requested.emit()

    def _on_entity_changed(self, index):
        """Cari secimi degistiginde"""
        self.current_entity_id = self.entity_combo.currentData()

    def _on_print(self):
        """Yazdir"""
        self.print_requested.emit(
            {
                "entity_type": self.current_entity_type,
                "entity_id": self.current_entity_id,
            }
        )

    def get_filter_data(self) -> dict:
        """Filtre verilerini getir"""
        return {
            "entity_type": self.type_combo.currentData(),
            "entity_id": self.entity_combo.currentData(),
        }
