"""
Akıllı İş - Üretim Takvimi Modelleri
"""

from sqlalchemy import Column, Integer, String, Boolean, Date, Time, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database.base import BaseModel


class ProductionShift(BaseModel):
    """Vardiyalar tablosu"""
    
    __tablename__ = "production_shifts"
    
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    break_minutes = Column(Integer, default=0)
    
    # İlişkiler
    schedules = relationship("WorkstationSchedule", back_populates="shift")
    
    @property
    def duration_hours(self) -> float:
        """Vardiya süresi (saat)"""
        from datetime import datetime, timedelta
        
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        
        # Gece vardiyası (gün geçişi)
        if end < start:
            end += timedelta(days=1)
        
        duration = (end - start).total_seconds() / 3600
        break_hours = (self.break_minutes or 0) / 60
        
        return duration - break_hours
    
    @property
    def net_minutes(self) -> int:
        """Net çalışma süresi (dakika)"""
        return int(self.duration_hours * 60)
    
    def __repr__(self):
        return f"<ProductionShift {self.code}: {self.name}>"


class ProductionHoliday(BaseModel):
    """Tatil günleri tablosu"""
    
    __tablename__ = "production_holidays"
    
    date = Column(Date, unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    is_half_day = Column(Boolean, default=False)
    applies_to_all = Column(Boolean, default=True)  # Tüm istasyonlar için geçerli mi?
    
    def __repr__(self):
        return f"<ProductionHoliday {self.date}: {self.name}>"


class WorkstationSchedule(BaseModel):
    """İş istasyonu çalışma takvimi"""
    
    __tablename__ = "workstation_schedules"
    
    work_station_id = Column(Integer, ForeignKey("work_stations.id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Pazartesi, 6=Pazar
    shift_id = Column(Integer, ForeignKey("production_shifts.id"), nullable=True)
    is_working = Column(Boolean, default=True)
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('work_station_id', 'day_of_week', 'shift_id', name='uq_workstation_day_shift'),
    )
    
    # İlişkiler
    work_station = relationship("WorkStation", backref="schedules")
    shift = relationship("ProductionShift", back_populates="schedules")
    
    @property
    def day_name(self) -> str:
        """Gün adı"""
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        return days[self.day_of_week] if 0 <= self.day_of_week <= 6 else "?"
    
    def __repr__(self):
        return f"<WorkstationSchedule WS:{self.work_station_id} Day:{self.day_of_week}>"
