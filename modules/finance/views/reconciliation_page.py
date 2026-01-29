"""
Akilli Is - Mutabakat Sayfasi
"""

from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QFrame,
    QComboBox,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta

from config.icons import ICONS
from ui.components.page_header import PageHeader
from ui.components.stat_cards import MiniStatCard
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


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
        self.header = PageHeader(
            title="Mutabakat",
            icon=ICONS.FINANCE,
            show_search=False,
            show_refresh=True,
            show_add=False,
            parent=self,
        )
        self.header.refresh_clicked.connect(self.refresh_requested.emit)

        h_layout = self.header.header_layout()
        print_btn = QPushButton("Yazdır")
        print_btn.setIcon(qta.icon(ICONS.REPORT, color="#ffffff"))
        print_btn.setFixedSize(110, 36)
        print_btn.setProperty("class", "btn-secondary")
        print_btn.clicked.connect(self._on_print)
        h_layout.addWidget(print_btn)

        layout.addWidget(self.header)

        # Filtre alani
        filter_group = QGroupBox("Cari Seçimi")
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(16)

        # Cari tipi
        type_layout = QVBoxLayout()
        type_layout.addWidget(QLabel("Cari Tipi"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("Müşteri", "customer")
        self.type_combo.addItem("Tedarikçi", "supplier")
        self.type_combo.setFixedWidth(150)
        self.type_combo.setFixedHeight(36)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        filter_layout.addLayout(type_layout)

        # Cari secimi
        entity_layout = QVBoxLayout()
        entity_layout.addWidget(QLabel("Cari Hesap"))
        self.entity_combo = QComboBox()
        self.entity_combo.setFixedWidth(300)
        self.entity_combo.setFixedHeight(36)
        self.entity_combo.currentIndexChanged.connect(self._on_entity_changed)
        entity_layout.addWidget(self.entity_combo)
        filter_layout.addLayout(entity_layout)

        # Sorgula butonu
        query_btn = QPushButton("Sorgula")
        query_btn.setIcon(qta.icon(ICONS.SEARCH, color="#ffffff"))
        query_btn.setFixedSize(120, 36)
        query_btn.setProperty("class", "btn-primary")
        query_btn.clicked.connect(self.refresh_requested.emit)
        filter_layout.addWidget(query_btn, alignment=Qt.AlignmentFlag.AlignBottom)

        filter_layout.addStretch()
        layout.addWidget(filter_group)

        # Ozet kartlari
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(16)
        self.stat_cards = {
            "balance": MiniStatCard("Bakiye", "0.00 TL", "info", icon=ICONS.MONEY),
            "open_count": MiniStatCard(
                "Açık Kalem", "0", "warning", icon=ICONS.INVOICE
            ),
            "open_amount": MiniStatCard(
                "Açık Tutar", "0.00 TL", "error", icon=ICONS.DANGER
            ),
        }
        for card in self.stat_cards.values():
            summary_layout.addWidget(card)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Acik kalemler tablosu
        cols = [
            ColumnConfig("invoice_no", "Fatura No", width=120),
            ColumnConfig("date", "Tarih", width=100),
            ColumnConfig("due_date", "Vade", width=100),
            ColumnConfig("total", "Toplam", width=120),
            ColumnConfig("paid", "Ödenen", width=120),
            ColumnConfig("remaining", "Kalan", width=120, stretch=True),
        ]
        self.open_table = EnhancedTableWidget(
            table_id="finance_open_items", columns=cols, parent=self
        )
        layout.addWidget(self.open_table)

    def load_entities(self, entity_type: str, entities: list):
        """Cari listesini yukle"""
        self.entity_combo.clear()
        self.entity_combo.addItem("Seçin...", None)
        for entity in entities:
            display = f"{entity.get('code', '')} - {entity.get('name', '')}"
            self.entity_combo.addItem(display, entity.get("id"))

    def load_data(self, data: dict):
        """Mutabakat verilerini yukle"""
        balance = data.get("balance", Decimal(0))
        self.stat_cards["balance"].update_value(f"₺{balance:,.2f}")

        open_invoices = data.get("open_invoices", [])
        self.stat_cards["open_count"].update_value(str(len(open_invoices)))

        total_open = data.get("total_open_amount", Decimal(0))
        self.stat_cards["open_amount"].update_value(f"₺{total_open:,.2f}")

        self.open_table.setRowCount(len(open_invoices))
        visible_cols = self.open_table.get_visible_columns()
        for row, inv in enumerate(open_invoices):
            self._populate_row(row, inv, visible_cols)

    def _populate_row(self, row, inv, visible_cols):
        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "invoice_no":
                self.open_table.setItem(
                    row, col_idx, QTableWidgetItem(inv.get("invoice_no", ""))
                )
            elif col_key == "date":
                val = inv.get("invoice_date")
                d_str = (
                    val.strftime("%d.%m.%Y")
                    if hasattr(val, "strftime")
                    else str(val or "")
                )
                self.open_table.setItem(row, col_idx, QTableWidgetItem(d_str))
            elif col_key == "due_date":
                val = inv.get("due_date")
                d_str = (
                    val.strftime("%d.%m.%Y")
                    if hasattr(val, "strftime")
                    else str(val or "")
                )
                self.open_table.setItem(row, col_idx, QTableWidgetItem(d_str))
            elif col_key == "total":
                val = inv.get("total_amount") or Decimal(0)
                item = QTableWidgetItem(f"{float(val):,.2f}")
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.open_table.setItem(row, col_idx, item)
            elif col_key == "paid":
                val = inv.get("paid_amount") or Decimal(0)
                item = QTableWidgetItem(f"{float(val):,.2f}")
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.open_table.setItem(row, col_idx, item)
            elif col_key == "remaining":
                val = inv.get("remaining_amount") or Decimal(0)
                item = QTableWidgetItem(f"{float(val):,.2f}")
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                item.setForeground(Qt.GlobalColor.red)
                self.open_table.setItem(row, col_idx, item)

    def _on_type_changed(self, index):
        self.current_entity_type = self.type_combo.currentData()
        self.refresh_requested.emit()

    def _on_entity_changed(self, index):
        self.current_entity_id = self.entity_combo.currentData()

    def _on_print(self):
        self.print_requested.emit(
            {
                "entity_type": self.current_entity_type,
                "entity_id": self.current_entity_id,
            }
        )

    def get_filter_data(self) -> dict:
        return {
            "entity_type": self.type_combo.currentData(),
            "entity_id": self.entity_combo.currentData(),
        }
