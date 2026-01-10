"""
Akıllı İş - MRP (Malzeme İhtiyaç Planlaması) Servisi
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
import json

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from database.base import get_session
from database.models.mrp import (
    MRPRun,
    MRPLine,
    MRPRunStatus,
    DemandSource,
    SuggestionType,
)
from database.models.inventory import Item, StockBalance
from database.models.production import (
    WorkOrder,
    WorkOrderLine,
    WorkOrderStatus,
    BillOfMaterials,
    BOMLine,
    BOMStatus,
)
from database.models.sales import SalesOrder, SalesOrderItem, SalesOrderStatus
from database.models.purchasing import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderStatus,
)


class MRPService:
    """MRP hesaplama motoru"""

    def __init__(self):
        self.session: Session = get_session()

    def close(self):
        if self.session:
            self.session.close()

    # =====================
    # MRP ÇALIŞTIRMA
    # =====================

    def run_mrp(
        self,
        horizon_days: int = 30,
        item_ids: List[int] = None,
        consider_safety: bool = True,
        include_work_orders: bool = True,
        include_sales_orders: bool = True,
    ) -> MRPRun:
        """
        MRP çalıştır

        1. MRP Run kaydı oluştur
        2. Brüt ihtiyaçları topla
        3. BOM patlatma yap
        4. Net ihtiyaç hesapla
        5. Tedarik önerileri oluştur
        """
        # MRP Run oluştur
        run = MRPRun(
            run_no=self._generate_run_no(),
            planning_horizon_days=horizon_days,
            consider_safety_stock=consider_safety,
            include_work_orders=include_work_orders,
            include_sales_orders=include_sales_orders,
            item_filter=json.dumps(item_ids) if item_ids else None,
            status=MRPRunStatus.PENDING,
        )
        self.session.add(run)
        self.session.flush()

        # Tarih aralığı
        start_date = date.today()
        end_date = start_date + timedelta(days=horizon_days)

        # Ürünleri belirle
        items = self._get_items_to_plan(item_ids)

        processed_items = 0
        items_with_shortage = 0
        total_suggestions = 0

        for item in items:
            # Brüt ihtiyaçları topla
            gross_reqs = self._get_gross_requirements(
                item.id, start_date, end_date, include_work_orders, include_sales_orders
            )

            # Mevcut stok
            current_stock = self._get_current_stock(item.id)

            # Beklenen girişler (açık siparişler)
            scheduled = self._get_scheduled_receipts(item.id, start_date, end_date)

            # Net ihtiyaç hesapla
            net_reqs = self._calculate_net_requirements(
                item, gross_reqs, current_stock, scheduled, consider_safety
            )

            # MRP satırları oluştur
            for req in net_reqs:
                line = MRPLine(
                    mrp_run_id=run.id,
                    item_id=item.id,
                    requirement_date=req["date"],
                    gross_requirement=req["gross"],
                    scheduled_receipts=req["scheduled"],
                    projected_on_hand=req["on_hand"],
                    net_requirement=req["net"],
                    demand_source=req.get("source"),
                    demand_source_id=req.get("source_id"),
                    demand_source_ref=req.get("source_ref"),
                )

                # Tedarik önerisi
                if req["net"] > 0:
                    self._create_suggestion(line, item, req)
                    items_with_shortage += 1
                    total_suggestions += 1

                self.session.add(line)

            processed_items += 1

        # Run istatistikleri güncelle
        run.total_items = processed_items
        run.items_with_shortage = items_with_shortage
        run.total_suggestions = total_suggestions
        run.status = MRPRunStatus.COMPLETED
        run.completed_at = datetime.now()

        self.session.commit()
        return run

    def _generate_run_no(self) -> str:
        """MRP çalışma numarası oluştur"""
        today = date.today()
        prefix = f"MRP-{today.strftime('%Y%m%d')}-"

        last = (
            self.session.query(MRPRun)
            .filter(MRPRun.run_no.like(f"{prefix}%"))
            .order_by(MRPRun.run_no.desc())
            .first()
        )

        if last:
            try:
                num = int(last.run_no.replace(prefix, ""))
                return f"{prefix}{num + 1:03d}"
            except ValueError:
                pass

        return f"{prefix}001"

    def _get_items_to_plan(self, item_ids: List[int] = None) -> List[Item]:
        """Planlanacak ürünleri getir"""
        query = self.session.query(Item).filter(Item.is_active == True)

        if item_ids:
            query = query.filter(Item.id.in_(item_ids))

        return query.all()

    # =====================
    # BRÜT İHTİYAÇ
    # =====================

    def _get_gross_requirements(
        self,
        item_id: int,
        start_date: date,
        end_date: date,
        include_wo: bool = True,
        include_so: bool = True,
    ) -> List[Dict]:
        """
        Brüt ihtiyaçları topla

        Kaynaklar:
        - İş emirleri (WorkOrderLine)
        - Satış siparişleri (SalesOrderItem)
        """
        requirements = []

        # İş Emirlerinden
        if include_wo:
            wo_reqs = self._get_work_order_requirements(item_id, start_date, end_date)
            requirements.extend(wo_reqs)

        # Satış Siparişlerinden
        if include_so:
            so_reqs = self._get_sales_order_requirements(item_id, start_date, end_date)
            requirements.extend(so_reqs)

        # Tarihe göre sırala
        requirements.sort(key=lambda x: x["date"])
        return requirements

    def _get_work_order_requirements(
        self, item_id: int, start_date: date, end_date: date
    ) -> List[Dict]:
        """İş emirlerinden malzeme ihtiyaçları"""
        # Açık iş emirlerinin malzeme satırları
        lines = (
            self.session.query(WorkOrderLine)
            .join(WorkOrder)
            .filter(
                WorkOrderLine.item_id == item_id,
                WorkOrder.status.in_(
                    [
                        WorkOrderStatus.PLANNED,
                        WorkOrderStatus.RELEASED,
                        WorkOrderStatus.IN_PROGRESS,
                    ]
                ),
                WorkOrder.planned_start >= start_date,
                WorkOrder.planned_start <= end_date,
            )
            .all()
        )

        return [
            {
                "date": line.work_order.planned_start,
                "gross": line.planned_quantity or Decimal(0),
                "source": DemandSource.WORK_ORDER,
                "source_id": line.work_order_id,
                "source_ref": line.work_order.order_no,
            }
            for line in lines
        ]

    def _get_sales_order_requirements(
        self, item_id: int, start_date: date, end_date: date
    ) -> List[Dict]:
        """Satış siparişlerinden ürün ihtiyaçları"""
        items = (
            self.session.query(SalesOrderItem)
            .join(SalesOrder)
            .filter(
                SalesOrderItem.item_id == item_id,
                SalesOrder.status.in_(
                    [SalesOrderStatus.CONFIRMED, SalesOrderStatus.PARTIAL]
                ),
                SalesOrder.delivery_date >= start_date,
                SalesOrder.delivery_date <= end_date,
            )
            .all()
        )

        return [
            {
                "date": item.sales_order.delivery_date,
                "gross": (item.quantity or Decimal(0))
                - (item.delivered_quantity or Decimal(0)),
                "source": DemandSource.SALES_ORDER,
                "source_id": item.sales_order_id,
                "source_ref": item.sales_order.order_no,
            }
            for item in items
            if (item.quantity or 0) > (item.delivered_quantity or 0)
        ]

    # =====================
    # STOK VE GİRİŞLER
    # =====================

    def _get_current_stock(self, item_id: int) -> Decimal:
        """Mevcut toplam stok"""
        result = (
            self.session.query(func.sum(StockBalance.quantity))
            .filter(StockBalance.item_id == item_id)
            .scalar()
        )

        return result or Decimal(0)

    def _get_scheduled_receipts(
        self, item_id: int, start_date: date, end_date: date
    ) -> Dict[date, Decimal]:
        """
        Beklenen girişler (açık satınalma siparişleri)
        """
        receipts = {}

        # Açık satınalma siparişleri
        po_items = (
            self.session.query(PurchaseOrderItem)
            .join(PurchaseOrder)
            .filter(
                PurchaseOrderItem.item_id == item_id,
                PurchaseOrder.status.in_(
                    [PurchaseOrderStatus.CONFIRMED, PurchaseOrderStatus.SENT]
                ),
                PurchaseOrder.delivery_date >= start_date,
                PurchaseOrder.delivery_date <= end_date,
            )
            .all()
        )

        for item in po_items:
            d = item.purchase_order.delivery_date
            pending = (item.quantity or 0) - (item.received_quantity or 0)
            if pending > 0:
                receipts[d] = receipts.get(d, Decimal(0)) + Decimal(str(pending))

        return receipts

    # =====================
    # NET İHTİYAÇ HESAPLAMA
    # =====================

    def _calculate_net_requirements(
        self,
        item: Item,
        gross_reqs: List[Dict],
        current_stock: Decimal,
        scheduled: Dict[date, Decimal],
        consider_safety: bool,
    ) -> List[Dict]:
        """
        Net ihtiyaç hesapla

        Formül: Net = Brüt - Eldeki - Planlanan Giriş + Emniyet
        """
        results = []
        on_hand = current_stock
        safety = Decimal(str(item.safety_stock or 0)) if consider_safety else Decimal(0)

        # Tarihlere göre grupla
        grouped = {}
        for req in gross_reqs:
            d = req["date"]
            if d not in grouped:
                grouped[d] = {"gross": Decimal(0), "reqs": []}
            grouped[d]["gross"] += req["gross"]
            grouped[d]["reqs"].append(req)

        # Tarihleri sırala
        for d in sorted(grouped.keys()):
            data = grouped[d]
            gross = data["gross"]
            sched = scheduled.get(d, Decimal(0))

            # Projeksiyon hesapla
            projected = on_hand + sched - gross

            # Net ihtiyaç
            net = Decimal(0)
            if projected < safety:
                net = safety - projected

            # Sonraki dönem için eldeki
            on_hand = projected

            # İlk ihtiyaç kaynağını al
            first_req = data["reqs"][0] if data["reqs"] else {}

            results.append(
                {
                    "date": d,
                    "gross": gross,
                    "scheduled": sched,
                    "on_hand": projected,
                    "net": net,
                    "source": first_req.get("source"),
                    "source_id": first_req.get("source_id"),
                    "source_ref": first_req.get("source_ref"),
                }
            )

        return results

    # =====================
    # TEDARİK ÖNERİSİ
    # =====================

    def _create_suggestion(self, line: MRPLine, item: Item, req: Dict):
        """Tedarik önerisi oluştur"""
        net = req["net"]
        req_date = req["date"]

        # Lot sizing uygula
        qty = self._apply_lot_sizing(net, item)

        # Lead time offset
        lead_days = item.lead_time_days or 0
        order_date = req_date - timedelta(days=lead_days)
        if order_date < date.today():
            order_date = date.today()

        # Tedarik türü belirle
        proc_type = item.procurement_type or "purchase"
        if proc_type == "manufacture" or item.is_producible:
            sug_type = SuggestionType.MANUFACTURE
        else:
            sug_type = SuggestionType.PURCHASE

        line.suggestion_type = sug_type
        line.suggested_qty = qty
        line.suggested_date = order_date
        line.planned_order_receipt = qty
        line.planned_order_release = qty

    def _apply_lot_sizing(self, net: Decimal, item: Item) -> Decimal:
        """
        Lot boyutlandırma

        - Minimum sipariş miktarı
        - Sipariş katı
        """
        qty = net
        min_qty = Decimal(str(item.min_order_qty or 1))
        multiple = Decimal(str(item.order_multiple or 1))

        # Minimum kontrol
        if qty < min_qty:
            qty = min_qty

        # Kat kontrolü
        if multiple > 1:
            remainder = qty % multiple
            if remainder > 0:
                qty = qty + (multiple - remainder)

        return qty

    # =====================
    # BOM PATLATMA
    # =====================

    def explode_bom(
        self, item_id: int, quantity: Decimal, level: int = 0, max_level: int = 10
    ) -> List[Dict]:
        """
        Çok seviyeli BOM patlatma

        Reçetenin tüm alt bileşenlerini açar.
        """
        if level >= max_level:
            return []

        # Aktif BOM bul
        bom = (
            self.session.query(BillOfMaterials)
            .filter(
                BillOfMaterials.item_id == item_id,
                BillOfMaterials.status == BOMStatus.ACTIVE,
                BillOfMaterials.is_active == True,
            )
            .first()
        )

        if not bom:
            return []

        results = []
        for line in bom.lines:
            comp_qty = (line.quantity or Decimal(0)) * quantity

            results.append(
                {
                    "level": level,
                    "item_id": line.item_id,
                    "item_code": line.item.code if line.item else "",
                    "item_name": line.item.name if line.item else "",
                    "quantity": comp_qty,
                    "unit_id": line.unit_id,
                }
            )

            # Alt reçete varsa recursive
            if line.item and line.item.is_producible:
                sub = self.explode_bom(line.item_id, comp_qty, level + 1, max_level)
                results.extend(sub)

        return results

    # =====================
    # CRUD İŞLEMLERİ
    # =====================

    def get_all_runs(
        self, limit: int = 50, status: MRPRunStatus = None
    ) -> List[MRPRun]:
        """Tüm MRP çalışmalarını getir"""
        query = self.session.query(MRPRun)

        if status:
            query = query.filter(MRPRun.status == status)

        return query.order_by(MRPRun.run_date.desc()).limit(limit).all()

    def get_run_by_id(self, run_id: int) -> Optional[MRPRun]:
        """ID ile MRP çalışması getir"""
        return self.session.query(MRPRun).get(run_id)

    def get_run_lines(
        self, run_id: int, with_suggestions_only: bool = False
    ) -> List[MRPLine]:
        """MRP satırlarını getir"""
        query = self.session.query(MRPLine).filter(MRPLine.mrp_run_id == run_id)

        if with_suggestions_only:
            query = query.filter(MRPLine.net_requirement > 0)

        return query.order_by(MRPLine.requirement_date, MRPLine.item_id).all()

    def get_suggestions(self, run_id: int) -> List[MRPLine]:
        """Tedarik önerilerini getir"""
        return (
            self.session.query(MRPLine)
            .filter(
                MRPLine.mrp_run_id == run_id,
                MRPLine.suggestion_type.isnot(None),
                MRPLine.is_applied == False,
            )
            .order_by(MRPLine.suggested_date, MRPLine.item_id)
            .all()
        )

    def apply_suggestion(self, line_id: int, auto_create: bool = True) -> Dict:
        """
        Öneriyi uygula

        Args:
            line_id: MRP satır ID
            auto_create: True ise otomatik sipariş/iş emri oluştur

        Returns:
            dict: İşlem sonucu
        """
        line = self.session.query(MRPLine).get(line_id)
        if not line:
            raise ValueError("MRP satırı bulunamadı")

        if line.is_applied:
            raise ValueError("Bu öneri zaten uygulandı")

        result = {}

        if line.suggestion_type == SuggestionType.PURCHASE:
            if auto_create:
                pr_id = self._create_purchase_request(line)
                result = {
                    "type": "purchase_request",
                    "order_id": pr_id,
                    "item_id": line.item_id,
                    "quantity": float(line.suggested_qty),
                    "date": line.suggested_date.isoformat(),
                    "message": f"Satınalma Talebi oluşturuldu (ID: {pr_id})",
                }
                line.applied_order_id = pr_id
            else:
                result = {
                    "type": "purchase_request",
                    "item_id": line.item_id,
                    "quantity": float(line.suggested_qty),
                    "date": line.suggested_date.isoformat(),
                    "message": "İşaretlendi (sipariş oluşturulmadı)",
                }

        elif line.suggestion_type == SuggestionType.MANUFACTURE:
            if auto_create:
                wo_id = self._create_work_order(line)
                result = {
                    "type": "work_order",
                    "order_id": wo_id,
                    "item_id": line.item_id,
                    "quantity": float(line.suggested_qty),
                    "date": line.suggested_date.isoformat(),
                    "message": f"İş Emri oluşturuldu (ID: {wo_id})",
                }
                line.applied_order_id = wo_id
            else:
                result = {
                    "type": "work_order",
                    "item_id": line.item_id,
                    "quantity": float(line.suggested_qty),
                    "date": line.suggested_date.isoformat(),
                    "message": "İşaretlendi (iş emri oluşturulmadı)",
                }

        # Uygulama işaretle
        line.is_applied = True
        line.applied_at = datetime.now()
        line.applied_order_type = result.get("type")
        self.session.commit()

        return result

    def _create_purchase_request(self, line: MRPLine) -> int:
        """MRP satırından Satınalma Talebi oluştur"""
        from modules.purchasing.services import PurchaseRequestService

        service = PurchaseRequestService()

        # Talep kalemi
        items_data = [
            {
                "item_id": line.item_id,
                "quantity": line.suggested_qty,
                "unit_id": line.item.unit_id if line.item else None,
                "notes": f"MRP: {line.demand_source_ref or ''}",
            }
        ]

        # Talep oluştur
        request = service.create(
            items_data=items_data,
            request_date=line.suggested_date,
            requestor="MRP Sistem",
            notes=f"MRP Run #{line.mrp_run.run_no} tarafından oluşturuldu",
        )

        return request.id

    def _create_work_order(self, line: MRPLine) -> int:
        """MRP satırından İş Emri oluştur"""
        from modules.production.services import WorkOrderService, BOMService

        wo_service = WorkOrderService()
        bom_service = BOMService()

        # Ürünün aktif BOM'unu bul
        bom = bom_service.get_active_bom(line.item_id)
        bom_id = bom.id if bom else None

        # İş emri oluştur
        order = wo_service.create(
            item_id=line.item_id,
            bom_id=bom_id,
            planned_quantity=line.suggested_qty,
            planned_start=line.suggested_date,
            notes=f"MRP Run #{line.mrp_run.run_no} tarafından oluşturuldu",
        )

        wo_service.close()
        bom_service.close()

        return order.id

    def apply_all_suggestions(self, run_id: int, auto_create: bool = True) -> Dict:
        """
        Tüm önerileri uygula

        Satınalma önerileri tek talep altında gruplandı
        Üretim önerileri ayrı iş emirleri olarak oluşturulur
        """
        suggestions = self.get_suggestions(run_id)

        results = {
            "total": len(suggestions),
            "purchase_requests": 0,
            "work_orders": 0,
            "errors": [],
        }

        # Satınalma önerilerini grupla (tek talep, çoklu kalem)
        purchase_lines = [
            s for s in suggestions if s.suggestion_type == SuggestionType.PURCHASE
        ]
        manufacture_lines = [
            s for s in suggestions if s.suggestion_type == SuggestionType.MANUFACTURE
        ]

        # Satınalma taleplerini tek seferde oluştur
        if purchase_lines and auto_create:
            try:
                pr_id = self._create_bulk_purchase_request(purchase_lines, run_id)
                for line in purchase_lines:
                    line.is_applied = True
                    line.applied_at = datetime.now()
                    line.applied_order_type = "purchase_request"
                    line.applied_order_id = pr_id
                results["purchase_requests"] = 1
                results["purchase_request_id"] = pr_id
            except Exception as e:
                results["errors"].append(f"Satınalma hatası: {e}")
        elif purchase_lines:
            for line in purchase_lines:
                line.is_applied = True
                line.applied_at = datetime.now()
                line.applied_order_type = "purchase_request"

        # Üretim emirlerini ayrı ayrı oluştur
        for line in manufacture_lines:
            try:
                if auto_create:
                    wo_id = self._create_work_order(line)
                    line.applied_order_id = wo_id
                    results["work_orders"] += 1
                line.is_applied = True
                line.applied_at = datetime.now()
                line.applied_order_type = "work_order"
            except Exception as e:
                results["errors"].append(f"İş emri hatası ({line.item.code}): {e}")

        self.session.commit()
        return results

    def _create_bulk_purchase_request(self, lines: List[MRPLine], run_id: int) -> int:
        """Çoklu MRP satırından tek Satınalma Talebi oluştur"""
        from modules.purchasing.services import PurchaseRequestService

        service = PurchaseRequestService()

        # Talep kalemleri
        items_data = []
        for line in lines:
            items_data.append(
                {
                    "item_id": line.item_id,
                    "quantity": line.suggested_qty,
                    "unit_id": line.item.unit_id if line.item else None,
                    "required_date": line.suggested_date,
                    "notes": f"MRP: {line.demand_source_ref or ''}",
                }
            )

        # MRP run bilgisi al
        run = self.get_run_by_id(run_id)
        run_no = run.run_no if run else ""

        # Talep oluştur
        request = service.create(
            items_data=items_data,
            request_date=date.today(),
            requestor="MRP Sistem",
            notes=f"MRP Run #{run_no} - {len(lines)} kalem",
        )

        return request.id

    def delete_run(self, run_id: int) -> bool:
        """MRP çalışması sil"""
        run = self.get_run_by_id(run_id)
        if run:
            self.session.delete(run)
            self.session.commit()
            return True
        return False
