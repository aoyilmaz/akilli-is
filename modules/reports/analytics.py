from datetime import date, datetime, timedelta
from typing import Dict, Any, List
from decimal import Decimal
from sqlalchemy import func

from database.base import get_session
from database.models.production import WorkOrder, WorkOrderStatus, WorkOrderOperation
from modules.reports.services import ReportsService


class AnalyticsService:
    """Dashboard ve analitik verileri için servis"""

    def __init__(self):
        self.session = get_session()
        self.reports_service = ReportsService()

    def close(self):
        if self.session:
            self.session.close()
        if self.reports_service:
            self.reports_service.close()

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Dashboard için özet istatistikleri getir"""
        today = date.today()
        start_date = today - timedelta(days=7)

        # 1. OEE Skoru (ReportsService'den)
        oee_data = self.reports_service.get_production_oee(start_date, today)
        oee_score = oee_data.get("oee", 0)

        # 2. Aktif Siparişler
        active_orders_count = (
            self.session.query(WorkOrder)
            .filter(
                WorkOrder.status.in_(
                    [WorkOrderStatus.RELEASED, WorkOrderStatus.IN_PROGRESS]
                ),
                WorkOrder.is_active == True,
            )
            .count()
        )

        # 3. Haftalık Üretim Hacmi (Son 7 Gün)
        weekly_volume = (
            self.session.query(func.sum(WorkOrder.completed_quantity))
            .filter(
                WorkOrder.actual_end >= start_date,
                WorkOrder.status.in_(
                    [WorkOrderStatus.COMPLETED, WorkOrderStatus.CLOSED]
                ),
                WorkOrder.is_active == True,
            )
            .scalar()
            or 0
        )

        # 4. Maliyet Etkinliği (Tamamlanan siparişlerin ortalama sapması)
        # Variance % = (Actual - Planned) / Planned * 100
        # Negatif varyans iyidir (Planlanandan az maliyet)
        completed_orders = (
            self.session.query(WorkOrder)
            .filter(
                WorkOrder.status.in_(
                    [WorkOrderStatus.COMPLETED, WorkOrderStatus.CLOSED]
                ),
                WorkOrder.is_active == True,
                WorkOrder.planned_material_cost > 0,  # Sıfıra bölünmeyi önle
            )
            .order_by(WorkOrder.actual_end.desc())
            .limit(50)
            .all()
        )

        total_variance_pct = 0
        count = 0

        variance_trend = []

        for order in completed_orders:
            planned = (
                (order.planned_material_cost or 0)
                + (order.planned_labor_cost or 0)
                + (order.planned_overhead_cost or 0)
            )
            actual = (
                (order.actual_material_cost or 0)
                + (order.actual_labor_cost or 0)
                + (order.actual_overhead_cost or 0)
            )

            if planned > 0:
                variance = actual - planned
                pct = (variance / planned) * 100
                total_variance_pct += pct
                count += 1

                variance_trend.append(
                    {
                        "order_no": order.order_no,
                        "variance_pct": float(pct),
                        "date": (
                            order.actual_end.strftime("%d.%m")
                            if order.actual_end
                            else ""
                        ),
                    }
                )

        avg_cost_efficiency = (total_variance_pct / count) if count > 0 else 0

        # 5. Günlük Üretim Trendi (Son 7 Gün)
        production_trend = []
        for i in range(7):
            day = start_date + timedelta(days=i)
            next_day = day + timedelta(days=1)

            # O gün tamamlanan veya operasyonu bitenler...
            # Basitlik için WorkOrder.actual_end kullanıyoruz
            qty = (
                self.session.query(func.sum(WorkOrder.completed_quantity))
                .filter(
                    WorkOrder.actual_end >= day,
                    WorkOrder.actual_end < next_day,
                    WorkOrder.status.in_(
                        [WorkOrderStatus.COMPLETED, WorkOrderStatus.CLOSED]
                    ),
                )
                .scalar()
                or 0
            )

            production_trend.append(
                {"date": day.strftime("%d.%m"), "quantity": float(qty)}
            )

        return {
            "oee_score": oee_score,
            "active_orders": active_orders_count,
            "weekly_volume": float(weekly_volume),
            "cost_efficiency": float(avg_cost_efficiency),
            "production_trend": production_trend,
            "cost_trend": variance_trend[:10],  # Son 10 sipariş
        }
