"""
Akıllı İş - Proje Yönetimi Servisi
"""

from datetime import date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from database.models.project import (
    Project,
    ProjectTask,
    TaskDependency,
    TimeEntry,
    ProjectStatus,
    TaskStatus,
    DependencyType,
)


class ProjectService:
    """Proje ve görev yönetimi iş mantığı"""

    def __init__(self, db: Session):
        self.db = db

    def create_project(self, data: Dict[str, Any]) -> Project:
        """Yeni bir proje oluşturur"""
        project = Project(**data)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project(self, project_id: int) -> Optional[Project]:
        """ID'ye göre projeyi getirir"""
        return self.db.query(Project).get(project_id)

    def list_projects(self, status: Optional[ProjectStatus] = None) -> List[Project]:
        """Projeleri listeler"""
        query = self.db.query(Project)
        if status:
            query = query.filter(Project.status == status)
        return query.all()

    def add_task(self, project_id: int, data: Dict[str, Any]) -> ProjectTask:
        """Projeye yeni bir görev ekler"""
        task = ProjectTask(project_id=project_id, **data)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        self.update_project_progress(project_id)
        return task

    def add_task_dependency(
        self,
        task_id: int,
        predecessor_id: int,
        dep_type: DependencyType = DependencyType.FS,
    ) -> TaskDependency:
        """Görevler arası bağımlılık ekler"""
        dependency = TaskDependency(
            task_id=task_id, predecessor_id=predecessor_id, dependency_type=dep_type
        )
        self.db.add(dependency)
        self.db.commit()
        self.db.refresh(dependency)
        return dependency

    def update_task_status(self, task_id: int, status: TaskStatus) -> ProjectTask:
        """Görev durumunu günceller ve proje ilerlemesini hesaplar"""
        task = self.db.query(ProjectTask).get(task_id)
        if not task:
            raise ValueError("Görev bulunamadı")

        task.status = status
        if status == TaskStatus.DONE:
            task.progress = 100

        self.db.commit()
        self.update_project_progress(task.project_id)
        return task

    def add_time_entry(
        self, task_id: int, employee_id: int, hours: float, description: str = ""
    ) -> TimeEntry:
        """Göreve zaman kaydı ekler"""
        entry = TimeEntry(
            task_id=task_id,
            employee_id=employee_id,
            hours=hours,
            description=description,
            entry_date=date.today(),
        )
        self.db.add(entry)

        # Görevdeki toplam çalışma saatini güncelle
        task = self.db.query(ProjectTask).get(task_id)
        task.actual_hours = (task.actual_hours or 0) + hours

        self.db.commit()
        self.db.refresh(entry)
        return entry

    def update_project_progress(self, project_id: int):
        """Projenin genel ilerleme yüzdesini hesaplar"""
        project = self.db.query(Project).get(project_id)
        if not project or not project.tasks:
            return

        total_tasks = len(project.tasks)
        completed_tasks = len([t for t in project.tasks if t.status == TaskStatus.DONE])

        # Basit hesaplama: (Tamamlanan Görev Sayısı / Toplam Görev Sayısı) * 100
        # Daha karmaşık: Görevlerin tahmini saatlerine göre ağırlıklandırma yapılabilir.
        project.progress = (completed_tasks / total_tasks) * 100

        if project.progress == 100:
            project.status = ProjectStatus.COMPLETED
            project.actual_end_date = date.today()

        self.db.commit()

    def get_kanban_data(self, project_id: int) -> Dict[str, List[ProjectTask]]:
        """Kanban görünümü için görevleri gruplar"""
        tasks = (
            self.db.query(ProjectTask)
            .filter(ProjectTask.project_id == project_id)
            .all()
        )
        board = {status.value: [] for status in TaskStatus}
        for task in tasks:
            board[task.status.value].append(task)
        return board

    def get_gantt_data(self, project_id: int) -> List[Dict[str, Any]]:
        """Gantt grafiği için gerekli verileri hazırlar"""
        tasks = (
            self.db.query(ProjectTask)
            .filter(ProjectTask.project_id == project_id)
            .all()
        )
        gantt_tasks = []
        for task in tasks:
            gantt_tasks.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "start": task.start_date.isoformat() if task.start_date else None,
                    "end": task.end_date.isoformat() if task.end_date else None,
                    "progress": float(task.progress),
                    "dependencies": [d.predecessor_id for d in task.dependencies],
                }
            )
        return gantt_tasks
