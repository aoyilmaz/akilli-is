from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QHBoxLayout,
    QPushButton,
)
from PyQt6.QtCore import Qt

from config.icons import ICONS
from config.styles import get_button_style
import qtawesome as qta
from modules.accounting.budget_service import BudgetService


class BudgetReportWidget(QWidget):
    """Bütçe Gerçekleşme Raporu"""

    def __init__(self, budget_id):
        super().__init__()
        self.budget_id = budget_id
        self.service = BudgetService()
        self.setup_ui()
        self.refresh_report()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        self.title = QLabel("Bütçe Raporu")
        self.title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(self.title)

        refresh_btn = QPushButton()
        refresh_btn.setIcon(qta.icon(ICONS.REFRESH, color="#64748b"))
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.clicked.connect(self.refresh_report)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Summary Cards
        cards_layout = QHBoxLayout()
        self.planned_lbl = QLabel("Planlanan: ₺0")
        self.actual_lbl = QLabel("Gerçekleşen: ₺0")
        self.variance_lbl = QLabel("Fark: ₺0")

        for lbl in [self.planned_lbl, self.actual_lbl, self.variance_lbl]:
            lbl.setStyleSheet(
                "font-size: 14px; padding: 10px; border: 1px solid #ddd; border-radius: 8px;"
            )
            cards_layout.addWidget(lbl)

        layout.addLayout(cards_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Hesap", "Hesap Adı", "Planlanan", "Gerçekleşen", "Fark (%)"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def refresh_report(self):
        try:
            report = self.service.get_budget_status(self.budget_id)
            budget = report["budget"]

            self.title.setText(
                f"{budget['name']} ({budget['period_year']}) - Gerçekleşme Raporu"
            )

            self.planned_lbl.setText(f"Planlanan: ₺{budget['total_planned']:,.2f}")
            self.actual_lbl.setText(f"Gerçekleşen: ₺{budget['total_actual']:,.2f}")
            self.variance_lbl.setText(f"Fark: ₺{budget['variance']:,.2f}")

            lines = report["lines"]
            self.table.setRowCount(len(lines))

            for i, line in enumerate(lines):
                self.table.setItem(i, 0, QTableWidgetItem(line["account_code"]))
                self.table.setItem(i, 1, QTableWidgetItem(line["account_name"]))

                planned = QTableWidgetItem(f"₺{line['planned']:,.2f}")
                planned.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(i, 2, planned)

                actual = QTableWidgetItem(f"₺{line['actual']:,.2f}")
                actual.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(i, 3, actual)

                diff = line["variance"]
                ratio = line["ratio"] if line["planned"] != 0 else 0

                diff_item = QTableWidgetItem(f"₺{diff:,.2f} (%{ratio:.1f})")
                diff_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )

                if diff < 0:  # Over budget (if expense)
                    diff_item.setForeground(Qt.GlobalColor.red)
                else:
                    diff_item.setForeground(Qt.GlobalColor.green)

                self.table.setItem(i, 4, diff_item)

        except Exception as e:
            self.title.setText(f"Hata: {str(e)}")

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)
