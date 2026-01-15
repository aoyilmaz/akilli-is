# Akıllı İş ERP

<p align="center">
  <img src="ui/resources/icons/logo.svg" width="120" alt="Akıllı İş Logo">
</p>

<p align="center">
  <strong>Küçük ve Orta Ölçekli İşletmeler için Modern ERP Sistemi</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PyQt5-5.15+-green.svg" alt="PyQt5">
  <img src="https://img.shields.io/badge/PostgreSQL-13+-orange.svg" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

---

## Özellikler

- **Modern Arayüz** - Light/Dark tema desteği, kullanıcı dostu PyQt5 arayüzü
- **Modüler Mimari** - 15+ iş modülü, genişletilebilir yapı
- **Merkezi Hata Yönetimi** - Veritabanı tabanlı loglama ve UI üzerinden hata takibi
- **Türkçe** - Tam Türkçe dil desteği
- **ORM Altyapısı** - SQLAlchemy ile güvenli veritabanı işlemleri
- **Rol Bazlı Yetkilendirme (RBAC)** - Gelişmiş kullanıcı ve yetki yönetimi
- **Etiket Tasarımcısı** - WYSIWYG görsel etiket editörü

---

## Modüller

### Kullanıcı ve Yetki Yönetimi (System)

- **Kullanıcı Yönetimi:** Kullanıcı ekleme, düzenleme, pasife alma
- **Rol Yönetimi:** Detaylı rol ve izin tanımları
- **Güvenlik:** Bcrypt şifreleme ve güvenli oturum yönetimi
- **Etiket Şablonları:** Görsel etiket tasarımcısı

### Üretim Yönetimi (Production)

- **Reçete (BOM) Yönetimi:** Versiyonlama, revizyon takibi, alt reçete desteği
- **İş Emirleri:** Stok entegrasyonlu iş emri takibi, malzeme rezervasyonu
- **İş İstasyonları:** Makine ve tezgah yönetimi
- **Planlama:** Makine bazlı Gantt şeması, kapasite doluluk takibi
- **Operatör Paneli:** Üretim sahası için basitleştirilmiş arayüz
- **Takvim & Vardiya:** Vardiya tanımları, tatil günleri ve net çalışma saati hesaplama

### Satınalma (Purchasing)

- **Tedarikçi Yönetimi:** Cari kartlar, iletişim bilgileri
- **Talep Yönetimi:** Departman bazlı satınalma talepleri ve onay mekanizması
- **Sipariş Yönetimi:** Tekliften siparişe dönüşüm, parçalı teslimat desteği
- **Mal Kabul:** İrsaliye ile depoya giriş, kalite kontrol
- **Satınalma Faturaları:** Fatura kaydı ve eşleştirme

### Stok Yönetimi (Inventory)

- **Stok Kartları:** Barkod, birim çevrimleri, kritik stok seviyeleri
- **Hareketler:** Giriş, Çıkış, Transfer, Fire, Sayım Fazlası/Eksiği
- **Depo Yönetimi:** Çoklu depo ve lokasyon takibi
- **Maliyetlendirme:** Ağırlıklı Ortalama Maliyet (Moving Average) yöntemi
- **Stok Sayımı:** Periyodik sayım ve mutabakat

### Satış Yönetimi (Sales)

- **Müşteri Yönetimi:** Cari kartlar, fiyat listeleri, iletişim bilgileri
- **Teklifler:** Satış teklifi oluşturma, siparişe dönüştürme
- **Siparişler:** Sipariş takibi, irsaliyeye dönüştürme
- **İrsaliyeler:** Teslimat irsaliyesi, faturaya dönüştürme
- **Faturalar:** Satış faturası, ödeme takibi
- **Fiyat Listeleri:** Müşteri bazlı fiyatlandırma

### Finans (Finance)

- **Cari Hesap Ekstresi:** Müşteri/tedarikçi hesap hareketleri
- **Tahsilat:** Müşterilerden tahsilat, fatura eşleştirme
- **Ödeme:** Tedarikçilere ödeme kayıtları
- **Mutabakat:** Cari hesap mutabakatı

### Muhasebe (Accounting)

- **Hesap Planı:** Tekdüzen hesap planı yapısı
- **Muhasebe Fişleri:** Yevmiye kayıtları
- **Raporlar:** Mizan, defteri kebir

### İnsan Kaynakları (HR)

- **Personel Yönetimi:** Çalışan kartları, özlük bilgileri
- **Organizasyon:** Departman ve pozisyon yapısı
- **İzin Yönetimi:** İzin talepleri ve onay süreci
- **Vardiya Rotasyonu:** Ekip bazlı vardiya planlama
- **Devam Takibi:** Giriş/çıkış kayıtları

### Kalite Yönetimi (Quality)

- **Kalite Kontrol:** Giriş ve üretim kalite kontrolleri
- **Uygunsuzluk (NCR):** Uygunsuzluk raporları
- **Düzeltici/Önleyici Faaliyet (CAPA):** İyileştirme takibi
- **Müşteri Şikayetleri:** Şikayet yönetimi
- **Denetim Şablonları:** Özelleştirilebilir kontrol listeleri

### Malzeme İhtiyaç Planlaması (MRP)

- **MRP Çalıştırma:** Otomatik ihtiyaç hesaplama
- **İhtiyaç Analizi:** Satış ve üretim bazlı analiz
- **Tedarik Önerileri:** Satınalma/üretim önerileri
- **BOM Patlatma:** Çok seviyeli reçete açılımı

### Müşteri İlişkileri Yönetimi (CRM)

- **Lead Yönetimi:** Potansiyel müşteri takibi
- **Fırsatlar:** Satış fırsatı pipeline'ı
- **Aktiviteler:** Görüşme ve toplantı kayıtları

### Bakım Yönetimi (Maintenance)

- **Bakım Talepleri:** Arıza ve bakım bildirimleri
- **Bakım Görevleri:** İş atama ve takip
- **Periyodik Bakım:** Planlı bakım takvimleri

### Raporlar (Reports)

- **Satış Raporları:** Satış analizi ve trendler
- **OEE Raporu:** Genel Ekipman Etkinliği
- **Stok Yaşlandırma:** Stok devir analizi
- **Alacak Yaşlandırma:** Vade analizi
- **Tedarikçi Performansı:** Tedarikçi değerlendirme

### Geliştirme Araçları (Development)

- **Error Handler:** Hataların detaylı traceback ile veritabanına kaydı
- **Log İzleme:** Hata kayıtlarını filtreleme, inceleme ve çözümleme ekranı
- **Migration:** Alembic ile veritabanı şema versiyonlama

---

## Planlanan Özellikler

- E-Fatura / E-Arşiv Entegrasyonu
- Barkod Okuyucu Entegrasyonu
- Mobil Uygulama (Depo operasyonları)

---

## Kurulum

### Gereksinimler

- Python 3.10+
- PostgreSQL 13+
- PyQt5

### Adımlar

```bash
# 1. Repoyu klonlayın
git clone https://github.com/kullanici/akilli-is.git
cd akilli-is

# 2. Virtual environment oluşturun
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. Veritabanını oluşturun (PostgreSQL)
createdb akilli_is

# 5. .env dosyasını ayarlayın
cp .env.example .env
# .env dosyasındaki DATABASE_URL'i kendi ayarlarınıza göre güncelleyin

# 6. Tabloları oluşturun ve Migration'ları çalıştırın
python -m alembic upgrade head

# 7. Başlangıç verilerini yükleyin (admin kullanıcısı dahil)
python init_db.py
# Varsayılan kullanıcı: admin / admin123

# 8. Uygulamayı başlatın
python main.py
```

---

## Proje Yapısı

```
akilli-is/
├── main.py                 # Uygulama giriş noktası
├── init_db.py              # Veritabanı başlatma
├── alembic/                # Veritabanı migrasyonları
├── config/                 # Ayarlar ve tema
│   ├── settings.py
│   ├── styles.py
│   └── theme_manager.py
├── core/                   # Çekirdek servisler
│   ├── auth_service.py
│   ├── permission_map.py
│   ├── export_manager.py
│   └── label_manager.py
├── database/               # Veritabanı katmanı
│   ├── base.py
│   └── models/             # ORM modelleri
├── modules/                # İş modülleri
│   ├── production/
│   ├── sales/
│   ├── purchasing/
│   ├── inventory/
│   ├── hr/
│   ├── quality/
│   ├── finance/
│   ├── accounting/
│   ├── mrp/
│   ├── crm/
│   ├── maintenance/
│   ├── reports/
│   └── system/
└── ui/                     # UI bileşenleri
    ├── main_window.py
    └── widgets/
```

---

## Lisans

MIT License - Detaylar için [LICENSE](LICENSE) dosyasına bakın.
