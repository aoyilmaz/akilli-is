"""
Akıllı İş - Proje Listesi Görünümü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLineEdit,
    QComboBox,
    QHeaderView,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from database.base import SessionLocal
from modules.project.services.project_service import ProjectService
from database.models.project import ProjectStatus


class ProjectListView(QWidget):
    """Projelerin listelendiği tablo barkı"""

    def __init__(self):
        super().__init__()
        self.db = SessionLocal()
        self.service = ProjectService(self.db)
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Upper Toolbar
        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Proje adı veya koduna göre ara...")
        self.search_input.textChanged.connect(self.filter_data)
        toolbar.addWidget(self.search_input)

        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        for status in ProjectStatus:
            self.status_filter.addItem(status.value.capitalize(), status)
        self.status_filter.currentIndexChanged.connect(self.refresh_data)
        toolbar.addWidget(self.status_filter)

        self.btn_new = QPushButton("Yeni Proje")
        self.btn_new.setIcon(QIcon.fromTheme("list-add"))
        toolbar.addWidget(self.btn_new)

        self.btn_refresh = QPushButton("Tazele")
        self.btn_refresh.clicked.connect(self.refresh_data)
        toolbar.addWidget(self.btn_refresh)

        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "Kod",
                "Proje Adı",
                "Müşteri",
                "Başlangıç",
                "Durum",
                "İlerleme",
                "Yönetici",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTriggers.NoEditTriggers)
        layout.addWidget(self.table)

    def refresh_data(self):
        """Projeleri veritabanından çek ve tabloyu doldur"""
        status = self.status_filter.currentData()
        projects = self.service.list_projects(status=status)

        self.table.setRowCount(0)
        for proj in projects:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(proj.code))
            self.table.setItem(row, 1, QTableWidgetItem(proj.name))
            self.table.setItem(
                row, 2, QTableWidgetItem(proj.customer.name if proj.customer else "-")
            )
            self.table.setItem(
                row, 3, QTableWidgetItem(proj.start_date.strftime("%d.%m.%Y"))
            )
            self.table.setItem(row, 4, QTableWidgetItem(proj.status.value))

            # Progress (Bar olarak da yapılabilir ama şimdilik metin)
            prog_item = QTableWidgetItem(f"%{proj.progress:.1f}")
            prog_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, prog_item)

            self.table.setItem(
                row,
                6,
                QTableWidgetItem(
                    f"{proj.manager.first_name} {proj.manager.last_name}"
                    if proj.manager
                    else "-"
                ),
            )

    def filter_data(self):
        """Arama kutusuna göre tabloyu filtrele (Local filtering)"""
        search_text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(2):  # Sadece kod ve ad sütunlarına bak
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
