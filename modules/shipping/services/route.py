"""
Akıllı İş - Rota Planlama Servisi
"""

from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from database.models.route import Route, RouteStop, RouteStatus, RouteStopType
from database.models.shipping import Shipment, ShipmentStatus
from database.models.sales import DeliveryNote
from modules.shipping.services.base import ShipmentService


class RoutePlanningService:
    def __init__(self, session: Session):
        self.session = session
        self.shipment_service = ShipmentService(session)

    def create_route(
        self,
        vehicle_id: Optional[int] = None,
        driver_id: Optional[int] = None,
        planned_start_time: Optional[datetime] = None,
        route_no: Optional[str] = None,
    ) -> Route:
        """Yeni bir rota taslağı oluşturur."""

        if not route_no:
            # Otomatik rota no üretimi: ROTA-YYYYMMDD-SEQUENCE
            today_str = datetime.now().strftime("%Y%m%d")
            count = (
                self.session.query(Route)
                .filter(Route.route_no.like(f"ROTA-{today_str}-%"))
                .count()
            )
            route_no = f"ROTA-{today_str}-{count + 1:03d}"

        route = Route(
            route_no=route_no,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            planned_start_time=planned_start_time,
            status=RouteStatus.DRAFT,
        )
        self.session.add(route)
        self.session.flush()
        return route

    def add_stop(
        self,
        route_id: int,
        stop_type: RouteStopType,
        location_name: str,
        address: Optional[str] = None,
        shipment_id: Optional[int] = None,
        planned_arrival: Optional[datetime] = None,
        sequence: Optional[int] = None,
    ) -> RouteStop:
        """Rotaya bir durak ekler."""

        route = self.session.query(Route).get(route_id)
        if not route:
            raise ValueError("Rota bulunamadı.")

        # Eğer sequence verilmediyse son sıraya ekle
        if sequence is None:
            max_seq = (
                self.session.query(func.max(RouteStop.sequence))
                .filter(RouteStop.route_id == route_id)
                .scalar()
            )
            sequence = (max_seq or 0) + 1

        stop = RouteStop(
            route_id=route_id,
            stop_type=stop_type,
            location_name=location_name,
            address=address,
            shipment_id=shipment_id,
            planned_arrival=planned_arrival,
            sequence=sequence,
        )
        self.session.add(stop)

        # Eğer bir sevkiyat eklendiyse, sevkiyatın bilgilerini güncellemek gerekebilir
        # Şimdilik sadece ilişkiyi kuruyoruz.

        self.session.flush()
        return stop

    def assign_shipment_to_route(self, route_id: int, shipment_id: int):
        """Mevcut bir sevkiyatı rotaya ekler (Delivery Stop olarak)."""
        shipment = self.session.query(Shipment).get(shipment_id)
        if not shipment:
            raise ValueError("Sevkiyat bulunamadı.")

        # Sevkiyatın teslimat adresi bilgisini alalım (ilk irsaliyeden)
        # Basitlik için ilk irsaliyenin müşteri bilgisi veya sevkiyatın kendi adresi kullanılabilir
        shipping_address = "-"
        customer_name = "Unknown Customer"

        # Sevkiyata bağlı irsaliyelerden adres bulmaya çalış
        # Shipment -> ShipmentItem -> DeliveryNote -> Customer/Address
        if shipment.items:
            first_item = shipment.items[0]
            if first_item.delivery_note:
                dn = first_item.delivery_note
                shipping_address = dn.shipping_address or "-"
                if dn.customer:
                    customer_name = dn.customer.name

        # Durak oluştur
        self.add_stop(
            route_id=route_id,
            stop_type=RouteStopType.DELIVERY,
            location_name=customer_name,
            address=shipping_address,
            shipment_id=shipment_id,
        )

    def get_route_details(self, route_id: int) -> Optional[Route]:
        """Rota detaylarını duraklarıyla beraber getirir."""
        return (
            self.session.query(Route)
            .options(
                joinedload(Route.stops).joinedload(RouteStop.shipment),
                joinedload(Route.vehicle),
                joinedload(Route.driver),
            )
            .filter(Route.id == route_id)
            .first()
        )

    def optimize_route(self, route_id: int):
        """
        Rotadaki durakları optimize eder.
        Şimdilik 'Greedy' yaklaşımı ile basit bir sıralama veya sadece sequence'i yeniden düzenleme yapabiliriz.
        Gerçek bir TSP (Traveling Salesman) algoritması ileride eklenebilir.
        Şu anlık: Sadece sequence numaralarını normalleştirir (1, 2, 3...)
        """
        route = self.get_route_details(route_id)
        if not route or not route.stops:
            return

        # Mevcut durakları sequence'e göre sırala
        current_stops = sorted(route.stops, key=lambda s: s.sequence)

        # Yeniden numaralandır
        for idx, stop in enumerate(current_stops, start=1):
            stop.sequence = idx

        self.session.flush()

    def calculate_capacity_usage(self, route_id: int) -> Dict[str, float]:
        """Rotadaki toplam yükü hesaplar."""
        route = self.get_route_details(route_id)
        if not route:
            return {"total_weight": 0, "total_volume": 0}

        total_weight = 0.0
        total_volume = 0.0

        for stop in route.stops:
            if stop.shipment_id and stop.shipment:
                # Sevkiyatın toplam ağırlığını/hacmini al
                # Shipment modelinde bu alanlar varsa topla, yoksa hesapla
                # Şimdilik Shipment modelinde total_weight var mı kontrol etmeliyiz.
                # Varsayalım ki ShipmentService hesaplıyor veya Shipment modelinde var.
                # (Shipment modelini incelemedik ama genellikle olur)
                # Sevkiyat modelinde total_weight_kg ve total_volume_m3 var
                if stop.shipment.total_weight_kg:
                    total_weight += float(stop.shipment.total_weight_kg)
                if stop.shipment.total_volume_m3:
                    total_volume += float(stop.shipment.total_volume_m3)

        return {"total_weight": total_weight, "total_volume": total_volume}

    def validate_capacity(
        self, route_id: int, new_shipment_id: int
    ) -> tuple[bool, str]:
        """
        Rota kapasite kontrolü yapar.
        Yeni eklenecek sevkiyat ile birlikte araç kapasitesinin aşılıp aşılmadığını kontrol eder.
        Dönüş: (is_valid, message)
        """
        route = self.get_route_details(route_id)
        if not route:
            return False, "Rota bulunamadı."

        if not route.vehicle:
            return True, "Araç atanmamış, kapasite kontrolü atlandı."

        vehicle = route.vehicle

        # 1. Mevcut yükü hesapla
        current_load = self.calculate_capacity_usage(route_id)
        total_weight = float(current_load["total_weight"] or 0)
        total_volume = float(current_load["total_volume"] or 0)

        # 2. Yeni sevkiyatın yükünü ekle
        shipment = self.session.query(Shipment).get(new_shipment_id)
        if not shipment:
            return False, "Sevkiyat bulunamadı."

        new_weight = float(shipment.total_weight_kg or 0)
        new_volume = float(shipment.total_volume_m3 or 0)

        final_weight = total_weight + new_weight
        final_volume = total_volume + new_volume

        # 3. Kontrol
        errors = []
        if vehicle.capacity_kg and final_weight > float(vehicle.capacity_kg):
            errors.append(
                f"Ağırlık kapasitesi aşılıyor! (Mevcut+Yeni: {final_weight} > Kapasite: {vehicle.capacity_kg})"
            )

        if vehicle.capacity_m3 and final_volume > float(vehicle.capacity_m3):
            errors.append(
                f"Hacim kapasitesi aşılıyor! (Mevcut+Yeni: {final_volume} > Kapasite: {vehicle.capacity_m3})"
            )

        if errors:
            return False, "\n".join(errors)

        return True, "Kapasite uygun."
