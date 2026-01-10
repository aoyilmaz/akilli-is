"""
Akıllı İş - MRP (Malzeme İhtiyaç Planlaması) Modelleri
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List

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
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from database.base import Base


class MRPRunStatus(str, Enum):
    """MRP çalışma durumları"""

    PENDING = "pending"
    COMPLETED = "completed"
    APPLIED = "applied"
    CANCELLED = "cancelled"


class DemandSource(str, Enum):
    """Talep kaynakları"""

    WORK_ORDER = "work_order"
    SALES_ORDER = "sales_order"
    MANUAL = "manual"
    FORECAST = "forecast"


class SuggestionType(str, Enum):
    """Tedarik önerisi türleri"""

    PURCHASE = "purchase"
    MANUFACTURE = "manufacture"


class MRPRun(Base):
    """
    MRP Çalışması

    Her MRP çalışması bir planlama dönemi için hesaplama yapar.
    """

    __tablename__ = "mrp_runs"

    id = Column(Integer, primary_key=True)

    # Çalışma numarası
    run_no = Column(String(30), unique=True, nullable=False, index=True)

    # Çalışma tarihi
    run_date = Column(DateTime, default=datetime.now)

    # Planlama parametreleri
    planning_horizon_days = Column(Integer, default=30)
    consider_safety_stock = Column(Boolean, default=True)
    include_work_orders = Column(Boolean, default=True)
    include_sales_orders = Column(Boolean, default=True)

    # Filtre (belirli ürünler için)
    item_filter = Column(Text, nullable=True)  # JSON array of item_ids

    # Durum
    status = Column(SQLEnum(MRPRunStatus), nullable=False, default=MRPRunStatus.PENDING)

    # İstatistikler
    total_items = Column(Integer, default=0)
    items_with_shortage = Column(Integer, default=0)
    total_suggestions = Column(Integer, default=0)

    # Açıklama
    notes = Column(Text, nullable=True)

    # İşlem bilgileri
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)

    # İlişkiler
    lines = relationship(
        "MRPLine",
        back_populates="mrp_run",
        cascade="all, delete-orphan",
        order_by="MRPLine.item_id, MRPLine.requirement_date",
    )

    def __repr__(self):
        return f"<MRPRun {self.run_no}>"


class MRPLine(Base):
    """
    MRP Satırı

    Her satır bir ürün ve tarih için ihtiyaç/tedarik bilgisini tutar.
    """

    __tablename__ = "mrp_lines"

    id = Column(Integer, primary_key=True)

    # Bağlı MRP çalışması
    mrp_run_id = Column(
        Integer, ForeignKey("mrp_runs.id", ondelete="CASCADE"), nullable=False
    )
    mrp_run = relationship("MRPRun", back_populates="lines")

    # Ürün
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    item = relationship("Item")

    # İhtiyaç tarihi
    requirement_date = Column(Date, nullable=False)

    # === MRP Hesaplama Kolonları ===
    # Brüt ihtiyaç (talep toplamı)
    gross_requirement = Column(Numeric(18, 4), default=Decimal("0"))

    # Planlanan girişler (açık siparişler)
    scheduled_receipts = Column(Numeric(18, 4), default=Decimal("0"))

    # Tahmini eldeki stok
    projected_on_hand = Column(Numeric(18, 4), default=Decimal("0"))

    # Net ihtiyaç (karşılanmamış)
    net_requirement = Column(Numeric(18, 4), default=Decimal("0"))

    # Planlanan sipariş girişi
    planned_order_receipt = Column(Numeric(18, 4), default=Decimal("0"))

    # Planlanan sipariş verme (lead time kaydırmalı)
    planned_order_release = Column(Numeric(18, 4), default=Decimal("0"))

    # === Talep Kaynağı ===
    demand_source = Column(SQLEnum(DemandSource), nullable=True)
    demand_source_id = Column(Integer, nullable=True)
    demand_source_ref = Column(String(50), nullable=True)

    # === Tedarik Önerisi ===
    suggestion_type = Column(SQLEnum(SuggestionType), nullable=True)
    suggested_qty = Column(Numeric(18, 4), default=Decimal("0"))
    suggested_date = Column(Date, nullable=True)

    # === Uygulama Durumu ===
    is_applied = Column(Boolean, default=False)
    applied_at = Column(DateTime, nullable=True)
    applied_order_type = Column(String(50), nullable=True)
    applied_order_id = Column(Integer, nullable=True)

    __table_args__ = (
        Index("idx_mrpline_run", "mrp_run_id"),
        Index("idx_mrpline_item", "item_id"),
        Index("idx_mrpline_date", "requirement_date"),
        Index("idx_mrpline_suggestion", "suggestion_type", "is_applied"),
    )

    def __repr__(self):
        return f"<MRPLine item={self.item_id} date={self.requirement_date}>"
