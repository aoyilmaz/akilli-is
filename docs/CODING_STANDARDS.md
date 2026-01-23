# Kodlama ve Geliştirme Standartları

Bu doküman, Akıllı İş ERP projesinde uyulması gereken kodlama standartlarını, isimlendirme kurallarını ve mimari prensipleri belirler.

## 1. Dil ve İletişim

*   **İletişim Dili:** Proje ekibi (AI ve geliştirici) arasındaki tüm iletişim **Türkçe** olmalıdır.
*   **Kod Yorumları (Comments):** Tüm açıklama satırları Türkçe olmalıdır.
*   **Docstrings:** Sınıf ve fonksiyon açıklamaları Türkçe olmalıdır.
*   **Commit Mesajları:** Türkçe, emir kipinde ve açıklayıcı olmalıdır (Örn: "Stok modülü hata düzeltmeleri yapıldı").
*   **Değişken/Fonksiyon İsimleri:** İngilizce (Örn: `calculate_tax`, `get_user_by_id`). İş mantığı terimleri İngilizce karşılıklarıyla kullanılmalıdır.

## 2. Format ve Stil

*   **Python:** PEP 8 standartlarına uyulmalıdır.
    *   Girinti: 4 boşluk (space).
    *   Satır uzunluğu: 100-120 karakter (esnek).
*   **SQL:** Anahtar kelimeler BÜYÜK HARF (SELECT, FROM), tablo ve kolon isimleri snake_case (user_accounts).

## 3. Mimari Prensipler

### 3.1. Modüler Yapı
Proje modüler bir yapıdadır (`modules/` klasörü). Her modül kendi içinde `views`, `services`, `models` (genellikle `database/models` altında toplanmış olsa da mantıksal ayrım korunmalı) yapılarına sahip olmalıdır.

### 3.2. Servis Katmanı (Service Layer)
İş mantığı (Business Logic) asla doğrudan UI sınıfları içinde yazılmamalıdır.
*   **Doğru:** `ui` -> `service` -> `db`
*   **Yanlış:** `ui` -> `db`

### 3.3. UI Mimarisi (PyQt6)
*   Yeni oluşturulan pencereler, `modules/system/views/base_window.py` (veya raporda belirtilen `BaseWindow`, proje içinde mevcutsa) sınıfından türetilmelidir.
*   UI elemanları isimlendirilirken tür öneki kullanılmalıdır:
    *   `btn_save` (QPushButton)
    *   `lbl_status` (QLabel)
    *   `txt_name` (QLineEdit)
    *   `cmb_type` (QComboBox)
    *   `tbl_data` (QTableWidget)

## 4. Veritabanı Yönetimi

*   **ORM:** SQLAlchemy kullanılmaktadır.
*   **Migrasyon:** Veritabanı şema değişiklikleri **mutlaka** Alembic migrasyon dosyası ile yapılmalıdır. `alembic revision --autogenerate -m "mesaj"` komutu kullanılabilir ancak her zaman oluşturulan dosya kontrol edilmelidir.

## 5. Bölgesel Ayarlar

*   **Para Birimi:** TRY (Türk Lirası).
*   **Tarih Formatı:** GG.AA.YYYY (DD.MM.YYYY).
*   **Ondalık Ayracı:**
    *   UI Gösterimi: Virgül (`,`) -> Örn: 1.250,50
    *   Kod/Veritabanı: Nokta (`.`) -> Örn: 1250.50

## 6. Hata Yönetimi

*   Kullanıcıya gösterilen hatalar anlaşılır bir Türkçe ile ifade edilmelidir.
*   Teknik hatalar loglanmalı, kullanıcıya "Bir hata oluştu" şeklinde genel bir bilgi verilmelidir.
