"""
Akıllı İş - Sevkiyat Modülü
"""

from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox

from .shipment_list import ShipmentListPage
from .shipment_form import ShipmentFormPage
from modules.development import ErrorHandler


class ShipmentModule(QWidget):
    """Sevkiyat yönetimi modülü"""

    page_title = "Sevkiyatlar"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.vehicle_service = None
        self.driver_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # Liste sayfası
        self.list_page = ShipmentListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_shipment)
        self.list_page.view_clicked.connect(self._show_view)
        self.list_page.refresh_requested.connect(self._load_data)
        self.stack.addWidget(self.list_page)

        layout.addWidget(self.stack)

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_service()
        self._load_data()

    def _ensure_service(self):
        if not self.service:
            try:
                from modules.shipping.services import (
                    ShipmentService,
                    VehicleService,
                    DriverService,
                )

                self.service = ShipmentService()
                self.vehicle_service = VehicleService()
                self.driver_service = DriverService()
            except Exception as e:
                ErrorHandler.handle_error(
                    e,
                    module="shipping",
                    screen="ShipmentModule",
                    function="_ensure_service",
                    parent_widget=self,
                    show_message=False,
                )

    def _load_data(self):
        if not self.service:
            return

        try:
            shipments = self.service.get_all()
            data = []
            for s in shipments:
                data.append(
                    {
                        "id": s.id,
                        "shipment_no": s.shipment_no,
                        "shipment_date": (
                            s.shipment_date.strftime("%d.%m.%Y")
                            if s.shipment_date
                            else ""
                        ),
                        "vehicle": s.vehicle.plate_no if s.vehicle else "",
                        "vehicle_id": s.vehicle_id,
                        "driver": s.driver.name if s.driver else "",
                        "driver_id": s.driver_id,
                        "status": s.status.value if s.status else "",
                        "status_display": s.status_display,
                        "total_items": s.total_items,
                        "total_loads": s.total_loads,
                        "total_weight_kg": (
                            float(s.total_weight_kg) if s.total_weight_kg else 0
                        ),
                        "total_volume_m3": (
                            float(s.total_volume_m3) if s.total_volume_m3 else 0
                        ),
                        "total_pallets": s.total_pallets,
                        "is_capacity_exceeded": s.is_capacity_exceeded,
                        "notes": s.notes,
                    }
                )
            self.list_page.load_data(data)
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module="shipping",
                screen="ShipmentModule",
                function="_load_data",
                parent_widget=self,
                show_message=False,
            )
            self.list_page.load_data([])

    def _get_vehicles_for_combo(self):
        """Form için araç listesini al"""
        if not self.vehicle_service:
            return []

        try:
            vehicles = self.vehicle_service.get_available()
            return [
                {
                    "id": v.id,
                    "plate_no": v.plate_no,
                    "vehicle_type_display": v.vehicle_type_display,
                    "capacity_kg": float(v.capacity_kg) if v.capacity_kg else 0,
                    "capacity_m3": float(v.capacity_m3) if v.capacity_m3 else 0,
                    "pallet_capacity": v.pallet_capacity,
                }
                for v in vehicles
            ]
        except:
            return []

    def _get_drivers_for_combo(self):
        """Form için sürücü listesini al"""
        if not self.driver_service:
            return []

        try:
            drivers = self.driver_service.get_available()
            return [
                {
                    "id": d.id,
                    "name": d.name,
                    "default_vehicle": (
                        d.default_vehicle.plate_no if d.default_vehicle else ""
                    ),
                    "default_vehicle_id": d.default_vehicle_id,
                }
                for d in drivers
            ]
        except:
            return []

    def _show_add_form(self):
        vehicles = self._get_vehicles_for_combo()
        drivers = self._get_drivers_for_combo()
        form = ShipmentFormPage(self.service, vehicles=vehicles, drivers=drivers)
        form.saved.connect(self._save_shipment)
        form.cancelled.connect(self._back_to_list)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_edit_form(self, shipment_id: int):
        if not self.service:
            return

        try:
            shipment = self.service.get_by_id(shipment_id)
            if not shipment:
                QMessageBox.warning(self, "Uyarı", "Sevkiyat bulunamadı.")
                return

            shipment_data = {
                "id": shipment.id,
                "shipment_no": shipment.shipment_no,
                "shipment_date": (
                    shipment.shipment_date.strftime("%Y-%m-%d")
                    if shipment.shipment_date
                    else None
                ),
                "vehicle_id": shipment.vehicle_id,
                "driver_id": shipment.driver_id,
                "status": shipment.status.value if shipment.status else "planlandi",
                "total_weight_kg": (
                    float(shipment.total_weight_kg) if shipment.total_weight_kg else 0
                ),
                "total_volume_m3": (
                    float(shipment.total_volume_m3) if shipment.total_volume_m3 else 0
                ),
                "total_pallets": shipment.total_pallets,
                "notes": shipment.notes,
                "loads": [
                    {
                        "id": load.id,
                        "transport_unit_id": load.transport_unit_id,
                        "sscc": load.transport_unit.sscc if load.transport_unit else "",
                        "loaded_at": load.loaded_at,
                    }
                    for load in shipment.loads
                ],
            }

            vehicles = self._get_vehicles_for_combo()
            drivers = self._get_drivers_for_combo()
            form = ShipmentFormPage(
                self.service,
                shipment_data=shipment_data,
                vehicles=vehicles,
                drivers=drivers,
            )
            form.saved.connect(self._save_shipment)
            form.cancelled.connect(self._back_to_list)
            self.stack.addWidget(form)
            self.stack.setCurrentWidget(form)
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module="shipping",
                screen="ShipmentModule",
                function="_show_edit_form",
                parent_widget=self,
            )

    def _show_view(self, shipment_id: int):
        self._show_edit_form(shipment_id)

    def _save_shipment(self, data: dict):
        if not self.service:
            return

        try:
            shipment_id = data.pop("id", None)
            shipment_no = data.pop("shipment_no", None)

            # Enum ve tarih dönüşümleri
            from database.models.shipping import ShipmentStatus

            if "status" in data:
                data["status"] = ShipmentStatus(data["status"])

            # Tarih dönüşümü
            if data.get("shipment_date"):
                data["shipment_date"] = datetime.strptime(
                    data["shipment_date"], "%Y-%m-%d"
                ).date()

            if shipment_id:
                self.service.update(shipment_id, **data)
                QMessageBox.information(self, "Başarılı", "Sevkiyat güncellendi.")
            else:
                self.service.create(**data)
                QMessageBox.information(self, "Başarılı", "Sevkiyat oluşturuldu.")

            self._back_to_list()
            self._load_data()
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module="shipping",
                screen="ShipmentModule",
                function="_save_shipment",
                parent_widget=self,
            )

    def _delete_shipment(self, shipment_id: int):
        if not self.service:
            return

        reply = QMessageBox.question(
            self,
            "Onay",
            "Bu sevkiyatı silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.service.delete(shipment_id)
            QMessageBox.information(self, "Başarılı", "Sevkiyat silindi.")
            self._load_data()
        except ValueError as e:
            QMessageBox.warning(self, "Uyarı", str(e))
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module="shipping",
                screen="ShipmentModule",
                function="_delete_shipment",
                parent_widget=self,
            )

    def _back_to_list(self):
        while self.stack.count() > 1:
            widget = self.stack.widget(1)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        self.stack.setCurrentIndex(0)
