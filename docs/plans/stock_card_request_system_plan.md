# Stok Kartı Talep Sistemi - Planlama ve Analiz Raporu

**Tarih:** 25.01.2026
**Hazırlayan:** Antigravity (AI Assistant)
**Durum:** Taslak (Onay Bekliyor)

## 1. Gereksinim Analizi ve Amaç
Kullanıcı, stok kartı açma yetkisinin sadece belirli "yetkili" kişilerde olmasını talep etmektedir. Diğer kullanıcıların sisteme kontrolsüz stok kartı eklemesini engellemek, ancak operasyonun aksamaması için "Stok Kartı Talebi" oluşturabilmelerini sağlamak hedeflenmektedir.

**Amaçlar:**
*   Stok veri kirliliğini önlemek.
*   Mükerrer stok kartı açılışını engellemek.
*   Stok kodlama standartlarını korumak.
*   Kullanıcılara kontrollü bir veri giriş kanalı sunmak.

## 2. Mevcut Durum Analizi
*   Mevcut sistemde `StockListPage` üzerinde bulunan "Yeni Stok Kartı" butonu, yetki kontrolü olmaksızın (veya genel erişimle) `StockFormPage`'i açmaktadır.
*   `modules/auth/decorators.py` dosyasında `require_permission` gibi yetkilendirme altyapısı mevcuttur ancak UI tarafında buton gizleme/gösterme mantığı tam entegre edilmemiştir.

## 3. Önerilen Çözüm: Stok Talep Sistemi

Sisteme yeni bir "Stok Talebi" (Stock Request) mekanizması eklenecektir.

### A. Veri Modeli (Database)
`database/models/inventory.py` dosyasına (veya yeni bir modüle) `StockRequest` modeli eklenecektir.

**Alanlar:**
*   `id`: Benzersiz kimlik.
*   `requester_id`: Talebi oluşturan kullanıcı (User ID).
*   `request_date`: Talep tarihi.
*   `status`: Durum (`PENDING` (Beklemede), `APPROVED` (Onaylandı), `REJECTED` (Reddedildi)).
*   `proposed_name`: Önerilen Stok Adı.
*   `proposed_code`: Önerilen Stok Kodu (Opsiyonel).
*   `item_type`: Stok Türü (Hammadde, Mamul vb.).
*   `category_id`: Önerilen Kategori.
*   `unit_id`: Önerilen Birim.
*   `reference_stock_id`: Referans alınan mevcut stok kartı (Opsiyonel). Kullanıcı "Buna benzer bir ürün istiyorum" dediğinde kullanılır.
*   `description`: Açıklama / Gerekçe.
*   `created_stock_id`: Onaylandığında oluşan gerçek stok kartının ID'si (Referans).

### B. Yetkilendirme (Permissions)
İki temel yetki tanımlanacaktır:
1.  `inventory.create`: Doğrudan stok kartı oluşturma ve talepleri onaylama yetkisi (Yönetici/Yetkili).
2.  `inventory.request`: Stok kartı talebi oluşturma yetkisi (Standart Kullanıcı).

### C. Arayüz (UI) Değişiklikleri

#### 1. Stok Listesi Sayfası (`StockListPage`)
*   Sayfanın başlığındaki "Yeni Stok Kartı" butonu dinamik hale getirilecek.
*   **Yetkili Kullanıcı:** Butonu olduğu gibi görür (+ Yeni Stok Kartı). Ayrıca "Bekleyen Talepler" adında bir bildirim/buton görebilir.
*   **Standart Kullanıcı:** Buton "Yeni Stok Talebi" olarak değişir ve rengi farklılaşır (Örn: Turuncu). Tıklandığında talep formu açılır.

#### 2. Stok Talep Formu (`StockRequestFormPage`)
*   Yeni bir view sınıfı oluşturulacak.
*   Stok kartı formundan daha sade olacak.
*   **Referans Stok Seçimi:** Kullanıcı, mevcut stok listesinden benzer bir ürünü (Örn: "40 cm Masura") seçebilecek. Bu seçildiğinde formdaki bazı alanlar (Kategori, Tür, Birim) otomatik dolacak.
*   Zorunlu alanlar: Stok Adı, Stok Türü, Açıklama.

#### 3. Talep Yönetim Listesi (`StockRequestListPage`)
*   Sadece yetkili kullanıcıların erişebileceği bir liste.
*   Bekleyen talepleri listeler.
*   **İşlemler:**
    *   **Onayla:** Talebi onaylar ve `StockFormPage`'i açar. Talepteki veriler forma otomatik doldurulur. Yetkili, kodu ve diğer detayları düzenleyip kaydettiğinde talep durumu `APPROVED` olur ve stok kartı oluşur.
    *   **Reddet:** Bir reddetme sebebi girilerek talep `REJECTED` durumuna çekilir.

## 4. Uygulama Adımları

**Faz 1: Altyapı**
1.  [ ] `StockRequest` modelinin veritabanına eklenmesi (`database/models/inventory.py`).
2.  [ ] Veritabanı migrasyonunun yapılması (veya `init_db` güncellemesi).

**Faz 2: Arayüz (Formlar)**
3.  [ ] `StockRequestFormPage` (Talep oluşturma formu) tasarımının yapılması.
4.  [ ] `StockRequestListPage` (Talep listesi - Yönetici paneli) tasarımının yapılması.

**Faz 3: Entegrasyon**
5.  [ ] `InventoryModule` içinde yetki kontrol mantığının kurulması.
6.  [ ] `StockListPage` içindeki "Yeni Ekle" butonunun kullanıcı yetkisine göre davranış değiştirmesi.
7.  [ ] Stok kartı oluştuğunda talebin durumunun güncellenmesi.

## 5. İş Akışı Özeti

1.  Standart kullanıcı "Stoklar" sayfasına girer.
2.  "Yeni Stok Talebi" butonuna basar.
3.  **Opsiyonel:** "Referans Ürün" seçerek (Örn: 40 cm Masura) formun ön dolumunu sağlar.
4.  Adı "50 cm Masura" olarak değiştirir ve gerekçesini girip kaydeder.
5.  Yetkili kullanıcı sisteme girer, "Stok Talepleri" menüsünü görür.
6.  Talebi inceler. Referans ürün varsa, sistem yeni stok kartını o ürünün özelliklerini (Fiyat, KDV, Tedarikçi vb.) kopyalayarak hazırlar.
7.  Yetkili sadece değişmesi gereken kısımları düzenler ve "Oluştur" der.
8.  Sistem stok kartını oluşturur ve talebi "Onaylandı" olarak işaretler.

---
**Onayınız durumunda bu planı uygulamaya başlayacağım.**
