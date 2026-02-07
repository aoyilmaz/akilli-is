"""
Akıllı İş - e-Fatura / e-Arşiv / e-İrsaliye Modelleri
"""

from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    LargeBinary,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
from database.base import BaseModel


class EInvoiceDirection(str, Enum):
    OUTGOING = "outgoing"  # Giden
    INCOMING = "incoming"  # Gelen


class EInvoiceType(str, Enum):
    EINVOICE = "einvoice"  # e-Fatura (kayıtlı mükelleflere)
    EARCHIVE = "earchive"  # e-Arşiv (kayıtsız mükelleflere)
    EDESPATCH = "edespatch"  # e-İrsaliye


class EInvoiceStatus(str, Enum):
    DRAFT = "draft"  # Taslak
    QUEUED = "queued"  # Kuyrukta (Gönderilmeyi bekliyor)
    PROCESSING = "processing"  # İşleniyor
    SENT = "sent"  # Gönderildi (GIB'e iletildi)
    DELIVERED = "delivered"  # Alıcıya teslim edildi
    ACCEPTED = "accepted"  # Kabul edildi (Ticari fatura için)
    REJECTED = "rejected"  # Reddedildi
    CANCELLED = "cancelled"  # İptal edildi (e-Arşiv için)
    ERROR = "error"  # Hata aldı


class EInvoiceProfile(str, Enum):
    TEMELFATURA = "TEMELFATURA"
    TICARIFATURA = "TICARIFATURA"
    EARSIVFATURA = "EARSIVFATURA"
    IHRACAT = "IHRACAT"


class EInvoice(BaseModel):
    """e-Fatura / e-Arşiv / e-İrsaliye Ana Tablosu"""

    __tablename__ = "einvoices"

    # Benzersiz Tanımlayıcılar
    uuid = Column(
        String(36), unique=True, nullable=False, index=True
    )  # GIB UUID (GUID)
    ettn = Column(
        String(36), unique=True, nullable=True, index=True
    )  # Evrensel Tekil Tanımlama No (Genelde UUID ile aynıdır)

    # Belge İlişkisi
    invoice_id = Column(
        Integer, ForeignKey("invoices.id"), nullable=True
    )  # Satış faturası
    purchase_invoice_id = Column(
        Integer, ForeignKey("purchase_invoices.id"), nullable=True
    )  # Alış faturası
    delivery_note_id = Column(
        Integer, ForeignKey("delivery_notes.id"), nullable=True
    )  # İrsaliye

    # Temel Bilgiler
    direction = Column(SQLEnum(EInvoiceDirection), nullable=False)
    type = Column(SQLEnum(EInvoiceType), nullable=False)
    status = Column(SQLEnum(EInvoiceStatus), default=EInvoiceStatus.DRAFT, index=True)
    profile = Column(SQLEnum(EInvoiceProfile), default=EInvoiceProfile.TICARIFATURA)

    # Fatura No ve Seri
    invoice_number = Column(
        String(16), nullable=True, index=True
    )  # GIB fatura no (ABC2026000001)
    series = Column(String(3), nullable=True)  # Fatura serisi (ABC)

    # Taraflar
    sender_vkn = Column(String(11), nullable=False, index=True)  # Gönderen VKN/TCKN
    receiver_vkn = Column(String(11), nullable=False, index=True)  # Alıcı VKN/TCKN
    sender_alias = Column(String(100), nullable=True)  # Gönderen Posta Kutusu
    receiver_alias = Column(String(100), nullable=True)  # Alıcı Posta Kutusu

    # İçerik
    xml_content = Column(Text, nullable=True)  # UBL-TR XML
    pdf_content = Column(
        LargeBinary, nullable=True
    )  # İmzalı PDF (e-Arşiv) veya GIB PDF

    # Entegrasyon Bilgileri
    envelope_id = Column(String(36), nullable=True)  # Zarf ID
    integrator_id = Column(String(100), nullable=True)  # Entegratördeki ID

    # Zamanlama
    sent_at = Column(DateTime, nullable=True)  # Gönderilme zamanı
    response_at = Column(DateTime, nullable=True)  # Cevap alınma zamanı

    # Hata ve Durum Detayları
    error_message = Column(Text, nullable=True)
    status_history = Column(JSON, nullable=True)  # Durum geçmişi logu
    gib_response = Column(JSON, nullable=True)  # GIB'den dönen cevap

    # İlişkiler
    invoice = relationship("Invoice", foreign_keys=[invoice_id])
    purchase_invoice = relationship(
        "PurchaseInvoice", foreign_keys=[purchase_invoice_id]
    )
    delivery_note = relationship("DeliveryNote", foreign_keys=[delivery_note_id])

    def __repr__(self):
        return f"<EInvoice {self.uuid} - {self.invoice_number or 'DRAFT'}>"


class EInvoiceSeries(BaseModel):
    """e-Fatura Serileri (örn: GIB2024...)"""

    __tablename__ = "einvoice_series"

    series_prefix = Column(String(3), nullable=False)  # ABC, GIB
    type = Column(SQLEnum(EInvoiceType), nullable=False)
    year = Column(Integer, nullable=False)
    last_number = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    __table_args__ = (
        Index("idx_einvoice_series_uni", "series_prefix", "year", "type", unique=True),
    )


class EInvoiceSettings(BaseModel):
    """Entegratör Ayarları"""

    __tablename__ = "einvoice_settings"

    integrator_name = Column(String(50), nullable=False)  # foriba, efinans, vb.
    api_url = Column(String(200), nullable=False)
    api_username = Column(String(100), nullable=False)
    api_password = Column(String(200), nullable=False)  # Şifreli saklanmalı

    sender_alias = Column(
        String(100), nullable=True
    )  # Varsayılan gönderici etiketi (pk...)

    is_active = Column(Boolean, default=True)
    is_test_mode = Column(Boolean, default=False)

    extra_config = Column(JSON, nullable=True)  # Entegratöre özel ek ayarlar
