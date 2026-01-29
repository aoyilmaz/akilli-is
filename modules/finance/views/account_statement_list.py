"""
Akilli Is - Cari Hesap Ekstresi Liste Sayfasi
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
    QDateEdit,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
import qtawesome as qta

from config.icons import ICONS
from ui.components.page_header import PageHeader
from ui.components.stat_cards import MiniStatCard
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


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
        self.header = PageHeader(
            title="Cari Hesap Ekstresi",
            icon=ICONS.FINANCE,
            show_search=False,
            show_refresh=True,
            show_export=True,
            parent=self,
        )
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.export_clicked.connect(self._on_export)
        layout.addWidget(self.header)

        # Filtre alani
        filter_group = QGroupBox("Filtreler")
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
        self.entity_combo.setFixedWidth(250)
        self.entity_combo.setFixedHeight(36)
        self.entity_combo.currentIndexChanged.connect(self._on_entity_changed)
        entity_layout.addWidget(self.entity_combo)
        filter_layout.addLayout(entity_layout)

        # Tarih araligi
        date_from_layout = QVBoxLayout()
        date_from_layout.addWidget(QLabel("Başlangıç Tarihi"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setFixedWidth(140)
        self.date_from.setFixedHeight(36)
        date_from_layout.addWidget(self.date_from)
        filter_layout.addLayout(date_from_layout)

        date_to_layout = QVBoxLayout()
        date_to_layout.addWidget(QLabel("Bitiş Tarihi"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setFixedWidth(140)
        self.date_to.setFixedHeight(36)
        date_to_layout.addWidget(self.date_to)
        filter_layout.addLayout(date_to_layout)

        # Filtrele butonu
        filter_btn = QPushButton("Filtrele")
        filter_btn.setIcon(qta.icon(ICONS.FILTER, color="#ffffff"))
        filter_btn.setFixedSize(120, 36)
        filter_btn.setProperty("class", "btn-primary")
        filter_btn.clicked.connect(self.refresh_requested.emit)
        filter_layout.addWidget(filter_btn, alignment=Qt.AlignmentFlag.AlignBottom)

        filter_layout.addStretch()
        layout.addWidget(filter_group)

        # Ozet kartlari
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(16)
        self.stat_cards = {
            "opening": MiniStatCard("Açılış", "0.00 TL", "info", icon=ICONS.MONEY),
            "debit": MiniStatCard("Toplam Borç", "0.00 TL", "error", icon=ICONS.DANGER),
            "credit": MiniStatCard(
                "Toplam Alacak", "0.00 TL", "success", icon=ICONS.CHECK
            ),
            "balance": MiniStatCard("Bakiye", "0.00 TL", "warning", icon=ICONS.TIME),
        }
        for card in self.stat_cards.values():
            summary_layout.addWidget(card)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Hareket tablosu
        cols = [
            ColumnConfig("date", "Tarih", width=100),
            ColumnConfig("transaction_no", "Hareket No", width=130),
            ColumnConfig("type", "Tür", width=100),
            ColumnConfig("description", "Açıklama", width=300, stretch=True),
            ColumnConfig("debit", "Borç", width=120),
            ColumnConfig("credit", "Alacak", width=120),
            ColumnConfig("balance", "Bakiye", width=120),
        ]
        self.table = EnhancedTableWidget(
            table_id="finance_statement", columns=cols, parent=self
        )
        layout.addWidget(self.table)

    def load_entities(self, entity_type: str, entities: list):
        """Cari listesini yukle"""
        self.entity_combo.clear()
        self.entity_combo.addItem("Seçin...", None)
        for entity in entities:
            display = f"{entity.get('code', '')} - {entity.get('name', '')}"
            self.entity_combo.addItem(display, entity.get("id"))

    def load_data(self, movements: list, summary: dict = None):
        """Hareket verilerini yukle"""
        self.statements = movements
        self.table.setRowCount(len(movements))
        visible_cols = self.table.get_visible_columns()
        for row, mov in enumerate(movements):
            self._populate_row(row, mov, visible_cols)

        if summary:
            op = summary.get("opening_balance", 0)
            self.stat_cards["opening"].update_value(f"₺{op:,.2f}")
            db = summary.get("total_debit", 0)
            self.stat_cards["debit"].update_value(f"₺{db:,.2f}")
            cr = summary.get("total_credit", 0)
            self.stat_cards["credit"].update_value(f"₺{cr:,.2f}")
            cl = summary.get("closing_balance", 0)
            self.stat_cards["balance"].update_value(f"₺{cl:,.2f}")

    def _populate_row(self, row, mov, visible_cols):
        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "date":
                val = mov.get("date")
                d_str = (
                    val.strftime("%d.%m.%Y")
                    if hasattr(val, "strftime")
                    else str(val or "")
                )
                self.table.setItem(row, col_idx, QTableWidgetItem(d_str))
            elif col_key == "transaction_no":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(mov.get("transaction_no", ""))
                )
            elif col_key == "type":
                t_map = {
                    "invoice": "Fatura",
                    "payment": "Ödeme",
                    "receipt": "Tahsilat",
                    "opening": "Açılış",
                    "adjustment": "Düzeltme",
                }
                self.table.setItem(
                    row,
                    col_idx,
                    QTableWidgetItem(
                        t_map.get(mov.get("type", ""), mov.get("type", ""))
                    ),
                )
            elif col_key == "description":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(mov.get("description", ""))
                )
            elif col_key == "debit":
                val = mov.get("debit") or Decimal(0)
                item = QTableWidgetItem(f"{val:,.2f}" if val else "")
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                if val:
                    item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, col_idx, item)
            elif col_key == "credit":
                val = mov.get("credit") or Decimal(0)
                item = QTableWidgetItem(f"{val:,.2f}" if val else "")
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                if val:
                    item.setForeground(Qt.GlobalColor.green)
                self.table.setItem(row, col_idx, item)
            elif col_key == "balance":
                val = mov.get("balance") or Decimal(0)
                item = QTableWidgetItem(f"{val:,.2f}")
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, item)

    def _on_type_changed(self, index):
        self.current_entity_type = self.type_combo.currentData()
        self.refresh_requested.emit()

    def _on_entity_changed(self, index):
        self.current_entity_id = self.entity_combo.currentData()

    def _on_export(self):
        self.export_requested.emit(
            {
                "entity_type": self.current_entity_type,
                "entity_id": self.current_entity_id,
                "date_from": self.date_from.date().toPyDate(),
                "date_to": self.date_to.date().toPyDate(),
            }
        )

    def get_filter_data(self) -> dict:
        return {
            "entity_type": self.type_combo.currentData(),
            "entity_id": self.entity_combo.currentData(),
            "date_from": self.date_from.date().toPyDate(),
            "date_to": self.date_to.date().toPyDate(),
        }
