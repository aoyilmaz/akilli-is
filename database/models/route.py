"""
Akıllı İş - Rota ve Taşıyıcı Planlama Modülü Veritabanı Modelleri
"""

from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Numeric,
    Enum as SQLEnum,
    Float,
)
from sqlalchemy.orm import relationship
from database.base import BaseModel


# === ENUM TANIMLARI ===


class RouteStatus(str, Enum):
    """Rota durumları"""

    DRAFT = "draft"  # Taslak
    APPROVED = "approved"  # Onaylandı
    ACTIVE = "active"  # Aktif/Yolda
    COMPLETED = "completed"  # Tamamlandı
    CANCELLED = "cancelled"  # İptal edildi


class RouteStopType(str, Enum):
    """Rota durak tipleri"""

    PICKUP = "pickup"  # Yükleme noktası (Depo)
    DELIVERY = "delivery"  # Teslimat noktası (Müşteri)
    WAYPOINT = "waypoint"  # Ara nokta (Mola, Yakıt vb.)


# === MODELLER ===


class Route(BaseModel):
    """Rota/Sefer Planı Tablosu"""

    __tablename__ = "routes"

    # Temel bilgiler
    route_no = Column(String(50), unique=True, nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)

    # Durum
    status = Column(
        SQLEnum(RouteStatus, values_callable=lambda x: [e.value for e in x]),
        default=RouteStatus.DRAFT,
    )

    # Zamanlama
    planned_start_time = Column(DateTime, nullable=True)
    planned_end_time = Column(DateTime, nullable=True)
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)

    # Metrikler
    total_distance_km = Column(Float, default=0.0)
    total_cost = Column(Numeric(15, 2), default=0)

    # Notlar
    description = Column(Text)

    # İlişkiler
    vehicle = relationship("Vehicle", foreign_keys=[vehicle_id])
    driver = relationship("Driver", foreign_keys=[driver_id])
    stops = relationship(
        "RouteStop",
        back_populates="route",
        cascade="all, delete-orphan",
        order_by="RouteStop.sequence",
    )

    def __repr__(self):
        return f"<Route {self.route_no}>"


class RouteStop(BaseModel):
    """Rota Durakları Tablosu"""

    __tablename__ = "route_stops"

    route_id = Column(
        Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False
    )

    # Sıralama ve Tip
    sequence = Column(Integer, nullable=False, default=0)
    stop_type = Column(
        SQLEnum(RouteStopType, values_callable=lambda x: [e.value for e in x]),
        default=RouteStopType.DELIVERY,
    )

    # İlişkili nesneler (Lokasyon veya Sevkiyat)
    # Location (Depo veya Müşteri Adresi) - Şimdilik sadece text/string tutabiliriz veya Location modeline bağlayabiliriz
    # Basitlik için shipping_address olarak tutalım, ileride Location tablosuna bağlanabilir.
    location_name = Column(String(255))
    address = Column(Text)

    # Eğer sevkiyat teslimatı ise
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True)

    # Zamanlama
    planned_arrival = Column(DateTime, nullable=True)
    planned_departure = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    actual_departure = Column(DateTime, nullable=True)

    # Notlar
    notes = Column(Text)

    # İlişkiler
    route = relationship("Route", back_populates="stops")
    shipment = relationship("Shipment", foreign_keys=[shipment_id])

    def __repr__(self):
        return f"<RouteStop {self.route_id}-{self.sequence}>"
