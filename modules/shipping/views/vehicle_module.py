"""
Akıllı İş - Araç Modülü
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox

from .vehicle_list import VehicleListPage
from .vehicle_form import VehicleFormPage
from modules.development import ErrorHandler


class VehicleModule(QWidget):
    """Araç yönetimi modülü"""

    page_title = "Araçlar"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # Liste sayfası
        self.list_page = VehicleListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_vehicle)
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
                from modules.shipping.services import VehicleService
                self.service = VehicleService()
            except Exception as e:
                ErrorHandler.handle_error(
                    e,
                    module='shipping',
                    screen='VehicleModule',
                    function='_ensure_service',
                    parent_widget=self,
                    show_message=False
                )

    def _load_data(self):
        if not self.service:
            return

        try:
            vehicles = self.service.get_all(active_only=False)
            data = []
            for v in vehicles:
                data.append({
                    "id": v.id,
                    "plate_no": v.plate_no,
                    "vehicle_type": v.vehicle_type.value if v.vehicle_type else "",
                    "vehicle_type_display": v.vehicle_type_display,
                    "brand": v.brand,
                    "model": v.model,
                    "year": v.year,
                    "capacity_kg": float(v.capacity_kg) if v.capacity_kg else 0,
                    "capacity_m3": float(v.capacity_m3) if v.capacity_m3 else 0,
                    "pallet_capacity": v.pallet_capacity,
                    "status": v.status.value if v.status else "",
                    "status_display": v.status_display,
                    "notes": v.notes,
                })
            self.list_page.load_data(data)
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='shipping',
                screen='VehicleModule',
                function='_load_data',
                parent_widget=self,
                show_message=False
            )
            self.list_page.load_data([])

    def _show_add_form(self):
        form = VehicleFormPage()
        form.saved.connect(self._save_vehicle)
        form.cancelled.connect(self._back_to_list)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_edit_form(self, vehicle_id: int):
        if not self.service:
            return

        try:
            vehicle = self.service.get_by_id(vehicle_id)
            if not vehicle:
                QMessageBox.warning(self, "Uyarı", "Araç bulunamadı.")
                return

            vehicle_data = {
                "id": vehicle.id,
                "plate_no": vehicle.plate_no,
                "vehicle_type": vehicle.vehicle_type.value if vehicle.vehicle_type else "kamyon",
                "brand": vehicle.brand,
                "model": vehicle.model,
                "year": vehicle.year,
                "capacity_kg": float(vehicle.capacity_kg) if vehicle.capacity_kg else 0,
                "capacity_m3": float(vehicle.capacity_m3) if vehicle.capacity_m3 else 0,
                "pallet_capacity": vehicle.pallet_capacity,
                "status": vehicle.status.value if vehicle.status else "aktif",
                "notes": vehicle.notes,
            }

            form = VehicleFormPage(vehicle_data)
            form.saved.connect(self._save_vehicle)
            form.cancelled.connect(self._back_to_list)
            self.stack.addWidget(form)
            self.stack.setCurrentWidget(form)
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='shipping',
                screen='VehicleModule',
                function='_show_edit_form',
                parent_widget=self,
            )

    def _show_view(self, vehicle_id: int):
        # Şimdilik edit formuna yönlendir (read-only view eklenebilir)
        self._show_edit_form(vehicle_id)

    def _save_vehicle(self, data: dict):
        if not self.service:
            return

        try:
            vehicle_id = data.pop("id", None)

            # Enum değerlerini dönüştür
            from database.models.shipping import VehicleStatus, VehicleType
            if "vehicle_type" in data:
                data["vehicle_type"] = VehicleType(data["vehicle_type"])
            if "status" in data:
                data["status"] = VehicleStatus(data["status"])

            if vehicle_id:
                self.service.update(vehicle_id, **data)
                QMessageBox.information(self, "Başarılı", "Araç güncellendi.")
            else:
                self.service.create(**data)
                QMessageBox.information(self, "Başarılı", "Araç oluşturuldu.")

            self._back_to_list()
            self._load_data()
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='shipping',
                screen='VehicleModule',
                function='_save_vehicle',
                parent_widget=self,
            )

    def _delete_vehicle(self, vehicle_id: int):
        if not self.service:
            return

        reply = QMessageBox.question(
            self,
            "Onay",
            "Bu aracı silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.service.delete(vehicle_id)
            QMessageBox.information(self, "Başarılı", "Araç silindi.")
            self._load_data()
        except ValueError as e:
            QMessageBox.warning(self, "Uyarı", str(e))
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='shipping',
                screen='VehicleModule',
                function='_delete_vehicle',
                parent_widget=self,
            )

    def _back_to_list(self):
        # Formları temizle
        while self.stack.count() > 1:
            widget = self.stack.widget(1)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        self.stack.setCurrentIndex(0)
