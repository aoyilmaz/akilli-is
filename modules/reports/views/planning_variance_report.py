import sys
from datetime import date, timedelta
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QDateEdit,
    QPushButton,
    QHeaderView,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

try:
    from modules.planning.services import MPSService
except ImportError:
    MPSService = None


class PlanningVarianceDialog(QDialog):
    """
    Planlanan vs Gerçekleşen Üretim Sapma Raporu Diyaloğu
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Üretim Planlama Sapma Raporu")
        self.resize(1000, 600)
        self.service = MPSService() if MPSService else None

        self.setup_ui()
        self.refresh_report()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Filtreler
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Başlangıç:"))
        self.date_start = QDateEdit()
        self.date_start.setDate(QDate.currentDate().addDays(-30))
        self.date_start.setCalendarPopup(True)
        filter_layout.addWidget(self.date_start)

        filter_layout.addWidget(QLabel("Bitiş:"))
        self.date_end = QDateEdit()
        self.date_end.setDate(QDate.currentDate().addDays(30))
        self.date_end.setCalendarPopup(True)
        filter_layout.addWidget(self.date_end)

        btn_refresh = QPushButton("Sorgula")
        btn_refresh.clicked.connect(self.refresh_report)
        filter_layout.addWidget(btn_refresh)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "Tarih",
                "Ürün Kodu",
                "Ürün Adı",
                "Plan No",
                "Planlanan",
                "Gerçekleşen",
                "Sapma",
                "Durum",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def refresh_report(self):
        if not self.service:
            return

        start = self.date_start.date().toPyDate()
        end = self.date_end.date().toPyDate()

        data = self.service.get_planning_variance(start, end)

        self.table.setRowCount(len(data))
        for i, row in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(row["date"]))
            self.table.setItem(i, 1, QTableWidgetItem(row["item_code"]))
            self.table.setItem(i, 2, QTableWidgetItem(row["item_name"]))
            self.table.setItem(i, 3, QTableWidgetItem(row["plan_no"]))
            self.table.setItem(i, 4, QTableWidgetItem(str(row["planned_qty"])))
            self.table.setItem(i, 5, QTableWidgetItem(str(row["actual_qty"])))

            # Sapma Renklendirme
            var_item = QTableWidgetItem(f"{row['variance']} ({row['variance_pct']}%)")
            if row["variance"] < 0:
                var_item.setForeground(QColor("#ff4d4d"))  # Kırmızı (Eksik Üretim)
            elif row["variance"] > 0:
                var_item.setForeground(QColor("#2da44e"))  # Yeşil (Fazla Üretim)

            self.table.setItem(i, 6, var_item)
            self.table.setItem(i, 7, QTableWidgetItem(row["status"]))

    def closeEvent(self, event):
        if self.service:
            self.service.close()
        super().closeEvent(event)
