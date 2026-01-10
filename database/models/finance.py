"""
Akilli Is - Finans Modulu Veritabani Modelleri
"""

from enum import Enum
from decimal import Decimal
from datetime import date
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime,
    ForeignKey, Numeric, Enum as SQLEnum, Index, Table
)
from sqlalchemy.orm import relationship
from database.base import BaseModel


# === ENUM TANIMLARI ===

class TransactionType(str, Enum):
    """Cari hesap hareket turleri"""
    INVOICE = "invoice"          # Fatura
    PAYMENT = "payment"          # Odeme (tedarikci)
    RECEIPT = "receipt"          # Tahsilat (musteri)
    OPENING = "opening"          # Acilis bakiyesi
    ADJUSTMENT = "adjustment"    # Duzeltme


class PaymentMethod(str, Enum):
    """Odeme yontemleri"""
    CASH = "cash"                        # Nakit
    BANK_TRANSFER = "bank_transfer"      # Havale/EFT
    CHECK = "check"                      # Cek
    CREDIT_CARD = "credit_card"          # Kredi Karti
    PROMISSORY_NOTE = "promissory_note"  # Senet


class PaymentStatus(str, Enum):
    """Odeme/Tahsilat durumlari"""
    PENDING = "pending"          # Beklemede
    COMPLETED = "completed"      # Tamamlandi
    CANCELLED = "cancelled"      # Iptal


# === CARI HESAP HAREKETI ===

class AccountTransaction(BaseModel):
    """Cari hesap hareketleri tablosu"""

    __tablename__ = "account_transactions"

    # Hareket bilgileri
    transaction_no = Column(String(20), unique=True, nullable=False, index=True)
    transaction_date = Column(Date, nullable=False, default=date.today)
    transaction_type = Column(
        SQLEnum(TransactionType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )

    # Cari hesap (musteri veya tedarikci)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)

    # Belge referansi
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id"), nullable=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)

    # Tutarlar
    debit = Column(Numeric(15, 2), default=0)   # Borc
    credit = Column(Numeric(15, 2), default=0)  # Alacak

    # Odeme bilgileri
    payment_method = Column(
        SQLEnum(PaymentMethod, values_callable=lambda x: [e.value for e in x]),
        nullable=True
    )
    reference_no = Column(String(50))  # Cek no, dekont no vs.

    # Aciklama
    description = Column(String(500))
    notes = Column(Text)

    # Iliskiler
    customer = relationship("Customer", foreign_keys=[customer_id])
    supplier = relationship("Supplier", foreign_keys=[supplier_id])
    invoice = relationship("Invoice", foreign_keys=[invoice_id])

    __table_args__ = (
        Index("idx_transaction_customer", "customer_id", "transaction_date"),
        Index("idx_transaction_supplier", "supplier_id", "transaction_date"),
        Index("idx_transaction_date", "transaction_date"),
    )

    def __repr__(self):
        return f"<AccountTransaction {self.transaction_no}>"


# === TAHSILAT (Musterilerden) ===

class Receipt(BaseModel):
    """Tahsilat kayitlari tablosu"""

    __tablename__ = "receipts"

    # Tahsilat bilgileri
    receipt_no = Column(String(20), unique=True, nullable=False, index=True)
    receipt_date = Column(Date, nullable=False, default=date.today)

    # Musteri
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # Tutar
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), default="TRY")
    exchange_rate = Column(Numeric(10, 4), default=1)

    # Odeme yontemi
    payment_method = Column(
        SQLEnum(PaymentMethod, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )

    # Banka/Cek bilgileri
    bank_name = Column(String(100))
    bank_account = Column(String(50))
    check_no = Column(String(50))
    check_date = Column(Date)  # Cek vadesi

    # Durum
    status = Column(
        SQLEnum(PaymentStatus, values_callable=lambda x: [e.value for e in x]),
        default=PaymentStatus.COMPLETED
    )

    # Aciklama
    description = Column(String(500))
    notes = Column(Text)

    # Iliskiler
    customer = relationship("Customer", backref="receipts")
    allocations = relationship(
        "ReceiptAllocation",
        back_populates="receipt",
        cascade="all, delete-orphan"
    )
    transactions = relationship(
        "AccountTransaction",
        foreign_keys=[AccountTransaction.receipt_id],
        backref="receipt_ref"
    )

    __table_args__ = (
        Index("idx_receipt_customer", "customer_id", "receipt_date"),
        Index("idx_receipt_date", "receipt_date"),
    )

    def __repr__(self):
        return f"<Receipt {self.receipt_no}>"

    @property
    def allocated_amount(self) -> Decimal:
        """Faturalara dagilmis tutar"""
        return sum(a.amount for a in self.allocations) if self.allocations else Decimal(0)

    @property
    def unallocated_amount(self) -> Decimal:
        """Dagitilmamis tutar"""
        return (self.amount or Decimal(0)) - self.allocated_amount


class ReceiptAllocation(BaseModel):
    """Tahsilat-Fatura eslestirme tablosu"""

    __tablename__ = "receipt_allocations"

    receipt_id = Column(Integer, ForeignKey("receipts.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)

    # Iliskiler
    receipt = relationship("Receipt", back_populates="allocations")
    invoice = relationship("Invoice")

    __table_args__ = (
        Index("idx_receipt_allocation", "receipt_id", "invoice_id", unique=True),
    )


# === ODEME (Tedarikcilere) ===

class Payment(BaseModel):
    """Odeme kayitlari tablosu"""

    __tablename__ = "payments"

    # Odeme bilgileri
    payment_no = Column(String(20), unique=True, nullable=False, index=True)
    payment_date = Column(Date, nullable=False, default=date.today)

    # Tedarikci
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)

    # Tutar
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), default="TRY")
    exchange_rate = Column(Numeric(10, 4), default=1)

    # Odeme yontemi
    payment_method = Column(
        SQLEnum(PaymentMethod, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )

    # Banka/Cek bilgileri
    bank_name = Column(String(100))
    bank_account = Column(String(50))
    check_no = Column(String(50))
    check_date = Column(Date)  # Cek vadesi

    # Durum
    status = Column(
        SQLEnum(PaymentStatus, values_callable=lambda x: [e.value for e in x]),
        default=PaymentStatus.COMPLETED
    )

    # Aciklama
    description = Column(String(500))
    notes = Column(Text)

    # Iliskiler
    supplier = relationship("Supplier", backref="payments_made")
    allocations = relationship(
        "PaymentAllocation",
        back_populates="payment",
        cascade="all, delete-orphan"
    )
    transactions = relationship(
        "AccountTransaction",
        foreign_keys=[AccountTransaction.payment_id],
        backref="payment_ref"
    )

    __table_args__ = (
        Index("idx_payment_supplier", "supplier_id", "payment_date"),
        Index("idx_payment_date", "payment_date"),
    )

    def __repr__(self):
        return f"<Payment {self.payment_no}>"

    @property
    def allocated_amount(self) -> Decimal:
        """Faturalara dagilmis tutar"""
        return sum(a.amount for a in self.allocations) if self.allocations else Decimal(0)

    @property
    def unallocated_amount(self) -> Decimal:
        """Dagitilmamis tutar"""
        return (self.amount or Decimal(0)) - self.allocated_amount


class PaymentAllocation(BaseModel):
    """Odeme-Fatura eslestirme tablosu (Tedarikci faturalari icin)"""

    __tablename__ = "payment_allocations"

    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    # Not: Tedarikci faturasi icin ayri tablo gerekebilir
    # Simdilik genel bir reference_type ve reference_id kullaniyoruz
    reference_type = Column(String(50))  # "purchase_invoice" gibi
    reference_id = Column(Integer)
    amount = Column(Numeric(15, 2), nullable=False)

    # Iliskiler
    payment = relationship("Payment", back_populates="allocations")

    __table_args__ = (
        Index("idx_payment_allocation", "payment_id", "reference_type", "reference_id"),
    )
