"""
Bakım Modülü - Views
"""

from modules.maintenance.views.base import MaintenanceBaseWidget
from modules.maintenance.views.equipment_module import (
    EquipmentListWidget,
    EquipmentDialog,
    EquipmentDetailDialog,
)
from modules.maintenance.views.request_module import (
    MaintenanceRequestWidget,
    RequestDialog,
)
from modules.maintenance.views.work_order_module import (
    WorkOrderManagerWidget,
    WorkOrderDialog,
    WorkOrderDetailsDialog,
    AddPartDialog,
)
from modules.maintenance.views.plan_module import (
    MaintenancePlanWidget,
    PlanDialog,
    MaintenanceCalendarWidget,
)
from modules.maintenance.views.reports_module import (
    ReportingWidget,
    KPIDashboardWidget,
    CostAnalysisWidget,
)
from modules.maintenance.views.checklist_module import (
    ChecklistEditorWidget,
    ChecklistDialog,
)
from modules.maintenance.views.downtime_module import (
    DowntimeTrackerWidget,
    DowntimeStartDialog,
)

__all__ = [
    "MaintenanceBaseWidget",
    "EquipmentListWidget",
    "EquipmentDialog",
    "EquipmentDetailDialog",
    "MaintenanceRequestWidget",
    "RequestDialog",
    "WorkOrderManagerWidget",
    "WorkOrderDialog",
    "WorkOrderDetailsDialog",
    "AddPartDialog",
    "MaintenancePlanWidget",
    "PlanDialog",
    "MaintenanceCalendarWidget",
    "ReportingWidget",
    "KPIDashboardWidget",
    "CostAnalysisWidget",
    "ChecklistEditorWidget",
    "ChecklistDialog",
    "DowntimeTrackerWidget",
    "DowntimeStartDialog",
]
