"""
Akıllı İş - UBL 2.1 E-Fatura XML Üreticisi
"""

import uuid
from datetime import datetime
from jinja2 import Template

UBL_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
    <cbc:CustomizationID>TR1.2</cbc:CustomizationID>
    <cbc:ProfileID>TEMELFATURA</cbc:ProfileID>
    <cbc:ID>{{ invoice_no }}</cbc:ID>
    <cbc:UUID>{{ uuid }}</cbc:UUID>
    <cbc:IssueDate>{{ issue_date }}</cbc:IssueDate>
    <cbc:InvoiceTypeCode>SATIS</cbc:InvoiceTypeCode>
    
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cbc:WebsiteURI>www.akilliis.com</cbc:WebsiteURI>
            <cac:PartyName><cbc:Name>Akıllı İş Teknoloji A.Ş.</cbc:Name></cac:PartyName>
            <cac:PostalAddress>
                <cbc:CitySubdivisionName>Kadıköy</cbc:CitySubdivisionName>
                <cbc:CityName>İstanbul</cbc:CityName>
            </cac:PostalAddress>
            <cac:PartyTaxScheme><cac:TaxScheme><cbc:Name>Erenköy</cbc:Name></cac:TaxScheme></cac:PartyTaxScheme>
        </cac:Party>
    </cac:AccountingSupplierParty>

    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyName><cbc:Name>{{ customer_name }}</cbc:Name></cac:PartyName>
            <cac:PartyTaxScheme><cac:TaxScheme><cbc:Name>{{ tax_office }}</cbc:Name></cac:TaxScheme></cac:PartyTaxScheme>
        </cac:Party>
    </cac:AccountingCustomerParty>

    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="TRY">{{ total_tax }}</cbc:TaxAmount>
    </cac:TaxTotal>

    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="TRY">{{ subtotal }}</cbc:LineExtensionAmount>
        <cbc:TaxExclusiveAmount currencyID="TRY">{{ subtotal }}</cbc:TaxExclusiveAmount>
        <cbc:TaxInclusiveAmount currencyID="TRY">{{ total }}</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="TRY">{{ total }}</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>

    {% for item in items %}
    <cac:InvoiceLine>
        <cbc:ID>{{ loop.index }}</cbc:ID>
        <cbc:InvoicedQuantity unitCode="C62">{{ item.quantity }}</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="TRY">{{ item.line_total }}</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Name>{{ item.name }}</cbc:Name>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount currencyID="TRY">{{ item.unit_price }}</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
    {% endfor %}
</Invoice>
"""


class UBLGenerator:
    @staticmethod
    def generate_xml(invoice_data: dict) -> str:
        """Fatura verilerinden UBL 2.1 XML üretir"""
        template = Template(UBL_TEMPLATE)

        # UUID ve tarih hazırlığı
        if "uuid" not in invoice_data:
            invoice_data["uuid"] = str(uuid.uuid4())
        if "issue_date" not in invoice_data:
            invoice_data["issue_date"] = datetime.now().strftime("%Y-%m-%d")

        return template.render(**invoice_data)
