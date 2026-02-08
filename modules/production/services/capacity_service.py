"""
Akıllı İş - APS Kapasite Analiz Servisi
"""

from datetime import date, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models.production import WorkStation
from database.models.aps import PlannedTask


class CapacityService:
    """
    İş istasyonları ve kaynaklar için kapasite analizi yapar.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_resource_load(
        self, scenario_id: int, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Belirtilen senaryo ve tarih aralığı için tüm yük durumunu döner.
        """
        stations = self.db.query(WorkStation).all()
        results = []

        for station in stations:
            load_data = self.get_station_load(
                station.id, scenario_id, start_date, end_date
            )
            results.append(
                {
                    "station_id": station.id,
                    "station_name": station.name,
                    "load": load_data,
                }
            )

        return results

    def get_station_load(
        self, station_id: int, scenario_id: int, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Belirli bir istasyonun gün bazlı doluluk oranlarını hesaplar.
        """
        station = self.db.query(WorkStation).get(station_id)
        if not station:
            return []

        daily_loads = []
        curr_d = start_date

        while curr_d <= end_date:
            # O gün için planlanmış görevlerin toplam süresi
            total_m = (
                self.db.query(func.sum(PlannedTask.setup_time + PlannedTask.run_time))
                .filter(
                    PlannedTask.scenario_id == scenario_id,
                    PlannedTask.work_station_id == station_id,
                    func.date(PlannedTask.planned_start) == curr_d,
                )
                .scalar()
            ) or 0

            # İstasyon kapasitesini al
            cap = float(station.daily_capacity_minutes or 480)
            util = (float(total_m) / cap * 100) if cap > 0 else 0

            daily_loads.append(
                {
                    "date": curr_d.strftime("%Y-%m-%d"),
                    "used_minutes": float(total_m),
                    "capacity_minutes": cap,
                    "utilization_rate": round(util, 2),
                }
            )
            curr_d += timedelta(days=1)

        return daily_loads
