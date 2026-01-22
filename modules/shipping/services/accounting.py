"""
Akıllı İş - Sevkiyat Muhasebe Entegrasyonu
"""

from decimal import Decimal
from typing import Optional
from database.models.accounting import AccountType, JournalEntry
from modules.accounting.services import AccountingService
from modules.shipping.services.base import ShipmentService


class ShipmentAccountingBridge:
    """Sevkiyat - Muhasebe Entegrasyon Köprüsü"""

    def __init__(self):
        self.accounting_service = AccountingService()
        self.shipment_service = ShipmentService()

    def _ensure_account(
        self, code: str, name: str, account_type: AccountType, parent_code: str = None
    ):
        """Hesap yoksa oluştur"""
        account = self.accounting_service.get_account_by_code(code)
        if not account:
            parent_id = None
            if parent_code:
                parent = self.accounting_service.get_account_by_code(parent_code)
                if parent:
                    parent_id = parent.id

            self.accounting_service.create_account(
                {
                    "code": code,
                    "name": name,
                    "account_type": account_type,
                    "parent_id": parent_id,
                    "level": len(code),  # Basit level mantığı
                    "is_detail": True,
                }
            )
            return self.accounting_service.get_account_by_code(code)
        return account

    def create_freight_invoice_journal(
        self, shipment_id: int
    ) -> Optional[JournalEntry]:
        """Sevkiyat navlun faturası için yevmiye fişi oluştur"""
        shipment = self.shipment_service.get_by_id(shipment_id)
        if not shipment:
            raise ValueError("Sevkiyat bulunamadı.")

        if not shipment.freight_amount or shipment.freight_amount <= 0:
            return None  # Maliyet yok

        # 1. Gerekli Hesapları Kontrol Et / Oluştur
        # 760 - Pazarlama Satış ve Dağıtım Giderleri
        exp_account = self._ensure_account(
            "760", "Pazarlama Satış ve Dağıtım Giderleri", AccountType.EXPENSE, "7"
        )
        if not exp_account:
            # 7 yoksa 7'yi de oluşturmak gerekebilir ama seed data'da var.
            # Seed data'da 760 yok, 7 var.
            pass

        # 320 - Satıcılar (Nakliyeci)
        # Gerçek senaryoda Nakliyeci'nin kendi cari kodu (320.01.005 vb.) olmalı.
        # Burada örnek olarak genel 320.01 kullanılacak.
        vendor_account = self._ensure_account(
            "320.01", "Nakliyeciler", AccountType.LIABILITY, "320"
        )

        # 2. Yevmiye Fişi Hazırla
        description = f"Navlun Gideri - Sevkiyat: {shipment.shipment_no}"
        if shipment.carrier_invoice_no:
            description += f" - Fat: {shipment.carrier_invoice_no}"

        journal_data = {
            "entry_date": shipment.shipment_date,
            "description": description,
            "reference_type": "shipment",
            "reference_id": shipment.id,
        }

        # 3. Satırlar
        lines = [
            # Borç: 760
            {
                "account_id": exp_account.id,
                "debit": Decimal(shipment.freight_amount),
                "credit": Decimal("0.00"),
                "description": description,
            },
            # Alacak: 320
            {
                "account_id": vendor_account.id,
                "debit": Decimal("0.00"),
                "credit": Decimal(shipment.freight_amount),
                "description": description,
            },
        ]

        # 4. Fişi Oluştur
        return self.accounting_service.create_journal(lines, **journal_data)
