"""
Akıllı İş - Performans Değerlendirme Modelleri

Yıllık/dönemsel performans değerlendirme, hedef takibi ve yetkinlik değerlendirmesi.
"""

from datetime import date
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    Numeric,
    ForeignKey,
    Enum,
    Boolean,
    Index,
)
from sqlalchemy.orm import relationship

from database.base import Base


class EvaluationPeriodType(PyEnum):
    """Değerlendirme dönem türleri"""

    ANNUAL = "annual"  # Yıllık
    SEMI_ANNUAL = "semi_annual"  # 6 aylık
    QUARTERLY = "quarterly"  # Çeyreklik
    MONTHLY = "monthly"  # Aylık
    PROBATION = "probation"  # Deneme süresi


class EvaluationStatus(PyEnum):
    """Değerlendirme durumları"""

    DRAFT = "draft"  # Taslak
    PENDING_SELF = "pending_self"  # Özdeğerlendirme bekliyor
    PENDING_MANAGER = "pending_manager"  # Yönetici değerlendirmesi bekliyor
    PENDING_HR = "pending_hr"  # İK onayı bekliyor
    COMPLETED = "completed"  # Tamamlandı
    CANCELLED = "cancelled"  # İptal


class CompetencyCategory(PyEnum):
    """Yetkinlik kategorileri"""

    TECHNICAL = "technical"  # Teknik yetkinlikler
    BEHAVIORAL = "behavioral"  # Davranışsal yetkinlikler
    LEADERSHIP = "leadership"  # Liderlik yetkinlikleri
    COMMUNICATION = "communication"  # İletişim
    TEAMWORK = "teamwork"  # Takım çalışması


class PerformanceRating(PyEnum):
    """Performans puanları"""

    EXCEPTIONAL = "exceptional"  # 5 - Olağanüstü
    EXCEEDS = "exceeds"  # 4 - Beklentinin üzerinde
    MEETS = "meets"  # 3 - Beklentiyi karşılıyor
    NEEDS_IMPROVEMENT = "needs_improvement"  # 2 - Gelişim gerekli
    UNSATISFACTORY = "unsatisfactory"  # 1 - Yetersiz


class EvaluationPeriod(Base):
    """
    Değerlendirme Dönemi

    Şirket genelinde değerlendirme dönemlerini tanımlar.
    """

    __tablename__ = "evaluation_periods"

    id = Column(Integer, primary_key=True)

    # Dönem adı (ör: "2026 Yıllık Değerlendirme")
    name = Column(String(100), nullable=False)

    # Dönem türü
    period_type = Column(Enum(EvaluationPeriodType), nullable=False)

    # Tarih aralığı
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Değerlendirme tarihleri
    evaluation_start = Column(Date, nullable=True)  # Değerlendirme başlangıcı
    evaluation_end = Column(Date, nullable=True)  # Değerlendirme bitişi

    # Durum
    is_active = Column(Boolean, default=True)

    # Açıklama
    description = Column(Text, nullable=True)

    # İlişkiler
    evaluations = relationship("PerformanceEvaluation", back_populates="period")

    __table_args__ = (Index("idx_eval_period_dates", "start_date", "end_date"),)


class Competency(Base):
    """
    Yetkinlik Tanımları

    Şirket genelinde kullanılacak yetkinlik havuzu.
    """

    __tablename__ = "competencies"

    id = Column(Integer, primary_key=True)

    # Yetkinlik adı
    name = Column(String(100), nullable=False)

    # Kategori
    category = Column(Enum(CompetencyCategory), nullable=False)

    # Açıklama
    description = Column(Text, nullable=True)

    # Ağırlık (varsayılan 1.0)
    weight = Column(Numeric(3, 2), default=1.0)

    # Aktif mi
    is_active = Column(Boolean, default=True)

    # Sıralama
    sort_order = Column(Integer, default=0)


class PerformanceEvaluation(Base):
    """
    Performans Değerlendirmesi

    Çalışan bazında dönemsel değerlendirme kaydı.
    """

    __tablename__ = "performance_evaluations"

    id = Column(Integer, primary_key=True)

    # Çalışan ve dönem
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("evaluation_periods.id"), nullable=False)

    # Değerlendiren (yönetici)
    evaluator_id = Column(Integer, ForeignKey("employees.id"), nullable=True)

    # Durum
    status = Column(Enum(EvaluationStatus), default=EvaluationStatus.DRAFT)

    # Özdeğerlendirme tarihi
    self_evaluation_date = Column(Date, nullable=True)

    # Yönetici değerlendirme tarihi
    manager_evaluation_date = Column(Date, nullable=True)

    # Genel puanlar (1-5 ölçeği)
    self_rating = Column(Numeric(3, 2), nullable=True)  # Özdeğerlendirme
    manager_rating = Column(Numeric(3, 2), nullable=True)  # Yönetici
    final_rating = Column(Numeric(3, 2), nullable=True)  # Nihai puan

    # Sonuç
    overall_result = Column(Enum(PerformanceRating), nullable=True)

    # Yorumlar
    self_comments = Column(Text, nullable=True)
    manager_comments = Column(Text, nullable=True)
    hr_comments = Column(Text, nullable=True)

    # Güçlü yönler / Gelişim alanları
    strengths = Column(Text, nullable=True)
    areas_for_improvement = Column(Text, nullable=True)

    # Gelişim planı
    development_plan = Column(Text, nullable=True)

    # İK onayı
    hr_approved_by = Column(Integer, ForeignKey("employees.id"), nullable=True)
    hr_approved_date = Column(Date, nullable=True)

    # İlişkiler
    employee = relationship(
        "Employee", foreign_keys=[employee_id], backref="evaluations"
    )
    evaluator = relationship("Employee", foreign_keys=[evaluator_id])
    period = relationship("EvaluationPeriod", back_populates="evaluations")
    competency_scores = relationship(
        "CompetencyScore", back_populates="evaluation", cascade="all, delete-orphan"
    )
    goals = relationship(
        "PerformanceGoal", back_populates="evaluation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_eval_employee", "employee_id"),
        Index("idx_eval_period", "period_id"),
        Index("idx_eval_status", "status"),
    )


class CompetencyScore(Base):
    """
    Yetkinlik Puanları

    Değerlendirme içinde her yetkinlik için verilen puanlar.
    """

    __tablename__ = "competency_scores"

    id = Column(Integer, primary_key=True)

    evaluation_id = Column(
        Integer, ForeignKey("performance_evaluations.id"), nullable=False
    )
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False)

    # Puanlar (1-5)
    self_score = Column(Numeric(3, 2), nullable=True)
    manager_score = Column(Numeric(3, 2), nullable=True)

    # Yorumlar
    self_comment = Column(Text, nullable=True)
    manager_comment = Column(Text, nullable=True)

    # İlişkiler
    evaluation = relationship(
        "PerformanceEvaluation", back_populates="competency_scores"
    )
    competency = relationship("Competency")

    __table_args__ = (Index("idx_comp_score_eval", "evaluation_id"),)


class PerformanceGoal(Base):
    """
    Performans Hedefleri

    Dönem içinde takip edilen hedefler ve gerçekleşmeleri.
    """

    __tablename__ = "performance_goals"

    id = Column(Integer, primary_key=True)

    evaluation_id = Column(
        Integer, ForeignKey("performance_evaluations.id"), nullable=False
    )

    # Hedef tanımı
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Ağırlık (%)
    weight = Column(Numeric(5, 2), default=20)

    # Hedef değer (sayısal hedefler için)
    target_value = Column(Numeric(15, 2), nullable=True)
    actual_value = Column(Numeric(15, 2), nullable=True)

    # Gerçekleşme oranı (%)
    achievement_rate = Column(Numeric(5, 2), nullable=True)

    # Puan (1-5)
    score = Column(Numeric(3, 2), nullable=True)

    # Yorumlar
    employee_comment = Column(Text, nullable=True)
    manager_comment = Column(Text, nullable=True)

    # Tarihler
    due_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)

    # İlişkiler
    evaluation = relationship("PerformanceEvaluation", back_populates="goals")

    __table_args__ = (Index("idx_goal_eval", "evaluation_id"),)
