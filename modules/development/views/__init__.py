"""
Akıllı İş - Geliştirme Modülü Views
"""

from modules.development.views.module import DevelopmentModule
from modules.development.views.settings_page import ThemeSettingsPage
from modules.development.views.trace_viewer_module import TraceViewerModule
from modules.development.views.trace_list_page import TraceListPage
from modules.development.views.trace_detail_page import TraceDetailPage

__all__ = [
    "DevelopmentModule",
    "ThemeSettingsPage",
    "TraceViewerModule",
    "TraceListPage",
    "TraceDetailPage",
]
