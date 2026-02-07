from decimal import Decimal
from typing import List, Dict, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.base import get_session
from database.models.production import (
    WorkOrder,
    WorkOrderStatus,
    WorkOrderOperation,
    WorkOrderLine,
    WorkStation,
)
from modules.inventory.services import ServiceBase


class CostAccountingService(ServiceBase):
    """Maliyet Muhasebesi Servisi"""

    def __init__(self):
        super().__init__()
        self.session: Session = get_session()

    def calculate_work_order_cost(self, work_order_id: int) -> Dict:
        """İş emri maliyetini hesapla ve güncelle"""
        work_order = self.session.query(WorkOrder).get(work_order_id)
        if not work_order:
            raise ValueError(f"Work order {work_order_id} not found")

        # 1. Malzeme Maliyeti
        material_cost = Decimal(0)
        for line in work_order.lines:
            qty = line.issued_quantity or Decimal(0)
            cost = line.unit_cost or Decimal(0)  # Assumed set during issuance
            line.line_cost = qty * cost
            material_cost += line.line_cost

        # 2. İşçilik ve Genel Gider (Operasyon bazlı)
        labor_cost = Decimal(0)
        overhead_cost = Decimal(0)

        for op in work_order.operations:
            duration_hours = Decimal(op.actual_run_time or 0) / Decimal(60)
            setup_hours = Decimal(op.actual_setup_time or 0) / Decimal(60)
            total_hours = duration_hours + setup_hours

            if op.work_station:
                rate = op.work_station.hourly_rate or Decimal(0)
                overhead_rate = op.work_station.overhead_rate or Decimal(0)

                op_labor = total_hours * rate
                op_overhead = total_hours * overhead_rate

                # Update op costs if needed (fields might accept manual override, here we calc)
                # BOMOperation has labor_cost field, WorkOrderOperation not explicitly separate but we can store totals

                labor_cost += op_labor
                overhead_cost += op_overhead

        # Update Work Order
        work_order.actual_material_cost = material_cost
        work_order.actual_labor_cost = labor_cost
        work_order.actual_overhead_cost = overhead_cost

        self.session.commit()

        total_cost = material_cost + labor_cost + overhead_cost
        unit_cost = Decimal(0)
        if work_order.completed_quantity and work_order.completed_quantity > 0:
            unit_cost = total_cost / work_order.completed_quantity

        return {
            "work_order_id": work_order.id,
            "order_no": work_order.order_no,
            "material_cost": float(material_cost),
            "labor_cost": float(labor_cost),
            "overhead_cost": float(overhead_cost),
            "total_cost": float(total_cost),
            "unit_cost": float(unit_cost),
            "completed_quantity": float(work_order.completed_quantity or 0),
        }

    def get_production_costs(self, start_date=None, end_date=None) -> List[Dict]:
        """Tarih aralığındaki üretim maliyetleri"""
        query = self.session.query(WorkOrder).filter(
            WorkOrder.status.in_([WorkOrderStatus.COMPLETED, WorkOrderStatus.CLOSED])
        )

        if start_date:
            query = query.filter(WorkOrder.actual_end >= start_date)
        if end_date:
            query = query.filter(WorkOrder.actual_end <= end_date)

        results = []
        for wo in query.all():
            cost = self.calculate_work_order_cost(wo.id)
            results.append(cost)

        return results

    def close(self):
        if self.session:
            self.session.close()
