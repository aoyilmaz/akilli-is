# Akıllı İş - Stok Modülü Geliştirici Dökümanı

Bu döküman, Akıllı İş ERP sisteminin **Stok (Inventory)** modülünün teknik detaylarını, veritabanı yapısını, mimarisini ve ilişkilerini açıklar.

## 1. Genel Bakış
Stok modülü, firmanın malzeme, hammadde, yarı mamul ve mamul stoklarının takibini, depo yönetimini ve stok hareketlerinin kaydını sağlar. Modül `modules/inventory` dizini altında yer alır ve veritabanı modelleri `database/models/inventory.py` dosyasında tanımlanmıştır.

## 2. Veritabanı Şeması ve Modeller

### 2.1. Temel Tablolar
Aşağıdaki diyagram tablolar arası ilişkileri özetler:
`Items (1)` <-> `(N) StockMovements (N)` <-> `(1) Warehouses`
`Items (1)` <-> `(N) StockBalances (N)` <-> `(1) Warehouses`

#### `items` (Stok Kartları)
*   **Tanım:** Temel stok kartı tanımları.
*   **Önemli Alanlar:**
    *   `code` (String, Unique): Stok kodu. Otomatik üretilebilir (`STK000001`).
    *   `item_type` (Enum): `hammadde`, `mamul`, `ticari`, `hizmet` vb.
    *   `unit_id` (Integer): Temel birim ID (`units` tablosu).
    *   `track_lot` / `track_serial` / `track_expiry` (Boolean): Takip özellikleri.
    *   `valuation_method`: Değerleme yöntemi (Varsayılan: Ağırlıklı Ortalama).

#### `warehouses` (Depolar)
*   **Tanım:** Fiziksel depolama alanları.
*   **Önemli Alanlar:**
    *   `allow_negative` (Boolean): Bu depoda eksiye düşmeye izin verilip verilmeyeceği.
    *   `is_production` (Boolean): Üretim deposu ise `True`.

#### `warehouse_locations` (Depo Lokasyonları)
*   **Tanım:** Depo içi raf/adres sistemi.
*   **Format:** Genellikle `Koridor-Raf-Kat-Hücre` (Örn: `A-01-02-01`).
*   **Alanlar:** `aisle`, `rack`, `shelf`, `bin`. Barkod (`LOC-UUID`) otomatik üretilir.

### 2.2. Hareket ve Bakiye (Core Tables)

#### `stock_movements` (Stok Hareketleri)
Tüm giriş/çıkış tarihçesi buradadır. Değiştirilemez (Immutable) log niteliğindedir.
*   **Hareket Tipleri (`StockMovementType` Enum):**
    *   **Girişler:** `giris`, `satin_alma`, `uretim_giris`, `sayim_fazla`, `iade_alis`.
    *   **Çıkışlar:** `cikis`, `satis`, `uretim_cikis`, `sayim_eksik`, `fire`, `iade_satis`.
    *   **Transfer:** `transfer` (İki depo arası).
*   **Kritik Alanlar:**
    *   `quantity`: Hareket miktarı (Her zaman pozitif).
    *   `unit_price`: O hareketin birim maliyeti.
    *   `secondary_quantity`: İkincil birim takibi (Örn: Koli adedi yanında KG takibi).

#### `stock_balances` (Stok Bakiyeleri)
Anlık durumu tutan özet tablodur.
*   **Primary Key:** `item_id` + `warehouse_id` (+ `location_id` opsiyonel).
*   **Mantık:** `StockMovementService` her hareket kaydında bu tabloyu **Transaction** içinde günceller.
*   **Maliyet:** `unit_cost` alanı Ağırlıklı Ortalama Maliyet (Moving Average) yöntemine göre her girişte güncellenir.

## 3. Servis Katmanı ve İş Mantığı

Servisler `modules/inventory/services/base.py` içinde `ServiceBase` sınıfından türetilmiştir.

### 3.1. `StockMovementService`
Modülün kalbidir. Stok hareketlerini yönetir.

#### `create_movement` Metodu
Stok hareketi oluşturur ve bakiyeyi günceller.
*   **Parametreler:** `item_id`, `type`, `quantity`, `from_warehouse`, `to_warehouse`, `unit_price`, `dual_unit_params`...
*   **Validasyonlar:**
    *   **Negatif Stok Kontrolü:** Eğer depo `allow_negative=False` ise ve çıkış miktarı mevcut stoktan fazlaysa `NegativeStockError` fırlatır.
    *   **Depo Zorunluluğu:** Girişler için `to_warehouse`, çıkışlar için `from_warehouse`, transfer için ikisi de zorunludur.
*   **Maliyet Mantığı:**
    *   **Giriş İşlemleri:** `unit_price` parametresi maliyet olarak alınır. Bakiye tablosunda ağırlıklı ortalama yeniden hesaplanır.
    *   **Çıkış İşlemleri:** Mevcut stoktaki `unit_cost` (ortalama maliyet) kullanılır.
*   **Transaction:** Hareket kaydı ve bakiye güncellemesi **ATOMİK** bir işlemdir. Hata olursa `rollback` yapılır.

```python
# Örnek Kullanım
service.create_movement(
    item_id=1,
    movement_type=StockMovementType.GIRIS,
    quantity=Decimal("100"),
    to_warehouse_id=2,
    unit_price=Decimal("50.00"),  # Birim maliyet
    description="Satın alma girişi"
)
```

### 3.2. `ItemService`
*   **Unique Kontrolleri:** `code` ve `barcode` alanlarının benzersiz olması `check_unique_code` ile sağlanır. Çakışma durumunda `DuplicateCodeError` fırlatılır.
*   **Otomatik Kod:** `get_next_code` metodu son stok kodunu bulup bir artırır (Örn: `STK001` -> `STK002`). *Not: Yüksek concurrency durumları için `SELECT FOR UPDATE` gerekir.*

### 3.3. `LocationService`
*   **Toplu Oluşturma (`create_bulk`):** Belirtilen aralıklar (Koridor A-Z, Raf 1-5) için otomatik lokasyonlar üretir.
*   **Barkod:** Her lokasyon için `LOC-{UUID}` formatında benzersiz barkod üretir.

## 4. Hata Yönetimi
Modülde özelleştirilmiş hata sınıfları kullanılır:
*   `NegativeStockError`: Stok yetersizliğinde fırlatılır. Depo adı, mevcut ve istenen miktarı içerir.
*   `DuplicateCodeError`: Mevcut bir stok kodu veya barkod girildiğinde fırlatılır.

## 5. UI Entegrasyonu
View katmanı (`modules/inventory/views`) servisleri kullanırken şu deseni izler:
1.  Servisi oluştur (`_get_services`).
2.  `try-except` bloğu içinde işlemi yap.
3.  Hata (`NegativeStockError` vb.) yakalanırsa kullanıcıya anlaşılır mesaj göster.
4.  `finally` bloğunda servisi kapat (`_close_services`).

## 6. Geliştirme İpuçları
*   **Dual-Unit (Çift Birim) Takibi:** Et, kumaş, metal gibi sektörlerde hem adet hem ağırlık takibi için `secondary_quantity` ve `secondary_unit_id` alanlarını kullanın.
*   **Maliyet:** Tüm parasal değerler `Decimal` tipindedir. Asla `float` kullanmayın.
*   **Stok Düzeltme:** Bakiyede tutarsızlık şüphesi varsa `rebuild_balance(item_id, warehouse_id)` metodu ile hareketlerden bakiye tekrar hesaplanabilir.
