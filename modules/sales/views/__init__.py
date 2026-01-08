"""
Akıllı İş - Satış Modülü Views
"""

from .customer_module import CustomerModule
from .customer_list import CustomerListPage
from .customer_form import CustomerFormPage

from .sales_quote_module import SalesQuoteModule
from .sales_quote_list import SalesQuoteListPage
from .sales_quote_form import SalesQuoteFormPage

from .sales_order_module import SalesOrderModule
from .sales_order_list import SalesOrderListPage
from .sales_order_form import SalesOrderFormPage

from .delivery_note_module import DeliveryNoteModule
from .delivery_note_list import DeliveryNoteListPage
from .delivery_note_form import DeliveryNoteFormPage

from .invoice_module import InvoiceModule
from .invoice_list import InvoiceListPage
from .invoice_form import InvoiceFormPage

__all__ = [
    # Customer
    "CustomerModule",
    "CustomerListPage",
    "CustomerFormPage",
    # Sales Quote
    "SalesQuoteModule",
    "SalesQuoteListPage",
    "SalesQuoteFormPage",
    # Sales Order
    "SalesOrderModule",
    "SalesOrderListPage",
    "SalesOrderFormPage",
    # Delivery Note
    "DeliveryNoteModule",
    "DeliveryNoteListPage",
    "DeliveryNoteFormPage",
    # Invoice
    "InvoiceModule",
    "InvoiceListPage",
    "InvoiceFormPage",
]
