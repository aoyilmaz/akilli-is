"""
Akıllı İş - Dashboard Widget'ları
"""

from .base import BaseWidget, WidgetConfig

# Animasyon utilities
from .animations import (
    ValueAnimator,
    FadeAnimator,
    PulseGlowAnimator,
    SkeletonWidget,
    SkeletonGroup,
    StaggeredAnimator,
)

# Stat widget'ları
from .stat_widget import (
    StatWidget,
    SalesTodayWidget,
    PendingOrdersWidget,
    LowStockWidget,
    OpenWorkOrdersWidget,
    TodayWarehouseEntryWidget,
    TodayWarehouseExitWidget,
    TotalStockValueWidget,
    TodayPurchasesWidget,
    PendingPurchaseOrdersWidget,
    TodayShipmentsWidget,
    PendingShipmentsWidget,
    TodayProductionWidget,
    ActiveCustomersWidget,
    ActiveSuppliersWidget,
)

# Gauge widget'ları
from .gauge_widget import (
    CircularGauge,
    GaugeWidget,
    CapacityGaugeWidget,
    EfficiencyGaugeWidget,
)

# Sparkline bileşeni
from .sparkline import MiniSparkline, TrendSparkline

# Empty state bileşenleri
from .empty_state import (
    EmptyStateWidget,
    ErrorStateWidget,
    NoDataWidget,
    LoadingFailedWidget,
    SearchEmptyWidget,
)

# Liste widget'ları
from .notification_widget import NotificationWidget
from .quick_action_widget import QuickActionWidget
from .currency_widget import CurrencyWidget
from .weather_widget import WeatherWidget
from .expiry_widget import ExpiryAlertWidget
from .bottleneck_widget import CapacityBottleneckDashboardWidget
from .pending_approvals_widget import PendingApprovalsWidget

__all__ = [
    # Base
    "BaseWidget",
    "WidgetConfig",
    # Animations
    "ValueAnimator",
    "FadeAnimator",
    "PulseGlowAnimator",
    "SkeletonWidget",
    "SkeletonGroup",
    "StaggeredAnimator",
    # Stat widgets
    "StatWidget",
    "SalesTodayWidget",
    "PendingOrdersWidget",
    "LowStockWidget",
    "OpenWorkOrdersWidget",
    "TodayWarehouseEntryWidget",
    "TodayWarehouseExitWidget",
    "TotalStockValueWidget",
    "TodayPurchasesWidget",
    "PendingPurchaseOrdersWidget",
    "TodayShipmentsWidget",
    "PendingShipmentsWidget",
    "TodayProductionWidget",
    "ActiveCustomersWidget",
    "ActiveSuppliersWidget",
    # Gauge widgets
    "CircularGauge",
    "GaugeWidget",
    "CapacityGaugeWidget",
    "EfficiencyGaugeWidget",
    # Sparkline
    "MiniSparkline",
    "TrendSparkline",
    # Empty states
    "EmptyStateWidget",
    "ErrorStateWidget",
    "NoDataWidget",
    "LoadingFailedWidget",
    "SearchEmptyWidget",
    # List widgets
    "NotificationWidget",
    "ExpiryAlertWidget",
    "CapacityBottleneckDashboardWidget",
    "PendingApprovalsWidget",
    # Action widgets
    "QuickActionWidget",
    # External data widgets
    "CurrencyWidget",
    "WeatherWidget",
]
