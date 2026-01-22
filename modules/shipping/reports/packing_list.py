"""
Akıllı İş - Sevkiyat Çeki Listesi (Packing List) Raporu
"""

import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from modules.shipping.services.base import ShipmentService


class PackingListReport:
    """Çeki Listesi PDF Raporu Oluşturucu"""

    def __init__(self):
        self.shipment_service = ShipmentService()
        self.template_dir = os.path.join(os.path.dirname(__file__), "templates")

        # Şablon klasörü yoksa oluştur (Geçici, normalde assets içinde olur)
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
            self._create_default_template()

        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    def _create_default_template(self):
        """Varsayılan HTML şablonunu oluştur"""
        template_path = os.path.join(self.template_dir, "packing_list.html")
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(
                """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Çeki Listesi</title>
    <style>
        body { font-family: 'Helvetica', 'Arial', sans-serif; font-size: 12px; color: #333; }
        .header { margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 10px; }
        .title { font-size: 24px; font-weight: bold; }
        .info-table { width: 100%; margin-bottom: 20px; }
        .info-table td { padding: 5px; }
        .label { font-weight: bold; width: 120px; }
        
        .load-container { margin-bottom: 15px; border: 1px solid #ddd; page-break-inside: avoid; }
        .load-header { background-color: #f5f5f5; padding: 8px; font-weight: bold; border-bottom: 1px solid #ddd; }
        .items-table { width: 100%; border-collapse: collapse; }
        .items-table th { text-align: left; padding: 5px; border-bottom: 1px solid #eee; font-size: 11px; }
        .items-table td { padding: 5px; border-bottom: 1px solid #eee; }
        
        .footer { margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; font-size: 10px; text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">ÇEKİ LİSTESİ (PACKING LIST)</div>
        <div>{{ company_name }}</div>
    </div>

    <table class="info-table">
        <tr>
            <td class="label">Sevkiyat No:</td>
            <td>{{ shipment.shipment_no }}</td>
            <td class="label">Tarih:</td>
            <td>{{ shipment.shipment_date.strftime('%d.%m.%Y') }}</td>
        </tr>
        <tr>
            <td class="label">Araç:</td>
            <td>{{ shipment.vehicle.plate_no if shipment.vehicle else '-' }}</td>
            <td class="label">Sürücü:</td>
            <td>{{ shipment.driver.name if shipment.driver else '-' }}</td>
        </tr>
        <tr>
            <td class="label">Toplam Palet:</td>
            <td>{{ shipment.total_pallets }}</td>
            <td class="label">Toplam Ağırlık:</td>
            <td>{{ shipment.total_weight_kg }} kg</td>
        </tr>
    </table>

    <h3>Yükleme Detayları</h3>

    {% for load in shipment.loads %}
    <div class="load-container">
        <div class="load-header">
            SSCC: {{ load.transport_unit.sscc }} 
            <span style="float: right;">Tip: {{ load.transport_unit.unit_type.value }}</span>
        </div>
        <table class="items-table">
            <thead>
                <tr>
                    <th>Ürün Kodu</th>
                    <th>Ürün Adı</th>
                    <th>Miktar</th>
                    <th>Birim</th>
                    <th>Lot/Seri</th>
                </tr>
            </thead>
            <tbody>
                {% for item in load.transport_unit.items %}
                <tr>
                    <td>{{ item.item.code }}</td>
                    <td>{{ item.item.name }}</td>
                    <td>{{ item.quantity }}</td>
                    <td>{{ item.unit.name }}</td>
                    <td>{{ item.lot_number or '-' }}</td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="5" style="text-align: center; color: #999;">İçerik bilgisi yok</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <div style="padding: 20px; text-align: center; background: #eee;">
        Henüz yükleme bilgisi oluşturulmamış.
    </div>
    {% endfor %}

    <div class="footer">
        Bu belge Akıllı İş ERP sistemi tarafından oluşturulmuştur. Tarih: {{ now.strftime('%d.%m.%Y %H:%M') }}
    </div>
</body>
</html>
            """
            )

    def generate_pdf(self, shipment_id: int, output_path: str = None) -> str:
        """PDF Raporu oluştur"""
        shipment = self.shipment_service.get_by_id(shipment_id)
        if not shipment:
            raise ValueError("Sevkiyat bulunamadı.")

        if not output_path:
            filename = f"packing_list_{shipment.shipment_no}_{datetime.now().strftime('%Y%m%d%H%M')}.pdf"
            output_path = os.path.join(os.path.expanduser("~/Desktop"), filename)

        template = self.env.get_template("packing_list.html")
        html_content = template.render(
            shipment=shipment,
            company_name="Akıllı İş A.Ş.",  # Config'den alınabilir
            now=datetime.now(),
        )

        HTML(string=html_content).write_pdf(output_path)
        return output_path
