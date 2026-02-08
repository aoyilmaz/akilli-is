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
from .attendance_module import AttendanceModule
from .performance_module import PerformanceModule
from .training_module import TrainingModule
from .personnel_module import PersonnelModule
from .hr_dashboard_module import HRDashboardModule
from .shift_planning_module import ShiftPlanningModule
from .recruitment_module import RecruitmentModule

__all__ = [
    "EmployeeModule",
    "EmployeeFormDialog",
    "DepartmentModule",
    "PositionModule",
    "LeaveModule",
    "OrgChartModule",
    "ShiftTeamOverview",
    "AttendanceModule",
    "PerformanceModule",
    "TrainingModule",
    "PersonnelModule",
    "HRDashboardModule",
    "ShiftPlanningModule",
    "RecruitmentModule",
]
