"""
Akıllı İş - Üretim Modülü Servisleri
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from database.base import get_session
from database.models.production import (
    BillOfMaterials, BOMLine, BOMOperation, BOMStatus,
    WorkStation, WorkStationType,
    WorkOrder, WorkOrderLine, WorkOrderOperation, 
    WorkOrderStatus, WorkOrderPriority
)
from database.models.inventory import Item, StockMovementType


class BOMService:
    """Ürün Reçetesi (BOM) servisi"""
    
    def __init__(self):
        self.session: Session = get_session()
        
    def close(self):
        if self.session:
            self.session.close()
            
    def get_all(self, status: BOMStatus = None, item_id: int = None) -> List[BillOfMaterials]:
        """Tüm reçeteleri getir"""
        query = self.session.query(BillOfMaterials).options(
            joinedload(BillOfMaterials.item),
            joinedload(BillOfMaterials.lines).joinedload(BOMLine.item)
        )
        
        if status:
            query = query.filter(BillOfMaterials.status == status)
        if item_id:
            query = query.filter(BillOfMaterials.item_id == item_id)
            
        return query.filter(BillOfMaterials.is_active == True).order_by(BillOfMaterials.code).all()
    
    def get_by_id(self, bom_id: int) -> Optional[BillOfMaterials]:
        """ID ile reçete getir"""
        return self.session.query(BillOfMaterials).options(
            joinedload(BillOfMaterials.item),
            joinedload(BillOfMaterials.lines).joinedload(BOMLine.item),
            joinedload(BillOfMaterials.operations).joinedload(BOMOperation.work_station)
        ).filter(BillOfMaterials.id == bom_id).first()
    
    def get_by_item(self, item_id: int, active_only: bool = True) -> List[BillOfMaterials]:
        """Ürüne ait reçeteleri getir"""
        query = self.session.query(BillOfMaterials).filter(BillOfMaterials.item_id == item_id)
        if active_only:
            query = query.filter(BillOfMaterials.status == BOMStatus.ACTIVE)
        return query.all()
    
    def get_active_bom(self, item_id: int) -> Optional[BillOfMaterials]:
        """Ürünün aktif reçetesini getir"""
        return self.session.query(BillOfMaterials).filter(
            BillOfMaterials.item_id == item_id,
            BillOfMaterials.status == BOMStatus.ACTIVE,
            BillOfMaterials.is_active == True
        ).first()
    
    def create(self, **kwargs) -> BillOfMaterials:
        """Yeni reçete oluştur"""
        lines_data = kwargs.pop('lines', [])
        operations_data = kwargs.pop('operations', [])
        
        bom = BillOfMaterials(**kwargs)
        self.session.add(bom)
        self.session.flush()
        
        # Satırları ekle
        for i, line_data in enumerate(lines_data):
            line_data['bom_id'] = bom.id
            line_data['line_no'] = i + 1
            line = BOMLine(**line_data)
            self.session.add(line)
            
        # Operasyonları ekle
        for op_data in operations_data:
            op_data['bom_id'] = bom.id
            op = BOMOperation(**op_data)
            self.session.add(op)
        
        self.session.commit()
        return bom
    
    def update(self, bom_id: int, **kwargs) -> Optional[BillOfMaterials]:
        """Reçete güncelle"""
        bom = self.get_by_id(bom_id)
        if not bom:
            return None
            
        lines_data = kwargs.pop('lines', None)
        operations_data = kwargs.pop('operations', None)
        
        for key, value in kwargs.items():
            if hasattr(bom, key):
                setattr(bom, key, value)
        
        # Satırları güncelle
        if lines_data is not None:
            # Mevcut satırları sil
            for line in bom.lines:
                self.session.delete(line)
            
            # Yeni satırları ekle
            for i, line_data in enumerate(lines_data):
                line_data['bom_id'] = bom.id
                line_data['line_no'] = i + 1
                line = BOMLine(**line_data)
                self.session.add(line)
        
        # Operasyonları güncelle
        if operations_data is not None:
            for op in bom.operations:
                self.session.delete(op)
            
            for op_data in operations_data:
                op_data['bom_id'] = bom.id
                op = BOMOperation(**op_data)
                self.session.add(op)
        
        self.session.commit()
        return bom
    
    def delete(self, bom_id: int, soft: bool = True) -> bool:
        """Reçete sil"""
        bom = self.get_by_id(bom_id)
        if not bom:
            return False
            
        if soft:
            bom.is_active = False
            bom.status = BOMStatus.OBSOLETE
        else:
            self.session.delete(bom)
            
        self.session.commit()
        return True
    
    def activate(self, bom_id: int) -> Optional[BillOfMaterials]:
        """Reçeteyi aktifleştir (diğerlerini pasifleştir)"""
        bom = self.get_by_id(bom_id)
        if not bom:
            return None
        
        # Aynı ürünün diğer aktif reçetelerini pasifleştir
        self.session.query(BillOfMaterials).filter(
            BillOfMaterials.item_id == bom.item_id,
            BillOfMaterials.id != bom_id,
            BillOfMaterials.status == BOMStatus.ACTIVE
        ).update({BillOfMaterials.status: BOMStatus.OBSOLETE})
        
        bom.status = BOMStatus.ACTIVE
        self.session.commit()
        return bom
    
    def copy(self, bom_id: int, new_code: str = None) -> Optional[BillOfMaterials]:
        """Reçeteyi kopyala"""
        original = self.get_by_id(bom_id)
        if not original:
            return None
        
        # Yeni reçete
        new_bom = BillOfMaterials(
            item_id=original.item_id,
            code=new_code or f"{original.code}_COPY",
            name=f"{original.name} (Kopya)",
            description=original.description,
            version=original.version + 1,
            status=BOMStatus.DRAFT,
            base_quantity=original.base_quantity,
            unit_id=original.unit_id,
            lead_time_days=original.lead_time_days,
            setup_time_minutes=original.setup_time_minutes,
            production_time_minutes=original.production_time_minutes,
            labor_cost=original.labor_cost,
            overhead_cost=original.overhead_cost,
        )
        self.session.add(new_bom)
        self.session.flush()
        
        # Satırları kopyala
        for line in original.lines:
            new_line = BOMLine(
                bom_id=new_bom.id,
                item_id=line.item_id,
                quantity=line.quantity,
                unit_id=line.unit_id,
                scrap_rate=line.scrap_rate,
                line_no=line.line_no,
                is_optional=line.is_optional,
                notes=line.notes,
            )
            self.session.add(new_line)
        
        # Operasyonları kopyala
        for op in original.operations:
            new_op = BOMOperation(
                bom_id=new_bom.id,
                operation_no=op.operation_no,
                name=op.name,
                description=op.description,
                work_station_id=op.work_station_id,
                setup_time=op.setup_time,
                run_time=op.run_time,
                wait_time=op.wait_time,
                move_time=op.move_time,
            )
            self.session.add(new_op)
        
        self.session.commit()
        return new_bom
    
    def calculate_cost(self, bom_id: int) -> dict:
        """Reçete maliyetini hesapla"""
        bom = self.get_by_id(bom_id)
        if not bom:
            return {}
        
        material_cost = Decimal(0)
        for line in bom.lines:
            if line.item and line.item.purchase_price:
                qty = line.effective_quantity
                material_cost += qty * line.item.purchase_price
        
        return {
            'material_cost': material_cost,
            'labor_cost': bom.labor_cost or Decimal(0),
            'overhead_cost': bom.overhead_cost or Decimal(0),
            'total_cost': material_cost + (bom.labor_cost or Decimal(0)) + (bom.overhead_cost or Decimal(0)),
        }
    
    def generate_code(self) -> str:
        """Otomatik reçete kodu üret"""
        last = self.session.query(BillOfMaterials).order_by(BillOfMaterials.id.desc()).first()
        if last:
            num = last.id + 1
        else:
            num = 1
        return f"BOM{num:06d}"


class WorkStationService:
    """İş İstasyonu servisi"""
    
    def __init__(self):
        self.session: Session = get_session()
        
    def close(self):
        if self.session:
            self.session.close()
            
    def get_all(self, active_only: bool = True) -> List[WorkStation]:
        """Tüm iş istasyonlarını getir"""
        query = self.session.query(WorkStation)
        if active_only:
            query = query.filter(WorkStation.is_active == True)
        return query.order_by(WorkStation.code).all()
    
    def get_by_id(self, station_id: int) -> Optional[WorkStation]:
        """ID ile iş istasyonu getir"""
        return self.session.query(WorkStation).filter(WorkStation.id == station_id).first()
    
    def create(self, **kwargs) -> WorkStation:
        """Yeni iş istasyonu oluştur"""
        station = WorkStation(**kwargs)
        self.session.add(station)
        self.session.commit()
        return station
    
    def update(self, station_id: int, **kwargs) -> Optional[WorkStation]:
        """İş istasyonu güncelle"""
        station = self.get_by_id(station_id)
        if not station:
            return None
        
        for key, value in kwargs.items():
            if hasattr(station, key):
                setattr(station, key, value)
        
        self.session.commit()
        return station
    
    def delete(self, station_id: int, soft: bool = True) -> bool:
        """İş istasyonu sil"""
        station = self.get_by_id(station_id)
        if not station:
            return False
        
        if soft:
            station.is_active = False
        else:
            self.session.delete(station)
        
        self.session.commit()
        return True


class WorkOrderService:
    """İş Emri servisi"""
    
    def __init__(self):
        self.session: Session = get_session()
        
    def close(self):
        if self.session:
            self.session.close()
            
    def get_all(self, status: WorkOrderStatus = None, item_id: int = None) -> List[WorkOrder]:
        """Tüm iş emirlerini getir"""
        query = self.session.query(WorkOrder).options(
            joinedload(WorkOrder.item),
            joinedload(WorkOrder.bom)
        )
        
        if status:
            query = query.filter(WorkOrder.status == status)
        if item_id:
            query = query.filter(WorkOrder.item_id == item_id)
            
        return query.filter(WorkOrder.is_active == True).order_by(WorkOrder.created_at.desc()).all()
    
    def get_by_id(self, order_id: int) -> Optional[WorkOrder]:
        """ID ile iş emri getir"""
        return self.session.query(WorkOrder).options(
            joinedload(WorkOrder.item),
            joinedload(WorkOrder.bom),
            joinedload(WorkOrder.lines).joinedload(WorkOrderLine.item),
            joinedload(WorkOrder.operations)
        ).filter(WorkOrder.id == order_id).first()
    
    def create(self, **kwargs) -> WorkOrder:
        """Yeni iş emri oluştur"""
        # BOM'dan satırları ve operasyonları otomatik oluştur
        bom_id = kwargs.get('bom_id')
        planned_quantity = kwargs.get('planned_quantity', Decimal(1))
        
        order = WorkOrder(**kwargs)
        self.session.add(order)
        self.session.flush()
        
        # BOM varsa satırları ve operasyonları kopyala
        if bom_id:
            bom = self.session.query(BillOfMaterials).options(
                joinedload(BillOfMaterials.lines),
                joinedload(BillOfMaterials.operations)
            ).filter(BillOfMaterials.id == bom_id).first()
            
            if bom:
                # Malzeme satırlarını oluştur
                multiplier = planned_quantity / (bom.base_quantity or Decimal(1))
                
                for line in bom.lines:
                    wo_line = WorkOrderLine(
                        work_order_id=order.id,
                        bom_line_id=line.id,
                        item_id=line.item_id,
                        required_quantity=line.effective_quantity * multiplier,
                        unit_id=line.unit_id,
                        unit_cost=line.item.purchase_price if line.item else Decimal(0),
                    )
                    wo_line.line_cost = wo_line.required_quantity * wo_line.unit_cost
                    self.session.add(wo_line)
                
                # Operasyonları oluştur
                for op in bom.operations:
                    wo_op = WorkOrderOperation(
                        work_order_id=order.id,
                        bom_operation_id=op.id,
                        operation_no=op.operation_no,
                        name=op.name,
                        work_station_id=op.work_station_id,
                        planned_setup_time=op.setup_time,
                        planned_run_time=int(op.run_time * float(planned_quantity)),
                    )
                    self.session.add(wo_op)
                
                # Planlanan maliyetleri hesapla
                order.planned_material_cost = bom.total_material_cost * multiplier
                order.planned_labor_cost = bom.labor_cost * multiplier if bom.labor_cost else Decimal(0)
                order.planned_overhead_cost = bom.overhead_cost * multiplier if bom.overhead_cost else Decimal(0)
        
        self.session.commit()
        return order
    
    def update(self, order_id: int, **kwargs) -> Optional[WorkOrder]:
        """İş emri güncelle"""
        order = self.get_by_id(order_id)
        if not order:
            return None
        
        for key, value in kwargs.items():
            if hasattr(order, key):
                setattr(order, key, value)
        
        self.session.commit()
        return order
    
    def change_status(self, order_id: int, new_status: WorkOrderStatus) -> Optional[WorkOrder]:
        """İş emri durumunu değiştir"""
        order = self.get_by_id(order_id)
        if not order:
            return None
        
        old_status = order.status
        order.status = new_status
        
        # Durum değişikliğine göre tarih güncelle
        now = datetime.now()
        if new_status == WorkOrderStatus.RELEASED:
            order.released_at = now
        elif new_status == WorkOrderStatus.IN_PROGRESS and not order.actual_start:
            order.actual_start = now
        elif new_status in [WorkOrderStatus.COMPLETED, WorkOrderStatus.CLOSED]:
            if not order.actual_end:
                order.actual_end = now
        
        self.session.commit()
        return order
    
    def delete(self, order_id: int, soft: bool = True) -> bool:
        """İş emri sil"""
        order = self.get_by_id(order_id)
        if not order:
            return False
        
        # Sadece taslak durumundayken silinebilir
        if order.status != WorkOrderStatus.DRAFT:
            return False
        
        if soft:
            order.is_active = False
            order.status = WorkOrderStatus.CANCELLED
        else:
            self.session.delete(order)
        
        self.session.commit()
        return True
    
    def generate_order_no(self) -> str:
        """Otomatik iş emri numarası üret"""
        today = datetime.now()
        prefix = f"WO{today.strftime('%Y%m')}"
        
        last = self.session.query(WorkOrder).filter(
            WorkOrder.order_no.like(f"{prefix}%")
        ).order_by(WorkOrder.order_no.desc()).first()
        
        if last:
            try:
                num = int(last.order_no[-4:]) + 1
            except:
                num = 1
        else:
            num = 1
        
        return f"{prefix}{num:04d}"
