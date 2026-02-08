from datetime import date
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models.rfq import (
    RFQ,
    RFQItem,
    SupplierOffer,
    SupplierOfferItem,
    RFQStatus,
    OfferStatus,
)
from database.models.purchasing import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderStatus,
    PurchaseRequest,
    PurchaseRequestItem,
)
from database.models.inventory import Item


class RFQService:
    def __init__(self, db: Session):
        self.db = db

    def create_rfq(self, data: dict) -> RFQ:
        """Yeni RFQ oluştur"""
        # Generate RFQ number if not provided
        if not data.get("rfq_no"):
            year = date.today().year
            count = self.db.query(RFQ).count() + 1
            data["rfq_no"] = f"RFQ-{year}-{count:04d}"

        rfq = RFQ(
            rfq_no=data["rfq_no"],
            title=data["title"],
            description=data.get("description"),
            date=data.get("date", date.today()),
            deadline=data["deadline"],
            status=RFQStatus.DRAFT,
        )
        self.db.add(rfq)
        self.db.flush()  # Get ID

        # Add items
        if "items" in data:
            for item_data in data["items"]:
                self.add_rfq_item(rfq.id, item_data)

        self.db.commit()
        self.db.refresh(rfq)
        return rfq

    def add_rfq_item(self, rfq_id: int, item_data: dict) -> RFQItem:
        """RFQ kalem ekle"""
        item = RFQItem(
            rfq_id=rfq_id,
            item_id=item_data.get("item_id"),
            description=item_data.get("description"),
            quantity=item_data["quantity"],
            unit_id=item_data.get("unit_id"),
            purchase_request_item_id=item_data.get("purchase_request_item_id"),
        )
        self.db.add(item)
        return item

    def list_rfqs(self, status: RFQStatus = None):
        """RFQ listele"""
        query = self.db.query(RFQ)
        if status:
            query = query.filter(RFQ.status == status)
        return query.order_by(RFQ.date.desc()).all()

    def get_rfq(self, rfq_id: int) -> Optional[RFQ]:
        """RFQ getir"""
        return self.db.query(RFQ).filter(RFQ.id == rfq_id).first()

    def publish_rfq(self, rfq_id: int):
        """RFQ'yu yayınla (Tedarikçilere duyurulmuş sayılır)"""
        rfq = self.get_rfq(rfq_id)
        if rfq and rfq.status == RFQStatus.DRAFT:
            rfq.status = RFQStatus.PUBLISHED
            self.db.commit()

    def add_offer(
        self, rfq_id: int, supplier_id: int, items: List[dict], offer_data: dict = None
    ) -> SupplierOffer:
        """Tedarikçi teklifi ekle"""
        offer = SupplierOffer(
            rfq_id=rfq_id,
            supplier_id=supplier_id,
            offer_date=(
                offer_data.get("offer_date", date.today())
                if offer_data
                else date.today()
            ),
            valid_until=offer_data.get("valid_until") if offer_data else None,
            currency=offer_data.get("currency", "TRY") if offer_data else "TRY",
            exchange_rate=offer_data.get("exchange_rate", 1.0) if offer_data else 1.0,
            status=OfferStatus.PENDING,
            notes=offer_data.get("notes") if offer_data else None,
        )
        self.db.add(offer)
        self.db.flush()

        for item_data in items:
            offer_item = SupplierOfferItem(
                offer_id=offer.id,
                rfq_item_id=item_data["rfq_item_id"],
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                tax_rate=item_data.get("tax_rate", 20),
                delivery_date=item_data.get("delivery_date"),
                notes=item_data.get("notes"),
            )
            self.db.add(offer_item)

        # Calculate totals
        offer.calculate_totals()

        self.db.commit()
        self.db.refresh(offer)
        return offer

    def compare_offers(self, rfq_id: int) -> dict:
        """Teklif karşılaştırma verisi hazırla"""
        rfq = self.get_rfq(rfq_id)
        if not rfq:
            return {}

        result = {
            "rfq": rfq,
            "items": [],
            "suppliers": [],
        }

        # Items
        for rfq_item in rfq.items:
            item_data = {
                "id": rfq_item.id,
                "description": rfq_item.description
                or (rfq_item.item.name if rfq_item.item else "Bilinmeyen"),
                "quantity": rfq_item.quantity,
                "offers": {},  # supplier_id -> {price, total, ...}
            }
            result["items"].append(item_data)

        # Suppliers and Offers
        for offer in rfq.offers:
            supplier_info = {
                "id": offer.supplier_id,
                "name": offer.supplier.name,
                "total_amount": offer.total_amount,
                "currency": offer.currency,
                "score": offer.supplier.rating or 0,
            }
            result["suppliers"].append(supplier_info)

            for offer_item in offer.items:
                # Find matching RFQ item in result
                for res_item in result["items"]:
                    if res_item["id"] == offer_item.rfq_item_id:
                        res_item["offers"][offer.supplier_id] = {
                            "unit_price": offer_item.unit_price,
                            "quantity": offer_item.quantity,
                            "line_total": offer_item.line_total,
                            "delivery_date": offer_item.delivery_date,
                        }
                        break

        return result

    def convert_to_order(self, offer_id: int) -> PurchaseOrder:
        """Teklifi siparişe dönüştür"""
        offer = (
            self.db.query(SupplierOffer).filter(SupplierOffer.id == offer_id).first()
        )
        if not offer:
            raise ValueError("Teklif bulunamadı.")

        # Generare PO Number
        year = date.today().year
        count = self.db.query(PurchaseOrder).count() + 1
        po_no = f"PO-{year}-{count:04d}"

        po = PurchaseOrder(
            order_no=po_no,
            order_date=date.today(),
            supplier_id=offer.supplier_id,
            status=PurchaseOrderStatus.DRAFT,
            currency=offer.currency,
            exchange_rate=offer.exchange_rate,
            notes=f"RFQ Ref: {offer.rfq.rfq_no}",
        )
        self.db.add(po)
        self.db.flush()

        for o_item in offer.items:
            rfq_item = o_item.rfq_item
            po_item = PurchaseOrderItem(
                order_id=po.id,
                item_id=rfq_item.item_id,
                quantity=o_item.quantity,
                unit_id=rfq_item.unit_id,
                unit_price=o_item.unit_price,
                tax_rate=o_item.tax_rate,
                description=rfq_item.description,
            )
            # Calculate line total
            po_item.calculate_line_total()
            self.db.add(po_item)

        po.calculate_totals()

        # Update Offer and RFQ status
        offer.status = OfferStatus.WON
        offer.rfq.status = RFQStatus.COMPLETED

        # Mark other offers as lost? Optional mechanism

        self.db.commit()
        return po
