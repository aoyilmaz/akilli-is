"""
Akıllı İş - Sürücü Modülü
"""

from datetime import date
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox

from .driver_list import DriverListPage
from .driver_form import DriverFormPage
from modules.development import ErrorHandler


class DriverModule(QWidget):
    """Sürücü yönetimi modülü"""

    page_title = "Sürücüler"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.vehicle_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # Liste sayfası
        self.list_page = DriverListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_driver)
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
                from modules.shipping.services import DriverService, VehicleService
                self.service = DriverService()
                self.vehicle_service = VehicleService()
            except Exception as e:
                ErrorHandler.handle_error(
                    e,
                    module='shipping',
                    screen='DriverModule',
                    function='_ensure_service',
                    parent_widget=self,
                    show_message=False
                )

    def _load_data(self):
        if not self.service:
            return

        try:
            drivers = self.service.get_all(active_only=False)
            data = []
            for d in drivers:
                data.append({
                    "id": d.id,
                    "code": d.code,
                    "name": d.name,
                    "tc_no": d.tc_no,
                    "phone": d.phone,
                    "license_type": d.license_type,
                    "license_expiry": d.license_expiry.strftime("%d.%m.%Y") if d.license_expiry else "",
                    "src_no": d.src_no,
                    "src_expiry": d.src_expiry.strftime("%d.%m.%Y") if d.src_expiry else "",
                    "default_vehicle": d.default_vehicle.plate_no if d.default_vehicle else "",
                    "default_vehicle_id": d.default_vehicle_id,
                    "status": d.status.value if d.status else "",
                    "status_display": d.status_display,
                    "is_license_expiring": d.is_license_expiring,
                    "is_src_expiring": d.is_src_expiring,
                    "notes": d.notes,
                })
            self.list_page.load_data(data)
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='shipping',
                screen='DriverModule',
                function='_load_data',
                parent_widget=self,
                show_message=False
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
                    "display_name": v.display_name,
                }
                for v in vehicles
            ]
        except:
            return []

    def _show_add_form(self):
        vehicles = self._get_vehicles_for_combo()
        form = DriverFormPage(vehicles=vehicles)
        form.saved.connect(self._save_driver)
        form.cancelled.connect(self._back_to_list)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_edit_form(self, driver_id: int):
        if not self.service:
            return

        try:
            driver = self.service.get_by_id(driver_id)
            if not driver:
                QMessageBox.warning(self, "Uyarı", "Sürücü bulunamadı.")
                return

            driver_data = {
                "id": driver.id,
                "code": driver.code,
                "name": driver.name,
                "tc_no": driver.tc_no,
                "phone": driver.phone,
                "license_type": driver.license_type,
                "license_expiry": driver.license_expiry.strftime("%Y-%m-%d") if driver.license_expiry else None,
                "src_no": driver.src_no,
                "src_expiry": driver.src_expiry.strftime("%Y-%m-%d") if driver.src_expiry else None,
                "default_vehicle_id": driver.default_vehicle_id,
                "status": driver.status.value if driver.status else "musait",
                "notes": driver.notes,
            }

            vehicles = self._get_vehicles_for_combo()
            form = DriverFormPage(driver_data, vehicles=vehicles)
            form.saved.connect(self._save_driver)
            form.cancelled.connect(self._back_to_list)
            self.stack.addWidget(form)
            self.stack.setCurrentWidget(form)
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='shipping',
                screen='DriverModule',
                function='_show_edit_form',
                parent_widget=self,
            )

    def _show_view(self, driver_id: int):
        self._show_edit_form(driver_id)

    def _save_driver(self, data: dict):
        if not self.service:
            return

        try:
            driver_id = data.pop("id", None)
            code = data.pop("code", None)

            # Enum ve tarih dönüşümleri
            from database.models.shipping import DriverStatus
            from datetime import datetime

            if "status" in data:
                data["status"] = DriverStatus(data["status"])

            # Tarih alanlarını dönüştür
            for date_field in ["license_expiry", "src_expiry"]:
                if data.get(date_field):
                    data[date_field] = datetime.strptime(data[date_field], "%Y-%m-%d").date()

            if driver_id:
                self.service.update(driver_id, **data)
                QMessageBox.information(self, "Başarılı", "Sürücü güncellendi.")
            else:
                self.service.create(**data)
                QMessageBox.information(self, "Başarılı", "Sürücü oluşturuldu.")

            self._back_to_list()
            self._load_data()
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='shipping',
                screen='DriverModule',
                function='_save_driver',
                parent_widget=self,
            )

    def _delete_driver(self, driver_id: int):
        if not self.service:
            return

        reply = QMessageBox.question(
            self,
            "Onay",
            "Bu sürücüyü silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.service.delete(driver_id)
            QMessageBox.information(self, "Başarılı", "Sürücü silindi.")
            self._load_data()
        except ValueError as e:
            QMessageBox.warning(self, "Uyarı", str(e))
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='shipping',
                screen='DriverModule',
                function='_delete_driver',
                parent_widget=self,
            )

    def _back_to_list(self):
        while self.stack.count() > 1:
            widget = self.stack.widget(1)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        self.stack.setCurrentIndex(0)
