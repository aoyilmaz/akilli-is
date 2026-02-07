"""
Akıllı İş - MPS (Master Production Scheduling) Servisi

Ana Üretim Planlama servisi. SAP PP/IBP standartlarına yakın
backward scheduling ve önceliklendirme algoritmaları içerir.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from database.base import get_session
from database.models.production import (
    ProductionPlan,
    ProductionPlanLine,
    ProductionPlanStatus,
    BillOfMaterials,
    BOMOperation,
    BOMStatus,
    WorkOrder,
    WorkOrderStatus,
    WorkStation,
)
from database.models.inventory import Item, ItemType, Warehouse
from database.models.sales import (
    SalesOrder,
    SalesOrderItem,
    SalesOrderStatus,
)
from database.models.purchasing import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderStatus,
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
                joinedload(SalesOrderItem.order).joinedload(SalesOrder.customer),
                joinedload(SalesOrderItem.item),
            )
            .filter(
                SalesOrder.is_active.is_(True),
                SalesOrderItem.is_active.is_(True),
                # Teslim tarihi dönem içinde
                or_(
                    SalesOrder.delivery_date.between(period_start, period_end),
                    SalesOrder.requested_delivery_date.between(
                        period_start, period_end
                    ),
                ),
                # Üretim gerektiren ürünler (mamül veya yarı mamül)
                Item.item_type.in_([ItemType.MAMUL, ItemType.YARI_MAMUL]),
            )
        )

        if only_confirmed:
            query = query.filter(
                SalesOrder.status.in_(
                    [
                        SalesOrderStatus.CONFIRMED,
                        SalesOrderStatus.IN_PRODUCTION,
                    ]
                )
            )

        order_items = query.all()

        # Plan satırları oluştur
        for oi in order_items:
            so = oi.order
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
            remaining = (oi.quantity or Decimal(0)) - (
                oi.delivered_quantity or Decimal(0)
            )

            if remaining <= 0:
                continue

            line = ProductionPlanLine(
                plan_id=plan.id,
                item_id=item.id,
                sales_order_id=so.id,
                sales_order_item_id=oi.id,
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
        priority = Decimal(str(customer_score)) * Decimal(
            str(customer_weight)
        ) + Decimal(str(delay_risk)) * Decimal(str(delay_weight))

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

        if bom and bom.lead_time_days:
            return int(bom.lead_time_days)

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
                run_per_unit = float(op.run_time or 0)
                run_total = run_per_unit * float(line.planned_quantity)
                total_minutes += setup + run_total
        elif bom and bom.lead_time:
            # Operasyon yoksa lead time'ı dakikaya çevir (8 saat/gün)
            total_minutes = int(bom.lead_time) * 8 * 60
        else:
            # Varsayılan: 1 gün
            total_minutes = 8 * 60

        # İş günlerini hesapla
        production_days = max(
            1, total_minutes // (8 * 60) + (1 if total_minutes % (8 * 60) > 0 else 0)
        )

        # Tatilleri dikkate alarak geriye say
        planned_end = datetime.combine(
            line.demand_date, datetime.max.time().replace(microsecond=0)
        )
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
                    datetime.max.time().replace(microsecond=0),
                )

        line.planned_start = datetime.combine(
            planned_start, datetime.min.time().replace(hour=8)
        )
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
                ProductionHoliday.date == check_date,
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
            run_total = (op.run_time or 0) * Decimal(str(quantity))
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
        Planı onayla ve hammadde rezervasyonu yap.

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

        # 1. Plan durumunu güncelle
        plan.status = ProductionPlanStatus.APPROVED
        plan.approved_by = user_id
        plan.approved_at = datetime.now()

        # 2. Hammadde rezervasyonu yap
        try:
            self._reserve_materials_for_plan(plan)
        except Exception as e:
            # Rezervasyon hatası onayı engellememeli mi?
            # Genelde MPS bir taahhüttür, rezervasyon başarısızsa (kod hatası vb) durmalı.
            # Ancak yetersiz stok allow_negative=True ile aşılacak.
            print(f"MPS Hammadde Rezervasyon Hatası: {e}")
            raise MPSError(f"Hammadde rezervasyonu sırasında hata oluştu: {e}")

        self.session.commit()

        return plan

    def _reserve_materials_for_plan(self, plan: ProductionPlan):
        """Plan içindeki ürünlerin hammaddelerini rezerve et"""
        from modules.inventory.services.base import StockMovementService

        stock_service = StockMovementService()

        # Varsayılan depo (tercihen üretim deposu)
        default_warehouse = (
            self.session.query(Warehouse)
            .filter(Warehouse.is_production == True)
            .first()
            or self.session.query(Warehouse)
            .filter(Warehouse.is_default == True)
            .first()
        )
        default_warehouse_id = default_warehouse.id if default_warehouse else 1

        for line in plan.lines:
            # Ürünün aktif reçetesini bul
            bom = (
                self.session.query(BillOfMaterials)
                .filter(
                    BillOfMaterials.item_id == line.item_id,
                    BillOfMaterials.status == BOMStatus.ACTIVE,
                )
                .first()
            )

            if not bom:
                continue

            for bom_line in bom.lines:
                # Toplam ihtiyaç = Planlanan Miktar * Reçete Miktarı
                required_qty = line.planned_quantity * bom_line.quantity

                # Rezervasyon yap (Gelecek planlaması için yetersiz stok olsa da devam et)
                stock_service.reserve_stock(
                    item_id=bom_line.item_id,
                    warehouse_id=default_warehouse_id,
                    quantity=required_qty,
                    reference_type="mps",
                    reference_id=plan.id,
                    allow_negative=True,
                )

    # =========================================
    # SORGULAR
    # =========================================

    def get_by_id(self, plan_id: int) -> Optional[ProductionPlan]:
        """ID ile plan getir."""
        return (
            self.session.query(ProductionPlan)
            .options(
                joinedload(ProductionPlan.lines).joinedload(ProductionPlanLine.item),
                joinedload(ProductionPlan.lines).joinedload(
                    ProductionPlanLine.sales_order
                ),
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

        return (
            query.options(
                joinedload(ProductionPlan.lines).joinedload(ProductionPlanLine.item),
                joinedload(ProductionPlan.lines).joinedload(
                    ProductionPlanLine.sales_order
                ),
                joinedload(ProductionPlan.lines).joinedload(
                    ProductionPlanLine.work_order
                ),
            )
            .order_by(ProductionPlan.created_at.desc())
            .all()
        )

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

    def get_aggregated_capacity(self, plan_id: int) -> List[Dict]:
        """
        Plandaki üretim miktarlarına göre iş istasyonu doluluklarını simüle eder.

        Args:
            plan_id: Plan ID

        Returns:
            [
                {
                    "station_name": "Kesim",
                    "utilization": 85.5,
                    "total_load_hours": 120,
                    "available_hours": 140
                },
                ...
            ]
        """
        plan = self.get_by_id(plan_id)
        if not plan:
            return []

        # 1. İstasyon yüklerini topla (Dakika)
        station_loads = {}  # {station_id: minutes}

        for line in plan.lines:
            qty = float(line.planned_quantity or 0)
            if qty <= 0:
                continue

            # BOM'u bul
            # NOT: Optimize edilebilir, her satır için sorgu yerine toplu çekim
            bom = (
                self.session.query(BillOfMaterials)
                .options(joinedload(BillOfMaterials.operations))
                .filter(
                    BillOfMaterials.item_id == line.item_id,
                    BillOfMaterials.status == BOMStatus.ACTIVE,
                    BillOfMaterials.is_active.is_(True),
                )
                .first()
            )

            if not bom or not bom.operations:
                continue

            for op in bom.operations:
                if not op.work_station_id:
                    continue

                s_id = op.work_station_id
                setup = op.setup_time or 0
                run = float(op.run_time or 0) * qty
                total_op_load = setup + run

                station_loads[s_id] = station_loads.get(s_id, 0) + total_op_load

        # 2. İstasyon kapasitelerini hesapla ve oranla
        results = []

        # Dönemdeki iş günü sayısı (kabaca)
        # Daha hassas hesap için tatiller çıkarılmalı
        total_days = (plan.period_end - plan.period_start).days
        work_days = max(1, int(total_days * 5 / 7))  # Haftada 5 gün varsayımı

        stations = (
            self.session.query(WorkStation)
            .filter(WorkStation.is_active.is_(True))
            .all()
        )

        for st in stations:
            load_min = station_loads.get(st.id, 0)

            # Kapasite: Günlük Dakika * İş Günü * Verimlilik
            daily_min = st.daily_capacity_minutes
            total_capacity_min = daily_min * work_days

            if total_capacity_min <= 0:
                utilization = 0
            else:
                utilization = (load_min / total_capacity_min) * 100

            if utilization > 0:  # Sadece yükü olanları veya darboğazları göster
                results.append(
                    {
                        "station_name": st.name,
                        "utilization": round(utilization, 1),
                        "total_load_hours": round(load_min / 60, 1),
                        "available_hours": round(total_capacity_min / 60, 1),
                    }
                )

        # Doluluk oranına göre sırala (Azalan)
        return sorted(results, key=lambda x: x["utilization"], reverse=True)

    # =========================================
    # MPS GRID (HÜCRE BAZLI) İŞLEMLER
    # =========================================

    def get_mps_grid_data(
        self,
        plan_id: int,
        item_id: int,
        start_date: date,
        period_days: int = 7,
        num_periods: int = 6,
    ) -> Dict:
        """
        Grid görünümü için verileri hazırla.

        Args:
            plan_id: Plan ID
            item_id: Ürün ID
            start_date: Başlangıç tarihi
            period_days: Periyot uzunluğu (gün)
            num_periods: Periyot sayısı

        Returns:
            {
                "periods": ["P1", "P2"...],
                "demand": [10, 20...],
                "incoming": [5, 0...],
                "mps": [15, 25...],
                "projected_stock": [100, 105...]
            }
        """
        result = {
            "periods": [],
            "period_dates": [],
            "demand": [0.0] * num_periods,
            "incoming": [0.0] * num_periods,
            "mps": [0.0] * num_periods,
            "projected_stock": [0.0] * num_periods,
            "safety_stock": 0.0,
            "risks": ["none"] * num_periods,
        }

        # Mevcut stok ve emniyet stoğu
        item = self.session.query(Item).get(item_id)
        current_stock = float(item.total_stock or 0) if item else 0
        safety_stock = float(item.safety_stock or 0) if item else 0
        result["safety_stock"] = safety_stock

        # Plan satırlarını çek
        lines = (
            self.session.query(ProductionPlanLine)
            .filter(
                ProductionPlanLine.plan_id == plan_id,
                ProductionPlanLine.item_id == item_id,
                ProductionPlanLine.demand_date >= start_date,
            )
            .all()
        )

        running_stock = current_stock

        for i in range(num_periods):
            p_start = start_date + timedelta(days=i * period_days)
            p_end = p_start + timedelta(days=period_days - 1)

            # Period label
            period_label = f"W{p_start.isocalendar()[1]}"  # Hafta numarası
            result["periods"].append(period_label)
            result["period_dates"].append(
                p_end.isoformat()
            )  # Hücre tarihi olarak dönem sonunu alıyoruz

            # Bu periyoda düşen satırları topla
            p_demand = 0
            p_mps = 0

            for line in lines:
                if p_start <= line.demand_date <= p_end:
                    p_demand += float(line.demand_quantity or 0)
                    p_mps += float(line.planned_quantity or 0)

            # Beklenen girişler (Satınalma / İş Emirleri)
            p_incoming = 0

            # 1. Satınalma Emirleri (WAITING veya PARTIAL)
            purchase_items = (
                self.session.query(PurchaseOrderItem)
                .join(PurchaseOrder)
                .filter(
                    PurchaseOrderItem.item_id == item_id,
                    PurchaseOrderItem.is_active.is_(True),
                    PurchaseOrder.is_active.is_(True),
                    PurchaseOrder.status.in_(
                        [PurchaseOrderStatus.CONFIRMED, PurchaseOrderStatus.PARTIAL]
                    ),
                    # Teslim tarihi bu periyoda düşenler
                    PurchaseOrder.delivery_date.between(p_start, p_end),
                )
                .all()
            )
            p_incoming += sum(
                float(pi.quantity or 0) - float(pi.delivered_quantity or 0)
                for pi in purchase_items
            )

            # 2. Planlanmış/Devam Eden İş Emirleri (Bu üretim planından bağımsız olanlar)
            # NOT: Kendi planımızdaki MPS zaten "mps" satırında. Burada "harici" gelenler olmalı mı?
            # Veya released olmuş iş emirleri artık "mps" değil "incoming" mi sayılır?
            # Standart: Released WO artık "Scheduled Receipt" (Gelen) olur, MPS (Planned Order) değildir.
            # O yüzden Released ve InProgress olanları incoming ekleyelim.
            work_orders = (
                self.session.query(WorkOrder)
                .filter(
                    WorkOrder.item_id == item_id,
                    WorkOrder.is_active.is_(True),
                    WorkOrder.status.in_(
                        [WorkOrderStatus.RELEASED, WorkOrderStatus.IN_PROGRESS]
                    ),
                    WorkOrder.planned_end.between(p_start, p_end),
                )
                .all()
            )
            p_incoming += sum(
                float(wo.planned_quantity or 0) - float(wo.completed_quantity or 0)
                for wo in work_orders
            )

            # Hesaplamalar
            running_stock = running_stock + p_incoming + p_mps - p_demand

            result["demand"][i] = p_demand
            result["incoming"][i] = p_incoming
            result["mps"][i] = p_mps
            result["projected_stock"][i] = running_stock

            # Risk Belirleme
            if running_stock < 0:
                result["risks"][i] = "critical"
            elif running_stock < safety_stock:
                result["risks"][i] = "warning"

        return result

    def update_mps_quantity(
        self,
        plan_id: int,
        item_id: int,
        target_date: date,
        quantity: float,
    ) -> ProductionPlanLine:
        """
        MPS Miktarını güncelle.

        Eğer o tarih için (veya dönem için) bir satır varsa onu günceller,
        yoksa yeni satır oluşturur.
        Note: Grid genelde dönem sonu tarihi gönderir.
        """
        # O tarihteki veya o tarihe denk gelen satırı bul
        # Basitleştirme: Tam tarih eşleşmesi arıyoruz.
        # İleride dönem mantığı eklenebilir.

        line = (
            self.session.query(ProductionPlanLine)
            .filter(
                ProductionPlanLine.plan_id == plan_id,
                ProductionPlanLine.item_id == item_id,
                ProductionPlanLine.demand_date == target_date,
            )
            .first()
        )

        if line:
            # Varsa güncelle
            if quantity <= 0 and line.demand_quantity == 0:
                # Hem talep hem plan 0 ise silinebilir
                self.session.delete(line)
            else:
                line.planned_quantity = quantity
        else:
            # Yoksa oluştur (sadece miktar > 0 ise)
            if quantity > 0:
                line = ProductionPlanLine(
                    plan_id=plan_id,
                    item_id=item_id,
                    demand_date=target_date,
                    demand_quantity=0,  # Manuel giriş olduğu için talep 0
                    planned_quantity=quantity,
                    priority_score=50,
                )
                self.session.add(line)

        self.session.commit()
        return line

    def get_planning_variance(
        self,
        start_date: date,
        end_date: date,
        item_id: Optional[int] = None,
    ) -> List[Dict]:
        """
        Planlanan vs Gerçekleşen Üretim Raporu.
        MPS (ProductionPlanLine) ile bağlı WorkOrder verilerini karşılaştırır.
        """
        query = self.session.query(ProductionPlanLine).filter(
            ProductionPlanLine.demand_date.between(start_date, end_date)
        )

        if item_id:
            query = query.filter(ProductionPlanLine.item_id == item_id)

        lines = query.all()
        results = []

        for line in lines:
            planned = float(line.planned_quantity or 0)
            actual = 0.0

            if line.work_order:
                actual = float(line.work_order.completed_quantity or 0)

            variance = actual - planned
            variance_pct = (variance / planned * 100) if planned > 0 else 0

            results.append(
                {
                    "date": line.demand_date.isoformat(),
                    "item_code": line.item.code if line.item else "",
                    "item_name": line.item.name if line.item else "",
                    "plan_no": line.plan.plan_no if line.plan else "",
                    "planned_qty": planned,
                    "actual_qty": actual,
                    "variance": variance,
                    "variance_pct": round(variance_pct, 1),
                    "status": (
                        line.work_order.status.value if line.work_order else "PLANNED"
                    ),
                }
            )

    def get_period_capacity_analysis(self, plan_id: int) -> Dict:
        """
        Periyot bazlı kapasite yük analizi.

        Returns:
            {
                "periods": ["W1", "W2", ...],
                "stations": [
                    {"name": "Kesim", "utilizations": [80.5, 120.0, 90.0, ...]},
                    ...
                ]
            }
        """
        plan = self.get_by_id(plan_id)
        if not plan:
            return {"periods": [], "stations": []}

        # Periyot tarihlerini al
        # NOT: mps_grid_data ile uyumlu olması için oradan da çekebiliriz
        # Şimdilik plan satırlarından tarihlerini gruplayalım
        period_dates = sorted(list(set(line.demand_date for line in plan.lines)))
        period_labels = [d.strftime("%d.%m") for d in period_dates]

        stations = (
            self.session.query(WorkStation)
            .filter(WorkStation.is_active.is_(True))
            .all()
        )

        # İstasyon günlük kapasiteleri
        station_caps = {s.id: float(s.daily_capacity_minutes or 0) for s in stations}
        station_names = {s.id: s.name for s in stations}

        # Grid hazırlığı: {station_id: [load_per_period]}
        grid = {s.id: [0.0] * len(period_dates) for s in stations}

        date_to_idx = {d: i for i, d in enumerate(period_dates)}

        for line in plan.lines:
            qty = float(line.planned_quantity or 0)
            if qty <= 0 or line.demand_date not in date_to_idx:
                continue

            idx = date_to_idx[line.demand_date]

            # BOM operasyonlarını bul
            bom = (
                self.session.query(BillOfMaterials)
                .options(joinedload(BillOfMaterials.operations))
                .filter(
                    BillOfMaterials.item_id == line.item_id,
                    BillOfMaterials.status == BOMStatus.ACTIVE,
                    BillOfMaterials.is_active.is_(True),
                )
                .first()
            )

            if not bom:
                continue

            for op in bom.operations:
                if op.work_station_id in grid:
                    load = (op.setup_time or 0) + (float(op.run_time or 0) * qty)
                    grid[op.work_station_id][idx] += load

        # Sonuçları orana çevir
        res_stations = []
        for s_id, loads in grid.items():
            if sum(loads) == 0:
                continue  # Yükü olmayanları gösterme

            # Varsayım: Her periyot arası kabaca iş günü sayısı (Basitleştirme: 5 gün)
            # Daha stabil bir dashboard için dinamik iş günü hesaplanabilir
            work_days = 5
            max_cap = station_caps[s_id] * work_days

            utils = []
            for load in loads:
                u = (load / max_cap * 100) if max_cap > 0 else 0
                utils.append(round(u, 1))

            res_stations.append({"name": station_names[s_id], "utilizations": utils})

        return {
            "periods": period_labels,
            "stations": sorted(
                res_stations, key=lambda x: max(x["utilizations"]), reverse=True
            ),
        }
