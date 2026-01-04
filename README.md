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

### Üretim ✅

- Ürün Reçeteleri
- İş Emirleri
- Üretim Planlama
- İş İstasyonları
- Çalışma Takvimi


### Satınalma ✅

- Tedarikçiler
- Talepler
- Siparişler
- Mal Kabul

### Planlanan Modüller 🚧

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

├── alembic
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       └── 20260101_001_add_actual_fields.py
├── alembic.ini
├── config
│   ├── __init__.py
│   ├── settings.py
│   └── themes.py
├── data
├── database
│   ├── __init__.py
│   ├── base.py
│   └── models
│       ├── __init__.py
│       ├── calendar.py
│       ├── common.py
│       ├── inventory.py
│       ├── production.py
│       ├── purchasing.py
│       └── user.py
├── docs
│   └── akilli-is-erp-dokumantasyon.docx
├── init_db.py
├── logs
│   ├── akilli_is_2025-12-31_14-30-47_011255.log
│   ├── akilli_is_2025-12-31_14-33-55_403321.log
│   └── akilli_is_2025-12-31_14-43-35_235183.log
├── main.py
├── modules
│   ├── __init__.py
│   ├── inventory
│   │   ├── __init__.py
│   │   ├── module.py
│   │   ├── services.py
│   │   └── views
│   │       ├── __init__.py
│   │       ├── category_form.py
│   │       ├── category_list.py
│   │       ├── category_module.py
│   │       ├── movement_form.py
│   │       ├── movement_list.py
│   │       ├── movement_module.py
│   │       ├── reports_module.py
│   │       ├── reports_page.py
│   │       ├── stock_count_form.py
│   │       ├── stock_count_list.py
│   │       ├── stock_count_module.py
│   │       ├── stock_form.py
│   │       ├── stock_list.py
│   │       ├── unit_management.py
│   │       ├── unit_module.py
│   │       ├── warehouse_form.py
│   │       ├── warehouse_list.py
│   │       └── warehouse_module.py
│   ├── production
│   │   ├── __init__.py
│   │   ├── calendar_services.py
│   │   ├── services.py
│   │   └── views
│   │       ├── __init__.py
│   │       ├── bom_form.py
│   │       ├── bom_list.py
│   │       ├── bom_module.py
│   │       ├── calendar_module.py
│   │       ├── planning_module.py
│   │       ├── planning_module_backup.py
│   │       ├── planning_page.py
│   │       ├── planning_page_backup.py
│   │       ├── work_order_form.py
│   │       ├── work_order_list.py
│   │       ├── work_order_module.py
│   │       ├── work_station_form.py
│   │       ├── work_station_list.py
│   │       └── work_station_module.py
│   └── purchasing
│       ├── __init__.py
│       ├── services.py
│       └── views
│           ├── __init__.py
│           ├── goods_receipt_form.py
│           ├── goods_receipt_list.py
│           ├── goods_receipt_module.py
│           ├── purchase_order_form.py
│           ├── purchase_order_list.py
│           ├── purchase_order_module.py
│           ├── purchase_request_form.py
│           ├── purchase_request_list.py
│           ├── purchase_request_module.py
│           ├── supplier_form.py
│           ├── supplier_list.py
│           └── supplier_module.py
├── requirements.txt
├── scripts
│   └── daily-commit.sh
├── setup.sh
├── ui
│   ├── __init__.py
│   ├── main_window.py
│   ├── pages
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   └── placeholder.py
│   ├── resources
│   │   └── icons
│   │       └── logo.svg
│   ├── themes
│   │   └── dark.qss
│   └── widgets
│       ├── __init__.py
│       ├── header.py
│       └── sidebar.py
└── {assets,config,core
    └── {auth,base},database
        └── {models,repositories,migrations},modules
            └── {inventory,production,purchasing,sales,finance,hr},ui
                └── {widgets,dialogs,themes,resources},reports
                    └── {designer,templates},ai,exports,utils,tests
                        └── {unit,integration}}
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

**Ahmet Okan YILMAZ** - [GitHub](https://github.com/aoyilmaz)

---
