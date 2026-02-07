import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from database.models.einvoice import EInvoice


class UBLBuilder:
    def __init__(self, einvoice: EInvoice):
        self.einvoice = einvoice
        self.template_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "templates"
        )
        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    def _prepare_context(self):
        # Basic context from EInvoice
        context = {
            "uuid": self.einvoice.uuid,
            "invoice_number": self.einvoice.invoice_number or "",
            "profile": (
                self.einvoice.profile if self.einvoice.profile else "TICARIFATURA"
            ),
            "issue_date": datetime.now(),  # Should be from invoice or einvoice
            "issue_time": datetime.now(),
            "invoice_type": self.einvoice.type.value if self.einvoice.type else "SATIS",
            "currency_code": "TRY",  # Default
            "sender_vkn": self.einvoice.sender_vkn,
            "sender_name": self.einvoice.sender_alias
            or "Sender Name",  # Need real name
            "receiver_vkn": self.einvoice.receiver_vkn,
            "receiver_name": self.einvoice.receiver_alias
            or "Receiver Name",  # Need real name
            "tax_amount": 0,
            "line_extension_amount": 0,
            "tax_exclusive_amount": 0,
            "tax_inclusive_amount": 0,
            "payable_amount": 0,
            "lines": [],
        }

        # If linked to invoice, enrich context
        if self.einvoice.invoice:
            inv = self.einvoice.invoice
            context.update(
                {
                    "invoice_number": self.einvoice.invoice_number or inv.invoice_no,
                    "issue_date": inv.invoice_date,
                    "currency_code": inv.currency,
                    "tax_amount": inv.tax_amount,
                    "line_extension_amount": inv.subtotal,
                    "tax_exclusive_amount": inv.subtotal - (inv.discount_amount or 0),
                    "tax_inclusive_amount": inv.total,
                    "payable_amount": inv.total,
                    "receiver_name": inv.customer.name if inv.customer else "",
                }
            )

            # Lines
            for item in inv.items:
                context["lines"].append(
                    {
                        "item_name": item.item.name if item.item else "Unknown Item",
                        "quantity": item.quantity,
                        "unit_code": item.unit.code if item.unit else "NIU",
                        "price": item.unit_price,
                        "line_total": item.line_total,
                        "tax_amount": (item.line_total * (item.tax_rate or 0) / 100),
                    }
                )

        return context

    def build_xml(self) -> str:
        """
        EInvoice nesnesini UBL-TR XML stringine çevirir.
        """
        template = self.env.get_template("ubl_invoice.xml.j2")
        context = self._prepare_context()
        return template.render(context)
