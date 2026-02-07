"""
Akıllı İş - Rota ve Taşıyıcı Planlama Ana Ekranı
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QMessageBox,
    QPushButton,
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from database.base import get_session
from database.models.shipping import Vehicle, Shipment, ShipmentStatus
from database.models.route import Route, RouteStatus, RouteStop, RouteStopType

from modules.shipping.views.shipment_pool import ShipmentPoolWidget
from modules.shipping.views.route_timeline import RouteTimelineWidget
from modules.shipping.views.route_map import RouteMapWidget
from modules.shipping.services.route import RoutePlanningService


class RoutePlanningWidget(QWidget):
    """Rota Planlama Modülü Ana Ekranı."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rota ve Taşıyıcı Planlama")
        self.resize(1200, 800)

        self.session = get_session()
        self.service = RoutePlanningService(self.session)

        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        """Arayüz bileşenlerini oluşturur."""
        # Ana Layout
        main_layout = QVBoxLayout(self)

        # Toolbar (Layout based)
        toolbar_layout = QHBoxLayout()
        main_layout.addLayout(toolbar_layout)

        refresh_btn = QPushButton("Yenile")
        refresh_btn.setIcon(QIcon(":/icons/refresh"))  # Varsa
        refresh_btn.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(refresh_btn)

        auto_plan_btn = QPushButton("Otomatik Planla")
        auto_plan_btn.clicked.connect(self.auto_plan)
        toolbar_layout.addWidget(auto_plan_btn)

        toolbar_layout.addStretch()

        # Splitter (Sol: Havuz, Sağ: Timeline + Harita)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # 1. Sol Panel: Sevkiyat Havuzu
        self.shipment_pool = ShipmentPoolWidget()
        splitter.addWidget(self.shipment_pool)

        # 2. Orta/Sağ Panel: Timeline ve Harita
        right_panel = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(right_panel)

        # Timeline
        self.timeline = RouteTimelineWidget()
        self.timeline.shipment_dropped.connect(self.on_shipment_dropped)
        right_panel.addWidget(self.timeline)

        # Harita
        self.map_widget = RouteMapWidget()
        right_panel.addWidget(self.map_widget)

        # Splitter oranları
        splitter.setSizes([300, 900])
        right_panel.setSizes([500, 300])

    def refresh_data(self):
        """Verileri veritabanından çeker ve arayüzü günceller."""
        # 1. Atanmamış Sevkiyatlar
        pending_shipments = (
            self.session.query(Shipment)
            .filter(Shipment.status == ShipmentStatus.PLANLANDI)
            .all()
        )
        self.shipment_pool.load_shipments(pending_shipments)

        # 2. Araçlar ve Rotalar
        vehicles = self.session.query(Vehicle).filter(Vehicle.is_active == True).all()
        # Bugün ve sonrası için aktif/taslak rotalar
        routes = (
            self.session.query(Route)
            .filter(Route.status != RouteStatus.CANCELLED)
            .all()
        )

        self.timeline.load_data(vehicles, routes)

    def on_shipment_dropped(self, vehicle_id, shipment_id, drop_time):
        """Timeline'a sevkiyat bırakıldığında çalışır."""
        try:
            # 1. O gün ve o araç için bir rota var mı? Yoksa oluştur.
            # Basitlik için drop_time tarihine bakıyoruz.
            target_date = drop_time.date()

            route = (
                self.session.query(Route)
                .filter(
                    Route.vehicle_id == vehicle_id,
                    # Route.planned_start_time cast date == target_date (SQLAlchemy date hook gerekebilir)
                    # Şimdilik memory'de filtreleyelim veya yeni rota açalım
                )
                .all()
            )

            # O gün için bu araçta rota bul
            active_route = None
            for r in route:
                if r.planned_start_time and r.planned_start_time.date() == target_date:
                    active_route = r
                    break

            if not active_route:
                # Yeni Rota Oluştur
                # Varsayılan şoför bul (araçta tanımlıysa)
                vehicle = self.session.get(Vehicle, vehicle_id)
                driver_id = vehicle.default_driver_id if vehicle else None

                active_route = self.service.create_route(
                    vehicle_id=vehicle_id,
                    driver_id=driver_id,
                    planned_start_time=drop_time,
                )
                print(f"Yeni rota oluşturuldu: {active_route.route_no}")

            # 2. Kapasite Kontrolü
            is_valid, message = self.service.validate_capacity(
                active_route.id, shipment_id
            )
            if not is_valid:
                reply = QMessageBox.question(
                    self,
                    "Kapasite Uyarısı",
                    f"{message}\n\nYine de eklemek istiyor musunuz?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.No:
                    self.session.rollback()
                    return

            # 3. Sevkiyatı rotaya ekle
            self.service.assign_shipment_to_route(active_route.id, shipment_id)
            self.service.optimize_route(active_route.id)  # Basit sıralama

            self.session.commit()

            QMessageBox.information(
                self, "Başarılı", f"Sevkiyat rotaya eklendi: {active_route.route_no}"
            )
            self.refresh_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İşlem başarısız: {str(e)}")
            self.session.rollback()

    def auto_plan(self):
        QMessageBox.information(
            self, "Bilgi", "Otomatik planlama motoru (TSP) henüz aktif değil."
        )
