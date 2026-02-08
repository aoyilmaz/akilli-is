from PyQt6.QtWidgets import QWidget, QStackedWidget
from modules.rfq.views.rfq_list import RFQListPage
from modules.rfq.views.rfq_form import RFQFormPage


class RFQModule(QWidget):
    def __init__(self):
        super().__init__()

        self.stacked_widget = QStackedWidget()

        # Pages
        self.list_page = RFQListPage()
        self.list_page.parent_module = self

        self.stacked_widget.addWidget(self.list_page)

        # Main layout
        from PyQt6.QtWidgets import QVBoxLayout

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked_widget)

    def show_list(self):
        self.list_page.refresh_data()
        self.stacked_widget.setCurrentWidget(self.list_page)

    def show_form(self, rfq_id=None):
        form_page = RFQFormPage(rfq_id)
        form_page.saved.connect(self.show_list)
        form_page.cancelled.connect(self.show_list)

        self.stacked_widget.addWidget(form_page)
        self.stacked_widget.setCurrentWidget(form_page)
