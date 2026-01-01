"""
Akıllı İş - Üretim Modülü
"""

from .services import BOMService, WorkStationService, WorkOrderService
from .views import (
    BOMModule, BOMListPage, BOMFormPage,
    WorkOrderModule, WorkOrderListPage, WorkOrderFormPage,
    PlanningModule, ProductionPlanningPage,
    WorkStationModule, WorkStationListPage, WorkStationFormPage,
)

__all__ = [
    # Services
    "BOMService",
    "WorkStationService", 
    "WorkOrderService",
    # BOM Views
    "BOMModule",
    "BOMListPage",
    "BOMFormPage",
    # Work Order Views
    "WorkOrderModule",
    "WorkOrderListPage",
    "WorkOrderFormPage",
    # Planning Views
    "PlanningModule",
    "ProductionPlanningPage",
    # Work Station Views
    "WorkStationModule",
    "WorkStationListPage",
    "WorkStationFormPage",
]
