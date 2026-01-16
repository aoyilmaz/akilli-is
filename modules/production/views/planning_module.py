"""
Akıllı İş - Üretim Planlama Modülü
Makine bazlı Gantt chart için veri yönetimi
Takvim entegrasyonu (tatil gösterimi)
"""

from datetime import date, timedelta
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt6.QtCore import pyqtSignal

from .planning_page import ProductionPlanningPage
from database.models.production import WorkOrderStatus


class PlanningModule(QWidget):
    """Üretim Planlama Modülü"""

    page_title = "Üretim Planlama"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.wo_service = None
        self.ws_service = None
        self.holiday_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.planning_page = ProductionPlanningPage()
        self.planning_page.refresh_requested.connect(self._load_data)
        self.planning_page.work_order_clicked.connect(self._on_work_order_clicked)

        layout.addWidget(self.planning_page)

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

    def _load_data(self):
        """Verileri yükle"""
        if not self.wo_service or not self.ws_service:
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
                if wo.status in [WorkOrderStatus.COMPLETED, WorkOrderStatus.CLOSED]:
                    continue

                # Sadece planlanan başlangıç/bitiş tarihi olanlar
                if not wo.planned_start or not wo.planned_end:
                    continue

                # Her operasyon için
                if wo.operations:
                    for op in wo.operations:
                        # Tamamlanan operasyonları Gantt'ta gösterme
                        if op.status == "completed":
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
                        if op.status == "completed":
                            progress = 100
                        elif op.status == "in_progress":
                            progress = 50  # Varsayılan
                            if op.completed_quantity and wo.planned_quantity:
                                progress = float(
                                    op.completed_quantity / wo.planned_quantity * 100
                                )

                        # İş emri durumunu al
                        wo_status = wo.status.value if wo.status else "draft"
                        op_status = wo_status  # İş emri durumunu kullan

                        operations.append(
                            {
                                "work_order_id": wo.id,
                                "order_no": wo.order_no,
                                "item_name": wo.item.name if wo.item else "-",
                                "work_station_id": op.work_station_id,
                                "operation_name": op.name,
                                "start_time": op_start,
                                "end_time": op_end,
                                "status": op_status,
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
                # Detay bilgisi göster
                info = f"""
                <b>İş Emri:</b> {wo.order_no}<br/>
                <b>Ürün:</b> {wo.item.name if wo.item else '-'}<br/>
                <b>Miktar:</b> {wo.planned_quantity}<br/>
                <b>Durum:</b> {wo.status.value}<br/>
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
