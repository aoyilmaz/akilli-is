from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from database.models.contracts import (
    Contract,
    ContractLine,
    ContractStatus,
    ContractType,
)


class ContractService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_by_id(self, contract_id: int) -> Optional[Contract]:
        return self.db.query(Contract).filter(Contract.id == contract_id).first()

    def get_by_code(self, code: str) -> Optional[Contract]:
        return self.db.query(Contract).filter(Contract.code == code).first()

    def list_contracts(
        self,
        contract_type: Optional[ContractType] = None,
        status: Optional[ContractStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Contract]:
        query = self.db.query(Contract)
        if contract_type:
            query = query.filter(Contract.contract_type == contract_type)
        if status:
            query = query.filter(Contract.status == status)

        return (
            query.order_by(desc(Contract.start_date)).offset(offset).limit(limit).all()
        )

    def create_contract(self, data: Dict[str, Any]) -> Contract:
        # Validate dates
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        if start_date and end_date and end_date < start_date:
            raise ValueError("Bitiş tarihi başlangıç tarihinden önce olamaz.")

        contract = Contract(
            code=data["code"],
            contract_type=data["contract_type"],
            customer_id=data.get("customer_id"),
            supplier_id=data.get("supplier_id"),
            start_date=start_date,
            end_date=end_date,
            status=data.get("status", ContractStatus.DRAFT),
            total_amount=data.get("total_amount", 0),
            currency=data.get("currency", "TRY"),
            description=data.get("description"),
            file_path=data.get("file_path"),
        )
        self.db.add(contract)
        self.db.flush()

        if "lines" in data:
            for line_data in data["lines"]:
                self.add_contract_line(contract.id, line_data)

        self.db.commit()
        return contract

    def add_contract_line(
        self, contract_id: int, line_data: Dict[str, Any]
    ) -> ContractLine:
        line = ContractLine(
            contract_id=contract_id,
            item_id=line_data.get("item_id"),
            description=line_data.get("description"),
            unit_price=line_data.get("unit_price", 0),
            quantity=line_data.get("quantity", 0),
            unit_id=line_data.get("unit_id"),
        )
        self.db.add(line)
        self.db.flush()
        return line

    def update_status(self, contract_id: int, new_status: ContractStatus) -> Contract:
        contract = self.get_by_id(contract_id)
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")

        contract.status = new_status
        self.db.commit()
        return contract

    def check_expiring_contracts(self, days_threshold: int = 30) -> List[Contract]:
        """Süresi dolmak üzere olan aktif sözleşmeleri getir"""
        today = date.today()
        threshold_date = today + timedelta(days=days_threshold)

        return (
            self.db.query(Contract)
            .filter(
                Contract.status == ContractStatus.ACTIVE,
                Contract.end_date >= today,
                Contract.end_date <= threshold_date,
            )
            .all()
        )
