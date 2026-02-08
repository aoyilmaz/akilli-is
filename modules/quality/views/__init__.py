"""
Akıllı İş - Kalite Views
"""

from .inspection_module import InspectionModule
from .ncr_module import NCRModule
from .complaint_module import ComplaintModule
from .capa_module import CAPAModule
from .template_module import TemplateModule
from .spc_module import SPCModule

__all__ = [
    "InspectionModule",
    "NCRModule",
    "ComplaintModule",
    "CAPAModule",
    "TemplateModule",
    "SPCModule",
]
