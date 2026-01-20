"""
Akıllı İş - Özlük Dosyası ve İzin Hakediş Modelleri

Personel belgeleri yönetimi ve yıllık izin hakediş otomasyonu.
"""

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


class DocumentType(PyEnum):
    """Belge türleri"""

    CONTRACT = "contract"  # İş sözleşmesi
    ID_CARD = "id_card"  # Kimlik belgesi
    DIPLOMA = "diploma"  # Diploma
    CERTIFICATE = "certificate"  # Sertifika
    HEALTH_REPORT = "health_report"  # Sağlık raporu
    CRIMINAL_RECORD = "criminal_record"  # Adli sicil
    PHOTO = "photo"  # Fotoğraf
    OTHER = "other"  # Diğer


class DocumentStatus(PyEnum):
    """Belge durumları"""

    VALID = "valid"  # Geçerli
    EXPIRING_SOON = "expiring_soon"  # Yakında sona erecek
    EXPIRED = "expired"  # Süresi dolmuş
    MISSING = "missing"  # Eksik


class LeaveEntitlementType(PyEnum):
    """İzin hakediş türleri"""

    ANNUAL = "annual"  # Yıllık izin
    SENIORITY = "seniority"  # Kıdem izni
    MARRIAGE = "marriage"  # Evlilik izni
    MATERNITY = "maternity"  # Doğum izni
    PATERNITY = "paternity"  # Babalık izni
    BEREAVEMENT = "bereavement"  # Vefat izni


class EmployeeDocument(Base):
    """
    Özlük Dosyası - Çalışan Belgeleri

    Çalışanlara ait tüm resmi belgelerin kaydı.
    """

    __tablename__ = "employee_documents"

    id = Column(Integer, primary_key=True)

    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Belge bilgileri
    document_type = Column(Enum(DocumentType), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Dosya
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes
    mime_type = Column(String(100), nullable=True)

    # Tarihler
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)

    # Durum
    status = Column(Enum(DocumentStatus), default=DocumentStatus.VALID)

    # Meta
    is_mandatory = Column(Boolean, default=False)  # Zorunlu mu?
    notes = Column(Text, nullable=True)

    # İlişkiler
    employee = relationship("Employee", backref="documents")

    __table_args__ = (
        Index("idx_doc_employee", "employee_id"),
        Index("idx_doc_type", "document_type"),
        Index("idx_doc_expiry", "expiry_date"),
        Index("idx_doc_status", "status"),
    )


class LeaveEntitlementRule(Base):
    """
    İzin Hakediş Kuralları

    Kıdeme göre yıllık izin hakediş tanımları.
    """

    __tablename__ = "leave_entitlement_rules"

    id = Column(Integer, primary_key=True)

    # Kural adı
    name = Column(String(100), nullable=False)

    # İzin türü
    leave_type = Column(Enum(LeaveEntitlementType), nullable=False)

    # Kıdem aralığı (yıl)
    min_years = Column(Integer, default=0)
    max_years = Column(Integer, nullable=True)  # null = sınırsız

    # Hakediş miktarı (gün)
    days_entitled = Column(Integer, nullable=False)

    # Aktif mi?
    is_active = Column(Boolean, default=True)

    # Açıklama
    description = Column(Text, nullable=True)

    __table_args__ = (Index("idx_rule_type", "leave_type"),)


class LeaveBalance(Base):
    """
    İzin Bakiyesi

    Çalışan bazında izin hakedişleri ve kullanımları.
    """

    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True)

    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Dönem
    year = Column(Integer, nullable=False)

    # İzin türü
    leave_type = Column(Enum(LeaveEntitlementType), nullable=False)

    # Bakiyeler (gün)
    carried_over = Column(Numeric(5, 2), default=0)  # Devreden
    entitled = Column(Numeric(5, 2), default=0)  # Hakediş
    used = Column(Numeric(5, 2), default=0)  # Kullanılan
    pending = Column(Numeric(5, 2), default=0)  # Bekleyen talep

    # Hesaplanan bakiye = carried_over + entitled - used - pending

    # İlişkiler
    employee = relationship("Employee", backref="leave_balances")

    __table_args__ = (
        Index("idx_balance_employee", "employee_id"),
        Index("idx_balance_year", "year"),
        Index("idx_balance_type", "leave_type"),
    )

    @property
    def available(self) -> float:
        """Kullanılabilir bakiye"""
        co = float(self.carried_over or 0)
        ent = float(self.entitled or 0)
        used = float(self.used or 0)
        pend = float(self.pending or 0)
        return co + ent - used - pend
