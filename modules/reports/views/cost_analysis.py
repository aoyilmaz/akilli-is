from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDateEdit,
    QPushButton,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from modules.production.services.base import WorkOrderService
from database.models.production import WorkOrderStatus


class CostAnalysisPage(QWidget):
    def __init__(self):
        super().__init__()
        self.service = WorkOrderService()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Başlangıç:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        filter_layout.addWidget(self.start_date)

        filter_layout.addWidget(QLabel("Bitiş:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        filter_layout.addWidget(self.end_date)

        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(refresh_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "İş Emri",
                "Ürün",
                "Durum",
                "Planlanan Toplam",
                "Gerçekleşen Toplam",
                "Fark (Tutar)",
                "Fark (%)",
                "Detay",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table)

    def load_data(self):
        self.table.setRowCount(0)
        orders = self.service.get_all()  # In real app, apply date filter here

        row = 0
        for order in orders:
            # We only care about cost-relevant orders
            if order.status not in [
                WorkOrderStatus.COMPLETED,
                WorkOrderStatus.CLOSED,
                WorkOrderStatus.IN_PROGRESS,
            ]:
                continue

            planned_total = (
                (order.planned_material_cost or 0)
                + (order.planned_labor_cost or 0)
                + (order.planned_overhead_cost or 0)
            )
            actual_total = (
                (order.actual_material_cost or 0)
                + (order.actual_labor_cost or 0)
                + (order.actual_overhead_cost or 0)
            )

            variance = actual_total - planned_total
            variance_pct = (variance / planned_total * 100) if planned_total else 0

            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(order.order_no))
            self.table.setItem(
                row, 1, QTableWidgetItem(order.item.name if order.item else "")
            )
            self.table.setItem(row, 2, QTableWidgetItem(order.status.value))

            self.table.setItem(row, 3, QTableWidgetItem(str(round(planned_total, 2))))
            self.table.setItem(row, 4, QTableWidgetItem(str(round(actual_total, 2))))

            var_item = QTableWidgetItem(str(round(variance, 2)))
            if variance > 0:
                var_item.setForeground(QColor("red"))
            elif variance < 0:
                var_item.setForeground(QColor("green"))
            self.table.setItem(row, 5, var_item)

            pct_item = QTableWidgetItem(f"%{round(variance_pct, 1)}")
            self.table.setItem(row, 6, pct_item)

            # Placeholder for detail button
            btn = QPushButton("Detay")
            self.table.setCellWidget(row, 7, btn)

            row += 1
