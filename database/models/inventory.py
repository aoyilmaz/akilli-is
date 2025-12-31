"""
Akıllı İş - Stok Modülü Veritabanı Modelleri
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, Boolean, 
    DateTime, ForeignKey, Enum, Index
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
    DIGER = "diger"


class StockMovementType(enum.Enum):
    """Stok hareket türleri"""
    GIRIS = "giris"
    CIKIS = "cikis"
    TRANSFER = "transfer"
    SAYIM = "sayim"
    FIRE = "fire"
    IADE = "iade"


class Unit(BaseModel):
    """Birim tanımları"""
    __tablename__ = "units"
    
    code = Column(String(20), unique=True, nullable=False)  # KG, ADET, MT
    name = Column(String(100), nullable=False)  # Kilogram, Adet, Metre
    
    # İlişkiler
    items = relationship("Item", back_populates="unit")
    
    def __repr__(self):
        return f"<Unit(code={self.code})>"


class ItemCategory(BaseModel):
    """Stok kategorileri (hiyerarşik)"""
    __tablename__ = "item_categories"
    
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("item_categories.id"), nullable=True)
    description = Column(Text, nullable=True)
    
    # İlişkiler
    parent = relationship("ItemCategory", remote_side="ItemCategory.id", backref="children")
    items = relationship("Item", back_populates="category")
    
    def __repr__(self):
        return f"<ItemCategory(code={self.code}, name={self.name})>"


class Warehouse(BaseModel):
    """Depo tanımları"""
    __tablename__ = "warehouses"
    
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    address = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    
    # İlişkiler
    stock_balances = relationship("StockBalance", back_populates="warehouse")
    movements_from = relationship("StockMovement", foreign_keys="StockMovement.from_warehouse_id", back_populates="from_warehouse")
    movements_to = relationship("StockMovement", foreign_keys="StockMovement.to_warehouse_id", back_populates="to_warehouse")
    
    def __repr__(self):
        return f"<Warehouse(code={self.code}, name={self.name})>"


class Item(BaseModel):
    """Stok kartları (ana tablo)"""
    __tablename__ = "items"
    
    # Temel bilgiler
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    item_type = Column(Enum(ItemType), default=ItemType.HAMMADDE, nullable=False)
    
    # Kategori ve birim
    category_id = Column(Integer, ForeignKey("item_categories.id"), nullable=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    
    # Barkod ve kodlar
    barcode = Column(String(100), nullable=True, index=True)
    manufacturer_code = Column(String(100), nullable=True)  # Üretici kodu
    
    # Fiyat bilgileri
    purchase_price = Column(Numeric(18, 4), default=0)  # Alış fiyatı
    sale_price = Column(Numeric(18, 4), default=0)  # Satış fiyatı
    currency = Column(String(3), default="TRY")
    vat_rate = Column(Numeric(5, 2), default=20)  # KDV oranı
    
    # Stok limitleri
    min_stock = Column(Numeric(18, 4), default=0)  # Minimum stok
    max_stock = Column(Numeric(18, 4), default=0)  # Maksimum stok
    reorder_point = Column(Numeric(18, 4), default=0)  # Yeniden sipariş noktası
    lead_time_days = Column(Integer, default=0)  # Temin süresi (gün)
    
    # Takip özellikleri
    track_lot = Column(Boolean, default=False)  # Lot takibi
    track_serial = Column(Boolean, default=False)  # Seri no takibi
    track_expiry = Column(Boolean, default=False)  # Son kullanma tarihi takibi
    
    # Fiziksel özellikler
    weight = Column(Numeric(18, 4), nullable=True)  # Ağırlık
    volume = Column(Numeric(18, 4), nullable=True)  # Hacim
    
    # Marka/Model
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    
    # İlişkiler
    category = relationship("ItemCategory", back_populates="items")
    unit = relationship("Unit", back_populates="items")
    stock_balances = relationship("StockBalance", back_populates="item")
    movements = relationship("StockMovement", back_populates="item")
    
    # Index'ler
    __table_args__ = (
        Index("idx_item_name", "name"),
        Index("idx_item_type", "item_type"),
    )
    
    @property
    def total_stock(self) -> Decimal:
        """Toplam stok miktarı"""
        return sum(b.quantity for b in self.stock_balances if b.quantity)
    
    def __repr__(self):
        return f"<Item(code={self.code}, name={self.name})>"


class StockBalance(BaseModel):
    """Stok bakiyeleri (depo bazlı)"""
    __tablename__ = "stock_balances"
    
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    quantity = Column(Numeric(18, 4), default=0, nullable=False)
    reserved_quantity = Column(Numeric(18, 4), default=0)  # Rezerve miktar
    
    # İlişkiler
    item = relationship("Item", back_populates="stock_balances")
    warehouse = relationship("Warehouse", back_populates="stock_balances")
    
    # Unique constraint
    __table_args__ = (
        Index("idx_stock_balance_unique", "item_id", "warehouse_id", unique=True),
    )
    
    @property
    def available_quantity(self) -> Decimal:
        """Kullanılabilir miktar"""
        return self.quantity - (self.reserved_quantity or 0)
    
    def __repr__(self):
        return f"<StockBalance(item_id={self.item_id}, warehouse_id={self.warehouse_id}, qty={self.quantity})>"


class StockMovement(BaseModel):
    """Stok hareketleri"""
    __tablename__ = "stock_movements"
    
    # Hareket bilgileri
    movement_type = Column(Enum(StockMovementType), nullable=False)
    movement_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    document_no = Column(String(50), nullable=True)  # Belge no
    
    # Stok kartı
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    
    # Depolar
    from_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    to_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    
    # Miktar ve fiyat
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_price = Column(Numeric(18, 4), default=0)
    total_price = Column(Numeric(18, 4), default=0)
    
    # Lot/Seri bilgileri
    lot_number = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # Açıklama
    description = Column(Text, nullable=True)
    
    # İlişkiler
    item = relationship("Item", back_populates="movements")
    from_warehouse = relationship("Warehouse", foreign_keys=[from_warehouse_id], back_populates="movements_from")
    to_warehouse = relationship("Warehouse", foreign_keys=[to_warehouse_id], back_populates="movements_to")
    
    # Index'ler
    __table_args__ = (
        Index("idx_movement_date", "movement_date"),
        Index("idx_movement_item", "item_id"),
        Index("idx_movement_document", "document_no"),
    )
    
    def __repr__(self):
        return f"<StockMovement(type={self.movement_type}, item_id={self.item_id}, qty={self.quantity})>"
