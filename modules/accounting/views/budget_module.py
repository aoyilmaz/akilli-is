from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import pyqtSignal

from modules.accounting.views.budget_list import BudgetList
from modules.accounting.views.budget_form import BudgetForm
from modules.accounting.views.budget_report import BudgetReportWidget


class BudgetModule(QWidget):
    """Bütçe Yönetimi Modülü"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)

        self.show_list()

    def show_list(self):
        """Liste görünümünü yükle"""
        if hasattr(self, "list_view"):
            self.stack.removeWidget(self.list_view)
            self.list_view.deleteLater()

        self.list_view = BudgetList()
        self.list_view.create_requested.connect(self.show_create_form)
        self.list_view.budget_selected.connect(self.show_detail)  # Or show report

        # Double click opens report by default? Or Edit?
        # Let's open Report, and have Edit button there?
        # Or open Edit form directly?
        # Standard: Edit form.

        self.stack.addWidget(self.list_view)
        self.stack.setCurrentWidget(self.list_view)

    def show_create_form(self):
        """Yeni bütçe formu"""
        self.form_view = BudgetForm()
        self.form_view.saved.connect(self.show_list)
        self.form_view.cancelled.connect(self.show_list)

        self.stack.addWidget(self.form_view)
        self.stack.setCurrentWidget(self.form_view)

    def show_detail(self, budget_id):
        """Detay görünümü (Report + Edit Button)"""
        # For now, let's just open the Edit Form
        # But we also want to see the report.
        # Maybe use TabWidget here?

        self.detail_container = QWidget()
        layout = QVBoxLayout(self.detail_container)

        from PyQt6.QtWidgets import QTabWidget

        tabs = QTabWidget()

        # Tab 1: Düzenle
        self.form_view = BudgetForm(budget_id)
        self.form_view.saved.connect(self.show_list)
        self.form_view.cancelled.connect(self.show_list)
        tabs.addTab(self.form_view, "Tanım & Kalemler")

        # Tab 2: Rapor
        self.report_view = BudgetReportWidget(budget_id)
        tabs.addTab(self.report_view, "Gerçekleşme Raporu")

        layout.addWidget(tabs)

        # Back button handled by form cancel or tab close?
        # Form has Cancel button which goes back to list.
        # Report doesn't have a back button.
        # We need a back button in container header?
        # Or rely on Form's Cancel button.

        # If user switches to Report tab, how to go back?
        # Let's add a "Back to List" button in header of container.

        # Header
        from PyQt6.QtWidgets import QHBoxLayout, QPushButton
        from config.icons import ICONS
        import qtawesome as qta

        header = QHBoxLayout()
        back_btn = QPushButton(" Listeye Dön")
        back_btn.setIcon(qta.icon(ICONS.BACK, color="#64748b"))
        back_btn.clicked.connect(self.show_list)
        header.addWidget(back_btn)
        header.addStretch()

        layout.insertLayout(0, header)

        self.stack.addWidget(self.detail_container)
        self.stack.setCurrentWidget(self.detail_container)
