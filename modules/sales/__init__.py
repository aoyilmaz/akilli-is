"""
Akıllı İş - Satış Modülü
"""

from .services import (
    CustomerService,
    PriceListService,
    SalesQuoteService,
    SalesOrderService,
    DeliveryNoteService,
    InvoiceService,
)

from .views import (
    CustomerModule,
    PriceListModule,
    SalesQuoteModule,
    SalesOrderModule,
    DeliveryNoteModule,
    InvoiceModule,
)

__all__ = [
    # Services
    "CustomerService",
    "PriceListService",
    "SalesQuoteService",
    "SalesOrderService",
    "DeliveryNoteService",
    "InvoiceService",
    # Modules
    "CustomerModule",
    "PriceListModule",
    "SalesQuoteModule",
    "SalesOrderModule",
    "DeliveryNoteModule",
    "InvoiceModule",
]
