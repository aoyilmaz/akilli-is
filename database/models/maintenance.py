"""
Akıllı İş - Bakım ve Onarım Modülü Modelleri
Güncellenmiş versiyon: Ekipman hiyerarşisi, duruş takibi, kontrol listeleri, KPI desteği
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
from sqlalchemy.orm import relationship, backref
import enum

from database.base import BaseModel


# ============== ENUM Tanımları ==============

class MaintenancePriority(enum.Enum):
    """Bakım/Arıza öncelikleri"""
    LOW = "dusuk"
    NORMAL = "normal"
    HIGH = "yuksek"
    CRITICAL = "kritik"


class MaintenanceStatus(enum.Enum):
    """Bakım talep durumları"""
    OPEN = "acik"
    IN_PROGRESS = "devam_ediyor"
    WAITING_PARTS = "parca_bekleniyor"
    RESOLVED = "cozuldu"
    CANCELLED = "iptal"


class WorkOrderStatus(enum.Enum):
    """İş emri durumları"""
    DRAFT = "taslak"
    ASSIGNED = "atandi"
    IN_PROGRESS = "devam_ediyor"
    COMPLETED = "tamamlandi"
    CLOSED = "kapandi"
    CANCELLED = "iptal"


class MaintenanceType(enum.Enum):
    """Bakım türleri"""
    BREAKDOWN = "ariza"          # Arıza Onarım
    PREVENTIVE = "periyodik"     # Periyodik Bakım
    PREDICTIVE = "kestirimci"    # Kestirimci Bakım
    CALIBRATION = "kalibrasyon"  # Kalibrasyon


class CriticalityLevel(enum.Enum):
    """Ekipman kritiklik seviyeleri"""
    LOW = "dusuk"
    MEDIUM = "orta"
    HIGH = "yuksek"
    CRITICAL = "kritik"


class EquipmentStatus(enum.Enum):
    """Ekipman çalışma durumları"""
    RUNNING = "calisiyor"
    STOPPED = "durdu"
    MAINTENANCE = "bakimda"
    BREAKDOWN = "arizali"


class DowntimeReason(enum.Enum):
    """Duruş sebepleri"""
    BREAKDOWN = "breakdown"
    MAINTENANCE = "maintenance"
    SETUP = "setup"
    NO_MATERIAL = "no_material"
    NO_OPERATOR = "no_operator"
    QUALITY_ISSUE = "quality_issue"
    OTHER = "other"


# ============== MODEL Tanımları ==============

class MaintenanceCategory(BaseModel):
    """Bakım kategorileri (Mekanik, Elektrik, Pnömatik vb.)"""
    __tablename__ = "maintenance_categories"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#3B82F6")  # UI için renk kodu

    # İlişkiler
    requests = relationship("MaintenanceRequest", back_populates="category")

    def __repr__(self):
        return f"<MaintenanceCategory {self.code}>"


class Equipment(BaseModel):
    """Ekipman/Makine tanımları - Geliştirilmiş versiyon"""
    __tablename__ = "equipments"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Hiyerarşi (Ana Ekipman / Alt Ekipman)
    parent_id = Column(Integer, ForeignKey("equipments.id"), nullable=True)
    children = relationship(
        "Equipment",
        backref=backref("parent", remote_side="Equipment.id"),
        lazy="dynamic"
    )

    # Marka/Model
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True, index=True)
    manufacturing_year = Column(Integer, nullable=True)

    # Lokasyon
    location = Column(String(200), nullable=True)
    department = Column(String(100), nullable=True)

    # Durum ve Kritiklik
    is_active = Column(Boolean, default=True)
    criticality = Column(Enum(CriticalityLevel), default=CriticalityLevel.MEDIUM)
    current_status = Column(Enum(EquipmentStatus), default=EquipmentStatus.RUNNING)

    # Çalışma Saati / Sayaç Takibi
    running_hours = Column(Numeric(18, 2), default=0)
    last_meter_reading = Column(Numeric(18, 2), nullable=True)
    last_meter_date = Column(DateTime, nullable=True)

    # Satın Alma ve Garanti
    purchase_date = Column(Date, nullable=True)
    warranty_end_date = Column(Date, nullable=True)
    purchase_price = Column(Numeric(18, 2), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)

    # Teknik Özellikler
    specifications = Column(Text, nullable=True)

    # Üretim Modülü Bağlantısı (Opsiyonel)
    work_station_id = Column(Integer, ForeignKey("work_stations.id"), nullable=True)

    # İlişkiler
    supplier = relationship("Supplier")
    work_station = relationship("WorkStation")
    maintenance_requests = relationship("MaintenanceRequest", back_populates="equipment")
    work_orders = relationship("MaintenanceWorkOrder", back_populates="equipment")
    maintenance_plans = relationship("MaintenancePlan", back_populates="equipment")
    spare_parts = relationship("EquipmentSparePart", back_populates="equipment")
    downtimes = relationship("EquipmentDowntime", back_populates="equipment")
    checklists = relationship("MaintenanceChecklist", back_populates="equipment")

    __table_args__ = (
        Index("idx_equipment_status", "current_status"),
        Index("idx_equipment_criticality", "criticality"),
    )

    def __repr__(self):
        return f"<Equipment {self.code}>"


class EquipmentSparePart(BaseModel):
    """Ekipman başına önerilen yedek parçalar"""
    __tablename__ = "equipment_spare_parts"

    equipment_id = Column(Integer, ForeignKey("equipments.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    min_quantity = Column(Numeric(18, 4), default=1)
    recommended_quantity = Column(Numeric(18, 4), nullable=True)
    notes = Column(Text, nullable=True)

    # İlişkiler
    equipment = relationship("Equipment", back_populates="spare_parts")
    item = relationship("Item")

    def __repr__(self):
        return f"<EquipmentSparePart {self.equipment_id}-{self.item_id}>"


class EquipmentDowntime(BaseModel):
    """Ekipman duruş kayıtları"""
    __tablename__ = "equipment_downtimes"

    equipment_id = Column(Integer, ForeignKey("equipments.id", ondelete="CASCADE"), nullable=False)

    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)

    reason = Column(String(50), nullable=True)  # DowntimeReason enum değeri
    notes = Column(Text, nullable=True)

    # Bağlı iş emri (varsa)
    work_order_id = Column(Integer, ForeignKey("maintenance_work_orders.id"), nullable=True)

    # Kayıt bilgileri
    recorded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # İlişkiler
    equipment = relationship("Equipment", back_populates="downtimes")
    work_order = relationship("MaintenanceWorkOrder", back_populates="downtimes")
    recorded_by = relationship("User", foreign_keys=[recorded_by_id])

    __table_args__ = (
        Index("idx_downtime_equipment", "equipment_id"),
        Index("idx_downtime_dates", "start_time", "end_time"),
    )

    @property
    def duration_minutes(self) -> float:
        """Duruş süresini dakika olarak hesapla"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return (datetime.utcnow() - self.start_time).total_seconds() / 60

    @property
    def duration_hours(self) -> float:
        """Duruş süresini saat olarak hesapla"""
        return self.duration_minutes / 60

    def __repr__(self):
        return f"<EquipmentDowntime {self.equipment_id} {self.start_time}>"


class MaintenanceRequest(BaseModel):
    """Arıza/Bakım Talepleri"""
    __tablename__ = "maintenance_requests"

    request_no = Column(String(50), unique=True, nullable=False, index=True)

    equipment_id = Column(Integer, ForeignKey("equipments.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("maintenance_categories.id"), nullable=True)

    request_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    description = Column(Text, nullable=False)

    priority = Column(Enum(MaintenancePriority), default=MaintenancePriority.NORMAL)
    maintenance_type = Column(Enum(MaintenanceType), default=MaintenanceType.BREAKDOWN)
    status = Column(Enum(MaintenanceStatus), default=MaintenanceStatus.OPEN)

    # Bildiren Kişi
    reported_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Çözüm Bilgileri
    resolution_notes = Column(Text, nullable=True)
    completed_date = Column(DateTime, nullable=True)

    # İlişkiler
    equipment = relationship("Equipment", back_populates="maintenance_requests")
    category = relationship("MaintenanceCategory", back_populates="requests")
    reported_by = relationship("User", foreign_keys=[reported_by_id])
    work_orders = relationship("MaintenanceWorkOrder", back_populates="request")
    attachments = relationship("MaintenanceRequestAttachment", back_populates="request", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_maint_req_status", "status"),
        Index("idx_maint_req_equipment", "equipment_id"),
        Index("idx_maint_req_date", "request_date"),
    )

    def __repr__(self):
        return f"<MaintenanceRequest {self.request_no}>"


class MaintenanceRequestAttachment(BaseModel):
    """Bakım talebi ekleri (fotoğraf vb.)"""
    __tablename__ = "maintenance_request_attachments"

    request_id = Column(Integer, ForeignKey("maintenance_requests.id", ondelete="CASCADE"), nullable=False)

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=True)
    file_size = Column(Integer, nullable=True)

    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    request = relationship("MaintenanceRequest", back_populates="attachments")
    uploaded_by = relationship("User")

    def __repr__(self):
        return f"<MaintenanceRequestAttachment {self.file_name}>"


class MaintenanceChecklist(BaseModel):
    """Bakım kontrol listesi şablonları"""
    __tablename__ = "maintenance_checklists"

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Opsiyonel: Belirli bir ekipman veya bakım türü için
    equipment_id = Column(Integer, ForeignKey("equipments.id"), nullable=True)
    maintenance_type = Column(Enum(MaintenanceType), nullable=True)

    is_active = Column(Boolean, default=True)

    # İlişkiler
    equipment = relationship("Equipment", back_populates="checklists")
    items = relationship("MaintenanceChecklistItem", back_populates="checklist", cascade="all, delete-orphan",
                         order_by="MaintenanceChecklistItem.order_no")

    def __repr__(self):
        return f"<MaintenanceChecklist {self.name}>"


class MaintenanceChecklistItem(BaseModel):
    """Kontrol listesi maddeleri"""
    __tablename__ = "maintenance_checklist_items"

    checklist_id = Column(Integer, ForeignKey("maintenance_checklists.id", ondelete="CASCADE"), nullable=False)

    order_no = Column(Integer, default=1)
    description = Column(Text, nullable=False)
    is_required = Column(Boolean, default=True)

    # İlişkiler
    checklist = relationship("MaintenanceChecklist", back_populates="items")
    results = relationship("WorkOrderChecklistResult", back_populates="checklist_item")

    def __repr__(self):
        return f"<MaintenanceChecklistItem {self.order_no}>"


class MaintenanceWorkOrder(BaseModel):
    """Bakım İş Emirleri - Geliştirilmiş versiyon"""
    __tablename__ = "maintenance_work_orders"

    order_no = Column(String(50), unique=True, nullable=False, index=True)

    request_id = Column(Integer, ForeignKey("maintenance_requests.id"), nullable=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id"), nullable=False)

    # Tarihler
    planned_start_date = Column(DateTime, nullable=True)
    actual_start_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)

    status = Column(Enum(WorkOrderStatus), default=WorkOrderStatus.DRAFT)
    priority = Column(Enum(MaintenancePriority), default=MaintenancePriority.NORMAL)

    # Atanan Teknisyen
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Açıklamalar
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Süre Takibi
    estimated_hours = Column(Numeric(8, 2), nullable=True)
    actual_hours = Column(Numeric(8, 2), nullable=True)

    # İşçilik
    labor_hours = Column(Numeric(8, 2), default=0)
    hourly_rate = Column(Numeric(18, 4), default=0)

    # Maliyetler
    labor_cost = Column(Numeric(18, 4), default=0)
    material_cost = Column(Numeric(18, 4), default=0)
    total_cost = Column(Numeric(18, 4), default=0)

    # Kontrol Listesi
    checklist_id = Column(Integer, ForeignKey("maintenance_checklists.id"), nullable=True)

    # İlişkiler
    request = relationship("MaintenanceRequest", back_populates="work_orders")
    equipment = relationship("Equipment", back_populates="work_orders")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    checklist = relationship("MaintenanceChecklist")
    parts = relationship("MaintenanceWorkOrderPart", back_populates="work_order", cascade="all, delete-orphan")
    attachments = relationship("WorkOrderAttachment", back_populates="work_order", cascade="all, delete-orphan")
    checklist_results = relationship("WorkOrderChecklistResult", back_populates="work_order", cascade="all, delete-orphan")
    downtimes = relationship("EquipmentDowntime", back_populates="work_order")

    __table_args__ = (
        Index("idx_wo_status", "status"),
        Index("idx_wo_equipment", "equipment_id"),
        Index("idx_wo_assigned", "assigned_to_id"),
    )

    def __repr__(self):
        return f"<MaintenanceWorkOrder {self.order_no}>"


class MaintenanceWorkOrderPart(BaseModel):
    """İş Emrinde Kullanılan Parçalar"""
    __tablename__ = "maintenance_work_order_parts"

    work_order_id = Column(Integer, ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    quantity = Column(Numeric(18, 4), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    unit_cost = Column(Numeric(18, 4), default=0)
    total_cost = Column(Numeric(18, 4), default=0)

    used_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    # İlişkiler
    work_order = relationship("MaintenanceWorkOrder", back_populates="parts")
    item = relationship("Item")
    unit = relationship("Unit")

    def __repr__(self):
        return f"<MaintenanceWorkOrderPart {self.item_id}>"


class WorkOrderAttachment(BaseModel):
    """İş emri dosya ekleri"""
    __tablename__ = "work_order_attachments"

    work_order_id = Column(Integer, ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"), nullable=False)

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=True)
    file_size = Column(Integer, nullable=True)

    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    work_order = relationship("MaintenanceWorkOrder", back_populates="attachments")
    uploaded_by = relationship("User")

    def __repr__(self):
        return f"<WorkOrderAttachment {self.file_name}>"


class WorkOrderChecklistResult(BaseModel):
    """İş emri kontrol listesi sonuçları"""
    __tablename__ = "work_order_checklist_results"

    work_order_id = Column(Integer, ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"), nullable=False)
    checklist_item_id = Column(Integer, ForeignKey("maintenance_checklist_items.id"), nullable=False)

    is_checked = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    checked_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    checked_at = Column(DateTime, nullable=True)

    # İlişkiler
    work_order = relationship("MaintenanceWorkOrder", back_populates="checklist_results")
    checklist_item = relationship("MaintenanceChecklistItem", back_populates="results")
    checked_by = relationship("User")

    def __repr__(self):
        return f"<WorkOrderChecklistResult {self.work_order_id}-{self.checklist_item_id}>"


class MaintenancePlan(BaseModel):
    """Periyodik Bakım Planları - Geliştirilmiş versiyon"""
    __tablename__ = "maintenance_plans"

    equipment_id = Column(Integer, ForeignKey("equipments.id"), nullable=False)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Zaman Bazlı Sıklık
    frequency_type = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'yearly'
    frequency_value = Column(Integer, default=1)

    # Sayaç/Çalışma Saati Bazlı
    is_counter_based = Column(Boolean, default=False)
    counter_interval = Column(Integer, nullable=True)  # Her X saatte bir
    last_counter_value = Column(Numeric(18, 2), nullable=True)
    next_due_counter = Column(Numeric(18, 2), nullable=True)

    # Tarihler
    last_maintenance_date = Column(DateTime, nullable=True)
    next_maintenance_date = Column(DateTime, nullable=True)

    # Otomatik İş Emri
    auto_generate_work_order = Column(Boolean, default=True)
    lead_days = Column(Integer, default=7)  # Kaç gün önce iş emri oluşsun

    # Kontrol Listesi Şablonu
    checklist_id = Column(Integer, ForeignKey("maintenance_checklists.id"), nullable=True)

    is_active = Column(Boolean, default=True)

    # İlişkiler
    equipment = relationship("Equipment", back_populates="maintenance_plans")
    checklist = relationship("MaintenanceChecklist")

    __table_args__ = (
        Index("idx_plan_equipment", "equipment_id"),
        Index("idx_plan_next_date", "next_maintenance_date"),
    )

    def __repr__(self):
        return f"<MaintenancePlan {self.name}>"
