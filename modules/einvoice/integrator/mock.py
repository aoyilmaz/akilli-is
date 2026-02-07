from typing import Dict, Any, Optional
import uuid
import random
from datetime import datetime
from database.models.einvoice import EInvoiceStatus
from .base import BaseIntegrator


class MockIntegrator(BaseIntegrator):
    """
    Test ve geliştirme amaçlı Mock entegratör.
    Gerçek bir API'ye bağlanmaz, dummy cevaplar döner.
    """

    def connect(self) -> bool:
        return True

    def send_invoice(
        self, ubl_content: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Faturayı gönderir (Mock).
        """
        success = True
        error_msg = None

        # Test modunda bazı faturalar hata alabilir (isteğe bağlı)
        if random.random() < 0.1:  # %10 ihtimalle hata
            success = False
            error_msg = "GIB servisine erişilemiyor."

        return {
            "success": success,
            "uuid": metadata.get("uuid"),
            "envelope_id": str(uuid.uuid4()) if success else None,
            "error": error_msg,
            "status": EInvoiceStatus.QUEUED if success else EInvoiceStatus.ERROR,
            "gib_status": "1000" if success else "9999",
            "description": "Zarf kuyruğa eklendi.",
        }

    def get_invoice_status(self, uuid: str) -> Dict[str, Any]:
        """
        Durum sorgular. Rastgele durum değişiklikleri simüle eder.
        """
        states = [
            (EInvoiceStatus.QUEUED, "1000", "Zarf kuyrukta"),
            (EInvoiceStatus.SENT, "1100", "GIB'e gönderildi"),
            (EInvoiceStatus.DELIVERED, "1200", "Alıcıya iletildi"),
            (EInvoiceStatus.ACCEPTED, "1300", "Başarıyla tamamlandı"),
        ]

        # Simüle edilmiş bir ilerleme
        # Gerçekte veritabanındaki son duruma göre bir sonraki durumu seçmek daha mantıklı olurdu
        # ama burada stateless.
        import random

        selected = random.choice(states)

        return {
            "status": selected[0],
            "gib_code": selected[1],
            "description": selected[2],
            "updated_at": datetime.now(),
        }

    def cancel_invoice(self, uuid: str, reason: str) -> bool:
        return True
