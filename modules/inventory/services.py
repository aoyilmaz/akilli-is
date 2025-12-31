"""
Akıllı İş - Stok Modülü Servisleri
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_session
from database.models import (
    Item, ItemCategory, Unit, Warehouse,
    StockBalance, StockMovement,
    ItemType, StockMovementType
)


class ItemService:
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
    
    def get_all(self, active_only: bool = True) -> List[Item]:
        query = self.session.query(Item)
        if active_only:
            query = query.filter(Item.is_active == True)
        return query.order_by(Item.code).all()
    
    def get_by_id(self, item_id: int) -> Optional[Item]:
        return self.session.query(Item).filter(Item.id == item_id).first()
    
    def get_by_code(self, code: str) -> Optional[Item]:
        return self.session.query(Item).filter(Item.code == code).first()
    
    def search(self, keyword: str = "", item_type: Optional[ItemType] = None,
               category_id: Optional[int] = None, limit: int = 100) -> List[Item]:
        query = self.session.query(Item).filter(Item.is_active == True)
        if keyword:
            search = f"%{keyword}%"
            query = query.filter(or_(
                Item.code.ilike(search),
                Item.name.ilike(search),
                Item.barcode.ilike(search),
            ))
        if item_type:
            query = query.filter(Item.item_type == item_type)
        if category_id:
            query = query.filter(Item.category_id == category_id)
        return query.order_by(Item.code).limit(limit).all()
    
    def create(self, **kwargs) -> Item:
        item = Item(**kwargs)
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item
    
    def update(self, item_id: int, **kwargs) -> Optional[Item]:
        item = self.get_by_id(item_id)
        if item:
            for key, value in kwargs.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            self.session.commit()
            self.session.refresh(item)
        return item
    
    def delete(self, item_id: int, soft: bool = True) -> bool:
        item = self.get_by_id(item_id)
        if item:
            if soft:
                item.is_active = False
            else:
                self.session.delete(item)
            self.session.commit()
            return True
        return False
    
    def get_next_code(self, prefix: str = "STK") -> str:
        last = self.session.query(Item).filter(
            Item.code.like(f"{prefix}%")
        ).order_by(Item.code.desc()).first()
        if last:
            try:
                num = int(last.code.replace(prefix, "")) + 1
            except:
                num = 1
        else:
            num = 1
        return f"{prefix}{num:06d}"
    
    def close(self):
        self.session.close()


class CategoryService:
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
    
    def get_all(self, active_only: bool = True) -> List[ItemCategory]:
        query = self.session.query(ItemCategory)
        if active_only:
            query = query.filter(ItemCategory.is_active == True)
        return query.order_by(ItemCategory.name).all()
    
    def get_by_id(self, category_id: int) -> Optional[ItemCategory]:
        return self.session.query(ItemCategory).filter(ItemCategory.id == category_id).first()
    
    def create(self, **kwargs) -> ItemCategory:
        cat = ItemCategory(**kwargs)
        self.session.add(cat)
        self.session.commit()
        self.session.refresh(cat)
        return cat
    
    def update(self, category_id: int, **kwargs) -> Optional[ItemCategory]:
        cat = self.get_by_id(category_id)
        if cat:
            for key, value in kwargs.items():
                if hasattr(cat, key):
                    setattr(cat, key, value)
            self.session.commit()
            self.session.refresh(cat)
        return cat
    
    def delete(self, category_id: int, soft: bool = True) -> bool:
        cat = self.get_by_id(category_id)
        if cat:
            if soft:
                cat.is_active = False
            else:
                self.session.delete(cat)
            self.session.commit()
            return True
        return False
    
    def close(self):
        self.session.close()


class UnitService:
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
    
    def get_all(self, active_only: bool = True) -> List[Unit]:
        query = self.session.query(Unit)
        if active_only:
            query = query.filter(Unit.is_active == True)
        return query.order_by(Unit.name).all()
    
    def get_by_id(self, unit_id: int) -> Optional[Unit]:
        return self.session.query(Unit).filter(Unit.id == unit_id).first()
    
    def close(self):
        self.session.close()


class WarehouseService:
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
    
    def get_all(self, active_only: bool = True) -> List[Warehouse]:
        query = self.session.query(Warehouse)
        if active_only:
            query = query.filter(Warehouse.is_active == True)
        return query.order_by(Warehouse.name).all()
    
    def get_by_id(self, warehouse_id: int) -> Optional[Warehouse]:
        return self.session.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    
    def get_default(self) -> Optional[Warehouse]:
        return self.session.query(Warehouse).filter(
            Warehouse.is_active == True,
            Warehouse.is_default == True
        ).first()
    
    def create(self, **kwargs) -> Warehouse:
        wh = Warehouse(**kwargs)
        self.session.add(wh)
        self.session.commit()
        self.session.refresh(wh)
        return wh
    
    def update(self, warehouse_id: int, **kwargs) -> Optional[Warehouse]:
        wh = self.get_by_id(warehouse_id)
        if wh:
            for key, value in kwargs.items():
                if hasattr(wh, key):
                    setattr(wh, key, value)
            self.session.commit()
            self.session.refresh(wh)
        return wh
    
    def delete(self, warehouse_id: int, soft: bool = True) -> bool:
        wh = self.get_by_id(warehouse_id)
        if wh:
            if soft:
                wh.is_active = False
            else:
                self.session.delete(wh)
            self.session.commit()
            return True
        return False
    
    def close(self):
        self.session.close()


class StockMovementService:
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()
    
    def create_movement(
        self,
        item_id: int,
        movement_type: StockMovementType,
        quantity: Decimal,
        to_warehouse_id: Optional[int] = None,
        from_warehouse_id: Optional[int] = None,
        unit_price: Decimal = Decimal(0),
        document_no: Optional[str] = None,
        document_type: Optional[str] = None,
        description: Optional[str] = None,
        lot_number: Optional[str] = None,
        **kwargs
    ) -> StockMovement:
        item = self.session.query(Item).filter(Item.id == item_id).first()
        if not item:
            raise ValueError(f"Stok kartı bulunamadı: {item_id}")
        
        movement = StockMovement(
            item_id=item_id,
            item_code=item.code,
            item_name=item.name,
            movement_type=movement_type,
            quantity=quantity,
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            unit_id=item.unit_id,
            unit_price=unit_price,
            total_price=quantity * unit_price,
            document_no=document_no,
            document_type=document_type,
            description=description,
            lot_number=lot_number,
            movement_date=datetime.now(),
            **kwargs
        )
        self.session.add(movement)
        
        # Bakiyeleri güncelle
        if movement_type in [StockMovementType.GIRIS, StockMovementType.SATIN_ALMA,
                            StockMovementType.URETIM_GIRIS, StockMovementType.IADE_SATIS,
                            StockMovementType.SAYIM_FAZLA]:
            self._update_balance(item_id, to_warehouse_id, quantity, unit_price, lot_number)
        elif movement_type in [StockMovementType.CIKIS, StockMovementType.SATIS,
                              StockMovementType.URETIM_CIKIS, StockMovementType.IADE_ALIS,
                              StockMovementType.SAYIM_EKSIK, StockMovementType.FIRE]:
            self._update_balance(item_id, from_warehouse_id, -quantity, unit_price, lot_number)
        elif movement_type == StockMovementType.TRANSFER:
            self._update_balance(item_id, from_warehouse_id, -quantity, unit_price, lot_number)
            self._update_balance(item_id, to_warehouse_id, quantity, unit_price, lot_number)
        
        self.session.commit()
        self.session.refresh(movement)
        return movement
    
    def _update_balance(self, item_id: int, warehouse_id: int, quantity: Decimal,
                        unit_cost: Decimal = Decimal(0), lot_number: Optional[str] = None):
        balance = self.session.query(StockBalance).filter(
            StockBalance.item_id == item_id,
            StockBalance.warehouse_id == warehouse_id,
            StockBalance.lot_number == lot_number
        ).first()
        
        if balance:
            balance.quantity += quantity
            if unit_cost > 0 and balance.quantity > 0:
                old_total = balance.unit_cost * (balance.quantity - quantity)
                new_total = old_total + (unit_cost * quantity)
                balance.unit_cost = new_total / balance.quantity
            balance.total_cost = balance.quantity * balance.unit_cost
        else:
            balance = StockBalance(
                item_id=item_id,
                warehouse_id=warehouse_id,
                quantity=quantity,
                lot_number=lot_number,
                unit_cost=unit_cost,
                total_cost=quantity * unit_cost
            )
            self.session.add(balance)
    
    def get_movements(
        self,
        item_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
        movement_type: Optional[StockMovementType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[StockMovement]:
        query = self.session.query(StockMovement)
        
        if item_id:
            query = query.filter(StockMovement.item_id == item_id)
        if warehouse_id:
            query = query.filter(or_(
                StockMovement.from_warehouse_id == warehouse_id,
                StockMovement.to_warehouse_id == warehouse_id
            ))
        if movement_type:
            query = query.filter(StockMovement.movement_type == movement_type)
        if start_date:
            query = query.filter(StockMovement.movement_date >= start_date)
        if end_date:
            query = query.filter(StockMovement.movement_date <= end_date)
        
        return query.order_by(StockMovement.movement_date.desc()).limit(limit).all()
    
    def close(self):
        self.session.close()
