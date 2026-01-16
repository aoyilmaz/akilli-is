"""
Akıllı İş - Üretim Modülü Modelleri
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
    Date,
)
from sqlalchemy.orm import relationship
import enum

from database.base import BaseModel


class BOMStatus(enum.Enum):
    """Reçete durumları"""

    DRAFT = "draft"
    ACTIVE = "active"
    REVISION = "revision"
    OBSOLETE = "obsolete"


class WorkOrderStatus(enum.Enum):
    """İş emri durumları"""

    DRAFT = "draft"
    PLANNED = "planned"
    RELEASED = "released"
    IN_PROGRESS = "in_progress"
    QUALITY_CHECK = "quality_check"  # Yeni: Kalite kontrol aşaması
    COMPLETED = "completed"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class WorkOrderPriority(enum.Enum):
    """İş emri öncelikleri"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class WorkStationType(enum.Enum):
    """İş istasyonu türleri"""

    MACHINE = "machine"
    WORKSTATION = "workstation"
    ASSEMBLY = "assembly"
    MANUAL = "manual"


class BillOfMaterials(BaseModel):
    """Ürün Reçeteleri (BOM) tablosu"""

    __tablename__ = "bill_of_materials"

    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    version = Column(Integer, default=1)
    revision = Column(String(20), default="A")
    status = Column(Enum(BOMStatus), default=BOMStatus.DRAFT)

    base_quantity = Column(Numeric(18, 4), default=1)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    lead_time_days = Column(Integer, default=0)
    setup_time_minutes = Column(Integer, default=0)
    production_time_minutes = Column(Integer, default=0)
    labor_cost = Column(Numeric(18, 4), default=0)
    overhead_cost = Column(Numeric(18, 4), default=0)

    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)

    notes = Column(Text, nullable=True)

    # İlişkiler
    item = relationship("Item", foreign_keys=[item_id])
    unit = relationship("Unit")
    lines = relationship(
        "BOMLine",
        back_populates="bom",
        foreign_keys="BOMLine.bom_id",
        cascade="all, delete-orphan",
    )
    operations = relationship(
        "BOMOperation", back_populates="bom", cascade="all, delete-orphan"
    )
    by_products = relationship(
        "BOMByProduct", back_populates="bom", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_bom_item", "item_id"),
        Index("idx_bom_status", "status"),
    )

    @property
    def total_material_cost(self) -> Decimal:
        return sum((line.line_cost or Decimal(0)) for line in self.lines)

    @property
    def total_cost(self) -> Decimal:
        return (
            self.total_material_cost
            + (self.labor_cost or Decimal(0))
            + (self.overhead_cost or Decimal(0))
        )


class BOMLine(BaseModel):
    """Reçete satırları"""

    __tablename__ = "bom_lines"

    bom_id = Column(
        Integer, ForeignKey("bill_of_materials.id", ondelete="CASCADE"), nullable=False
    )
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    quantity = Column(Numeric(18, 6), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    scrap_rate = Column(Numeric(5, 2), default=0)

    line_no = Column(Integer, default=0)
    is_optional = Column(Boolean, default=False)
    is_alternative = Column(Boolean, default=False)
    alternative_group = Column(String(50), nullable=True)

    # Alt reçete referansı (ayrı foreign key)
    sub_bom_id = Column(Integer, nullable=True)

    unit_cost = Column(Numeric(18, 4), default=0)
    line_cost = Column(Numeric(18, 4), default=0)

    notes = Column(Text, nullable=True)

    # İlişkiler - foreign_keys açıkça belirtildi
    bom = relationship("BillOfMaterials", back_populates="lines", foreign_keys=[bom_id])
    item = relationship("Item", foreign_keys=[item_id])
    unit = relationship("Unit")

    __table_args__ = (
        Index("idx_bomline_bom", "bom_id"),
        Index("idx_bomline_item", "item_id"),
    )

    @property
    def effective_quantity(self) -> Decimal:
        qty = self.quantity or Decimal(0)
        scrap = self.scrap_rate or Decimal(0)
        return qty * (1 + scrap / 100)


class WorkStation(BaseModel):
    """İş istasyonları tablosu"""

    __tablename__ = "work_stations"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    station_type = Column(Enum(WorkStationType), default=WorkStationType.MACHINE)

    capacity_per_hour = Column(Numeric(18, 4), nullable=True)
    efficiency_rate = Column(Numeric(5, 2), default=100)

    hourly_rate = Column(Numeric(18, 4), default=0)
    setup_cost = Column(Numeric(18, 4), default=0)

    working_hours_per_day = Column(Numeric(4, 2), default=8)

    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    location = Column(String(100), nullable=True)

    # Varsayılan operasyon değerleri (otomatik doldurma için)
    default_operation_name = Column(String(200), nullable=True)
    default_setup_time = Column(Integer, default=0)  # dakika
    default_run_time_per_unit = Column(Numeric(18, 4), default=0)  # dakika/birim

    warehouse = relationship("Warehouse")

    # Fason Üretim (Subcontracting)
    is_external = Column(Boolean, default=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    supplier = relationship("Supplier", foreign_keys=[supplier_id])


class BOMOperation(BaseModel):
    """Reçete operasyonları"""

    __tablename__ = "bom_operations"

    bom_id = Column(
        Integer, ForeignKey("bill_of_materials.id", ondelete="CASCADE"), nullable=False
    )

    operation_no = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    work_station_id = Column(Integer, ForeignKey("work_stations.id"), nullable=True)

    setup_time = Column(Integer, default=0)
    run_time = Column(Integer, default=0)
    wait_time = Column(Integer, default=0)
    move_time = Column(Integer, default=0)

    labor_cost = Column(Numeric(18, 4), default=0)
    machine_cost = Column(Numeric(18, 4), default=0)

    bom = relationship("BillOfMaterials", back_populates="operations")
    work_station = relationship("WorkStation")

    __table_args__ = (Index("idx_bomop_bom", "bom_id"),)

    @property
    def total_time(self) -> int:
        return (
            (self.setup_time or 0)
            + (self.run_time or 0)
            + (self.wait_time or 0)
            + (self.move_time or 0)
        )


class BOMByProduct(BaseModel):
    """Reçete Yan Ürünleri"""

    __tablename__ = "bom_by_products"

    bom_id = Column(
        Integer, ForeignKey("bill_of_materials.id", ondelete="CASCADE"), nullable=False
    )
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    quantity = Column(Numeric(18, 6), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    # Maliyet paylaşım oranı (örn: %10) veya birim sabit maliyet
    cost_share_rate = Column(Numeric(5, 2), default=0)

    notes = Column(Text, nullable=True)

    # İlişkiler
    bom = relationship("BillOfMaterials", back_populates="by_products")
    item = relationship("Item", foreign_keys=[item_id])
    unit = relationship("Unit")

    __table_args__ = (
        Index("idx_bombyprod_bom", "bom_id"),
        Index("idx_bombyprod_item", "item_id"),
    )


class WorkOrder(BaseModel):
    """İş emirleri tablosu"""

    __tablename__ = "work_orders"

    order_no = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    status = Column(Enum(WorkOrderStatus), default=WorkOrderStatus.DRAFT)
    priority = Column(Enum(WorkOrderPriority), default=WorkOrderPriority.NORMAL)

    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    bom_id = Column(Integer, ForeignKey("bill_of_materials.id"), nullable=False)

    planned_quantity = Column(Numeric(18, 4), nullable=False)
    completed_quantity = Column(Numeric(18, 4), default=0)
    scrapped_quantity = Column(Numeric(18, 4), default=0)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    planned_start = Column(DateTime, nullable=True)
    planned_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)

    source_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    target_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)

    planned_material_cost = Column(Numeric(18, 4), default=0)
    planned_labor_cost = Column(Numeric(18, 4), default=0)
    planned_overhead_cost = Column(Numeric(18, 4), default=0)
    actual_material_cost = Column(Numeric(18, 4), default=0)
    actual_labor_cost = Column(Numeric(18, 4), default=0)
    actual_overhead_cost = Column(Numeric(18, 4), default=0)

    sales_order_id = Column(Integer, nullable=True)
    parent_work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    released_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    released_at = Column(DateTime, nullable=True)

    # Kalite Kontrol Alanları
    qc_approved_quantity = Column(Numeric(18, 4), default=0)  # Kalite onaylı miktar
    qc_rejected_quantity = Column(Numeric(18, 4), default=0)  # Kalite red miktar
    qc_notes = Column(Text, nullable=True)  # Kalite kontrol notları
    qc_checked_by = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # Kalite kontrol yapan
    qc_checked_at = Column(DateTime, nullable=True)  # Kalite kontrol tarihi

    # Özel Açıklamalar
    production_notes = Column(Text, nullable=True)  # Üretim açıklamaları
    quality_notes = Column(
        Text, nullable=True
    )  # Kalite/QC açıklamaları (qc_notes ile paralel veya yedek)
    shipping_notes = Column(Text, nullable=True)  # Sevkiyat açıklamaları

    notes = Column(Text, nullable=True)

    # İlişkiler
    item = relationship("Item", foreign_keys=[item_id])
    bom = relationship("BillOfMaterials")
    unit = relationship("Unit")
    source_warehouse = relationship("Warehouse", foreign_keys=[source_warehouse_id])
    target_warehouse = relationship("Warehouse", foreign_keys=[target_warehouse_id])
    parent_work_order = relationship("WorkOrder", remote_side="WorkOrder.id")
    lines = relationship(
        "WorkOrderLine", back_populates="work_order", cascade="all, delete-orphan"
    )
    operations = relationship(
        "WorkOrderOperation", back_populates="work_order", cascade="all, delete-orphan"
    )
    by_products = relationship(
        "WorkOrderByProduct", back_populates="work_order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_wo_status", "status"),
        Index("idx_wo_item", "item_id"),
        Index("idx_wo_dates", "planned_start", "planned_end"),
    )

    @property
    def progress_rate(self) -> Decimal:
        if not self.operations:
            if not self.planned_quantity:
                return Decimal(0)
            return (self.completed_quantity or Decimal(0)) / self.planned_quantity * 100

        # Operasyon bazlı hesapla (Ağırlıklı - basitleştirilmiş)
        total_planned = sum(
            op.planned_quantity or 0 for op in self.operations
        )  # Genelde hepsi aynıdır ama sağlama alalım
        if total_planned == 0:
            # Eğer planned_quantity operasyonlarda yoksa operasyon sayısı üzerinden git
            completed_count = sum(
                1 for op in self.operations if op.status == "completed"
            )
            return Decimal(completed_count) / Decimal(len(self.operations)) * 100

        total_completed = sum(op.completed_quantity or 0 for op in self.operations)
        # Ortalama yüzde (basit versiyon)
        total_percent = sum(
            (op.completed_quantity or 0) / (op.planned_quantity or 1)
            for op in self.operations
        )
        return (total_percent / len(self.operations)) * 100

    @property
    def remaining_quantity(self) -> Decimal:
        return (self.planned_quantity or Decimal(0)) - (
            self.completed_quantity or Decimal(0)
        )


class WorkOrderLine(BaseModel):
    """İş emri malzeme satırları"""

    __tablename__ = "work_order_lines"

    work_order_id = Column(
        Integer, ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False
    )
    bom_line_id = Column(Integer, ForeignKey("bom_lines.id"), nullable=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    required_quantity = Column(Numeric(18, 4), nullable=False)
    issued_quantity = Column(Numeric(18, 4), default=0)
    returned_quantity = Column(Numeric(18, 4), default=0)
    scrapped_quantity = Column(Numeric(18, 4), default=0)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)

    is_reserved = Column(Boolean, default=False)
    reserved_quantity = Column(Numeric(18, 4), default=0)

    unit_cost = Column(Numeric(18, 4), default=0)
    line_cost = Column(Numeric(18, 4), default=0)

    work_order = relationship("WorkOrder", back_populates="lines")
    bom_line = relationship("BOMLine")
    item = relationship("Item")
    unit = relationship("Unit")
    warehouse = relationship("Warehouse")

    __table_args__ = (
        Index("idx_woline_wo", "work_order_id"),
        Index("idx_woline_item", "item_id"),
    )

    @property
    def pending_quantity(self) -> Decimal:
        return (self.required_quantity or Decimal(0)) - (
            self.issued_quantity or Decimal(0)
        )


class WorkOrderOperation(BaseModel):
    """İş emri operasyonları"""

    __tablename__ = "work_order_operations"

    work_order_id = Column(
        Integer, ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False
    )
    bom_operation_id = Column(Integer, ForeignKey("bom_operations.id"), nullable=True)

    operation_no = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)

    work_station_id = Column(Integer, ForeignKey("work_stations.id"), nullable=True)

    status = Column(String(20), default="pending")

    planned_setup_time = Column(Integer, default=0)
    planned_run_time = Column(Integer, default=0)

    actual_setup_time = Column(Integer, default=0)
    actual_run_time = Column(Integer, default=0)

    planned_start = Column(DateTime, nullable=True)
    planned_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    planned_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)

    # Duraklat/Devam Et için son başlangıç zamanı
    last_start_time = Column(DateTime, nullable=True)

    completed_quantity = Column(Numeric(18, 4), default=0)
    scrapped_quantity = Column(Numeric(18, 4), default=0)

    work_order = relationship("WorkOrder", back_populates="operations")
    bom_operation = relationship("BOMOperation")
    work_station = relationship("WorkStation")

    # Fason Üretim - Hizmet Alımı Siparişi
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    purchase_order = relationship("PurchaseOrder", foreign_keys=[purchase_order_id])

    __table_args__ = (Index("idx_woop_wo", "work_order_id"),)

    personnel = relationship(
        "WorkOrderOperationPersonnel",
        back_populates="operation",
        cascade="all, delete-orphan",
    )


class WorkOrderOperationPersonnel(BaseModel):
    """İş emri operasyon personelleri"""

    __tablename__ = "work_order_operation_personnel"

    operation_id = Column(
        Integer,
        ForeignKey("work_order_operations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    role = Column(String(50), default="operator")  # operator, supervisor

    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)

    duration_minutes = Column(Integer, default=0)

    operation = relationship("WorkOrderOperation", back_populates="personnel")
    user = relationship("User")

    __table_args__ = (
        Index("idx_woopp_op", "operation_id"),
        Index("idx_woopp_user", "user_id"),
    )


class WorkOrderByProduct(BaseModel):
    """İş Emri Yan Ürünleri"""

    __tablename__ = "work_order_by_products"

    work_order_id = Column(
        Integer, ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False
    )
    bom_by_product_id = Column(Integer, ForeignKey("bom_by_products.id"), nullable=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    planned_quantity = Column(Numeric(18, 4), nullable=False)
    completed_quantity = Column(Numeric(18, 4), default=0)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    actual_date = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)

    work_order = relationship("WorkOrder", back_populates="by_products")
    bom_by_product = relationship("BOMByProduct")
    item = relationship("Item", foreign_keys=[item_id])
    unit = relationship("Unit")

    __table_args__ = (
        Index("idx_wobyprod_wo", "work_order_id"),
        Index("idx_wobyprod_item", "item_id"),
    )
