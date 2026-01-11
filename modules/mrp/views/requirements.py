"""
Akıllı İş - MRP İhtiyaç Listesi Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QLineEdit,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from modules.mrp.services import MRPService
from config.styles import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HOVER, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, ACCENT, SUCCESS, WARNING, ERROR,
    INPUT_BG, INPUT_BORDER, INPUT_FOCUS,
    get_table_style, get_input_style
)

class RequirementsPage(QWidget):
    """İhtiyaç listesi sayfası"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_run_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        title = QLabel("Net Ihtiyac Listesi")
        layout.addWidget(title)

        # Arama
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Urun ara...")
        self.search_input.textChanged.connect(self._filter_table)
        search_row.addWidget(self.search_input)
        search_row.addStretch()

        self.count_label = QLabel("0 satir")
        search_row.addWidget(self.count_label)

        layout.addLayout(search_row)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "Ürün Kodu",
                "Ürün Adı",
                "Tarih",
                "Brüt",
                "Giriş",
                "Eldeki",
                "Net",
                "Öneri",
            ]
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 90)
        self.table.setColumnWidth(6, 90)
        self.table.setColumnWidth(7, 100)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def load_requirements(self, run_id: int):
        """İhtiyaçları yükle"""
        self.current_run_id = run_id

        try:
            service = MRPService()
            lines = service.get_run_lines(run_id)
            service.close()

            self._populate_table(lines)
            self.count_label.setText(f"{len(lines)} satir")

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Yüklenirken hata:\n{e}")

    def _populate_table(self, lines):
        """Tabloyu doldur"""
        self.table.setRowCount(len(lines))

        for row, line in enumerate(lines):
            # Ürün kodu
            code = line.item.code if line.item else ""
            self.table.setItem(row, 0, QTableWidgetItem(code))

            # Ürün adı
            name = line.item.name if line.item else ""
            self.table.setItem(row, 1, QTableWidgetItem(name))

            # Tarih
            date_str = line.requirement_date.strftime("%d.%m.%Y")
            self.table.setItem(row, 2, QTableWidgetItem(date_str))

            # Brüt
            gross_item = QTableWidgetItem(f"{line.gross_requirement:,.2f}")
            gross_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 3, gross_item)

            # Giriş
            sched_item = QTableWidgetItem(f"{line.scheduled_receipts:,.2f}")
            sched_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 4, sched_item)

            # Eldeki
            on_hand = line.projected_on_hand or 0
            oh_item = QTableWidgetItem(f"{on_hand:,.2f}")
            oh_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            if on_hand < 0:
                oh_item.setForeground(QColor(ERROR))
            self.table.setItem(row, 5, oh_item)

            # Net
            net = line.net_requirement or 0
            net_item = QTableWidgetItem(f"{net:,.2f}")
            net_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            if net > 0:
                net_item.setForeground(QColor(WARNING))
            self.table.setItem(row, 6, net_item)

            # Öneri
            if line.suggestion_type:
                sug_text = f"{line.suggested_qty:,.0f}"
                sug_item = QTableWidgetItem(sug_text)
                sug_item.setForeground(QColor(SUCCESS))
            else:
                sug_item = QTableWidgetItem("-")
            sug_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 7, sug_item)

    def _filter_table(self, text: str):
        """Tabloyu filtrele"""
        text = text.lower()
        for row in range(self.table.rowCount()):
            code = self.table.item(row, 0).text().lower()
            name = self.table.item(row, 1).text().lower()
            visible = text in code or text in name
            self.table.setRowHidden(row, not visible)
