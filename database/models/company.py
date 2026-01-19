"""
Akıllı İş - Firma Modeli
ERP entegrasyonu için kapsamlı firma kartı yapısı
"""

from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    Enum,
    Index,
)
from sqlalchemy.orm import relationship

from database.models.common import BaseModel


# === ENUMLAR ===


class CompanyType(PyEnum):
    """Firma türleri"""

    ANONIM = "anonim"  # A.Ş.
    LIMITED = "limited"  # Ltd. Şti.
    SAHIS = "sahis"  # Şahıs
    KOOPERATIF = "kooperatif"  # Kooperatif
    KAMU = "kamu"  # Kamu kurumu
    DIGER = "diger"  # Diğer


class AddressType(PyEnum):
    """Adres türleri"""

    MERKEZ = "merkez"  # Ana merkez
    FATURA = "fatura"  # Fatura adresi
    SEVKIYAT = "sevkiyat"  # Sevkiyat adresi
    SUBE = "sube"  # Şube


class BankAccountType(PyEnum):
    """Banka hesap para birimi"""

    TRY = "TRY"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


class ProductionType(PyEnum):
    """Üretim türleri"""

    SIPARISE_URETIM = "siparise"  # Make to Order
    STOKA_URETIM = "stoka"  # Make to Stock
    KARMA = "karma"  # Hybrid


# === ANA FİRMA TABLOSU ===


class Company(BaseModel):
    """Ana firma tablosu"""

    __tablename__ = "companies"

    # Temel Kimlik
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    legal_name = Column(String(255), nullable=True)
    company_type = Column(Enum(CompanyType), default=CompanyType.LIMITED)
    parent_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    foundation_date = Column(Date, nullable=True)
    nace_code = Column(String(20), nullable=True)

    # Vergi & Resmi Bilgiler
    tax_country = Column(String(3), default="TR")
    tax_office = Column(String(100), nullable=True)
    tax_number = Column(String(20), nullable=True)
    mersis_no = Column(String(20), nullable=True)
    trade_reg_no = Column(String(50), nullable=True)
    sgk_workplace = Column(String(30), nullable=True)
    kep_address = Column(String(255), nullable=True)

    # E-Dönüşüm
    is_efatura = Column(Boolean, default=False)
    is_earsiv = Column(Boolean, default=False)
    is_eirsaliye = Column(Boolean, default=False)
    is_edefter = Column(Boolean, default=False)

    # İletişim
    phone = Column(String(20), nullable=True)
    phone2 = Column(String(20), nullable=True)
    fax = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)

    # Durum
    is_active = Column(Boolean, default=True)

    # İlişkiler
    parent = relationship("Company", remote_side="Company.id", backref="subsidiaries")
    addresses = relationship(
        "CompanyAddress", back_populates="company", cascade="all, delete-orphan"
    )
    banks = relationship(
        "CompanyBank", back_populates="company", cascade="all, delete-orphan"
    )
    contacts = relationship(
        "CompanyContact", back_populates="company", cascade="all, delete-orphan"
    )
    settings = relationship(
        "CompanySettings",
        back_populates="company",
        uselist=False,
        cascade="all, delete-orphan",
    )
    documents = relationship(
        "CompanyDocument", back_populates="company", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_company_code", "code"),
        Index("idx_company_tax", "tax_number"),
    )

    @property
    def full_address(self):
        """Varsayılan adresi döndür"""
        default = next((a for a in self.addresses if a.is_default), None)
        if default:
            return f"{default.address}, {default.district}/{default.city}"
        return None


# === ADRES TABLOSU ===


class CompanyAddress(BaseModel):
    """Firma adresleri (çoklu)"""

    __tablename__ = "company_addresses"

    company_id = Column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    address_type = Column(Enum(AddressType), default=AddressType.MERKEZ)
    country = Column(String(3), default="TR")
    city = Column(String(50), nullable=True)
    district = Column(String(50), nullable=True)
    postal_code = Column(String(10), nullable=True)
    address = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)

    # İlişki
    company = relationship("Company", back_populates="addresses")

    __table_args__ = (Index("idx_company_addr", "company_id"),)


# === BANKA HESAPLARI ===


class CompanyBank(BaseModel):
    """Firma banka hesapları (çoklu)"""

    __tablename__ = "company_banks"

    company_id = Column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    bank_name = Column(String(100), nullable=False)
    branch = Column(String(100), nullable=True)
    account_holder = Column(String(255), nullable=True)
    iban = Column(String(34), nullable=True)
    account_type = Column(Enum(BankAccountType), default=BankAccountType.TRY)
    swift_code = Column(String(11), nullable=True)
    is_default = Column(Boolean, default=False)

    # İlişki
    company = relationship("Company", back_populates="banks")

    __table_args__ = (Index("idx_company_bank", "company_id"),)


# === YETKİLİ KİŞİLER ===


class CompanyContact(BaseModel):
    """Firma yetkili kişileri"""

    __tablename__ = "company_contacts"

    company_id = Column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(100), nullable=False)
    title = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    mobile = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True)
    is_primary = Column(Boolean, default=False)

    # İlişki
    company = relationship("Company", back_populates="contacts")

    __table_args__ = (Index("idx_company_contact", "company_id"),)


# === FİRMA AYARLARI ===


class CompanySettings(BaseModel):
    """Firma ayarları (1-1 ilişki)"""

    __tablename__ = "company_settings"

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Bölgesel Ayarlar
    timezone = Column(String(50), default="Europe/Istanbul")
    language = Column(String(5), default="tr")
    date_format = Column(String(20), default="DD.MM.YYYY")
    decimal_separator = Column(String(1), default=",")
    thousand_separator = Column(String(1), default=".")

    # Finans Ayarları
    currency = Column(String(3), default="TRY")
    local_currency = Column(String(3), default="TRY")
    fiscal_year_start = Column(Integer, default=1)  # Ay
    fiscal_year_end = Column(Integer, default=12)  # Ay
    default_vat_rate = Column(Numeric(5, 2), default=20.00)
    default_withholding = Column(Numeric(5, 2), default=0.00)
    accounting_plan = Column(String(50), nullable=True)
    rounding_rule = Column(String(20), default="nearest")

    # Numaralandırma
    invoice_prefix = Column(String(10), default="FTR")
    order_prefix = Column(String(10), default="SIP")
    delivery_prefix = Column(String(10), default="IRS")
    purchase_prefix = Column(String(10), default="SAT")

    # Operasyonel Ayarlar
    default_warehouse_id = Column(Integer, nullable=True)
    has_lot_tracking = Column(Boolean, default=True)
    has_serial_tracking = Column(Boolean, default=False)
    barcode_standard = Column(String(20), default="EAN13")
    production_type = Column(
        Enum(ProductionType), default=ProductionType.SIPARISE_URETIM
    )
    work_calendar = Column(String(50), nullable=True)

    # Entegrasyon
    erp_uuid = Column(String(50), nullable=True)
    api_key = Column(String(255), nullable=True)
    efatura_integrator = Column(String(50), nullable=True)
    ecommerce_id = Column(String(100), nullable=True)

    # İletişim
    sms_sender_id = Column(String(20), nullable=True)
    whatsapp_business = Column(String(20), nullable=True)
    backup_email = Column(String(255), nullable=True)

    # Güvenlik
    user_limit = Column(Integer, default=0)  # 0 = sınırsız
    ip_restriction = Column(Text, nullable=True)
    data_isolation = Column(String(20), default="full")

    # İlişki
    company = relationship("Company", back_populates="settings")


# === DÖKÜMANLAR ===


class CompanyDocument(BaseModel):
    """Firma dökümanları (logo, şablon, vs)"""

    __tablename__ = "company_documents"

    company_id = Column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    doc_type = Column(String(50), nullable=False)
    # logo, letterhead, stamp, signature, invoice_template
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    # İlişki
    company = relationship("Company", back_populates="documents")

    __table_args__ = (Index("idx_company_doc", "company_id", "doc_type"),)
