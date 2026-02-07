from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseIntegrator(ABC):
    """
    Tüm entegratörlerin (Logo, Sovos, vb.) türeyeceği temel sınıf.
    """

    def __init__(self, settings: Optional[Any] = None):
        self.settings = settings

    @abstractmethod
    def connect(self) -> bool:
        """Entegratöre bağlanır (login)."""
        pass

    @abstractmethod
    def send_invoice(
        self, ubl_content: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Faturayı gönderir.
        :param ubl_content: İmzalı UBL XML içeriği (string veya bytes)
        :param metadata: Ek bilgiler (alıcı, gönderici, vb.)
        :return: {'success': bool, 'uuid': str, 'envelope_id': str, 'error': str}
        """
        pass

    @abstractmethod
    def get_invoice_status(self, uuid: str) -> Dict[str, Any]:
        """
        Fatura durumunu sorgular.
        :return: {'status': EInvoiceStatus, 'gib_code': str, 'description': str}
        """
        pass

    @abstractmethod
    def cancel_invoice(self, uuid: str, reason: str) -> bool:
        """
        Faturayı iptal eder (e-Arşiv için).
        """
        pass
