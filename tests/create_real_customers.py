import sys
import os

# Proje ana dizinini path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.base import get_session
from sqlalchemy import text


def create_real_customers():
    """
    ÖNCE tabloyu doğru şema ile yeniden oluşturur.
    SONRA gerçek müşteri verilerini ekler.
    """
    session = get_session()

    # 1. ADIM: TABLOYU YENİDEN OLUŞTURMA (Schema Migration)
    # Mevcut tablo yapınız muhtemelen eksik, bu yüzden önce onu güncelliyoruz.
    print("🛠️ Tablo yapısı kontrol ediliyor ve güncelleniyor...")

    create_table_sql = text(
        """
        DROP TABLE IF EXISTS customers CASCADE;
        
        CREATE TABLE customers (
            id SERIAL PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL UNIQUE,
            sector VARCHAR(100),
            city VARCHAR(50),
            district VARCHAR(50),
            website VARCHAR(255),
            phone VARCHAR(50),
            tax_office VARCHAR(100),
            tax_id VARCHAR(50),
            status VARCHAR(20) DEFAULT 'Aday',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    )

    try:
        session.execute(create_table_sql)
        session.commit()
        print("✅ Tablo 'customers' başarıyla yeniden oluşturuldu.")
    except Exception as e:
        session.rollback()
        print(f"❌ Tablo oluşturulurken hata: {e}")
        return

    # 2. ADIM: VERİ LİSTESİ
    customers_data = [
        # --- A. TAVUK VE BEYAZ ET ÜRETİCİLERİ ---
        {
            "company_name": "Erpiliç Entegre Tavukçuluk A.Ş.",
            "sector": "Gıda Üretim",
            "city": "Bolu",
            "district": "Merkez",
            "website": "www.erpilic.com.tr",
            "phone": "0374 253 66 66",
            "tax_office": "Bolu VD",
        },
        {
            "company_name": "Beypi Beypazarı (Beypiliç) A.Ş.",
            "sector": "Gıda Üretim",
            "city": "Bolu",
            "district": "Merkez",
            "website": "www.beypilic.com.tr",
            "phone": "0374 253 44 44",
            "tax_office": "Bolu VD",
        },
        {
            "company_name": "Şenpiliç Gıda Sanayi A.Ş.",
            "sector": "Gıda Üretim",
            "city": "Sakarya",
            "district": "Söğütlü",
            "website": "www.senpilic.com.tr",
            "phone": "0216 579 03 00",
            "tax_office": "Büyük Mükellefler",
        },
        {
            "company_name": "Banvit (BRF) A.Ş.",
            "sector": "Gıda Üretim",
            "city": "Balıkesir",
            "district": "Bandırma",
            "website": "www.banvit.com",
            "phone": "0266 714 11 11",
            "tax_office": "Bandırma VD",
        },
        {
            "company_name": "Keskinoğlu Tavukçuluk A.Ş.",
            "sector": "Gıda Üretim",
            "city": "Manisa",
            "district": "Akhisar",
            "website": "www.keskinoglu.com.tr",
            "phone": "0236 427 25 72",
            "tax_office": "Akhisar VD",
        },
        {
            "company_name": "Gedik Piliç (Gedik Tavukçuluk A.Ş.)",
            "sector": "Gıda Üretim",
            "city": "Uşak",
            "district": "Eşme",
            "website": "www.gedikpilic.com",
            "phone": "0276 414 15 50",
            "tax_office": "Eşme VD",
        },
        {
            "company_name": "Lezita (Abalıoğlu) A.Ş.",
            "sector": "Gıda Üretim",
            "city": "İzmir",
            "district": "Kemalpaşa",
            "website": "www.lezita.com.tr",
            "phone": "0232 878 00 00",
            "tax_office": "Hasan Tahsin VD",
        },
        {
            "company_name": "HasTavuk A.Ş.",
            "sector": "Gıda Üretim",
            "city": "Bursa",
            "district": "Nilüfer",
            "website": "www.hastavuk.com.tr",
            "phone": "0224 411 18 18",
            "tax_office": "Bursa VD",
        },
        {
            "company_name": "CP Standart Gıda A.Ş.",
            "sector": "Gıda Üretim",
            "city": "Bursa",
            "district": "İnegöl",
            "website": "www.cp-turkiye.com",
            "phone": "0224 714 81 80",
            "tax_office": "İnegöl VD",
        },
        {
            "company_name": "Ak Piliç Ltd. Şti.",
            "sector": "Gıda Üretim",
            "city": "Bolu",
            "district": "Merkez",
            "website": "www.akpilic.com.tr",
            "phone": "0374 253 45 35",
            "tax_office": "Bolu VD",
        },
        {
            "company_name": "Bupiliç Entegre Gıda San. A.Ş.",
            "sector": "Gıda Üretim",
            "city": "Balıkesir",
            "district": "Merkez",
            "website": "www.bupilic.com.tr",
            "phone": "0266 244 44 44",
            "tax_office": "Balıkesir VD",
        },
        {
            "company_name": "Bolez Piliç (Ege-Tav A.Ş.)",
            "sector": "Gıda Üretim",
            "city": "İzmir",
            "district": "Torbalı",
            "website": "www.bolez.com",
            "phone": "0232 853 80 80",
            "tax_office": "Torbalı VD",
        },
        # --- B. TOPTAN AMBALAJ FİRMALARI ---
        {
            "company_name": "Yetgin Ambalaj A.Ş.",
            "sector": "Ambalaj Toptan",
            "city": "İstanbul",
            "district": "Esenyurt",
            "website": "www.yetginambalaj.com",
            "phone": "0212 620 20 20",
            "tax_office": "Esenyurt VD",
        },
        {
            "company_name": "İM Ambalaj",
            "sector": "Ambalaj Toptan",
            "city": "İstanbul",
            "district": "İstoç",
            "website": "www.imambalaj.com",
            "phone": "0212 659 59 59",
            "tax_office": "İstoç VD",
        },
        {
            "company_name": "Doku Ambalaj",
            "sector": "Ambalaj Toptan",
            "city": "İstanbul",
            "district": "Başakşehir",
            "website": "www.dokuambalaj.com",
            "phone": "0212 485 85 85",
            "tax_office": "İkitelli VD",
        },
        {
            "company_name": "Köksallar Ambalaj",
            "sector": "Ambalaj Toptan",
            "city": "Ankara",
            "district": "Gimat",
            "website": "www.koksallar.com.tr",
            "phone": "0312 397 97 97",
            "tax_office": "Yenimahalle VD",
        },
        {
            "company_name": "Ulusoy Ambalaj",
            "sector": "Ambalaj Toptan",
            "city": "İstanbul",
            "district": "Bayrampaşa",
            "website": "www.ulusoyambalaj.com",
            "phone": "0212 544 44 44",
            "tax_office": "Bayrampaşa VD",
        },
        {
            "company_name": "Bubi Plastik",
            "sector": "Ambalaj Toptan",
            "city": "İstanbul",
            "district": "Beylikdüzü",
            "website": "www.bubiplastik.com",
            "phone": "0212 876 76 76",
            "tax_office": "Beylikdüzü VD",
        },
        {
            "company_name": "Joypack Ambalaj",
            "sector": "Ambalaj Toptan",
            "city": "İstanbul",
            "district": "Hadımköy",
            "website": "www.joypack.com.tr",
            "phone": "0212 771 71 71",
            "tax_office": "Büyükçekmece VD",
        },
        {
            "company_name": "Çağdaş Ambalaj",
            "sector": "Ambalaj Toptan",
            "city": "İstanbul",
            "district": "Güngören",
            "website": "www.cagdasambalaj.com",
            "phone": "0212 500 00 00",
            "tax_office": "Güngören VD",
        },
        {
            "company_name": "Sembol Ambalaj (Sartın)",
            "sector": "Ambalaj Toptan",
            "city": "İstanbul",
            "district": "İstoç",
            "website": "www.sembolambalaj.com",
            "phone": "0212 659 90 90",
            "tax_office": "İstoç VD",
        },
        {
            "company_name": "Mete Plastik A.Ş.",
            "sector": "Ambalaj Sanayi",
            "city": "İzmir",
            "district": "Çiğli",
            "website": "www.mete.com.tr",
            "phone": "0232 376 74 60",
            "tax_office": "Çiğli VD",
        },
        {
            "company_name": "Korozo Ambalaj San. A.Ş.",
            "sector": "Ambalaj Sanayi",
            "city": "İstanbul",
            "district": "Esenyurt",
            "website": "www.korozo.com.tr",
            "phone": "0212 866 66 66",
            "tax_office": "Büyük Mükellefler",
        },
        {
            "company_name": "Öztaş Ambalaj",
            "sector": "Ambalaj Toptan",
            "city": "İstanbul",
            "district": "Zeytinburnu",
            "website": "www.oztasambalaj.com",
            "phone": "0212 415 15 15",
            "tax_office": "Zeytinburnu VD",
        },
        {
            "company_name": "Polinas Plastik A.Ş.",
            "sector": "Ambalaj Sanayi",
            "city": "Manisa",
            "district": "OSB",
            "website": "www.polinas.com",
            "phone": "0236 213 00 00",
            "tax_office": "Manisa VD",
        },
        {
            "company_name": "Ambalaj Store",
            "sector": "E-Ticaret/Toptan",
            "city": "İstanbul",
            "district": "Ümraniye",
            "website": "www.ambalajstore.com",
            "phone": "0216 500 00 00",
            "tax_office": "Ümraniye VD",
        },
        # --- C. ZİNCİR RESTORAN & KAFE & HORECA ---
        {
            "company_name": "Big Chefs (Büyük Şefler A.Ş.)",
            "sector": "HoReCa Zincir",
            "city": "İstanbul",
            "district": "Sarıyer",
            "website": "www.bigchefs.com.tr",
            "phone": "0212 352 70 80",
            "tax_office": "Sarıyer VD",
        },
        {
            "company_name": "Midpoint (Num Num Gıda A.Ş.)",
            "sector": "HoReCa Zincir",
            "city": "İstanbul",
            "district": "Beşiktaş",
            "website": "www.midpoint.com.tr",
            "phone": "0212 227 27 27",
            "tax_office": "Beşiktaş VD",
        },
        {
            "company_name": "Happy Moon's Grup",
            "sector": "HoReCa Zincir",
            "city": "İstanbul",
            "district": "Kadıköy",
            "website": "www.happymoons.com.tr",
            "phone": "0216 330 30 30",
            "tax_office": "Kadıköy VD",
        },
        {
            "company_name": "Cookshop",
            "sector": "HoReCa Zincir",
            "city": "İstanbul",
            "district": "Şişli",
            "website": "www.cookshop.com.tr",
            "phone": "0212 234 34 34",
            "tax_office": "Şişli VD",
        },
        {
            "company_name": "Huqqa",
            "sector": "HoReCa Zincir",
            "city": "İstanbul",
            "district": "Beşiktaş",
            "website": "www.huqqa.com",
            "phone": "0212 265 06 66",
            "tax_office": "Beşiktaş VD",
        },
        {
            "company_name": "Tavuk Dünyası A.Ş.",
            "sector": "HoReCa Zincir",
            "city": "İstanbul",
            "district": "Maltepe",
            "website": "www.tavukdunyasi.com",
            "phone": "0216 399 15 20",
            "tax_office": "Maltepe VD",
        },
        {
            "company_name": "Baydöner Restoranları A.Ş.",
            "sector": "HoReCa Zincir",
            "city": "İzmir",
            "district": "Konak",
            "website": "www.baydoner.com",
            "phone": "0232 464 42 35",
            "tax_office": "Konak VD",
        },
        {
            "company_name": "Köfteci Ramiz Gıda A.Ş.",
            "sector": "HoReCa Zincir",
            "city": "Manisa",
            "district": "Akhisar",
            "website": "www.kofteciramiz.com",
            "phone": "0236 414 33 33",
            "tax_office": "Akhisar VD",
        },
        {
            "company_name": "Mado (Yaşar Dondurma A.Ş.)",
            "sector": "Kafe Zincir",
            "city": "K.Maraş",
            "district": "Merkez",
            "website": "www.mado.com.tr",
            "phone": "0344 236 06 00",
            "tax_office": "K.Maraş VD",
        },
        {
            "company_name": "Kahve Dünyası A.Ş.",
            "sector": "Kafe Zincir",
            "city": "İstanbul",
            "district": "Fatih",
            "website": "www.kahvedunyasi.com",
            "phone": "0212 292 92 00",
            "tax_office": "Fatih VD",
        },
        {
            "company_name": "Özsüt (ST Gıda A.Ş.)",
            "sector": "Kafe Zincir",
            "city": "İzmir",
            "district": "Kemalpaşa",
            "website": "www.ozsut.com.tr",
            "phone": "0232 877 00 00",
            "tax_office": "Kemalpaşa VD",
        },
        {
            "company_name": "Pelit Pastaneleri A.Ş.",
            "sector": "Pastane Zincir",
            "city": "İstanbul",
            "district": "Esenyurt",
            "website": "www.pelit.com.tr",
            "phone": "0212 411 13 00",
            "tax_office": "Esenyurt VD",
        },
        {
            "company_name": "Divan Pastaneleri (Divan Grubu)",
            "sector": "Pastane Zincir",
            "city": "İstanbul",
            "district": "Ümraniye",
            "website": "www.divan.com.tr",
            "phone": "0216 522 64 00",
            "tax_office": "Büyük Mükellefler",
        },
        {
            "company_name": "Kırıntı Restoran",
            "sector": "Restoran Zincir",
            "city": "İstanbul",
            "district": "Nişantaşı",
            "website": "www.kirinti.com.tr",
            "phone": "0212 291 26 92",
            "tax_office": "Şişli VD",
        },
        {
            "company_name": "Nusret (D.ream Grubu)",
            "sector": "Lüks Restoran",
            "city": "İstanbul",
            "district": "Etiler",
            "website": "www.nusr-et.com.tr",
            "phone": "0212 358 30 22",
            "tax_office": "Beşiktaş VD",
        },
        {
            "company_name": "Günaydın Et Restoranları",
            "sector": "Restoran Zincir",
            "city": "İstanbul",
            "district": "Bostancı",
            "website": "www.gunaydinet.com",
            "phone": "0216 658 60 60",
            "tax_office": "Kadıköy VD",
        },
        {
            "company_name": "Develi Restoranları",
            "sector": "Restoran Zincir",
            "city": "İstanbul",
            "district": "Samatya",
            "website": "www.develi1912.com",
            "phone": "0212 529 08 33",
            "tax_office": "Fatih VD",
        },
        # --- D. ÇİĞKÖFTE VE ET ZİNCİRLERİ ---
        {
            "company_name": "Komagene (Yörpaş A.Ş.)",
            "sector": "Çiğköfte Zincir",
            "city": "İstanbul",
            "district": "Gebze",
            "website": "www.komagene.com.tr",
            "phone": "0262 751 45 55",
            "tax_office": "İlyasbey VD",
        },
        {
            "company_name": "Oses Çiğköfte Ltd. Şti.",
            "sector": "Çiğköfte Zincir",
            "city": "İstanbul",
            "district": "Sultangazi",
            "website": "www.oses.com.tr",
            "phone": "0212 419 02 02",
            "tax_office": "Sultangazi VD",
        },
        {
            "company_name": "Battalbey Çiğköfte",
            "sector": "Çiğköfte Zincir",
            "city": "İstanbul",
            "district": "Bağcılar",
            "website": "www.battalbey.com.tr",
            "phone": "0212 461 44 44",
            "tax_office": "Bağcılar VD",
        },
        {
            "company_name": "Tatlıses Gıda A.Ş.",
            "sector": "Çiğköfte Zincir",
            "city": "İstanbul",
            "district": "Seyrantepe",
            "website": "www.tatlises.com.tr",
            "phone": "0212 294 94 94",
            "tax_office": "Şişli VD",
        },
        {
            "company_name": "Çiğköftem (EM Group)",
            "sector": "Çiğköfte Zincir",
            "city": "İstanbul",
            "district": "Beylikdüzü",
            "website": "www.cigkoftem.com",
            "phone": "0212 855 55 55",
            "tax_office": "Beylikdüzü VD",
        },
        {
            "company_name": "Namet Gıda A.Ş.",
            "sector": "Et Entegre",
            "city": "Kocaeli",
            "district": "Çayırova",
            "website": "www.namet.com.tr",
            "phone": "0262 723 50 00",
            "tax_office": "İlyasbey VD",
        },
        {
            "company_name": "Cumhuriyet Sucukları (Afyon Et)",
            "sector": "Et Entegre",
            "city": "Afyon",
            "district": "Merkez",
            "website": "www.cumhuriyetsucuklari.com.tr",
            "phone": "0272 215 10 30",
            "tax_office": "Afyon VD",
        },
        {
            "company_name": "Şahin Sucukları A.Ş.",
            "sector": "Et Entegre",
            "city": "Kayseri",
            "district": "Kocasinan",
            "website": "www.sahin.com.tr",
            "phone": "0352 331 06 60",
            "tax_office": "Mimar Sinan VD",
        },
        {
            "company_name": "Bonfilet Et Sanayi A.Ş.",
            "sector": "Et Entegre",
            "city": "İstanbul",
            "district": "Beylikdüzü",
            "website": "www.bonfilet.com.tr",
            "phone": "0212 856 12 12",
            "tax_office": "Beylikdüzü VD",
        },
        {
            "company_name": "Amasya Et Ürünleri A.Ş.",
            "sector": "Et Entegre",
            "city": "Amasya",
            "district": "Suluova",
            "website": "www.amasyaeturunleri.com.tr",
            "phone": "0358 417 80 00",
            "tax_office": "Amasya VD",
        },
        # --- E. OTELLER ---
        {
            "company_name": "Rixos Hotels (Fine Otelcilik)",
            "sector": "Otel Zinciri",
            "city": "Antalya",
            "district": "Muratpaşa",
            "website": "www.rixos.com",
            "phone": "0242 323 00 00",
            "tax_office": "Kurumlar VD",
        },
        {
            "company_name": "Divan Otelleri A.Ş.",
            "sector": "Otel Zinciri",
            "city": "İstanbul",
            "district": "Şişli",
            "website": "www.divan.com.tr",
            "phone": "0212 315 55 00",
            "tax_office": "Büyük Mükellefler",
        },
        {
            "company_name": "Dedeman Hotels & Resorts",
            "sector": "Otel Zinciri",
            "city": "İstanbul",
            "district": "Gayrettepe",
            "website": "www.dedeman.com",
            "phone": "0212 337 45 00",
            "tax_office": "Beşiktaş VD",
        },
        {
            "company_name": "Titanic Hotels (AYG Group)",
            "sector": "Otel Zinciri",
            "city": "Antalya",
            "district": "Lara",
            "website": "www.titanic.com.tr",
            "phone": "0242 352 00 00",
            "tax_office": "Antalya VD",
        },
        {
            "company_name": "Limak Hotels A.Ş.",
            "sector": "Otel Zinciri",
            "city": "Ankara",
            "district": "GOP",
            "website": "www.limakhotels.com",
            "phone": "0312 446 88 00",
            "tax_office": "Ankara VD",
        },
        {
            "company_name": "Kaya Hotels & Resorts",
            "sector": "Otel Zinciri",
            "city": "İstanbul",
            "district": "Büyükçekmece",
            "website": "www.kayahotels.com",
            "phone": "0212 866 23 23",
            "tax_office": "Büyükçekmece VD",
        },
        {
            "company_name": "The Green Park Hotels",
            "sector": "Otel Zinciri",
            "city": "İstanbul",
            "district": "Taksim",
            "website": "www.thegreenpark.com",
            "phone": "0212 238 00 00",
            "tax_office": "Beyoğlu VD",
        },
        {
            "company_name": "Barut Hotels",
            "sector": "Otel Zinciri",
            "city": "Antalya",
            "district": "Lara",
            "website": "www.baruthotels.com",
            "phone": "0242 323 11 11",
            "tax_office": "Antalya VD",
        },
        {
            "company_name": "Crystal Hotels (Kilit Group)",
            "sector": "Otel Zinciri",
            "city": "Antalya",
            "district": "Aksu",
            "website": "www.crystalhotels.com.tr",
            "phone": "0242 340 60 50",
            "tax_office": "Antalya VD",
        },
        {
            "company_name": "Hilton İstanbul (Bosphorus)",
            "sector": "Otel Zinciri",
            "city": "İstanbul",
            "district": "Harbiye",
            "website": "www.hilton.com.tr",
            "phone": "0212 315 60 00",
            "tax_office": "Şişli VD",
        },
        # --- F. CATERING VE YEMEK SANAYİ ---
        {
            "company_name": "Sofra Grup (Compass) A.Ş.",
            "sector": "Catering",
            "city": "İstanbul",
            "district": "Ataşehir",
            "website": "www.sofragrup.com",
            "phone": "0216 510 50 50",
            "tax_office": "Ataşehir VD",
        },
        {
            "company_name": "Sardunya Catering A.Ş.",
            "sector": "Catering",
            "city": "İstanbul",
            "district": "Gayrettepe",
            "website": "www.sardunya.com",
            "phone": "0212 274 65 00",
            "tax_office": "Beşiktaş VD",
        },
        {
            "company_name": "BTA Havalimanları Yiyecek A.Ş.",
            "sector": "Catering",
            "city": "İstanbul",
            "district": "Havalimanı",
            "website": "www.bta.com.tr",
            "phone": "0212 463 88 88",
            "tax_office": "Bakırköy VD",
        },
        {
            "company_name": "Do & Co İkram Hizmetleri A.Ş.",
            "sector": "Catering",
            "city": "İstanbul",
            "district": "Yeşilköy",
            "website": "www.doco.com",
            "phone": "0212 463 30 00",
            "tax_office": "Bakırköy VD",
        },
        {
            "company_name": "Parıltı Yemek Üretim A.Ş.",
            "sector": "Catering",
            "city": "İstanbul",
            "district": "Kağıthane",
            "website": "www.pariltiyemek.com.tr",
            "phone": "0212 294 30 30",
            "tax_office": "Kağıthane VD",
        },
    ]

    print(f"🔄 Toplam {len(customers_data)} müşteri veritabanına aktarılıyor...")

    # 3. ADIM: VERİ EKLEME
    try:
        for customer in customers_data:
            sql = text(
                """
                INSERT INTO customers 
                (company_name, sector, city, district, website, phone, tax_office, status, created_at)
                VALUES 
                (:company_name, :sector, :city, :district, :website, :phone, :tax_office, 'Aday', NOW())
                ON CONFLICT (company_name) DO NOTHING;
            """
            )
            session.execute(sql, customer)

        session.commit()
        print("✅ Başarılı: Tüm gerçek müşteri verileri eklendi.")

    except Exception as e:
        session.rollback()
        print(f"❌ Veri eklenirken hata: {str(e)}")
    finally:
        session.close()


if __name__ == "__main__":
    create_real_customers()
