"""
Akıllı İş - Sevkiyat Modülü

Araç, sürücü ve sevkiyat yönetimi için modül.
"""

from .services import (
    VehicleService,
    DriverService,
    ShipmentService,
)

from .views import (
    VehicleModule,
    DriverModule,
    ShipmentModule,
)

from .module import ShippingMainModule

__all__ = [
    # Services
    "VehicleService",
    "DriverService",
    "ShipmentService",
    # Modules
    "VehicleModule",
    "DriverModule",
    "ShipmentModule",
    # Main Module
    "ShippingMainModule",
]
