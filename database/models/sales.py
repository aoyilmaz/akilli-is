"""
Akıllı İş - Satış Modülü Veritabanı Modelleri
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
    Index,
)
from sqlalchemy.orm import relationship
from database.base import BaseModel


# === ENUM TANIMLARI ===


class SalesQuoteStatus(str, Enum):
    """Satış teklifi durumları"""

    DRAFT = "draft"  # Taslak
    SENT = "sent"  # Müşteriye gönderildi
    ACCEPTED = "accepted"  # Kabul edildi
    REJECTED = "rejected"  # Reddedildi
    ORDERED = "ordered"  # Siparişe dönüştürüldü
    EXPIRED = "expired"  # Süresi doldu
    CANCELLED = "cancelled"  # İptal


class SalesOrderStatus(str, Enum):
    """Satış siparişi durumları"""

    DRAFT = "draft"  # Taslak
    CONFIRMED = "confirmed"  # Onaylandı
    PARTIAL = "partial"  # Kısmi sevk
    DELIVERED = "delivered"  # Tam sevk
    CLOSED = "closed"  # Kapatıldı
    CANCELLED = "cancelled"  # İptal


class DeliveryNoteStatus(str, Enum):
    """Teslimat irsaliyesi durumları"""

    DRAFT = "draft"  # Taslak
    SHIPPED = "shipped"  # Sevk edildi
    DELIVERED = "delivered"  # Teslim edildi
    CANCELLED = "cancelled"  # İptal


class InvoiceStatus(str, Enum):
    """Fatura durumları"""

    DRAFT = "draft"  # Taslak
    ISSUED = "issued"  # Kesildi
    PARTIAL = "partial"  # Kısmi ödendi
    PAID = "paid"  # Ödendi
    OVERDUE = "overdue"  # Vadesi geçti
    CANCELLED = "cancelled"  # İptal


class Currency(str, Enum):
    """Para birimleri"""

    TRY = "TRY"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


class PriceListType(str, Enum):
    """Fiyat listesi türleri"""

    SALES = "sales"  # Satış fiyat listesi
    PURCHASE = "purchase"  # Alış fiyat listesi


class PaymentType(str, Enum):
    """Sipariş ödeme türleri"""

    PESIN = "pesin"  # Peşin - sevk için ödeme gerekli
    VADELI = "vadeli"  # Vadeli - direkt sevk edilebilir
    KAPIDA = "kapida"  # Kapıda ödeme


class ShipmentReadiness(str, Enum):
    """Sevkiyat hazırlık durumları"""

    BEKLIYOR = "bekliyor"  # Hazırlık bekleniyor
    ODEME_BEKLIYOR = "odeme"  # Ödeme bekleniyor
    ONAY_BEKLIYOR = "onay"  # Müşteri onayı bekleniyor
    STOK_BEKLIYOR = "stok"  # Stok hazırlığı bekleniyor
    URETIM_BEKLIYOR = "uretim"  # Üretim bekleniyor
    HAZIR = "hazir"  # Sevke hazır


class AdvancePaymentMethod(str, Enum):
    """Avans ödeme yöntemleri"""

    NAKIT = "nakit"  # Nakit
    HAVALE = "havale"  # Havale/EFT
    KREDI_KARTI = "kredi_karti"  # Kredi Kartı
    CEK = "cek"  # Çek


# === FİYAT LİSTESİ ===


class PriceList(BaseModel):
    """Fiyat listeleri tablosu"""

    __tablename__ = "price_lists"

    # Temel bilgiler
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Tür
    list_type = Column(
        SQLEnum(PriceListType, values_callable=lambda x: [e.value for e in x]),
        default=PriceListType.SALES,
    )

    # Para birimi
    currency = Column(String(10), default="TRY")

    # Geçerlilik
    valid_from = Column(Date)
    valid_until = Column(Date)

    # Varsayılan fiyat listesi mi?
    is_default = Column(Boolean, default=False)

    # Öncelik (düşük değer = yüksek öncelik)
    priority = Column(Integer, default=10)

    # İlişkiler
    items = relationship(
        "PriceListItem", back_populates="price_list", cascade="all, delete-orphan"
    )
    customers = relationship("Customer", back_populates="price_list")

    def __repr__(self):
        return f"<PriceList {self.code}: {self.name}>"


class PriceListItem(BaseModel):
    """Fiyat listesi kalemleri"""

    __tablename__ = "price_list_items"

    # İlişkiler
    price_list_id = Column(Integer, ForeignKey("price_lists.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    # Fiyat
    unit_price = Column(Numeric(18, 4), nullable=False)

    # Minimum miktar (miktar bazlı fiyatlandırma için)
    min_quantity = Column(Numeric(18, 4), default=0)

    # İndirim oranı (opsiyonel)
    discount_rate = Column(Numeric(5, 2), default=0)

    # Notlar
    notes = Column(String(200))

    # İlişkiler
    price_list = relationship("PriceList", back_populates="items")
    item = relationship("Item")

    __table_args__ = (
        Index(
            "idx_price_list_item_unique",
            "price_list_id",
            "item_id",
            "min_quantity",
            unique=True,
        ),
    )

    def __repr__(self):
        return f"<PriceListItem list={self.price_list_id} item={self.item_id}>"


# === MÜŞTERİ ===


class Customer(BaseModel):
    """Müşteriler tablosu"""

    __tablename__ = "customers"

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
    currency = Column(String(10), default="TRY")
    price_list_id = Column(Integer, ForeignKey("price_lists.id"), nullable=True)

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
    price_list = relationship("PriceList", back_populates="customers")
    sales_quotes = relationship("SalesQuote", back_populates="customer")
    sales_orders = relationship("SalesOrder", back_populates="customer")
    delivery_notes = relationship("DeliveryNote", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.code}: {self.name}>"


# === SATIŞ TEKLİFİ ===


class SalesQuote(BaseModel):
    """Satış teklifleri tablosu"""

    __tablename__ = "sales_quotes"

    # Temel bilgiler
    quote_no = Column(String(20), unique=True, nullable=False, index=True)
    quote_date = Column(Date, nullable=False)

    # Müşteri
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # CRM Fırsat Bağlantısı
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)

    # Durum
    status = Column(
        SQLEnum(SalesQuoteStatus, values_callable=lambda x: [e.value for e in x]),
        default=SalesQuoteStatus.DRAFT,
    )

    # Geçerlilik
    valid_until = Column(Date)

    # Öncelik
    priority = Column(Integer, default=2)

    # Satış temsilcisi
    sales_rep = Column(String(100))

    # Fiyatlandırma
    currency = Column(String(10), default="TRY")
    exchange_rate = Column(Numeric(10, 4), default=1)

    subtotal = Column(Numeric(15, 2), default=0)
    discount_rate = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)

    # Red nedeni
    rejection_reason = Column(Text)

    # Notlar
    notes = Column(Text)

    # İlişkiler
    customer = relationship("Customer", back_populates="sales_quotes")
    items = relationship(
        "SalesQuoteItem", back_populates="quote", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_sq_customer", "customer_id"),
        Index("idx_sq_status", "status"),
        Index("idx_sq_date", "quote_date"),
    )

    @property
    def total_items(self) -> int:
        return len(self.items) if self.items else 0

    @property
    def status_display(self) -> str:
        status_names = {
            "draft": "Taslak",
            "sent": "Gönderildi",
            "accepted": "Kabul Edildi",
            "rejected": "Reddedildi",
            "ordered": "Siparişe Dönüştürüldü",
            "expired": "Süresi Doldu",
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
        return f"<SalesQuote {self.quote_no}>"


class SalesQuoteItem(BaseModel):
    """Satış teklifi kalemleri"""

    __tablename__ = "sales_quote_items"

    quote_id = Column(
        Integer, ForeignKey("sales_quotes.id", ondelete="CASCADE"), nullable=False
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
    quote = relationship("SalesQuote", back_populates="items")
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
        return f"<SalesQuoteItem {self.quote_id}-{self.item_id}>"


# === SATIŞ SİPARİŞİ ===


class SalesOrder(BaseModel):
    """Satış siparişleri tablosu"""

    __tablename__ = "sales_orders"

    # Temel bilgiler
    order_no = Column(String(20), unique=True, nullable=False, index=True)
    order_date = Column(Date, nullable=False)

    # Müşteri
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # İlgili teklif
    quote_id = Column(Integer, ForeignKey("sales_quotes.id"), nullable=True)

    # Durum
    status = Column(
        SQLEnum(SalesOrderStatus, values_callable=lambda x: [e.value for e in x]),
        default=SalesOrderStatus.DRAFT,
    )

    # Tarihler
    delivery_date = Column(Date)
    actual_delivery_date = Column(Date)

    # Fiyatlandırma
    currency = Column(String(10), default="TRY")
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
    source_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)

    # Notlar
    notes = Column(Text)
    internal_notes = Column(Text)

    # Sevkiyat hazırlık bilgileri
    payment_type = Column(
        SQLEnum(PaymentType, values_callable=lambda x: [e.value for e in x]),
        default=PaymentType.VADELI,
    )
    shipment_approved = Column(Boolean, default=False)
    shipment_approval_date = Column(DateTime, nullable=True)
    shipment_approval_by = Column(String(100), nullable=True)
    shipment_notes = Column(Text, nullable=True)  # Sevkiyat notları (adres teyidi vb.)
    requested_delivery_date = Column(Date, nullable=True)  # Müşterinin istediği tarih

    # İlişkiler
    customer = relationship("Customer", back_populates="sales_orders")
    quote = relationship("SalesQuote", foreign_keys=[quote_id])
    source_warehouse = relationship("Warehouse", foreign_keys=[source_warehouse_id])
    items = relationship(
        "SalesOrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    delivery_notes = relationship("DeliveryNote", back_populates="sales_order")
    invoices = relationship("Invoice", back_populates="sales_order")
    advance_payments = relationship(
        "OrderAdvancePayment", back_populates="order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_so_customer", "customer_id"),
        Index("idx_so_status", "status"),
        Index("idx_so_date", "order_date"),
    )

    @property
    def total_items(self) -> int:
        return len(self.items) if self.items else 0

    @property
    def delivered_rate(self) -> float:
        if not self.items:
            return 0
        total_qty = sum(float(i.quantity or 0) for i in self.items)
        delivered_qty = sum(float(i.delivered_quantity or 0) for i in self.items)
        return (delivered_qty / total_qty * 100) if total_qty > 0 else 0

    @property
    def status_display(self) -> str:
        status_names = {
            "draft": "Taslak",
            "confirmed": "Onaylandı",
            "partial": "Kısmi Sevk",
            "delivered": "Teslim Edildi",
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

    @property
    def total_advance_paid(self) -> Decimal:
        """Toplam alınan avans"""
        if not self.advance_payments:
            return Decimal("0")
        return sum(Decimal(str(p.amount or 0)) for p in self.advance_payments)

    @property
    def is_paid(self) -> bool:
        """Peşin siparişte ödeme yeterli mi?"""
        if self.payment_type != PaymentType.PESIN:
            return True
        return self.total_advance_paid >= (self.total or Decimal("0"))

    @property
    def remaining_payment(self) -> Decimal:
        """Kalan ödeme tutarı"""
        return max(Decimal("0"), (self.total or Decimal("0")) - self.total_advance_paid)

    @property
    def has_production(self) -> bool:
        """Bu sipariş için üretim iş emri var mı?"""
        # WorkOrder ilişkisi üzerinden kontrol edilecek
        # Şimdilik False döndürüyoruz, servis katmanında kontrol edilecek
        return False

    @property
    def is_production_complete(self) -> bool:
        """Üretim tamamlandı mı?"""
        # WorkOrder ilişkisi üzerinden kontrol edilecek
        # Şimdilik True döndürüyoruz, servis katmanında kontrol edilecek
        return True

    @property
    def is_stock_ready(self) -> bool:
        """Stok hazır mı?"""
        # Stok rezervasyon sistemi üzerinden kontrol edilecek
        # Şimdilik True döndürüyoruz, servis katmanında kontrol edilecek
        return True

    @property
    def shipment_readiness(self) -> "ShipmentReadiness":
        """Sevkiyat hazırlık durumu hesapla"""
        if self.status != SalesOrderStatus.CONFIRMED:
            return ShipmentReadiness.BEKLIYOR
        if self.payment_type == PaymentType.PESIN and not self.is_paid:
            return ShipmentReadiness.ODEME_BEKLIYOR
        if not self.shipment_approved:
            return ShipmentReadiness.ONAY_BEKLIYOR
        if not self.is_stock_ready:
            return ShipmentReadiness.STOK_BEKLIYOR
        if self.has_production and not self.is_production_complete:
            return ShipmentReadiness.URETIM_BEKLIYOR
        return ShipmentReadiness.HAZIR

    @property
    def is_ready_for_shipment(self) -> bool:
        """Sevkiyata hazır mı?"""
        return self.shipment_readiness == ShipmentReadiness.HAZIR

    @property
    def shipment_readiness_display(self) -> str:
        """Sevkiyat hazırlık durumu gösterimi"""
        readiness_names = {
            "bekliyor": "Hazırlık Bekleniyor",
            "odeme": "Ödeme Bekleniyor",
            "onay": "Onay Bekleniyor",
            "stok": "Stok Bekleniyor",
            "uretim": "Üretim Bekleniyor",
            "hazir": "Sevke Hazır",
        }
        return readiness_names.get(self.shipment_readiness.value, self.shipment_readiness.value)

    def __repr__(self):
        return f"<SalesOrder {self.order_no}>"


class SalesOrderItem(BaseModel):
    """Satış siparişi kalemleri"""

    __tablename__ = "sales_order_items"

    order_id = Column(
        Integer, ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False
    )
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)

    # Miktar
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    delivered_quantity = Column(Numeric(15, 4), default=0)
    invoiced_quantity = Column(Numeric(15, 4), default=0)

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
    order = relationship("SalesOrder", back_populates="items")
    item = relationship("Item", foreign_keys=[item_id])
    unit = relationship("Unit", foreign_keys=[unit_id])

    @property
    def remaining_quantity(self) -> Decimal:
        return Decimal(str(self.quantity or 0)) - Decimal(
            str(self.delivered_quantity or 0)
        )

    @property
    def is_fully_delivered(self) -> bool:
        return self.remaining_quantity <= 0

    def calculate_line_total(self):
        qty = Decimal(str(self.quantity or 0))
        price = Decimal(str(self.unit_price or 0))
        discount = Decimal(str(self.discount_rate or 0))

        subtotal = qty * price
        discount_amount = subtotal * discount / 100
        self.line_total = subtotal - discount_amount

    def __repr__(self):
        return f"<SalesOrderItem {self.order_id}-{self.item_id}>"


# === TESLİMAT İRSALİYESİ ===


class DeliveryNote(BaseModel):
    """Teslimat irsaliyeleri tablosu"""

    __tablename__ = "delivery_notes"

    # Temel bilgiler
    delivery_no = Column(String(20), unique=True, nullable=False, index=True)
    delivery_date = Column(Date, nullable=False)

    # İlişkili sipariş
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=True)

    # Müşteri
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # Durum
    status = Column(
        SQLEnum(DeliveryNoteStatus, values_callable=lambda x: [e.value for e in x]),
        default=DeliveryNoteStatus.DRAFT,
    )

    # Kaynak depo
    source_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)

    # Teslimat bilgileri
    shipping_address = Column(Text)
    shipping_method = Column(String(100))
    tracking_no = Column(String(100))

    # Teslimat tarihi
    actual_delivery_date = Column(Date)

    # Notlar
    notes = Column(Text)

    # İlişkiler
    sales_order = relationship("SalesOrder", back_populates="delivery_notes")
    customer = relationship("Customer", back_populates="delivery_notes")
    source_warehouse = relationship("Warehouse", foreign_keys=[source_warehouse_id])
    items = relationship(
        "DeliveryNoteItem", back_populates="delivery_note", cascade="all, delete-orphan"
    )
    invoices = relationship("Invoice", back_populates="delivery_note")

    __table_args__ = (
        Index("idx_dn_customer", "customer_id"),
        Index("idx_dn_order", "sales_order_id"),
        Index("idx_dn_status", "status"),
        Index("idx_dn_date", "delivery_date"),
    )

    @property
    def total_items(self) -> int:
        return len(self.items) if self.items else 0

    @property
    def status_display(self) -> str:
        status_names = {
            "draft": "Taslak",
            "shipped": "Sevk Edildi",
            "delivered": "Teslim Edildi",
            "cancelled": "İptal",
        }
        return status_names.get(self.status.value, self.status.value)

    def __repr__(self):
        return f"<DeliveryNote {self.delivery_no}>"


class DeliveryNoteItem(BaseModel):
    """Teslimat irsaliyesi kalemleri"""

    __tablename__ = "delivery_note_items"

    delivery_note_id = Column(
        Integer, ForeignKey("delivery_notes.id", ondelete="CASCADE"), nullable=False
    )
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)

    # Sipariş kalemi (varsa)
    so_item_id = Column(Integer, ForeignKey("sales_order_items.id"), nullable=True)

    # Miktar
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    # Lot/Seri takibi
    lot_number = Column(String(50))
    serial_numbers = Column(Text)

    # Notlar
    notes = Column(Text)

    # İlişkiler
    delivery_note = relationship("DeliveryNote", back_populates="items")
    item = relationship("Item", foreign_keys=[item_id])
    unit = relationship("Unit", foreign_keys=[unit_id])
    so_item = relationship("SalesOrderItem", foreign_keys=[so_item_id])

    def __repr__(self):
        return f"<DeliveryNoteItem {self.delivery_note_id}-{self.item_id}>"


# === FATURA ===


class Invoice(BaseModel):
    """Faturalar tablosu"""

    __tablename__ = "invoices"

    # Temel bilgiler
    invoice_no = Column(String(20), unique=True, nullable=False, index=True)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date)

    # Müşteri
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # İlişkili belgeler
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=True)
    delivery_note_id = Column(Integer, ForeignKey("delivery_notes.id"), nullable=True)

    # Durum
    status = Column(
        SQLEnum(InvoiceStatus, values_callable=lambda x: [e.value for e in x]),
        default=InvoiceStatus.DRAFT,
    )

    # Fiyatlandırma
    currency = Column(String(10), default="TRY")
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
    customer = relationship("Customer", back_populates="invoices")
    sales_order = relationship("SalesOrder", back_populates="invoices")
    delivery_note = relationship("DeliveryNote", back_populates="invoices")
    items = relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_inv_customer", "customer_id"),
        Index("idx_inv_status", "status"),
        Index("idx_inv_date", "invoice_date"),
        Index("idx_inv_due_date", "due_date"),
    )

    @property
    def total_items(self) -> int:
        return len(self.items) if self.items else 0

    @property
    def is_overdue(self) -> bool:
        from datetime import date

        if self.due_date and self.status not in [
            InvoiceStatus.PAID,
            InvoiceStatus.CANCELLED,
        ]:
            return date.today() > self.due_date
        return False

    @property
    def status_display(self) -> str:
        status_names = {
            "draft": "Taslak",
            "issued": "Kesildi",
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
        return f"<Invoice {self.invoice_no}>"


class InvoiceItem(BaseModel):
    """Fatura kalemleri"""

    __tablename__ = "invoice_items"

    invoice_id = Column(
        Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
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
    invoice = relationship("Invoice", back_populates="items")
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
        return f"<InvoiceItem {self.invoice_id}-{self.item_id}>"


# === SİPARİŞ AVANS ÖDEMELERİ ===


class OrderAdvancePayment(BaseModel):
    """Sipariş avans ödemeleri tablosu"""

    __tablename__ = "order_advance_payments"

    # Sipariş ilişkisi
    order_id = Column(
        Integer, ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False
    )

    # Ödeme bilgileri
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    payment_method = Column(
        SQLEnum(AdvancePaymentMethod, values_callable=lambda x: [e.value for e in x]),
        default=AdvancePaymentMethod.HAVALE,
    )
    reference_no = Column(String(50), nullable=True)  # Dekont/referans no

    # Notlar
    notes = Column(Text, nullable=True)

    # Kaydeden kullanıcı
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # İlişkiler
    order = relationship("SalesOrder", back_populates="advance_payments")
    created_by = relationship("User", foreign_keys=[created_by_id])

    __table_args__ = (
        Index("idx_oap_order", "order_id"),
        Index("idx_oap_date", "payment_date"),
    )

    @property
    def payment_method_display(self) -> str:
        """Ödeme yöntemi gösterimi"""
        method_names = {
            "nakit": "Nakit",
            "havale": "Havale/EFT",
            "kredi_karti": "Kredi Kartı",
            "cek": "Çek",
        }
        return method_names.get(self.payment_method.value, self.payment_method.value)

    def __repr__(self):
        return f"<OrderAdvancePayment {self.order_id} - {self.amount}>"
