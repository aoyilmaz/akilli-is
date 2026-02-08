"""
Akıllı İş - Gantt Grafiği Bileşeni (Custom Drawing)
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame
from PyQt6.QtCore import Qt, QRect, QPoint, QSize, QDate
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush

from database.base import SessionLocal
from modules.project.services.project_service import ProjectService
from database.models.project import Project


class GanttCanvas(QWidget):
    """Gantt çizim alanı"""

    def __init__(self):
        super().__init__()
        self.tasks = []
        self.row_height = 40
        self.day_width = 40
        self.header_height = 50
        self.left_margin = 200
        self.start_date = QDate.currentDate().addDays(-5)
        self.num_days = 30

        self.setMinimumSize(1000, 600)

    def set_data(self, tasks):
        self.tasks = tasks
        # Yüksekliği görev sayısına göre ayarla
        h = self.header_height + (len(tasks) * self.row_height) + 50
        self.setMinimumHeight(max(600, h))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Timeline Arka Plan ve Izgara (Grid)
        painter.setPen(QPen(QColor("#ddd"), 1))
        for i in range(self.num_days + 1):
            x = self.left_margin + (i * self.day_width)
            painter.drawLine(x, 0, x, h)

            # Gün başlıkları
            d = self.start_date.addDays(i)
            painter.drawText(
                QRect(x, 0, self.day_width, self.header_height),
                Qt.AlignmentFlag.AlignCenter,
                str(d.day()),
            )

        # Sol Panel Ayracı
        painter.setPen(QPen(QColor("#bbb"), 2))
        painter.drawLine(self.left_margin, 0, self.left_margin, h)

        # 2. Görevleri Çiz
        y = self.header_height
        task_points = {}  # Bağımlılık çizgileri için konumlar

        for i, task in enumerate(self.tasks):
            # Görev Adı (Sol Panel)
            painter.setPen(QColor("#333"))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(
                QRect(10, y, self.left_margin - 20, self.row_height),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                task["title"],
            )

            # Görev Çubuğu (Gantt Bar)
            if task["start"] and task["end"]:
                s = QDate.fromString(task["start"], Qt.DateFormat.ISODate)
                e = QDate.fromString(task["end"], Qt.DateFormat.ISODate)

                start_offset = self.start_date.daysTo(s)
                duration = s.daysTo(e) + 1

                x = self.left_margin + (start_offset * self.day_width)
                bw = duration * self.day_width
                rect = QRect(x + 5, y + 10, bw - 10, self.row_height - 20)

                # Bar Arka Planı
                painter.setBrush(QBrush(QColor("#3498db")))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(rect, 4, 4)

                # İlerleme (Progress)
                if task["progress"] > 0:
                    pw = (rect.width() * task["progress"]) / 100
                    painter.setBrush(QBrush(QColor("#2ecc71")))
                    painter.drawRoundedRect(
                        QRect(rect.x(), rect.y(), int(pw), rect.height()), 4, 4
                    )

                # Kaydet (Bağımlılıklar için)
                task_points[task["id"]] = QPoint(x + bw / 2, y + self.row_height / 2)

            y += self.row_height

        # 3. Bağımlılık Çizgileri (Arrows)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#e74c3c"), 1.5, Qt.PenStyle.DashLine))
        for task in self.tasks:
            if task["id"] in task_points:
                end_pt = task_points[task["id"]]
                for pred_id in task.get("dependencies", []):
                    if pred_id in task_points:
                        start_pt = task_points[pred_id]
                        painter.drawLine(start_pt, end_pt)


class GanttChart(QWidget):
    """Gantt grafiği konteynerı"""

    def __init__(self, project_id: int = None):
        super().__init__()
        self.project_id = project_id
        self.db = SessionLocal()
        self.service = ProjectService(self.db)
        self.init_ui()
        if project_id:
            self.refresh_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.canvas = GanttCanvas()
        scroll.setWidget(self.canvas)

        layout.addWidget(scroll)

    def refresh_data(self):
        if not self.project_id:
            from database.models.project import Project

            proj = self.db.query(Project).first()
            if proj:
                self.project_id = proj.id
            else:
                return

        data = self.service.get_gantt_data(self.project_id)
        self.canvas.set_data(data)

    def set_project(self, project_id):
        self.project_id = project_id
        self.refresh_data()

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
