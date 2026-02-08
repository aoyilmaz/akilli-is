from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QStackedWidget
from database.models.contracts import ContractType
from modules.contracts.views.contract_list import ContractListPage
from modules.contracts.views.contract_form import ContractFormPage


class ContractModule(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        # Main Tab View
        self.tabs_widget = QWidget()
        self.tabs_layout = QVBoxLayout(self.tabs_widget)
        self.tabs_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs_layout.addWidget(self.tabs)

        # Satış Sözleşmeleri
        self.sales_list = ContractListPage(ContractType.SALES)
        self.sales_list.parent_module = self
        self.tabs.addTab(self.sales_list, "Satış Sözleşmeleri")

        # Tedarik Sözleşmeleri
        self.purchase_list = ContractListPage(ContractType.PURCHASE)
        self.purchase_list.parent_module = self
        self.tabs.addTab(self.purchase_list, "Tedarik Sözleşmeleri")

        self.stacked_widget.addWidget(self.tabs_widget)

    def show_form(self, contract_id=None, contract_type=None):
        target_type = contract_type or ContractType.SALES
        self.form_page = ContractFormPage(target_type, contract_id)
        self.form_page.saved.connect(self._on_saved)
        self.form_page.cancelled.connect(self._on_cancelled)

        index = self.stacked_widget.addWidget(self.form_page)
        self.stacked_widget.setCurrentIndex(index)

    def _on_saved(self):
        widget = self.stacked_widget.currentWidget()
        if widget != self.tabs_widget:
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()

        self.sales_list.refresh_data()
        self.purchase_list.refresh_data()
        self.stacked_widget.setCurrentWidget(self.tabs_widget)

    def _on_cancelled(self):
        widget = self.stacked_widget.currentWidget()
        if widget != self.tabs_widget:
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()

        self.stacked_widget.setCurrentWidget(self.tabs_widget)
