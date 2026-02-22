# Akıllı İş ERP

<p align="center">
<img src="ui/resources/icons/logo.svg" width="120" alt="Akıllı İş Logo">
</p>

<p align="center">
<strong>Orta ve Büyük Ölçekli İşletmeler için Modern, Modüler ERP Ekosistemi</strong>
</p>

<p align="center">
<img src="https://img.shields.io/badge/Python-3.12-blue.svg" alt="Python">
<img src="https://img.shields.io/badge/PyQt6-6.4+-green.svg" alt="PyQt6">
<img src="https://img.shields.io/badge/PostgreSQL-13+-orange.svg" alt="PostgreSQL">
<img src="https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg" alt="SQLAlchemy">
<img src="https://img.shields.io/badge/Alembic-Migrations-yellow.svg" alt="Alembic">
<img src="https://img.shields.io/badge/Architecture-Modular-purple.svg" alt="Architecture">
</p>

---

## Genel Bakış

Akıllı İş, tek bir masaüstü uygulamasında uçtan uca yönetim sunan, PyQt6 tabanlı modern bir ERP sistemidir. Stok ve üretimden muhasebe, İK ve proje yönetimine kadar 16+ işlevsel modül içerir. Mimari olarak her modül kendi `views/` ve `services.py` katmanına sahip olup merkezi bir veritabanı altyapısı ve denetim motoru üzerinde çalışır.

---

## Kurumsal Özellikler

| Özellik | Açıklama |
|---------|----------|
| **Bridge Mimarisi** | Modüller arası bağımlılığı azaltan köprü servisleri (Bordro↔Muhasebe, Kalite↔Stok) |
| **Audit Engine** | Veritabanı seviyesinde her değişikliği (kim, ne zaman, JSON farkıyla) otomatik loglayan denetim motoru |
| **E-Dönüşüm** | GİB standartlarında UBL 2.1 formatında E-Fatura, E-Arşiv, E-İrsaliye üretimi |
| **SSCC & İzlenebilirlik** | Palet/taşıma birimi bazlı lojistik yönetim ve lot/seri numarası bazlı uçtan uca soyağacı |
| **Dahili Mesajlaşma** | Status bar'dan açılan popup panel: direkt mesaj, grup, departman kanalı ve kayıt bazlı konuşmalar |
| **Zeki Bildirim Sistemi** | Kritik olaylarda (düşük stok, onay bekleyenler) anlık uygulama içi bildirimler |
| **İş Akışı Motoru** | Onay süreçleri ve görev atamaları için yapılandırılabilir iş akışı altyapısı |

---

## Modüller

### Dashboard

Ana kontrol paneli — Satış, üretim, stok ve finans özetleri; bekleyen onaylar ve son işlemler.

---

### Stok Yönetimi

Çoklu depo ve raf bazlı envanter yönetimi.

| Sayfa | Açıklama |
|-------|----------|
| Ürünler | Ürün tanımları, stok seviyeleri, maliyet takibi |
| Kategoriler | Hiyerarşik kategori yapısı |
| Hareketler | Giriş/çıkış/transfer hareketleri |
| Stok Sayımı | Dönemsel sayım planlaması ve fark raporları |
| SSCC Takibi | Palet ve taşıma birimi bazlı etiketleme ve takip |
| Stok Talepleri | Dahili stok talep yönetimi |
| Depolar | Depo ve lokasyon tanımları |
| Birim Yönetimi | Ölçü birimleri ve çevrim tabloları |
| Raporlar | Stok yaşlandırma, hareket özeti, değerleme raporları |

---

### Satınalma

Tedarik zinciri süreçlerinin uçtan uca yönetimi.

| Sayfa | Açıklama |
|-------|----------|
| Tedarikçiler | Tedarikçi kartları, iletişim bilgileri, değerlendirme geçmişi |
| Satın Alma Talepleri | Departman bazlı satın alma talepleri ve onay süreci |
| Satın Alma Siparişleri | Sipariş oluşturma, onay ve takip |
| Mal Kabul | Gelen mal kalite kontrolü ve stok girişi |
| Satın Alma Faturaları | Tedarikçi fatura eşleştirme ve muhasebe entegrasyonu |
| RFQ (Teklif Talebi) | Tedarikçilerden çoklu teklif toplama ve karşılaştırma matrisi |
| Tedarikçi Değerlendirme | Kalite, teslimat ve fiyat performansına göre otomatik puanlama |

---

### Planlama

Üretim ve kapasite planlama araçları.

| Sayfa | Açıklama |
|-------|----------|
| MPS Cockpit | Ana üretim planı yönetim merkezi |
| MRP Çalıştır | Malzeme ihtiyaç hesaplama ve öneri üretme |
| MRP Gereksinimleri | Malzeme açıkları ve ihtiyaç detayları |
| MRP Önerileri | Satın alma ve üretim emirleri için otomatik öneriler |
| Kapasite Planlaması | İş merkezi bazlı kapasite analizi ve yük dengesi |
| APS (İleri Planlama) | Sonlu kapasite çizelgeleme ve darboğaz analizi |

---

### Üretim

İş emri yaşam döngüsü ve atölye yönetimi.

| Sayfa | Açıklama |
|-------|----------|
| İş Emirleri | Üretim emirleri oluşturma, takip ve kapatma |
| Ürün Ağaçları (BOM) | Çok seviyeli malzeme listeleri yönetimi |
| İş İstasyonları | Makine ve çalışma merkezi tanımları |
| Üretim Takvimi | Görsel üretim çizelgesi |
| Kapasite Analizi | Gerçek kapasite kullanım raporları |
| Darboğaz Analizi | Kısıt kaynakları ve yük dengeleme önerileri |
| Operatör Paneli | Saha çalışanları için basitleştirilmiş üretim takip ve duruş girişi ekranı |

---

### Kalite Yönetimi

Gelen maldan üretim sürecine ve müşteri şikayetine kadar kapsamlı kalite kontrol.

| Sayfa | Açıklama |
|-------|----------|
| Kontrol Şablonları | Muayene kontrol listesi tanımları |
| Muayeneler | Mal kabul ve üretim muayene kayıtları |
| NCR (Uygunsuzluk) | Uygunsuz ürün raporları ve karantina yönetimi |
| CAPA | Düzeltici ve önleyici faaliyet takibi |
| Şikayetler | Müşteri şikayet kayıtları ve çözüm süreci |
| SPC | X-bar/R grafikleri ile istatistiksel proses kontrolü, Cp/Cpk analizi |

---

### Bakım

Preventif ve korektif bakım süreçleri yönetimi.

| Sayfa | Açıklama |
|-------|----------|
| Ekipmanlar | Makine ve ekipman kartları |
| Bakım Planları | Periyodik bakım planları ve takvimi |
| Bakım İş Emirleri | Planlı ve plansız bakım emirleri |
| Duruş Yönetimi | Arıza ve duruş kayıtları, neden analizi |
| Bakım Talepleri | Operatör kökenli arıza bildirimleri |
| Kontrol Listeleri | Bakım kontrol listesi şablonları |
| Raporlar | OEE raporları, ekipman güvenilirlik istatistikleri |

---

### CRM

Satış hunisi ve müşteri ilişkileri yönetimi.

| Sayfa | Açıklama |
|-------|----------|
| Fırsatlar (Kanban) | Görsel satış hunisi panosu |
| Fırsat Formu | Fırsat detayları, teklif bağlantısı ve aktivite geçmişi |
| Adaylar (Lead) | Potansiyel müşteri listesi ve nitelendirme süreci |
| Aktiviteler | Müşteri görüşme, toplantı ve görev takvimleri |

---

### Satış

Teklif'ten Fatura'ya uçtan uca satış yönetimi.

| Sayfa | Açıklama |
|-------|----------|
| Müşteriler | Müşteri kartları, kredi limitleri, iletişim bilgileri |
| Teklifler | Satış teklifi oluşturma, revizyon ve onay |
| Satış Siparişleri | Sipariş yönetimi, sevkiyat planlama |
| İrsaliyeler | Teslimat belgeleri ve stok çıkışı |
| Satış Faturaları | Müşteri faturalandırma ve muhasebe entegrasyonu |
| Fiyat Listeleri | Müşteri/kanal bazlı özel fiyatlandırma |
| Sözleşmeler | Müşteri ve tedarikçi sözleşmeleri, vade ve yenileme takibi |
| İadeler (RMA) | Satış ve satın alma iade yönetimi |

---

### Sevkiyat & Lojistik

Araç, sürücü ve rota bazlı nakliye yönetimi.

| Sayfa | Açıklama |
|-------|----------|
| Sevkiyatlar | Sevkiyat emirleri, yükleme listesi ve teslimat takibi |
| Araç Yönetimi | Filo tanımları, araç bakım ve sigorta takibi |
| Sürücü Yönetimi | Sürücü profilleri, ehliyet ve belge takibi |
| Rota Planlama | Harita tabanlı rota optimizasyonu |
| Rota Zaman Çizelgesi | Sürücü ve araç bazlı günlük çizelge |
| Sevkiyat Havuzu | Bekleyen siparişleri sevkiyata atama |
| Depo Kiosk | Depo çalışanları için basit sevkiyat onay ekranı |

---

### e-Dönüşüm

GİB entegrasyonlu elektronik belge yönetimi.

| Sayfa | Açıklama |
|-------|----------|
| e-Fatura Listesi | Gönderilen ve alınan e-Faturaların yönetimi |
| Belge Önizleme | UBL 2.1 XML görüntüleyici ve indirme |

---

### Muhasebe

Genel muhasebe ve bütçe yönetimi.

| Sayfa | Açıklama |
|-------|----------|
| Hesap Planı | Tekdüzen hesap planı ağaç yapısı |
| Yevmiye Fişleri | Manuel ve otomatik yevmiye kayıtları |
| Bütçe Planlaması | Dönemsel bütçe girişi ve revizyon |
| Bütçe Raporları | Gerçekleşme vs. bütçe varyans analizi |
| Muhasebe Raporları | Mizan, bilanço ve gelir tablosu |

---

### Finans

Nakit akışı ve cari hesap yönetimi.

| Sayfa | Açıklama |
|-------|----------|
| Ödemeler | Tedarikçi ödeme emirleri ve gerçekleşme takibi |
| Tahsilatlar | Müşteri tahsilatları ve makbuz yönetimi |
| Mutabakatlar | Banka ve cari hesap mutabakatları |
| Hesap Ekstreleri | Cari hesap hareketleri ve bakiye sorgulama |

---

### İnsan Kaynakları

İşe alımdan bordro ve performansa kapsamlı İK yönetimi.

| Sayfa | Açıklama |
|-------|----------|
| İK Dashboard | Personel istatistikleri ve öne çıkan metrikler |
| Personel | Çalışan profilleri, belgeler, sözleşme bilgileri |
| Departmanlar | Organizasyonel birim tanımları |
| Pozisyonlar | İş tanımları ve yetkinlik gereksinimleri |
| Org Şeması | İnteraktif organizasyon şeması |
| İzinler | İzin talepleri, onay süreci ve yıllık haklar |
| Vardiya Planlama | Vardiya tanımları ve personel çizelgesi |
| Devam/Devamsızlık | Giriş-çıkış takibi ve rapor |
| İşe Alım | İş ilanları, aday havuzu ve işe alım süreci |
| Mülakatlar | Mülakat takvimi ve değerlendirme formları |
| Performans Yönetimi | Dönemsel değerlendirmeler, yetkinlik ve hedef skorlama |
| Eğitimler | Eğitim planları ve sertifika takibi |

---

### Proje Yönetimi

Dahili proje ve görev takip sistemi.

| Sayfa | Açıklama |
|-------|----------|
| Proje Listesi | Aktif ve tamamlanmış projeler |
| Kanban Panosu | Sürükle-bırak görev yönetimi |
| Gantt Şeması | Zaman çizelgesi ve bağımlılık görünümü |

---

### Raporlar

Tüm modüllere ait analitik raporlar.

| Rapor | Açıklama |
|-------|----------|
| OEE İzleme | Ekipman verimliliği ve duruş nedenleri |
| Üretim OEE | Üretim bazlı verimlilik analizi |
| Üretim Raporları | İş emri tamamlanma ve performans istatistikleri |
| Satış Raporları | Müşteri, ürün ve kanal bazlı satış analizi |
| Stok Yaşlandırma | Ürün bazlı stok yaş dağılımı |
| Alacak Yaşlandırma | Vadesi geçmiş alacak takibi |
| Tedarikçi Performansı | Teslimat, kalite ve fiyat skoru karşılaştırması |
| Maliyet Analizi | Ürün ve departman bazlı maliyet dağılımı |
| Planlama Varyansı | MPS/MRP plan-gerçekleşme karşılaştırması |

---

## Sistem & Geliştirici Modülleri (Sidebar Dışı)

### Dahili Mesajlaşma

Status bar'daki 💬 butonundan açılan popup tabanlı tam özellikli mesajlaşma sistemi.

| Özellik | Detay |
|---------|-------|
| Direkt Mesaj | Kullanıcılar arası birebir mesajlaşma |
| Grup Konuşmaları | Başlık ve özel üye listeleriyle grup sohbetleri |
| Departman Kanalları | Her departman için otomatik kanal oluşturma |
| Kayıt Bazlı Konuşmalar | Sipariş, iş emri gibi ERP kayıtlarına bağlı konuşma |
| Sistem Bildirimleri | Kritik olaylar için otomatik sistem mesajları |
| Bildirim Merkezi | Öncelik bazlı (low/normal/high/urgent) bildirim listesi |
| Okunmamış Sayacı | Status bar badge, 10 saniyede bir güncelleme |
| Yanıtlama (Reply) | Alıntılı mesaj yanıtlama |
| Mesaj Sabitleme | Önemli mesajları konuşmada sabitleme |
| Yıldızlama | Mesajları daha sonra erişim için yıldızlama |
| Düzenleme & Silme | Gönderilen mesajları düzenleme veya silme |
| Dosya Eki Altyapısı | `MessageAttachment` modeli hazır (UI entegrasyonu yol haritasında) |

### İzlenebilirlik (Traceability)

Lot ve seri numarası bazlı uçtan uca soyağacı — hammaddeden müşteriye tüm dönüşüm adımları.

### İş Akışı (Workflow)

Onay süreçleri ve görev atamaları için yapılandırılabilir iş akışı motoru.

### Bildirimler (Notifications)

Uygulama genelinde olaya dayalı bildirim altyapısı; mesajlaşma modülüyle entegre çalışır.

### Kimlik Doğrulama & Yetkilendirme

Rol ve izin tabanlı erişim kontrolü; her modül için granüler izin tanımları.

### Sabit Varlık Yönetimi (Fixed Assets)

| Sayfa | Açıklama |
|-------|----------|
| Varlık Listesi | Demirbaş ve sabit varlık kayıtları |
| Varlık Formu | Alım, amortisman ve hurda bilgileri |

### İş Akışı (Workflow)

| Sayfa | Açıklama |
|-------|----------|
| İş Akışı Listesi | Tanımlı onay süreçleri |
| İş Akışı Formu | Adım, koşul ve atama yapılandırması |

---

## Geliştirici & Sistem Altyapısı

### Hata Yönetimi & Geliştirme Paneli

`modules/development/` — Uygulama genelinde hata yakalama ve geliştirici araçları.

| Bileşen | Açıklama |
|---------|----------|
| **Hata Log Görüntüleyici** | Şiddet (INFO/WARNING/ERROR/CRITICAL) filtreli hata listesi, stack trace görünümü |
| **Hata Detay Diyalogu** | Hata tipi, modül, ekran, fonksiyon bilgisi ve tam traceback |
| **Ayarlar Sayfası** | Şirket ve sistem parametreleri |
| **Şirket Kartı** | Şirket profili, logo ve iletişim bilgileri |
| **Trace Viewer** | Audit log izleri; kayıt, kullanıcı ve zaman bazlı filtreleme |

```python
# Uygulama genelinde kullanım
from modules.development.error_handler import handle_error
handle_error(e, module="inventory", screen="StockList")
```

### Audit Engine (All-Seeing Eye)

`database/audit_engine.py` — Veritabanı seviyesinde otomatik değişiklik kaydı.

- Her `INSERT`, `UPDATE`, `DELETE` için kim/ne zaman/ne değişti bilgisi JSON olarak loglanır
- `BaseModel`'dan türeyen tüm tablolar otomatik olarak denetim kapsamındadır
- Trace Viewer'dan kullanıcı arayüzü üzerinden sorgulanabilir

### Etiket Tasarımcısı (Label Designer)

`modules/system/views/label_designer/` — Ürün ve palet etiketleri için WYSIWYG tasarım aracı.

| Bileşen | Açıklama |
|---------|----------|
| **Visual Editor** | Sürükle-bırak etiket tasarım kanvası |
| **Canvas** | Boyut, yön ve kenar boşluğu yapılandırması |
| **Items** | Metin, barkod, QR kod, şekil ve resim elemanları |
| **Renderers** | ZPL (Zebra), PDF ve PNG çıktı üretimi |
| **Şablonlar** | Önceden tanımlı etiket şablonları |
| **Cetvel** | Piksel/mm/inç hassasiyetinde konumlandırma |
| **Birim Dönüştürücü** | mm ↔ px ↔ inç çevrim hesaplamaları |

### Kullanıcı & İzin Yönetimi

`modules/system/views/user_management.py` — Sistem yöneticisi için kullanıcı ve rol paneli.

- Kullanıcı oluşturma, aktif/pasif yönetimi, şifre sıfırlama
- Rol tabanlı erişim: `permission_map.py`'de tanımlı modül bazlı izin matrisi
- Granüler izin kodları (ör: `messaging.create_group`, `quality.delete_ncr`)

### Dış API Entegrasyonları

`core/external_apis/` — Hazır entegrasyon adaptörleri.

| API | Açıklama |
|-----|----------|
| **TCMB (Merkez Bankası)** | Günlük döviz kurları otomatik çekme |
| **Hava Durumu** | Operasyonel planlama için hava durumu verisi |
| **E-Belge (GİB)** | UBL 2.1 E-Fatura, E-Arşiv, E-İrsaliye üretimi |

### Raporlama Altyapısı

`core/reporting/` — Tüm modüllere ortak rapor üretim servisi.

- `report_service.py`: PDF, Excel ve HTML çıktı desteği
- `templates/`: Jinja2 tabanlı rapor şablonları
- Stok, satış, alacak yaşlandırma, OEE ve planlama varyansı raporları hazır

### Veri Dışa Aktarma

`core/export_manager.py` — Tablo verilerini tek satırda dışa aktarma.

- Excel (`.xlsx`), CSV ve PDF formatlarında export
- Filtrelenmiş/seçili satırları dışa aktarma desteği

### Thread Yönetimi

`core/threads/worker_manager.py` — Arka plan iş kuyruğu yönetimi.

- `QRunnable` + `QThreadPool` tabanlı, UI'yi bloklamayan iş akışı
- Tüm ağır sorgu ve API çağrıları bu altyapı üzerinden çalışır

### Oturum & Bağlam Yönetimi

| Bileşen | Açıklama |
|---------|----------|
| `core/auth_service.py` | Oturum açma, doğrulama ve mevcut kullanıcı bilgisi |
| `core/user_context.py` | Uygulama genelinde aktif kullanıcı context'i |
| `core/company_context.py` | Çok şirket desteği için aktif şirket context'i |
| `core/session_manager.py` | Veritabanı session havuzu ve lifecycle yönetimi |

---

## Test Altyapısı

```
tests/
├── unit/               # Birim testler (BOM, kapasite, MRP, planlama)
├── integration/        # Entegrasyon testleri (MRP, stok, iş emri)
├── e2e/               # Uçtan uca senaryo testleri (üretim, sevkiyat)
├── factories/         # Test veri fabrikaları
├── fixtures/          # Paylaşılan fixture'lar
└── scripts/           # Doğrulama ve seed scriptleri
```

| Test Kategorisi | Kapsam |
|-----------------|--------|
| **Unit** | BOM yönetimi, kapasite planlama, MRP hesaplamaları, üretim KPI'ları |
| **Integration** | MRP akışı, stok işlemleri, iş emri yaşam döngüsü |
| **E2E** | Üretim senaryosu, sevkiyat akışı, gerçek hayat ERP testi |
| **Verify Scripts** | APS, e-Fatura, sözleşme, işe alım, proje, iade modülü doğrulama |
| **Seed Scripts** | Gerçekçi müşteri, tedarikçi, çalışan ve depo test verisi üretimi |

```bash
# Testleri çalıştır
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Belirli modül doğrulama
python tests/scripts/verify_aps.py
python tests/scripts/verify_recruitment.py
```

---

## Teknik Mimari

```
akilli-is/
├── core/               # API entegrasyonları, AuthService, thread yönetimi
├── config/             # Stil sabitleri, ikon tanımları, menü yapısı
├── database/
│   ├── base.py         # BaseModel (AuditEngine dahil), Session yönetimi
│   └── models/         # SQLAlchemy ORM modelleri (40+ tablo)
├── modules/            # İş modülleri
│   ├── <modul>/
│   │   ├── views/      # PyQt6 widget'ları (UI katmanı)
│   │   └── services.py # İş mantığı ve veritabanı işlemleri
├── ui/
│   ├── main_window.py  # Ana pencere ve status bar
│   └── components/     # Paylaşılan UI bileşenleri
├── alembic/            # Veritabanı migration'ları
└── tests/              # Unit, integration ve doğrulama testleri
```

### Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Dil | Python 3.12+ |
| UI | PyQt6 6.4+ |
| Veritabanı | PostgreSQL 13+ |
| ORM | SQLAlchemy 2.0 |
| Migration | Alembic |
| İkonlar | QtAwesome (Phosphor Icons) |
| Arka Plan İşlemleri | QRunnable + QThreadPool |

### Önemli Tasarım Kararları

- **Service Pattern:** Her modül `MessagingService(session)` gibi instance-based service sınıfına sahiptir.
- **Thread Safety:** Tüm veritabanı sorguları `QRunnable` + `QThreadPool` ile UI thread'i bloklamadan çalışır.
- **Denormalize Alanlar:** Sorgu performansı için `unread_count`, `last_message_at` gibi alanlar gerçek zamanlı güncellenir.
- **Polimorfik İlişkiler:** Çapraz modül bağlantıları için `entity_type + entity_id` deseni kullanılır (Traceability, Messaging).
- **Audit Trail:** `BaseModel` seviyesinde tüm INSERT/UPDATE/DELETE işlemleri otomatik loglanır.

---

## Kurulum

### Gereksinimler

- Python 3.12+
- PostgreSQL 13+
- PyQt6

### Hızlı Başlangıç

```bash
# 1. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 2. Veritabanı bağlantısını yapılandırın
cp .env.example .env
# .env dosyasında DATABASE_URL ayarlayın

# 3. Veritabanı şemasını oluşturun
python -m alembic upgrade head

# 4. Yönetici kullanıcısını oluşturun
python scripts/create_admin.py

# 5. Uygulamayı başlatın
python main.py
```

---

## Yol Haritası

- [ ] **B2B / Müşteri Portali:** Müşterilerin siparişlerini takip edebileceği web arayüzü
- [ ] **IoT Gateway:** PLC verilerinin OEE modülüne anlık aktarımı
- [ ] **Mobil Uygulama:** Depo işlemleri için el terminali desteği
- [ ] **BI Dashboard:** Yönetim için gelişmiş iş zekası panoları
- [ ] **Mesajlaşma — Dosya Eki:** Altyapı hazır, UI entegrasyonu planlanıyor
- [ ] **Mesajlaşma — Arama:** Konuşma ve mesaj içi tam metin arama

---

## Son Güncellemeler

### v2.2 — Dahili Mesajlaşma & Lojistik Genişletme

1. **Dahili Mesajlaşma Sistemi (Faz 1-5):** Status bar'dan açılan popup tabanlı tam özellikli mesajlaşma — direkt mesaj, grup, departman kanalı, kayıt bazlı konuşmalar, bildirim merkezi
2. **Kayıt Bazlı Mesajlaşma:** Herhangi bir ERP kaydına (sipariş, iş emri) bağlanabilir `RecordMessagingButton` bileşeni
3. **Sevkiyat Modülü:** Araç, sürücü, rota ve sevkiyat havuzu eklendi

### v2.1 — APS, SPC & HR Suite

1. **APS & SPC:** İleri planlama ve istatistiksel kalite kontrol modülleri
2. **HR Suite:** İşe alım, performans ve eğitim modülleri
3. **Proje Yönetimi:** Kanban/Gantt tabanlı proje takip sistemi
4. **SCM Genişlemesi:** Sözleşme, iade (RMA), RFQ ve tedarikçi değerlendirme
5. **Test Altyapısı:** `tests/scripts` altında modül doğrulama mekanizmaları
