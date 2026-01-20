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
    UserSession,
    UserPagePermission,
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
    Notification,
    NotificationType,
)

# Dashboard
from database.models.dashboard import (
    DashboardWidget,
    RoleDefaultLayout,
    UserDashboardLayout,
)

__all__ = [
    # User
    "User",
    "Role",
    "Permission",
    "AuditLog",
    "Setting",
    "Sequence",
    "UserSession",
    "UserPagePermission",
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
    "Notification",
    "NotificationType",
    # Dashboard
    "DashboardWidget",
    "RoleDefaultLayout",
    "UserDashboardLayout",
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
from .shift_teams import ShiftTeam, RotationPattern, RotationSchedule

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

# İnsan Kaynakları modülü
from database.models.hr import (
    Department,
    Position,
    Employee,
    Leave,
    Attendance,
    EmploymentType,
    Gender,
    LeaveType,
    LeaveStatus,
    AttendanceStatus,
)

# Kalite modülü
from database.models.quality import (
    InspectionTemplate,
    InspectionCriteria,
    Inspection,
    InspectionResult,
    NonConformance,
    CustomerComplaint,
    CAPA,
    Audit,
    InspectionType,
    InspectionStatus,
    NCRSeverity,
    NCRStatus,
    ComplaintCategory,
    ComplaintStatus,
    CAPAType,
    CAPAStatus,
)

# CRM Modülü
from database.models.crm import (
    Lead,
    LeadStatus,
    LeadSource,
    Opportunity,
    OpportunityStage,
    Activity,
    ActivityType,
)

# Bakım ve Onarım Modülü
from database.models.maintenance import (
    MaintenanceCategory,
    Equipment,
    MaintenanceRequest,
    MaintenanceWorkOrder,
    MaintenanceWorkOrderPart,
    MaintenancePriority,
    MaintenanceStatus,
    WorkOrderStatus,
    MaintenanceType,
    CriticalityLevel,
)

# Firma Modülü
from database.models.company import (
    Company,
    CompanyAddress,
    CompanyBank,
    CompanyContact,
    CompanySettings,
    CompanyDocument,
    CompanyType,
    AddressType,
    BankAccountType,
    ProductionType,
)

# Performans Değerlendirme Modülü
from database.models.performance import (
    EvaluationPeriodType,
    EvaluationStatus,
    CompetencyCategory,
    PerformanceRating,
    EvaluationPeriod,
    Competency,
    PerformanceEvaluation,
    CompetencyScore,
    PerformanceGoal,
)

# Eğitim Takibi Modülü
from database.models.training import (
    TrainingStatus,
    TrainingType,
    CertificateStatus,
    Training,
    TrainingSession,
    TrainingParticipant,
    EmployeeCertificate,
)

# Özlük Dosyası ve İzin Hakediş Modülü
from database.models.personnel import (
    DocumentType,
    DocumentStatus,
    LeaveEntitlementType,
    EmployeeDocument,
    LeaveEntitlementRule,
    LeaveBalance,
)

# Taşıma Birimi (SSCC) Modülü
from database.models.transport_unit import (
    TransportUnit,
    TransportUnitItem,
    TransportUnitType,
    TransportUnitStatus,
)

__all__.extend(
    [
        "TransportUnit",
        "TransportUnitItem",
        "TransportUnitType",
        "TransportUnitStatus",
    ]
)
