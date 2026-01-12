"""
Akıllı İş - İnsan Kaynakları Views
"""

from .employee_module import EmployeeModule
from .employee_form import EmployeeFormDialog
from .department_module import DepartmentModule
from .position_module import PositionModule
from .leave_module import LeaveModule
from .org_chart_module import OrgChartModule
from .shift_team_overview import ShiftTeamOverview

__all__ = [
    "EmployeeModule",
    "EmployeeFormDialog",
    "DepartmentModule",
    "PositionModule",
    "LeaveModule",
    "OrgChartModule",
    "ShiftTeamOverview",
]
