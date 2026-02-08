"""
Akıllı İş - Proje Yönetimi Modelleri
"""

from datetime import date
import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    ForeignKey,
    Numeric,
    Enum,
    Index,
)
from sqlalchemy.orm import relationship
from database.base import BaseModel


class ProjectStatus(enum.Enum):
    """Proje durumu"""

    STAGING = "staging"  # Hazırlık
    ACTIVE = "active"  # Aktif
    ON_HOLD = "on_hold"  # Beklemede
    COMPLETED = "completed"  # Tamamlandı
    CANCELLED = "cancelled"  # İptal


class TaskPriority(enum.Enum):
    """Görev önceliği"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(enum.Enum):
    """Görev durumu"""

    TODO = "todo"  # Yapılacak
    IN_PROGRESS = "in_progress"  # Devam Ediyor
    REVIEW = "review"  # İncelemede
    DONE = "done"  # Tamamlandı
    BLOCKED = "blocked"  # Engellendi


class DependencyType(enum.Enum):
    """Bağımlılık türü"""

    FS = "fs"  # Finish-to-Start (Önceki bitince bu başlar)
    SS = "ss"  # Start-to-Start (Birlikte başlar)
    FF = "ff"  # Finish-to-Finish (Birlikte biter)
    SF = "sf"  # Start-to-Finish


class Project(BaseModel):
    """Projeler tablosu"""

    __tablename__ = "projects"

    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)

    budget = Column(Numeric(15, 2), default=0)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=True)
    status: Column[ProjectStatus] = Column(
        Enum(ProjectStatus), default=ProjectStatus.STAGING
    )

    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    progress = Column(Numeric(5, 2), default=0)  # 0-100 arası

    # İlişkiler
    customer = relationship("Customer")
    currency = relationship("Currency")
    manager = relationship("Employee")
    tasks = relationship(
        "ProjectTask", back_populates="project", cascade="all, delete-orphan"
    )
    resources = relationship("ProjectResource", back_populates="project")

    def __repr__(self):
        return f"<Project(code={self.code}, name={self.name})>"


class ProjectTask(BaseModel):
    """Proje görevleri tablosu"""

    __tablename__ = "project_tasks"

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    code = Column(String(20), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    status: Column[TaskStatus] = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority: Column[TaskPriority] = Column(
        Enum(TaskPriority), default=TaskPriority.MEDIUM
    )

    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    duration_days = Column(Integer, default=1)

    assigned_to = Column(Integer, ForeignKey("employees.id"), nullable=True)
    progress = Column(Numeric(5, 2), default=0)

    estimated_hours = Column(Numeric(10, 2), default=0)
    actual_hours = Column(Numeric(10, 2), default=0)

    # İlişkiler
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("Employee")
    dependencies = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    time_entries = relationship("TimeEntry", back_populates="task")

    def __repr__(self):
        return f"<ProjectTask(id={self.id}, title={self.title})>"


class TaskDependency(BaseModel):
    """Görevler arası bağımlılıklar"""

    __tablename__ = "task_dependencies"

    task_id = Column(Integer, ForeignKey("project_tasks.id"), nullable=False)
    predecessor_id = Column(Integer, ForeignKey("project_tasks.id"), nullable=False)
    dependency_type: Column[DependencyType] = Column(
        Enum(DependencyType), default=DependencyType.FS
    )
    lag_days = Column(Integer, default=0)

    # İlişkiler
    task = relationship(
        "ProjectTask", foreign_keys=[task_id], back_populates="dependencies"
    )
    predecessor = relationship("ProjectTask", foreign_keys=[predecessor_id])


class ProjectResource(BaseModel):
    """Projeye atanan kaynaklar (Personel)"""

    __tablename__ = "project_resources"

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    role = Column(String(50), nullable=True)  # Analist, Geliştirici, vb.
    allocation_percent = Column(Numeric(5, 2), default=100)  # % kaç kapasite ile atandı

    # İlişkiler
    project = relationship("Project", back_populates="resources")
    employee = relationship("Employee")


class TimeEntry(BaseModel):
    """Zaman kayıtları (Timesheets)"""

    __tablename__ = "project_time_entries"

    task_id = Column(Integer, ForeignKey("project_tasks.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    entry_date = Column(Date, default=date.today)
    hours = Column(Numeric(5, 2), nullable=False)
    description = Column(Text, nullable=True)

    # İlişkiler
    task = relationship("ProjectTask", back_populates="time_entries")
    employee = relationship("Employee")

    __table_args__ = (
        Index("idx_time_entry_task", "task_id"),
        Index("idx_time_entry_emp", "employee_id"),
        Index("idx_time_entry_date", "entry_date"),
    )
