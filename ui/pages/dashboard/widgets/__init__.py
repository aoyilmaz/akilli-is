"""
Akıllı İş - Dashboard Widget'ları
"""

from .base import BaseWidget, WidgetConfig

from .stat_widget import (
    StatWidget,
    SalesTodayWidget,
    PendingOrdersWidget,
    LowStockWidget,
    OpenWorkOrdersWidget,
)

from .notification_widget import NotificationWidget
from .quick_action_widget import QuickActionWidget
from .currency_widget import CurrencyWidget
from .weather_widget import WeatherWidget

__all__ = [
    # Base
    "BaseWidget",
    "WidgetConfig",
    # Stat widgets
    "StatWidget",
    "SalesTodayWidget",
    "PendingOrdersWidget",
    "LowStockWidget",
    "OpenWorkOrdersWidget",
    # List widgets
    "NotificationWidget",
    # Action widgets
    "QuickActionWidget",
    # External data widgets
    "CurrencyWidget",
    "WeatherWidget",
]
