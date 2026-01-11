"""
Akıllı İş - Kalite Yönetim Modelleri
"""

from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Numeric,
    Enum,
    Index,
)
from sqlalchemy.orm import relationship
import enum

from database.base import BaseModel


class InspectionType(enum.Enum):
    """Kontrol türü"""

    INCOMING = "incoming"  # Giriş kontrolü
    IN_PROCESS = "in_process"  # Proses kontrolü
    FINAL = "final"  # Final kontrol
    PERIODIC = "periodic"  # Periyodik kontrol


class CriteriaType(enum.Enum):
    """Kriter türü"""

    VISUAL = "visual"  # Görsel kontrol
    MEASUREMENT = "measurement"  # Ölçüm
    FUNCTIONAL = "functional"  # Fonksiyonel test
    DOCUMENT = "document"  # Döküman kontrolü


class InspectionStatus(enum.Enum):
    """Kontrol durumu"""

    PENDING = "pending"  # Beklemede
    PASSED = "passed"  # Geçti
    FAILED = "failed"  # Kaldı
    CONDITIONAL = "conditional"  # Şartlı kabul


class NCRSeverity(enum.Enum):
    """Uygunsuzluk şiddeti"""

    MINOR = "minor"  # Küçük
    MAJOR = "major"  # Büyük
    CRITICAL = "critical"  # Kritik


class NCRDisposition(enum.Enum):
    """Uygunsuzluk kararı"""

    REWORK = "rework"  # Yeniden işle
    SCRAP = "scrap"  # Hurda
    USE_AS_IS = "use_as_is"  # Olduğu gibi kullan
    RETURN = "return"  # İade


class NCRStatus(enum.Enum):
    """NCR durumu"""

    OPEN = "open"  # Açık
    ANALYSIS = "analysis"  # Analiz
    ACTION = "action"  # Aksiyon
    VERIFICATION = "verification"  # Doğrulama
    CLOSED = "closed"  # Kapalı


class ComplaintCategory(enum.Enum):
    """Şikayet kategorisi"""

    QUALITY = "quality"  # Kalite
    DELIVERY = "delivery"  # Teslimat
    SERVICE = "service"  # Servis
    DOCUMENTATION = "documentation"  # Dokümantasyon
    OTHER = "other"  # Diğer


class ComplaintPriority(enum.Enum):
    """Şikayet önceliği"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplaintStatus(enum.Enum):
    """Şikayet durumu"""

    OPEN = "open"  # Açık
    INVESTIGATION = "investigation"  # İnceleme
    RESOLUTION = "resolution"  # Çözüm
    CLOSED = "closed"  # Kapalı


class CAPAType(enum.Enum):
    """CAPA türü"""

    CORRECTIVE = "corrective"  # Düzeltici
    PREVENTIVE = "preventive"  # Önleyici


class CAPASource(enum.Enum):
    """CAPA kaynağı"""

    NCR = "ncr"
    AUDIT = "audit"
    CUSTOMER_COMPLAINT = "customer_complaint"
    INTERNAL = "internal"


class CAPAStatus(enum.Enum):
    """CAPA durumu"""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    VERIFICATION = "verification"
    CLOSED = "closed"


class AuditType(enum.Enum):
    """Denetim türü"""

    INTERNAL = "internal"  # İç denetim
    EXTERNAL = "external"  # Dış denetim
    SUPPLIER = "supplier"  # Tedarikçi denetimi


class InspectionTemplate(BaseModel):
    """Kontrol şablonları"""

    __tablename__ = "inspection_templates"

    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    inspection_type = Column(Enum(InspectionType), nullable=False)

    # İlişkiler
    criteria = relationship(
        "InspectionCriteria", back_populates="template", cascade="all, delete-orphan"
    )
    inspections = relationship("Inspection", back_populates="template")

    def __repr__(self):
        return f"<InspectionTemplate(code={self.code}, name={self.name})>"


class InspectionCriteria(BaseModel):
    """Kontrol kriterleri"""

    __tablename__ = "inspection_criteria"

    template_id = Column(Integer, ForeignKey("inspection_templates.id"), nullable=False)
    sequence = Column(Integer, default=1)
    name = Column(String(200), nullable=False)
    criteria_type = Column(Enum(CriteriaType), nullable=False)
    specification = Column(Text, nullable=True)
    tolerance_min = Column(Numeric(15, 4), nullable=True)
    tolerance_max = Column(Numeric(15, 4), nullable=True)
    unit = Column(String(20), nullable=True)
    is_required = Column(Boolean, default=True)

    # İlişkiler
    template = relationship("InspectionTemplate", back_populates="criteria")
    results = relationship("InspectionResult", back_populates="criteria")

    __table_args__ = (Index("idx_criteria_template", "template_id"),)

    def __repr__(self):
        return f"<InspectionCriteria(name={self.name})>"


class Inspection(BaseModel):
    """Kalite kontrolleri"""

    __tablename__ = "inspections"

    inspection_no = Column(String(20), unique=True, nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("inspection_templates.id"), nullable=True)

    # Kaynak bilgisi
    source_type = Column(String(20), nullable=True)  # purchase/production/stock
    source_id = Column(Integer, nullable=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)
    lot_no = Column(String(50), nullable=True)

    # Miktar
    quantity = Column(Numeric(15, 4), nullable=True)
    sample_size = Column(Numeric(15, 4), nullable=True)

    # Kontrol bilgileri
    inspector_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    inspection_date = Column(Date, default=date.today)
    status = Column(Enum(InspectionStatus), default=InspectionStatus.PENDING)
    result_summary = Column(Text, nullable=True)

    # İlişkiler
    template = relationship("InspectionTemplate", back_populates="inspections")
    results = relationship(
        "InspectionResult", back_populates="inspection", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_insp_no", "inspection_no"),
        Index("idx_insp_date", "inspection_date"),
        Index("idx_insp_status", "status"),
    )

    def __repr__(self):
        return f"<Inspection(no={self.inspection_no}, status={self.status})>"


class InspectionResult(BaseModel):
    """Kontrol sonuçları"""

    __tablename__ = "inspection_results"

    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    criteria_id = Column(Integer, ForeignKey("inspection_criteria.id"), nullable=False)
    result_value = Column(String(200), nullable=True)
    is_passed = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    # İlişkiler
    inspection = relationship("Inspection", back_populates="results")
    criteria = relationship("InspectionCriteria", back_populates="results")

    __table_args__ = (Index("idx_result_insp", "inspection_id"),)


class NonConformance(BaseModel):
    """Uygunsuzluk kayıtları (NCR)"""

    __tablename__ = "non_conformances"

    ncr_no = Column(String(20), unique=True, nullable=False, index=True)

    # Kaynak
    source_type = Column(String(20), nullable=True)
    source_id = Column(Integer, nullable=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=True)

    # Tespit bilgileri
    detected_at = Column(String(20), nullable=True)  # incoming/process/final
    ncr_type = Column(String(20), nullable=True)  # product/process/supplier
    severity = Column(Enum(NCRSeverity), default=NCRSeverity.MINOR)

    # Detaylar
    description = Column(Text, nullable=False)
    quantity_affected = Column(Numeric(15, 4), nullable=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)
    lot_no = Column(String(50), nullable=True)

    # Analiz ve karar
    root_cause = Column(Text, nullable=True)
    disposition = Column(Enum(NCRDisposition), nullable=True)
    disposition_notes = Column(Text, nullable=True)

    # Durum
    status = Column(Enum(NCRStatus), default=NCRStatus.OPEN)
    reported_by = Column(Integer, ForeignKey("employees.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("employees.id"), nullable=True)
    closed_date = Column(Date, nullable=True)

    # İlişkiler
    capas = relationship("CAPA", back_populates="ncr")

    __table_args__ = (
        Index("idx_ncr_no", "ncr_no"),
        Index("idx_ncr_status", "status"),
        Index("idx_ncr_severity", "severity"),
    )

    def __repr__(self):
        return f"<NonConformance(ncr_no={self.ncr_no}, status={self.status})>"


class CustomerComplaint(BaseModel):
    """Müşteri şikayetleri"""

    __tablename__ = "customer_complaints"

    complaint_no = Column(String(20), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    complaint_date = Column(Date, default=date.today)

    # Kategori ve öncelik
    category = Column(Enum(ComplaintCategory), default=ComplaintCategory.QUALITY)
    priority = Column(Enum(ComplaintPriority), default=ComplaintPriority.MEDIUM)

    # Şikayet detayları
    description = Column(Text, nullable=False)
    product_info = Column(String(200), nullable=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)
    lot_no = Column(String(50), nullable=True)
    invoice_no = Column(String(50), nullable=True)

    # Analiz
    root_cause = Column(Text, nullable=True)
    immediate_action = Column(Text, nullable=True)

    # Durum
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.OPEN)
    assigned_to = Column(Integer, ForeignKey("employees.id"), nullable=True)
    resolution = Column(Text, nullable=True)
    resolution_date = Column(Date, nullable=True)

    # Müşteri geri bildirimi
    customer_feedback = Column(Text, nullable=True)
    satisfaction_score = Column(Integer, nullable=True)  # 1-5

    # İlişkiler
    capas = relationship("CAPA", back_populates="complaint")

    __table_args__ = (
        Index("idx_complaint_no", "complaint_no"),
        Index("idx_complaint_status", "status"),
        Index("idx_complaint_date", "complaint_date"),
    )

    def __repr__(self):
        return f"<CustomerComplaint(no={self.complaint_no}, status={self.status})>"


class CAPA(BaseModel):
    """Düzeltici/Önleyici Faaliyetler"""

    __tablename__ = "capas"

    capa_no = Column(String(20), unique=True, nullable=False, index=True)
    capa_type = Column(Enum(CAPAType), nullable=False)
    source = Column(Enum(CAPASource), nullable=False)

    # Kaynak bağlantıları
    ncr_id = Column(Integer, ForeignKey("non_conformances.id"), nullable=True)
    complaint_id = Column(Integer, ForeignKey("customer_complaints.id"), nullable=True)
    audit_id = Column(Integer, ForeignKey("audits.id"), nullable=True)

    # Detaylar
    description = Column(Text, nullable=False)
    root_cause_analysis = Column(Text, nullable=True)
    action_plan = Column(Text, nullable=True)

    # Sorumluluk
    responsible_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    target_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)

    # Doğrulama
    verification_result = Column(Text, nullable=True)
    verified_by = Column(Integer, ForeignKey("employees.id"), nullable=True)
    verification_date = Column(Date, nullable=True)

    # Durum
    status = Column(Enum(CAPAStatus), default=CAPAStatus.OPEN)

    # İlişkiler
    ncr = relationship("NonConformance", back_populates="capas")
    complaint = relationship("CustomerComplaint", back_populates="capas")
    audit = relationship("Audit", back_populates="capas")

    __table_args__ = (
        Index("idx_capa_no", "capa_no"),
        Index("idx_capa_status", "status"),
        Index("idx_capa_type", "capa_type"),
    )

    def __repr__(self):
        return f"<CAPA(capa_no={self.capa_no}, type={self.capa_type})>"


class Audit(BaseModel):
    """Denetimler"""

    __tablename__ = "audits"

    audit_no = Column(String(20), unique=True, nullable=False, index=True)
    audit_type = Column(Enum(AuditType), nullable=False)

    # Denetim bilgileri
    auditee = Column(String(200), nullable=True)  # Denetlenen birim/firma
    auditor_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    lead_auditor = Column(String(100), nullable=True)

    # Tarihler
    planned_date = Column(Date, nullable=True)
    actual_date = Column(Date, nullable=True)

    # Kapsam ve bulgular
    scope = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)

    # Durum
    status = Column(String(20), default="planned")  # planned/ongoing/completed

    # İlişkiler
    capas = relationship("CAPA", back_populates="audit")

    __table_args__ = (
        Index("idx_audit_no", "audit_no"),
        Index("idx_audit_type", "audit_type"),
    )

    def __repr__(self):
        return f"<Audit(audit_no={self.audit_no}, type={self.audit_type})>"
