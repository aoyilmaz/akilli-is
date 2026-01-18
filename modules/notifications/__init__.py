"""
Akıllı İş ERP - Bildirim Modülü

Olay tabanlı bildirim sistemi.
Stok uyarıları, onay bekleyen işlemler vb. olayları
kullanıcılara bildirir.
"""

from .services import NotificationService

__all__ = ["NotificationService"]
