"""
Akıllı İş - APS (Advanced Planning & Scheduling) Servisi

Gelişmiş Planlama ve Çizelgeleme servisi:
- Zeki yeniden çizelgeleme (cascade rescheduling)
- Darboğaz analizi
- Yük dengeleme
- Sürükle-bırak doğrulama
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
import uuid

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session, joinedload

from database.base import get_session
from database.models.production import (
    WorkOrder,
    WorkOrderLine,
    WorkOrderOperation,
    WorkOrderStatus,
    WorkStation,
    BillOfMaterials,
    BOMOperation,
    BOMStatus,
)
from database.models.calendar import ProductionHoliday
from modules.notifications.services import NotificationService


class APSError(Exception):
    """APS hatası base class"""
    pass


class APSService:
    """
    Advanced Planning & Scheduling (APS) Servisi

    Özellikler:
    - Operasyon yeniden çizelgeleme (cascade desteği)
    - Bileşen tarih kaskadı
    - Darboğaz tespiti ve analizi
    - Alternatif istasyonlara yük dengeleme
    - Sürükle-bırak için önizleme doğrulama
    """

    def __init__(self):
        self.session: Session = get_session()
        self._holidays_cache: Dict[date, bool] = {}

    def close(self):
        if self.session:
            self.session.close()

    # =========================================
    # OPERASYON YENİDEN ÇİZELGELEME
    # =========================================

    def reschedule_operation(
        self,
        operation_id: int,
        new_start: datetime,
        new_station_id: int = None,
        cascade_mode: str = "shift",
    ) -> Dict:
        """
        Operasyonu yeniden çizelgele.

        Args:
            operation_id: Operasyon ID
            new_start: Yeni başlangıç zamanı
            new_station_id: Yeni istasyon ID (opsiyonel, istasyon değişimi)
            cascade_mode: Kaskad modu
                - "shift": Sonraki operasyonları ileri kaydır
                - "insert": Araya sıkıştır, gerekirse diğerlerini kaydır
                - "none": Sadece bu operasyonu taşı

        Returns:
            {
                "success": bool,
                "operation": WorkOrderOperation,
                "affected_operations": List[Dict],
                "conflicts": List[str]
            }
        """
        operation = self.session.query(WorkOrderOperation).get(operation_id)
        if not operation:
            raise APSError(f"Operasyon bulunamadı: {operation_id}")

        # Kilitli mi kontrol et
        if operation.is_locked:
            return {
                "success": False,
                "operation": operation,
                "affected_operations": [],
                "conflicts": ["Operasyon kilitli, taşınamaz"],
            }

        old_start = operation.planned_start
        old_station_id = operation.work_station_id

        # Süre hesapla
        duration_minutes = (operation.planned_setup_time or 0) + (
            operation.planned_run_time or 0
        )

        # Yeni bitiş zamanı
        new_end = new_start + timedelta(minutes=duration_minutes)

        affected = []
        conflicts = []

        # İstasyon değişikliği
        if new_station_id and new_station_id != old_station_id:
            operation.work_station_id = new_station_id

        # Cascade moduna göre işle
        if cascade_mode == "shift":
            # Aynı istasyondaki çakışan operasyonları bul ve kaydır
            affected = self._shift_conflicting_operations(
                station_id=new_station_id or old_station_id,
                new_start=new_start,
                new_end=new_end,
                exclude_operation_id=operation_id,
            )
        elif cascade_mode == "insert":
            # Araya sıkıştır
            affected, conflicts = self._insert_operation(
                station_id=new_station_id or old_station_id,
                new_start=new_start,
                duration_minutes=duration_minutes,
                exclude_operation_id=operation_id,
            )

        # Operasyonu güncelle
        operation.planned_start = new_start
        operation.planned_end = new_end

        # Cascade group oluştur (ilişkili değişiklikleri grupla)
        if affected:
            group_id = str(uuid.uuid4())[:8]
            operation.cascade_group_id = group_id
            for op_data in affected:
                op = self.session.query(WorkOrderOperation).get(op_data["id"])
                if op:
                    op.cascade_group_id = group_id

        self.session.commit()

        # Bileşen tarihlerini kaskat güncelle
        if cascade_mode != "none":
            self.cascade_component_dates(operation.work_order_id, new_start)

        return {
            "success": True,
            "operation": operation,
            "affected_operations": affected,
            "conflicts": conflicts,
        }

    def _shift_conflicting_operations(
        self,
        station_id: int,
        new_start: datetime,
        new_end: datetime,
        exclude_operation_id: int,
    ) -> List[Dict]:
        """Çakışan operasyonları ileri kaydır."""
        affected = []

        # Çakışan operasyonları bul (aynı istasyon, zaman aralığı çakışıyor)
        conflicting = (
            self.session.query(WorkOrderOperation)
            .filter(
                WorkOrderOperation.work_station_id == station_id,
                WorkOrderOperation.id != exclude_operation_id,
                WorkOrderOperation.status.notin_(["completed", "cancelled"]),
                WorkOrderOperation.is_locked.isnot(True),
                # Zaman çakışması
                or_(
                    and_(
                        WorkOrderOperation.planned_start >= new_start,
                        WorkOrderOperation.planned_start < new_end,
                    ),
                    and_(
                        WorkOrderOperation.planned_end > new_start,
                        WorkOrderOperation.planned_end <= new_end,
                    ),
                    and_(
                        WorkOrderOperation.planned_start <= new_start,
                        WorkOrderOperation.planned_end >= new_end,
                    ),
                ),
            )
            .order_by(WorkOrderOperation.planned_start)
            .all()
        )

        shift_amount = timedelta(minutes=0)
        prev_end = new_end

        for op in conflicting:
            if op.planned_start < prev_end:
                # Kaydırma miktarı hesapla
                shift_needed = prev_end - op.planned_start
                shift_amount = max(shift_amount, shift_needed)

                old_start = op.planned_start
                old_end = op.planned_end

                # Kaydır
                op.planned_start = op.planned_start + shift_needed
                op.planned_end = op.planned_end + shift_needed

                affected.append({
                    "id": op.id,
                    "work_order_id": op.work_order_id,
                    "old_start": old_start.isoformat() if old_start else None,
                    "old_end": old_end.isoformat() if old_end else None,
                    "new_start": op.planned_start.isoformat(),
                    "new_end": op.planned_end.isoformat(),
                    "shift_minutes": int(shift_needed.total_seconds() / 60),
                })

                prev_end = op.planned_end

        return affected

    def _insert_operation(
        self,
        station_id: int,
        new_start: datetime,
        duration_minutes: int,
        exclude_operation_id: int,
    ) -> Tuple[List[Dict], List[str]]:
        """Araya sıkıştır, gerekirse diğerlerini kaydır."""
        # Basit implementasyon: shift ile aynı, ama önce boşluk arar
        new_end = new_start + timedelta(minutes=duration_minutes)

        # Önce tam boşluk var mı kontrol et
        conflicting = (
            self.session.query(WorkOrderOperation)
            .filter(
                WorkOrderOperation.work_station_id == station_id,
                WorkOrderOperation.id != exclude_operation_id,
                WorkOrderOperation.status.notin_(["completed", "cancelled"]),
                or_(
                    and_(
                        WorkOrderOperation.planned_start >= new_start,
                        WorkOrderOperation.planned_start < new_end,
                    ),
                    and_(
                        WorkOrderOperation.planned_end > new_start,
                        WorkOrderOperation.planned_end <= new_end,
                    ),
                ),
            )
            .first()
        )

        if not conflicting:
            # Çakışma yok, direkt yerleştir
            return [], []

        # Çakışma var, shift yap
        affected = self._shift_conflicting_operations(
            station_id, new_start, new_end, exclude_operation_id
        )

        conflicts = [
            f"{len(affected)} operasyon kaydırıldı"
        ] if affected else []

        return affected, conflicts

    # =========================================
    # BİLEŞEN TARİH KASKADI
    # =========================================

    def cascade_component_dates(
        self,
        parent_work_order_id: int,
        new_start: datetime,
    ) -> List[WorkOrder]:
        """
        Ana iş emri taşındığında bileşen iş emirlerini de güncelle.

        BOM patlatarak bağımlı iş emirlerini bulur ve tarihlerini
        orantılı olarak günceller.
        """
        parent_wo = self.session.query(WorkOrder).get(parent_work_order_id)
        if not parent_wo:
            return []

        updated_orders = []

        # Ana iş emrinin eski başlangıcı
        old_start = parent_wo.planned_start
        if not old_start:
            return []

        # Zaman farkı
        time_delta = new_start - old_start

        if time_delta.total_seconds() == 0:
            return []

        # Bileşen iş emirlerini bul (sales_order_id üzerinden veya parent referansı)
        # Bu projede bileşen iş emirleri ayrı bir referans ile tutulmuyor olabilir
        # Alternatif: BOM üzerinden ilişkili ürünlerin iş emirlerini bul

        # Ana ürünün BOM'unu al
        if parent_wo.bom_id:
            bom = self.session.query(BillOfMaterials).get(parent_wo.bom_id)
            if bom:
                # BOM satırlarındaki ürünler için açık iş emirlerini bul
                for bom_line in bom.lines:
                    component_wos = (
                        self.session.query(WorkOrder)
                        .filter(
                            WorkOrder.item_id == bom_line.item_id,
                            WorkOrder.status.in_([
                                WorkOrderStatus.DRAFT,
                                WorkOrderStatus.PLANNED,
                            ]),
                            WorkOrder.planned_start.isnot(None),
                            # Tarih yakınlığı kontrolü (ana iş emrinden önce olmalı)
                            WorkOrder.planned_end <= parent_wo.planned_start,
                        )
                        .all()
                    )

                    for comp_wo in component_wos:
                        # Tarihleri kaydır
                        if comp_wo.planned_start:
                            comp_wo.planned_start = comp_wo.planned_start + time_delta
                        if comp_wo.planned_end:
                            comp_wo.planned_end = comp_wo.planned_end + time_delta

                        updated_orders.append(comp_wo)

        self.session.commit()
        return updated_orders

    # =========================================
    # DARBOĞAZ ANALİZİ
    # =========================================

    def get_bottleneck_stations(
        self,
        start_date: date,
        end_date: date,
        threshold: float = 100.0,
    ) -> List[Dict]:
        """
        Doluluk oranı threshold'u aşan istasyonları bul.

        Args:
            start_date: Başlangıç tarihi
            end_date: Bitiş tarihi
            threshold: Doluluk eşiği (%, varsayılan 100)

        Returns:
            [
                {
                    "station": WorkStation,
                    "date": date,
                    "utilization": float,
                    "overload_minutes": int,
                    "alternatives": List[WorkStation]
                }
            ]
        """
        bottlenecks = []

        # Tüm aktif istasyonları al
        stations = (
            self.session.query(WorkStation)
            .filter(WorkStation.is_active.is_(True))
            .all()
        )

        current = start_date
        while current <= end_date:
            # Hafta sonu ve tatilleri atla
            if current.weekday() >= 5 or self._is_holiday(current):
                current += timedelta(days=1)
                continue

            for station in stations:
                total = station.daily_capacity_minutes
                if total <= 0:
                    continue

                remaining = station.get_remaining_capacity(current, self.session)
                scheduled = total - remaining
                utilization = (scheduled / total) * 100

                if utilization >= threshold:
                    overload = max(0, scheduled - total)

                    bottlenecks.append({
                        "station": station,
                        "station_id": station.id,
                        "station_code": station.code,
                        "station_name": station.name,
                        "date": current,
                        "utilization": round(utilization, 1),
                        "overload_minutes": overload,
                        "total_capacity": total,
                        "scheduled": scheduled,
                        "alternatives": list(station.alternatives),
                    })

            current += timedelta(days=1)

        # Doluluk oranına göre sırala (yüksekten düşüğe)
        bottlenecks.sort(key=lambda x: x["utilization"], reverse=True)

        return bottlenecks

    # =========================================
    # YÜK DENGELEME
    # =========================================

    def balance_load(
        self,
        station_id: int,
        target_date: date,
        use_alternatives: bool = True,
    ) -> Dict:
        """
        Aşırı yüklenmiş istasyonun yükünü dengele.

        Strateji:
        1. Taşınabilir operasyonları bul (kilitli olmayanlar)
        2. Önceliğe göre sırala (en esnek olanlar önce)
        3. Alternatif istasyonlara veya sonraki günlere dağıt

        Returns:
            {
                "moved_operations": List[Dict],
                "remaining_overload": int,
                "new_utilization": float
            }
        """
        station = self.session.query(WorkStation).get(station_id)
        if not station:
            raise APSError(f"İstasyon bulunamadı: {station_id}")

        total_capacity = station.daily_capacity_minutes
        remaining = station.get_remaining_capacity(target_date, self.session)
        overload = max(0, (total_capacity - remaining) - total_capacity)

        if overload <= 0:
            return {
                "moved_operations": [],
                "remaining_overload": 0,
                "new_utilization": ((total_capacity - remaining) / total_capacity * 100)
                if total_capacity > 0
                else 0,
            }

        moved = []
        freed_minutes = 0

        # Taşınabilir operasyonları bul
        movable_ops = (
            self.session.query(WorkOrderOperation)
            .join(WorkOrder)
            .filter(
                WorkOrderOperation.work_station_id == station_id,
                func.date(WorkOrderOperation.planned_start) == target_date,
                WorkOrderOperation.status.notin_(["completed", "cancelled", "in_progress"]),
                WorkOrderOperation.is_locked.isnot(True),
            )
            .order_by(WorkOrder.planned_end.desc())  # En geç bitiş tarihi olanları önce taşı
            .all()
        )

        for op in movable_ops:
            if freed_minutes >= overload:
                break

            op_duration = (op.planned_setup_time or 0) + (op.planned_run_time or 0)

            # Alternatif istasyonları dene
            moved_to = None
            if use_alternatives and station.alternatives:
                for alt in station.alternatives:
                    alt_remaining = alt.get_remaining_capacity(target_date, self.session)
                    if alt_remaining >= op_duration:
                        # Bu alternatife taşı
                        old_station_id = op.work_station_id
                        op.work_station_id = alt.id

                        moved.append({
                            "operation_id": op.id,
                            "work_order_id": op.work_order_id,
                            "from_station": station.code,
                            "to_station": alt.code,
                            "duration_minutes": op_duration,
                            "action": "moved_to_alternative",
                        })

                        moved_to = alt
                        freed_minutes += op_duration
                        break

            # Alternatif bulunamadıysa sonraki güne kaydır
            if not moved_to:
                next_day = self._find_available_day(station_id, op_duration, target_date)
                if next_day and next_day != target_date:
                    old_start = op.planned_start
                    new_start = datetime.combine(next_day, old_start.time())
                    duration = (op.planned_end - op.planned_start) if op.planned_end else timedelta(minutes=op_duration)
                    op.planned_start = new_start
                    op.planned_end = new_start + duration

                    moved.append({
                        "operation_id": op.id,
                        "work_order_id": op.work_order_id,
                        "from_date": target_date.isoformat(),
                        "to_date": next_day.isoformat(),
                        "duration_minutes": op_duration,
                        "action": "shifted_to_next_day",
                    })

                    freed_minutes += op_duration

        self.session.commit()

        # Yeni durumu hesapla
        new_remaining = station.get_remaining_capacity(target_date, self.session)
        new_scheduled = total_capacity - new_remaining
        new_utilization = (new_scheduled / total_capacity * 100) if total_capacity > 0 else 0

        # Bildirim gönder
        if moved:
            NotificationService.send_to_role(
                role_code="PRODUCTION_MANAGER",
                title="Yük Dengeleme Tamamlandı",
                message=f"{station.name} - {target_date}: {len(moved)} operasyon taşındı",
                notification_type="SUCCESS",
                link=f"/production/planning?date={target_date}&station={station_id}",
            )

        return {
            "moved_operations": moved,
            "remaining_overload": max(0, overload - freed_minutes),
            "new_utilization": round(new_utilization, 1),
        }

    def _find_available_day(
        self,
        station_id: int,
        required_minutes: int,
        after_date: date,
        max_days: int = 7,
    ) -> Optional[date]:
        """Yeterli kapasitesi olan sonraki günü bul."""
        station = self.session.query(WorkStation).get(station_id)
        if not station:
            return None

        current = after_date + timedelta(days=1)

        for _ in range(max_days):
            if current.weekday() >= 5 or self._is_holiday(current):
                current += timedelta(days=1)
                continue

            remaining = station.get_remaining_capacity(current, self.session)
            if remaining >= required_minutes:
                return current

            current += timedelta(days=1)

        return None

    # =========================================
    # SÜRÜKLE-BIRAK DOĞRULAMA
    # =========================================

    def validate_move(
        self,
        operation_id: int,
        new_start: datetime,
        new_station_id: int,
    ) -> Dict:
        """
        Taşıma işlemini doğrula (sürükle-bırak önizleme).

        Returns:
            {
                "valid": bool,
                "warnings": List[str],
                "conflicts": List[Dict],
                "affected_count": int
            }
        """
        operation = self.session.query(WorkOrderOperation).get(operation_id)
        if not operation:
            return {
                "valid": False,
                "warnings": ["Operasyon bulunamadı"],
                "conflicts": [],
                "affected_count": 0,
            }

        warnings = []
        conflicts = []

        # Kilitli mi?
        if operation.is_locked:
            return {
                "valid": False,
                "warnings": ["Operasyon kilitli"],
                "conflicts": [],
                "affected_count": 0,
            }

        # Süre hesapla
        duration = (operation.planned_setup_time or 0) + (operation.planned_run_time or 0)
        new_end = new_start + timedelta(minutes=duration)

        # Kapasite kontrolü
        station = self.session.query(WorkStation).get(new_station_id)
        if station:
            remaining = station.get_remaining_capacity(new_start.date(), self.session)
            if remaining < duration:
                warnings.append(
                    f"Kapasite yetersiz: {remaining} dk kaldı, {duration} dk gerekli"
                )

        # Çakışma kontrolü
        conflicting = (
            self.session.query(WorkOrderOperation)
            .filter(
                WorkOrderOperation.work_station_id == new_station_id,
                WorkOrderOperation.id != operation_id,
                WorkOrderOperation.status.notin_(["completed", "cancelled"]),
                or_(
                    and_(
                        WorkOrderOperation.planned_start >= new_start,
                        WorkOrderOperation.planned_start < new_end,
                    ),
                    and_(
                        WorkOrderOperation.planned_end > new_start,
                        WorkOrderOperation.planned_end <= new_end,
                    ),
                ),
            )
            .all()
        )

        for conf in conflicting:
            conflicts.append({
                "operation_id": conf.id,
                "work_order_no": conf.work_order.order_no if conf.work_order else "",
                "operation_name": conf.name,
                "current_start": conf.planned_start.isoformat() if conf.planned_start else "",
                "current_end": conf.planned_end.isoformat() if conf.planned_end else "",
            })

        # Geçmiş tarih kontrolü
        if new_start.date() < date.today():
            warnings.append("Geçmiş tarihe planlama yapılıyor")

        return {
            "valid": len(conflicts) == 0 or True,  # Çakışma varsa da taşınabilir (cascade ile)
            "warnings": warnings,
            "conflicts": conflicts,
            "affected_count": len(conflicts),
        }

    # =========================================
    # YARDIMCI METODLAR
    # =========================================

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

    def get_station_schedule(
        self,
        station_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[date, List[Dict]]:
        """
        İstasyonun belirli dönemdeki çizelgesini getir.

        Returns:
            {
                date: [
                    {
                        "operation_id": int,
                        "work_order_no": str,
                        "item_name": str,
                        "start": datetime,
                        "end": datetime,
                        "duration_minutes": int,
                        "status": str
                    }
                ]
            }
        """
        operations = (
            self.session.query(WorkOrderOperation)
            .join(WorkOrder)
            .options(
                joinedload(WorkOrderOperation.work_order).joinedload(WorkOrder.item)
            )
            .filter(
                WorkOrderOperation.work_station_id == station_id,
                WorkOrderOperation.planned_start >= datetime.combine(start_date, datetime.min.time()),
                WorkOrderOperation.planned_start < datetime.combine(end_date + timedelta(days=1), datetime.min.time()),
            )
            .order_by(WorkOrderOperation.planned_start)
            .all()
        )

        schedule = {}

        for op in operations:
            op_date = op.planned_start.date() if op.planned_start else None
            if not op_date:
                continue

            if op_date not in schedule:
                schedule[op_date] = []

            schedule[op_date].append({
                "operation_id": op.id,
                "work_order_id": op.work_order_id,
                "work_order_no": op.work_order.order_no if op.work_order else "",
                "item_name": op.work_order.item.name if op.work_order and op.work_order.item else "",
                "operation_name": op.name,
                "start": op.planned_start.isoformat() if op.planned_start else None,
                "end": op.planned_end.isoformat() if op.planned_end else None,
                "duration_minutes": (op.planned_setup_time or 0) + (op.planned_run_time or 0),
                "status": op.status,
                "is_locked": op.is_locked,
            })

        return schedule
