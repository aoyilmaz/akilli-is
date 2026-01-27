"""
Akıllı İş - Stok Talep Servisi
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import joinedload

from database.models import StockRequest, StockRequestStatus, User, Item
from .base import ServiceBase


class StockRequestService(ServiceBase):
    """Stok talep işlemleri servisi"""

    def get_all(self, status: StockRequestStatus = None) -> List[StockRequest]:
        """Tüm talepleri getir"""
        query = self.session.query(StockRequest).options(
            joinedload(StockRequest.requester),
            joinedload(StockRequest.reference_stock),
            joinedload(StockRequest.category),
            joinedload(StockRequest.unit),
        )

        if status:
            query = query.filter(StockRequest.status == status)

        return query.order_by(StockRequest.request_date.desc()).all()

    def get_by_id(self, request_id: int) -> Optional[StockRequest]:
        """ID'ye göre talep getir"""
        return (
            self.session.query(StockRequest)
            .filter(StockRequest.id == request_id)
            .first()
        )

    def create_request(self, requester_id: int, **kwargs) -> StockRequest:
        """Yeni talep oluştur"""
        request = StockRequest(
            requester_id=requester_id,
            status=StockRequestStatus.PENDING,
            request_date=datetime.utcnow(),
            **kwargs
        )
        self.session.add(request)
        self.session.commit()
        return request

    def approve_request(self, request_id: int, created_stock_id: int) -> bool:
        """Talebi onayla"""
        request = self.get_by_id(request_id)
        if not request:
            return False

        request.status = StockRequestStatus.APPROVED
        request.created_stock_id = created_stock_id

        self.session.commit()
        return True

    def reject_request(self, request_id: int, reason: str) -> bool:
        """Talebi reddet"""
        request = self.get_by_id(request_id)
        if not request:
            return False

        request.status = StockRequestStatus.REJECTED
        request.rejection_reason = reason

        self.session.commit()
        return True
