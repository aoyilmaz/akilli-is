"""
Akıllı İş - APS (İleri Planlama & Çizelgeleme) Çizelgeleme Motoru
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import case
from database.models.production import (
    WorkOrder,
    WorkOrderOperation,
    WorkOrderStatus,
    WorkOrderPriority,
)
from database.models.aps import APSScenario, PlannedTask


class SchedulerService:
    """
    Üretim planlama ve çizelgeleme motoru.
    """

    def __init__(self, db: Session):
        self.db = db

    def schedule_scenario(self, scenario_id: int):
        """
        Belirli bir senaryo için tüm bekleyen iş emirlerini çizelgeler.
        """
        scenario = self.db.query(APSScenario).get(scenario_id)
        if not scenario:
            raise ValueError(f"Senaryo ID {scenario_id} bulunamadı")

        # 1. Mevcut kilitlenmemiş planları temizle
        self.db.query(PlannedTask).filter(
            PlannedTask.scenario_id == scenario_id, PlannedTask.is_locked == False
        ).delete()

        # 2. Bekleyen iş emirlerini sırala
        target_statuses = [
            WorkOrderStatus.DRAFT,
            WorkOrderStatus.PLANNED,
            WorkOrderStatus.RELEASED,
        ]

        # Öncelik ağırlıklarını belirle (Enum'ların DB'deki sırasına güvenmek yerine)
        priority_weight = case(
            (WorkOrder.priority == WorkOrderPriority.URGENT, 4),
            (WorkOrder.priority == WorkOrderPriority.HIGH, 3),
            (WorkOrder.priority == WorkOrderPriority.NORMAL, 2),
            (WorkOrder.priority == WorkOrderPriority.LOW, 1),
            else_=0,
        )

        orders = (
            self.db.query(WorkOrder)
            .filter(WorkOrder.status.in_(target_statuses))
            .order_by(priority_weight.desc(), WorkOrder.planned_end.asc())
            .all()
        )

        curr_time = scenario.start_date or datetime.now()

        # 3. Her iş emri için operasyonları yerleştir
        for wo in orders:
            self._schedule_work_order(wo, scenario_id, curr_time)

        self.db.commit()

    def _schedule_work_order(
        self, wo: WorkOrder, scenario_id: int, start_horizon: datetime
    ):
        """
        Operasyonları ardışık olarak yerleştirir.
        """
        operations = (
            self.db.query(WorkOrderOperation)
            .filter(WorkOrderOperation.work_order_id == wo.id)
            .order_by(WorkOrderOperation.operation_no.asc())
            .all()
        )

        last_op_end = start_horizon

        for op in operations:
            planned_task = self._find_first_available_slot(op, scenario_id, last_op_end)

            if planned_task:
                self.db.add(planned_task)
                # Flush yaparak verinin identity map ve sonraki sorgularda
                # görünmesini sağla
                self.db.flush()
                last_op_end = planned_task.planned_end

    def _find_first_available_slot(
        self, op: WorkOrderOperation, scenario_id: int, earliest_start: datetime
    ):
        """
        İstasyonun uygun olduğu en erken zaman dilimini bulur.
        """
        if not op.work_station_id:
            return None

        # İstasyonun son görevini bul
        last_task = (
            self.db.query(PlannedTask)
            .filter(
                PlannedTask.scenario_id == scenario_id,
                PlannedTask.work_station_id == op.work_station_id,
            )
            .order_by(PlannedTask.planned_end.desc())
            .first()
        )

        actual_start = earliest_start
        if last_task and last_task.planned_end > actual_start:
            actual_start = last_task.planned_end

        # Süreyi hesapla
        setup_t = op.planned_setup_time or 0
        run_t = op.planned_run_time or 0
        total_d = setup_t + run_t

        planned_end = actual_start + timedelta(minutes=total_d)

        return PlannedTask(
            scenario_id=scenario_id,
            work_order_id=op.work_order_id,
            operation_id=op.id,
            work_station_id=op.work_station_id,
            planned_start=actual_start,
            planned_end=planned_end,
            setup_time=setup_t,
            run_time=run_t,
            priority=1,
        )

    def confirm_scenario(self, scenario_id: int):
        """
        Onaylanan senaryoyu üretim takvimine aktarır.
        """
        tasks = (
            self.db.query(PlannedTask)
            .filter(PlannedTask.scenario_id == scenario_id)
            .all()
        )

        for task in tasks:
            op = task.operation
            if op:
                op.planned_start = task.planned_start
                op.planned_end = task.planned_end
                op.work_station_id = task.work_station_id
                op.status = "planned"

                if op.work_order and op.work_order.status != "in_progress":
                    op.work_order.status = "planned"

        self.db.commit()
