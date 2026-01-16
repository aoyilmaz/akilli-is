# Akıllı İş ERP - Geliştirme Kuralları

## Teknoloji Yığını
- **Dil:** Python 3.10+
- **UI:** PyQt5 (Modern, flat tasarım)
- **Veritabanı:** PostgreSQL + SQLAlchemy (ORM)
- **Migrasyon:** Alembic

## Mimari Kurallar
1. **Modüler Yapı:** Her özellik `modules/` altında kendi klasöründe olmalı (örn: `modules/sales`).
2. **Katmanlar:** - `views/`: Sadece UI kodları (PyQt widget'ları). İş mantığı barındırmaz.
   - `services.py`: Veritabanı işlemleri ve iş mantığı buradadır.
   - `models/`: Veritabanı tabloları `database/models/` altındadır.
3. **UI Standartları:**
   - `ActionButtons` bileşenini kullan.
   - Renkleri `config/styles.py` dosyasından çek, hardcode yapma.

## Kodlama Tarzı
- Type hinting kullan.
- Hata yönetimi için `modules/development/error_handler.py` kullan.