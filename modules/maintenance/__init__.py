"""
Bakım Onarım (CMMS) Modülü

Bu modül şunları içerir:
- Ekipman yönetimi ve takibi
- Arıza/bakım talepleri
- İş emirleri
- Periyodik bakım planları
- Duruş takibi ve KPI'lar
- Kontrol listeleri
- Raporlar ve analizler
"""

from modules.maintenance.services import MaintenanceService
from modules.maintenance.views import (
    EquipmentListWidget,
    EquipmentDialog,
    EquipmentDetailDialog,
    MaintenanceRequestWidget,
    RequestDialog,
    WorkOrderManagerWidget,
    WorkOrderDialog,
    WorkOrderDetailsDialog,
    MaintenancePlanWidget,
    PlanDialog,
    MaintenanceCalendarWidget,
    DowntimeTrackerWidget,
    DowntimeStartDialog,
    ChecklistEditorWidget,
    ChecklistDialog,
    ReportingWidget,
    KPIDashboardWidget,
    CostAnalysisWidget,
)

__all__ = [
    # Service
    "MaintenanceService",
    # Ekipman
    "EquipmentListWidget",
    "EquipmentDialog",
    "EquipmentDetailDialog",
    # Talepler
    "MaintenanceRequestWidget",
    "RequestDialog",
    # İş Emirleri
    "WorkOrderManagerWidget",
    "WorkOrderDialog",
    "WorkOrderDetailsDialog",
    # Planlar
    "MaintenancePlanWidget",
    "PlanDialog",
    "MaintenanceCalendarWidget",
    # Duruş Takibi
    "DowntimeTrackerWidget",
    "DowntimeStartDialog",
    # Kontrol Listeleri
    "ChecklistEditorWidget",
    "ChecklistDialog",
    # Raporlar
    "ReportingWidget",
    "KPIDashboardWidget",
    "CostAnalysisWidget",
]
