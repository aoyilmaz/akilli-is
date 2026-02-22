from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
)
from PyQt6.QtCore import Qt
from ui.components.base_list_page import BaseListPage
from ui.components.enhanced_table import ColumnConfig
from config.icons import ICONS
from database.base import get_session
from modules.rfq.services.rfq_service import RFQService
from database.models.rfq import RFQStatus


class RFQListPage(BaseListPage):
    def __init__(self):
        self.service = RFQService(get_session())

        columns = [
            ColumnConfig("rfq_no", "RFQ No", 150),
            ColumnConfig("title", "Başlık", 250),
            ColumnConfig("date", "Tarih", 120),
            ColumnConfig("deadline", "Son Tarih", 120),
            ColumnConfig("status", "Durum", 100),
            ColumnConfig("offer_count", "Teklif Sayısı", 100),
        ]

        super().__init__(
            title="Teklif Talepleri (RFQ)",
            icon=ICONS.PURCHASE_ORDER,  # TODO: dedicated icon
            table_id="rfq_list",
            columns=columns,
            show_add=True,
            add_text="Yeni RFQ",
        )

        self.refresh_requested.connect(self.refresh_data)
        self.add_clicked.connect(self._on_add_clicked)
        self.view_clicked.connect(self._on_view_clicked)

        self.parent_module = None
        self.refresh_data()

    def refresh_data(self):
        try:
            rfqs = self.service.list_rfqs()
            self.table.setRowCount(0)

            for row, rfq in enumerate(rfqs):
                self.table.insertRow(row)

                self.table.setItem(row, 0, QTableWidgetItem(rfq.rfq_no))
                self.table.setItem(row, 1, QTableWidgetItem(rfq.title))
                self.table.setItem(row, 2, QTableWidgetItem(str(rfq.date)))
                self.table.setItem(row, 3, QTableWidgetItem(str(rfq.deadline)))
                self.table.setItem(row, 4, QTableWidgetItem(rfq.status_display))
                self.table.setItem(row, 5, QTableWidgetItem(str(len(rfq.offers))))

                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, rfq.id)

            self.update_count(len(rfqs))
        except Exception as e:
            self.show_error("Hata", f"Veriler yüklenirken hata: {str(e)}")

    def _on_add_clicked(self):
        if self.parent_module:
            self.parent_module.show_form()

    def _on_view_clicked(self, rfq_id):
        if self.parent_module:
            self.parent_module.show_form(rfq_id)
