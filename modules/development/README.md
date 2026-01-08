# Geliştirme Modülü - Hata Yönetimi

Merkezi hata yönetimi ve loglama sistemi.

## Özellikler

- ✅ Detaylı hata kaydı (traceback, dosya, satır numarası, kullanıcı)
- ✅ Rich ile renkli terminal çıktısı
- ✅ Database'e otomatik kayıt
- ✅ PyQt6 QMessageBox entegrasyonu
- ✅ Hata kayıtlarını görüntüleme UI'ı
- ✅ Filtreleme (modül, severity, çözüm durumu)
- ✅ İstatistikler

## Kullanım

### 1. Basit Kullanım

```python
from modules.development import ErrorHandler

try:
    # Riskli kod
    result = some_operation()
except Exception as e:
    ErrorHandler.handle_error(
        e,
        module='inventory',
        screen='WarehouseModule',
        function='_save_warehouse',
        parent_widget=self  # QMessageBox için
    )
```

### 2. Severity Seviyeleri

```python
# Critical hata (kırmızı)
ErrorHandler.handle_error(
    e, 'inventory', 'WarehouseModule', 'critical_function',
    severity='critical'
)

# Warning (sarı)
ErrorHandler.handle_error(
    e, 'inventory', 'WarehouseModule', 'check_stock',
    severity='warning'
)

# Info (mavi)
ErrorHandler.handle_error(
    e, 'inventory', 'WarehouseModule', 'log_action',
    severity='info'
)
```

### 3. QMessageBox Olmadan

```python
ErrorHandler.handle_error(
    e, 'inventory', 'WarehouseModule', '_internal_method',
    show_message=False  # Sadece log, popup yok
)
```

### 4. Kısayol Fonksiyon

```python
from modules.development.error_handler import log_error

try:
    ...
except Exception as e:
    log_error(e, 'production', 'WorkOrderModule', '_complete_order')
```

## Terminal Çıktısı

ErrorHandler hataları renkli ve detaylı şekilde terminale yazar:

```
╭─ 🔴 ERROR: IntegrityError ──────────────────────────╮
│ Module: inventory                                   │
│ Screen: WarehouseModule                             │
│ Function: _save_warehouse                           │
│ Time: 2026-01-08 14:23:45                          │
│ User: admin (ID: 1)                                 │
│                                                     │
│ Error Message:                                      │
│ duplicate key value violates unique constraint     │
╰─────────────────────────────────────────────────────╯

Full Traceback:
  /modules/inventory/views/warehouse_module.py:156 in _save_warehouse
    self.service.create(**data)
  ...
```

## Database Kaydı

Her hata `error_logs` tablosuna kaydedilir:

- Kullanıcı bilgisi (user_id, username, ip_address)
- Hata detayı (type, message, traceback, args)
- Konum (module, screen, function, file, line)
- Sistem bilgisi (Python version, OS)
- Severity (critical, error, warning, info)
- Çözüm takibi (is_resolved, resolved_at, resolution_notes)

## UI Kullanımı

1. Ana menüden **"Geliştirme"** modülüne girin
2. **"Hata Kayıtları"** ekranını açın
3. Filtreleme yapın:
   - Modül (inventory, production, purchasing)
   - Severity (critical, error, warning, info)
   - Sadece çözülmemiş hatalar
4. Bir hatayı çift tıklayarak detayını görün
5. **"Çözüme İşaretle"** butonu ile hatayı çözüldü olarak işaretleyin

## Migration

Database migration'ı çalıştırın:

```bash
# Terminal'de
python3 -m alembic upgrade head

# Veya uygulama içinde migrations otomatik çalışır
```

## Mevcut Kodları Güncelleme

Eski hata yönetimi kodlarını değiştirin:

### Önce

```python
try:
    self.service.save(data)
except Exception as e:
    QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")
    import traceback
    traceback.print_exc()
```

### Sonra

```python
try:
    self.service.save(data)
except Exception as e:
    ErrorHandler.handle_error(
        e, 'inventory', 'WarehouseModule', '_save_warehouse',
        parent_widget=self
    )
```

## İstatistikler

ErrorLogService üzerinden istatistikler alın:

```python
from modules.development import ErrorLogService

service = ErrorLogService()
stats = service.get_statistics(module='inventory', days=7)

print(f"Son 7 gün:")
print(f"  Toplam: {stats['total']}")
print(f"  Çözülmemiş: {stats['unresolved']}")
print(f"  Critical: {stats['by_severity']['critical']}")
print(f"  Modüller: {stats['by_module']}")
```

## Notlar

- ErrorHandler kullanıcı bilgisini otomatik alır (login'den sonra `ErrorHandler.set_current_user(user)` çağrılmalı)
- Şu an main_window.py'de mock user kullanılıyor
- Database hatası durumunda sadece console'a yazar, uygulama çökmez
- QMessageBox hatası durumunda sadece console'a yazar
