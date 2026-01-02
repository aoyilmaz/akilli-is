"""
Akıllı İş - Üretim Modülü Servisleri
V3 - MODEL UYUMLU STOK ENTEGRASYONU

DÜZELTMELER (V2 -> V3):
- scrap_quantity → scrapped_quantity
- actual_quantity → completed_quantity  
- warehouse_id → source_warehouse_id
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
from database.models.inventory import Item, Warehouse, StockMovement, StockMovementType, StockBalance


# ============================================================
# CUSTOM EXCEPTIONS
# ============================================================

class ProductionError(Exception):
    """Üretim hatası base class"""
    pass


class InsufficientMaterialError(ProductionError):
    """Yetersiz malzeme hatası"""
    def __init__(self, item_code: str, required: Decimal, available: Decimal):
        self.item_code = item_code
        self.required = required
        self.available = available
        super().__init__(
            f"Yetersiz malzeme! {item_code}: Gerekli {required}, Mevcut {available}"
        )


class InvalidStatusTransitionError(ProductionError):
    """Geçersiz durum geçişi hatası"""
    def __init__(self, current: str, target: str):
        super().__init__(f"Geçersiz durum geçişi: {current} → {target}")


# ============================================================
# BOM SERVICE (Ürün Reçetesi)
# ============================================================

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
        
        # ACTIVE BOM düzenlenemez - kopyalanmalı
        if bom.status == BOMStatus.ACTIVE:
            raise ProductionError("Aktif reçete düzenlenemez! Önce kopyalayın.")
            
        lines_data = kwargs.pop('lines', None)
        operations_data = kwargs.pop('operations', None)
        
        for key, value in kwargs.items():
            if hasattr(bom, key):
                setattr(bom, key, value)
        
        # Satırları güncelle
        if lines_data is not None:
            for line in bom.lines:
                self.session.delete(line)
            
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
        """Reçeteyi kopyala (yeni versiyon)"""
        original = self.get_by_id(bom_id)
        if not original:
            return None
        
        # Yeni reçete
        new_bom = BillOfMaterials(
            item_id=original.item_id,
            code=new_code or f"{original.code}_V{original.version + 1}",
            name=f"{original.name}",
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


# ============================================================
# WORKSTATION SERVICE (İş İstasyonu)
# ============================================================

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


# ============================================================
# WORKORDER SERVICE (İş Emri) - STOK ENTEGRASYONLU
# ============================================================

class WorkOrderService:
    """
    İş Emri servisi - STOK ENTEGRASYONLU
    
    Durum Geçişleri:
    - DRAFT: Taslak, düzenlenebilir
    - PLANNED: Planlandı, malzeme rezervasyonu yapılabilir
    - RELEASED: Serbest bırakıldı, üretime hazır
    - IN_PROGRESS: Üretimde, malzemeler stoktan düşüldü
    - COMPLETED: Tamamlandı, mamül stoka girdi
    - CLOSED: Kapatıldı
    - CANCELLED: İptal edildi
    """
    
    def __init__(self):
        self.session: Session = get_session()
        
    def close(self):
        if self.session:
            self.session.close()
    
    # ----------------------------------------------------------
    # TEMEL CRUD İŞLEMLERİ
    # ----------------------------------------------------------
            
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
        bom_id = kwargs.get('bom_id')
        planned_quantity = kwargs.get('planned_quantity', Decimal(1))
        
        order = WorkOrder(**kwargs)
        self.session.add(order)
        self.session.flush()
        
        # BOM varsa satırları ve operasyonları kopyala
        if bom_id:
            self._create_lines_from_bom(order, bom_id, planned_quantity)
        
        self.session.commit()
        return order
    
    def _create_lines_from_bom(self, order: WorkOrder, bom_id: int, planned_quantity: Decimal):
        """BOM'dan iş emri satırlarını oluştur"""
        bom = self.session.query(BillOfMaterials).options(
            joinedload(BillOfMaterials.lines).joinedload(BOMLine.item),
            joinedload(BillOfMaterials.operations)
        ).filter(BillOfMaterials.id == bom_id).first()
        
        if not bom:
            return
        
        multiplier = planned_quantity / (bom.base_quantity or Decimal(1))
        
        # Malzeme satırlarını oluştur
        for line in bom.lines:
            wo_line = WorkOrderLine(
                work_order_id=order.id,
                bom_line_id=line.id,
                item_id=line.item_id,
                required_quantity=line.effective_quantity * multiplier,
                issued_quantity=Decimal(0),  # Henüz çıkış yapılmadı
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
        if bom.total_material_cost:
            order.planned_material_cost = bom.total_material_cost * multiplier
        order.planned_labor_cost = (bom.labor_cost or Decimal(0)) * multiplier
        order.planned_overhead_cost = (bom.overhead_cost or Decimal(0)) * multiplier
    
    def update(self, order_id: int, **kwargs) -> Optional[WorkOrder]:
        """İş emri güncelle"""
        order = self.get_by_id(order_id)
        if not order:
            return None
        
        # Sadece DRAFT ve PLANNED durumda güncellenebilir
        if order.status not in [WorkOrderStatus.DRAFT, WorkOrderStatus.PLANNED]:
            raise ProductionError(f"Bu durumda ({order.status.value}) iş emri güncellenemez!")
        
        for key, value in kwargs.items():
            if hasattr(order, key):
                setattr(order, key, value)
        
        self.session.commit()
        return order
    
    def delete(self, order_id: int, soft: bool = True) -> bool:
        """İş emri sil"""
        order = self.get_by_id(order_id)
        if not order:
            return False
        
        if order.status not in [WorkOrderStatus.DRAFT, WorkOrderStatus.PLANNED]:
            return False
        
        if soft:
            order.is_active = False
            order.status = WorkOrderStatus.CANCELLED
        else:
            self.session.delete(order)
        
        self.session.commit()
        return True
    
    # ----------------------------------------------------------
    # DURUM GEÇİŞLERİ - STOK ENTEGRASYONLU
    # ----------------------------------------------------------
    
    def release(self, order_id: int) -> WorkOrder:
        """
        İş emrini serbest bırak (RELEASED)
        Malzeme kontrolü yapar ama stok düşmez
        """
        order = self.get_by_id(order_id)
        if not order:
            raise ProductionError("İş emri bulunamadı!")
        
        if order.status not in [WorkOrderStatus.DRAFT, WorkOrderStatus.PLANNED]:
            raise InvalidStatusTransitionError(order.status.value, "RELEASED")
        
        # NOT: Stok kontrolü burada yapılmaz, start_production'da yapılır
        # self._check_material_availability(order)  # Kaldırıldı
        
        order.status = WorkOrderStatus.RELEASED
        order.released_at = datetime.now()
        
        self.session.commit()
        return order
    
    def start_production(self, order_id: int, warehouse_id: int) -> WorkOrder:
        """
        Üretimi başlat (IN_PROGRESS)
        
        KRİTİK: Malzemeleri stoktan düşer!
        - Tüm malzeme satırları için URETIM_GIRIS hareketi oluşturur
        - Yetersiz stok varsa hata fırlatır
        """
        order = self.get_by_id(order_id)
        if not order:
            raise ProductionError("İş emri bulunamadı!")
        
        if order.status != WorkOrderStatus.RELEASED:
            raise InvalidStatusTransitionError(order.status.value, "IN_PROGRESS")
        
        warehouse = self.session.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        if not warehouse:
            raise ProductionError("Depo bulunamadı!")
        
        try:
            # === TRANSACTION BAŞLANGICI ===
            
            # Malzeme yeterliliği son kontrol
            self._check_material_availability(order, warehouse_id)
            
            # Malzemeleri stoktan düş
            actual_material_cost = Decimal(0)
            
            for line in order.lines:
                if line.required_quantity <= 0:
                    continue
                
                # Stok bakiyesini al
                balance = self._get_balance(line.item_id, warehouse_id)
                current_cost = balance.unit_cost if balance else (line.unit_cost or Decimal(0))
                
                # Stok hareketi oluştur (URETIM_GIRIS = üretim için malzeme çıkışı)
                movement = StockMovement(
                    item_id=line.item_id,
                    movement_type=StockMovementType.URETIM_GIRIS,
                    quantity=line.required_quantity,
                    unit_price=current_cost,
                    total_price=line.required_quantity * current_cost,
                    from_warehouse_id=warehouse_id,
                    document_no=order.order_no,
                    document_type="work_order",
                    description=f"İş Emri: {order.order_no} - Malzeme çıkışı",
                    movement_date=datetime.now(),
                )
                self.session.add(movement)
                
                # Bakiyeyi güncelle
                if balance:
                    balance.quantity -= line.required_quantity
                    if balance.quantity < 0:
                        balance.quantity = Decimal(0)
                
                # İş emri satırını güncelle
                line.issued_quantity = line.required_quantity
                line.actual_unit_cost = current_cost
                line.actual_line_cost = line.required_quantity * current_cost
                
                actual_material_cost += line.actual_line_cost
            
            # İş emrini güncelle
            order.status = WorkOrderStatus.IN_PROGRESS
            order.actual_start = datetime.now()
            order.source_warehouse_id = warehouse_id  # DÜZELTME: warehouse_id → source_warehouse_id
            order.actual_material_cost = actual_material_cost
            
            # Transaction'ı tamamla
            self.session.commit()
            
            return order
            
        except Exception as e:
            self.session.rollback()
            raise e
    
    def complete_production(
        self, 
        order_id: int, 
        completed_quantity: Decimal,
        scrap_quantity: Decimal = Decimal(0),
        target_warehouse_id: int = None
    ) -> WorkOrder:
        """
        Üretimi tamamla (COMPLETED)
        
        KRİTİK: Mamülü stoka ekler!
        - Üretilen mamül için URETIM_CIKIS hareketi oluşturur
        - Fire varsa FIRE hareketi oluşturur
        - Actual değerleri hesaplar
        """
        order = self.get_by_id(order_id)
        if not order:
            raise ProductionError("İş emri bulunamadı!")
        
        if order.status != WorkOrderStatus.IN_PROGRESS:
            raise InvalidStatusTransitionError(order.status.value, "COMPLETED")
        
        if completed_quantity <= 0:
            raise ProductionError("Tamamlanan miktar sıfırdan büyük olmalı!")
        
        # Hedef depo (belirtilmezse kaynak depo kullan)
        warehouse_id = target_warehouse_id or order.target_warehouse_id or order.source_warehouse_id
        if not warehouse_id:
            raise ProductionError("Hedef depo belirtilmeli!")
        
        try:
            # === TRANSACTION BAŞLANGICI ===
            
            # Birim maliyet hesapla
            total_cost = (
                (order.actual_material_cost or Decimal(0)) +
                (order.actual_labor_cost or order.planned_labor_cost or Decimal(0)) +
                (order.actual_overhead_cost or order.planned_overhead_cost or Decimal(0))
            )
            unit_cost = total_cost / completed_quantity if completed_quantity > 0 else Decimal(0)
            
            # Mamül stok girişi (URETIM_CIKIS = üretimden mamül girişi)
            movement = StockMovement(
                item_id=order.item_id,
                movement_type=StockMovementType.URETIM_CIKIS,
                quantity=completed_quantity,
                unit_price=unit_cost,
                total_price=completed_quantity * unit_cost,
                to_warehouse_id=warehouse_id,
                document_no=order.order_no,
                document_type="work_order",
                description=f"İş Emri: {order.order_no} - Mamül girişi",
                movement_date=datetime.now(),
            )
            self.session.add(movement)
            
            # Bakiyeyi güncelle (mamül için)
            balance = self._get_or_create_balance(order.item_id, warehouse_id)
            old_qty = balance.quantity
            old_cost = balance.unit_cost
            new_qty = old_qty + completed_quantity
            
            # Ağırlıklı ortalama maliyet
            if new_qty > 0:
                balance.unit_cost = ((old_qty * old_cost) + (completed_quantity * unit_cost)) / new_qty
            balance.quantity = new_qty
            
            # Fire varsa
            if scrap_quantity > 0:
                scrap_movement = StockMovement(
                    item_id=order.item_id,
                    movement_type=StockMovementType.FIRE,
                    quantity=scrap_quantity,
                    unit_price=unit_cost,
                    total_price=scrap_quantity * unit_cost,
                    from_warehouse_id=warehouse_id,
                    document_no=order.order_no,
                    document_type="work_order",
                    description=f"İş Emri: {order.order_no} - Üretim firesi",
                    movement_date=datetime.now(),
                )
                self.session.add(scrap_movement)
            
            # İş emrini güncelle - DÜZELTMELER
            order.status = WorkOrderStatus.COMPLETED
            order.actual_end = datetime.now()
            order.completed_quantity = completed_quantity  # DÜZELTME: actual_quantity → completed_quantity
            order.scrapped_quantity = scrap_quantity       # DÜZELTME: scrap_quantity → scrapped_quantity
            order.actual_unit_cost = unit_cost
            order.target_warehouse_id = warehouse_id
            
            # Verimlilik hesapla
            if order.planned_quantity > 0:
                order.efficiency_rate = (completed_quantity / order.planned_quantity) * 100
            
            # Transaction'ı tamamla
            self.session.commit()
            
            return order
            
        except Exception as e:
            self.session.rollback()
            raise e
    
    def cancel_production(self, order_id: int) -> WorkOrder:
        """
        Üretimi iptal et
        
        NOT: IN_PROGRESS durumundaysa stok geri yüklenmez!
        Manuel düzeltme gerekir.
        """
        order = self.get_by_id(order_id)
        if not order:
            raise ProductionError("İş emri bulunamadı!")
        
        if order.status in [WorkOrderStatus.COMPLETED, WorkOrderStatus.CLOSED]:
            raise ProductionError("Tamamlanmış veya kapatılmış iş emri iptal edilemez!")
        
        order.status = WorkOrderStatus.CANCELLED
        order.actual_end = datetime.now()
        
        self.session.commit()
        return order
    
    def close_order(self, order_id: int) -> WorkOrder:
        """İş emrini kapat (CLOSED)"""
        order = self.get_by_id(order_id)
        if not order:
            raise ProductionError("İş emri bulunamadı!")
        
        if order.status != WorkOrderStatus.COMPLETED:
            raise InvalidStatusTransitionError(order.status.value, "CLOSED")
        
        order.status = WorkOrderStatus.CLOSED
        self.session.commit()
        return order
    
    # ----------------------------------------------------------
    # FIRE (HURDA) YÖNETİMİ
    # ----------------------------------------------------------
    
    def report_scrap(
        self, 
        order_id: int, 
        item_id: int, 
        quantity: Decimal, 
        reason: str = None
    ) -> StockMovement:
        """
        Üretim sırasında fire/hurda bildir
        
        - Malzeme veya yarı mamül firesi olabilir
        - FIRE hareketi oluşturur
        """
        order = self.get_by_id(order_id)
        if not order:
            raise ProductionError("İş emri bulunamadı!")
        
        if order.status != WorkOrderStatus.IN_PROGRESS:
            raise ProductionError("Fire sadece üretim sırasında bildirilebilir!")
        
        if not order.source_warehouse_id:  # DÜZELTME: warehouse_id → source_warehouse_id
            raise ProductionError("İş emrinde depo bilgisi yok!")
        
        # Fire hareketi
        movement = StockMovement(
            item_id=item_id,
            movement_type=StockMovementType.FIRE,
            quantity=quantity,
            unit_price=Decimal(0),  # Fire maliyeti hesaplanabilir
            total_price=Decimal(0),
            from_warehouse_id=order.source_warehouse_id,  # DÜZELTME
            document_no=order.order_no,
            document_type="work_order_scrap",
            description=f"İş Emri Fire: {reason or 'Belirtilmedi'}",
            movement_date=datetime.now(),
        )
        self.session.add(movement)
        
        # Bakiyeyi güncelle
        balance = self._get_balance(item_id, order.source_warehouse_id)  # DÜZELTME
        if balance:
            balance.quantity -= quantity
            if balance.quantity < 0:
                balance.quantity = Decimal(0)
        
        self.session.commit()
        return movement
    
    # ----------------------------------------------------------
    # OPERASYON TAKİBİ
    # ----------------------------------------------------------
    
    def start_operation(self, operation_id: int) -> WorkOrderOperation:
        """Operasyonu başlat"""
        op = self.session.query(WorkOrderOperation).filter(
            WorkOrderOperation.id == operation_id
        ).first()
        
        if not op:
            raise ProductionError("Operasyon bulunamadı!")
        
        op.actual_start = datetime.now()
        op.status = "in_progress"
        
        self.session.commit()
        return op
    
    def complete_operation(
        self, 
        operation_id: int, 
        actual_run_time: int = None
    ) -> WorkOrderOperation:
        """Operasyonu tamamla"""
        op = self.session.query(WorkOrderOperation).filter(
            WorkOrderOperation.id == operation_id
        ).first()
        
        if not op:
            raise ProductionError("Operasyon bulunamadı!")
        
        op.actual_end = datetime.now()
        op.status = "completed"
        
        if actual_run_time:
            op.actual_run_time = actual_run_time
        elif op.actual_start:
            # Otomatik hesapla
            delta = op.actual_end - op.actual_start
            op.actual_run_time = int(delta.total_seconds() / 60)
        
        self.session.commit()
        return op
    
    # ----------------------------------------------------------
    # YARDIMCI METODLAR
    # ----------------------------------------------------------
    
    def _check_material_availability(self, order: WorkOrder, warehouse_id: int = None):
        """Malzeme yeterliliği kontrolü"""
        for line in order.lines:
            if line.required_quantity <= 0:
                continue
            
            if warehouse_id:
                balance = self._get_balance(line.item_id, warehouse_id)
                available = balance.quantity if balance else Decimal(0)
            else:
                # Tüm depolardaki toplam
                available = self._get_total_stock(line.item_id)
            
            if available < line.required_quantity:
                item = self.session.query(Item).filter(Item.id == line.item_id).first()
                raise InsufficientMaterialError(
                    item.code if item else str(line.item_id),
                    line.required_quantity,
                    available
                )
    
    def _get_balance(self, item_id: int, warehouse_id: int) -> Optional[StockBalance]:
        """Stok bakiyesi getir"""
        return self.session.query(StockBalance).filter(
            StockBalance.item_id == item_id,
            StockBalance.warehouse_id == warehouse_id
        ).first()
    
    def _get_or_create_balance(self, item_id: int, warehouse_id: int) -> StockBalance:
        """Stok bakiyesi getir veya oluştur"""
        balance = self._get_balance(item_id, warehouse_id)
        if not balance:
            balance = StockBalance(
                item_id=item_id,
                warehouse_id=warehouse_id,
                quantity=Decimal(0),
                unit_cost=Decimal(0),
            )
            self.session.add(balance)
        return balance
    
    def _get_total_stock(self, item_id: int) -> Decimal:
        """Tüm depolardaki toplam stok"""
        from sqlalchemy import func
        result = self.session.query(func.sum(StockBalance.quantity)).filter(
            StockBalance.item_id == item_id
        ).scalar()
        return result or Decimal(0)
    
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
    
    # ----------------------------------------------------------
    # RAPORLAMA
    # ----------------------------------------------------------
    
    def get_production_summary(self, order_id: int) -> dict:
        """Üretim özeti"""
        order = self.get_by_id(order_id)
        if not order:
            return {}
        
        return {
            "order_no": order.order_no,
            "item": order.item.name if order.item else "",
            "status": order.status.value,
            "planned_quantity": float(order.planned_quantity),
            "completed_quantity": float(order.completed_quantity or 0),  # DÜZELTME
            "scrapped_quantity": float(order.scrapped_quantity or 0),    # DÜZELTME
            "efficiency_rate": float(order.efficiency_rate or 0),
            "planned_cost": {
                "material": float(order.planned_material_cost or 0),
                "labor": float(order.planned_labor_cost or 0),
                "overhead": float(order.planned_overhead_cost or 0),
                "total": float(
                    (order.planned_material_cost or 0) +
                    (order.planned_labor_cost or 0) +
                    (order.planned_overhead_cost or 0)
                ),
            },
            "actual_cost": {
                "material": float(order.actual_material_cost or 0),
                "labor": float(order.actual_labor_cost or 0),
                "overhead": float(order.actual_overhead_cost or 0),
                "total": float(
                    (order.actual_material_cost or 0) +
                    (order.actual_labor_cost or 0) +
                    (order.actual_overhead_cost or 0)
                ),
            },
            "variance": {
                "material": float(
                    (order.actual_material_cost or 0) - (order.planned_material_cost or 0)
                ),
                "quantity": float(
                    (order.completed_quantity or 0) - order.planned_quantity  # DÜZELTME
                ),
            },
            "duration": {
                "planned_start": order.planned_start.isoformat() if order.planned_start else None,
                "planned_end": order.planned_end.isoformat() if order.planned_end else None,
                "actual_start": order.actual_start.isoformat() if order.actual_start else None,
                "actual_end": order.actual_end.isoformat() if order.actual_end else None,
            },
        }

    def change_status(self, order_id: int, new_status: WorkOrderStatus) -> WorkOrder:
        """
        İş emri durumunu değiştir (UI için basit metod)
        
        Geçerli geçişler:
        - DRAFT → PLANNED
        - PLANNED → RELEASED
        - RELEASED → IN_PROGRESS (start_production kullan)
        - IN_PROGRESS → COMPLETED (complete_production kullan)
        - COMPLETED → CLOSED
        """
        order = self.get_by_id(order_id)
        if not order:
            raise ProductionError("İş emri bulunamadı!")
        
        current = order.status
        
        # Geçiş kuralları
        valid_transitions = {
            WorkOrderStatus.DRAFT: [WorkOrderStatus.PLANNED, WorkOrderStatus.CANCELLED],
            WorkOrderStatus.PLANNED: [WorkOrderStatus.RELEASED, WorkOrderStatus.DRAFT, WorkOrderStatus.CANCELLED],
            WorkOrderStatus.RELEASED: [WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.PLANNED, WorkOrderStatus.CANCELLED],
            WorkOrderStatus.IN_PROGRESS: [WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED],
            WorkOrderStatus.COMPLETED: [WorkOrderStatus.CLOSED],
            WorkOrderStatus.CLOSED: [],
            WorkOrderStatus.CANCELLED: [],
        }
        
        if new_status not in valid_transitions.get(current, []):
            raise InvalidStatusTransitionError(current.value, new_status.value)
        
        # Özel durumlar
        if new_status == WorkOrderStatus.RELEASED:
            return self.release(order_id)
        elif new_status == WorkOrderStatus.CLOSED:
            return self.close_order(order_id)
        elif new_status == WorkOrderStatus.CANCELLED:
            return self.cancel_production(order_id)
        
        # Basit durum değişiklikleri
        order.status = new_status
        
        if new_status == WorkOrderStatus.PLANNED:
            order.released_at = None
        
        self.session.commit()
        return order
