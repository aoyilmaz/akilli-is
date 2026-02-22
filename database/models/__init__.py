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
    LotSizingProcedure,
    StockRequest,
    StockRequestStatus,
    MrpType,
    LotSizePolicy,
    ValuationMethod,
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
    LabelTemplate,
)

# Dashboard
from database.models.dashboard import (
    DashboardWidget,
    RoleDefaultLayout,
    UserDashboardLayout,
)

# DMS
from database.models.dms import (
    Document,
    DocumentRelation,
)

# Company
from database.models.company import (
    Company,
    CompanyAddress,
    CompanyBank,
    CompanyContact,
    CompanySettings,
    CompanyDocument,
)

# Satis
from database.models.sales import (
    Customer,
    SalesOrder,
    SalesOrderItem,
    SalesQuote,
    SalesQuoteItem,
    DeliveryNote,
    DeliveryNoteItem,
    Invoice,
    SalesOrderStatus,
    SalesQuoteStatus,
    DeliveryNoteStatus,
)

# Satin Alma
from database.models.purchasing import (
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequest,
    PurchaseRequestItem,
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseInvoice,
    PurchaseOrderStatus,
    PurchaseRequestStatus,
    GoodsReceiptStatus,
    PurchaseInvoiceStatus,
    VendorRating,
)

# CRM
from database.models.crm import Opportunity

# Shipping
from database.models.shipping import Vehicle, Driver, Shipment
from database.models.transport_unit import (
    TransportUnit,
    TransportUnitItem,
    TransportUnitType,
    TransportUnitStatus,
)

# Production
from database.models.production import (
    BillOfMaterials,
    BOMLine,
    WorkStation,
    BOMOperation,
    BOMByProduct,
    WorkOrder,
    WorkOrderLine,
    WorkOrderOperation,
    WorkOrderOperationPersonnel,
    WorkOrderByProduct,
    BOMType,
    BOMStatus,
    WorkOrderStatus,
    WorkStationType,
)

# MRP
from database.models.mrp import (
    MRPRun,
    MRPLine,
    MRPRunStatus,
    DemandSource,
    SuggestionType,
)

# Quality
from database.models.quality import (
    InspectionTemplate,
    InspectionCriteria,
    Inspection,
    InspectionResult,
    NonConformance,
    CustomerComplaint,
    CAPA,
    Audit,
)

# HR
from database.models.hr import (
    Department,
    Position,
    Employee,
    Leave,
    Attendance,
    Payroll,
    JobPosting,
    JobApplication,
    Interview,
)

# Shifts & Calendar
from database.models.shift_teams import (
    ShiftTeam,
    RotationPattern,
    RotationSchedule,
)
from database.models.calendar import (
    ProductionShift,
    ProductionHoliday,
    WorkstationSchedule,
)

# Iade Yonetimi
from database.models.returns import (
    ReturnOrder,
    ReturnOrderLine,
    ReturnType,
    ReturnStatus,
    ReturnReason,
)

# Muhasebe
from database.models.accounting import (
    Account,
    AccountType,
    JournalEntry,
    JournalEntryLine,
    JournalEntryStatus,
)

# Workflow
from database.models.workflow import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowInstance,
    WorkflowAction,
    WorkflowStatus,
    WorkflowActionType,
)

# Finance
from database.models.finance import (
    AccountTransaction,
    Receipt,
    ReceiptAllocation,
    Payment,
    PaymentAllocation,
)

# E-Invoice
from database.models.einvoice import (
    EInvoice,
    EInvoiceSeries,
    EInvoiceSettings,
)

# Fixed Assets
from database.models.fixed_asset import (
    FixedAsset,
    DepreciationEntry,
)

# Maintenance
from database.models.maintenance import (
    MaintenanceCategory,
    Equipment,
    EquipmentSparePart,
    EquipmentDowntime,
    MaintenanceRequest,
    MaintenanceRequestAttachment,
    MaintenanceChecklist,
    MaintenanceChecklistItem,
    MaintenanceWorkOrder,
    MaintenanceWorkOrderPart,
    WorkOrderAttachment,
    WorkOrderChecklistResult,
    MaintenancePlan,
)

# Personnel (Extra)
from database.models.personnel import (
    EmployeeDocument,
    LeaveEntitlementRule,
    LeaveBalance,
)

# Training
from database.models.training import (
    Training,
    TrainingSession,
    TrainingParticipant,
    EmployeeCertificate,
)

# Performance
from database.models.performance import (
    EvaluationPeriod,
    Competency,
    PerformanceEvaluation,
    CompetencyScore,
    PerformanceGoal,
)

# Route
from database.models.route import (
    Route,
    RouteStop,
)

# Development
from database.models.development import (
    ErrorLog,
    TraceSession,
    TraceEvent,
)

# Contracts
from database.models.contracts import (
    Contract,
    ContractLine,
    ContractType,
    ContractStatus,
)

# Traceability
from database.models.traceability import (
    Lot,
    SerialNumber,
    TraceLink,
    LotStatus,
)

# APS
from database.models.aps import (
    APSScenario,
    PlannedTask,
    SchedulingMode,
)

# Messaging
from database.models.messaging import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageAttachment,
    MessageStar,
    NotificationPreference,
    ConversationType,
    MessagePriority,
)

# Project Management
from database.models.project import (
    Project,
    ProjectTask,
    TaskDependency,
    ProjectResource,
    TimeEntry,
    ProjectStatus,
    TaskPriority,
    TaskStatus,
    DependencyType,
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
    "LotSizingProcedure",
    "StockRequest",
    "StockRequestStatus",
    "MrpType",
    "LotSizePolicy",
    "ValuationMethod",
    # Company
    # Company
    "Company",
    "CompanyAddress",
    "CompanyBank",
    "CompanyContact",
    "CompanySettings",
    "CompanyDocument",
    # Sales
    "Customer",
    "SalesOrder",
    "SalesOrderItem",
    "SalesQuote",
    "SalesQuoteItem",
    "DeliveryNote",
    "DeliveryNoteItem",
    "Invoice",
    "SalesOrderStatus",
    "SalesQuoteStatus",
    "DeliveryNoteStatus",
    # Purchasing
    "Supplier",
    "PurchaseOrder",
    "PurchaseOrderItem",
    "PurchaseRequest",
    "PurchaseRequestItem",
    "GoodsReceipt",
    "GoodsReceiptItem",
    "PurchaseInvoice",
    "PurchaseOrderStatus",
    "PurchaseRequestStatus",
    "GoodsReceiptStatus",
    "PurchaseInvoiceStatus",
    "VendorRating",
    # CRM
    "Opportunity",
    # RFQ
    "RFQ",
    "RFQItem",
    "RFQSupplier",
    "RFQSupplierItem",
    # Shipping
    "Vehicle",
    "Driver",
    "Shipment",
    "TransportUnit",
    "TransportUnitItem",
    "TransportUnitType",
    "TransportUnitStatus",
    # Production
    "BillOfMaterials",
    "BOMLine",
    "WorkStation",
    "BOMOperation",
    "BOMByProduct",
    "WorkOrder",
    "WorkOrderLine",
    "WorkOrderOperation",
    "WorkOrderOperationPersonnel",
    "WorkOrderByProduct",
    "BOMType",
    "BOMStatus",
    "WorkOrderStatus",
    "WorkStationType",
    # MRP
    "MRPRun",
    "MRPLine",
    "MRPRunStatus",
    "DemandSource",
    "SuggestionType",
    # Quality
    "InspectionTemplate",
    "InspectionCriteria",
    "Inspection",
    "InspectionResult",
    "NonConformance",
    "CustomerComplaint",
    "CAPA",
    "Audit",
    # HR
    "Department",
    "Position",
    "Employee",
    "Leave",
    "Attendance",
    "Payroll",
    "JobPosting",
    "JobApplication",
    "Interview",
    # Shifts & Calendar
    "ShiftTeam",
    "RotationPattern",
    "RotationSchedule",
    "ProductionShift",
    "ProductionHoliday",
    "WorkstationSchedule",
    # Common
    "Currency",
    "ExchangeRate",
    "Country",
    "City",
    "District",
    "Attachment",
    "Note",
    "Notification",
    "Notification",
    "NotificationType",
    "LabelTemplate",
    # Dashboard
    "DashboardWidget",
    "RoleDefaultLayout",
    "UserDashboardLayout",
    # DMS
    "Document",
    "DocumentRelation",
    # Returns
    "ReturnOrder",
    "ReturnOrderLine",
    "ReturnType",
    "ReturnStatus",
    "ReturnReason",
    # Accounting
    "Account",
    "AccountType",
    "JournalEntry",
    "JournalEntryLine",
    "JournalEntryStatus",
    # Workflow
    "WorkflowDefinition",
    "WorkflowStep",
    "WorkflowInstance",
    "WorkflowAction",
    "WorkflowStatus",
    "WorkflowActionType",
    # Finance
    "AccountTransaction",
    "Receipt",
    "ReceiptAllocation",
    "Payment",
    "PaymentAllocation",
    # E-Invoice
    "EInvoice",
    "EInvoiceSeries",
    "EInvoiceSettings",
    # Fixed Assets
    "FixedAsset",
    "DepreciationEntry",
    # Maintenance
    "MaintenanceCategory",
    "Equipment",
    "EquipmentSparePart",
    "EquipmentDowntime",
    "MaintenanceRequest",
    "MaintenanceRequestAttachment",
    "MaintenanceChecklist",
    "MaintenanceChecklistItem",
    "MaintenanceWorkOrder",
    "MaintenanceWorkOrderPart",
    "WorkOrderAttachment",
    "WorkOrderChecklistResult",
    "MaintenancePlan",
    # Personnel
    "EmployeeDocument",
    "LeaveEntitlementRule",
    "LeaveBalance",
    # Training
    "Training",
    "TrainingSession",
    "TrainingParticipant",
    "EmployeeCertificate",
    # Performance
    "EvaluationPeriod",
    "Competency",
    "PerformanceEvaluation",
    "CompetencyScore",
    "PerformanceGoal",
    # Route
    "Route",
    "RouteStop",
    # Development
    "ErrorLog",
    "TraceSession",
    "TraceEvent",
    # Contracts
    "Contract",
    "ContractLine",
    "ContractType",
    "ContractStatus",
    # Traceability
    "Lot",
    "SerialNumber",
    "TraceLink",
    "LotStatus",
    # APS
    "APSScenario",
    "PlannedTask",
    "SchedulingMode",
    # Project Management
    "Project",
    "ProjectTask",
    "TaskDependency",
    "ProjectResource",
    "TimeEntry",
    "ProjectStatus",
    "TaskPriority",
    "TaskStatus",
    "DependencyType",
    # Messaging
    "Conversation",
    "ConversationParticipant",
    "Message",
    "MessageAttachment",
    "MessageStar",
    "NotificationPreference",
    "ConversationType",
    "MessagePriority",
]
