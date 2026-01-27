"""
Akıllı İş - MPS (Master Production Scheduling) Modülü

Ana Üretim Planlama modülü. Satış siparişlerinden veya talep tahminlerinden
üretim planları oluşturur ve backward scheduling ile başlangıç tarihlerini hesaplar.
"""

from modules.mps.services import MPSService
from modules.mps.views import MPSPage

__all__ = ["MPSService", "MPSPage"]
