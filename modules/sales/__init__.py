"""
Akıllı İş - Satış Modülü
"""

from .services import (
    CustomerService,
    SalesQuoteService,
    SalesOrderService,
    DeliveryNoteService,
    InvoiceService,
)

from .views import (
    CustomerModule,
    SalesQuoteModule,
    SalesOrderModule,
    DeliveryNoteModule,
    InvoiceModule,
)

__all__ = [
    # Services
    "CustomerService",
    "SalesQuoteService",
    "SalesOrderService",
    "DeliveryNoteService",
    "InvoiceService",
    # Modules
    "CustomerModule",
    "SalesQuoteModule",
    "SalesOrderModule",
    "DeliveryNoteModule",
    "InvoiceModule",
]
