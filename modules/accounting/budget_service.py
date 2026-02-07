from datetime import date
from decimal import Decimal
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.base import get_session
from database.models.accounting import (
    Budget,
    BudgetLine,
    BudgetStatus,
    Account,
    JournalEntryLine,
    JournalEntry,
    JournalEntryStatus,
)
from modules.inventory.services import ServiceBase


class BudgetService(ServiceBase):
    """Bütçe Yönetimi Servisi"""

    def __init__(self):
        super().__init__()
        self.session: Session = get_session()

    def create_budget(
        self,
        name: str,
        period_year: int,
        start_date: date,
        end_date: date,
        description: str = None,
    ) -> Budget:
        """Yeni bütçe oluştur"""
        budget = Budget(
            name=name,
            period_year=period_year,
            start_date=start_date,
            end_date=end_date,
            description=description,
            status=BudgetStatus.DRAFT,
        )
        self.session.add(budget)
        self.session.commit()
        return budget

    def update_budget_line(
        self, budget_id: int, account_id: int, planned_amount: Decimal
    ) -> BudgetLine:
        """Bütçe kalemini güncelle veya ekle"""
        line = (
            self.session.query(BudgetLine)
            .filter_by(budget_id=budget_id, account_id=account_id)
            .first()
        )

        if line:
            line.planned_amount = planned_amount
        else:
            line = BudgetLine(
                budget_id=budget_id,
                account_id=account_id,
                planned_amount=planned_amount,
            )
            self.session.add(line)

        self.session.flush()

        # Update total
        self._update_budget_total(budget_id)

        self.session.commit()
        return line

    def _update_budget_total(self, budget_id: int):
        total = (
            self.session.query(func.sum(BudgetLine.planned_amount))
            .filter_by(budget_id=budget_id)
            .scalar()
        )
        budget = self.session.query(Budget).get(budget_id)
        budget.total_amount = total or 0

    def get_budget_status(self, budget_id: int) -> Dict:
        """Bütçe gerçekleşme durumunu raporla"""
        budget = self.session.query(Budget).get(budget_id)
        if not budget:
            raise ValueError("Budget not found")

        report = {
            "budget": {
                "id": budget.id,
                "name": budget.name,
                "period_year": budget.period_year,
                "total_planned": float(budget.total_amount or 0),
                "total_actual": 0.0,
                "variance": 0.0,
            },
            "lines": [],
        }

        total_actual = Decimal(0)

        for line in budget.lines:
            # Hesap bakiyesini (veya dönem hareketini) hesapla
            # Gider hesapları (7 ve 6) için borç bakiyesi
            # Gelir hesapları (6) için alacak bakiyesi
            # Basit olması için toplam hareket farkını alalım (Borç - Alacak)

            # Not: Tam eşleşme mi yoksa alt hesaplar dahil mi?
            # Şimdilik sadece tam eşleşen hesap

            # İlgili dönemdeki hareketler
            balance_query = (
                self.session.query(
                    func.sum(JournalEntryLine.debit - JournalEntryLine.credit)
                )
                .join(JournalEntry)
                .filter(
                    JournalEntryLine.account_id == line.account_id,
                    JournalEntry.entry_date.between(budget.start_date, budget.end_date),
                    JournalEntry.status == JournalEntryStatus.POSTED,
                )
            )

            actual = balance_query.scalar() or Decimal(0)

            # Gider hesabı ise pozitif (Borç bakiye), Gelir ise negatif dönebilir
            # Ancak bütçede genelde mutlak değer tutulur.
            # Şimdilik basitçe actual değerini alalım.

            variance = (line.planned_amount or 0) - actual

            # Ratio
            ratio = 0
            if line.planned_amount and line.planned_amount != 0:
                ratio = (actual / line.planned_amount) * 100

            line_data = {
                "account_code": line.account.code,
                "account_name": line.account.name,
                "planned": float(line.planned_amount or 0),
                "actual": float(actual),
                "variance": float(variance),
                "ratio": float(ratio),
            }
            report["lines"].append(line_data)
            total_actual += actual

        report["budget"]["total_actual"] = float(total_actual)
        report["budget"]["variance"] = float(budget.total_amount or 0) - float(
            total_actual
        )

        return report

    def close(self):
        if self.session:
            self.session.close()
