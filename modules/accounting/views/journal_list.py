"""
Akıllı İş - Yevmiye Listesi
VS Code Dark Theme
"""

from datetime import date

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QDateEdit,
    QComboBox,
    QHeaderView,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor

from config.styles import (
    BG_PRIMARY, BG_SECONDARY, BORDER, TEXT_PRIMARY, TEXT_MUTED, ACCENT,
    SUCCESS, WARNING, ERROR,
    get_table_style, get_button_style,
)
from database.models.accounting import JournalEntryStatus


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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Filtreler
        filter_layout = QHBoxLayout()

        # Başlangıç tarihi
        start_label = QLabel("Başlangıç:")
        start_label.setStyleSheet(f"color: {TEXT_MUTED};")
        filter_layout.addWidget(start_label)
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        self._style_date(self.start_date)
        filter_layout.addWidget(self.start_date)

        # Bitiş tarihi
        end_label = QLabel("Bitiş:")
        end_label.setStyleSheet(f"color: {TEXT_MUTED};")
        filter_layout.addWidget(end_label)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self._style_date(self.end_date)
        filter_layout.addWidget(self.end_date)

        # Durum
        status_label = QLabel("Durum:")
        status_label.setStyleSheet(f"color: {TEXT_MUTED};")
        filter_layout.addWidget(status_label)
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem("Taslak", JournalEntryStatus.DRAFT)
        self.status_combo.addItem("İşlenmiş", JournalEntryStatus.POSTED)
        self.status_combo.addItem("İptal", JournalEntryStatus.CANCELLED)
        self._style_combo(self.status_combo)
        filter_layout.addWidget(self.status_combo)

        filter_layout.addStretch()

        # Filtrele butonu
        filter_btn = QPushButton("Filtrele")
        filter_btn.setStyleSheet(get_button_style("secondary"))
        filter_btn.clicked.connect(lambda: self.refresh_requested.emit())
        filter_layout.addWidget(filter_btn)

        layout.addLayout(filter_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Fiş No", "Tarih", "Açıklama", "Borç", "Alacak", "Durum"]
        )

        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 100)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        self.table.setStyleSheet(get_table_style())

        self.table.itemDoubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table)

    def _style_date(self, widget):
        widget.setStyleSheet(f"""
            QDateEdit {{
                background-color: {BG_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                color: {TEXT_PRIMARY};
            }}
            QDateEdit:focus {{ border-color: {ACCENT}; }}
        """)

    def _style_combo(self, widget):
        widget.setStyleSheet(f"""
            QComboBox {{
                background-color: {BG_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                color: {TEXT_PRIMARY};
                min-width: 100px;
            }}
            QComboBox:focus {{ border-color: {ACCENT}; }}
            QComboBox QAbstractItemView {{
                background-color: {BG_SECONDARY};
                border: 1px solid {BORDER};
                selection-background-color: {ACCENT};
                color: {TEXT_PRIMARY};
            }}
        """)

    def load_journals(self, journals: list):
        """Yevmiyeleri yükle"""
        self.table.setRowCount(len(journals))

        for row, journal in enumerate(journals):
            # Fiş No
            no_item = QTableWidgetItem(journal.entry_no)
            no_item.setData(Qt.ItemDataRole.UserRole, journal.id)
            self.table.setItem(row, 0, no_item)

            # Tarih
            date_str = journal.entry_date.strftime("%d.%m.%Y")
            self.table.setItem(row, 1, QTableWidgetItem(date_str))

            # Açıklama
            self.table.setItem(
                row, 2, QTableWidgetItem(journal.description or "")
            )

            # Borç
            debit = sum(line.debit or 0 for line in journal.lines)
            debit_item = QTableWidgetItem(f"₺{debit:,.2f}")
            debit_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 3, debit_item)

            # Alacak
            credit = sum(line.credit or 0 for line in journal.lines)
            credit_item = QTableWidgetItem(f"₺{credit:,.2f}")
            credit_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 4, credit_item)

            # Durum
            status_item = QTableWidgetItem(
                self._get_status_label(journal.status)
            )
            status_item.setForeground(
                QColor(self._get_status_color(journal.status))
            )
            self.table.setItem(row, 5, status_item)

    def _get_status_label(self, status: JournalEntryStatus) -> str:
        labels = {
            JournalEntryStatus.DRAFT: "Taslak",
            JournalEntryStatus.POSTED: "İşlenmiş",
            JournalEntryStatus.CANCELLED: "İptal",
        }
        return labels.get(status, "")

    def _get_status_color(self, status: JournalEntryStatus) -> str:
        colors = {
            JournalEntryStatus.DRAFT: WARNING,
            JournalEntryStatus.POSTED: SUCCESS,
            JournalEntryStatus.CANCELLED: ERROR,
        }
        return colors.get(status, TEXT_MUTED)

    def _on_double_click(self, item):
        row = item.row()
        journal_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if journal_id:
            self.journal_double_clicked.emit(journal_id)

    def get_filters(self) -> dict:
        """Filtre değerleri"""
        qstart = self.start_date.date()
        qend = self.end_date.date()

        return {
            "start_date": date(qstart.year(), qstart.month(), qstart.day()),
            "end_date": date(qend.year(), qend.month(), qend.day()),
            "status": self.status_combo.currentData(),
        }

    def get_selected_journal_id(self) -> int:
        """Seçili yevmiye ID'si"""
        row = self.table.currentRow()
        if row >= 0:
            return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return None
