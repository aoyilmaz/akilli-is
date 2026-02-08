"""
Akıllı İş - İade Yönetimi Base Service
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.models.returns import (
    ReturnOrder,
    ReturnOrderLine,
    ReturnStatus,
    ReturnType,
)
from database.models.inventory import (
    StockMovement,
    StockMovementType,
)


class BaseReturnService:
    """
    İade İşlemleri Temel Servisi

    Tüm iade türleri (Satış, Satınalma) için ortak iş mantığını barındırır.
    Alt sınıflar (SalesReturnService, PurchaseReturnService) bu sınıfı genişletir.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_by_id(self, return_id: int) -> Optional[ReturnOrder]:
        """ID ile iade siparişi getir"""
        return self.db.query(ReturnOrder).filter(ReturnOrder.id == return_id).first()

    def get_by_code(self, code: str) -> Optional[ReturnOrder]:
        """Kod ile iade siparişi getir"""
        return self.db.query(ReturnOrder).filter(ReturnOrder.code == code).first()

    def list_returns(
        self,
        type: Optional[ReturnType] = None,
        status: Optional[ReturnStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ReturnOrder]:
        """İade siparişlerini listele"""
        query = self.db.query(ReturnOrder)

        if type:
            query = query.filter(ReturnOrder.type == type)

        if status:
            query = query.filter(ReturnOrder.status == status)

        return (
            query.order_by(desc(ReturnOrder.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def create_return(self, data: Dict[str, Any], user_id: int) -> ReturnOrder:
        """
        Yeni iade siparişi oluştur

        Args:
            data: İade verileri
            user_id: İşlemi yapan kullanıcı ID

        Returns:
            Oluşturulan iade siparişi
        """
        # Sıra numarası üret (Alt sınıflarda özelleştirilebilir)
        if "code" not in data:
            prefix = "IADE"
            if data.get("type") == ReturnType.SALES:
                prefix = "SIADE"
            elif data.get("type") == ReturnType.PURCHASE:
                prefix = "AIADE"

            data["code"] = self._generate_return_code(prefix)

        # Ana kayıt oluştur
        return_order = ReturnOrder(
            code=data["code"],
            type=data["type"],
            return_date=data.get("return_date", datetime.utcnow().date()),
            status=ReturnStatus.DRAFT,
            notes=data.get("description"),  # description -> notes
            # İlişkili kayıtlar
            customer_id=data.get("customer_id"),
            supplier_id=data.get("supplier_id"),
            related_sale_order_id=data.get("related_sale_order_id"),
            related_purchase_order_id=data.get("related_purchase_order_id"),
            created_by=user_id,
        )

        self.db.add(return_order)
        self.db.flush()

        # Kalemleri ekle
        if "lines" in data:
            for line_data in data["lines"]:
                self.add_return_line(return_order.id, line_data)

        self.db.commit()
        return return_order

    def add_return_line(
        self, return_id: int, line_data: Dict[str, Any]
    ) -> ReturnOrderLine:
        """İadeye kalem ekle"""
        line = ReturnOrderLine(
            return_order_id=return_id,
            item_id=line_data["item_id"],
            warehouse_id=line_data.get("warehouse_id"),  # unit_id removed/not in model?
            quantity=line_data["quantity"],
            unit_price=line_data.get("unit_price", 0),
            line_total=line_data.get("quantity", 0) * line_data.get("unit_price", 0),
            reason=line_data.get("reason"),
            condition=line_data.get("condition"),
            # related lines removed or mapped differently if needed
        )

        self.db.add(line)
        self.db.flush()
        return line

    def update_status(
        self, return_id: int, new_status: ReturnStatus, user_id: int
    ) -> ReturnOrder:
        """Durum güncelle"""
        return_order = self.get_by_id(return_id)
        if not return_order:
            raise ValueError(f"Return order {return_id} not found")

        old_status = return_order.status

        # Durum geçiş kontrolleri
        if not self._validate_status_transition(old_status, new_status):
            raise ValueError(
                f"Invalid status transition from {old_status} to {new_status}"
            )

        return_order.status = new_status
        # return_order.updated_at = datetime.utcnow() # updated_at not in model based on check?

        # Onaylandıysa stok hareketlerini oluştur
        if new_status == ReturnStatus.APPROVED and old_status != ReturnStatus.APPROVED:
            return_order.approved_by = user_id
            return_order.approved_at = datetime.utcnow()
            self._create_stock_movements(return_order, user_id)

        self.db.commit()
        return return_order

    def _validate_status_transition(
        self, old_status: ReturnStatus, new_status: ReturnStatus
    ) -> bool:
        """Durum geçişi geçerli mi?"""
        # Basit bir durum makinesi
        if old_status == ReturnStatus.DRAFT:
            return new_status in [
                ReturnStatus.PENDING_APPROVAL,
                ReturnStatus.CANCELLED,
            ]
        elif old_status == ReturnStatus.PENDING_APPROVAL:
            return new_status in [
                ReturnStatus.APPROVED,
                ReturnStatus.REJECTED,
                ReturnStatus.CANCELLED,
                ReturnStatus.DRAFT,
            ]
        elif old_status == ReturnStatus.APPROVED:
            return new_status in [
                ReturnStatus.RECEIVED,  # Depoya alma
                ReturnStatus.COMPLETED,
                ReturnStatus.CANCELLED,  # (Belki kısıtlı)
            ]
        elif old_status == ReturnStatus.COMPLETED:
            return False  # Tamamlanan değişmez

        return True

    def _generate_return_code(self, prefix: str) -> str:
        """
        Basit numara üreteci
        Üretim ortamında Sequence tablosu kullanılmalı
        """
        # Sequence tablosu varsa oradan al, yoksa timestamp bazlı geçici çözüm
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{prefix}-{timestamp}"

    def _create_stock_movements(self, return_order: ReturnOrder, user_id: int):
        """
        Stok hareketlerini oluştur

        Satış İadesi -> Stok Girişi (Müşteriden Depoya)
        Satınalma İadesi -> Stok Çıkışı (Depodan Tedarikçiye)
        """

        for line in return_order.lines:
            # İşlem türünü belirle
            if return_order.type == ReturnType.SALES:
                # Müşteri iadesi: Stok artar (Giriş)
                # İade, satışın tersidir. Satış = CIKIS, İade = IADE_SATIS (Giriş yönlü)
                movement_type = StockMovementType.IADE_SATIS
                # Kaynak: Müşteri (Depo yok), Hedef: Satırın deposu
                from_warehouse_id = None
                to_warehouse_id = (
                    line.warehouse_id or 1
                )  # Varsayılan Ana Depo (TODO: Parametrik yap)

            else:  # PURCHASE
                # Tedarikçi iadesi: Stok azalır (Çıkış)
                # Alış = GIRIS, İade = IADE_ALIS (Çıkış yönlü)
                movement_type = StockMovementType.IADE_ALIS
                from_warehouse_id = line.warehouse_id or 1  # Varsayılan Ana Depo
                to_warehouse_id = None  # Tedarikçi

            # Stok hareketi oluştur
            movement = StockMovement(
                item_id=line.item_id,
                quantity=line.quantity,
                # unit_id=line.unit_id, # ReturnOrderLine doesn't have unit_id in updated check
                movement_type=movement_type,
                movement_date=datetime.utcnow(),
                from_warehouse_id=from_warehouse_id,
                to_warehouse_id=to_warehouse_id,
                description=f"İade İşlemi: {return_order.code}",
                document_no=return_order.code,
                document_type="ReturnOrder",
                created_by=user_id,
            )
            self.db.add(movement)
