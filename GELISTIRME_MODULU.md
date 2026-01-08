# Geliştirme Modülü - Kurulum ve Kullanım

## ✅ Tamamlandı

Geliştirme modülü başarıyla oluşturuldu ve test edildi!

## 🚀 Uygulamayı Çalıştırma

**ÖNEMLİ:** Uygulamayı çalıştırmadan önce virtual environment'ı aktif edin:

```bash
# Virtual environment'ı aktif et
source venv/bin/activate

# Uygulamayı başlat
python main.py
```

**NOT:** `python3 main.py` ile doğrudan çalıştırırsanız sistem Python'u kullanılır ve gerekli modüller (PyQt6, Rich, vs) bulunamaz. Mutlaka `venv` kullanın!

## 📋 Özellikler

### 1. Merkezi Hata Yönetimi
- Tüm exception'ları yakalar ve loglar
- Database'e otomatik kayıt
- Renkli terminal çıktısı (Rich ile)
- QMessageBox entegrasyonu
- User tracking (hangi kullanıcı hangi hatayı aldı)

### 2. Detaylı Hata Kaydı
Her hata için kaydedilen bilgiler:
- **Kullanıcı:** user_id, username
- **Hata:** type, message, traceback, args
- **Konum:** module, screen, function, file_path, line_number
- **Sistem:** Python version, OS info
- **Severity:** critical, error, warning, info
- **Çözüm:** is_resolved, resolved_at, resolved_by, notes

### 3. UI Modülü
- Hata listesi (tablo görünümü)
- Filtreleme:
  - Modül bazında (inventory, production, purchasing)
  - Severity bazında (critical, error, warning, info)
  - Çözüm durumu (sadece çözülmemiş)
- Detay görüntüleme (çift tıklama)
- Çözüme işaretleme
- İstatistikler (son 7 gün)

## 📖 Kullanım Örnekleri

### Basit Kullanım

```python
from modules.development import ErrorHandler

try:
    # Riskli kod
    self.service.save(data)
except Exception as e:
    ErrorHandler.handle_error(
        e,
        module='inventory',
        screen='WarehouseModule',
        function='_save_warehouse',
        parent_widget=self  # QMessageBox için
    )
```

### Severity Seviyeleri

```python
# Critical (🔴 kırmızı)
ErrorHandler.handle_error(
    e, 'inventory', 'DBConnection', 'connect',
    severity='critical'
)

# Warning (🟡 sarı)
ErrorHandler.handle_error(
    e, 'inventory', 'StockCheck', 'check_level',
    severity='warning'
)

# Info (🔵 mavi)
ErrorHandler.handle_error(
    e, 'system', 'Login', 'login',
    severity='info'
)
```

### QMessageBox Olmadan

```python
ErrorHandler.handle_error(
    e, 'background', 'Scheduler', 'run_task',
    show_message=False  # Sadece log, popup yok
)
```

## 🎨 Terminal Çıktısı

### Rich Varsa (venv ile)
```
╭────── 🔴 CRITICAL: ValueError ──────╮
│ Module: inventory                   │
│ Screen: WarehouseModule             │
│ Function: connect_database          │
│ Time: 2026-01-08 02:02:20           │
│ User: admin (ID: 1)                 │
│                                     │
│ Error Message:                      │
│ Critical database connection error! │
╰─────────────────────────────────────╯

Full Traceback:
  [Syntax highlighted traceback...]
```

### Rich Yoksa (fallback)
```
============================================================
🔴 CRITICAL: ValueError
============================================================
Module: inventory
Screen: WarehouseModule
Function: connect_database
Time: 2026-01-08 02:02:20
User: admin (ID: 1)

Error Message:
  Critical database connection error!

Full Traceback:
  [Plain text traceback...]
============================================================
```

## 🧪 Test

Test hatalarını oluşturmak için:

```bash
source venv/bin/activate
python test_error_handler.py
```

Bu script 6 farklı test hatası oluşturur:
- 1x Critical (inventory)
- 3x Error (inventory, production, purchasing)
- 1x Warning (inventory)
- 1x Info (system)

## 📊 UI Kullanımı

1. Uygulamayı başlatın
2. Sol menüden **"🐛 Geliştirme"** butonuna tıklayın
3. **"Hata Kayıtları"** ekranını açın
4. Filtreleme yapın (modül, severity, çözüm durumu)
5. Bir hataya **çift tıklayarak** detayını görün
6. **"✅ Çözüme İşaretle"** butonu ile hatayı çözüldü olarak işaretleyin

## 📁 Dosya Yapısı

```
modules/development/
├── __init__.py              # Module exports
├── services.py              # ErrorLogService (CRUD)
├── error_handler.py         # Merkezi ErrorHandler
├── views/
│   ├── __init__.py
│   └── module.py           # DevelopmentModule UI
└── README.md               # Detaylı dokümantasyon

database/models/development.py   # ErrorLog model
alembic/versions/20260108_002_add_error_log_table.py  # Migration
test_error_handler.py       # Test script
```

## 🔧 Teknik Detaylar

### Database
- **Tablo:** `error_logs`
- **Enum:** `errorseverity` (critical, error, warning, info)
- **İndeksler:** severity, module, resolved, date, user

### Bağımlılıklar
- **Zorunlu:** SQLAlchemy, PyQt6, psycopg2
- **İsteğe bağlı:** rich (yoksa plain text fallback)

### Virtual Environment
```bash
# Kurulum (ilk kez)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Kullanım (her seferinde)
source venv/bin/activate
python main.py
```

## ✨ Özellikler

- ✅ Rich ile renkli terminal (varsa)
- ✅ Plain text fallback (Rich yoksa)
- ✅ Database kayıtları çalışıyor
- ✅ UI modülü hazır
- ✅ Filtreleme ve arama
- ✅ Detay görüntüleme
- ✅ Çözüm takibi
- ✅ İstatistikler
- ✅ User tracking

## 🐛 Sorun Giderme

### "No module named 'PyQt6'"
- Virtual environment kullanmıyorsunuz
- Çözüm: `source venv/bin/activate` çalıştırın

### "No module named 'rich'"
- Sistem Python kullanıyorsunuz
- Rich isteğe bağlı, uygulama çalışır (plain text ile)
- İdeal: venv kullanın

### Database hatası
- Migration çalıştırıldı mı?
- Çözüm: `source venv/bin/activate && alembic upgrade head`

## 📝 Notlar

- ErrorHandler kullanıcı bilgisini otomatik alır (login'den sonra `ErrorHandler.set_current_user(user)`)
- Şu an main_window.py'de mock admin user kullanılıyor
- Database hatası durumunda sadece console'a yazar, uygulama çökmez
- QMessageBox hatası durumunda sadece console'a yazar

---

**Hazırlayan:** Claude Sonnet 4.5
**Tarih:** 2026-01-08
**Versiyon:** 1.0.0
