"""
Akıllı İş - Satın Alma Views
"""

from .supplier_list import SupplierListPage
from .supplier_form import SupplierFormPage
from .supplier_module import SupplierModule

from .purchase_request_list import PurchaseRequestListPage
from .purchase_request_form import PurchaseRequestFormPage
from .purchase_request_module import PurchaseRequestModule

from .purchase_order_list import PurchaseOrderListPage
from .purchase_order_form import PurchaseOrderFormPage
from .purchase_order_module import PurchaseOrderModule

from .goods_receipt_list import GoodsReceiptListPage
from .goods_receipt_form import GoodsReceiptFormPage
from .goods_receipt_module import GoodsReceiptModule

from .purchase_invoice_list import PurchaseInvoiceListPage
from .purchase_invoice_form import PurchaseInvoiceFormPage
from .purchase_invoice_module import PurchaseInvoiceModule

__all__ = [
    "SupplierListPage",
    "SupplierFormPage",
    "SupplierModule",
    "PurchaseRequestListPage",
    "PurchaseRequestFormPage",
    "PurchaseRequestModule",
    "PurchaseOrderListPage",
    "PurchaseOrderFormPage",
    "PurchaseOrderModule",
    "GoodsReceiptListPage",
    "GoodsReceiptFormPage",
    "GoodsReceiptModule",
    "PurchaseInvoiceListPage",
    "PurchaseInvoiceFormPage",
    "PurchaseInvoiceModule",
]
