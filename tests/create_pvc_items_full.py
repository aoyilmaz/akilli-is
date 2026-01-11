import sys
import os
import random
from decimal import Decimal
from datetime import datetime

# Proje dizinini path'e ekle
sys.path.append(os.getcwd())

from database.base import get_session
from database.models.inventory import Item, ItemCategory, Unit, ItemType
from database.models.common import Currency


def create_pvc_inventory_full():
    session = get_session()
    print("🏭 PVC Streç Fabrikası Detaylı Stok Kartları Oluşturuluyor...")

    # --- 1. Para Birimleri ve Birimlerin Hazırlanması ---
    def get_or_create_currency(code):
        curr = session.query(Currency).filter(Currency.code == code).first()
        if not curr:
            print(f"⚠️ {code} para birimi bulunamadı, veritabanını kontrol edin.")
            return None
        return curr.id

    try:
        try_id = get_or_create_currency("TRY")
        usd_id = get_or_create_currency("USD")
        eur_id = get_or_create_currency("EUR")
    except Exception:
        # Currency tablosu henüz yoksa veya boşsa dummy ID'ler (Demo ortamı için)
        print("⚠️ Para birimi tablosu okunamadı, varsayılan ID'ler kullanılıyor.")
        try_id, usd_id, eur_id = 1, 2, 3

    def get_unit_id(code):
        u = session.query(Unit).filter(Unit.code == code).first()
        return u.id if u else session.query(Unit).filter(Unit.code == "ADET").first().id

    # --- 2. Kategorilerin Oluşturulması ---
    categories_data = [
        # Ana Dallar
        {"code": "HM", "name": "Hammadde", "parent": None},
        {"code": "YM", "name": "Yarı Mamul", "parent": None},
        {"code": "MAM", "name": "Mamul Ürün", "parent": None},
        {"code": "AMB", "name": "Ambalaj Malzemesi", "parent": None},
        {"code": "YDK", "name": "Yedek Parça & Teknik", "parent": None},
        # Hammadde Alt
        {"code": "HM-PVC", "name": "PVC Reçine (Resin)", "parent": "HM"},
        {"code": "HM-YAG", "name": "Plastifiyan ve Yağlar", "parent": "HM"},
        {
            "code": "HM-KAT",
            "name": "Katkı Malzemeleri (Antiblok/Antifog)",
            "parent": "HM",
        },
        {"code": "HM-BOY", "name": "Masterbatch Boyalar", "parent": "HM"},
        # Mamul Alt
        {"code": "MAM-GID", "name": "Gıda Streci", "parent": "MAM"},
        {"code": "MAM-END", "name": "Endüstriyel Palet Streci", "parent": "MAM"},
        {"code": "MAM-SVR", "name": "Sıvı Sarma (Silaj)", "parent": "MAM"},
        # Ambalaj Alt
        {"code": "AMB-KUT", "name": "Kutu ve Koli", "parent": "AMB"},
        {"code": "AMB-MAS", "name": "Masura (Karton Boru)", "parent": "AMB"},
        {"code": "AMB-ETK", "name": "Etiket ve Barkod", "parent": "AMB"},
        # Yedek Parça Alt
        {"code": "YDK-MEK", "name": "Mekanik Aksam", "parent": "YDK"},
        {"code": "YDK-ELK", "name": "Elektrik & Elektronik", "parent": "YDK"},
        {"code": "YDK-SARF", "name": "İşletme Sarf Malzemeleri", "parent": "YDK"},
    ]

    cat_map = {}
    for cat in categories_data:
        existing = (
            session.query(ItemCategory).filter(ItemCategory.code == cat["code"]).first()
        )
        if not existing:
            parent_id = cat_map.get(cat["parent"])
            new_cat = ItemCategory(
                code=cat["code"], name=cat["name"], parent_id=parent_id
            )
            session.add(new_cat)
            session.flush()
            cat_map[cat["code"]] = new_cat.id
        else:
            cat_map[cat["code"]] = existing.id

    # --- 3. Stok Kartlarının Tanımlanması ---
    # Not: Fiyatlar 2025-2026 tahmini piyasa fiyatlarıdır.

    items_to_create = []

    # --- A. HAMMADDELER ---
    items_to_create.extend(
        [
            {
                "code": "HM-PVC-001",
                "name": "PVC Reçine S65 (K65) Süspansiyon",
                "cat": "HM-PVC",
                "type": ItemType.HAMMADDE,
                "unit": "KG",
                "curr": usd_id,
                "price": 0.85,
                "origin": "Güney Kore",
                "brand": "LG Chem",
                "min_stock": 20000,
                "lead_time": 45,
                "gtip": "3904.10.00.00.11",
                "track_lot": True,
                "weight": 1.0,
                "desc": "Genel maksatlı film üretimi için.",
            },
            {
                "code": "HM-PVC-002",
                "name": "PVC Reçine S70 (K70) Yüksek Viskozite",
                "cat": "HM-PVC",
                "type": ItemType.HAMMADDE,
                "unit": "KG",
                "curr": usd_id,
                "price": 0.88,
                "origin": "Türkiye",
                "brand": "Petkim",
                "min_stock": 10000,
                "lead_time": 7,
                "gtip": "3904.10.00.00.12",
                "track_lot": True,
                "weight": 1.0,
                "desc": "Yüksek mukavemet gerektiren filmler için.",
            },
            {
                "code": "HM-YAG-001",
                "name": "DOTP (Dioktil Tereftalat) Plastifiyan",
                "cat": "HM-YAG",
                "type": ItemType.HAMMADDE,
                "unit": "KG",
                "curr": usd_id,
                "price": 1.10,
                "origin": "Türkiye",
                "brand": "Basf",
                "min_stock": 5000,
                "lead_time": 3,
                "gtip": "2917.39.95.90.13",
                "track_lot": True,
                "is_liquid": True,
                "desc": "Ftalat içermeyen yumuşatıcı yağ.",
            },
            {
                "code": "HM-YAG-002",
                "name": "DOA (Dioktil Adipat) Soğuk Direnç Ajanı",
                "cat": "HM-YAG",
                "type": ItemType.HAMMADDE,
                "unit": "KG",
                "curr": eur_id,
                "price": 1.95,
                "origin": "Almanya",
                "brand": "Lanxess",
                "min_stock": 1000,
                "lead_time": 20,
                "desc": "Dondurulmuş gıda streci için esneklik sağlar.",
            },
            {
                "code": "HM-YAG-003",
                "name": "Epoksidize Soya Yağı (ESBO)",
                "cat": "HM-YAG",
                "type": ItemType.HAMMADDE,
                "unit": "KG",
                "curr": usd_id,
                "price": 1.45,
                "origin": "Çin",
                "brand": "Drako",
                "min_stock": 2000,
                "lead_time": 60,
                "desc": "Isı stabilizatörü ve yardımcı yumuşatıcı.",
            },
            {
                "code": "HM-KAT-001",
                "name": "Sıvı Antifog (Buğu Önleyici)",
                "cat": "HM-KAT",
                "type": ItemType.HAMMADDE,
                "unit": "KG",
                "curr": eur_id,
                "price": 5.20,
                "origin": "İtalya",
                "brand": "Palo",
                "min_stock": 500,
                "lead_time": 30,
                "desc": "Gıda ambalajında su damlacığı oluşumunu engeller.",
            },
            {
                "code": "HM-KAT-002",
                "name": "Ca-Zn Stabilizatör (Kalsiyum Çinko)",
                "cat": "HM-KAT",
                "type": ItemType.HAMMADDE,
                "unit": "KG",
                "curr": eur_id,
                "price": 2.80,
                "origin": "Türkiye",
                "brand": "Akdeniz Kimya",
                "min_stock": 1500,
                "lead_time": 5,
                "desc": "Isıl kararlılık sağlayıcı, şeffaf.",
            },
            {
                "code": "HM-BOY-001",
                "name": "Sarı Masterbatch (Limon Küfü)",
                "cat": "HM-BOY",
                "type": ItemType.HAMMADDE,
                "unit": "KG",
                "curr": usd_id,
                "price": 3.50,
                "origin": "Türkiye",
                "min_stock": 100,
                "desc": "Gıda streci renklendirme.",
            },
            {
                "code": "HM-BOY-002",
                "name": "Mor Masterbatch (Premium)",
                "cat": "HM-BOY",
                "type": ItemType.HAMMADDE,
                "unit": "KG",
                "curr": usd_id,
                "price": 4.10,
                "origin": "Türkiye",
                "min_stock": 50,
                "desc": "Özel üretim endüstriyel film için.",
            },
        ]
    )

    # --- B. YARI MAMULLER (Jumbo Bobinler) ---
    # Farklı kalınlıklar (mikron)
    microns = [8, 9, 10, 12, 14, 17, 23, 30, 46]
    for mic in microns:
        items_to_create.append(
            {
                "code": f"YM-JUMBO-{mic:02d}",
                "name": f"Jumbo Bobin PVC Streç {mic} Mikron",
                "cat": "YM",
                "type": ItemType.YARI_MAMUL,
                "unit": "KG",
                "curr": usd_id,
                "price": 1.60,  # Tahmini üretim maliyeti
                "origin": "Dahili Üretim",
                "track_lot": True,
                "desc": f"{mic} mikron kalınlığında dilimlenmemiş ana bobin.",
            }
        )

    # --- C. MAMULLER (Satılabilir Ürünler) ---
    # Gıda Streci (30cm ve 45cm)
    for width in [30, 45]:
        for length in [300, 1500]:
            code_suffix = "KUTULU" if length <= 300 else "JUMBO"
            items_to_create.append(
                {
                    "code": f"MAM-GID-{width}-{length}",
                    "name": f"Gıda Streci {width}cm x {length}m 8mic",
                    "cat": "MAM-GID",
                    "type": ItemType.MAMUL,
                    "unit": "ADET",
                    "curr": try_id,
                    "price": (Decimal(length) * Decimal(width) * Decimal("0.005"))
                    + Decimal("15"),  # Basit fiyat formülü
                    "sale_price": (Decimal(length) * Decimal(width) * Decimal("0.008"))
                    + Decimal("25"),
                    "min_stock": 500,
                    "brand": "FreshWrap",
                    "barcode": f"8690000{width}{length}",
                    "track_lot": True,
                    "track_expiry": True,
                    "shelf_life": 365,
                }
            )

    # Endüstriyel Streç (17 ve 23 mikron)
    industrial_specs = [
        (17, 50, 200, "El Tipi Standart"),
        (17, 50, 300, "El Tipi Ekonomik"),
        (23, 50, 200, "El Tipi Ağır Hizmet"),
        (17, 50, 1500, "Makine Tipi Standart"),
        (23, 50, 1500, "Makine Tipi Power"),
        (46, 50, 1200, "Süper Power Makine"),
    ]
    for mic, width, length, desc in industrial_specs:
        type_prefix = "EL" if length < 1000 else "MAK"
        items_to_create.append(
            {
                "code": f"MAM-END-{type_prefix}-{mic}-{length}",
                "name": f"{desc} Streç {mic}mic {width}cm {length}m",
                "cat": "MAM-END",
                "type": ItemType.MAMUL,
                "unit": "RULO",
                "curr": try_id,
                "price": Decimal(length) * Decimal("1.2"),  # Maliyet
                "sale_price": Decimal(length) * Decimal("1.8"),  # Satış
                "min_stock": 200,
                "brand": "ProPack",
                "barcode": f"869111{mic}{length}",
                "track_lot": True,
                "weight": (mic * width * length * 1.25 / 10000)
                + 0.5,  # Tahmini ağırlık hesaplama
            }
        )

    # --- D. AMBALAJ MALZEMELERİ ---
    items_to_create.extend(
        [
            {
                "code": "AMB-MAS-50-EL",
                "name": "Masura 50cm - 300gr (El Tipi)",
                "cat": "AMB-MAS",
                "type": ItemType.SARF,
                "unit": "ADET",
                "curr": try_id,
                "price": 4.50,
                "min_stock": 5000,
            },
            {
                "code": "AMB-MAS-50-MK",
                "name": "Masura 50cm - 1200gr (Makine Tipi)",
                "cat": "AMB-MAS",
                "type": ItemType.SARF,
                "unit": "ADET",
                "curr": try_id,
                "price": 12.00,
                "min_stock": 2000,
            },
            {
                "code": "AMB-MAS-30-GD",
                "name": "Masura 30cm - Gıda İnce",
                "cat": "AMB-MAS",
                "type": ItemType.SARF,
                "unit": "ADET",
                "curr": try_id,
                "price": 3.00,
                "min_stock": 10000,
            },
            {
                "code": "AMB-KOLI-6LI",
                "name": "Oluklu Koli 50x30x30 (6'lı)",
                "cat": "AMB-KUT",
                "type": ItemType.SARF,
                "unit": "ADET",
                "curr": try_id,
                "price": 18.50,
                "min_stock": 1000,
            },
            {
                "code": "AMB-KUTU-TEK",
                "name": "Baskılı Gıda Kutusu 30cm",
                "cat": "AMB-KUT",
                "type": ItemType.SARF,
                "unit": "ADET",
                "curr": try_id,
                "price": 6.75,
                "min_stock": 5000,
            },
            {
                "code": "AMB-ETK-001",
                "name": "Ürün Etiketi (Termal 100x50)",
                "cat": "AMB-ETK",
                "type": ItemType.SARF,
                "unit": "RULO",
                "curr": try_id,
                "price": 85.00,
                "min_stock": 50,
            },
        ]
    )

    # --- E. YEDEK PARÇA VE TEKNİK ---
    # Gerçekçi ve çeşitli yedek parçalar
    spares = [
        (
            "YDK-001",
            "Extruder Vida (Screw) Ø90mm",
            "YDK-MEK",
            4500.00,
            usd_id,
            "Çelik alaşım ana vida",
        ),
        (
            "YDK-002",
            "Kovan (Barrel) Isıtıcı Ceket",
            "YDK-MEK",
            1200.00,
            usd_id,
            "Kovan dış gömleği",
        ),
        (
            "YDK-003",
            "Seramik Rezistans 220V 1500W",
            "YDK-ELK",
            45.00,
            usd_id,
            "Kovan ısıtma",
        ),
        (
            "YDK-004",
            "Melt Pressure Sensor (Basınç Sensörü)",
            "YDK-ELK",
            280.00,
            usd_id,
            "Gefran marka",
        ),
        ("YDK-005", "Solid State Relay (SSR) 40A", "YDK-ELK", 25.00, usd_id, "Fotek"),
        (
            "YDK-006",
            "Dilimleme Jileti (Paket)",
            "YDK-SARF",
            150.00,
            try_id,
            "100'lü paket sanayi tipi",
        ),
        (
            "YDK-007",
            "Teflon Bant (Isıya Dayanıklı)",
            "YDK-SARF",
            85.00,
            try_id,
            "Yapışkanlı teflon",
        ),
        (
            "YDK-008",
            "Redüktör Yağı (ISO VG 320)",
            "YDK-SARF",
            2500.00,
            try_id,
            "20 Litre teneke",
        ),
        (
            "YDK-009",
            "Frekans İnvertörü 37kW",
            "YDK-ELK",
            1800.00,
            usd_id,
            "ABB/Siemens Sürücü",
        ),
        (
            "YDK-010",
            "Termokupl J Tipi 2m",
            "YDK-ELK",
            15.00,
            usd_id,
            "Isı okuyucu prob",
        ),
        (
            "YDK-011",
            "Pnömatik Valf 5/2 24VDC",
            "YDK-MEK",
            45.00,
            usd_id,
            "Festo muadili",
        ),
        (
            "YDK-012",
            "Hava Şaftı (Air Shaft) 3 inç",
            "YDK-MEK",
            650.00,
            usd_id,
            "Bobin sarıcı şaft",
        ),
        ("YDK-013", "Rulman 6206 ZZ C3", "YDK-MEK", 120.00, try_id, "SKF/FAG"),
        (
            "YDK-014",
            "Döner Başlık Keçesi",
            "YDK-MEK",
            350.00,
            try_id,
            "Yüksek ısı silikon",
        ),
        (
            "YDK-015",
            "Manüel Çemberleme Makinesi",
            "YDK-SARF",
            2500.00,
            try_id,
            "Paletleme için",
        ),
    ]

    for code, name, cat_code, price, curr, desc in spares:
        items_to_create.append(
            {
                "code": code,
                "name": name,
                "cat": cat_code,
                "type": ItemType.SARF,
                "unit": "ADET",
                "curr": curr,
                "price": price,
                "min_stock": 1 if price > 500 else 5,
                "desc": desc,
            }
        )

    # --- 4. Veritabanına Yazma ---
    count = 0
    for item_data in items_to_create:
        exists = session.query(Item).filter(Item.code == item_data["code"]).first()

        if not exists:
            # Currency ve Unit ID'leri ayarla
            unit_code = item_data.get("unit", "ADET")
            unit_id = get_unit_id(unit_code)

            # Fiyat dönüşümleri (Basit mantık)
            p_price = Decimal(str(item_data.get("price", 0)))
            s_price = Decimal(str(item_data.get("sale_price", 0)))

            # Sale price yoksa maliyetin üstüne %20 koy
            if s_price == 0 and item_data["type"] in [
                ItemType.MAMUL,
                ItemType.YARI_MAMUL,
            ]:
                s_price = p_price * Decimal("1.2")

            new_item = Item(
                code=item_data["code"],
                name=item_data["name"],
                item_type=item_data["type"],
                category_id=cat_map.get(item_data["cat"]),
                unit_id=unit_id,
                currency_id=item_data.get("curr", try_id),
                purchase_price=p_price,
                sale_price=s_price,
                list_price=s_price * Decimal("1.1"),  # Liste fiyatı %10 daha yüksek
                # Detaylar
                barcode=item_data.get("barcode"),
                gtip_code=item_data.get("gtip"),
                brand=item_data.get("brand"),
                origin_country=item_data.get("origin", "Türkiye"),
                description=item_data.get("desc"),
                # Stok Limitleri
                min_stock=Decimal(str(item_data.get("min_stock", 0))),
                max_stock=Decimal(str(item_data.get("min_stock", 0))) * 5,
                lead_time_days=item_data.get("lead_time", 7),
                # İzleme
                track_lot=item_data.get("track_lot", False),
                track_expiry=item_data.get("track_expiry", False),
                shelf_life_days=item_data.get("shelf_life"),
                # Fiziksel
                weight=Decimal(str(item_data.get("weight", 0))),
                is_active=True,
            )
            session.add(new_item)
            count += 1
            if count % 10 == 0:
                print(f"✅ {count} stok kartı hazırlandı...")
        else:
            pass  # Zaten varsa atla

    try:
        session.commit()
        print(
            f"\n🎉 İşlem Tamamlandı! Toplam {count} yeni stok kartı veritabanına eklendi."
        )
    except Exception as e:
        session.rollback()
        print(f"\n❌ Hata oluştu: {str(e)}")
    finally:
        session.close()


if __name__ == "__main__":
    create_pvc_inventory_full()
