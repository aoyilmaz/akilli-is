from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QAction
import qtawesome as qta

from config.icons import ICONS
from config.styles import get_button_style, BTN_HEIGHT_NORMAL
from database.models.accounting import Budget, BudgetStatus
from modules.accounting.budget_service import BudgetService


class BudgetList(QWidget):
    """Bütçe Listesi"""

    budget_selected = pyqtSignal(int)
    create_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.service = BudgetService()
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header_layout = QHBoxLayout()

        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(ICONS.BUDGET, color="#475569").pixmap(24, 24))
        header_layout.addWidget(icon_lbl)

        title = QLabel("Bütçe Yönetimi")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        add_btn = QPushButton(" Yeni Bütçe")
        add_btn.setIcon(qta.icon(ICONS.ADD, color="#ffffff"))
        add_btn.setStyleSheet(get_button_style("primary"))
        add_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        add_btn.clicked.connect(self.create_requested.emit)
        header_layout.addWidget(add_btn)

        refresh_btn = QPushButton()
        refresh_btn.setIcon(qta.icon(ICONS.REFRESH, color="#64748b"))
        refresh_btn.setFixedSize(BTN_HEIGHT_NORMAL, BTN_HEIGHT_NORMAL)
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Bütçe Adı", "Dönem", "Tarih Aralığı", "Toplam Tutar", "Durum"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_row_double_clicked)

        layout.addWidget(self.table)

    def refresh_data(self):
        try:
            budgets = (
                self.service.session.query(Budget)
                .order_by(Budget.period_year.desc())
                .all()
            )

            self.table.setRowCount(len(budgets))
            for i, budget in enumerate(budgets):
                self.table.setItem(i, 0, QTableWidgetItem(str(budget.id)))
                self.table.setItem(i, 1, QTableWidgetItem(budget.name))
                self.table.setItem(i, 2, QTableWidgetItem(str(budget.period_year)))

                date_range = f"{budget.start_date.strftime('%d.%m.%Y')} - {budget.end_date.strftime('%d.%m.%Y')}"
                self.table.setItem(i, 3, QTableWidgetItem(date_range))

                amount_item = QTableWidgetItem(f"₺{budget.total_amount:,.2f}")
                amount_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(i, 4, amount_item)

                status_map = {
                    BudgetStatus.DRAFT: ("Taslak", "#fca5a5"),
                    BudgetStatus.APPROVED: ("Onaylandı", "#86efac"),
                    BudgetStatus.ACTIVE: ("Aktif", "#93c5fd"),
                    BudgetStatus.CLOSED: ("Kapandı", "#d1d5db"),
                    BudgetStatus.CANCELLED: ("İptal", "#fcd34d"),
                }
                status_text, color = status_map.get(budget.status, (budget.status, ""))
                status_item = QTableWidgetItem(status_text)
                # status_item.setBackground(QColor(color)) # Optional styling
                self.table.setItem(i, 5, status_item)

        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def _on_row_double_clicked(self):
        row = self.table.currentRow()
        if row >= 0:
            budget_id = int(self.table.item(row, 0).text())
            self.budget_selected.emit(budget_id)

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)
