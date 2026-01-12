"""
Akıllı İş - Vardiya Ekibi ve Rotasyon Modelleri
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from database.base import BaseModel


class ShiftTeam(BaseModel):
    """Vardiya ekipleri tablosu (A, B, C ekipleri)"""

    __tablename__ = "shift_teams"

    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#6366f1")  # Hex renk kodu

    # İlişkiler
    employees = relationship("Employee", back_populates="shift_team")
    rotation_schedules = relationship("RotationSchedule", back_populates="team")

    __table_args__ = (Index("idx_shift_team_code", "code"),)

    def __repr__(self):
        return f"<ShiftTeam {self.code}: {self.name}>"


class RotationPattern(BaseModel):
    """Rotasyon şablonu (2x12, 3x8 gibi)"""

    __tablename__ = "rotation_patterns"

    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Döngü bilgileri
    cycle_days = Column(Integer, nullable=False, default=6)  # Döngü gün sayısı
    shifts_per_day = Column(Integer, nullable=False, default=2)  # Günlük vardiya sayısı

    # İlişkiler
    schedules = relationship(
        "RotationSchedule", back_populates="pattern", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_rotation_pattern_code", "code"),)

    def __repr__(self):
        return f"<RotationPattern {self.code}: {self.name}>"


class RotationSchedule(BaseModel):
    """Rotasyon takvimi - Hangi gün hangi ekip hangi vardiyada"""

    __tablename__ = "rotation_schedules"

    # Şablon ilişkisi
    pattern_id = Column(
        Integer, ForeignKey("rotation_patterns.id", ondelete="CASCADE"), nullable=False
    )

    # Döngü içindeki gün (1'den başlar)
    day_in_cycle = Column(Integer, nullable=False)

    # Vardiya ilişkisi
    shift_id = Column(Integer, ForeignKey("production_shifts.id"), nullable=False)

    # Ekip ilişkisi (NULL ise o vardiyada çalışılmıyor)
    team_id = Column(Integer, ForeignKey("shift_teams.id"), nullable=True)

    # İlişkiler
    pattern = relationship("RotationPattern", back_populates="schedules")
    shift = relationship("ProductionShift")
    team = relationship("ShiftTeam", back_populates="rotation_schedules")

    __table_args__ = (
        Index("idx_rotation_pattern_day", "pattern_id", "day_in_cycle"),
        Index("idx_rotation_team", "team_id"),
    )

    def __repr__(self):
        return f"<RotationSchedule Pattern:{self.pattern_id} Day:{self.day_in_cycle}>"
