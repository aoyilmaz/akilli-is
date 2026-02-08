"""
Akıllı İş - Kanban Panosu Bileşeni
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag, QColor, QPalette

from database.base import SessionLocal
from modules.project.services.project_service import ProjectService
from database.models.project import TaskStatus, ProjectTask


class KanbanCard(QFrame):
    """Kanban panosundaki tek bir görev kartı"""

    def __init__(self, task: ProjectTask):
        super().__init__()
        self.task_id = task.id
        self.init_ui(task)

    def init_ui(self, task):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)
        self.setMinimumHeight(80)
        self.setFixedWidth(240)
        self.setStyleSheet(
            """
            KanbanCard {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 10px;
            }
            KanbanCard:hover {
                border-color: #3498db;
                background-color: #f7fbfe;
            }
        """
        )

        layout = QVBoxLayout(self)

        # Priority Indicator
        priority_colors = {
            "low": "#2ecc71",
            "medium": "#f1c40f",
            "high": "#e67e22",
            "critical": "#e74c3c",
        }
        color = priority_colors.get(task.priority.value, "#95a5a6")

        header_layout = QHBoxLayout()
        priority_label = QLabel(task.priority.value.upper())
        priority_label.setStyleSheet(
            f"""
            color: white; 
            background-color: {color}; 
            border-radius: 4px; 
            padding: 2px 6px; 
            font-size: 9px; 
            font-weight: bold;
        """
        )
        header_layout.addWidget(priority_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Title
        title_label = QLabel(task.title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        layout.addWidget(title_label)

        # Assignee
        if task.assignee:
            assignee_label = QLabel(f"👤 {task.assignee.first_name}")
            assignee_label.setStyleSheet("color: #666; font-size: 11px;")
            layout.addWidget(assignee_label)

        # Progress
        if task.progress > 0:
            progress_label = QLabel(f"İlerleme: %{task.progress:.0f}")
            progress_label.setStyleSheet("color: #27ae60; font-size: 10px;")
            layout.addWidget(progress_label)


class KanbanColumn(QFrame):
    """Kanban sütunu (Durumlara göre gruplar)"""

    def __init__(self, title, status: TaskStatus):
        super().__init__()
        self.status = status
        self.init_ui(title)

    def init_ui(self, title):
        self.setFixedWidth(270)
        self.setStyleSheet("background-color: #f0f2f5; border-radius: 8px;")

        layout = QVBoxLayout(self)

        header = QLabel(title.upper())
        header.setStyleSheet("font-weight: bold; color: #5f6368; padding: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Card container
        self.content = QFrame()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self.content)
        layout.addWidget(scroll)

    def add_card(self, card):
        self.content_layout.addWidget(card)

    def clear(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class KanbanBoard(QWidget):
    """Tüm sütunları içeren ana Kanban bileşeni"""

    def __init__(self, project_id: int = None):
        super().__init__()
        self.project_id = project_id
        self.db = SessionLocal()
        self.service = ProjectService(self.db)
        self.columns = {}
        self.init_ui()
        if project_id:
            self.refresh_data()

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setSpacing(15)

        status_names = {
            TaskStatus.TODO: "Yapılacaklar",
            TaskStatus.IN_PROGRESS: "Devam Ediyor",
            TaskStatus.REVIEW: "İnceleme",
            TaskStatus.DONE: "Tamamlandı",
            TaskStatus.BLOCKED: "Engellendi",
        }

        for status in TaskStatus:
            col = KanbanColumn(status_names[status], status)
            self.columns[status.value] = col
            self.main_layout.addWidget(col)

    def refresh_data(self):
        """Görevleri çek ve kartları oluştur"""
        if not self.project_id:
            # Örnek olarak ilk projeyi çek (Test amaçlı)
            from database.models.project import Project

            proj = self.db.query(Project).first()
            if proj:
                self.project_id = proj.id
            else:
                return

        data = self.service.get_kanban_data(self.project_id)
        for status_val, col in self.columns.items():
            col.clear()
            for task in data.get(status_val, []):
                card = KanbanCard(task)
                col.add_card(card)

    def set_project(self, project_id):
        self.project_id = project_id
        self.refresh_data()

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
