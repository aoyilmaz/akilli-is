"""
Akıllı İş - İzlenebilirlik (Traceability) Modelleri
"""

from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    Date,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from database.base import BaseModel
from datetime import date


class LotStatus(str, Enum):
    """Lot (Parti) durumları"""

    ACTIVE = "active"  # Aktif kullanımda
    QUARANTINE = "quarantine"  # Karantina altında
    BLOCKED = "blocked"  # Kullanımı engellenmiş
    EXPIRED = "expired"  # Miadı dolmuş
    CONSUMED = "consumed"  # Tamamen tüketilmiþ


class Lot(BaseModel):
    """Lot (Parti) yönetimi"""

    __tablename__ = "lots"

    lot_number = Column(String(50), unique=True, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    status = Column(SQLEnum(LotStatus), default=LotStatus.ACTIVE, nullable=False)

    quantity = Column(Numeric(14, 3), default=0)
    remaining_qty = Column(Numeric(14, 3), default=0)

    production_date = Column(Date, default=date.today)
    expiry_date = Column(Date)

    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=True)
    supplier_lot = Column(String(100))
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)

    warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    location_id = Column(Integer, ForeignKey("warehouse_locations.id"))

    notes = Column(Text)

    # İlişkiler
    product = relationship("Item")
    work_order = relationship("WorkOrder")
    purchase_order = relationship("PurchaseOrder")
    warehouse = relationship("Warehouse")
    location = relationship("WarehouseLocation")

    def __repr__(self):
        return f"<Lot {self.lot_number}>"


class SerialNumber(BaseModel):
    """Seri Numarası takibi"""

    __tablename__ = "serial_numbers"

    serial = Column(String(100), unique=True, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    lot_id = Column(Integer, ForeignKey("lots.id"))

    status = Column(String(50), default="in_stock")  # in_stock, sold, vb.

    work_order_id = Column(Integer, ForeignKey("work_orders.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))

    sale_date = Column(Date)
    warranty_start = Column(Date)
    warranty_end = Column(Date)

    # İlişkiler
    product = relationship("Item")
    lot = relationship("Lot")
    customer = relationship("Customer")

    def __repr__(self):
        return f"<SerialNumber {self.serial}>"


class TraceLink(BaseModel):
    """Lotlar arası hiyerarşik bağ (Genealogy)"""

    __tablename__ = "trace_links"

    parent_lot_id = Column(Integer, ForeignKey("lots.id"), nullable=False)
    child_lot_id = Column(Integer, ForeignKey("lots.id"), nullable=False)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=True)

    quantity_used = Column(Numeric(14, 3), nullable=False)

    # İlişkiler
    parent_lot = relationship("Lot", foreign_keys=[parent_lot_id])
    child_lot = relationship("Lot", foreign_keys=[child_lot_id])

    def __repr__(self):
        return f"<TraceLink {self.parent_lot_id} -> {self.child_lot_id}>"
