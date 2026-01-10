"""
Akıllı İş - Satın Alma Modülü Veritabanı Modelleri
"""

from enum import Enum
from decimal import Decimal
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
    Enum as SQLEnum,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from database.base import BaseModel


# === ENUM TANIMLARI ===


class PurchaseRequestStatus(str, Enum):
    """Satın alma talep durumları"""

    DRAFT = "draft"  # Taslak
    PENDING = "pending"  # Onay bekliyor
    APPROVED = "approved"  # Onaylandı
    REJECTED = "rejected"  # Reddedildi
    ORDERED = "ordered"  # Sipariş verildi
    CANCELLED = "cancelled"  # İptal


class PurchaseOrderStatus(str, Enum):
    """Satın alma sipariş durumları"""

    DRAFT = "draft"  # Taslak
    SENT = "sent"  # Tedarikçiye gönderildi
    CONFIRMED = "confirmed"  # Tedarikçi onayladı
    PARTIAL = "partial"  # Kısmi teslim
    RECEIVED = "received"  # Tam teslim alındı
    CLOSED = "closed"  # Kapatıldı
    CANCELLED = "cancelled"  # İptal


class GoodsReceiptStatus(str, Enum):
    """Mal kabul durumları"""

    DRAFT = "draft"  # Taslak
    COMPLETED = "completed"  # Tamamlandı
    CANCELLED = "cancelled"  # İptal


class Currency(str, Enum):
    """Para birimleri"""

    TRY = "TRY"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


# === TEDARİKÇİ ===


class Supplier(BaseModel):
    """Tedarikçiler tablosu"""

    __tablename__ = "suppliers"

    # Temel bilgiler
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    short_name = Column(String(50))
    tax_number = Column(String(20))
    tax_office = Column(String(100))

    # İletişim bilgileri
    contact_person = Column(String(100))
    phone = Column(String(30))
    mobile = Column(String(30))
    fax = Column(String(30))
    email = Column(String(100))
    website = Column(String(200))

    # Adres bilgileri
    address = Column(Text)
    city = Column(String(50))
    district = Column(String(50))
    postal_code = Column(String(10))
    country = Column(String(50), default="Türkiye")

    # Ticari bilgiler
    payment_term_days = Column(Integer, default=30)
    credit_limit = Column(Numeric(15, 2), default=0)
    currency = Column(SQLEnum(Currency), default=Currency.TRY)

    # Banka bilgileri
    bank_name = Column(String(100))
    bank_branch = Column(String(100))
    bank_account_no = Column(String(50))
    iban = Column(String(50))

    # Değerlendirme
    rating = Column(Integer, default=0)

    # Notlar
    notes = Column(Text)

    # İlişkiler
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    goods_receipts = relationship("GoodsReceipt", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier {self.code}: {self.name}>"


# === SATIN ALMA TALEBİ ===


class PurchaseRequest(BaseModel):
    """Satın alma talepleri tablosu"""

    __tablename__ = "purchase_requests"

    # Temel bilgiler
    request_no = Column(String(20), unique=True, nullable=False, index=True)
    request_date = Column(Date, nullable=False)

    # Talep eden
    requested_by = Column(String(100))
    department = Column(String(100))

    # Durum
    status = Column(SQLEnum(PurchaseRequestStatus), default=PurchaseRequestStatus.DRAFT)

    # Öncelik
    priority = Column(Integer, default=2)

    # İstenen teslim tarihi
    required_date = Column(Date)

    # Onay bilgileri
    approved_by = Column(String(100))
    approved_date = Column(DateTime)
    rejection_reason = Column(Text)

    # Notlar
    notes = Column(Text)

    # İlişkiler
    items = relationship(
        "PurchaseRequestItem", back_populates="request", cascade="all, delete-orphan"
    )

    @property
    def total_items(self) -> int:
        return len(self.items) if self.items else 0

    @property
    def status_display(self) -> str:
        status_names = {
            "draft": "Taslak",
            "pending": "Onay Bekliyor",
            "approved": "Onaylandı",
            "rejected": "Reddedildi",
            "ordered": "Sipariş Verildi",
            "cancelled": "İptal",
        }
        return status_names.get(self.status.value, self.status.value)

    def __repr__(self):
        return f"<PurchaseRequest {self.request_no}>"


class PurchaseRequestItem(BaseModel):
    """Satın alma talep kalemleri"""

    __tablename__ = "purchase_request_items"

    request_id = Column(
        Integer, ForeignKey("purchase_requests.id", ondelete="CASCADE"), nullable=False
    )
    item_id = Column(
        Integer, ForeignKey("items.id"), nullable=True
    )  # items tablosuna referans

    quantity = Column(Numeric(15, 4), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    # Açıklama/Spesifikasyon
    specification = Column(Text)

    # Önerilen tedarikçi
    suggested_supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)

    # Tahmini fiyat
    estimated_price = Column(Numeric(15, 4))

    # İlişkiler
    request = relationship("PurchaseRequest", back_populates="items")
    item = relationship("Item", foreign_keys=[item_id])
    unit = relationship("Unit", foreign_keys=[unit_id])
    suggested_supplier = relationship("Supplier", foreign_keys=[suggested_supplier_id])

    def __repr__(self):
        return f"<PurchaseRequestItem {self.request_id}-{self.item_id}>"


# === SATIN ALMA SİPARİŞİ ===


class PurchaseOrder(BaseModel):
    """Satın alma siparişleri tablosu"""

    __tablename__ = "purchase_orders"

    # Temel bilgiler
    order_no = Column(String(20), unique=True, nullable=False, index=True)
    order_date = Column(Date, nullable=False)

    # Tedarikçi
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)

    # Durum
    status = Column(SQLEnum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT)

    # Tarihler
    delivery_date = Column(Date)
    actual_delivery_date = Column(Date)

    # Fiyatlandırma
    currency = Column(SQLEnum(Currency), default=Currency.TRY)
    exchange_rate = Column(Numeric(10, 4), default=1)

    subtotal = Column(Numeric(15, 2), default=0)
    discount_rate = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)

    # Ödeme
    payment_term_days = Column(Integer)
    payment_due_date = Column(Date)

    # Teslimat
    delivery_address = Column(Text)
    delivery_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)

    # İlgili talep
    request_id = Column(Integer, ForeignKey("purchase_requests.id"), nullable=True)

    # Notlar
    notes = Column(Text)
    internal_notes = Column(Text)

    # İlişkiler
    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship(
        "PurchaseOrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    goods_receipts = relationship("GoodsReceipt", back_populates="purchase_order")
    request = relationship("PurchaseRequest", foreign_keys=[request_id])
    delivery_warehouse = relationship("Warehouse", foreign_keys=[delivery_warehouse_id])

    @property
    def total_items(self) -> int:
        return len(self.items) if self.items else 0

    @property
    def received_rate(self) -> float:
        if not self.items:
            return 0
        total_qty = sum(float(i.quantity or 0) for i in self.items)
        received_qty = sum(float(i.received_quantity or 0) for i in self.items)
        return (received_qty / total_qty * 100) if total_qty > 0 else 0

    @property
    def status_display(self) -> str:
        status_names = {
            "draft": "Taslak",
            "sent": "Gönderildi",
            "confirmed": "Onaylandı",
            "partial": "Kısmi Teslim",
            "received": "Teslim Alındı",
            "closed": "Kapatıldı",
            "cancelled": "İptal",
        }
        return status_names.get(self.status.value, self.status.value)

    def calculate_totals(self):
        self.subtotal = sum(
            Decimal(str(item.quantity or 0)) * Decimal(str(item.unit_price or 0))
            for item in self.items
        )
        self.discount_amount = (
            self.subtotal * Decimal(str(self.discount_rate or 0)) / 100
        )
        taxable = self.subtotal - self.discount_amount
        self.tax_amount = sum(
            Decimal(str(item.quantity or 0))
            * Decimal(str(item.unit_price or 0))
            * Decimal(str(item.tax_rate or 0))
            / 100
            for item in self.items
        )
        self.total = taxable + self.tax_amount

    def __repr__(self):
        return f"<PurchaseOrder {self.order_no}>"


class PurchaseOrderItem(BaseModel):
    """Satın alma sipariş kalemleri"""

    __tablename__ = "purchase_order_items"

    order_id = Column(
        Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)

    # Miktar
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    received_quantity = Column(Numeric(15, 4), default=0)

    # Fiyatlandırma
    unit_price = Column(Numeric(15, 4), nullable=False, default=0)
    discount_rate = Column(Numeric(5, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=18)

    # Hesaplanan değerler
    line_total = Column(Numeric(15, 2), default=0)

    # Açıklama
    description = Column(Text)

    # Teslimat
    delivery_date = Column(Date)

    # İlişkiler
    order = relationship("PurchaseOrder", back_populates="items")
    item = relationship("Item", foreign_keys=[item_id])
    unit = relationship("Unit", foreign_keys=[unit_id])

    @property
    def remaining_quantity(self) -> Decimal:
        return Decimal(str(self.quantity or 0)) - Decimal(
            str(self.received_quantity or 0)
        )

    @property
    def is_fully_received(self) -> bool:
        return self.remaining_quantity <= 0

    def calculate_line_total(self):
        qty = Decimal(str(self.quantity or 0))
        price = Decimal(str(self.unit_price or 0))
        discount = Decimal(str(self.discount_rate or 0))

        subtotal = qty * price
        discount_amount = subtotal * discount / 100
        self.line_total = subtotal - discount_amount

    def __repr__(self):
        return f"<PurchaseOrderItem {self.order_id}-{self.item_id}>"


# === MAL KABUL ===


class GoodsReceipt(BaseModel):
    """Mal kabul tablosu"""

    __tablename__ = "goods_receipts"

    # Temel bilgiler
    receipt_no = Column(String(20), unique=True, nullable=False, index=True)
    receipt_date = Column(Date, nullable=False)

    # İlişkili sipariş
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)

    # Tedarikçi
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)

    # Durum
    status = Column(SQLEnum(GoodsReceiptStatus), default=GoodsReceiptStatus.DRAFT)

    # Depo
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)

    # Belge bilgileri
    supplier_invoice_no = Column(String(50))
    supplier_delivery_no = Column(String(50))

    # Notlar
    notes = Column(Text)

    # İlişkiler
    purchase_order = relationship("PurchaseOrder", back_populates="goods_receipts")
    supplier = relationship("Supplier", back_populates="goods_receipts")
    warehouse = relationship("Warehouse", foreign_keys=[warehouse_id])
    items = relationship(
        "GoodsReceiptItem", back_populates="receipt", cascade="all, delete-orphan"
    )

    @property
    def total_items(self) -> int:
        return len(self.items) if self.items else 0

    @property
    def status_display(self) -> str:
        status_names = {
            "draft": "Taslak",
            "completed": "Tamamlandı",
            "cancelled": "İptal",
        }
        return status_names.get(self.status.value, self.status.value)

    def __repr__(self):
        return f"<GoodsReceipt {self.receipt_no}>"


class GoodsReceiptItem(BaseModel):
    """Mal kabul kalemleri"""

    __tablename__ = "goods_receipt_items"

    receipt_id = Column(
        Integer, ForeignKey("goods_receipts.id", ondelete="CASCADE"), nullable=False
    )
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)

    # Sipariş kalemi (varsa)
    po_item_id = Column(Integer, ForeignKey("purchase_order_items.id"), nullable=True)

    # Miktar
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    # Kalite kontrol
    accepted_quantity = Column(Numeric(15, 4))
    rejected_quantity = Column(Numeric(15, 4), default=0)
    rejection_reason = Column(Text)

    # Lot/Seri takibi
    lot_number = Column(String(50))
    serial_numbers = Column(Text)
    expiry_date = Column(Date)

    # Notlar
    notes = Column(Text)

    # İlişkiler
    receipt = relationship("GoodsReceipt", back_populates="items")
    item = relationship("Item", foreign_keys=[item_id])
    unit = relationship("Unit", foreign_keys=[unit_id])
    po_item = relationship("PurchaseOrderItem", foreign_keys=[po_item_id])

    def __repr__(self):
        return f"<GoodsReceiptItem {self.receipt_id}-{self.item_id}>"


# === SATINALMA FATURASI ===


class PurchaseInvoiceStatus(str, Enum):
    """Satınalma faturası durumları"""

    DRAFT = "draft"  # Taslak
    RECEIVED = "received"  # Alındı
    PARTIAL = "partial"  # Kısmi ödendi
    PAID = "paid"  # Ödendi
    OVERDUE = "overdue"  # Vadesi geçti
    CANCELLED = "cancelled"  # İptal


class PurchaseInvoice(BaseModel):
    """Satınalma faturaları tablosu"""

    __tablename__ = "purchase_invoices"

    # Temel bilgiler
    invoice_no = Column(String(50), unique=True, nullable=False, index=True)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date)

    # Tedarikçi fatura bilgileri
    supplier_invoice_no = Column(String(50))
    supplier_invoice_date = Column(Date)

    # Tedarikçi
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)

    # İlişkili belgeler
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    goods_receipt_id = Column(Integer, ForeignKey("goods_receipts.id"), nullable=True)

    # Durum
    status = Column(
        SQLEnum(PurchaseInvoiceStatus, values_callable=lambda x: [e.value for e in x]),
        default=PurchaseInvoiceStatus.DRAFT,
    )

    # Fiyatlandırma
    currency = Column(SQLEnum(Currency), default=Currency.TRY)
    exchange_rate = Column(Numeric(10, 4), default=1)

    subtotal = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)

    # Ödeme
    paid_amount = Column(Numeric(15, 2), default=0)
    balance = Column(Numeric(15, 2), default=0)
    paid_date = Column(Date)
    payment_method = Column(String(50))
    payment_notes = Column(Text)

    # Notlar
    notes = Column(Text)

    # İlişkiler
    supplier = relationship("Supplier", backref="purchase_invoices")
    purchase_order = relationship("PurchaseOrder", backref="purchase_invoices")
    goods_receipt = relationship("GoodsReceipt", backref="purchase_invoices")
    items = relationship(
        "PurchaseInvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )

    @property
    def total_items(self) -> int:
        return len(self.items) if self.items else 0

    @property
    def is_overdue(self) -> bool:
        from datetime import date

        if self.due_date and self.status not in [
            PurchaseInvoiceStatus.PAID,
            PurchaseInvoiceStatus.CANCELLED,
        ]:
            return date.today() > self.due_date
        return False

    @property
    def status_display(self) -> str:
        status_names = {
            "draft": "Taslak",
            "received": "Alındı",
            "partial": "Kısmi Ödendi",
            "paid": "Ödendi",
            "overdue": "Vadesi Geçti",
            "cancelled": "İptal",
        }
        return status_names.get(self.status.value, self.status.value)

    def calculate_totals(self):
        self.subtotal = sum(
            Decimal(str(item.quantity or 0)) * Decimal(str(item.unit_price or 0))
            for item in self.items
        )
        self.tax_amount = sum(
            Decimal(str(item.quantity or 0))
            * Decimal(str(item.unit_price or 0))
            * Decimal(str(item.tax_rate or 0))
            / 100
            for item in self.items
        )
        self.total = self.subtotal - self.discount_amount + self.tax_amount
        self.balance = self.total - Decimal(str(self.paid_amount or 0))

    def __repr__(self):
        return f"<PurchaseInvoice {self.invoice_no}>"


class PurchaseInvoiceItem(BaseModel):
    """Satınalma faturası kalemleri"""

    __tablename__ = "purchase_invoice_items"

    invoice_id = Column(
        Integer, ForeignKey("purchase_invoices.id", ondelete="CASCADE"), nullable=False
    )
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)

    # Miktar
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    # Fiyatlandırma
    unit_price = Column(Numeric(15, 4), nullable=False, default=0)
    discount_rate = Column(Numeric(5, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=18)

    # Hesaplanan değerler
    line_total = Column(Numeric(15, 2), default=0)

    # Açıklama
    description = Column(Text)

    # İlişkiler
    invoice = relationship("PurchaseInvoice", back_populates="items")
    item = relationship("Item", foreign_keys=[item_id])
    unit = relationship("Unit", foreign_keys=[unit_id])

    def calculate_line_total(self):
        qty = Decimal(str(self.quantity or 0))
        price = Decimal(str(self.unit_price or 0))
        discount = Decimal(str(self.discount_rate or 0))

        subtotal = qty * price
        discount_amount = subtotal * discount / 100
        self.line_total = subtotal - discount_amount

    def __repr__(self):
        return f"<PurchaseInvoiceItem {self.invoice_id}-{self.item_id}>"
