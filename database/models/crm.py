"""
CRM (Müşteri İlişkileri Yönetimi) veritabanı modelleri
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Enum,
    Text,
    Date,
)
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from ..base import BaseModel
from .user import User


class LeadStatus(enum.Enum):
    """Aday Müşteri Durumları"""

    NEW = "Yeni"
    CONTACTED = "İletişime Geçildi"
    QUALIFIED = "Kalifiye"
    LOST = "Kayıp"
    CONVERTED = "Dönüştürüldü"


class LeadSource(enum.Enum):
    """Aday Müşteri Kaynakları"""

    WEB = "Web Sitesi"
    REFERRAL = "Referans"
    EVENT = "Etkinlik"
    ADS = "Reklam"  # case-insensitive olduğu için 'Ads' yerine 'ADS' kullanabiliriz ama UI'da görünen değer "Reklam"
    COLD_CALL = "Soğuk Arama"
    OTHER = "Diğer"


class OpportunityStage(enum.Enum):
    """Fırsat Aşamaları"""

    NEW = "Yeni"
    QUALIFIED = "Kalifiye"
    PROPOSITION = "Teklif"
    NEGOTIATION = "Pazarlık"
    WON = "Kazanıldı"
    LOST = "Kaybedildi"


class ActivityType(enum.Enum):
    """Aktivite Tipleri"""

    CALL = "Arama"
    MEETING = "Toplantı"
    EMAIL = "E-posta"
    NOTE = "Not"
    TASK = "Görev"


class Lead(BaseModel):
    """Aday Müşteri Modeli"""

    __tablename__ = "leads"

    # Temel Bilgiler
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    company_name = Column(String(200))
    title = Column(String(100))

    # İletişim
    email = Column(String(100))
    phone = Column(String(30))
    mobile = Column(String(30))
    website = Column(String(200))

    # Adres
    address = Column(Text)
    city = Column(String(50))
    country = Column(String(50), default="Türkiye")

    # Durum ve Kaynak
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW, nullable=False)
    source = Column(Enum(LeadSource), default=LeadSource.OTHER)

    # Notlar
    notes = Column(Text)

    # Atanan Kişi
    assigned_to_id = Column(Integer, ForeignKey("users.id"))
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])

    def to_dict(self):
        """Sözlük formatına çevir"""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "company_name": self.company_name,
            "title": self.title,
            "email": self.email,
            "phone": self.phone,
            "mobile": self.mobile,
            "website": self.website,
            "address": self.address,
            "city": self.city,
            "country": self.country,
            "status": self.status.value if self.status else None,
            "source": self.source.value if self.source else None,
            "notes": self.notes,
            "assigned_to_id": self.assigned_to_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Opportunity(BaseModel):
    """Fırsat Modeli"""

    __tablename__ = "opportunities"

    name = Column(String(200), nullable=False)

    # İlişkiler (Aday veya Müşteri olabilir)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    lead = relationship("Lead")

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer = relationship(
        "Customer", foreign_keys=[customer_id]
    )  # Customer modelini string referansla veriyoruz, sales modülü import döngüsü yaratmasın diye

    # Finansal
    expected_revenue = Column(Float, default=0.0)
    probability = Column(Integer, default=0)  # 0-100 arası
    currency = Column(String(3), default="TRY")

    # Durum
    stage = Column(Enum(OpportunityStage), default=OpportunityStage.NEW, nullable=False)
    closing_date = Column(Date)

    # Diğer
    description = Column(Text)
    next_step = Column(String(200))

    # Atanan Kişi
    assigned_to_id = Column(Integer, ForeignKey("users.id"))
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])


class Activity(BaseModel):
    """Aktivite Modeli"""

    __tablename__ = "activities"

    subject = Column(String(200), nullable=False)
    activity_type = Column(Enum(ActivityType), nullable=False)

    due_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)

    # İlişkiler
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    lead = relationship("Lead")

    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    opportunity = relationship("Opportunity")

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    # customer relationship lazy loaded elsewhere if needed

    # Atanan Kişi
    assigned_to_id = Column(Integer, ForeignKey("users.id"))
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])

    description = Column(Text)
    result = Column(Text)
