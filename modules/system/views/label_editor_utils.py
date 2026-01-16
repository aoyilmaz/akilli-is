"""
Etiket editörü için yardımcı fonksiyonlar ve veri tanımları
"""

from typing import Dict, List, Any

# Şablon tiplerine göre kullanılabilir değişkenler
TEMPLATE_VARIABLES = {
    "product": [
        {
            "key": "name",
            "label": "Ürün Adı",
            "example": "Test Ürünü - Model X",
            "type": "text",
        },
        {"key": "code", "label": "Ürün Kodu", "example": "PRD-001", "type": "text"},
        {
            "key": "barcode",
            "label": "Barkod",
            "example": "8691234567890",
            "type": "barcode",
        },
        {
            "key": "price",
            "label": "Satış Fiyatı",
            "example": "1,250.00 TL",
            "type": "text",
        },
        {
            "key": "purchase_price",
            "label": "Alış Fiyatı",
            "example": "950.00 TL",
            "type": "text",
        },
        {
            "key": "category",
            "label": "Kategori",
            "example": "Elektronik",
            "type": "text",
        },
        {"key": "unit", "label": "Birim", "example": "ADET", "type": "text"},
        {
            "key": "description",
            "label": "Açıklama",
            "example": "Ürün açıklaması burada yer alır.",
            "type": "text",
        },
        {"key": "brand", "label": "Marka", "example": "TestMarka", "type": "text"},
        {"key": "model", "label": "Model", "example": "X-2024", "type": "text"},
    ],
    "work_order": [
        {
            "key": "wo_no",
            "label": "İş Emri No",
            "example": "WO-2024-001",
            "type": "text",
        },
        {
            "key": "product",
            "label": "Ürün Adı",
            "example": "Özel Üretim Masa",
            "type": "text",
        },
        {"key": "quantity", "label": "Miktar", "example": "50", "type": "text"},
        {"key": "date", "label": "Tarih", "example": "14.01.2024", "type": "text"},
        {
            "key": "customer",
            "label": "Müşteri",
            "example": "ABC Ltd. Şti.",
            "type": "text",
        },
        {"key": "priority", "label": "Öncelik", "example": "Yüksek", "type": "text"},
        {"key": "status", "label": "Durum", "example": "Üretimde", "type": "text"},
        {
            "key": "notes",
            "label": "Notlar",
            "example": "Dikkatli taşıyınız.",
            "type": "text",
        },
        {
            "key": "barcode",
            "label": "İş Emri Barkodu",
            "example": "WO-2024-001",
            "type": "barcode",
        },
    ],
    "shipping": [
        {
            "key": "shipment_no",
            "label": "Sevkiyat No",
            "example": "SH-2024-056",
            "type": "text",
        },
        {
            "key": "recipient",
            "label": "Alıcı",
            "example": "Ahmet Yılmaz",
            "type": "text",
        },
        {
            "key": "address",
            "label": "Adres",
            "example": "Organize Sanayi Bölgesi, 5. Cadde No:12",
            "type": "text",
        },
        {"key": "city", "label": "Şehir", "example": "İstanbul", "type": "text"},
        {
            "key": "phone",
            "label": "Telefon",
            "example": "0555 123 45 67",
            "type": "text",
        },
        {
            "key": "date",
            "label": "Sevk Tarihi",
            "example": "15.01.2024",
            "type": "text",
        },
        {
            "key": "package_count",
            "label": "Paket Sayısı",
            "example": "3",
            "type": "text",
        },
        {
            "key": "barcode",
            "label": "Sevkiyat Barkodu",
            "example": "SH-2024-056",
            "type": "barcode",
        },
    ],
    "location": [
        {"key": "code", "label": "Konum Kodu", "example": "A-01-05", "type": "text"},
        {"key": "warehouse", "label": "Depo", "example": "Ana Depo", "type": "text"},
        {"key": "aisle", "label": "Koridor", "example": "A", "type": "text"},
        {"key": "shelf", "label": "Raf", "example": "01", "type": "text"},
        {
            "key": "barcode",
            "label": "Konum Barkodu",
            "example": "LOC-A-01-05",
            "type": "barcode",
        },
    ],
}

LABEL_SNIPPETS = {
    "Başlık Alanı": """<div style="text-align: center; margin-bottom: 10px;">
    <h1 style="margin: 0; font-size: 24px;">{{ name }}</h1>
</div>""",
    "Fiyat Kutusu": """<div style="border: 2px solid #000; padding: 10px; text-align: center; margin: 10px 0; border-radius: 8px;">
    <div style="font-size: 14px; color: #666;">SATIŞ FİYATI</div>
    <div style="font-size: 32px; font-weight: bold;">{{ price }}</div>
</div>""",
    "Barkod Alanı": """<div style="text-align: center; margin-top: 15px;">
    <img src="{{ barcode_path }}" style="max-width: 100%; height: 60px;">
    <div style="font-family: monospace; font-size: 12px; letter-spacing: 2px;">{{ code }}</div>
</div>""",
    "Özellik Listesi": """<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
    <tr style="border-bottom: 1px solid #ccc;">
        <td style="padding: 5px; font-weight: bold;">Özellik 1:</td>
        <td style="padding: 5px;">Değer 1</td>
    </tr>
    <tr style="border-bottom: 1px solid #ccc;">
        <td style="padding: 5px; font-weight: bold;">Özellik 2:</td>
        <td style="padding: 5px;">Değer 2</td>
    </tr>
</table>""",
    "Firma Logosu": """<div style="text-align: right; margin-bottom: 10px;">
    <img src="https://via.placeholder.com/100x40?text=LOGO" style="height: 30px;">
</div>""",
    "Ayırıcı Çizgi": """<hr style="border: 0; border-top: 1px solid #000; margin: 15px 0;">""",
}


def get_dummy_data(template_type: str) -> Dict[str, Any]:
    """Şablon tipi için test verisi döndürür"""
    variables = TEMPLATE_VARIABLES.get(template_type, [])
    data = {}
    for var in variables:
        # Örnek veriyi kullan, yoksa boş string
        key = var["key"]
        example = var.get("example", f"Test {var['label']}")

        # Eğer barkod ise ve data'da henüz yoksa, key'i olduğu gibi kullan
        if var["type"] == "barcode" and key not in data:
            data[key] = example
        elif key not in data:
            data[key] = example

    # Genel fallback veriler
    if not data:
        data = {"name": "Test Verisi", "code": "TEST-001", "date": "01.01.2024"}

    return data
