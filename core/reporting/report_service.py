"""
Akıllı İş - Raporlama Servisi
"""

import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


class ReportService:
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), "templates")
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)

        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    def render_to_html(self, template_name: str, data: dict) -> str:
        """Verileri HTML şablonuna giydirir"""
        template = self.env.get_template(template_name)

        # Standart verileri ekle
        data["print_date"] = datetime.now().strftime("%d.%m.%Y %H:%M")

        # Firma bilgilerini otomatik ekle
        try:
            from core.company_context import get_company_context

            ctx = get_company_context()
            if ctx.company:
                # Ana firma bilgileri
                data["company"] = {
                    "name": ctx.name,
                    "legal_name": ctx.legal_name,
                    "tax_office": ctx.tax_office,
                    "tax_number": ctx.tax_number,
                    "phone": ctx.phone,
                    "email": ctx.email,
                    "website": ctx.website,
                    "currency": ctx.currency,
                    "address": ctx.get_default_address(),
                    "bank": ctx.get_default_bank(),
                    "logo_path": ctx.get_logo_path(),
                }
                # Geriye uyumluluk için
                data["company_name"] = ctx.legal_name or ctx.name
                data["company_address"] = ctx.get_default_address().get("full", "")
                data["company_tax"] = (
                    f"{ctx.tax_office} - {ctx.tax_number}"
                    if ctx.tax_office
                    else ctx.tax_number
                )
        except Exception:
            pass

        return template.render(**data)

    def generate_pdf(self, template_name: str, data: dict, output_path: str):
        """
        HTML şablonundan PDF üretir.
        Not: WeasyPrint veya pdfkit (wkhtmltopdf) gerektirir.
        """
        html_content = self.render_to_html(template_name, data)

        try:
            # Örnek: pdfkit kullanımı
            # import pdfkit
            # pdfkit.from_string(html_content, output_path)

            # Şimdilik debug amaçlı HTML olarak kaydet
            debug_path = output_path.replace(".pdf", ".html")
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"✓ Rapor taslağı oluşturuldu: {debug_path}")
            return True
        except Exception as e:
            print(f"✗ PDF üretim hatası: {e}")
            return False


# Varsayılan fatura şablonu oluştur
DEFAULT_INVOICE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: sans-serif; }
        .header { text-align: center; border-bottom: 2px solid #333; margin-bottom: 20px; }
        .info { display: flex; justify-content: space-between; margin-bottom: 30px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background-color: #f2f2f2; }
        .totals { float: right; width: 300px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>SATIŞ FATURASI</h1>
        <p>{{ company_name }}</p>
    </div>
    
    <div class="info">
        <div>
            <strong>Müşteri:</strong><br>
            {{ customer_name }}<br>
            {{ customer_address }}
        </div>
        <div>
            <strong>Fatura No:</strong> {{ invoice_no }}<br>
            <strong>Tarih:</strong> {{ invoice_date }}<br>
            <strong>Yazdırma:</strong> {{ print_date }}
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Ürün</th>
                <th>Miktar</th>
                <th>Birim Fiyat</th>
                <th>Toplam</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ item.name }}</td>
                <td>{{ item.quantity }}</td>
                <td>{{ item.unit_price }}</td>
                <td>{{ item.line_total }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="totals">
        <table>
            <tr><td>Ara Toplam:</td><td>{{ subtotal }}</td></tr>
            <tr><td>KDV:</td><td>{{ tax_total }}</td></tr>
            <tr><td><strong>GENEL TOPLAM:</strong></td><td><strong>{{ total }}</strong></td></tr>
        </table>
    </div>
</body>
</html>
"""
