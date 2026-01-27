"""
Akıllı İş - MPS (Master Production Scheduling) Servisi

Ana Üretim Planlama servisi. SAP PP/IBP standartlarına yakın
backward scheduling ve önceliklendirme algoritmaları içerir.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
import uuid

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session, joinedload

from database.base import get_session
from database.models.production import (
    ProductionPlan,
    ProductionPlanLine,
    ProductionPlanStatus,
    BillOfMaterials,
    BOMLine,
    BOMOperation,
    BOMStatus,
    WorkOrder,
    WorkOrderLine,
    WorkOrderOperation,
    WorkOrderStatus,
    WorkStation,
)
from database.models.inventory import Item, StockBalance
from database.models.sales import (
    SalesOrder,
    SalesOrderItem,
    SalesOrderStatus,
    Customer,
)
from database.models.calendar import ProductionHoliday
from modules.production.services.base import WorkOrderService


class MPSError(Exception):
    """MPS hatası base class"""
    pass


class MPSService:
    """
    Master Production Scheduling (MPS) Servisi

    Ana Üretim Planlaması:
    - Satış siparişlerinden plan oluşturma
    - Backward scheduling (geriye doğru çizelgeleme)
    - Önceliklendirme (müşteri skoru + gecikme riski)
    - İş emirlerine dönüştürme (release)
    """

    def __init__(self):
        self.session: Session = get_session()
        self._holidays_cache: Dict[date, bool] = {}

    def close(self):
        if self.session:
            self.session.close()

    # =========================================
    # PLAN OLUŞTURMA
    # =========================================

    def generate_plan_no(self) -> str:
        """Yeni plan numarası oluştur: MPS-YYYYMM-XXX"""
        prefix = f"MPS-{datetime.now().strftime('%Y%m')}"

        last = (
            self.session.query(ProductionPlan)
            .filter(ProductionPlan.plan_no.like(f"{prefix}%"))
            .order_by(ProductionPlan.plan_no.desc())
            .first()
        )

        seq = 1
        if last and last.plan_no:
            try:
                seq = int(last.plan_no.split("-")[-1]) + 1
            except ValueError:
                pass

        return f"{prefix}-{seq:03d}"

    def create_plan(
        self,
        period_start: date,
        period_end: date,
        name: str = None,
        description: str = None,
    ) -> ProductionPlan:
        """
        Yeni üretim planı oluştur.

        Args:
            period_start: Planlama dönemi başlangıcı
            period_end: Planlama dönemi bitişi
            name: Plan adı (opsiyonel)
            description: Açıklama (opsiyonel)

        Returns:
            Oluşturulan ProductionPlan
        """
        plan_no = self.generate_plan_no()

        if not name:
            name = f"Üretim Planı {period_start.strftime('%d.%m.%Y')} - {period_end.strftime('%d.%m.%Y')}"

        plan = ProductionPlan(
            plan_no=plan_no,
            name=name,
            description=description,
            period_start=period_start,
            period_end=period_end,
            status=ProductionPlanStatus.DRAFT,
        )

        self.session.add(plan)
        self.session.commit()

        return plan

    def generate_from_sales_orders(
        self,
        period_start: date,
        period_end: date,
        customer_weight: float = 0.5,
        delay_weight: float = 0.5,
        only_confirmed: bool = True,
    ) -> ProductionPlan:
        """
        Satış siparişlerinden otomatik üretim planı oluştur.

        Args:
            period_start: Planlama dönemi başlangıcı
            period_end: Planlama dönemi bitişi
            customer_weight: Müşteri skoru ağırlığı (0-1)
            delay_weight: Gecikme riski ağırlığı (0-1)
            only_confirmed: Sadece onaylı siparişleri dahil et

        Returns:
            Oluşturulan ProductionPlan
        """
        # Plan oluştur
        plan = self.create_plan(
            period_start=period_start,
            period_end=period_end,
            name=f"Siparişlerden Oluşturulan Plan {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        )

        # Siparişleri çek
        query = (
            self.session.query(SalesOrderItem)
            .join(SalesOrder)
            .join(Item, SalesOrderItem.item_id == Item.id)
            .options(
                joinedload(SalesOrderItem.sales_order).joinedload(SalesOrder.customer),
                joinedload(SalesOrderItem.item),
            )
            .filter(
                SalesOrder.is_active.is_(True),
                SalesOrderItem.is_active.is_(True),
                # Teslim tarihi dönem içinde
                or_(
                    SalesOrder.delivery_date.between(period_start, period_end),
                    SalesOrder.requested_delivery_date.between(period_start, period_end),
                ),
                # Üretim gerektiren ürünler (mamül veya yarı mamül)
                Item.item_type.in_(["manufactured", "semi_finished"]),
            )
        )

        if only_confirmed:
            query = query.filter(
                SalesOrder.status.in_([
                    SalesOrderStatus.CONFIRMED,
                    SalesOrderStatus.IN_PRODUCTION,
                ])
            )

        order_items = query.all()

        # Plan satırları oluştur
        for oi in order_items:
            so = oi.sales_order
            item = oi.item

            # Talep tarihi: delivery_date veya requested_delivery_date
            demand_date = so.delivery_date or so.requested_delivery_date or period_end

            # Öncelik hesapla
            priority = self.calculate_priority(
                sales_order=so,
                item_id=item.id,
                demand_date=demand_date,
                customer_weight=customer_weight,
                delay_weight=delay_weight,
            )

            # Kalan miktar hesapla (sevk edilmemiş)
            remaining = (oi.quantity or Decimal(0)) - (oi.delivered_quantity or Decimal(0))

            if remaining <= 0:
                continue

            line = ProductionPlanLine(
                plan_id=plan.id,
                item_id=item.id,
                sales_order_id=so.id,
                sales_order_line_id=oi.id,
                demand_quantity=remaining,
                planned_quantity=remaining,
                demand_date=demand_date,
                priority_score=priority,
            )

            self.session.add(line)

        self.session.commit()

        return plan

    # =========================================
    # ÖNCELİKLENDİRME
    # =========================================

    def calculate_priority(
        self,
        sales_order: SalesOrder,
        item_id: int,
        demand_date: date,
        customer_weight: float = 0.5,
        delay_weight: float = 0.5,
    ) -> Decimal:
        """
        Öncelik skoru hesapla (0-100).

        Formül: priority = (customer_score * customer_weight) + (delay_risk * delay_weight)

        Args:
            sales_order: Satış siparişi
            item_id: Ürün ID
            demand_date: Talep tarihi
            customer_weight: Müşteri skoru ağırlığı
            delay_weight: Gecikme riski ağırlığı

        Returns:
            Öncelik skoru (Decimal, 0-100)
        """
        # 1. Müşteri Skoru (0-100)
        customer_score = 50  # Varsayılan
        if sales_order.customer:
            rating = sales_order.customer.rating or 0
            customer_score = min(100, max(0, rating))

        # 2. Gecikme Riski (0-100)
        # Lead time al
        lead_time_days = self._get_lead_time(item_id)

        days_until_delivery = (demand_date - date.today()).days

        if days_until_delivery <= 0:
            # Zaten geçmiş, maksimum risk
            delay_risk = 100
        elif days_until_delivery < lead_time_days:
            # Lead time'dan az kaldı, yüksek risk
            delay_risk = 80 + (20 * (1 - days_until_delivery / lead_time_days))
        else:
            # Yeterli zaman var
            buffer_ratio = days_until_delivery / lead_time_days
            delay_risk = max(0, 50 - (buffer_ratio - 1) * 10)

        # 3. Ağırlıklı toplam
        priority = (
            Decimal(str(customer_score)) * Decimal(str(customer_weight))
            + Decimal(str(delay_risk)) * Decimal(str(delay_weight))
        )

        return min(Decimal("100"), max(Decimal("0"), priority))

    def _get_lead_time(self, item_id: int) -> int:
        """Ürün için lead time (gün) döndür."""
        # Aktif BOM'dan al
        bom = (
            self.session.query(BillOfMaterials)
            .filter(
                BillOfMaterials.item_id == item_id,
                BillOfMaterials.status == BOMStatus.ACTIVE,
                BillOfMaterials.is_active.is_(True),
            )
            .first()
        )

        if bom and bom.lead_time:
            return int(bom.lead_time)

        return 7  # Varsayılan 7 gün

    # =========================================
    # BACKWARD SCHEDULING
    # =========================================

    def backward_schedule(
        self,
        line: ProductionPlanLine,
        check_capacity: bool = False,
    ) -> ProductionPlanLine:
        """
        Geriye doğru çizelgeleme: Talep tarihinden lead time kadar geriye git.

        Args:
            line: Plan satırı
            check_capacity: Kapasite kontrolü yap (True ise kapasiteye göre öteleme)

        Returns:
            Güncellenen plan satırı
        """
        item = self.session.query(Item).get(line.item_id)
        if not item:
            raise MPSError(f"Ürün bulunamadı: {line.item_id}")

        # BOM ve operasyonları al
        bom = (
            self.session.query(BillOfMaterials)
            .options(joinedload(BillOfMaterials.operations))
            .filter(
                BillOfMaterials.item_id == item.id,
                BillOfMaterials.status == BOMStatus.ACTIVE,
                BillOfMaterials.is_active.is_(True),
            )
            .first()
        )

        # Toplam üretim süresini hesapla
        total_minutes = 0

        if bom and bom.operations:
            for op in bom.operations:
                setup = op.setup_time or 0
                run_per_unit = float(op.run_time_per_unit or 0)
                run_total = run_per_unit * float(line.planned_quantity)
                total_minutes += setup + run_total
        elif bom and bom.lead_time:
            # Operasyon yoksa lead time'ı dakikaya çevir (8 saat/gün)
            total_minutes = int(bom.lead_time) * 8 * 60
        else:
            # Varsayılan: 1 gün
            total_minutes = 8 * 60

        # İş günlerini hesapla
        production_days = max(1, total_minutes // (8 * 60) + (1 if total_minutes % (8 * 60) > 0 else 0))

        # Tatilleri dikkate alarak geriye say
        planned_end = datetime.combine(line.demand_date, datetime.max.time().replace(microsecond=0))
        planned_start = self._subtract_working_days(line.demand_date, production_days)

        # Kapasite kontrolü
        if check_capacity and bom and bom.operations:
            adjusted_start = self._check_and_adjust_for_capacity(
                bom.operations,
                planned_start,
                float(line.planned_quantity),
            )
            if adjusted_start != planned_start:
                planned_start = adjusted_start
                # End date'i de güncelle
                planned_end = datetime.combine(
                    self._add_working_days(planned_start, production_days),
                    datetime.max.time().replace(microsecond=0)
                )

        line.planned_start = datetime.combine(planned_start, datetime.min.time().replace(hour=8))
        line.planned_end = planned_end

        self.session.commit()

        return line

    def backward_schedule_all(
        self,
        plan_id: int,
        check_capacity: bool = False,
    ) -> ProductionPlan:
        """
        Plandaki tüm satırları öncelik sırasına göre backward schedule et.

        Args:
            plan_id: Plan ID
            check_capacity: Kapasite kontrolü yap

        Returns:
            Güncellenen plan
        """
        plan = self.get_by_id(plan_id)
        if not plan:
            raise MPSError(f"Plan bulunamadı: {plan_id}")

        # Öncelik sırasına göre sırala (yüksek öncelik önce)
        lines = sorted(plan.lines, key=lambda x: x.priority_score or 0, reverse=True)

        for line in lines:
            self.backward_schedule(line, check_capacity=check_capacity)

        return plan

    def _subtract_working_days(self, from_date: date, days: int) -> date:
        """Tatilleri atlayarak geriye doğru iş günü say."""
        current = from_date
        remaining = days

        while remaining > 0:
            current = current - timedelta(days=1)
            if not self._is_holiday(current) and current.weekday() < 5:
                remaining -= 1

        return current

    def _add_working_days(self, from_date: date, days: int) -> date:
        """Tatilleri atlayarak ileriye doğru iş günü say."""
        current = from_date
        remaining = days

        while remaining > 0:
            current = current + timedelta(days=1)
            if not self._is_holiday(current) and current.weekday() < 5:
                remaining -= 1

        return current

    def _is_holiday(self, check_date: date) -> bool:
        """Tatil mi kontrol et."""
        if check_date in self._holidays_cache:
            return self._holidays_cache[check_date]

        holiday = (
            self.session.query(ProductionHoliday)
            .filter(
                ProductionHoliday.holiday_date == check_date,
                ProductionHoliday.is_active.is_(True),
            )
            .first()
        )

        is_holiday = holiday is not None
        self._holidays_cache[check_date] = is_holiday

        return is_holiday

    def _check_and_adjust_for_capacity(
        self,
        operations: List[BOMOperation],
        start_date: date,
        quantity: float,
    ) -> date:
        """
        Kapasite kontrolü yap ve gerekirse başlangıç tarihini öne al.

        Returns:
            Ayarlanan başlangıç tarihi
        """
        adjusted_date = start_date

        for op in operations:
            if not op.work_station_id:
                continue

            station = self.session.query(WorkStation).get(op.work_station_id)
            if not station:
                continue

            # Operasyon süresi
            setup = op.setup_time or 0
            run_total = (op.run_time_per_unit or 0) * Decimal(str(quantity))
            op_minutes = int(setup + float(run_total))

            # Kalan kapasite
            remaining = station.get_remaining_capacity(adjusted_date, self.session)

            if remaining < op_minutes:
                # Kapasite yetersiz, bir önceki güne kaydır
                adjusted_date = self._subtract_working_days(adjusted_date, 1)

        return adjusted_date

    # =========================================
    # RELEASE (İŞ EMİRLERİNE DÖNÜŞTÜRME)
    # =========================================

    def release_plan(self, plan_id: int) -> List[WorkOrder]:
        """
        Planı iş emirlerine dönüştür.

        Args:
            plan_id: Plan ID

        Returns:
            Oluşturulan iş emirleri listesi
        """
        plan = self.get_by_id(plan_id)
        if not plan:
            raise MPSError(f"Plan bulunamadı: {plan_id}")

        if plan.status != ProductionPlanStatus.APPROVED:
            raise MPSError(f"Plan onaylı değil: {plan.status.value}")

        wo_service = WorkOrderService()
        work_orders = []

        try:
            for line in plan.lines:
                if line.work_order_id:
                    # Zaten iş emri oluşturulmuş
                    continue

                if not line.planned_start or not line.planned_end:
                    # Henüz çizelgelenmemiş
                    continue

                # Aktif BOM bul
                bom = (
                    self.session.query(BillOfMaterials)
                    .filter(
                        BillOfMaterials.item_id == line.item_id,
                        BillOfMaterials.status == BOMStatus.ACTIVE,
                        BillOfMaterials.is_active.is_(True),
                    )
                    .first()
                )

                if not bom:
                    continue  # BOM yoksa atla

                # İş emri oluştur
                wo = wo_service.create(
                    item_id=line.item_id,
                    bom_id=bom.id,
                    planned_quantity=line.planned_quantity,
                    planned_start=line.planned_start,
                    planned_end=line.planned_end,
                    status=WorkOrderStatus.PLANNED,
                    sales_order_id=line.sales_order_id,
                )

                line.work_order_id = wo.id
                work_orders.append(wo)

            # Plan durumunu güncelle
            plan.status = ProductionPlanStatus.RELEASED

            self.session.commit()

        finally:
            wo_service.close()

        return work_orders

    def approve_plan(self, plan_id: int, user_id: int) -> ProductionPlan:
        """
        Planı onayla.

        Args:
            plan_id: Plan ID
            user_id: Onaylayan kullanıcı ID

        Returns:
            Güncellenen plan
        """
        plan = self.get_by_id(plan_id)
        if not plan:
            raise MPSError(f"Plan bulunamadı: {plan_id}")

        if plan.status != ProductionPlanStatus.DRAFT:
            raise MPSError(f"Sadece taslak planlar onaylanabilir: {plan.status.value}")

        plan.status = ProductionPlanStatus.APPROVED
        plan.approved_by = user_id
        plan.approved_at = datetime.now()

        self.session.commit()

        return plan

    # =========================================
    # SORGULAR
    # =========================================

    def get_by_id(self, plan_id: int) -> Optional[ProductionPlan]:
        """ID ile plan getir."""
        return (
            self.session.query(ProductionPlan)
            .options(
                joinedload(ProductionPlan.lines).joinedload(ProductionPlanLine.item),
                joinedload(ProductionPlan.lines).joinedload(ProductionPlanLine.sales_order),
            )
            .filter(ProductionPlan.id == plan_id)
            .first()
        )

    def get_all(
        self,
        status: ProductionPlanStatus = None,
        period_start: date = None,
        period_end: date = None,
    ) -> List[ProductionPlan]:
        """Tüm planları getir."""
        query = self.session.query(ProductionPlan).filter(
            ProductionPlan.is_active.is_(True)
        )

        if status:
            query = query.filter(ProductionPlan.status == status)

        if period_start:
            query = query.filter(ProductionPlan.period_end >= period_start)

        if period_end:
            query = query.filter(ProductionPlan.period_start <= period_end)

        return query.order_by(ProductionPlan.created_at.desc()).all()

    def get_plan_summary(self, plan_id: int) -> Dict:
        """Plan özeti getir."""
        plan = self.get_by_id(plan_id)
        if not plan:
            return {}

        total_items = len(plan.lines)
        scheduled_items = sum(1 for l in plan.lines if l.planned_start)
        released_items = sum(1 for l in plan.lines if l.work_order_id)

        total_quantity = sum(l.planned_quantity or 0 for l in plan.lines)

        return {
            "plan_id": plan.id,
            "plan_no": plan.plan_no,
            "status": plan.status.value,
            "total_items": total_items,
            "scheduled_items": scheduled_items,
            "released_items": released_items,
            "total_quantity": float(total_quantity),
            "period_start": plan.period_start.isoformat(),
            "period_end": plan.period_end.isoformat(),
        }

    # =========================================
    # KAPASİTE ANALİZİ
    # =========================================

    def check_capacity_for_period(
        self,
        station_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[date, Dict]:
        """
        Belirli bir dönem için istasyon kapasitesini kontrol et.

        Returns:
            {date: {"total": int, "scheduled": int, "remaining": int, "utilization": float}}
        """
        station = self.session.query(WorkStation).get(station_id)
        if not station:
            return {}

        result = {}
        current = start_date

        while current <= end_date:
            if not self._is_holiday(current) and current.weekday() < 5:
                total = station.daily_capacity_minutes
                remaining = station.get_remaining_capacity(current, self.session)
                scheduled = total - remaining
                utilization = (scheduled / total * 100) if total > 0 else 0

                result[current] = {
                    "total_capacity": total,
                    "scheduled": scheduled,
                    "remaining": remaining,
                    "utilization": round(utilization, 1),
                }

            current += timedelta(days=1)

        return result
