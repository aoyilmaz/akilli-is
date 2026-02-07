from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from database.models.einvoice import (
    EInvoice,
    EInvoiceStatus,
    EInvoiceType,
    EInvoiceDirection,
)


from database.base import get_session


class EInvoiceService:
    def __init__(self, session: Session = None):
        self.session = session or get_session()

    def create_draft(self, invoice_data: Dict[str, Any]) -> EInvoice:
        """
        Taslak bir e-fatura kaydı oluşturur.
        """
        if "uuid" not in invoice_data:
            import uuid

            invoice_data["uuid"] = str(uuid.uuid4())

        if "type" not in invoice_data:
            invoice_data["type"] = EInvoiceType.EINVOICE

        if "profile" not in invoice_data:
            from database.models.einvoice import EInvoiceProfile

            invoice_data["profile"] = EInvoiceProfile.TICARIFATURA

        einvoice = EInvoice(
            direction=EInvoiceDirection.OUTGOING,
            status=EInvoiceStatus.DRAFT,
            **invoice_data,
        )
        self.session.add(einvoice)
        self.session.flush()
        return einvoice

    def get_by_uuid(self, uuid: str) -> Optional[EInvoice]:
        return self.session.query(EInvoice).filter_by(uuid=uuid).first()

    def generate_xml(self, uuid: str) -> str:
        """
        UBL XML oluşturur ve veritabanına kaydeder.
        """
        einvoice = self.get_by_uuid(uuid)
        if not einvoice:
            raise ValueError("EInvoice not found")

        from modules.einvoice.services.ubl_builder import UBLBuilder

        builder = UBLBuilder(einvoice)
        xml_content = builder.build_xml()

        einvoice.xml_content = xml_content
        self.session.flush()
        return xml_content

    def send_invoice(self, uuid: str) -> Dict[str, Any]:
        """
        Faturayı entegratöre gönderir.
        """
        einvoice = self.get_by_uuid(uuid)
        if not einvoice:
            raise ValueError("EInvoice not found")

        if not einvoice.xml_content:
            self.generate_xml(uuid)

        from modules.einvoice.integrator import get_integrator

        # TODO: Fetch real settings from DB
        settings = {}
        integrator = get_integrator("MOCK", settings)
        integrator.connect()

        metadata = {
            "uuid": einvoice.uuid,
            "sender_vkn": einvoice.sender_vkn,
            "receiver_vkn": einvoice.receiver_vkn,
        }

        result = integrator.send_invoice(einvoice.xml_content, metadata)

        if result.get("success"):
            einvoice.status = EInvoiceStatus.QUEUED
            einvoice.envelope_id = result.get("envelope_id")
            einvoice.sent_at = datetime.now()

            history = einvoice.status_history or []
            history.append(
                {
                    "status": "QUEUED",
                    "timestamp": datetime.now().isoformat(),
                    "description": result.get("description"),
                }
            )
            einvoice.status_history = history  # Re-assign to trigger update if needed
        else:
            einvoice.status = EInvoiceStatus.ERROR
            einvoice.error_message = result.get("error")

        self.session.flush()
        return result

    def get_all(self, limit: int = 100) -> list[EInvoice]:
        """Son e-faturaları getirir."""
        return (
            self.session.query(EInvoice)
            .order_by(EInvoice.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_html(self, uuid: str) -> str:
        """
        Faturanın HTML görüntüsünü oluşturur (XSLT ile).
        """
        einvoice = self.get_by_uuid(uuid)
        if not einvoice:
            raise ValueError("EInvoice not found")

        if not einvoice.xml_content:
            # XML yoksa oluştur
            self.generate_xml(uuid)

        try:
            from lxml import etree
            import os

            # XML'i parse et
            # Encoding belirterek parse etmek daha güvenli
            xml_bytes = einvoice.xml_content.encode("utf-8")
            xml_doc = etree.fromstring(xml_bytes)

            # XSLT dosyasını bul
            xslt_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "templates",
                "general.xslt",
            )

            if not os.path.exists(xslt_path):
                return f"<h3>Hata: Şablon bulunamadı</h3><p>{xslt_path}</p>"

            xslt_doc = etree.parse(xslt_path)
            transform = etree.XSLT(xslt_doc)

            # Dönüştür
            html_doc = transform(xml_doc)
            return str(html_doc)

        except ImportError:
            return "<h3>Hata</h3><p>lxml kütüphanesi yüklü değil.</p>"
        except Exception as e:
            import traceback

            return f"<h3>Hata</h3><pre>{traceback.format_exc()}</pre>"
