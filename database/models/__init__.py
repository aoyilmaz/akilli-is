"""
Akıllı İş - Veritabanı Modelleri
"""

# Kullanıcı ve yetkilendirme
from database.models.user import (
    User,
    Role,
    Permission,
    AuditLog,
    Setting,
    Sequence,
    user_roles,
    role_permissions,
)

# Stok yönetimi
from database.models.inventory import (
    Unit,
    UnitConversion,
    ItemCategory,
    Item,
    ItemBarcode,
    Warehouse,
    WarehouseLocation,
    StockBalance,
    StockMovement,
    ItemType,
    StockMovementType,
)

# Ortak tablolar
from database.models.common import (
    Currency,
    ExchangeRate,
    Country,
    City,
    District,
    Attachment,
    Note,
)

__all__ = [
    # User
    "User",
    "Role",
    "Permission",
    "AuditLog",
    "Setting",
    "Sequence",
    "user_roles",
    "role_permissions",
    # Inventory
    "Unit",
    "UnitConversion",
    "ItemCategory",
    "Item",
    "ItemBarcode",
    "Warehouse",
    "WarehouseLocation",
    "StockBalance",
    "StockMovement",
    "ItemType",
    "StockMovementType",
    # Common
    "Currency",
    "ExchangeRate",
    "Country",
    "City",
    "District",
    "Attachment",
    "Note",
]

from .production import (
    BillOfMaterials,
    BOMLine,
    BOMOperation,
    BOMStatus,
    WorkStation,
    WorkStationType,
    WorkOrder,
    WorkOrderLine,
    WorkOrderOperation,
    WorkOrderStatus,
    WorkOrderPriority,
)
from .calendar import ProductionShift, ProductionHoliday, WorkstationSchedule

from .purchasing import (
    Supplier,
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseOrder,
    PurchaseOrderItem,
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseInvoice,
    PurchaseInvoiceItem,
    PurchaseRequestStatus,
    PurchaseOrderStatus,
    GoodsReceiptStatus,
    PurchaseInvoiceStatus,
    Currency,
)

# Geliştirme modülü
from database.models.development import (
    ErrorLog,
    ErrorSeverity,
)

# Satış modülü
from database.models.sales import (
    Customer,
    PriceList,
    PriceListItem,
    PriceListType,
    SalesQuote,
    SalesQuoteItem,
    SalesQuoteStatus,
    SalesOrder,
    SalesOrderItem,
    SalesOrderStatus,
    DeliveryNote,
    DeliveryNoteItem,
    DeliveryNoteStatus,
    Invoice,
    InvoiceItem,
    InvoiceStatus,
)

# Finans modülü
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

# Muhasebe modülü
from database.models.accounting import (
    AccountType,
    JournalEntryStatus,
    Account,
    FiscalPeriod,
    JournalEntry,
    JournalEntryLine,
)

# MRP modülü
from database.models.mrp import (
    MRPRunStatus,
    DemandSource,
    SuggestionType,
    MRPRun,
    MRPLine,
)
