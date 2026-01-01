"""
Akıllı İş - Üretim Modülü View'ları
"""

from .bom_list import BOMListPage
from .bom_form import BOMFormPage
from .bom_module import BOMModule

from .work_order_list import WorkOrderListPage
from .work_order_form import WorkOrderFormPage
from .work_order_module import WorkOrderModule

from .planning_page import ProductionPlanningPage
from .planning_module import PlanningModule

from .work_station_list import WorkStationListPage
from .work_station_form import WorkStationFormPage
from .work_station_module import WorkStationModule

__all__ = [
    # BOM
    "BOMListPage",
    "BOMFormPage", 
    "BOMModule",
    # Work Order
    "WorkOrderListPage",
    "WorkOrderFormPage",
    "WorkOrderModule",
    # Planning
    "ProductionPlanningPage",
    "PlanningModule",
    # Work Station
    "WorkStationListPage",
    "WorkStationFormPage",
    "WorkStationModule",
]
