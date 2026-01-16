"""
Akıllı İş - Bakım ve Onarım Modülü Servis Sınıfı
Kapsamlı CMMS işlevleri: KPI hesaplamaları, duruş takibi, kontrol listeleri
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
import shutil
import os

from database.models.maintenance import (
    Equipment,
    EquipmentSparePart,
    EquipmentDowntime,
    MaintenanceCategory,
    MaintenanceRequest,
    MaintenanceRequestAttachment,
    MaintenanceChecklist,
    MaintenanceChecklistItem,
    MaintenanceWorkOrder,
    MaintenanceWorkOrderPart,
    WorkOrderAttachment,
    WorkOrderChecklistResult,
    MaintenancePlan,
    MaintenancePriority,
    MaintenanceStatus,
    WorkOrderStatus,
    MaintenanceType,
    CriticalityLevel,
    EquipmentStatus,
)
from database.models.inventory import (
    Item,
    StockBalance,
    StockMovement,
    StockMovementType,
    Warehouse,
)
from database.models.purchasing import PurchaseRequest, PurchaseRequestItem, Supplier
from database.models.production import WorkStation
from database.models.user import User, Role
from database.models.hr import Employee, Department, Position


class MaintenanceService:
    """Bakım ve Onarım Modülü Servis Sınıfı"""

    UPLOAD_PATH = "uploads/maintenance"

    def __init__(self, db_session: Session):
        self.db = db_session

    # ==================== EKİPMAN YÖNETİMİ ====================

    def create_equipment(self, code: str, name: str, **kwargs) -> Equipment:
        """Yeni ekipman oluşturur"""
        equipment = Equipment(code=code, name=name, **kwargs)
        self.db.add(equipment)
        self.db.commit()
        self.db.refresh(equipment)
        return equipment

    def update_equipment(self, equipment_id: int, **kwargs) -> Equipment:
        """Ekipman bilgilerini günceller"""
        equipment = self.db.query(Equipment).get(equipment_id)
        if not equipment:
            raise ValueError(f"Ekipman bulunamadı: {equipment_id}")

        for key, value in kwargs.items():
            if hasattr(equipment, key):
                setattr(equipment, key, value)

        self.db.commit()
        self.db.refresh(equipment)
        return equipment

    def get_equipment_list(self, active_only: Optional[bool] = None) -> List[Equipment]:
        """Ekipman listesini getirir"""
        query = self.db.query(Equipment)

        if active_only is True:
            query = query.filter(Equipment.is_active == True)
        elif active_only is False:
            query = query.filter(Equipment.is_active == False)

        return query.order_by(Equipment.name).all()

    def get_equipment_by_id(self, equipment_id: int) -> Optional[Equipment]:
        """ID'ye göre ekipman getirir"""
        return self.db.query(Equipment).get(equipment_id)

    def deactivate_equipment(self, equipment_id: int) -> Equipment:
        """Ekipmanı pasife alır"""
        equipment = self.db.query(Equipment).get(equipment_id)
        if equipment:
            equipment.is_active = False
            self.db.commit()
        return equipment

    def get_last_maintenance_date(self, equipment_id: int) -> Optional[datetime]:
        """Ekipmanın son bakım tarihini getirir"""
        wo = (
            self.db.query(MaintenanceWorkOrder)
            .filter(
                MaintenanceWorkOrder.equipment_id == equipment_id,
                MaintenanceWorkOrder.status == WorkOrderStatus.COMPLETED,
            )
            .order_by(desc(MaintenanceWorkOrder.completed_date))
            .first()
        )
        return wo.completed_date if wo else None

    # ==================== YEDEK PARÇA ====================

    def get_equipment_spare_parts(self, equipment_id: int) -> List[EquipmentSparePart]:
        """Ekipmanın yedek parça listesini getirir"""
        return (
            self.db.query(EquipmentSparePart)
            .filter(EquipmentSparePart.equipment_id == equipment_id)
            .all()
        )

    def add_equipment_spare_part(
        self, equipment_id: int, item_id: int, min_quantity: float = 1, **kwargs
    ) -> EquipmentSparePart:
        """Ekipmana yedek parça ekler"""
        spare_part = EquipmentSparePart(
            equipment_id=equipment_id,
            item_id=item_id,
            min_quantity=min_quantity,
            **kwargs,
        )
        self.db.add(spare_part)
        self.db.commit()
        return spare_part

    def get_item_total_stock(self, item_id: int) -> float:
        """Ürünün toplam stok miktarını getirir"""
        result = (
            self.db.query(func.sum(StockBalance.quantity))
            .filter(StockBalance.item_id == item_id)
            .scalar()
        )
        return float(result) if result else 0

    # ==================== DURUŞ TAKİBİ ====================

    def start_downtime(
        self,
        equipment_id: int,
        reason: str,
        start_time: datetime = None,
        work_order_id: int = None,
        notes: str = None,
    ) -> EquipmentDowntime:
        """Ekipman duruşu başlatır"""
        # Ekipman durumunu güncelle
        equipment = self.db.query(Equipment).get(equipment_id)
        if equipment:
            if reason == "breakdown":
                equipment.current_status = EquipmentStatus.BREAKDOWN
            else:
                equipment.current_status = EquipmentStatus.STOPPED

        downtime = EquipmentDowntime(
            equipment_id=equipment_id,
            reason=reason,
            start_time=start_time or datetime.utcnow(),
            work_order_id=work_order_id,
            notes=notes,
        )
        self.db.add(downtime)
        self.db.commit()
        return downtime

    def end_downtime(self, downtime_id: int) -> EquipmentDowntime:
        """Duruşu sonlandırır"""
        downtime = self.db.query(EquipmentDowntime).get(downtime_id)
        if downtime:
            downtime.end_time = datetime.utcnow()

            # Ekipman durumunu güncelle
            equipment = self.db.query(Equipment).get(downtime.equipment_id)
            if equipment:
                equipment.current_status = EquipmentStatus.RUNNING

            self.db.commit()
        return downtime

    def get_downtime_by_id(self, downtime_id: int) -> Optional[EquipmentDowntime]:
        """ID'ye göre duruş kaydı getirir"""
        return self.db.query(EquipmentDowntime).get(downtime_id)

    def get_equipment_downtimes(
        self, equipment_id: int, start_date: datetime = None, end_date: datetime = None
    ) -> List[EquipmentDowntime]:
        """Ekipmanın duruş kayıtlarını getirir"""
        query = self.db.query(EquipmentDowntime).filter(
            EquipmentDowntime.equipment_id == equipment_id
        )

        if start_date:
            query = query.filter(EquipmentDowntime.start_time >= start_date)
        if end_date:
            query = query.filter(EquipmentDowntime.start_time <= end_date)

        return query.order_by(desc(EquipmentDowntime.start_time)).all()

    def get_active_downtimes(self) -> List[EquipmentDowntime]:
        """Aktif duruşları getirir"""
        return (
            self.db.query(EquipmentDowntime)
            .filter(EquipmentDowntime.end_time == None)
            .order_by(desc(EquipmentDowntime.start_time))
            .all()
        )

    def get_today_downtimes(self) -> List[EquipmentDowntime]:
        """Bugünkü duruşları getirir"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return (
            self.db.query(EquipmentDowntime)
            .filter(EquipmentDowntime.start_time >= today)
            .order_by(desc(EquipmentDowntime.start_time))
            .all()
        )

    def get_week_downtimes(self) -> List[EquipmentDowntime]:
        """Bu haftaki duruşları getirir"""
        week_ago = datetime.now() - timedelta(days=7)
        return (
            self.db.query(EquipmentDowntime)
            .filter(EquipmentDowntime.start_time >= week_ago)
            .order_by(desc(EquipmentDowntime.start_time))
            .all()
        )

    def get_all_downtimes(self, limit: int = 100) -> List[EquipmentDowntime]:
        """Tüm duruşları getirir"""
        return (
            self.db.query(EquipmentDowntime)
            .order_by(desc(EquipmentDowntime.start_time))
            .limit(limit)
            .all()
        )

    # ==================== KATEGORİ YÖNETİMİ ====================

    def create_category(
        self, code: str, name: str, description: str = None
    ) -> MaintenanceCategory:
        """Yeni bakım kategorisi oluşturur"""
        category = MaintenanceCategory(code=code, name=name, description=description)
        self.db.add(category)
        self.db.commit()
        return category

    def get_all_categories(self) -> List[MaintenanceCategory]:
        """Tüm kategorileri getirir"""
        return self.db.query(MaintenanceCategory).all()

    # ==================== KULLANICI / TEKNİSYEN ====================

    def get_all_users(self) -> List[User]:
        """Tüm aktif kullanıcıları getirir"""
        return self.db.query(User).filter(User.is_active == True).all()

    def get_maintenance_technicians(self) -> List[User]:
        """Bakım teknisyenlerini getirir"""
        return (
            self.db.query(User)
            .join(User.roles)
            .outerjoin(Employee, User.id == Employee.user_id)
            .outerjoin(Department, Employee.department_id == Department.id)
            .outerjoin(Position, Employee.position_id == Position.id)
            .filter(
                User.is_active == True,
                or_(
                    Role.code.in_(["MAINTENANCE", "TECHNICIAN", "ADMIN"]),
                    Role.name.ilike("%Bakım%"),
                    Department.code == "MAINT",
                    Position.code.in_(["MAINT_MGR", "MAINT_CHIEF", "MAINT_TECH"]),
                ),
            )
            .group_by(User.id)
            .all()
        )

    # ==================== TEDARİKÇİ / İŞ İSTASYONU ====================

    def get_all_suppliers(self) -> List[Supplier]:
        """Tüm tedarikçileri getirir"""
        return self.db.query(Supplier).filter(Supplier.is_active == True).all()

    def get_all_workstations(self) -> List[WorkStation]:
        """Tüm iş istasyonlarını getirir"""
        return self.db.query(WorkStation).filter(WorkStation.is_active == True).all()

    # ==================== ENVANTER ====================

    def get_all_warehouses(self) -> List[Warehouse]:
        """Tüm depoları getirir"""
        return self.db.query(Warehouse).filter(Warehouse.is_active == True).all()

    def get_items_with_stock(self, warehouse_id: int) -> List[Tuple[Item, float]]:
        """Depodaki stoklu ürünleri getirir"""
        return (
            self.db.query(Item, StockBalance.quantity)
            .join(StockBalance, StockBalance.item_id == Item.id)
            .filter(
                StockBalance.warehouse_id == warehouse_id,
                StockBalance.quantity > 0,
                Item.is_active == True,
            )
            .all()
        )

    # ==================== BAKIM TALEBİ ====================

    def create_request(
        self,
        equipment_id: int,
        description: str,
        priority: MaintenancePriority = MaintenancePriority.NORMAL,
        category_id: int = None,
        reported_by_id: int = None,
        maintenance_type: MaintenanceType = MaintenanceType.BREAKDOWN,
    ) -> MaintenanceRequest:
        """Yeni arıza/bakım talebi oluşturur"""
        today_str = datetime.now().strftime("%Y%m%d")
        count = (
            self.db.query(MaintenanceRequest)
            .filter(MaintenanceRequest.request_no.like(f"REQ-{today_str}-%"))
            .count()
        )
        request_no = f"REQ-{today_str}-{count + 1:03d}"

        request = MaintenanceRequest(
            request_no=request_no,
            equipment_id=equipment_id,
            description=description,
            priority=priority,
            category_id=category_id,
            reported_by_id=reported_by_id,
            maintenance_type=maintenance_type,
            status=MaintenanceStatus.OPEN,
        )
        self.db.add(request)
        self.db.commit()
        return request

    def get_request_by_id(self, request_id: int) -> Optional[MaintenanceRequest]:
        """ID'ye göre talep getirir"""
        return self.db.query(MaintenanceRequest).get(request_id)

    def update_request_status(
        self, request_id: int, status: MaintenanceStatus, notes: str = None
    ) -> MaintenanceRequest:
        """Talep durumunu günceller"""
        request = self.db.query(MaintenanceRequest).get(request_id)
        if request:
            request.status = status
            if notes:
                request.resolution_notes = notes
            if status == MaintenanceStatus.RESOLVED:
                request.completed_date = datetime.utcnow()
            self.db.commit()
        return request

    def get_pending_requests(
        self, priority: MaintenancePriority = None
    ) -> List[MaintenanceRequest]:
        """Bekleyen talepleri listeler"""
        query = self.db.query(MaintenanceRequest).filter(
            MaintenanceRequest.status.notin_(
                [MaintenanceStatus.RESOLVED, MaintenanceStatus.CANCELLED]
            )
        )

        if priority:
            query = query.filter(MaintenanceRequest.priority == priority)

        return query.order_by(desc(MaintenanceRequest.request_date)).all()

    def get_resolved_requests(
        self, priority: MaintenancePriority = None
    ) -> List[MaintenanceRequest]:
        """Çözülen talepleri listeler"""
        query = self.db.query(MaintenanceRequest).filter(
            MaintenanceRequest.status == MaintenanceStatus.RESOLVED
        )

        if priority:
            query = query.filter(MaintenanceRequest.priority == priority)

        return query.order_by(desc(MaintenanceRequest.completed_date)).all()

    def get_all_requests(
        self, priority: MaintenancePriority = None
    ) -> List[MaintenanceRequest]:
        """Tüm talepleri listeler"""
        query = self.db.query(MaintenanceRequest)

        if priority:
            query = query.filter(MaintenanceRequest.priority == priority)

        return query.order_by(desc(MaintenanceRequest.request_date)).all()

    def add_request_attachment(
        self, request_id: int, file_path: str
    ) -> MaintenanceRequestAttachment:
        """Talebe dosya ekler"""
        file_name = os.path.basename(file_path)
        file_type = file_name.split(".")[-1] if "." in file_name else "unknown"
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        # Dosyayı kopyala
        dest_dir = os.path.join(self.UPLOAD_PATH, "requests", str(request_id))
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, file_name)
        shutil.copy2(file_path, dest_path)

        attachment = MaintenanceRequestAttachment(
            request_id=request_id,
            file_name=file_name,
            file_path=dest_path,
            file_type=file_type,
            file_size=file_size,
        )
        self.db.add(attachment)
        self.db.commit()
        return attachment

    # ==================== İŞ EMRİ ====================

    def create_work_order(
        self,
        equipment_id: int,
        request_id: int = None,
        assigned_to_id: int = None,
        priority: MaintenancePriority = MaintenancePriority.NORMAL,
        planned_start_date: datetime = None,
        due_date: datetime = None,
        estimated_hours: float = None,
        checklist_id: int = None,
        description: str = None,
    ) -> MaintenanceWorkOrder:
        """Yeni iş emri oluşturur"""
        today_str = datetime.now().strftime("%Y%m%d")
        count = (
            self.db.query(MaintenanceWorkOrder)
            .filter(MaintenanceWorkOrder.order_no.like(f"WO-{today_str}-%"))
            .count()
        )
        order_no = f"WO-{today_str}-{count + 1:03d}"

        status = WorkOrderStatus.ASSIGNED if assigned_to_id else WorkOrderStatus.DRAFT

        work_order = MaintenanceWorkOrder(
            order_no=order_no,
            equipment_id=equipment_id,
            request_id=request_id,
            assigned_to_id=assigned_to_id,
            priority=priority,
            planned_start_date=planned_start_date,
            due_date=due_date,
            estimated_hours=estimated_hours,
            checklist_id=checklist_id,
            description=description,
            status=status,
        )
        self.db.add(work_order)

        # Talep varsa durumu güncelle
        if request_id:
            request = self.db.query(MaintenanceRequest).get(request_id)
            if request:
                request.status = MaintenanceStatus.IN_PROGRESS

        self.db.commit()
        self.db.refresh(work_order)

        # Kontrol listesi varsa sonuç kayıtlarını oluştur
        if checklist_id:
            self._create_checklist_results(work_order.id, checklist_id)

        return work_order

    def _create_checklist_results(self, work_order_id: int, checklist_id: int):
        """İş emri için kontrol listesi sonuç kayıtlarını oluşturur"""
        checklist = self.db.query(MaintenanceChecklist).get(checklist_id)
        if checklist and checklist.items:
            for item in checklist.items:
                result = WorkOrderChecklistResult(
                    work_order_id=work_order_id,
                    checklist_item_id=item.id,
                    is_checked=False,
                )
                self.db.add(result)
            self.db.commit()

    def get_work_order_by_id(self, work_order_id: int) -> Optional[MaintenanceWorkOrder]:
        """ID'ye göre iş emri getirir"""
        return self.db.query(MaintenanceWorkOrder).get(work_order_id)

    def get_active_work_orders(self) -> List[MaintenanceWorkOrder]:
        """Aktif iş emirlerini listeler"""
        return (
            self.db.query(MaintenanceWorkOrder)
            .filter(
                MaintenanceWorkOrder.status.notin_(
                    [
                        WorkOrderStatus.COMPLETED,
                        WorkOrderStatus.CANCELLED,
                        WorkOrderStatus.CLOSED,
                    ]
                )
            )
            .order_by(desc(MaintenanceWorkOrder.created_at))
            .all()
        )

    def get_completed_work_orders(self) -> List[MaintenanceWorkOrder]:
        """Tamamlanan iş emirlerini listeler"""
        return (
            self.db.query(MaintenanceWorkOrder)
            .filter(MaintenanceWorkOrder.status == WorkOrderStatus.COMPLETED)
            .order_by(desc(MaintenanceWorkOrder.completed_date))
            .all()
        )

    def get_all_work_orders(self) -> List[MaintenanceWorkOrder]:
        """Tüm iş emirlerini listeler"""
        return (
            self.db.query(MaintenanceWorkOrder)
            .order_by(desc(MaintenanceWorkOrder.created_at))
            .all()
        )

    def start_work_order(self, work_order_id: int) -> MaintenanceWorkOrder:
        """İş emrini başlatır"""
        wo = self.db.query(MaintenanceWorkOrder).get(work_order_id)
        if wo:
            wo.status = WorkOrderStatus.IN_PROGRESS
            wo.actual_start_date = datetime.utcnow()

            # Ekipman durumunu güncelle
            equipment = self.db.query(Equipment).get(wo.equipment_id)
            if equipment:
                equipment.current_status = EquipmentStatus.MAINTENANCE

            self.db.commit()
        return wo

    def complete_work_order(
        self, work_order_id: int, notes: str = None, actual_hours: float = None
    ) -> MaintenanceWorkOrder:
        """İş emrini tamamlar"""
        wo = self.db.query(MaintenanceWorkOrder).get(work_order_id)
        if wo:
            wo.status = WorkOrderStatus.COMPLETED
            wo.completed_date = datetime.utcnow()
            if notes:
                wo.notes = notes
            if actual_hours:
                wo.actual_hours = actual_hours
                wo.labor_hours = actual_hours
                wo.labor_cost = Decimal(str(actual_hours)) * (wo.hourly_rate or 0)
                wo.total_cost = (wo.material_cost or 0) + wo.labor_cost

            # Talep varsa kapat
            if wo.request_id:
                req = self.db.query(MaintenanceRequest).get(wo.request_id)
                if req:
                    req.status = MaintenanceStatus.RESOLVED
                    req.completed_date = datetime.utcnow()
                    req.resolution_notes = f"İş emri {wo.order_no} ile tamamlandı. {notes or ''}"

            # Ekipman durumunu güncelle
            equipment = self.db.query(Equipment).get(wo.equipment_id)
            if equipment:
                equipment.current_status = EquipmentStatus.RUNNING

            self.db.commit()
        return wo

    def update_work_order_notes(self, work_order_id: int, notes: str) -> MaintenanceWorkOrder:
        """İş emri notlarını günceller"""
        wo = self.db.query(MaintenanceWorkOrder).get(work_order_id)
        if wo:
            wo.notes = notes
            self.db.commit()
        return wo

    # ==================== YEDEK PARÇA KULLANIMI ====================

    def add_part_to_work_order(
        self, work_order_id: int, item_id: int, quantity: float, warehouse_id: int
    ) -> MaintenanceWorkOrderPart:
        """İş emrine yedek parça ekler ve stoktan düşer"""
        item = self.db.query(Item).get(item_id)
        unit_cost = item.purchase_price or 0

        part = MaintenanceWorkOrderPart(
            work_order_id=work_order_id,
            item_id=item_id,
            quantity=quantity,
            unit_id=item.unit_id,
            unit_cost=unit_cost,
            total_cost=float(quantity) * float(unit_cost),
        )
        self.db.add(part)

        # Maliyet güncelle
        wo = self.db.query(MaintenanceWorkOrder).get(work_order_id)
        wo.material_cost = (wo.material_cost or 0) + part.total_cost
        wo.total_cost = (wo.total_cost or 0) + part.total_cost

        # Stok hareketi
        movement = StockMovement(
            movement_type=StockMovementType.CIKIS,
            item_id=item_id,
            from_warehouse_id=warehouse_id,
            quantity=quantity,
            unit_id=item.unit_id,
            description=f"Bakım İş Emri: {wo.order_no}",
            document_type="MaintenanceWorkOrder",
            document_no=wo.order_no,
        )
        self.db.add(movement)

        # Stok bakiyesi güncelle
        balance = (
            self.db.query(StockBalance)
            .filter(
                StockBalance.item_id == item_id,
                StockBalance.warehouse_id == warehouse_id,
            )
            .first()
        )
        if balance:
            balance.quantity -= Decimal(str(quantity))

        self.db.commit()
        return part

    def get_work_order_attachments(self, work_order_id: int) -> List[WorkOrderAttachment]:
        """İş emri eklerini getirir"""
        return (
            self.db.query(WorkOrderAttachment)
            .filter(WorkOrderAttachment.work_order_id == work_order_id)
            .all()
        )

    def add_work_order_attachment(
        self, work_order_id: int, file_path: str, file_name: str, file_type: str
    ) -> WorkOrderAttachment:
        """İş emrine dosya ekler"""
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        # Dosyayı kopyala
        dest_dir = os.path.join(self.UPLOAD_PATH, "work_orders", str(work_order_id))
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, file_name)
        shutil.copy2(file_path, dest_path)

        attachment = WorkOrderAttachment(
            work_order_id=work_order_id,
            file_name=file_name,
            file_path=dest_path,
            file_type=file_type,
            file_size=file_size,
        )
        self.db.add(attachment)
        self.db.commit()
        return attachment

    # ==================== KONTROL LİSTESİ ====================

    def get_all_checklists(self) -> List[MaintenanceChecklist]:
        """Tüm kontrol listelerini getirir"""
        return (
            self.db.query(MaintenanceChecklist)
            .filter(MaintenanceChecklist.is_active == True)
            .all()
        )

    def get_checklist_by_id(self, checklist_id: int) -> Optional[MaintenanceChecklist]:
        """ID'ye göre kontrol listesi getirir"""
        return self.db.query(MaintenanceChecklist).get(checklist_id)

    def create_checklist(self, name: str, items: List[Dict], **kwargs) -> MaintenanceChecklist:
        """Kontrol listesi oluşturur"""
        checklist = MaintenanceChecklist(name=name, **kwargs)
        self.db.add(checklist)
        self.db.flush()

        for item_data in items:
            item = MaintenanceChecklistItem(
                checklist_id=checklist.id,
                description=item_data["description"],
                is_required=item_data.get("is_required", True),
                order_no=item_data.get("order_no", 1),
            )
            self.db.add(item)

        self.db.commit()
        return checklist

    def update_checklist(self, checklist_id: int, items: List[Dict] = None, **kwargs) -> MaintenanceChecklist:
        """Kontrol listesini günceller"""
        checklist = self.db.query(MaintenanceChecklist).get(checklist_id)
        if not checklist:
            raise ValueError(f"Kontrol listesi bulunamadı: {checklist_id}")

        for key, value in kwargs.items():
            if hasattr(checklist, key) and key != "items":
                setattr(checklist, key, value)

        if items is not None:
            # Mevcut maddeleri sil
            self.db.query(MaintenanceChecklistItem).filter(
                MaintenanceChecklistItem.checklist_id == checklist_id
            ).delete()

            # Yeni maddeleri ekle
            for item_data in items:
                item = MaintenanceChecklistItem(
                    checklist_id=checklist_id,
                    description=item_data["description"],
                    is_required=item_data.get("is_required", True),
                    order_no=item_data.get("order_no", 1),
                )
                self.db.add(item)

        self.db.commit()
        return checklist

    def duplicate_checklist(self, checklist_id: int) -> MaintenanceChecklist:
        """Kontrol listesini kopyalar"""
        original = self.db.query(MaintenanceChecklist).get(checklist_id)
        if not original:
            raise ValueError(f"Kontrol listesi bulunamadı: {checklist_id}")

        new_checklist = MaintenanceChecklist(
            name=f"{original.name} (Kopya)",
            description=original.description,
            equipment_id=original.equipment_id,
            maintenance_type=original.maintenance_type,
        )
        self.db.add(new_checklist)
        self.db.flush()

        for item in original.items:
            new_item = MaintenanceChecklistItem(
                checklist_id=new_checklist.id,
                description=item.description,
                is_required=item.is_required,
                order_no=item.order_no,
            )
            self.db.add(new_item)

        self.db.commit()
        return new_checklist

    def delete_checklist(self, checklist_id: int):
        """Kontrol listesini siler"""
        checklist = self.db.query(MaintenanceChecklist).get(checklist_id)
        if checklist:
            self.db.delete(checklist)
            self.db.commit()

    def get_work_order_checklist_results(
        self, work_order_id: int
    ) -> List[WorkOrderChecklistResult]:
        """İş emri kontrol listesi sonuçlarını getirir"""
        return (
            self.db.query(WorkOrderChecklistResult)
            .filter(WorkOrderChecklistResult.work_order_id == work_order_id)
            .all()
        )

    def update_checklist_result(
        self, result_id: int, is_checked: bool, notes: str = None
    ) -> WorkOrderChecklistResult:
        """Kontrol listesi sonucunu günceller"""
        result = self.db.query(WorkOrderChecklistResult).get(result_id)
        if result:
            result.is_checked = is_checked
            if notes:
                result.notes = notes
            if is_checked:
                result.checked_at = datetime.utcnow()
            self.db.commit()
        return result

    # ==================== PERİYODİK BAKIM PLANI ====================

    def create_maintenance_plan(self, **kwargs) -> MaintenancePlan:
        """Bakım planı oluşturur"""
        plan = MaintenancePlan(**kwargs)

        # İlk sonraki bakım tarihini hesapla
        if not plan.next_maintenance_date:
            plan.next_maintenance_date = self._calculate_next_maintenance_date(
                datetime.utcnow(), plan.frequency_type, plan.frequency_value
            )

        self.db.add(plan)
        self.db.commit()
        return plan

    def update_maintenance_plan(self, plan_id: int, **kwargs) -> MaintenancePlan:
        """Bakım planını günceller"""
        plan = self.db.query(MaintenancePlan).get(plan_id)
        if not plan:
            raise ValueError(f"Plan bulunamadı: {plan_id}")

        for key, value in kwargs.items():
            if hasattr(plan, key):
                setattr(plan, key, value)

        self.db.commit()
        return plan

    def get_maintenance_plan_by_id(self, plan_id: int) -> Optional[MaintenancePlan]:
        """ID'ye göre bakım planı getirir"""
        return self.db.query(MaintenancePlan).get(plan_id)

    def get_maintenance_plans(self, active_only: bool = True) -> List[MaintenancePlan]:
        """Bakım planlarını listeler"""
        query = self.db.query(MaintenancePlan)
        if active_only:
            query = query.filter(MaintenancePlan.is_active == True)
        return query.order_by(MaintenancePlan.next_maintenance_date).all()

    def get_active_maintenance_plans(self) -> List[MaintenancePlan]:
        """Aktif bakım planlarını listeler"""
        return self.get_maintenance_plans(active_only=True)

    def get_overdue_maintenance_plans(self) -> List[MaintenancePlan]:
        """Vadesi geçmiş bakım planlarını getirir"""
        return (
            self.db.query(MaintenancePlan)
            .filter(
                MaintenancePlan.is_active == True,
                MaintenancePlan.next_maintenance_date < datetime.utcnow(),
            )
            .order_by(MaintenancePlan.next_maintenance_date)
            .all()
        )

    def get_plans_by_date(self, date: datetime) -> List[MaintenancePlan]:
        """Belirli tarihteki bakım planlarını getirir"""
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        return (
            self.db.query(MaintenancePlan)
            .filter(
                MaintenancePlan.is_active == True,
                MaintenancePlan.next_maintenance_date >= start,
                MaintenancePlan.next_maintenance_date < end,
            )
            .all()
        )

    def generate_work_order_from_plan(self, plan_id: int) -> MaintenanceWorkOrder:
        """Plandan iş emri oluşturur"""
        plan = self.db.query(MaintenancePlan).get(plan_id)
        if not plan:
            raise ValueError(f"Plan bulunamadı: {plan_id}")

        wo = self.create_work_order(
            equipment_id=plan.equipment_id,
            checklist_id=plan.checklist_id,
            description=f"Periyodik Bakım: {plan.name}",
        )

        # Plan tarihlerini güncelle
        plan.last_maintenance_date = datetime.utcnow()
        plan.next_maintenance_date = self._calculate_next_maintenance_date(
            datetime.utcnow(), plan.frequency_type, plan.frequency_value
        )
        self.db.commit()

        return wo

    def _calculate_next_maintenance_date(
        self, from_date: datetime, freq_type: str, freq_value: int
    ) -> datetime:
        """Sonraki bakım tarihini hesaplar"""
        if freq_type == "daily":
            return from_date + timedelta(days=freq_value)
        elif freq_type == "weekly":
            return from_date + timedelta(weeks=freq_value)
        elif freq_type == "monthly":
            return from_date + timedelta(days=freq_value * 30)
        elif freq_type == "yearly":
            return from_date + timedelta(days=freq_value * 365)
        return from_date + timedelta(days=30)

    # ==================== BAKIM GEÇMİŞİ ====================

    def get_equipment_maintenance_history(
        self, equipment_id: int, limit: int = 50
    ) -> List[MaintenanceWorkOrder]:
        """Ekipmanın bakım geçmişini getirir"""
        return (
            self.db.query(MaintenanceWorkOrder)
            .filter(
                MaintenanceWorkOrder.equipment_id == equipment_id,
                MaintenanceWorkOrder.status == WorkOrderStatus.COMPLETED,
            )
            .order_by(desc(MaintenanceWorkOrder.completed_date))
            .limit(limit)
            .all()
        )

    def get_equipment_total_cost(self, equipment_id: int) -> Dict[str, float]:
        """Ekipmanın toplam bakım maliyetini hesaplar"""
        result = (
            self.db.query(
                func.sum(MaintenanceWorkOrder.material_cost).label("material"),
                func.sum(MaintenanceWorkOrder.labor_cost).label("labor"),
                func.sum(MaintenanceWorkOrder.total_cost).label("total"),
            )
            .filter(
                MaintenanceWorkOrder.equipment_id == equipment_id,
                MaintenanceWorkOrder.status == WorkOrderStatus.COMPLETED,
            )
            .first()
        )

        return {
            "material_cost": float(result.material or 0),
            "labor_cost": float(result.labor or 0),
            "total_cost": float(result.total or 0),
        }

    # ==================== KPI HESAPLAMALARI ====================

    def get_equipment_kpis(self, equipment_id: int, period_days: int = 30) -> Dict[str, Any]:
        """Ekipman KPI'larını hesaplar (MTBF, MTTR, Kullanılabilirlik)"""
        start_date = datetime.utcnow() - timedelta(days=period_days)

        # Arıza sayısı
        failures = (
            self.db.query(MaintenanceWorkOrder)
            .filter(
                MaintenanceWorkOrder.equipment_id == equipment_id,
                MaintenanceWorkOrder.status == WorkOrderStatus.COMPLETED,
                MaintenanceWorkOrder.created_at >= start_date,
            )
            .count()
        )

        # Toplam duruş süresi (dakika)
        downtimes = (
            self.db.query(EquipmentDowntime)
            .filter(
                EquipmentDowntime.equipment_id == equipment_id,
                EquipmentDowntime.start_time >= start_date,
            )
            .all()
        )

        total_downtime_hours = sum(d.duration_hours for d in downtimes)

        # Toplam çalışma saati (varsayım: 24/7 çalışma)
        total_hours = period_days * 24

        # MTBF (Mean Time Between Failures)
        mtbf = (total_hours - total_downtime_hours) / max(failures, 1)

        # MTTR (Mean Time To Repair)
        mttr = total_downtime_hours / max(failures, 1)

        # Kullanılabilirlik
        availability = ((total_hours - total_downtime_hours) / total_hours) * 100

        # Toplam maliyet
        costs = self.get_equipment_total_cost(equipment_id)

        return {
            "mtbf": mtbf,
            "mttr": mttr,
            "availability": availability,
            "failure_count": failures,
            "total_downtime": total_downtime_hours,
            "total_cost": costs["total_cost"],
        }

    def get_all_equipment_kpis(self, period_days: int = 30) -> List[Dict[str, Any]]:
        """Tüm ekipmanların KPI'larını hesaplar"""
        equipments = self.get_equipment_list(active_only=True)
        result = []

        for eq in equipments:
            kpis = self.get_equipment_kpis(eq.id, period_days)
            kpis["equipment_id"] = eq.id
            kpis["equipment_code"] = eq.code
            kpis["equipment_name"] = eq.name
            result.append(kpis)

        return result

    # ==================== RAPORLAR ====================

    def get_work_order_stats(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """İş emri istatistiklerini getirir"""
        query = self.db.query(MaintenanceWorkOrder).filter(
            MaintenanceWorkOrder.created_at >= start_date,
            MaintenanceWorkOrder.created_at <= end_date,
        )

        total = query.count()
        completed = query.filter(
            MaintenanceWorkOrder.status == WorkOrderStatus.COMPLETED
        ).count()
        in_progress = query.filter(
            MaintenanceWorkOrder.status == WorkOrderStatus.IN_PROGRESS
        ).count()
        cancelled = query.filter(
            MaintenanceWorkOrder.status == WorkOrderStatus.CANCELLED
        ).count()

        total_cost = (
            query.with_entities(func.sum(MaintenanceWorkOrder.total_cost)).scalar() or 0
        )

        # Talep istatistikleri
        req_query = self.db.query(MaintenanceRequest).filter(
            MaintenanceRequest.request_date >= start_date,
            MaintenanceRequest.request_date <= end_date,
        )

        requests_total = req_query.count()
        requests_resolved = req_query.filter(
            MaintenanceRequest.status == MaintenanceStatus.RESOLVED
        ).count()
        requests_pending = req_query.filter(
            MaintenanceRequest.status.notin_(
                [MaintenanceStatus.RESOLVED, MaintenanceStatus.CANCELLED]
            )
        ).count()

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "cancelled": cancelled,
            "total_cost": float(total_cost),
            "requests_total": requests_total,
            "requests_resolved": requests_resolved,
            "requests_pending": requests_pending,
        }

    def get_equipment_cost_report(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Ekipman bazlı maliyet raporu"""
        results = (
            self.db.query(
                Equipment.id,
                Equipment.code,
                Equipment.name,
                func.sum(MaintenanceWorkOrder.material_cost).label("material_cost"),
                func.sum(MaintenanceWorkOrder.labor_cost).label("labor_cost"),
                func.sum(MaintenanceWorkOrder.total_cost).label("total_cost"),
                func.count(MaintenanceWorkOrder.id).label("work_order_count"),
            )
            .join(MaintenanceWorkOrder, MaintenanceWorkOrder.equipment_id == Equipment.id)
            .filter(
                MaintenanceWorkOrder.completed_date >= start_date,
                MaintenanceWorkOrder.completed_date <= end_date,
                MaintenanceWorkOrder.status == WorkOrderStatus.COMPLETED,
            )
            .group_by(Equipment.id)
            .order_by(desc("total_cost"))
            .all()
        )

        return [
            {
                "equipment_id": r.id,
                "equipment_code": r.code,
                "equipment_name": r.name,
                "material_cost": float(r.material_cost or 0),
                "labor_cost": float(r.labor_cost or 0),
                "total_cost": float(r.total_cost or 0),
                "work_order_count": r.work_order_count,
            }
            for r in results
        ]

    def get_technician_performance(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Teknisyen performans raporu"""
        results = (
            self.db.query(
                User.id,
                User.first_name,
                User.last_name,
                func.count(MaintenanceWorkOrder.id).label("completed_count"),
                func.sum(MaintenanceWorkOrder.actual_hours).label("total_hours"),
            )
            .join(MaintenanceWorkOrder, MaintenanceWorkOrder.assigned_to_id == User.id)
            .filter(
                MaintenanceWorkOrder.completed_date >= start_date,
                MaintenanceWorkOrder.completed_date <= end_date,
                MaintenanceWorkOrder.status == WorkOrderStatus.COMPLETED,
            )
            .group_by(User.id, User.first_name, User.last_name)
            .all()
        )

        return [
            {
                "user_id": r.id,
                "name": f"{r.first_name or ''} {r.last_name or ''}".strip() or "Bilinmiyor",
                "completed_count": r.completed_count,
                "total_hours": float(r.total_hours or 0),
                "avg_hours": float(r.total_hours or 0) / max(r.completed_count, 1),
                "success_rate": 100.0,  # Basitleştirilmiş
            }
            for r in results
        ]

    # ==================== SATINALMA ENTEGRASYONU ====================

    def create_purchase_request_for_part(
        self,
        work_order_id: int,
        item_id: int,
        quantity: float,
        requested_by_id: int = None,
    ) -> PurchaseRequest:
        """Parça için satınalma talebi oluşturur"""
        wo = self.db.query(MaintenanceWorkOrder).get(work_order_id)

        today_str = datetime.now().strftime("%Y%m%d")
        count = (
            self.db.query(PurchaseRequest)
            .filter(PurchaseRequest.request_no.like(f"PR-{today_str}-%"))
            .count()
        )
        request_no = f"PR-{today_str}-{count + 1:03d}"

        request = PurchaseRequest(
            request_no=request_no,
            request_date=datetime.now(),
            requested_by=f"Bakım Modülü (WO: {wo.order_no})",
            notes=f"Bakım İş Emri: {wo.order_no} için otomatik oluşturuldu.",
            priority=3,
        )
        self.db.add(request)
        self.db.flush()

        item = self.db.query(Item).get(item_id)
        pr_item = PurchaseRequestItem(
            request_id=request.id,
            item_id=item_id,
            quantity=quantity,
            unit_id=item.unit_id,
            estimated_price=item.purchase_price,
        )
        self.db.add(pr_item)
        self.db.commit()

        return request
