"""
Akilli Is - Finans Modulu Views
"""

from .account_statement_module import AccountStatementModule
from .account_statement_list import AccountStatementListPage

from .receipt_module import ReceiptModule
from .receipt_list import ReceiptListPage
from .receipt_form import ReceiptFormPage

from .payment_module import PaymentModule
from .payment_list import PaymentListPage
from .payment_form import PaymentFormPage

from .reconciliation_module import ReconciliationModule
from .reconciliation_page import ReconciliationPage

__all__ = [
    # Account Statement
    "AccountStatementModule",
    "AccountStatementListPage",
    # Receipt
    "ReceiptModule",
    "ReceiptListPage",
    "ReceiptFormPage",
    # Payment
    "PaymentModule",
    "PaymentListPage",
    "PaymentFormPage",
    # Reconciliation
    "ReconciliationModule",
    "ReconciliationPage",
]
