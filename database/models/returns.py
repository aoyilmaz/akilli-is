from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    Text,
    Boolean,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from database.base import Base


class ReturnType(str, Enum):
    SALES = "sales"
    PURCHASE = "purchase"


class ReturnReason(str, Enum):
    DEFECTIVE = "defective"
    WRONG_ITEM = "wrong_item"
    EXCESS = "excess"
    DAMAGED = "damaged"
    CUSTOMER_REQUEST = "customer_request"
    OTHER = "other"


class ReturnStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending"
    APPROVED = "approved"
    RECEIVED = "received"  # Iade alindi (Depoya girdi)
    INSPECTED = "inspected"  # Kontrol edildi
    COMPLETED = "completed"  # Muhasebelesti ve kapandi
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ReturnOrder(Base):
    __tablename__ = "return_orders"

    id = Column(Integer, primary_key=True)
    code = Column(
        String(20), unique=True, nullable=False, index=True
    )  # SIA2602-0001 / AIA2602-0001

    type = Column(SQLEnum(ReturnType), nullable=False)
    status = Column(SQLEnum(ReturnStatus), default=ReturnStatus.DRAFT, nullable=False)
    reason = Column(SQLEnum(ReturnReason), nullable=True)  # Genel iade nedeni

    # Iliskiler
    # Satis Iade icin
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer = relationship("Customer", backref="returns")

    # Satin Alma Iade icin
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    supplier = relationship("Supplier", backref="returns")

    # Baglanti
    original_invoice_id = Column(
        Integer, nullable=True
    )  # Fatura FK (generic olabilir veya ayri ayri)

    # Sipariş Bağlantıları
    related_sale_order_id = Column(
        Integer, ForeignKey("sales_orders.id"), nullable=True
    )
    related_sale_order = relationship("SalesOrder")

    related_purchase_order_id = Column(
        Integer, ForeignKey("purchase_orders.id"), nullable=True
    )
    related_purchase_order = relationship("PurchaseOrder")

    return_date = Column(Date, default=datetime.now, nullable=False)
    total_amount = Column(Numeric(14, 2), default=0)
    currency = Column(String(3), default="TRY")

    # Entegrasyon
    credit_note_id = Column(Integer, nullable=True)  # Muhasebe iade faturasi ID
    stock_movement_id = Column(
        Integer, ForeignKey("stock_movements.id"), nullable=True
    )  # Stok hareketi ID
    stock_movement = relationship("StockMovement")

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    lines = relationship(
        "ReturnOrderLine", back_populates="return_order", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ReturnOrder {self.code}>"


class ReturnOrderLine(Base):
    __tablename__ = "return_order_lines"

    id = Column(Integer, primary_key=True)
    return_order_id = Column(Integer, ForeignKey("return_orders.id"), nullable=False)
    return_order = relationship("ReturnOrder", back_populates="lines")

    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    item = relationship("Item")

    quantity = Column(Numeric(14, 3), nullable=False)
    unit_price = Column(Numeric(14, 4), nullable=False)
    line_total = Column(Numeric(14, 2), nullable=False)

    reason = Column(SQLEnum(ReturnReason), nullable=True)  # Satir bazli neden
    condition = Column(String(50), nullable=True)  # iyi, hasarli, kullanilmis

    # Iade alinacak/cikirilacak depo
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    warehouse = relationship("Warehouse")

    def __repr__(self):
        return f"<ReturnOrderLine {self.id} - {self.quantity}>"
