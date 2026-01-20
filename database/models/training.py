"""
Akıllı İş - Eğitim Takibi Modelleri

Personel eğitimleri, sertifikalar ve yetkinlik geliştirme takibi.
"""

from datetime import date
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


class TrainingStatus(PyEnum):
    """Eğitim durumları"""

    PLANNED = "planned"  # Planlandı
    IN_PROGRESS = "in_progress"  # Devam ediyor
    COMPLETED = "completed"  # Tamamlandı
    CANCELLED = "cancelled"  # İptal


class TrainingType(PyEnum):
    """Eğitim türleri"""

    INTERNAL = "internal"  # İç eğitim
    EXTERNAL = "external"  # Dış eğitim
    ONLINE = "online"  # Çevrimiçi
    ON_THE_JOB = "on_the_job"  # İş başı eğitim
    CERTIFICATION = "certification"  # Sertifikalı kurs


class CertificateStatus(PyEnum):
    """Sertifika durumları"""

    VALID = "valid"  # Geçerli
    EXPIRING_SOON = "expiring_soon"  # Yakında sona erecek
    EXPIRED = "expired"  # Süresi dolmuş
    RENEWED = "renewed"  # Yenilendi


class Training(Base):
    """
    Eğitim Tanımları

    Şirket genelinde verilebilecek eğitimler.
    """

    __tablename__ = "trainings"

    id = Column(Integer, primary_key=True)

    # Eğitim bilgileri
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Eğitim türü
    training_type = Column(Enum(TrainingType), default=TrainingType.INTERNAL)

    # Süre (saat)
    duration_hours = Column(Numeric(5, 1), nullable=True)

    # Eğitmen/Kurum
    trainer_name = Column(String(200), nullable=True)
    training_provider = Column(String(200), nullable=True)

    # Maliyet
    cost = Column(Numeric(15, 2), nullable=True)
    currency = Column(String(3), default="TRY")

    # Sertifikalı mı?
    has_certificate = Column(Boolean, default=False)
    certificate_validity_months = Column(Integer, nullable=True)

    # Aktif mi?
    is_active = Column(Boolean, default=True)

    # İlişkiler
    sessions = relationship("TrainingSession", back_populates="training")


class TrainingSession(Base):
    """
    Eğitim Oturumları

    Belirli tarihlerde gerçekleştirilen eğitim seansları.
    """

    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True)

    training_id = Column(Integer, ForeignKey("trainings.id"), nullable=False)

    # Tarih bilgileri
    planned_date = Column(Date, nullable=False)
    actual_date = Column(Date, nullable=True)

    # Lokasyon
    location = Column(String(200), nullable=True)
    is_online = Column(Boolean, default=False)

    # Durum
    status = Column(Enum(TrainingStatus), default=TrainingStatus.PLANNED)

    # Kapasit
    max_participants = Column(Integer, nullable=True)

    # Notlar
    notes = Column(Text, nullable=True)

    # İlişkiler
    training = relationship("Training", back_populates="sessions")
    participants = relationship(
        "TrainingParticipant", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_session_training", "training_id"),
        Index("idx_session_date", "planned_date"),
        Index("idx_session_status", "status"),
    )


class TrainingParticipant(Base):
    """
    Eğitim Katılımcıları

    Eğitime katılan çalışanlar ve sonuçları.
    """

    __tablename__ = "training_participants"

    id = Column(Integer, primary_key=True)

    session_id = Column(Integer, ForeignKey("training_sessions.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Katılım durumu
    attended = Column(Boolean, default=False)
    attendance_hours = Column(Numeric(5, 1), nullable=True)

    # Değerlendirme (1-5)
    score = Column(Numeric(3, 2), nullable=True)
    passed = Column(Boolean, nullable=True)

    # Geri bildirim
    feedback = Column(Text, nullable=True)

    # Sertifika verildi mi?
    certificate_issued = Column(Boolean, default=False)
    certificate_date = Column(Date, nullable=True)

    # İlişkiler
    session = relationship("TrainingSession", back_populates="participants")
    employee = relationship("Employee", backref="training_participations")

    __table_args__ = (
        Index("idx_participant_session", "session_id"),
        Index("idx_participant_employee", "employee_id"),
    )


class EmployeeCertificate(Base):
    """
    Çalışan Sertifikaları

    Çalışanların sahip olduğu sertifikalar ve geçerlilik süreleri.
    """

    __tablename__ = "employee_certificates"

    id = Column(Integer, primary_key=True)

    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Sertifika bilgileri
    name = Column(String(200), nullable=False)
    issuing_authority = Column(String(200), nullable=True)
    certificate_number = Column(String(100), nullable=True)

    # Tarihler
    issue_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)

    # Durum
    status = Column(Enum(CertificateStatus), default=CertificateStatus.VALID)

    # Eğitim bağlantısı (opsiyonel)
    training_id = Column(Integer, ForeignKey("trainings.id"), nullable=True)

    # Dosya
    document_path = Column(String(500), nullable=True)

    # Notlar
    notes = Column(Text, nullable=True)

    # İlişkiler
    employee = relationship("Employee", backref="certificates")
    training = relationship("Training")

    __table_args__ = (
        Index("idx_cert_employee", "employee_id"),
        Index("idx_cert_expiry", "expiry_date"),
        Index("idx_cert_status", "status"),
    )
