"""
Akıllı İş - Stok ve Kalite Entegrasyon Servisi
"""

from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from database.models.inventory import (
    Item,
    StockBalance,
    StockMovement,
    WarehouseLocation,
    LocationType,
    StockMovementType,
)
from database.models.purchasing import GoodsReceipt
from database.models.quality import Inspection, InspectionStatus


class StockQualityService:
    @staticmethod
    def handle_goods_receipt(session: Session, receipt: GoodsReceipt):
        """
        Mal kabul tamamlandığında stok girişlerini yönetir.
        QC zorunlu olan ürünler Karantina lokasyonuna, diğerleri Normal lokasyona girer.
        """
        for item in receipt.items:
            # Ürünün kalite kontrol durumunu kontrol et
            product = session.query(Item).get(item.item_id)

            # Hedef lokasyonu belirle
            target_location = None
            if product.is_qc_required:
                # Karantina lokasyonunu bul (Depo içindeki ilk karantina lokasyonu)
                target_location = (
                    session.query(WarehouseLocation)
                    .filter(
                        WarehouseLocation.warehouse_id == receipt.warehouse_id,
                        WarehouseLocation.location_type == LocationType.QUARANTINE,
                    )
                    .first()
                )

                if not target_location:
                    # Karantina lokasyonu yoksa oluştur (Sistem otomatiği)
                    target_location = WarehouseLocation(
                        warehouse_id=receipt.warehouse_id,
                        code="QUAR-01",
                        name="Otomatik Karantina Alanı",
                        location_type=LocationType.QUARANTINE,
                    )
                    session.add(target_location)
                    session.flush()

            # Stok hareketini kaydet
            movement = StockMovement(
                movement_type=StockMovementType.GIRIS,
                movement_date=datetime.utcnow(),
                item_id=item.item_id,
                to_warehouse_id=receipt.warehouse_id,
                to_location_id=target_location.id if target_location else None,
                quantity=item.quantity,
                document_type="GoodsReceipt",
                document_no=receipt.receipt_no,
                created_by=receipt.created_by,
            )
            session.add(movement)

            # Bakiyeyi güncelle
            balance = (
                session.query(StockBalance)
                .filter(
                    StockBalance.item_id == item.item_id,
                    StockBalance.warehouse_id == receipt.warehouse_id,
                    StockBalance.location_id
                    == (target_location.id if target_location else None),
                    StockBalance.lot_number == item.lot_number,
                )
                .first()
            )

            if balance:
                balance.quantity += item.quantity
            else:
                balance = StockBalance(
                    item_id=item.item_id,
                    warehouse_id=receipt.warehouse_id,
                    location_id=target_location.id if target_location else None,
                    quantity=item.quantity,
                    lot_number=item.lot_number,
                )
                session.add(balance)

    @staticmethod
    def approve_quality_inspection(session: Session, inspection: Inspection):
        """
        Kalite onayı verildiğinde stoğu Karantina'dan Ana Depoya transfer eder.
        """
        if inspection.status != InspectionStatus.PASSED:
            return

        # Karantina lokasyonunu bul (muayenenin yapıldığı depodaki)
        quar_location = (
            session.query(WarehouseLocation)
            .filter(
                WarehouseLocation.warehouse_id == inspection.source_id,
                WarehouseLocation.location_type == LocationType.QUARANTINE,
            )
            .first()
        )

        if not quar_location:
            return

        # Karantina bakiyesini bul
        quar_balance = (
            session.query(StockBalance)
            .filter(
                StockBalance.item_id == inspection.item_id,
                StockBalance.warehouse_id == inspection.source_id,
                StockBalance.location_id == quar_location.id,
            )
            .first()
        )

        if not quar_balance or quar_balance.quantity < inspection.quantity:
            raise ValueError(
                f"Karantina lokasyonunda yeterli stok yok! "
                f"Mevcut: {quar_balance.quantity if quar_balance else 0}, "
                f"İstenen: {inspection.quantity}"
            )

        # Stok transfer hareketi oluştur
        transfer = StockMovement(
            movement_type=StockMovementType.TRANSFER,
            movement_date=datetime.utcnow(),
            item_id=inspection.item_id,
            from_warehouse_id=inspection.source_id,
            to_warehouse_id=inspection.source_id,
            from_location_id=quar_location.id,
            to_location_id=None,  # Normal lokasyon (varsayılan)
            quantity=inspection.quantity,
            unit_price=quar_balance.unit_cost,
            document_type="InspectionApproval",
            document_no=inspection.inspection_no,
        )
        session.add(transfer)

        # Karantina bakiyesini düş
        quar_balance.quantity -= inspection.quantity

        # Normal lokasyon bakiyesini artır (veya oluştur)
        normal_balance = (
            session.query(StockBalance)
            .filter(
                StockBalance.item_id == inspection.item_id,
                StockBalance.warehouse_id == inspection.source_id,
                StockBalance.location_id.is_(None),  # Normal lokasyon
            )
            .first()
        )

        if normal_balance:
            # Ağırlıklı ortalama maliyet hesabı
            old_qty = normal_balance.quantity
            old_cost = normal_balance.unit_cost or Decimal(0)
            new_qty = old_qty + inspection.quantity
            new_cost = quar_balance.unit_cost or Decimal(0)

            if new_qty > 0:
                normal_balance.unit_cost = (
                    (old_qty * old_cost) + (inspection.quantity * new_cost)
                ) / new_qty

            normal_balance.quantity = new_qty
        else:
            # Yeni bakiye oluştur
            normal_balance = StockBalance(
                item_id=inspection.item_id,
                warehouse_id=inspection.source_id,
                location_id=None,
                quantity=inspection.quantity,
                unit_cost=quar_balance.unit_cost,
            )
            session.add(normal_balance)

        session.flush()
