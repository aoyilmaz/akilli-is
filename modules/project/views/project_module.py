"""
Akıllı İş - Proje Yönetimi Ana Modülü
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from ui.components.page_header import PageHeader
from modules.project.views.project_list import ProjectListView
from modules.project.views.kanban_board import KanbanBoard
from modules.project.views.gantt_chart import GanttChart


class ProjectMainModule(QWidget):
    """Proje Yönetimi ana konteynerı"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self.header = PageHeader(
            title="Proje Yönetimi",
            subtitle="Projeler, görevler ve zaman çizelgeleri",
            icon="ph.briefcase",
        )
        layout.addWidget(self.header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Tab 1: Proje Listesi
        self.project_list = ProjectListView()
        self.tabs.addTab(self.project_list, "Projeler")

        # Tab 2: Kanban Panosu
        self.kanban = KanbanBoard()
        self.tabs.addTab(self.kanban, "Kanban Panosu")

        # Tab 3: Gantt Grafiği
        self.gantt = GanttChart()
        self.tabs.addTab(self.gantt, "Gantt Çizelgesi")

        layout.addWidget(self.tabs)

    def refresh_data(self):
        """Tüm sekmeleri tazele"""
        current_widget = self.tabs.currentWidget()
        if hasattr(current_widget, "refresh_data"):
            current_widget.refresh_data()
