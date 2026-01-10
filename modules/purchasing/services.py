"""
Akıllı İş - Satın Alma Modülü Servisleri
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import joinedload

from database.base import get_session
from database.models.purchasing import (
    Supplier,
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseOrder,
    PurchaseOrderItem,
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseInvoice,
    PurchaseInvoiceItem,
    PurchaseRequestStatus,
    PurchaseOrderStatus,
    GoodsReceiptStatus,
    PurchaseInvoiceStatus,
    Currency,
)
from database.models.inventory import StockMovementType


class SupplierService:
    """Tedarikçi servisi"""

    def __init__(self):
        self.session = get_session()

    def get_all(self, active_only: bool = True) -> List[Supplier]:
        """Tüm tedarikçileri getir"""
        query = self.session.query(Supplier)
        if active_only:
            query = query.filter(Supplier.is_active == True)
        return query.order_by(Supplier.name).all()

    def get_by_id(self, supplier_id: int) -> Optional[Supplier]:
        """ID ile tedarikçi getir"""
        return self.session.query(Supplier).filter(Supplier.id == supplier_id).first()

    def get_by_code(self, code: str) -> Optional[Supplier]:
        """Kod ile tedarikçi getir"""
        return self.session.query(Supplier).filter(Supplier.code == code).first()

    def search(self, keyword: str, limit: int = 20) -> List[Supplier]:
        """Tedarikçi ara"""
        keyword = f"%{keyword}%"
        return (
            self.session.query(Supplier)
            .filter(
                and_(
                    Supplier.is_active == True,
                    or_(
                        Supplier.code.ilike(keyword),
                        Supplier.name.ilike(keyword),
                        Supplier.tax_number.ilike(keyword),
                    ),
                )
            )
            .limit(limit)
            .all()
        )

    def create(self, **data) -> Supplier:
        """Yeni tedarikçi oluştur"""
        supplier = Supplier(**data)
        self.session.add(supplier)
        self.session.commit()
        return supplier

    def update(self, supplier_id: int, **data) -> Optional[Supplier]:
        """Tedarikçi güncelle"""
        supplier = self.get_by_id(supplier_id)
        if supplier:
            for key, value in data.items():
                if hasattr(supplier, key):
                    setattr(supplier, key, value)
            self.session.commit()
        return supplier

    def delete(self, supplier_id: int) -> bool:
        """Tedarikçi sil (soft delete)"""
        supplier = self.get_by_id(supplier_id)
        if supplier:
            supplier.is_active = False
            self.session.commit()
            return True
        return False

    def generate_code(self) -> str:
        """Otomatik kod üret"""
        last = self.session.query(Supplier).order_by(desc(Supplier.id)).first()
        if last and last.code.startswith("SUP"):
            try:
                num = int(last.code[3:]) + 1
            except:
                num = 1
        else:
            num = 1
        return f"SUP{num:04d}"


class PurchaseRequestService:
    """Satın alma talep servisi"""

    def __init__(self):
        self.session = get_session()

    def get_all(self, status: PurchaseRequestStatus = None) -> List[PurchaseRequest]:
        """Tüm talepleri getir"""
        query = self.session.query(PurchaseRequest).options(
            joinedload(PurchaseRequest.items)
        )
        if status:
            query = query.filter(PurchaseRequest.status == status)
        return query.order_by(desc(PurchaseRequest.request_date)).all()

    def get_by_id(self, request_id: int) -> Optional[PurchaseRequest]:
        """ID ile talep getir"""
        return (
            self.session.query(PurchaseRequest)
            .options(
                joinedload(PurchaseRequest.items).joinedload(PurchaseRequestItem.item),
                joinedload(PurchaseRequest.items).joinedload(PurchaseRequestItem.unit),
            )
            .filter(PurchaseRequest.id == request_id)
            .first()
        )

    def get_pending(self) -> List[PurchaseRequest]:
        """Onay bekleyen talepleri getir"""
        return self.get_all(status=PurchaseRequestStatus.PENDING)

    def get_approved(self) -> List[PurchaseRequest]:
        """Onaylanan (sipariş verilmemiş) talepleri getir"""
        return self.get_all(status=PurchaseRequestStatus.APPROVED)

    def create(self, items_data: List[Dict], **data) -> PurchaseRequest:
        """Yeni talep oluştur"""
        # Talep numarası üret
        data["request_no"] = self.generate_request_no()

        request = PurchaseRequest(**data)
        self.session.add(request)
        self.session.flush()

        # Kalemleri ekle
        for item_data in items_data:
            item = PurchaseRequestItem(request_id=request.id, **item_data)
            self.session.add(item)

        self.session.commit()
        return request

    def update(
        self, request_id: int, items_data: List[Dict] = None, **data
    ) -> Optional[PurchaseRequest]:
        """Talep güncelle"""
        request = self.get_by_id(request_id)
        if not request:
            return None

        # Sadece taslak durumda güncellenebilir
        if request.status != PurchaseRequestStatus.DRAFT:
            raise ValueError("Sadece taslak durumdaki talepler güncellenebilir")

        for key, value in data.items():
            if hasattr(request, key):
                setattr(request, key, value)

        # Kalemleri güncelle
        if items_data is not None:
            # Mevcut kalemleri sil
            for item in request.items:
                self.session.delete(item)

            # Yeni kalemleri ekle
            for item_data in items_data:
                item = PurchaseRequestItem(request_id=request.id, **item_data)
                self.session.add(item)

        self.session.commit()
        return request

    def submit_for_approval(self, request_id: int) -> Optional[PurchaseRequest]:
        """Talebi onaya gönder"""
        request = self.get_by_id(request_id)
        if request and request.status == PurchaseRequestStatus.DRAFT:
            request.status = PurchaseRequestStatus.PENDING
            self.session.commit()
        return request

    def approve(self, request_id: int, approved_by: str) -> Optional[PurchaseRequest]:
        """Talebi onayla"""
        request = self.get_by_id(request_id)
        if request and request.status == PurchaseRequestStatus.PENDING:
            request.status = PurchaseRequestStatus.APPROVED
            request.approved_by = approved_by
            request.approved_date = datetime.now()
            self.session.commit()
        return request

    def reject(self, request_id: int, reason: str) -> Optional[PurchaseRequest]:
        """Talebi reddet"""
        request = self.get_by_id(request_id)
        if request and request.status == PurchaseRequestStatus.PENDING:
            request.status = PurchaseRequestStatus.REJECTED
            request.rejection_reason = reason
            self.session.commit()
        return request

    def delete(self, request_id: int) -> bool:
        """Talep sil"""
        request = self.get_by_id(request_id)
        if request and request.status == PurchaseRequestStatus.DRAFT:
            self.session.delete(request)
            self.session.commit()
            return True
        return False

    def generate_request_no(self) -> str:
        """Talep numarası üret"""
        today = date.today()
        prefix = f"PR{today.strftime('%y%m')}"

        last = (
            self.session.query(PurchaseRequest)
            .filter(PurchaseRequest.request_no.like(f"{prefix}%"))
            .order_by(desc(PurchaseRequest.request_no))
            .first()
        )

        if last:
            try:
                num = int(last.request_no[-4:]) + 1
            except:
                num = 1
        else:
            num = 1

        return f"{prefix}{num:04d}"


class PurchaseOrderService:
    """Satın alma sipariş servisi"""

    def __init__(self):
        self.session = get_session()

    def get_all(
        self, status: PurchaseOrderStatus = None, supplier_id: int = None
    ) -> List[PurchaseOrder]:
        """Tüm siparişleri getir"""
        query = self.session.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.supplier), joinedload(PurchaseOrder.items)
        )
        if status:
            query = query.filter(PurchaseOrder.status == status)
        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        return query.order_by(desc(PurchaseOrder.order_date)).all()

    def get_by_id(self, order_id: int) -> Optional[PurchaseOrder]:
        """ID ile sipariş getir"""
        return (
            self.session.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.item),
                joinedload(PurchaseOrder.items).joinedload(PurchaseOrderItem.unit),
            )
            .filter(PurchaseOrder.id == order_id)
            .first()
        )

    def get_open_orders(self) -> List[PurchaseOrder]:
        """Açık siparişleri getir"""
        return (
            self.session.query(PurchaseOrder)
            .filter(
                PurchaseOrder.status.in_(
                    [
                        PurchaseOrderStatus.SENT,
                        PurchaseOrderStatus.CONFIRMED,
                        PurchaseOrderStatus.PARTIAL,
                    ]
                )
            )
            .order_by(PurchaseOrder.delivery_date)
            .all()
        )

    def create(self, items_data: List[Dict], **data) -> PurchaseOrder:
        """Yeni sipariş oluştur"""
        data["order_no"] = self.generate_order_no()

        order = PurchaseOrder(**data)
        self.session.add(order)
        self.session.flush()

        for item_data in items_data:
            item = PurchaseOrderItem(order_id=order.id, **item_data)
            item.calculate_line_total()
            self.session.add(item)

        self.session.flush()
        order.calculate_totals()
        self.session.commit()

        return order

    def create_from_request(
        self, request_id: int, supplier_id: int, items_data: List[Dict], **data
    ) -> PurchaseOrder:
        """Talepten sipariş oluştur"""
        request_service = PurchaseRequestService()
        request = request_service.get_by_id(request_id)

        if not request or request.status != PurchaseRequestStatus.APPROVED:
            raise ValueError("Geçerli bir onaylı talep bulunamadı")

        data["request_id"] = request_id
        data["supplier_id"] = supplier_id

        # order_date yoksa bugünün tarihini kullan
        if "order_date" not in data or data["order_date"] is None:
            data["order_date"] = date.today()

        order = self.create(items_data, **data)

        # Talebin durumunu güncelle
        request.status = PurchaseRequestStatus.ORDERED
        self.session.commit()

        return order

    def update(
        self, order_id: int, items_data: List[Dict] = None, **data
    ) -> Optional[PurchaseOrder]:
        """Sipariş güncelle"""
        order = self.get_by_id(order_id)
        if not order:
            return None

        if order.status not in [PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.SENT]:
            raise ValueError("Bu sipariş artık güncellenemez")

        for key, value in data.items():
            if hasattr(order, key):
                setattr(order, key, value)

        if items_data is not None:
            for item in order.items:
                self.session.delete(item)

            for item_data in items_data:
                item = PurchaseOrderItem(order_id=order.id, **item_data)
                item.calculate_line_total()
                self.session.add(item)

            self.session.flush()
            order.calculate_totals()

        self.session.commit()
        return order

    def send_to_supplier(self, order_id: int) -> Optional[PurchaseOrder]:
        """Siparişi tedarikçiye gönder"""
        order = self.get_by_id(order_id)
        if order and order.status == PurchaseOrderStatus.DRAFT:
            order.status = PurchaseOrderStatus.SENT
            self.session.commit()
        return order

    def confirm(self, order_id: int) -> Optional[PurchaseOrder]:
        """Tedarikçi onayı"""
        order = self.get_by_id(order_id)
        if order and order.status == PurchaseOrderStatus.SENT:
            order.status = PurchaseOrderStatus.CONFIRMED
            self.session.commit()
        return order

    def cancel(self, order_id: int) -> Optional[PurchaseOrder]:
        """Sipariş iptal"""
        order = self.get_by_id(order_id)
        if order and order.status in [
            PurchaseOrderStatus.DRAFT,
            PurchaseOrderStatus.SENT,
        ]:
            order.status = PurchaseOrderStatus.CANCELLED
            self.session.commit()
        return order

    def close(self, order_id: int) -> Optional[PurchaseOrder]:
        """Sipariş kapat"""
        order = self.get_by_id(order_id)
        if order and order.status in [
            PurchaseOrderStatus.RECEIVED,
            PurchaseOrderStatus.PARTIAL,
        ]:
            order.status = PurchaseOrderStatus.CLOSED
            self.session.commit()
        return order

    def update_received_quantities(self, order_id: int):
        """Teslim alınan miktarları güncelle ve durumu kontrol et"""
        order = self.get_by_id(order_id)
        if not order:
            return

        all_received = True
        any_received = False

        for item in order.items:
            if item.received_quantity > 0:
                any_received = True
            if not item.is_fully_received:
                all_received = False

        if all_received:
            order.status = PurchaseOrderStatus.RECEIVED
            order.actual_delivery_date = date.today()
        elif any_received:
            order.status = PurchaseOrderStatus.PARTIAL

        self.session.commit()

    def delete(self, order_id: int) -> bool:
        """Sipariş sil"""
        order = self.get_by_id(order_id)
        if order and order.status == PurchaseOrderStatus.DRAFT:
            self.session.delete(order)
            self.session.commit()
            return True
        return False

    def generate_order_no(self) -> str:
        """Sipariş numarası üret"""
        today = date.today()
        prefix = f"PO{today.strftime('%y%m')}"

        last = (
            self.session.query(PurchaseOrder)
            .filter(PurchaseOrder.order_no.like(f"{prefix}%"))
            .order_by(desc(PurchaseOrder.order_no))
            .first()
        )

        if last:
            try:
                num = int(last.order_no[-4:]) + 1
            except:
                num = 1
        else:
            num = 1

        return f"{prefix}{num:04d}"


class GoodsReceiptService:
    """Mal kabul servisi"""

    def __init__(self):
        self.session = get_session()

    def get_all(self, status: GoodsReceiptStatus = None) -> List[GoodsReceipt]:
        """Tüm mal kabulleri getir"""
        query = self.session.query(GoodsReceipt).options(
            joinedload(GoodsReceipt.supplier),
            joinedload(GoodsReceipt.warehouse),
            joinedload(GoodsReceipt.items),
        )
        if status:
            query = query.filter(GoodsReceipt.status == status)
        return query.order_by(desc(GoodsReceipt.receipt_date)).all()

    def get_by_id(self, receipt_id: int) -> Optional[GoodsReceipt]:
        """ID ile mal kabul getir"""
        return (
            self.session.query(GoodsReceipt)
            .options(
                joinedload(GoodsReceipt.supplier),
                joinedload(GoodsReceipt.warehouse),
                joinedload(GoodsReceipt.purchase_order),
                joinedload(GoodsReceipt.items).joinedload(GoodsReceiptItem.item),
                joinedload(GoodsReceipt.items).joinedload(GoodsReceiptItem.unit),
            )
            .filter(GoodsReceipt.id == receipt_id)
            .first()
        )

    def create(self, items_data: List[Dict], **data) -> GoodsReceipt:
        """Yeni mal kabul oluştur"""
        data["receipt_no"] = self.generate_receipt_no()

        receipt = GoodsReceipt(**data)
        self.session.add(receipt)
        self.session.flush()

        for item_data in items_data:
            # Varsayılan kabul miktarı
            if "accepted_quantity" not in item_data:
                item_data["accepted_quantity"] = item_data.get("quantity", 0)

            item = GoodsReceiptItem(receipt_id=receipt.id, **item_data)
            self.session.add(item)

        self.session.commit()
        return receipt

    def create_from_order(
        self, order_id: int, warehouse_id: int, items_data: List[Dict], **data
    ) -> GoodsReceipt:
        """Siparişten mal kabul oluştur"""
        po_service = PurchaseOrderService()
        order = po_service.get_by_id(order_id)

        if not order:
            raise ValueError("Sipariş bulunamadı")

        if order.status not in [
            PurchaseOrderStatus.CONFIRMED,
            PurchaseOrderStatus.PARTIAL,
            PurchaseOrderStatus.SENT,
        ]:
            raise ValueError("Bu sipariş için mal kabul yapılamaz")

        data["purchase_order_id"] = order_id
        data["supplier_id"] = order.supplier_id
        data["warehouse_id"] = warehouse_id

        # receipt_date yoksa bugünün tarihini kullan
        if "receipt_date" not in data or data["receipt_date"] is None:
            data["receipt_date"] = date.today()

        receipt = self.create(items_data, **data)

        # Sipariş kalemlerini güncelle
        for grn_item in receipt.items:
            if grn_item.po_item_id:
                po_item = self.session.query(PurchaseOrderItem).get(grn_item.po_item_id)
                if po_item:
                    po_item.received_quantity = Decimal(
                        str(po_item.received_quantity or 0)
                    ) + Decimal(str(grn_item.accepted_quantity or 0))

        # Sipariş durumunu güncelle
        po_service.update_received_quantities(order_id)

        return receipt

    def complete(self, receipt_id: int) -> Optional[GoodsReceipt]:
        """Mal kabul tamamla ve stok girişi yap"""
        receipt = self.get_by_id(receipt_id)
        if not receipt or receipt.status != GoodsReceiptStatus.DRAFT:
            return None

        # Stok girişi yap
        try:
            from modules.inventory.services import StockMovementService

            movement_service = StockMovementService()

            for item in receipt.items:
                if item.accepted_quantity and item.accepted_quantity > 0:
                    movement_service.create_movement(
                        movement_type=StockMovementType.SATIN_ALMA,
                        item_id=item.item_id,
                        to_warehouse_id=receipt.warehouse_id,
                        quantity=float(item.accepted_quantity),
                        document_type="goods_receipt",
                        document_no=receipt.receipt_no,
                        description=f"Mal Kabul: {receipt.receipt_no}",
                    )

            receipt.status = GoodsReceiptStatus.COMPLETED
            self.session.commit()

        except Exception as e:
            self.session.rollback()
            raise e

        return receipt

    def cancel(self, receipt_id: int) -> Optional[GoodsReceipt]:
        """Mal kabul iptal"""
        receipt = self.get_by_id(receipt_id)
        if receipt and receipt.status == GoodsReceiptStatus.DRAFT:
            receipt.status = GoodsReceiptStatus.CANCELLED
            self.session.commit()
        return receipt

    def delete(self, receipt_id: int) -> bool:
        """Mal kabul sil"""
        receipt = self.get_by_id(receipt_id)
        if receipt and receipt.status == GoodsReceiptStatus.DRAFT:
            self.session.delete(receipt)
            self.session.commit()
            return True
        return False

    def generate_receipt_no(self) -> str:
        """Mal kabul numarası üret"""
        today = date.today()
        prefix = f"GRN{today.strftime('%y%m')}"

        last = (
            self.session.query(GoodsReceipt)
            .filter(GoodsReceipt.receipt_no.like(f"{prefix}%"))
            .order_by(desc(GoodsReceipt.receipt_no))
            .first()
        )

        if last:
            try:
                num = int(last.receipt_no[-4:]) + 1
            except:
                num = 1
        else:
            num = 1

        return f"{prefix}{num:04d}"


class PurchaseInvoiceService:
    """Satınalma faturası servisi"""

    def __init__(self):
        self.session = get_session()

    def get_all(
        self, status: PurchaseInvoiceStatus = None, supplier_id: int = None
    ) -> List[PurchaseInvoice]:
        """Tüm faturaları getir"""
        query = self.session.query(PurchaseInvoice).options(
            joinedload(PurchaseInvoice.supplier),
            joinedload(PurchaseInvoice.items),
        )
        if status:
            query = query.filter(PurchaseInvoice.status == status)
        if supplier_id:
            query = query.filter(PurchaseInvoice.supplier_id == supplier_id)
        return query.order_by(desc(PurchaseInvoice.invoice_date)).all()

    def get_by_id(self, invoice_id: int) -> Optional[PurchaseInvoice]:
        """ID ile fatura getir"""
        return (
            self.session.query(PurchaseInvoice)
            .options(
                joinedload(PurchaseInvoice.supplier),
                joinedload(PurchaseInvoice.goods_receipt),
                joinedload(PurchaseInvoice.items).joinedload(PurchaseInvoiceItem.item),
                joinedload(PurchaseInvoice.items).joinedload(PurchaseInvoiceItem.unit),
            )
            .filter(PurchaseInvoice.id == invoice_id)
            .first()
        )

    def get_open_invoices(self) -> List[PurchaseInvoice]:
        """Açık (ödenmemiş) faturaları getir"""
        return (
            self.session.query(PurchaseInvoice)
            .filter(
                PurchaseInvoice.status.in_(
                    [
                        PurchaseInvoiceStatus.RECEIVED,
                        PurchaseInvoiceStatus.PARTIAL,
                        PurchaseInvoiceStatus.OVERDUE,
                    ]
                )
            )
            .order_by(PurchaseInvoice.due_date)
            .all()
        )

    def get_overdue_invoices(self) -> List[PurchaseInvoice]:
        """Vadesi geçmiş faturaları getir"""
        from datetime import date as dt_date

        return (
            self.session.query(PurchaseInvoice)
            .filter(
                PurchaseInvoice.status.in_(
                    [
                        PurchaseInvoiceStatus.RECEIVED,
                        PurchaseInvoiceStatus.PARTIAL,
                    ]
                ),
                PurchaseInvoice.due_date < dt_date.today(),
            )
            .order_by(PurchaseInvoice.due_date)
            .all()
        )

    def create(self, items_data: List[Dict], **data) -> PurchaseInvoice:
        """Yeni fatura oluştur"""
        data["invoice_no"] = self.generate_invoice_no()

        invoice = PurchaseInvoice(**data)
        self.session.add(invoice)
        self.session.flush()

        for item_data in items_data:
            item = PurchaseInvoiceItem(invoice_id=invoice.id, **item_data)
            item.calculate_line_total()
            self.session.add(item)

        self.session.flush()
        invoice.calculate_totals()
        self.session.commit()

        return invoice

    def create_from_goods_receipt(
        self, goods_receipt_id: int, **data
    ) -> PurchaseInvoice:
        """Mal kabulden fatura oluştur"""
        gr_service = GoodsReceiptService()
        receipt = gr_service.get_by_id(goods_receipt_id)

        if not receipt:
            raise ValueError("Mal kabul bulunamadı")

        if receipt.status != GoodsReceiptStatus.COMPLETED:
            raise ValueError("Fatura için mal kabul tamamlanmış olmalıdır")

        data["goods_receipt_id"] = goods_receipt_id
        data["supplier_id"] = receipt.supplier_id
        data["purchase_order_id"] = receipt.purchase_order_id

        if "invoice_date" not in data or data["invoice_date"] is None:
            data["invoice_date"] = date.today()

        # Kalemler
        items_data = []
        for grn_item in receipt.items:
            if grn_item.accepted_quantity and grn_item.accepted_quantity > 0:
                # Birim fiyatı varsa kullan
                unit_price = 0
                if grn_item.po_item_id:
                    po_item = self.session.query(PurchaseOrderItem).get(
                        grn_item.po_item_id
                    )
                    if po_item:
                        unit_price = po_item.unit_price

                items_data.append(
                    {
                        "item_id": grn_item.item_id,
                        "quantity": grn_item.accepted_quantity,
                        "unit_id": grn_item.unit_id,
                        "unit_price": unit_price,
                        "tax_rate": 18,
                    }
                )

        return self.create(items_data, **data)

    def update(
        self, invoice_id: int, items_data: List[Dict] = None, **data
    ) -> Optional[PurchaseInvoice]:
        """Fatura güncelle"""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return None

        if invoice.status != PurchaseInvoiceStatus.DRAFT:
            raise ValueError("Sadece taslak faturalar güncellenebilir")

        for key, value in data.items():
            if hasattr(invoice, key):
                setattr(invoice, key, value)

        if items_data is not None:
            for item in invoice.items:
                self.session.delete(item)

            for item_data in items_data:
                item = PurchaseInvoiceItem(invoice_id=invoice.id, **item_data)
                item.calculate_line_total()
                self.session.add(item)

            self.session.flush()
            invoice.calculate_totals()

        self.session.commit()
        return invoice

    def confirm(self, invoice_id: int) -> Optional[PurchaseInvoice]:
        """Faturayı onayla/kaydet"""
        invoice = self.get_by_id(invoice_id)
        if invoice and invoice.status == PurchaseInvoiceStatus.DRAFT:
            invoice.status = PurchaseInvoiceStatus.RECEIVED
            self.session.commit()
        return invoice

    def record_payment(
        self,
        invoice_id: int,
        amount: Decimal,
        payment_method: str = None,
        payment_notes: str = None,
    ) -> Optional[PurchaseInvoice]:
        """Ödeme kaydet"""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return None

        if invoice.status in [
            PurchaseInvoiceStatus.PAID,
            PurchaseInvoiceStatus.CANCELLED,
        ]:
            raise ValueError("Bu faturaya ödeme kaydedilemez")

        new_paid = Decimal(str(invoice.paid_amount or 0)) + amount
        invoice.paid_amount = new_paid
        invoice.balance = invoice.total - new_paid

        if payment_method:
            invoice.payment_method = payment_method
        if payment_notes:
            invoice.payment_notes = payment_notes

        if invoice.balance <= 0:
            invoice.status = PurchaseInvoiceStatus.PAID
            invoice.paid_date = date.today()
        else:
            invoice.status = PurchaseInvoiceStatus.PARTIAL

        self.session.commit()
        return invoice

    def cancel(self, invoice_id: int) -> Optional[PurchaseInvoice]:
        """Fatura iptal"""
        invoice = self.get_by_id(invoice_id)
        if invoice and invoice.status in [
            PurchaseInvoiceStatus.DRAFT,
            PurchaseInvoiceStatus.RECEIVED,
        ]:
            invoice.status = PurchaseInvoiceStatus.CANCELLED
            self.session.commit()
        return invoice

    def delete(self, invoice_id: int) -> bool:
        """Fatura sil"""
        invoice = self.get_by_id(invoice_id)
        if invoice and invoice.status == PurchaseInvoiceStatus.DRAFT:
            self.session.delete(invoice)
            self.session.commit()
            return True
        return False

    def mark_overdue(self):
        """Vadesi geçmiş faturaları işaretle"""
        from datetime import date as dt_date

        overdue = (
            self.session.query(PurchaseInvoice)
            .filter(
                PurchaseInvoice.status.in_(
                    [
                        PurchaseInvoiceStatus.RECEIVED,
                        PurchaseInvoiceStatus.PARTIAL,
                    ]
                ),
                PurchaseInvoice.due_date < dt_date.today(),
            )
            .all()
        )

        for inv in overdue:
            inv.status = PurchaseInvoiceStatus.OVERDUE

        self.session.commit()
        return len(overdue)

    def generate_invoice_no(self) -> str:
        """Fatura numarası üret"""
        today = date.today()
        prefix = f"PI{today.strftime('%y%m')}"

        last = (
            self.session.query(PurchaseInvoice)
            .filter(PurchaseInvoice.invoice_no.like(f"{prefix}%"))
            .order_by(desc(PurchaseInvoice.invoice_no))
            .first()
        )

        if last:
            try:
                num = int(last.invoice_no[-4:]) + 1
            except ValueError:
                num = 1
        else:
            num = 1

        return f"{prefix}{num:04d}"

    def get_supplier_balance(self, supplier_id: int) -> Decimal:
        """Tedarikçi bakiyesi hesapla"""
        total = (
            self.session.query(
                func.coalesce(func.sum(PurchaseInvoice.balance), Decimal(0))
            )
            .filter(
                PurchaseInvoice.supplier_id == supplier_id,
                PurchaseInvoice.status.in_(
                    [
                        PurchaseInvoiceStatus.RECEIVED,
                        PurchaseInvoiceStatus.PARTIAL,
                        PurchaseInvoiceStatus.OVERDUE,
                    ]
                ),
            )
            .scalar()
        )

        return total or Decimal(0)
