"""
Akıllı İş - Stok Yönetimi Modelleri
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    Index,
)
from sqlalchemy.orm import relationship
import enum

from database.base import BaseModel


class ItemType(enum.Enum):
    """Stok kartı türleri"""

    HAMMADDE = "hammadde"
    MAMUL = "mamul"
    YARI_MAMUL = "yari_mamul"
    AMBALAJ = "ambalaj"
    SARF = "sarf"
    TICARI = "ticari"
    HIZMET = "hizmet"
    DIGER = "diger"


class StockMovementType(enum.Enum):
    """Stok hareket türleri"""

    GIRIS = "giris"
    CIKIS = "cikis"
    SATIN_ALMA = "satin_alma"
    SATIS = "satis"
    URETIM_GIRIS = "uretim_giris"
    URETIM_CIKIS = "uretim_cikis"
    TRANSFER = "transfer"
    SAYIM_FAZLA = "sayim_fazla"
    SAYIM_EKSIK = "sayim_eksik"
    FIRE = "fire"
    IADE_ALIS = "iade_alis"
    IADE_SATIS = "iade_satis"


class Unit(BaseModel):
    """Birim tanımları"""

    __tablename__ = "units"

    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    short_name = Column(String(20), nullable=True)

    # İlişkiler
    items = relationship("Item", back_populates="unit")
    conversions_from = relationship(
        "UnitConversion",
        foreign_keys="UnitConversion.from_unit_id",
        back_populates="from_unit",
    )
    conversions_to = relationship(
        "UnitConversion",
        foreign_keys="UnitConversion.to_unit_id",
        back_populates="to_unit",
    )

    def __repr__(self):
        return f"<Unit {self.code}>"


class UnitConversion(BaseModel):
    """Birim dönüşümleri tablosu"""

    __tablename__ = "unit_conversions"

    from_unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    to_unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    multiplier = Column(Numeric(18, 6), nullable=False)

    # Stok kartına özel dönüşüm (opsiyonel)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)

    # İlişkiler
    from_unit = relationship(
        "Unit", foreign_keys=[from_unit_id], back_populates="conversions_from"
    )
    to_unit = relationship(
        "Unit", foreign_keys=[to_unit_id], back_populates="conversions_to"
    )
    item = relationship("Item", back_populates="unit_conversions")

    __table_args__ = (
        Index(
            "idx_unit_conversion_unique",
            "from_unit_id",
            "to_unit_id",
            "item_id",
            unique=True,
        ),
    )

    def __repr__(self):
        return f"<UnitConversion(from={self.from_unit_id}, to={self.to_unit_id}, multiplier={self.multiplier})>"


class ItemCategory(BaseModel):
    """Stok kategorileri tablosu (hiyerarşik)"""

    __tablename__ = "item_categories"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Hiyerarşi
    parent_id = Column(Integer, ForeignKey("item_categories.id"), nullable=True)
    level = Column(Integer, default=0)
    path = Column(String(500), nullable=True)

    # Görsel
    icon = Column(String(50), nullable=True)
    color = Column(String(7), nullable=True)

    # İlişkiler
    parent = relationship(
        "ItemCategory", remote_side="ItemCategory.id", backref="children"
    )
    items = relationship("Item", back_populates="category")

    __table_args__ = (
        Index("idx_category_parent", "parent_id"),
        Index("idx_category_path", "path"),
    )

    def __repr__(self):
        return f"<ItemCategory(code={self.code}, name={self.name})>"


class Item(BaseModel):
    """Stok kartları tablosu (ana tablo)"""

    __tablename__ = "items"

    # === Temel Bilgiler ===
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(300), nullable=False)
    short_name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    item_type = Column(Enum(ItemType), default=ItemType.HAMMADDE, nullable=False)

    # === Kategori ve Birim ===
    category_id = Column(Integer, ForeignKey("item_categories.id"), nullable=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)

    # === Kodlar ===
    barcode = Column(String(100), nullable=True, index=True)
    manufacturer_code = Column(String(100), nullable=True)
    supplier_code = Column(String(100), nullable=True)
    gtip_code = Column(String(20), nullable=True)

    # === Fiyatlar ===
    purchase_price = Column(Numeric(18, 4), default=0)
    sale_price = Column(Numeric(18, 4), default=0)
    list_price = Column(Numeric(18, 4), default=0)
    min_sale_price = Column(Numeric(18, 4), default=0)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=True)

    # === Vergiler ===
    vat_rate = Column(Numeric(5, 2), default=20)
    withholding_rate = Column(Numeric(5, 2), default=0)

    # === Stok Limitleri ===
    min_stock = Column(Numeric(18, 4), default=0)
    max_stock = Column(Numeric(18, 4), default=0)
    reorder_point = Column(Numeric(18, 4), default=0)
    reorder_quantity = Column(Numeric(18, 4), default=0)
    lead_time_days = Column(Integer, default=0)
    safety_stock = Column(Numeric(18, 4), default=0)

    # === MRP Özellikleri ===
    min_order_qty = Column(Numeric(18, 4), default=1)  # Minimum sipariş miktarı
    order_multiple = Column(Numeric(18, 4), default=1)  # Sipariş katı
    procurement_type = Column(String(20), default="purchase")  # purchase/manufacture

    # === Takip Özellikleri ===
    track_lot = Column(Boolean, default=False)
    track_serial = Column(Boolean, default=False)
    track_expiry = Column(Boolean, default=False)
    shelf_life_days = Column(Integer, nullable=True)

    # === Fiziksel Özellikler ===
    weight = Column(Numeric(18, 4), nullable=True)
    net_weight = Column(Numeric(18, 4), nullable=True)
    gross_weight = Column(Numeric(18, 4), nullable=True)
    volume = Column(Numeric(18, 4), nullable=True)
    width = Column(Numeric(18, 4), nullable=True)
    height = Column(Numeric(18, 4), nullable=True)
    depth = Column(Numeric(18, 4), nullable=True)

    # === Marka/Model ===
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    origin_country = Column(String(100), nullable=True)

    # === Durum ===
    is_purchasable = Column(Boolean, default=True)
    is_saleable = Column(Boolean, default=True)
    is_producible = Column(Boolean, default=False)
    is_raw_material = Column(Boolean, default=False)

    # === Notlar ===
    purchase_notes = Column(Text, nullable=True)
    sale_notes = Column(Text, nullable=True)
    production_notes = Column(Text, nullable=True)

    # === İlişkiler ===
    category = relationship("ItemCategory", back_populates="items")
    unit = relationship("Unit", back_populates="items")
    currency = relationship("Currency", back_populates="items")
    stock_balances = relationship(
        "StockBalance", back_populates="item", cascade="all, delete-orphan"
    )
    movements = relationship("StockMovement", back_populates="item")
    barcodes = relationship(
        "ItemBarcode", back_populates="item", cascade="all, delete-orphan"
    )
    unit_conversions = relationship("UnitConversion", back_populates="item")

    __table_args__ = (
        Index("idx_item_name", "name"),
        Index("idx_item_type", "item_type"),
        Index("idx_item_category", "category_id"),
        Index("idx_item_barcode", "barcode"),
        Index("idx_item_active_type", "is_active", "item_type"),
    )

    @property
    def total_stock(self) -> Decimal:
        """Toplam stok miktarı"""
        return sum((b.quantity or Decimal(0)) for b in self.stock_balances)

    @property
    def available_stock(self) -> Decimal:
        """Kullanılabilir stok (rezerve hariç)"""
        return sum((b.available_quantity or Decimal(0)) for b in self.stock_balances)

    @property
    def stock_status(self) -> str:
        """Stok durumu"""
        total = self.total_stock
        if total <= 0:
            return "out_of_stock"
        elif self.min_stock and total <= self.min_stock:
            return "critical"
        elif self.reorder_point and total <= self.reorder_point:
            return "low"
        return "normal"

    def __repr__(self):
        return f"<Item(code={self.code}, name={self.name})>"


class ItemBarcode(BaseModel):
    """Stok kartı barkodları tablosu (çoklu barkod desteği)"""

    __tablename__ = "item_barcodes"

    item_id = Column(
        Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    barcode = Column(String(100), nullable=False, index=True)
    barcode_type = Column(String(20), default="EAN13")
    is_primary = Column(Boolean, default=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    quantity = Column(Numeric(18, 4), default=1)

    # İlişkiler
    item = relationship("Item", back_populates="barcodes")
    unit = relationship("Unit")

    __table_args__ = (
        Index("idx_barcode_item", "item_id"),
        Index("idx_barcode_unique", "barcode", unique=True),
    )

    def __repr__(self):
        return f"<ItemBarcode(barcode={self.barcode}, item_id={self.item_id})>"


class Warehouse(BaseModel):
    """Depolar tablosu"""

    __tablename__ = "warehouses"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    short_name = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

    # Adres
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    postal_code = Column(String(10), nullable=True)
    country = Column(String(100), default="Türkiye")

    # İletişim
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    manager_name = Column(String(200), nullable=True)

    # Özellikler
    warehouse_type = Column(String(50), default="general")
    is_default = Column(Boolean, default=False)
    is_production = Column(Boolean, default=False)
    allow_negative = Column(Boolean, default=False)

    # İlişkiler
    stock_balances = relationship("StockBalance", back_populates="warehouse")
    locations = relationship(
        "WarehouseLocation", back_populates="warehouse", cascade="all, delete-orphan"
    )
    movements_from = relationship(
        "StockMovement",
        foreign_keys="StockMovement.from_warehouse_id",
        back_populates="from_warehouse",
    )
    movements_to = relationship(
        "StockMovement",
        foreign_keys="StockMovement.to_warehouse_id",
        back_populates="to_warehouse",
    )

    def __repr__(self):
        return f"<Warehouse(code={self.code}, name={self.name})>"


class WarehouseLocation(BaseModel):
    """Depo lokasyonları tablosu (raf, koridor)"""

    __tablename__ = "warehouse_locations"

    warehouse_id = Column(
        Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False
    )
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)

    # Lokasyon detayları
    aisle = Column(String(20), nullable=True)
    rack = Column(String(20), nullable=True)
    shelf = Column(String(20), nullable=True)
    bin = Column(String(20), nullable=True)

    # Kapasite
    max_weight = Column(Numeric(18, 4), nullable=True)
    max_volume = Column(Numeric(18, 4), nullable=True)
    max_items = Column(Integer, nullable=True)

    # İlişkiler
    warehouse = relationship("Warehouse", back_populates="locations")

    __table_args__ = (
        Index("idx_location_warehouse", "warehouse_id"),
        Index("idx_location_unique", "warehouse_id", "code", unique=True),
    )

    @property
    def full_code(self) -> str:
        """Tam lokasyon kodu"""
        parts = [self.warehouse.code, self.code]
        return "-".join(parts)

    def __repr__(self):
        return f"<WarehouseLocation(warehouse={self.warehouse_id}, code={self.code})>"


class StockBalance(BaseModel):
    """Stok bakiyeleri tablosu (depo bazlı)"""

    __tablename__ = "stock_balances"

    item_id = Column(
        Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    warehouse_id = Column(
        Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False
    )
    location_id = Column(Integer, ForeignKey("warehouse_locations.id"), nullable=True)

    # Miktarlar
    quantity = Column(Numeric(18, 4), default=0, nullable=False)
    reserved_quantity = Column(Numeric(18, 4), default=0)
    ordered_quantity = Column(Numeric(18, 4), default=0)

    # Lot/Seri bilgileri
    lot_number = Column(String(100), nullable=True, index=True)
    serial_number = Column(String(100), nullable=True, index=True)
    expiry_date = Column(DateTime, nullable=True)
    production_date = Column(DateTime, nullable=True)

    # Maliyet
    unit_cost = Column(Numeric(18, 4), default=0)
    total_cost = Column(Numeric(18, 4), default=0)

    # İlişkiler
    item = relationship("Item", back_populates="stock_balances")
    warehouse = relationship("Warehouse", back_populates="stock_balances")
    location = relationship("WarehouseLocation")

    __table_args__ = (
        Index("idx_balance_item_warehouse", "item_id", "warehouse_id"),
        Index("idx_balance_lot", "lot_number"),
        Index("idx_balance_expiry", "expiry_date"),
    )

    @property
    def available_quantity(self) -> Decimal:
        """Kullanılabilir miktar"""
        return (self.quantity or Decimal(0)) - (self.reserved_quantity or Decimal(0))

    def __repr__(self):
        return f"<StockBalance(item_id={self.item_id}, warehouse_id={self.warehouse_id}, qty={self.quantity})>"


class StockMovement(BaseModel):
    """Stok hareketleri tablosu"""

    __tablename__ = "stock_movements"

    # === Hareket Bilgileri ===
    movement_type = Column(Enum(StockMovementType), nullable=False, index=True)
    movement_date = Column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # === Belge Bilgileri ===
    document_type = Column(String(50), nullable=True)
    document_no = Column(String(50), nullable=True, index=True)
    document_date = Column(DateTime, nullable=True)
    reference_no = Column(String(100), nullable=True)

    # === Stok Kartı ===
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    item_code = Column(String(50), nullable=True)
    item_name = Column(String(300), nullable=True)

    # === Depolar ===
    from_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    to_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    from_location_id = Column(
        Integer, ForeignKey("warehouse_locations.id"), nullable=True
    )
    to_location_id = Column(
        Integer, ForeignKey("warehouse_locations.id"), nullable=True
    )

    # === Miktar ve Fiyat ===
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    unit_price = Column(Numeric(18, 4), default=0)
    total_price = Column(Numeric(18, 4), default=0)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=True)
    exchange_rate = Column(Numeric(18, 6), default=1)

    # === Lot/Seri Bilgileri ===
    lot_number = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    production_date = Column(DateTime, nullable=True)

    # === Bakiye Bilgileri ===
    balance_before = Column(Numeric(18, 4), nullable=True)
    balance_after = Column(Numeric(18, 4), nullable=True)

    # === Açıklama ve Notlar ===
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # === Kim yaptı ===
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # === İlişkiler ===
    item = relationship("Item", back_populates="movements")
    from_warehouse = relationship(
        "Warehouse", foreign_keys=[from_warehouse_id], back_populates="movements_from"
    )
    to_warehouse = relationship(
        "Warehouse", foreign_keys=[to_warehouse_id], back_populates="movements_to"
    )
    from_location = relationship("WarehouseLocation", foreign_keys=[from_location_id])
    to_location = relationship("WarehouseLocation", foreign_keys=[to_location_id])
    unit = relationship("Unit")
    currency = relationship("Currency")

    __table_args__ = (
        Index("idx_movement_item", "item_id"),
        Index("idx_movement_date", "movement_date"),
        Index("idx_movement_type_date", "movement_type", "movement_date"),
        Index("idx_movement_document", "document_type", "document_no"),
        Index("idx_movement_warehouses", "from_warehouse_id", "to_warehouse_id"),
        Index("idx_movement_lot", "lot_number"),
    )

    def __repr__(self):
        return f"<StockMovement(type={self.movement_type.value}, item={self.item_code}, qty={self.quantity})>"
