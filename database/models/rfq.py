"""
Akıllı İş - RFQ (Teklif Talebi) Modülü Veritabanı Modelleri
"""

from enum import Enum
from decimal import Decimal
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    ForeignKey,
    Numeric,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from database.base import BaseModel


class RFQStatus(str, Enum):
    """RFQ durumları"""

    DRAFT = "draft"  # Taslak
    PUBLISHED = "published"  # Yayınlandı / Tedarikçilere Duyuruldu
    COMPLETED = "completed"  # Tamamlandı (Kazanan belirlendi)
    CANCELLED = "cancelled"  # İptal


class OfferStatus(str, Enum):
    """Teklif durumları"""

    PENDING = "pending"  # Değerlendirme bekliyor
    WON = "won"  # Kazandı
    LOST = "lost"  # Kaybetti
    CANCELLED = "cancelled"  # İptal


class RFQ(BaseModel):
    """Teklif Talebi (RFQ) Başlık"""

    __tablename__ = "rfqs"

    # Temel bilgiler
    rfq_no = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # Tarihler
    date = Column(Date, nullable=False)
    deadline = Column(Date, nullable=False)  # Son teklif verme tarihi

    # Durum
    status = Column(
        SQLEnum(RFQStatus, values_callable=lambda x: [e.value for e in x]),
        default=RFQStatus.DRAFT,
    )

    # İlişkiler
    items = relationship(
        "RFQItem",
        back_populates="rfq",
        cascade="all, delete-orphan",
    )
    offers = relationship(
        "SupplierOffer",
        back_populates="rfq",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<RFQ {self.rfq_no}: {self.title}>"

    @property
    def status_display(self) -> str:
        status_names = {
            "draft": "Taslak",
            "published": "Yayınlandı",
            "completed": "Tamamlandı",
            "cancelled": "İptal",
        }
        return status_names.get(self.status.value, self.status.value)


class RFQItem(BaseModel):
    """RFQ Kalemleri (İstenen ürünler)"""

    __tablename__ = "rfq_items"

    rfq_id = Column(Integer, ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False)

    # Ürün/Hizmet
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)
    description = Column(String(200))  # Ürün seçilmezse serbest metin

    # Miktar
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    # İlişkili Satın Alma Talebi
    purchase_request_item_id = Column(
        Integer, ForeignKey("purchase_request_items.id"), nullable=True
    )

    # İlişkiler
    rfq = relationship("RFQ", back_populates="items")
    item = relationship("Item")
    unit = relationship("Unit")
    purchase_request_item = relationship("PurchaseRequestItem")


class SupplierOffer(BaseModel):
    """Tedarikçi Teklifi"""

    __tablename__ = "supplier_offers"

    rfq_id = Column(Integer, ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)

    # Teklif Detayları
    offer_date = Column(Date, nullable=False)
    valid_until = Column(Date)

    # Finansal
    currency = Column(String(10), default="TRY")
    exchange_rate = Column(Numeric(10, 4), default=1)

    total_amount = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    grand_total = Column(Numeric(15, 2), default=0)

    # Durum
    status = Column(
        SQLEnum(OfferStatus, values_callable=lambda x: [e.value for e in x]),
        default=OfferStatus.PENDING,
    )

    notes = Column(Text)

    # İlişkiler
    rfq = relationship("RFQ", back_populates="offers")
    supplier = relationship("Supplier")
    items = relationship(
        "SupplierOfferItem",
        back_populates="offer",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<SupplierOffer {self.id} Supplier:{self.supplier_id}>"

    @property
    def status_display(self) -> str:
        status_names = {
            "pending": "Bekliyor",
            "won": "Kazandı",
            "lost": "Kaybetti",
            "cancelled": "İptal",
        }
        return status_names.get(self.status.value, self.status.value)

    def calculate_totals(self):
        """Kalemlerden toplam tutarı hesapla"""
        self.total_amount = sum(item.line_total for item in self.items)
        # Basitlik için fatura altı iskonto yok
        # Vergi hesabı da kalemlerden
        self.grand_total = self.total_amount


class SupplierOfferItem(BaseModel):
    """Tedarikçi Teklif Kalemi"""

    __tablename__ = "supplier_offer_items"

    offer_id = Column(
        Integer, ForeignKey("supplier_offers.id", ondelete="CASCADE"), nullable=False
    )
    rfq_item_id = Column(
        Integer, ForeignKey("rfq_items.id"), nullable=False
    )  # Hangi kalem için?

    # Teklif edilen miktar (Kısmi teklif olabilir)
    quantity = Column(Numeric(15, 4), nullable=False)

    # Fiyat
    unit_price = Column(Numeric(15, 4), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=20)  # KDV %20

    # Teslimat
    delivery_date = Column(Date)  # Termin tarihi

    notes = Column(String(200))

    # İlişkiler
    offer = relationship("SupplierOffer", back_populates="items")
    rfq_item = relationship("RFQItem")

    @property
    def line_total(self):
        return Decimal(str(self.quantity or 0)) * Decimal(str(self.unit_price or 0))
