"""
Akıllı İş - Sabit Kıymet (Demirbaş) Modelleri
"""

from enum import Enum
from datetime import date
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey,
    Enum as SQLEnum,
    Text,
)
from sqlalchemy.orm import relationship
from database.base import BaseModel


class AssetCategory(str, Enum):
    BUILDING = "building"  # Bina
    VEHICLE = "vehicle"  # Taşıt
    EQUIPMENT = "equipment"  # Teçhizat / Makine
    FURNITURE = "furniture"  # Demirbaş / Mobilya
    SOFTWARE = "software"  # Yazılım / Haklar
    LAND = "land"  # Arazi (Amortisman ayrılmaz)
    OTHER = "other"  # Diğer


class DepreciationMethod(str, Enum):
    STRAIGHT_LINE = "straight_line"  # Normal (Eşit Tutarlı) Amortisman
    DECLINING_BALANCE = "declining_balance"  # Azalan Bakiyeler (Hızlandırılmış)
    NO_DEPRECIATION = "no_depreciation"  # Amortisman Yok (Örn: Arazi)


class AssetStatus(str, Enum):
    ACTIVE = "active"  # Aktif Kullanımda
    SOLD = "sold"  # Satıldı
    SCRAPPED = "scrapped"  # Hurdaya Ayrıldı
    RETIRED = "retired"  # Kullanım Dışı (Emekli)


class FixedAsset(BaseModel):
    """Sabit Kıymet (Demirbaş) Kartı"""

    __tablename__ = "fixed_assets"

    # Temel Bilgiler
    name = Column(String(200), nullable=False)  # Demirbaş Adı
    description = Column(Text, nullable=True)  # Açıklama
    serial_number = Column(String(100), nullable=True)  # Seri No
    barcode = Column(String(50), nullable=True)  # Barkod / Etiket No

    # Sınıflandırma
    category = Column(
        SQLEnum(AssetCategory), nullable=False, default=AssetCategory.EQUIPMENT
    )
    status = Column(SQLEnum(AssetStatus), nullable=False, default=AssetStatus.ACTIVE)
    location = Column(String(100), nullable=True)  # Bulunduğu Yer (Ofis, Depo A...)

    # Satınalma Bilgileri
    purchase_date = Column(Date, nullable=False)  # Alım Tarihi
    purchase_price = Column(Float, nullable=False)  # Alış Bedeli
    currency = Column(String(3), default="TRY")  # Para Birimi
    supplier_id = Column(Integer, nullable=True)  # Tedarikçi ID (Opsiyonel)
    invoice_no = Column(String(50), nullable=True)  # Fatura No

    # Amortisman Ayarları
    depreciation_method = Column(
        SQLEnum(DepreciationMethod),
        nullable=False,
        default=DepreciationMethod.STRAIGHT_LINE,
    )
    useful_life_years = Column(Integer, nullable=False, default=5)  # Faydalı Ömür (Yıl)
    salvage_value = Column(Float, default=0.0)  # Hurda Değeri

    # Güncel Durum (Hesaplanan alanlar - Cache amaçlı)
    current_value = Column(Float, nullable=True)  # Net Defter Değeri

    # İlişkiler
    depreciation_entries = relationship(
        "DepreciationEntry", back_populates="fixed_asset", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<FixedAsset {self.name} ({self.status})>"


class DepreciationEntry(BaseModel):
    """Amortisman Kayıtları (Dönemsel)"""

    __tablename__ = "depreciation_entries"

    fixed_asset_id = Column(Integer, ForeignKey("fixed_assets.id"), nullable=False)

    period = Column(Date, nullable=False)  # Dönem (Genelde yıl sonu veya ay sonu)
    amount = Column(Float, nullable=False)  # Bu dönem ayrılan tutar
    accumulated_amount = Column(Float, nullable=False)  # Toplam birikmiş amortisman
    book_value = Column(Float, nullable=False)  # Kalan defter değeri

    description = Column(
        String(200), nullable=True
    )  # Açıklama (Örn: 2024 Yılı Amortismanı)

    fixed_asset = relationship("FixedAsset", back_populates="depreciation_entries")

    def __repr__(self):
        return f"<DepreciationEntry {self.period} - {self.amount}>"
