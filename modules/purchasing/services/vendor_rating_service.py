from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy import func
from database.base import get_session
from database.models.purchasing import (
    Supplier,
    VendorRating,
    PurchaseOrder,
    GoodsReceipt,
)


class VendorRatingService:
    def __init__(self, db_session=None):
        self.db = db_session or get_session()

    def calculate_supplier_scores(self, supplier_id: int) -> Dict[str, Any]:
        """Tedarikçinin son performans verilerini analiz eder"""
        # Son 1 yıllık veriye bak
        one_year_ago = date.today() - timedelta(days=365)

        # 1. Kalite Puanı (Mal Kabul Kabul/Red Oranı)
        quality_score = self._calculate_quality_score(supplier_id, one_year_ago)

        # 2. Termin Puanı (Teslimat Gecikmeleri)
        delivery_score = self._calculate_delivery_score(supplier_id, one_year_ago)

        # 3. Maliyet Puanı (Şimdilik sabit veya RFQ bazlı - v2)
        cost_score = Decimal("100.00")

        # Toplam Puan (Ağırlıklı Ortalama)
        # %40 Kalite, %40 Termin, %20 Maliyet
        total_score = (
            (quality_score * Decimal("0.4"))
            + (delivery_score * Decimal("0.4"))
            + (cost_score * Decimal("0.2"))
        )

        return {
            "quality": quality_score,
            "delivery": delivery_score,
            "cost": cost_score,
            "total": total_score.quantize(Decimal("0.01")),
        }

    def _calculate_quality_score(self, supplier_id: int, since_date: date) -> Decimal:
        """Kabul edilen miktar / Toplam mal kabul miktarı"""
        from database.models.purchasing import GoodsReceiptItem

        query = (
            self.db.query(
                func.sum(GoodsReceiptItem.quantity).label("total"),
                func.sum(GoodsReceiptItem.accepted_quantity).label("accepted"),
            )
            .join(GoodsReceipt)
            .filter(
                GoodsReceipt.supplier_id == supplier_id,
                GoodsReceipt.receipt_date >= since_date,
            )
            .first()
        )

        if not query or not query.total or query.total == 0:
            return Decimal("100.00")  # Veri yoksa tam puan

        score = (Decimal(str(query.accepted)) / Decimal(str(query.total))) * 100
        return score.quantize(Decimal("0.01"))

    def _calculate_delivery_score(self, supplier_id: int, since_date: date) -> Decimal:
        """Gecikilen gün başına puan kırma"""
        orders = (
            self.db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.order_date >= since_date,
                PurchaseOrder.actual_delivery_date.isnot(None),
            )
            .all()
        )

        if not orders:
            return Decimal("100.00")

        total_penalty = 0
        for order in orders:
            if order.actual_delivery_date > order.delivery_date:
                delay_days = (order.actual_delivery_date - order.delivery_date).days
                # Her gün için 5 puan kır (max %100 kırılabilir)
                total_penalty += min(delay_days * 5, 100)

        avg_penalty = total_penalty / len(orders)
        score = max(Decimal("100.00") - Decimal(str(avg_penalty)), Decimal("0.00"))
        return score.quantize(Decimal("0.01"))

    def save_rating(
        self, supplier_id: int, scores: Dict[str, Decimal], comments: str = ""
    ):
        """Değerlendirmeyi kaydet ve tedarikçi kartını güncelle"""
        rating = VendorRating(
            supplier_id=supplier_id,
            quality_score=scores["quality"],
            delivery_score=scores["delivery"],
            cost_score=scores["cost"],
            total_score=scores["total"],
            comments=comments,
            rating_date=date.today(),
        )
        self.db.add(rating)

        # Tedarikçi kartındaki rating alanını güncelle
        supplier = self.db.query(Supplier).get(supplier_id)
        if supplier:
            supplier.rating = int(scores["total"])

        self.db.commit()
        return rating
