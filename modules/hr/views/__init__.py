"""
Akıllı İş - İnsan Kaynakları Views
"""

from .employee_module import EmployeeModule
from .employee_form import EmployeeFormDialog
from .department_module import DepartmentModule
from .position_module import PositionModule
from .leave_module import LeaveModule

__all__ = [
    "EmployeeModule",
    "EmployeeFormDialog",
    "DepartmentModule",
    "PositionModule",
    "LeaveModule",
]
