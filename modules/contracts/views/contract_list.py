from typing import List, Optional
from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox, QWidget
from ui.components.base_list_page import BaseListPage
from ui.components.enhanced_table import ColumnConfig
from config.icons import ICONS
from database.base import get_session as get_db
from modules.contracts.services.contract_service import ContractService
from database.models.contracts import ContractType


class ContractListPage(BaseListPage):
    def __init__(self, contract_type: ContractType):
        self.contract_type = contract_type
        self.service = ContractService(get_db())

        title = (
            "Satış Sözleşmeleri"
            if contract_type == ContractType.SALES
            else "Tedarik Sözleşmeleri"
        )

        # Define Columns
        columns = [
            ColumnConfig("code", "Sözleşme Kodu", 150),
            ColumnConfig("party", "Taraf", 250),  # Müşteri/Tedarikçi
            ColumnConfig("start_date", "Başlangıç", 120),
            ColumnConfig("end_date", "Bitiş", 120),
            ColumnConfig("status", "Durum", 100),
            ColumnConfig("amount", "Tutar", 120),
        ]

        super().__init__(
            title=title,
            icon=ICONS.CONTRACT,
            table_id=f"contract_list_{contract_type.value}",
            columns=columns,
            show_add=True,
            add_text="Yeni Sözleşme",
        )

        self.refresh_requested.connect(self.refresh_data)
        self.add_clicked.connect(self._on_add_clicked)
        self.view_clicked.connect(self._on_view_clicked)

        self.parent_module = None

        self.refresh_data()

    def refresh_data(self):
        try:
            contracts = self.service.list_contracts(contract_type=self.contract_type)
            self.table.setRowCount(0)

            for row, contract in enumerate(contracts):
                self.table.insertRow(row)

                # Code
                self.table.setItem(row, 0, QTableWidgetItem(contract.code))

                # Party
                party_name = "-"
                if contract.customer:
                    party_name = contract.customer.name
                elif contract.supplier:
                    party_name = contract.supplier.name
                self.table.setItem(row, 1, QTableWidgetItem(party_name))

                # Dates
                self.table.setItem(row, 2, QTableWidgetItem(str(contract.start_date)))
                self.table.setItem(row, 3, QTableWidgetItem(str(contract.end_date)))

                # Status
                status_val = (
                    contract.status.value
                    if hasattr(contract.status, "value")
                    else str(contract.status)
                )
                status_item = QTableWidgetItem(status_val)
                self.table.setItem(row, 4, status_item)

                # Amount
                amount_str = f"{contract.total_amount:,.2f} {contract.currency}"
                self.table.setItem(row, 5, QTableWidgetItem(amount_str))

                # Store ID
                self.table.set_row_id(row, contract.id)

            self.update_count(len(contracts))
        except Exception as e:
            self.show_error("Hata", f"Veriler yüklenirken hata: {str(e)}")

    def _on_add_clicked(self):
        if self.parent_module and hasattr(self.parent_module, "show_form"):
            self.parent_module.show_form(contract_type=self.contract_type)

    def _on_view_clicked(self, contract_id):
        if self.parent_module and hasattr(self.parent_module, "show_form"):
            self.parent_module.show_form(
                contract_id=contract_id, contract_type=self.contract_type
            )
