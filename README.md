# Akıllı İş ERP

<p align="center">
  <img src="assets/favicon.svg" width="120" alt="Akıllı İş Logo">
</p>

<p align="center">
  <strong>Küçük ve Orta Ölçekli İşletmeler için Modern ERP Sistemi</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PyQt6-6.0+-green.svg" alt="PyQt6">
  <img src="https://img.shields.io/badge/PostgreSQL-13+-orange.svg" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

---

## 🚀 Özellikler

- ✅ **Modern Arayüz** - Dark theme, kullanıcı dostu tasarım
- ✅ **Modüler Yapı** - Esnek ve genişletilebilir mimari
- ✅ **Türkçe** - Tam Türkçe dil desteği
- ✅ **PostgreSQL** - Güçlü ve güvenilir veritabanı

## 📦 Mevcut Modüller

### Stok Yönetimi ✅

- Stok Kartları (liste, form, CRUD)
- Kategoriler (hiyerarşik yapı)
- Birimler (dönüşüm desteği)
- Depolar (lokasyon yönetimi)
- Stok Hareketleri (giriş/çıkış/transfer)
- Stok Sayımı (envanter)
- Stok Raporları

### Planlanan Modüller 🚧

- Üretim (İş emirleri, BOM)
- Satın Alma
- Satış
- Finans
- CRM
- İK

## 🛠 Kurulum

### Gereksinimler

- Python 3.9+
- PostgreSQL 13+
- PyQt6

### Adımlar

```bash
# 1. Repoyu klonla
git clone https://github.com/kullanici/akilli-is.git
cd akilli-is

# 2. Virtual environment oluştur
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Bağımlılıkları yükle
pip install -r requirements.txt

# 4. Veritabanını oluştur
createdb akilli_is

# 5. .env dosyasını düzenle
cp .env.example .env
# DATABASE_URL'i güncelle

# 6. Tabloları oluştur
python init_db.py

# 7. Uygulamayı başlat
python main.py
```

## 📁 Proje Yapısı

```
akilli-is/
├── assets/              # Logo, ikonlar
├── config/              # Ayar dosyaları
├── database/            # Veritabanı modelleri
│   ├── models/
│   └── base.py
├── docs/                # Dokümantasyon
├── modules/             # Uygulama modülleri
│   └── inventory/       # Stok modülü
│       ├── services.py
│       └── views/
├── ui/                  # Arayüz bileşenleri
│   ├── pages/
│   └── widgets/
├── main.py              # Ana giriş noktası
├── init_db.py           # Veritabanı başlatma
└── requirements.txt
```

## 📖 Dokümantasyon

Detaylı dokümantasyon için `docs/` klasörüne bakın:

- [Teknik Dokümantasyon](docs/akilli-is-erp-dokumantasyon.docx)

## 📸 Ekran Görüntüleri

_Yakında eklenecek_

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Commit edin (`git commit -m 'Yeni özellik eklendi'`)
4. Push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request açın

## 📄 Lisans

MIT License - Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 👨‍💻 Geliştirici

**Okan** - [GitHub](https://github.com/kullanici)

---
