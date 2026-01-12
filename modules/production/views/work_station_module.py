"""
Akıllı İş - İş İstasyonları Modülü
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox

from .work_station_list import WorkStationListPage
from .work_station_form import WorkStationFormPage


class WorkStationModule(QWidget):
    """İş İstasyonları modülü"""

    page_title = "İş İstasyonları"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.station_service = None
        self.warehouse_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # Liste sayfası
        self.list_page = WorkStationListPage()
        self.list_page.new_clicked.connect(self._show_new_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.copy_clicked.connect(self._show_copy_form)
        self.list_page.delete_clicked.connect(self._delete_station)
        self.list_page.refresh_requested.connect(self._load_data)
        self.stack.addWidget(self.list_page)

        layout.addWidget(self.stack)

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_data()

    def _ensure_services(self):
        """Servisleri yükle"""
        if not self.station_service:
            try:
                from modules.production.services import WorkStationService
                from modules.inventory.services import WarehouseService

                self.station_service = WorkStationService()
                self.warehouse_service = WarehouseService()
            except Exception as e:
                print(f"Servis yükleme hatası: {e}")

    def _load_data(self):
        """Verileri yükle"""
        if not self.station_service:
            return

        try:
            stations = self.station_service.get_all(active_only=False)

            station_list = []
            for s in stations:
                station_list.append(
                    {
                        "id": s.id,
                        "code": s.code,
                        "name": s.name,
                        "station_type": (
                            s.station_type.value if s.station_type else "machine"
                        ),
                        "capacity_per_hour": float(s.capacity_per_hour or 0),
                        "efficiency_rate": float(s.efficiency_rate or 100),
                        "hourly_rate": float(s.hourly_rate or 0),
                        "location": s.location,
                        "warehouse_name": s.warehouse.name if s.warehouse else None,
                        "is_active": s.is_active,
                    }
                )

            self.list_page.load_data(station_list)

        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
            self.list_page.load_data([])

    def _show_new_form(self):
        """Yeni istasyon formu göster"""
        self._ensure_services()

        form = WorkStationFormPage()
        form.saved.connect(self._save_station)
        form.cancelled.connect(self._show_list)

        self._load_form_data(form)

        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_edit_form(self, station_id: int):
        """Düzenleme formu göster"""
        self._ensure_services()

        station = self.station_service.get_by_id(station_id)
        if not station:
            QMessageBox.warning(self, "Hata", "İstasyon bulunamadı!")
            return

        station_data = {
            "id": station.id,
            "code": station.code,
            "name": station.name,
            "description": station.description,
            "station_type": (
                station.station_type.value if station.station_type else "machine"
            ),
            "capacity_per_hour": station.capacity_per_hour,
            "efficiency_rate": station.efficiency_rate,
            "working_hours_per_day": station.working_hours_per_day,
            "hourly_rate": station.hourly_rate,
            "setup_cost": station.setup_cost,
            "warehouse_id": station.warehouse_id,
            "location": station.location,
            "is_active": station.is_active,
        }

        form = WorkStationFormPage(station_data)
        form.saved.connect(self._save_station)
        form.cancelled.connect(self._show_list)

        self._load_form_data(form)

        # Depo seçimini ayarla
        if station.warehouse_id:
            for i in range(form.warehouse_combo.count()):
                if form.warehouse_combo.itemData(i) == station.warehouse_id:
                    form.warehouse_combo.setCurrentIndex(i)
                    break

        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_copy_form(self, station_id: int):
        """Kopyalama formu göster"""
        self._ensure_services()

        station = self.station_service.get_by_id(station_id)
        if not station:
            QMessageBox.warning(self, "Hata", "İstasyon bulunamadı!")
            return

        # Mevcut istasyonun verilerini kopyala
        station_data = {
            "code": f"{station.code}_KOPYA",
            "name": f"{station.name} (Kopya)",
            "description": station.description,
            "station_type": (
                station.station_type.value if station.station_type else "machine"
            ),
            "capacity_per_hour": station.capacity_per_hour,
            "efficiency_rate": station.efficiency_rate,
            "working_hours_per_day": station.working_hours_per_day,
            "hourly_rate": station.hourly_rate,
            "setup_cost": station.setup_cost,
            "warehouse_id": station.warehouse_id,
            "location": station.location,
            "is_active": station.is_active,
            "default_operation_name": getattr(station, "default_operation_name", None),
            "default_setup_time": getattr(station, "default_setup_time", None),
            "default_run_time_per_unit": getattr(
                station, "default_run_time_per_unit", None
            ),
        }

        # ID olmadan form aç (yeni kayıt olarak)
        form = WorkStationFormPage(station_data)
        form.saved.connect(self._save_station)
        form.cancelled.connect(self._show_list)

        self._load_form_data(form)

        # Depo seçimini ayarla
        if station.warehouse_id:
            for i in range(form.warehouse_combo.count()):
                if form.warehouse_combo.itemData(i) == station.warehouse_id:
                    form.warehouse_combo.setCurrentIndex(i)
                    break

        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _load_form_data(self, form: WorkStationFormPage):
        """Form verilerini yükle"""
        try:
            warehouses = self.warehouse_service.get_all()
            form.set_warehouses(warehouses)
        except Exception as e:
            print(f"Form veri yükleme hatası: {e}")

    def _save_station(self, data: dict):
        """İstasyonu kaydet"""
        try:
            station_id = data.pop("id", None)

            # station_type'ı enum'a dönüştür
            from database.models.production import WorkStationType

            type_val = data.get("station_type", "machine")
            data["station_type"] = WorkStationType(type_val)

            if station_id:
                self.station_service.update(station_id, **data)
                QMessageBox.information(self, "Başarılı", "İstasyon güncellendi!")
            else:
                self.station_service.create(**data)
                QMessageBox.information(self, "Başarılı", "İstasyon oluşturuldu!")

            self._show_list()
            self._load_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {str(e)}")

    def _delete_station(self, station_id: int):
        """İstasyonu sil"""
        try:
            self.station_service.delete(station_id)
            QMessageBox.information(self, "Başarılı", "İstasyon silindi!")
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")

    def _show_list(self):
        """Liste sayfasına dön"""
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.removeWidget(current)
            current.deleteLater()

        self.stack.setCurrentWidget(self.list_page)
