"""
Akıllı İş - Taşıma Birimi (SSCC/Palet) Modelleri

Ürünleri palet veya konteyner gibi taşıma birimlerinde gruplayarak
tek bir SSCC barkodu ile takip etmeyi sağlar.
"""

import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    Numeric,
    Enum,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from database.base import BaseModel


class TransportUnitType(enum.Enum):
    """Taşıma birimi türleri"""

    PALET = "palet"
    KONTEYNER = "konteyner"
    KOLI = "koli"
    KASA = "kasa"
    SANDIK = "sandik"
    DIGER = "diger"


class TransportUnitStatus(enum.Enum):
    """Taşıma birimi durumları"""

    ACIK = "acik"  # İçine ürün eklenebilir
    KAPALI = "kapali"  # Kapatılmış, hareket edilebilir
    SEVK_EDILDI = "sevk"  # Sevk edildi
    TESLIM_ALINDI = "teslim"  # Teslim alındı
    IPTAL = "iptal"


class TransportUnit(BaseModel):
    """
    Taşıma Birimi (Palet/SSCC) tablosu

    Birden fazla ürünü tek bir SSCC barkodu altında gruplar.
    Örn: Bir palet içinde 50 koli farklı ürün olabilir.
    """

    __tablename__ = "transport_units"

    # === SSCC Bilgileri ===
    sscc = Column(String(20), unique=True, nullable=False, index=True)
    barcode = Column(String(50), nullable=True)  # Alternatif barkod

    # === Tür ve Durum ===
    unit_type = Column(
        Enum(TransportUnitType), default=TransportUnitType.PALET, nullable=False
    )
    status = Column(
        Enum(TransportUnitStatus), default=TransportUnitStatus.ACIK, nullable=False
    )

    # === Lokasyon ===
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    location_id = Column(Integer, ForeignKey("warehouse_locations.id"), nullable=True)

    # === Fiziksel Özellikler ===
    length_cm = Column(Numeric(10, 2), nullable=True)  # Uzunluk
    width_cm = Column(Numeric(10, 2), nullable=True)  # Genişlik
    height_cm = Column(Numeric(10, 2), nullable=True)  # Yükseklik
    gross_weight_kg = Column(Numeric(12, 3), nullable=True)  # Brüt ağırlık
    net_weight_kg = Column(Numeric(12, 3), nullable=True)  # Net ağırlık

    # === Tarihler ===
    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_date = Column(DateTime, nullable=True)  # Kapatılma tarihi
    shipped_date = Column(DateTime, nullable=True)  # Sevk tarihi

    # === Açıklama ===
    notes = Column(Text, nullable=True)

    # === İlişkiler ===
    warehouse = relationship("Warehouse")
    location = relationship("WarehouseLocation")
    items = relationship(
        "TransportUnitItem",
        back_populates="transport_unit",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_tu_status", "status"),
        Index("idx_tu_warehouse", "warehouse_id"),
        Index("idx_tu_created", "created_date"),
    )

    @property
    def total_items(self) -> int:
        """Toplam kalem sayısı"""
        return len(self.items) if self.items else 0

    @property
    def total_quantity(self) -> Decimal:
        """Toplam ürün miktarı"""
        if not self.items:
            return Decimal(0)
        return sum(item.quantity for item in self.items)

    def __repr__(self):
        return f"<TransportUnit(sscc={self.sscc}, type={self.unit_type.value})>"


class TransportUnitItem(BaseModel):
    """
    Taşıma Birimi İçerikleri tablosu

    Bir taşıma birimi içindeki her bir stok kalemini temsil eder.
    """

    __tablename__ = "transport_unit_items"

    # === Taşıma Birimi ===
    transport_unit_id = Column(
        Integer, ForeignKey("transport_units.id", ondelete="CASCADE"), nullable=False
    )

    # === Stok Kartı ===
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    # === Miktar ===
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    # === İkincil Birim (Dual-Unit) ===
    secondary_quantity = Column(Numeric(18, 4), nullable=True)
    secondary_unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    # === Lot/Seri ===
    lot_number = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    expiry_date = Column(DateTime, nullable=True)

    # === Eklenme Bilgisi ===
    added_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    added_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # === İlişkiler ===
    transport_unit = relationship("TransportUnit", back_populates="items")
    item = relationship("Item")
    unit = relationship("Unit", foreign_keys=[unit_id])
    secondary_unit = relationship("Unit", foreign_keys=[secondary_unit_id])

    __table_args__ = (
        Index("idx_tui_transport", "transport_unit_id"),
        Index("idx_tui_item", "item_id"),
        Index("idx_tui_lot", "lot_number"),
    )

    def __repr__(self):
        return f"<TransportUnitItem(tu={self.transport_unit_id}, item={self.item_id}, qty={self.quantity})>"
