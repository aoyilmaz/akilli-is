# Akıllı İş ERP

<p align="center">
  <img src="ui/resources/icons/logo.svg" width="120" alt="Akıllı İş Logo">
</p>

<p align="center">
  <strong>Küçük ve Orta Ölçekli İşletmeler için Modern ERP Sistemi</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PyQt6-6.10+-green.svg" alt="PyQt6">
  <img src="https://img.shields.io/badge/PostgreSQL-13+-orange.svg" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

---

## Özellikler

- **Modern Arayüz** - Light/Dark tema desteği, Premium görsel tasarım, PyQt6 tabanlı dinamik arayüz
- **Multi-Company (Çoklu Firma)** - Aynı sistem üzerinde birden fazla firmayı yönetebilme, firma bazlı izole veri yapısı
- **Merkezi Firma Context** - Tüm modüllerde aktif firma ayarlarının (KDV, numara önekleri, para birimi) otomatik yönetimi
- **Modüler Mimari** - 15+ entegre iş modülü, mikro-servis yaklaşımıyla genişletilebilir yapı
- **Gelişmiş Doküman Yönetimi** - Kurumsal kimlik belgeleri (Logo, Kaşe, İmza) ve dinamik belge şablonları (Antetli, Fatura, İrsaliye)
- **Merkezi Hata Yönetimi** - Veritabanı tabanlı loglama ve UI üzerinden hata takip/çözüm ekranı
- **Rol Bazlı Yetkilendirme (RBAC)** - Gelişmiş kullanıcı, rol ve detaylı izin yönetimi
- **Görsel Tasarımcılar** - WYSIWYG etiket editörü ve dinamik rapor tasarım desteği

---

## Modüller

### Sistem ve Geliştirme (System & Development)

- **Firma Kartı (Multi-Company):** Çoklu firma yönetimi, adres, banka ve iletişim bilgileri
- **Kurumsal Kimlik:** Logo, kaşe ve imza yönetimi, PDF şablon entegrasyonu
- **Kullanıcı Yönetimi:** Rol tanımları, detaylı yetki matrisi (Permissions Map)
- **Etiket Şablonları:** Sürükle-bırak görsel etiket tasarımcısı
- **Log İzleme:** Sistem hatalarının detaylı traceback ile takibi ve çözümlenmesi

### İnsan Kaynakları (HR)

- **Personel Yönetimi:** Fotoğraflı çalışan kartları, özlük ve iletişim bilgileri
- **Kimlik Kartı Sistemi:** QR kodlu, fotoğraflı ve kurumsal logolu personel kimlik basımı
- **Vardiya ve Organizasyon:** Departman hiyerarşisi, ekip bazlı vardiya rotasyonu
- **İzin ve Devam:** Giriş/çıkış takibi (PDKS) ve onaylı izin süreci

### Satış Yönetimi (Sales)

- **Otomatik Numaralandırma:** Firma ayarlarına bağlı otomatik Fatura/İrsaliye/Sipariş numarası üretimi
- **İşlem Akışı:** Teklif → Sipariş → İrsaliye → Fatura zinciri ile tam izlenebilirlik
- **Fiyatlandırma:** Müşteri bazlı özel fiyat listeleri ve indirim tanımları
- **Cari Yönetimi:** Müşteri risk limiti ve bakiye kontrolü

### Üretim Yönetimi (Production)

- **Reçete (BOM):** Versiyonlu reçeteler, üretim operasyonları ve süre tanımları
- **Operatör Paneli:** Tablet uyumlu basitleştirilmiş üretim takip ekranı
- **İş Emirleri:** Malzeme rezervasyonlu ve kapasite planlamalı iş emri yönetimi
- **Gantt Planlama:** Makine ve personel bazlı sürükle-bırak zaman planlama

### Stok ve Depo (Inventory)

- **Çoklu Depo:** Lokasyon bazlı stok takibi, depolar arası transfer
- **Lot/Seri Takibi:** Üretim ve mal kabulde lot/seri izlenebilirliği
- **Sayım Yönetimi:** Periyodik ve anlık stok sayım mutabakatı
- **Maliyet:** Ağırlıklı Ortalama (Moving Average) ile anlık stok maliyet hesabı

### Finans ve Muhasebe (Finance & Accounting)

- **Cari Hesaplar:** Borç/Alacak takibi, hesap ekstreleri
- **Muhasebe:** Tekdüzen hesap planı, otomatik yevmiye fişi üretimi
- **Tahsilat/Ödeme:** Banka ve kasa entegrasyonlu nakit akışı yönetimi

---

## Kurulum

### Gereksinimler

- Python 3.10+
- PostgreSQL 13+ (veya SQLite3)
- PyQt6

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

# 4. Veritabanını yapılandırın
cp .env.example .env
# .env içindeki DATABASE_URL'i güncelleyin

# 5. Migration ve Başlangıç Verileri
python -m alembic upgrade head
python init_db.py  # Varsayılan: admin / admin123

# 6. Uygulamayı başlatın
python main.py
```

---

## Proje Yapısı

```
akilli-is/
├── core/                   # Çekirdek servisler (Auth, Context, Logging)
│   ├── company_context.py  # Global firma yönetimi
│   └── report_service.py   # PDF/HTML rapor motoru
├── database/               # Veritabanı katmanı
│   └── models/             # ORM (Company, Sales, HR, vb.)
├── modules/                # İş modülleri (Service & View)
│   ├── system/             # CompanyService, UserService
│   ├── sales/              # Satış ve fatura işlemleri
│   └── hr/                 # Personel ve vardiya işlemleri
├── ui/                     # UI bileşenleri (Main Window, Sidebar)
└── assets/                 # Statik dosyalar (Logo, Belgeler)
```

---

## Lisans

MIT License - Detaylar için [LICENSE](LICENSE) dosyasına bakın.
