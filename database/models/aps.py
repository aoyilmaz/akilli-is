"""
Akıllı İş - APS (İleri Planlama & Çizelgeleme) Modelleri
"""

from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,
)
from sqlalchemy.orm import relationship
from database.base import BaseModel


class SchedulingMode(str, Enum):
    """Çizelgeleme Modu"""

    FORWARD = "forward"  # En erken başlama (ASAP)
    BACKWARD = "backward"  # En geç bitiş (JIT)


class APSScenario(BaseModel):
    """
    APS Senaryoları.
    Farklı planlama alternatiflerini karşılaştırmak için kullanılır.
    """

    __tablename__ = "aps_scenarios"

    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=False)  # Aktif planlama senaryosu mu?

    start_date = Column(DateTime)
    end_date = Column(DateTime)

    # Senaryo parametreleri (Örn: öncelik ağırlıkları, kısıtlar)
    settings = Column(JSON)

    # İlişkiler
    planned_tasks = relationship(
        "PlannedTask", back_populates="scenario", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<APSScenario {self.name}>"


class PlannedTask(BaseModel):
    """
    Senaryo bazlı planlanmış görevler/operasyonlar.
    """

    __tablename__ = "aps_planned_tasks"

    scenario_id = Column(
        Integer, ForeignKey("aps_scenarios.id", ondelete="CASCADE"), nullable=False
    )
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=False)
    operation_id = Column(
        Integer, ForeignKey("work_order_operations.id"), nullable=False
    )
    work_station_id = Column(Integer, ForeignKey("work_stations.id"), nullable=False)

    planned_start = Column(DateTime, nullable=False)
    planned_end = Column(DateTime, nullable=False)

    setup_time = Column(Integer, default=0)  # dakika
    run_time = Column(Integer, default=0)  # dakika

    priority = Column(Integer, default=1)
    is_locked = Column(Boolean, default=False)  # Manuel sabitlenmiş görev

    # İlişkiler
    scenario = relationship("APSScenario", back_populates="planned_tasks")
    work_order = relationship("WorkOrder")
    operation = relationship("WorkOrderOperation")
    work_station = relationship("WorkStation")

    def __repr__(self):
        return f"<PlannedTask {self.id}: {self.planned_start}>"
