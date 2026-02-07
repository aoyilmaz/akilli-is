<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
                xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" 
                xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
                xmlns:ubl="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">

    <xsl:template match="/">
        <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { display: flex; justify-content: space-between; margin-bottom: 20px; }
                    .logo { font-size: 24px; font-weight: bold; }
                    .invoice-details { text-align: right; }
                    .party-info { margin-bottom: 20px; border: 1px solid #ddd; padding: 10px; }
                    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                    .totals { margin-top: 20px; text-align: right; }
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="logo">E-FATURA</div>
                    <div class="invoice-details">
                        <p><strong>Fatura No:</strong> <xsl:value-of select="//cbc:ID"/></p>
                        <p><strong>Tarih:</strong> <xsl:value-of select="//cbc:IssueDate"/></p>
                        <p><strong>UUID:</strong> <xsl:value-of select="//cbc:UUID"/></p>
                    </div>
                </div>

                <div class="party-info">
                    <h3>Gönderen</h3>
                    <p><xsl:value-of select="//cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name"/></p>
                    <p>VKN: <xsl:value-of select="//cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID"/></p>
                </div>

                <div class="party-info">
                    <h3>Alıcı</h3>
                    <p><xsl:value-of select="//cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name"/></p>
                    <p>VKN: <xsl:value-of select="//cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID"/></p>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Sıra</th>
                            <th>Ürün/Hizmet</th>
                            <th>Miktar</th>
                            <th>Birim Fiyat</th>
                            <th>Tutar</th>
                        </tr>
                    </thead>
                    <tbody>
                        <xsl:for-each select="//cac:InvoiceLine">
                            <tr>
                                <td><xsl:value-of select="cbc:ID"/></td>
                                <td><xsl:value-of select="cac:Item/cbc:Name"/></td>
                                <td><xsl:value-of select="cbc:InvoicedQuantity"/> <xsl:value-of select="cbc:InvoicedQuantity/@unitCode"/></td>
                                <td><xsl:value-of select="cac:Price/cbc:PriceAmount"/></td>
                                <td><xsl:value-of select="cbc:LineExtensionAmount"/></td>
                            </tr>
                        </xsl:for-each>
                    </tbody>
                </table>

                <div class="totals">
                    <p><strong>Ara Toplam:</strong> <xsl:value-of select="//cac:LegalMonetaryTotal/cbc:LineExtensionAmount"/></p>
                    <p><strong>Vergi Toplam:</strong> <xsl:value-of select="//cac:TaxTotal/cbc:TaxAmount"/></p>
                    <p><strong>Genel Toplam:</strong> <xsl:value-of select="//cac:LegalMonetaryTotal/cbc:PayableAmount"/></p>
                </div>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
