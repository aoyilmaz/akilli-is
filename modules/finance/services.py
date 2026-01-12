"""
Akıllı İş - Finans Modülü Servisleri
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Tuple
from sqlalchemy import desc, and_, or_, func
from sqlalchemy.orm import joinedload

from database.base import get_session
from database.models.finance import (
    TransactionType,
    PaymentMethod,
    PaymentStatus,
    AccountTransaction,
    Receipt,
    ReceiptAllocation,
    Payment,
    PaymentAllocation,
)
from database.models.sales import Customer, Invoice, InvoiceStatus
from database.models.purchasing import Supplier


class AccountTransactionService:
    """Cari hesap hareketi servisi"""

    def __init__(self):
        self.session = get_session()

    def generate_transaction_no(self) -> str:
        """Otomatik hareket numarası oluştur"""
        today = date.today()
        prefix = f"CHK{today.strftime('%Y%m')}"

        last = (
            self.session.query(AccountTransaction)
            .filter(AccountTransaction.transaction_no.like(f"{prefix}%"))
            .order_by(desc(AccountTransaction.transaction_no))
            .first()
        )

        if last:
            last_num = int(last.transaction_no[-4:])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}{new_num:04d}"

    def get_customer_statement(
        self, customer_id: int, date_from: date = None, date_to: date = None
    ) -> List[AccountTransaction]:
        """Müşteri cari hesap ekstresi"""
        query = (
            self.session.query(AccountTransaction)
            .filter(AccountTransaction.customer_id == customer_id)
            .filter(AccountTransaction.is_active == True)
        )

        if date_from:
            query = query.filter(AccountTransaction.transaction_date >= date_from)
        if date_to:
            query = query.filter(AccountTransaction.transaction_date <= date_to)

        return query.order_by(
            AccountTransaction.transaction_date, AccountTransaction.id
        ).all()

    def get_supplier_statement(
        self, supplier_id: int, date_from: date = None, date_to: date = None
    ) -> List[AccountTransaction]:
        """Tedarikçi cari hesap ekstresi"""
        query = (
            self.session.query(AccountTransaction)
            .filter(AccountTransaction.supplier_id == supplier_id)
            .filter(AccountTransaction.is_active == True)
        )

        if date_from:
            query = query.filter(AccountTransaction.transaction_date >= date_from)
        if date_to:
            query = query.filter(AccountTransaction.transaction_date <= date_to)

        return query.order_by(
            AccountTransaction.transaction_date, AccountTransaction.id
        ).all()

    def get_customer_balance(self, customer_id: int) -> Decimal:
        """Müşteri bakiyesi (Borç - Alacak)"""
        result = (
            self.session.query(
                func.coalesce(func.sum(AccountTransaction.debit), 0)
                - func.coalesce(func.sum(AccountTransaction.credit), 0)
            )
            .filter(AccountTransaction.customer_id == customer_id)
            .filter(AccountTransaction.is_active == True)
            .scalar()
        )
        return Decimal(result) if result else Decimal(0)

    def get_supplier_balance(self, supplier_id: int) -> Decimal:
        """Tedarikçi bakiyesi (Alacak - Borç, tedarikçiye borcumuz)"""
        result = (
            self.session.query(
                func.coalesce(func.sum(AccountTransaction.credit), 0)
                - func.coalesce(func.sum(AccountTransaction.debit), 0)
            )
            .filter(AccountTransaction.supplier_id == supplier_id)
            .filter(AccountTransaction.is_active == True)
            .scalar()
        )
        return Decimal(result) if result else Decimal(0)

    def create_from_invoice(self, invoice: Invoice) -> AccountTransaction:
        """Fatura kesildiğinde cari hesap hareketi oluştur"""
        transaction = AccountTransaction(
            transaction_no=self.generate_transaction_no(),
            transaction_date=invoice.invoice_date,
            transaction_type=TransactionType.INVOICE,
            customer_id=invoice.customer_id,
            invoice_id=invoice.id,
            debit=invoice.total_amount,  # Müşteri borçlanır
            credit=Decimal(0),
            description=f"Fatura: {invoice.invoice_no}",
        )
        self.session.add(transaction)
        self.session.commit()

        # Otomatik yevmiye fişi oluştur
        self._create_journal_entry(transaction)

        return transaction

    def create_from_purchase_invoice(self, invoice) -> AccountTransaction:
        """Satınalma faturası için cari hareket oluştur (Tedarikçiye borç)"""
        transaction = AccountTransaction(
            transaction_no=self.generate_transaction_no(),
            transaction_date=invoice.invoice_date,
            transaction_type=TransactionType.PURCHASE_INVOICE,
            supplier_id=invoice.supplier_id,
            purchase_invoice_id=invoice.id,
            debit=Decimal(0),
            credit=invoice.total_amount,  # Tedarikçiye borcumuz artar
            description=f"Satınalma Faturası: {invoice.invoice_no}",
        )
        self.session.add(transaction)
        self.session.commit()

        # Otomatik yevmiye fişi oluştur
        self._create_journal_entry(transaction)

        return transaction

    def _create_journal_entry(self, transaction: AccountTransaction):
        """
        Cari hareketten otomatik yevmiye fişi oluştur

        Tekdüzen Hesap Planı:
        - 100: Kasa
        - 102: Bankalar
        - 120: Alıcılar (Müşteriler)
        - 320: Satıcılar (Tedarikçiler)
        - 391: Hesaplanan KDV
        - 191: İndirilecek KDV
        - 600: Yurt İçi Satışlar
        - 153: Ticari Mallar
        """
        try:
            from modules.accounting.services import AccountingService

            accounting = AccountingService()
            lines_data = []

            if transaction.transaction_type == TransactionType.INVOICE:
                # Satış Faturası: 120 Alıcılar (B) / 600 Satışlar + 391 KDV (A)
                kdv_orani = Decimal("0.20")  # %20 KDV
                kdv_tutari = transaction.debit * kdv_orani / (1 + kdv_orani)
                net_tutar = transaction.debit - kdv_tutari

                lines_data = [
                    {
                        "account_code": "120.01",
                        "debit": transaction.debit,
                        "credit": Decimal(0),
                    },
                    {
                        "account_code": "600.01",
                        "debit": Decimal(0),
                        "credit": net_tutar,
                    },
                    {
                        "account_code": "391.01",
                        "debit": Decimal(0),
                        "credit": kdv_tutari,
                    },
                ]

            elif transaction.transaction_type == TransactionType.PURCHASE_INVOICE:
                # Satınalma Faturası: 153 Tic.Mal + 191 KDV (B) / 320 Satıcılar (A)
                kdv_orani = Decimal("0.20")
                kdv_tutari = transaction.credit * kdv_orani / (1 + kdv_orani)
                net_tutar = transaction.credit - kdv_tutari

                lines_data = [
                    {
                        "account_code": "153.01",
                        "debit": net_tutar,
                        "credit": Decimal(0),
                    },
                    {
                        "account_code": "191.01",
                        "debit": kdv_tutari,
                        "credit": Decimal(0),
                    },
                    {
                        "account_code": "320.01",
                        "debit": Decimal(0),
                        "credit": transaction.credit,
                    },
                ]

            elif transaction.transaction_type == TransactionType.RECEIPT:
                # Tahsilat: 100/102 Kasa/Banka (B) / 120 Alıcılar (A)
                kasa_hesap = (
                    "100.01"
                    if transaction.payment_method == PaymentMethod.CASH
                    else "102.01"
                )
                lines_data = [
                    {
                        "account_code": kasa_hesap,
                        "debit": transaction.credit,
                        "credit": Decimal(0),
                    },
                    {
                        "account_code": "120.01",
                        "debit": Decimal(0),
                        "credit": transaction.credit,
                    },
                ]

            elif transaction.transaction_type == TransactionType.PAYMENT:
                # Ödeme: 320 Satıcılar (B) / 100/102 Kasa/Banka (A)
                kasa_hesap = (
                    "100.01"
                    if transaction.payment_method == PaymentMethod.CASH
                    else "102.01"
                )
                lines_data = [
                    {
                        "account_code": "320.01",
                        "debit": transaction.debit,
                        "credit": Decimal(0),
                    },
                    {
                        "account_code": kasa_hesap,
                        "debit": Decimal(0),
                        "credit": transaction.debit,
                    },
                ]

            if lines_data:
                journal = accounting.create_journal(
                    lines_data,
                    entry_date=transaction.transaction_date,
                    description=transaction.description,
                )
                # Yevmiye ID'sini cari harekete bağla
                if journal:
                    transaction.journal_entry_id = journal.id
                    self.session.commit()

        except Exception as e:
            # Muhasebe modülü yüklü değilse veya hata olursa sessizce devam et
            print(f"Yevmiye fişi oluşturulamadı: {e}")

    def create_from_receipt(
        self,
        receipt_id: int,
        receipt_date: date,
        customer_id: int,
        amount: Decimal,
        payment_method: PaymentMethod,
        receipt_no: str,
        check_no: str = None,
    ) -> AccountTransaction:
        """Tahsilat yapıldığında cari hesap hareketi oluştur (primitive değerlerle)"""
        transaction = AccountTransaction(
            transaction_no=self.generate_transaction_no(),
            transaction_date=receipt_date,
            transaction_type=TransactionType.RECEIPT,
            customer_id=customer_id,
            receipt_id=receipt_id,
            debit=Decimal(0),
            credit=amount,  # Müşteri borcunu öder
            payment_method=payment_method,
            reference_no=check_no,
            description=f"Tahsilat: {receipt_no}",
        )
        self.session.add(transaction)
        self.session.commit()
        return transaction

    def create_from_payment(
        self,
        payment_id: int,
        payment_date: date,
        supplier_id: int,
        amount: Decimal,
        payment_method: PaymentMethod,
        payment_no: str,
        check_no: str = None,
    ) -> AccountTransaction:
        """Ödeme yapıldığında cari hesap hareketi oluştur (primitive değerlerle)"""
        transaction = AccountTransaction(
            transaction_no=self.generate_transaction_no(),
            transaction_date=payment_date,
            transaction_type=TransactionType.PAYMENT,
            supplier_id=supplier_id,
            payment_id=payment_id,
            debit=amount,  # Tedarikçiye olan borcumuz azalır
            credit=Decimal(0),
            payment_method=payment_method,
            reference_no=check_no,
            description=f"Ödeme: {payment_no}",
        )
        self.session.add(transaction)
        self.session.commit()
        return transaction

    def create_opening_balance(
        self,
        customer_id: int = None,
        supplier_id: int = None,
        amount: Decimal = Decimal(0),
        transaction_date: date = None,
        description: str = "Açılış bakiyesi",
    ) -> AccountTransaction:
        """Açılış bakiyesi girişi"""
        if not customer_id and not supplier_id:
            raise ValueError("Müşteri veya tedarikçi belirtilmeli")

        transaction = AccountTransaction(
            transaction_no=self.generate_transaction_no(),
            transaction_date=transaction_date or date.today(),
            transaction_type=TransactionType.OPENING,
            customer_id=customer_id,
            supplier_id=supplier_id,
            debit=amount if amount > 0 else Decimal(0),
            credit=abs(amount) if amount < 0 else Decimal(0),
            description=description,
        )
        self.session.add(transaction)
        self.session.commit()
        return transaction

    def create_adjustment(
        self,
        customer_id: int = None,
        supplier_id: int = None,
        debit: Decimal = Decimal(0),
        credit: Decimal = Decimal(0),
        transaction_date: date = None,
        description: str = "Düzeltme kaydı",
    ) -> AccountTransaction:
        """Düzeltme kaydı"""
        if not customer_id and not supplier_id:
            raise ValueError("Müşteri veya tedarikçi belirtilmeli")

        transaction = AccountTransaction(
            transaction_no=self.generate_transaction_no(),
            transaction_date=transaction_date or date.today(),
            transaction_type=TransactionType.ADJUSTMENT,
            customer_id=customer_id,
            supplier_id=supplier_id,
            debit=debit,
            credit=credit,
            description=description,
        )
        self.session.add(transaction)
        self.session.commit()
        return transaction


class ReceiptService:
    """Tahsilat servisi (Müşterilerden)"""

    def __init__(self):
        self.session = get_session()
        self.transaction_service = AccountTransactionService()

    def generate_receipt_no(self) -> str:
        """Otomatik tahsilat numarası oluştur"""
        today = date.today()
        prefix = f"THS{today.strftime('%Y%m')}"

        last = (
            self.session.query(Receipt)
            .filter(Receipt.receipt_no.like(f"{prefix}%"))
            .order_by(desc(Receipt.receipt_no))
            .first()
        )

        if last:
            last_num = int(last.receipt_no[-4:])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}{new_num:04d}"

    def get_all(
        self,
        customer_id: int = None,
        date_from: date = None,
        date_to: date = None,
        status: PaymentStatus = None,
    ) -> List[Receipt]:
        """Tahsilatları listele"""
        query = (
            self.session.query(Receipt)
            .options(joinedload(Receipt.customer))
            .filter(Receipt.is_active == True)
        )

        if customer_id:
            query = query.filter(Receipt.customer_id == customer_id)
        if date_from:
            query = query.filter(Receipt.receipt_date >= date_from)
        if date_to:
            query = query.filter(Receipt.receipt_date <= date_to)
        if status:
            query = query.filter(Receipt.status == status)

        return query.order_by(desc(Receipt.receipt_date), desc(Receipt.id)).all()

    def get_by_id(self, receipt_id: int) -> Optional[Receipt]:
        """ID ile tahsilat getir"""
        return (
            self.session.query(Receipt)
            .options(
                joinedload(Receipt.customer),
                joinedload(Receipt.allocations).joinedload(ReceiptAllocation.invoice),
            )
            .filter(Receipt.id == receipt_id)
            .first()
        )

    def create(
        self,
        customer_id: int,
        amount: Decimal,
        payment_method: PaymentMethod,
        receipt_date: date = None,
        invoice_allocations: List[Dict] = None,
        **kwargs,
    ) -> Receipt:
        """Yeni tahsilat oluştur"""
        receipt_no = self.generate_receipt_no()
        actual_receipt_date = receipt_date or date.today()

        receipt = Receipt(
            receipt_no=receipt_no,
            receipt_date=actual_receipt_date,
            customer_id=customer_id,
            amount=amount,
            payment_method=payment_method,
            status=PaymentStatus.COMPLETED,
            **kwargs,
        )
        self.session.add(receipt)
        self.session.flush()

        # Commit öncesi değerleri sakla (detached object sorunu için)
        receipt_id = receipt.id
        check_no = kwargs.get("check_no")

        # Fatura dağılımları
        if invoice_allocations:
            for alloc in invoice_allocations:
                allocation = ReceiptAllocation(
                    receipt_id=receipt_id,
                    invoice_id=alloc["invoice_id"],
                    amount=alloc["amount"],
                )
                self.session.add(allocation)

                # Fatura ödeme durumunu güncelle
                self._update_invoice_payment_status(alloc["invoice_id"])

        # Önce receipt'i commit et (FK constraint için gerekli)
        self.session.commit()

        # Cari hesap hareketi oluştur (primitive değerlerle)
        self.transaction_service.create_from_receipt(
            receipt_id=receipt_id,
            receipt_date=actual_receipt_date,
            customer_id=customer_id,
            amount=amount,
            payment_method=payment_method,
            receipt_no=receipt_no,
            check_no=check_no,
        )

        return receipt

    def apply_to_invoices(self, receipt_id: int, allocations: List[Dict]) -> Receipt:
        """Tahsilatı faturalara uygula"""
        receipt = self.get_by_id(receipt_id)
        if not receipt:
            raise ValueError("Tahsilat bulunamadı")

        # Mevcut dağılımları temizle
        for alloc in receipt.allocations:
            self.session.delete(alloc)

        # Yeni dağılımlar
        total_allocated = Decimal(0)
        for alloc_data in allocations:
            if total_allocated + alloc_data["amount"] > receipt.amount:
                raise ValueError("Dağıtılan tutar tahsilat tutarından fazla olamaz")

            allocation = ReceiptAllocation(
                receipt_id=receipt.id,
                invoice_id=alloc_data["invoice_id"],
                amount=alloc_data["amount"],
            )
            self.session.add(allocation)
            total_allocated += alloc_data["amount"]

            # Fatura ödeme durumunu güncelle
            self._update_invoice_payment_status(alloc_data["invoice_id"])

        self.session.commit()
        return receipt

    def cancel(self, receipt_id: int) -> Receipt:
        """Tahsilatı iptal et"""
        receipt = self.get_by_id(receipt_id)
        if not receipt:
            raise ValueError("Tahsilat bulunamadı")

        if receipt.status == PaymentStatus.CANCELLED:
            raise ValueError("Tahsilat zaten iptal edilmiş")

        # Fatura dağılımlarını iptal et
        invoice_ids = [a.invoice_id for a in receipt.allocations]
        for alloc in receipt.allocations:
            self.session.delete(alloc)

        receipt.status = PaymentStatus.CANCELLED

        # İlgili cari hesap hareketini iptal et
        transaction = (
            self.session.query(AccountTransaction)
            .filter(AccountTransaction.receipt_id == receipt_id)
            .first()
        )
        if transaction:
            transaction.is_active = False

        self.session.commit()

        # Fatura durumlarını güncelle
        for invoice_id in invoice_ids:
            self._update_invoice_payment_status(invoice_id)

        return receipt

    def _update_invoice_payment_status(self, invoice_id: int):
        """Fatura ödeme durumunu güncelle"""
        invoice = self.session.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return

        # Toplam tahsilat tutarı
        total_paid = (
            self.session.query(func.coalesce(func.sum(ReceiptAllocation.amount), 0))
            .join(Receipt)
            .filter(
                ReceiptAllocation.invoice_id == invoice_id,
                Receipt.status != PaymentStatus.CANCELLED,
            )
            .scalar()
        )

        total_paid = Decimal(total_paid) if total_paid else Decimal(0)

        if total_paid >= invoice.total_amount:
            invoice.status = InvoiceStatus.PAID
        elif total_paid > 0:
            invoice.status = InvoiceStatus.PARTIAL_PAID
        elif invoice.status in [InvoiceStatus.PAID, InvoiceStatus.PARTIAL_PAID]:
            invoice.status = InvoiceStatus.ISSUED

        invoice.paid_amount = total_paid
        self.session.commit()

    def get_customer_open_invoices(self, customer_id: int) -> List[Invoice]:
        """Müşterinin açık faturalarını getir"""
        return (
            self.session.query(Invoice)
            .filter(
                Invoice.customer_id == customer_id,
                Invoice.status.in_(
                    [
                        InvoiceStatus.ISSUED,
                        InvoiceStatus.PARTIAL_PAID,
                        InvoiceStatus.OVERDUE,
                    ]
                ),
                Invoice.is_active == True,
            )
            .order_by(Invoice.invoice_date)
            .all()
        )


class PaymentService:
    """Ödeme servisi (Tedarikçilere)"""

    def __init__(self):
        self.session = get_session()
        self.transaction_service = AccountTransactionService()

    def generate_payment_no(self) -> str:
        """Otomatik ödeme numarası oluştur"""
        today = date.today()
        prefix = f"ODM{today.strftime('%Y%m')}"

        last = (
            self.session.query(Payment)
            .filter(Payment.payment_no.like(f"{prefix}%"))
            .order_by(desc(Payment.payment_no))
            .first()
        )

        if last:
            last_num = int(last.payment_no[-4:])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}{new_num:04d}"

    def get_all(
        self,
        supplier_id: int = None,
        date_from: date = None,
        date_to: date = None,
        status: PaymentStatus = None,
    ) -> List[Payment]:
        """Ödemeleri listele"""
        query = (
            self.session.query(Payment)
            .options(joinedload(Payment.supplier))
            .filter(Payment.is_active == True)
        )

        if supplier_id:
            query = query.filter(Payment.supplier_id == supplier_id)
        if date_from:
            query = query.filter(Payment.payment_date >= date_from)
        if date_to:
            query = query.filter(Payment.payment_date <= date_to)
        if status:
            query = query.filter(Payment.status == status)

        return query.order_by(desc(Payment.payment_date), desc(Payment.id)).all()

    def get_by_id(self, payment_id: int) -> Optional[Payment]:
        """ID ile ödeme getir"""
        return (
            self.session.query(Payment)
            .options(joinedload(Payment.supplier), joinedload(Payment.allocations))
            .filter(Payment.id == payment_id)
            .first()
        )

    def create(
        self,
        supplier_id: int,
        amount: Decimal,
        payment_method: PaymentMethod,
        payment_date: date = None,
        allocations: List[Dict] = None,
        **kwargs,
    ) -> Payment:
        """Yeni ödeme oluştur"""
        payment_no = self.generate_payment_no()
        actual_payment_date = payment_date or date.today()

        payment = Payment(
            payment_no=payment_no,
            payment_date=actual_payment_date,
            supplier_id=supplier_id,
            amount=amount,
            payment_method=payment_method,
            status=PaymentStatus.COMPLETED,
            **kwargs,
        )
        self.session.add(payment)
        self.session.flush()

        # Commit öncesi değerleri sakla (detached object sorunu için)
        payment_id = payment.id
        check_no = kwargs.get("check_no")

        # Fatura/belge dağılımları
        if allocations:
            for alloc in allocations:
                allocation = PaymentAllocation(
                    payment_id=payment_id,
                    reference_type=alloc.get("reference_type", "purchase_invoice"),
                    reference_id=alloc.get("reference_id"),
                    amount=alloc["amount"],
                )
                self.session.add(allocation)

        # Önce payment'ı commit et (FK constraint için gerekli)
        self.session.commit()

        # Cari hesap hareketi oluştur (primitive değerlerle)
        self.transaction_service.create_from_payment(
            payment_id=payment_id,
            payment_date=actual_payment_date,
            supplier_id=supplier_id,
            amount=amount,
            payment_method=payment_method,
            payment_no=payment_no,
            check_no=check_no,
        )

        return payment

    def cancel(self, payment_id: int) -> Payment:
        """Ödemeyi iptal et"""
        payment = self.get_by_id(payment_id)
        if not payment:
            raise ValueError("Ödeme bulunamadı")

        if payment.status == PaymentStatus.CANCELLED:
            raise ValueError("Ödeme zaten iptal edilmiş")

        # Dağılımları temizle
        for alloc in payment.allocations:
            self.session.delete(alloc)

        payment.status = PaymentStatus.CANCELLED

        # İlgili cari hesap hareketini iptal et
        transaction = (
            self.session.query(AccountTransaction)
            .filter(AccountTransaction.payment_id == payment_id)
            .first()
        )
        if transaction:
            transaction.is_active = False

        self.session.commit()
        return payment


class ReconciliationService:
    """Mutabakat servisi"""

    def __init__(self):
        self.session = get_session()
        self.transaction_service = AccountTransactionService()

    def get_customer_open_items(self, customer_id: int) -> Dict:
        """Müşteri açık kalemleri"""
        # Bakiye
        balance = self.transaction_service.get_customer_balance(customer_id)

        # Açık faturalar
        open_invoices = (
            self.session.query(Invoice)
            .filter(
                Invoice.customer_id == customer_id,
                Invoice.status.in_(
                    [
                        InvoiceStatus.ISSUED,
                        InvoiceStatus.PARTIAL_PAID,
                        InvoiceStatus.OVERDUE,
                    ]
                ),
                Invoice.is_active == True,
            )
            .order_by(Invoice.invoice_date)
            .all()
        )

        invoices_data = []
        for inv in open_invoices:
            remaining = (inv.total_amount or Decimal(0)) - (
                inv.paid_amount or Decimal(0)
            )
            invoices_data.append(
                {
                    "invoice_id": inv.id,
                    "invoice_no": inv.invoice_no,
                    "invoice_date": inv.invoice_date,
                    "due_date": inv.due_date,
                    "total_amount": inv.total_amount,
                    "paid_amount": inv.paid_amount or Decimal(0),
                    "remaining_amount": remaining,
                    "status": inv.status.value if inv.status else "",
                }
            )

        return {
            "balance": balance,
            "open_invoices": invoices_data,
            "total_open_amount": sum(i["remaining_amount"] for i in invoices_data),
        }

    def get_supplier_open_items(self, supplier_id: int) -> Dict:
        """Tedarikçi açık kalemleri"""
        # Bakiye (tedarikçiye borcumuz)
        balance = self.transaction_service.get_supplier_balance(supplier_id)

        # Not: Tedarikçi faturaları için ayrı bir model gerekebilir
        # Şimdilik sadece bakiyeyi döndürüyoruz

        return {
            "balance": balance,
            "open_items": [],
            "total_open_amount": balance,
        }

    def get_reconciliation_report(
        self,
        customer_id: int = None,
        supplier_id: int = None,
        date_from: date = None,
        date_to: date = None,
    ) -> Dict:
        """Mutabakat raporu"""
        if customer_id:
            transactions = self.transaction_service.get_customer_statement(
                customer_id, date_from, date_to
            )
            balance = self.transaction_service.get_customer_balance(customer_id)
            entity_type = "customer"
            entity = (
                self.session.query(Customer).filter(Customer.id == customer_id).first()
            )
        elif supplier_id:
            transactions = self.transaction_service.get_supplier_statement(
                supplier_id, date_from, date_to
            )
            balance = self.transaction_service.get_supplier_balance(supplier_id)
            entity_type = "supplier"
            entity = (
                self.session.query(Supplier).filter(Supplier.id == supplier_id).first()
            )
        else:
            raise ValueError("Müşteri veya tedarikçi belirtilmeli")

        # Hareket detayları
        movements = []
        running_balance = Decimal(0)
        for t in transactions:
            if entity_type == "customer":
                running_balance += (t.debit or Decimal(0)) - (t.credit or Decimal(0))
            else:
                running_balance += (t.credit or Decimal(0)) - (t.debit or Decimal(0))

            movements.append(
                {
                    "date": t.transaction_date,
                    "transaction_no": t.transaction_no,
                    "type": t.transaction_type.value if t.transaction_type else "",
                    "description": t.description,
                    "debit": t.debit,
                    "credit": t.credit,
                    "balance": running_balance,
                }
            )

        return {
            "entity_type": entity_type,
            "entity_name": entity.name if entity else "",
            "entity_code": getattr(entity, "code", "") if entity else "",
            "date_from": date_from,
            "date_to": date_to,
            "movements": movements,
            "total_debit": sum(t.debit or Decimal(0) for t in transactions),
            "total_credit": sum(t.credit or Decimal(0) for t in transactions),
            "closing_balance": balance,
        }
