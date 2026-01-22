"""
Akıllı İş - Sevkiyat Modülü Veritabanı Modelleri

Araç, sürücü ve sevkiyat yönetimi için gerekli modeller.
"""

from enum import Enum
from datetime import datetime
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


class VehicleStatus(str, Enum):
    """Araç durumları"""

    AKTIF = "aktif"  # Kullanıma hazır
    BAKIMDA = "bakimda"  # Bakımda
    PASIF = "pasif"  # Kullanım dışı


class VehicleType(str, Enum):
    """Araç türleri"""

    TIR = "tir"
    KAMYON = "kamyon"
    KAMYONET = "kamyonet"
    PANELVAN = "panelvan"
    PICKUP = "pickup"
    DIGER = "diger"


class DriverStatus(str, Enum):
    """Sürücü durumları"""

    MUSAIT = "musait"  # Müsait
    GOREVDE = "gorevde"  # Görevde
    IZINLI = "izinli"  # İzinli
    PASIF = "pasif"  # Aktif değil


class ShipmentStatus(str, Enum):
    """Sevkiyat durumları"""

    PLANLANDI = "planlandi"  # Planlandı
    YUKLENIYOR = "yukleniyor"  # Yükleniyor
    YOLDA = "yolda"  # Yolda
    TESLIM_EDILDI = "teslim"  # Teslim edildi
    IPTAL = "iptal"  # İptal edildi


# === ARAÇ YÖNETİMİ ===


class Vehicle(BaseModel):
    """Araçlar tablosu"""

    __tablename__ = "vehicles"

    # Temel bilgiler
    plate_no = Column(String(15), unique=True, nullable=False, index=True)
    brand = Column(String(50), nullable=True)
    model = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)

    # Araç türü
    vehicle_type = Column(
        SQLEnum(VehicleType, values_callable=lambda x: [e.value for e in x]),
        default=VehicleType.KAMYON,
    )

    # Kapasite bilgileri
    capacity_kg = Column(Numeric(12, 2), nullable=True)  # Yük kapasitesi (kg)
    capacity_m3 = Column(Numeric(10, 2), nullable=True)  # Hacim kapasitesi (m³)
    pallet_capacity = Column(Integer, nullable=True)  # Palet kapasitesi

    # Durum
    status = Column(
        SQLEnum(VehicleStatus, values_callable=lambda x: [e.value for e in x]),
        default=VehicleStatus.AKTIF,
    )

    # Notlar
    notes = Column(Text, nullable=True)

    # İlişkiler
    drivers = relationship("Driver", back_populates="default_vehicle")
    shipments = relationship("Shipment", back_populates="vehicle")

    __table_args__ = (
        Index("idx_vehicle_status", "status"),
        Index("idx_vehicle_type", "vehicle_type"),
    )

    @property
    def status_display(self) -> str:
        """Durum gösterimi"""
        status_names = {
            "aktif": "Aktif",
            "bakimda": "Bakımda",
            "pasif": "Pasif",
        }
        return status_names.get(self.status.value, self.status.value)

    @property
    def vehicle_type_display(self) -> str:
        """Araç türü gösterimi"""
        type_names = {
            "tir": "Tır",
            "kamyon": "Kamyon",
            "kamyonet": "Kamyonet",
            "panelvan": "Panelvan",
            "pickup": "Pickup",
            "diger": "Diğer",
        }
        return type_names.get(self.vehicle_type.value, self.vehicle_type.value)

    @property
    def display_name(self) -> str:
        """Görüntüleme adı"""
        parts = [self.plate_no]
        if self.brand:
            parts.append(self.brand)
        if self.model:
            parts.append(self.model)
        return " - ".join(parts)

    def __repr__(self):
        return f"<Vehicle {self.plate_no}>"


# === SÜRÜCÜ YÖNETİMİ ===


class Driver(BaseModel):
    """Sürücüler tablosu"""

    __tablename__ = "drivers"

    # Temel bilgiler
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    tc_no = Column(String(11), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)

    # Ehliyet bilgileri
    license_type = Column(String(10), nullable=True)  # B, C, D, E vb.
    license_expiry = Column(Date, nullable=True)

    # SRC belgesi
    src_no = Column(String(20), nullable=True)
    src_expiry = Column(Date, nullable=True)

    # Durum
    status = Column(
        SQLEnum(DriverStatus, values_callable=lambda x: [e.value for e in x]),
        default=DriverStatus.MUSAIT,
    )

    # Varsayılan araç
    default_vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)

    # Notlar
    notes = Column(Text, nullable=True)

    # İlişkiler
    default_vehicle = relationship("Vehicle", back_populates="drivers")
    shipments = relationship("Shipment", back_populates="driver")

    __table_args__ = (
        Index("idx_driver_status", "status"),
        Index("idx_driver_license_expiry", "license_expiry"),
    )

    @property
    def status_display(self) -> str:
        """Durum gösterimi"""
        status_names = {
            "musait": "Müsait",
            "gorevde": "Görevde",
            "izinli": "İzinli",
            "pasif": "Pasif",
        }
        return status_names.get(self.status.value, self.status.value)

    @property
    def is_license_expiring(self) -> bool:
        """Ehliyet süresi 30 gün içinde doluyor mu?"""
        if not self.license_expiry:
            return False
        from datetime import date, timedelta
        return self.license_expiry <= date.today() + timedelta(days=30)

    @property
    def is_src_expiring(self) -> bool:
        """SRC süresi 30 gün içinde doluyor mu?"""
        if not self.src_expiry:
            return False
        from datetime import date, timedelta
        return self.src_expiry <= date.today() + timedelta(days=30)

    def __repr__(self):
        return f"<Driver {self.code} - {self.name}>"


# === SEVKİYAT YÖNETİMİ ===


class Shipment(BaseModel):
    """Sevkiyatlar tablosu"""

    __tablename__ = "shipments"

    # Temel bilgiler
    shipment_no = Column(String(20), unique=True, nullable=False, index=True)
    shipment_date = Column(Date, nullable=False)

    # Araç ve sürücü
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)

    # Durum
    status = Column(
        SQLEnum(ShipmentStatus, values_callable=lambda x: [e.value for e in x]),
        default=ShipmentStatus.PLANLANDI,
    )

    # Zamanlar
    departure_time = Column(DateTime, nullable=True)  # Çıkış zamanı
    return_time = Column(DateTime, nullable=True)  # Dönüş zamanı

    # Yük bilgileri
    total_weight_kg = Column(Numeric(12, 2), default=0)  # Toplam ağırlık
    total_volume_m3 = Column(Numeric(10, 2), default=0)  # Toplam hacim
    total_pallets = Column(Integer, default=0)  # Toplam palet sayısı

    # Rota bilgisi (JSON formatında teslimat sırası)
    route_order = Column(Text, nullable=True)

    # Notlar
    notes = Column(Text, nullable=True)

    # İlişkiler
    vehicle = relationship("Vehicle", back_populates="shipments")
    driver = relationship("Driver", back_populates="shipments")
    items = relationship(
        "ShipmentItem", back_populates="shipment", cascade="all, delete-orphan"
    )
    loads = relationship(
        "ShipmentLoad", back_populates="shipment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_shipment_date", "shipment_date"),
        Index("idx_shipment_status", "status"),
        Index("idx_shipment_vehicle", "vehicle_id"),
        Index("idx_shipment_driver", "driver_id"),
    )

    @property
    def status_display(self) -> str:
        """Durum gösterimi"""
        status_names = {
            "planlandi": "Planlandı",
            "yukleniyor": "Yükleniyor",
            "yolda": "Yolda",
            "teslim": "Teslim Edildi",
            "iptal": "İptal",
        }
        return status_names.get(self.status.value, self.status.value)

    @property
    def total_items(self) -> int:
        """Toplam irsaliye sayısı"""
        return len(self.items) if self.items else 0

    @property
    def total_loads(self) -> int:
        """Toplam yüklenen birim sayısı"""
        return len(self.loads) if self.loads else 0

    @property
    def is_capacity_exceeded(self) -> bool:
        """Araç kapasitesi aşıldı mı?"""
        if not self.vehicle:
            return False
        if self.vehicle.capacity_kg and self.total_weight_kg:
            if self.total_weight_kg > self.vehicle.capacity_kg:
                return True
        if self.vehicle.capacity_m3 and self.total_volume_m3:
            if self.total_volume_m3 > self.vehicle.capacity_m3:
                return True
        if self.vehicle.pallet_capacity and self.total_pallets:
            if self.total_pallets > self.vehicle.pallet_capacity:
                return True
        return False

    def __repr__(self):
        return f"<Shipment {self.shipment_no}>"


class ShipmentItem(BaseModel):
    """Sevkiyat kalemleri (irsaliyeler)"""

    __tablename__ = "shipment_items"

    # Sevkiyat ilişkisi
    shipment_id = Column(
        Integer, ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False
    )

    # İrsaliye ilişkisi
    delivery_note_id = Column(
        Integer, ForeignKey("delivery_notes.id"), nullable=False
    )

    # Teslimat sırası
    sequence = Column(Integer, default=0)

    # Notlar
    notes = Column(Text, nullable=True)

    # İlişkiler
    shipment = relationship("Shipment", back_populates="items")
    delivery_note = relationship("DeliveryNote")

    __table_args__ = (
        Index("idx_si_shipment", "shipment_id"),
        Index("idx_si_delivery_note", "delivery_note_id"),
    )

    def __repr__(self):
        return f"<ShipmentItem {self.shipment_id}-{self.delivery_note_id}>"


class ShipmentLoad(BaseModel):
    """Sevkiyat yük detayları (SSCC/Palet)"""

    __tablename__ = "shipment_loads"

    # Sevkiyat ilişkisi
    shipment_id = Column(
        Integer, ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False
    )

    # Taşıma birimi (SSCC) ilişkisi
    transport_unit_id = Column(
        Integer, ForeignKey("transport_units.id"), nullable=False
    )

    # Yükleme bilgileri
    load_sequence = Column(Integer, default=0)  # Yükleme sırası
    loaded_at = Column(DateTime, nullable=True)  # Yüklenme zamanı
    loaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # İlişkiler
    shipment = relationship("Shipment", back_populates="loads")
    transport_unit = relationship("TransportUnit")
    loaded_by = relationship("User", foreign_keys=[loaded_by_id])

    __table_args__ = (
        Index("idx_sl_shipment", "shipment_id"),
        Index("idx_sl_transport_unit", "transport_unit_id"),
    )

    def __repr__(self):
        return f"<ShipmentLoad {self.shipment_id}-{self.transport_unit_id}>"
