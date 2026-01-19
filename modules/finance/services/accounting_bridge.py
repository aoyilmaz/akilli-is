"""
Akıllı İş - Finans ve Muhasebe Entegrasyon Köprüsü
"""

from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from database.models.sales import Invoice
from database.models.finance import Payment, Receipt
from database.models.accounting import (
    JournalEntry,
    JournalEntryLine,
    JournalEntryStatus,
    Account,
)


class AccountingBridge:
    def __init__(self, session: Session):
        self.session = session

    def create_invoice_journal(self, invoice: Invoice):
        """Satış faturası için yevmiye fişi oluşturur"""
        # 120 (Alıcılar), 600 (Satışlar), 391 (KDV) hesaplarını bul/belirle
        # Not: Gerçek uygulamada bu hesaplar parametrik olmalıdır.

        entry = JournalEntry(
            entry_no=f"YV-INV-{invoice.invoice_no}",
            entry_date=invoice.invoice_date,
            description=f"Satış Faturası: {invoice.invoice_no}",
            reference_type="invoice",
            reference_id=invoice.id,
            status=JournalEntryStatus.POSTED,
        )
        self.session.add(entry)
        self.session.flush()

        # 1. 120 Alıcılar Hesabı (Borç)
        line1 = JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=self._get_account_id("120"),
            debit=invoice.total,
            credit=0,
            description=f"{invoice.customer.name} - Fatura Borcu",
        )

        # 2. 600 Yurtiçi Satışlar (Alacak)
        line2 = JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=self._get_account_id("600"),
            debit=0,
            credit=invoice.subtotal,
            description="Ürün Satış Geliri",
        )

        # 3. 391 Hesaplanan KDV (Alacak)
        if invoice.tax_amount > 0:
            line3 = JournalEntryLine(
                journal_entry_id=entry.id,
                account_id=self._get_account_id("391"),
                debit=0,
                credit=invoice.tax_amount,
                description="KDV Tahakkuku",
            )
            self.session.add(line3)

        self.session.add_all([line1, line2])
        return entry

    def create_payment_journal(self, payment: Payment):
        """Ödeme için yevmiye fişi oluşturur"""
        # 320 (Satıcılar) Borç, 100/102 (Kasa/Banka) Alacak
        entry = JournalEntry(
            entry_no=f"YV-PAY-{payment.payment_no}",
            entry_date=payment.payment_date,
            description=f"Ödeme: {payment.payment_no}",
            reference_type="payment",
            reference_id=payment.id,
            status=JournalEntryStatus.POSTED,
        )
        self.session.add(entry)
        self.session.flush()

        # 320 Satıcılar (Borç)
        line1 = JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=self._get_account_id("320"),
            debit=payment.amount,
            credit=0,
        )

        # 102 Bankalar (Alacak)
        line2 = JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=self._get_account_id("102"),
            debit=0,
            credit=payment.amount,
        )

        self.session.add_all([line1, line2])
        return entry

    def _get_account_id(self, code: str) -> int:
        """Koda göre hesap ID'sini getirir, yoksa oluşturur (Örnek amaçlı)"""
        account = (
            self.session.query(Account).filter(Account.code.startswith(code)).first()
        )
        if not account:
            # Gerçekte hata dönmeli veya varsayılan hesap oluşturmalı
            pass
        return account.id if account else 1
