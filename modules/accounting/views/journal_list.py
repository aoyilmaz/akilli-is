"""
Akıllı İş - Yevmiye Listesi
"""

from datetime import date
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QDateEdit,
    QComboBox,
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor
import qtawesome as qta

from config.icons import ICONS
from database.models.accounting import JournalEntryStatus
from ui.components.page_header import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


class JournalListWidget(QWidget):
    """Yevmiye listesi"""

    journal_selected = pyqtSignal(int)
    journal_double_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Yevmiye Defteri",
            icon=ICONS.INVOICE,
            show_search=False,
            show_refresh=True,
            show_add=False,
            parent=self,
        )

        h_layout = self.header.header_layout()

        # Filtreler
        h_layout.addWidget(QLabel("Başlangıç:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setFixedWidth(110)
        self.start_date.setFixedHeight(36)
        h_layout.addWidget(self.start_date)

        h_layout.addWidget(QLabel("Bitiş:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setFixedWidth(110)
        self.end_date.setFixedHeight(36)
        h_layout.addWidget(self.end_date)

        h_layout.addWidget(QLabel("Durum:"))
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem("Taslak", JournalEntryStatus.DRAFT)
        self.status_combo.addItem("İşlenmiş", JournalEntryStatus.POSTED)
        self.status_combo.addItem("İptal", JournalEntryStatus.CANCELLED)
        self.status_combo.setFixedWidth(120)
        self.status_combo.setFixedHeight(36)
        h_layout.addWidget(self.status_combo)

        filter_btn = QPushButton("Filtrele")
        filter_btn.setIcon(qta.icon(ICONS.FILTER, color="#ffffff"))
        filter_btn.setFixedHeight(36)
        filter_btn.setProperty("class", "btn-secondary")
        filter_btn.clicked.connect(lambda: self.refresh_requested.emit())
        h_layout.addWidget(filter_btn)

        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        layout.addWidget(self.header)

        # Tablo
        columns = [
            ColumnConfig("entry_no", "Fiş No", width=120),
            ColumnConfig("date", "Tarih", width=100),
            ColumnConfig("description", "Açıklama", width=300, stretch=True),
            ColumnConfig("debit", "Borç", width=120),
            ColumnConfig("credit", "Alacak", width=120),
            ColumnConfig("status", "Durum", width=100),
        ]

        self.table = EnhancedTableWidget(
            table_id="journal_entries",
            columns=columns,
            parent=self,
        )
        self.table.row_double_clicked.connect(self.journal_double_clicked.emit)
        layout.addWidget(self.table)

    def load_journals(self, journals: list):
        """Yevmiyeleri yükle"""
        self.table.setRowCount(len(journals))
        visible_cols = self.table.get_visible_columns()

        for row, journal in enumerate(journals):
            self._populate_row(row, journal, visible_cols)

    def _populate_row(self, row: int, journal, visible_cols: list):
        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "entry_no":
                item = QTableWidgetItem(journal.entry_no)
                item.setData(Qt.ItemDataRole.UserRole, journal.id)
                self.table.setItem(row, col_idx, item)

            elif col_key == "date":
                dt_str = journal.entry_date.strftime("%d.%m.%Y")
                self.table.setItem(row, col_idx, QTableWidgetItem(dt_str))

            elif col_key == "description":
                desc = journal.description or ""
                self.table.setItem(row, col_idx, QTableWidgetItem(desc))

            elif col_key == "debit":
                debit = sum(line.debit or 0 for line in journal.lines)
                item = QTableWidgetItem(f"₺{debit:,.2f}")
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, item)

            elif col_key == "credit":
                credit = sum(line.credit or 0 for line in journal.lines)
                item = QTableWidgetItem(f"₺{credit:,.2f}")
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, item)

            elif col_key == "status":
                txt = self._get_status_label(journal.status)
                item = QTableWidgetItem(txt)
                item.setForeground(QColor(self._get_status_color(journal.status)))
                self.table.setItem(row, col_idx, item)

    def _get_status_label(self, status: JournalEntryStatus) -> str:
        labels = {
            JournalEntryStatus.DRAFT: "Taslak",
            JournalEntryStatus.POSTED: "İşlenmiş",
            JournalEntryStatus.CANCELLED: "İptal",
        }
        return labels.get(status, "Bilinmiyor")

    def _get_status_color(self, status: JournalEntryStatus) -> str:
        colors = {
            JournalEntryStatus.DRAFT: "#f59e0b",
            JournalEntryStatus.POSTED: "#10b981",
            JournalEntryStatus.CANCELLED: "#ef4444",
        }
        return colors.get(status, "#94a3b8")

    def get_filters(self) -> dict:
        qstart = self.start_date.date()
        qend = self.end_date.date()
        return {
            "start_date": date(qstart.year(), qstart.month(), qstart.day()),
            "end_date": date(qend.year(), qend.month(), qend.day()),
            "status": self.status_combo.currentData(),
        }
