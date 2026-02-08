from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Numeric,
    Enum as SQLEnum,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.orm import relationship
from database.models.common import BaseModel


class ContractType(str, Enum):
    SALES = "sales"
    PURCHASE = "purchase"


class ContractStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Contract(BaseModel):
    __tablename__ = "contracts"

    code = Column(String(20), unique=True, nullable=False, index=True)
    contract_type = Column(SQLEnum(ContractType), nullable=False)

    # Taraf
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)

    # Tarihler
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Durum
    status = Column(SQLEnum(ContractStatus), default=ContractStatus.DRAFT)

    # Finansal
    total_amount = Column(Numeric(15, 2), default=0)
    currency = Column(String(3), default="TRY")

    # Detaylar
    description = Column(Text)
    file_path = Column(String(255))  # Dosya eki yolu

    # İlişkiler
    customer = relationship("Customer", backref="contracts")
    supplier = relationship("Supplier", backref="contracts")
    lines = relationship(
        "ContractLine", back_populates="contract", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_contract_type", "contract_type"),
        Index("idx_contract_status", "status"),
        Index("idx_contract_dates", "start_date", "end_date"),
    )

    def __repr__(self):
        return f"<Contract {self.code}>"


class ContractLine(BaseModel):
    __tablename__ = "contract_lines"

    contract_id = Column(
        Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False
    )
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)

    # Tanım (Ürün değilse)
    description = Column(Text)

    unit_price = Column(Numeric(15, 4))
    quantity = Column(Numeric(15, 4))

    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    contract = relationship("Contract", back_populates="lines")
    item = relationship("Item")
    unit = relationship("Unit")

    def __repr__(self):
        return f"<ContractLine {self.contract_id}-{self.item_id}>"
