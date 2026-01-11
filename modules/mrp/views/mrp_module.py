"""
Akilli Is - MRP Ana Modulu
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QTabWidget,
)
from PyQt6.QtCore import Qt

from .mrp_run import MRPRunPage
from .requirements import RequirementsPage
from .suggestions import SuggestionsPage

class MRPModule(QWidget):
    """MRP ana modulu - ic menu yok, tab yapisi"""

    page_title = "MRP"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_run_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab widget
        self.tabs = QTabWidget()
        # Sayfalar
        self.run_page = MRPRunPage()
        self.run_page.mrp_completed.connect(self._on_mrp_completed)
        self.tabs.addTab(self.run_page, "MRP Calistir")

        self.requirements_page = RequirementsPage()
        self.tabs.addTab(self.requirements_page, "Net Ihtiyaclar")

        self.suggestions_page = SuggestionsPage()
        self.tabs.addTab(self.suggestions_page, "Tedarik Onerileri")

        self.tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self.tabs)

    def _on_tab_changed(self, index: int):
        """Tab degisti"""
        if self.current_run_id and index > 0:
            if index == 1:
                self.requirements_page.load_requirements(self.current_run_id)
            elif index == 2:
                self.suggestions_page.load_suggestions(self.current_run_id)

    def _on_mrp_completed(self, run_id: int):
        """MRP tamamlandi veya secildi"""
        self.current_run_id = run_id

        # Oneriler tabina gec
        self.tabs.setCurrentIndex(2)
        self.suggestions_page.load_suggestions(run_id)
