"""
Akıllı İş - Sevkiyat Modülü Views
"""

from .vehicle_list import VehicleListPage
from .vehicle_form import VehicleFormPage
from .vehicle_module import VehicleModule

from .driver_list import DriverListPage
from .driver_form import DriverFormPage
from .driver_module import DriverModule

from .shipment_list import ShipmentListPage
from .shipment_form import ShipmentFormPage
from .shipment_module import ShipmentModule

__all__ = [
    # Vehicle
    "VehicleListPage",
    "VehicleFormPage",
    "VehicleModule",
    # Driver
    "DriverListPage",
    "DriverFormPage",
    "DriverModule",
    # Shipment
    "ShipmentListPage",
    "ShipmentFormPage",
    "ShipmentModule",
]
