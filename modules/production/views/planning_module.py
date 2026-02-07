"""
Akıllı İş - Üretim Planlama Modülü
Makine bazlı Gantt chart için veri yönetimi
Takvim entegrasyonu (tatil gösterimi)
"""

from datetime import date, timedelta
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QTabWidget
from PyQt6.QtCore import pyqtSignal

from .planning_page import ProductionPlanningPage

from database.models.production import WorkOrderStatus, WorkOrderOperationStatus


class PlanningModule(QWidget):
    """Üretim Planlama Modülü"""

    page_title = "Üretim Planlama"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.wo_service = None
        self.ws_service = None
        self.holiday_service = None
        self.aps_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()

        # 1. Tab: Gantt Şeması
        self.planning_page = ProductionPlanningPage()
        self.planning_page.refresh_requested.connect(self._load_data)
        self.planning_page.work_order_clicked.connect(self._on_work_order_clicked)
        self.planning_page.operation_moved.connect(self._on_operation_rescheduled)
        self.tabs.addTab(self.planning_page, "📅 Gantt Şeması")

        self.tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self.tabs)

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_data()

    def _ensure_services(self):
        """Servisleri yükle"""
        if not self.wo_service:
            try:
                from modules.production.services import (
                    WorkOrderService,
                    WorkStationService,
                )

                self.wo_service = WorkOrderService()
                self.ws_service = WorkStationService()

            except Exception as e:
                print(f"Servis yükleme hatası: {e}")

        # Tatil servisini yükle
        if not self.holiday_service:
            try:
                from modules.production.calendar_services import HolidayService

                self.holiday_service = HolidayService()
            except Exception as e:
                print(f"Tatil servisi yükleme hatası: {e}")

        # APS servisini yükle
        if not self.aps_service:
            try:
                from modules.aps import APSService

                self.aps_service = APSService()
                self.planning_page.set_aps_service(self.aps_service)
            except Exception as e:
                print(f"APS servisi yükleme hatası: {e}")

    def _load_holidays(self) -> list:
        """Tatilleri yükle"""
        holidays = []

        if not self.holiday_service:
            return holidays

        try:
            # Bu yıl için tatilleri al
            current_year = date.today().year
            start_date = date(current_year, 1, 1)
            end_date = date(current_year, 12, 31)

            holiday_records = self.holiday_service.get_holidays_in_range(
                start_date, end_date
            )

            for h in holiday_records:
                holidays.append(
                    {
                        "date": h.date,
                        "name": h.name,
                        "is_half_day": (
                            h.is_half_day if hasattr(h, "is_half_day") else False
                        ),
                    }
                )

        except Exception as e:
            print(f"Tatil yükleme hatası: {e}")

        return holidays

    def _on_tab_changed(self, index):
        """Sekme değiştiğinde veriyi yenile"""
        if index == 0:
            self._load_data()

    def _load_data(self):
        """Gantt verilerini yükle"""
        # Servislerin yüklü olduğundan emin ol
        self._ensure_services()

        if not self.wo_service or not self.ws_service:
            print("Uyarı: Servisler yüklenemedi, veri yüklenemiyor")
            return

        try:
            # Tatilleri yükle
            holidays = self._load_holidays()

            # İş istasyonlarını yükle
            stations = self.ws_service.get_all(active_only=True)
            work_stations = []
            for ws in stations:
                work_stations.append(
                    {
                        "id": ws.id,
                        "code": ws.code,
                        "name": ws.name,
                        "station_type": (
                            ws.station_type.value if ws.station_type else "machine"
                        ),
                        "capacity_per_hour": float(ws.capacity_per_hour or 0),
                    }
                )

            # İş emirlerini ve operasyonlarını yükle
            work_orders = self.wo_service.get_all()
            operations = []

            for wo in work_orders:
                # Tamamlanan veya kapatılan iş emirlerini Gantt'ta gösterme
                if wo.status in [
                    WorkOrderStatus.COMPLETED,
                    WorkOrderStatus.CLOSED,
                    WorkOrderStatus.CANCELLED,
                ]:
                    continue

                # Sadece planlanan başlangıç/bitiş tarihi olanlar
                if not wo.planned_start or not wo.planned_end:
                    continue

                # Her operasyon için
                if wo.operations:
                    for op in wo.operations:
                        # Tamamlanan operasyonları Gantt'ta gösterme
                        if op.status == WorkOrderOperationStatus.COMPLETED:
                            continue

                        # Operasyon zamanlarını hesapla
                        op_start = op.planned_start or wo.planned_start
                        op_end = op.planned_end or wo.planned_end

                        # Eğer operasyonun kendi zamanı yoksa, iş emri süresini böl
                        if not op.planned_start and not op.planned_end:
                            # Toplam süreyi operasyon sayısına böl (basit yaklaşım)
                            total_ops = len(wo.operations)
                            if total_ops > 0:
                                total_duration = (
                                    wo.planned_end - wo.planned_start
                                ).total_seconds()
                                op_duration = total_duration / total_ops
                                op_index = list(wo.operations).index(op)

                                op_start = wo.planned_start + timedelta(
                                    seconds=op_duration * op_index
                                )
                                op_end = op_start + timedelta(seconds=op_duration)

                        # İlerleme hesapla
                        progress = 0
                        if op.status == WorkOrderOperationStatus.COMPLETED:
                            progress = 100
                        elif op.status == WorkOrderOperationStatus.IN_PROGRESS:
                            progress = 50  # Varsayılan
                            if op.completed_quantity and wo.planned_quantity:
                                progress = float(
                                    op.completed_quantity / wo.planned_quantity * 100
                                )

                        # İş emri durumunu al
                        wo_status = wo.status.value if wo.status else "draft"
                        # Operasyon bazlı WIP takibi için kendi durumunu kullan (yeni)
                        # Ama Gantt renkleri için şimdilik WO durumuna sadık kalmak istenebilir.
                        # Ancak op.status.value daha doğru bir yaklaşım.
                        op_status_val = op.status.value if op.status else wo_status

                        operations.append(
                            {
                                "operation_id": op.id,
                                "work_order_id": wo.id,
                                "order_no": wo.order_no,
                                "item_name": wo.item.name if wo.item else "-",
                                "work_station_id": op.work_station_id,
                                "operation_name": op.name,
                                "start_time": op_start,
                                "end_time": op_end,
                                "status": op_status_val,
                                "progress": progress,
                                "setup_time": op.planned_setup_time or 0,
                                "run_time": op.planned_run_time or 0,
                            }
                        )
                else:
                    # Operasyon yoksa, iş emrini direkt göster
                    # İlk iş istasyonuna ata (veya atanmamış)
                    progress = float(wo.progress_rate or 0)

                    operations.append(
                        {
                            "operation_id": None,
                            "work_order_id": wo.id,
                            "order_no": wo.order_no,
                            "item_name": wo.item.name if wo.item else "-",
                            "work_station_id": None,  # Atanmamış
                            "operation_name": "Üretim",
                            "start_time": wo.planned_start,
                            "end_time": wo.planned_end,
                            "status": wo.status.value,
                            "progress": progress,
                            "setup_time": 0,
                            "run_time": 0,
                        }
                    )

            # Sayfaya verileri gönder (tatillerle birlikte)
            self.planning_page.load_data(work_stations, operations, holidays)

        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
            import traceback

            traceback.print_exc()
            self.planning_page.load_data([], [], [])

    def _on_work_order_clicked(self, wo_id: int):
        """İş emrine tıklandığında"""
        try:
            wo = self.wo_service.get_by_id(wo_id)
            if wo:
                status_map = {
                    "draft": "Taslak",
                    "planned": "Planlandı",
                    "released": "Serbest",
                    "in_progress": "Üretimde",
                    "quality_check": "Kalite Kontrol",
                    "completed": "Tamamlandı",
                    "closed": "Kapatıldı",
                    "cancelled": "İptal Edildi",
                }
                status_text = status_map.get(wo.status.value, wo.status.value)

                # Detay bilgisi göster
                info = f"""
                <b>İş Emri:</b> {wo.order_no}<br/>
                <b>Ürün:</b> {wo.item.name if wo.item else '-'}<br/>
                <b>Miktar:</b> {wo.planned_quantity}<br/>
                <b>Durum:</b> {status_text}<br/>
                <b>Başlangıç:</b> {wo.planned_start.strftime('%d.%m.%Y %H:%M') if wo.planned_start else '-'}<br/>
                <b>Bitiş:</b> {wo.planned_end.strftime('%d.%m.%Y %H:%M') if wo.planned_end else '-'}
                """

                msg = QMessageBox(self)
                msg.setWindowTitle("İş Emri Detayı")
                msg.setTextFormat(Qt.TextFormat.RichText)
                msg.setText(info)
                msg.exec()

        except Exception as e:
            print(f"İş emri detay hatası: {e}")

    def _on_operation_rescheduled(
        self,
        wo_id: int,
        new_start_time: object,
        operation_id: int = None,
        new_machine_id: int = None,
    ):
        """Operasyon taşındığında"""
        if not self.wo_service:
            return

        try:
            # QDateTime -> python datetime dönüşümü (gerekirse)
            start_dt = new_start_time
            if hasattr(new_start_time, "toPython"):
                start_dt = new_start_time.toPython()

            success = self.wo_service.reschedule_operation(
                order_id=wo_id,
                new_start_time=start_dt,
                operation_id=operation_id,
                new_work_station_id=new_machine_id,
            )

            if success:
                # Verileri yenile
                self._load_data()

            else:
                QMessageBox.warning(
                    self, "Hata", "Planlama güncellenemedi veya taşınamaz durumda."
                )
                self._load_data()  # Geri al

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Planlama hatası: {str(e)}")
            self._load_data()  # Geri al
