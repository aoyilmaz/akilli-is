"""
Akıllı İş - HR ve Muhasebe Entegrasyon Köprüsü
"""

from decimal import Decimal
from sqlalchemy.orm import Session
from database.models.hr import Payroll
from database.models.accounting import (
    JournalEntry,
    JournalEntryLine,
    JournalEntryStatus,
)


class HRBridge:
    def __init__(self, session: Session):
        self.session = session

    def post_payroll_to_accounting(self, payroll: Payroll):
        """Maaş tahakkukunu muhasebe fişine dönüştürür"""
        entry = JournalEntry(
            entry_no=f"YV-PR-{payroll.period_year}-{payroll.period_month}-{payroll.employee_id}",
            entry_date=payroll.paid_date or datetime.now().date(),
            description=f"Maaş Tahakkuku: {payroll.employee.full_name} ({payroll.period_month}/{payroll.period_year})",
            reference_type="payroll",
            reference_id=payroll.id,
            status=JournalEntryStatus.POSTED,
        )
        self.session.add(entry)
        self.session.flush()

        # 1. 770 Genel Yönetim Giderleri (Borç) - Brüt + SGK İşveren vb.
        # Basitleştirilmiş: Brüt maaş
        line1 = JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=self._get_account_id("770"),
            debit=payroll.net_salary + payroll.deductions,
            credit=0,
        )

        # 2. 335 Personele Borçlar (Alacak) - Net Ödenecek
        line2 = JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=self._get_account_id("335"),
            debit=0,
            credit=payroll.net_salary,
        )

        # 3. 360/361 Ödenecek Vergi/Primler (Alacak)
        if payroll.deductions > 0:
            line3 = JournalEntryLine(
                journal_entry_id=entry.id,
                account_id=self._get_account_id("360"),
                debit=0,
                credit=payroll.deductions,
            )
            self.session.add(line3)

        self.session.add_all([line1, line2])
        return entry

    def _get_account_id(self, code: str) -> int:
        from database.models.accounting import Account

        account = (
            self.session.query(Account).filter(Account.code.startswith(code)).first()
        )
        return account.id if account else 1


from datetime import datetime
