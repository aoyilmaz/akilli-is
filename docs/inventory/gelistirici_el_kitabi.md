# Akıllı İş - Stok Modülü Geliştirici El Kitabı

---

## 1. Giriş

Bu döküman, **modules/inventory** modülünün teknik mimarisini, veritabanı yapısını, servis mantığını ve UI entegrasyonunu ayrıntılı olarak açıklar. Yeni geliştiricilerin modülü anlaması ve genişletmesi için referans niteliğindedir.

### Dosya Yapısı
```
modules/inventory/
├── __init__.py          # Modül exports
├── module.py            # Ana InventoryModule widget
├── services/
│   ├── __init__.py
│   ├── base.py          # Core servisler (Item, Movement, Warehouse...)
│   ├── location_service.py
│   └── sscc_service.py
└── views/
    ├── __init__.py
    ├── stock_list.py     # Liste sayfası
    ├── stock_form.py     # Form sayfası
    ├── movement_*.py     # Hareket modülü
    ├── warehouse_*.py    # Depo modülü
    └── ...
```

---

## 2. Veritabanı Modelleri

Tüm modeller `database/models/inventory.py` içinde tanımlanmıştır ve `BaseModel` sınıfından türetilmiştir.

### 2.1. Entity-Relationship Diyagramı (Metin)

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    Unit     │←─────→│    Item     │←─────→│ ItemCategory│
│  (Birimler) │  1:N  │(Stok Kartı) │  N:1  │ (Kategori)  │
└─────────────┘       └──────┬──────┘       └─────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │ 1:N              │ 1:N              │ 1:N
          ▼                  ▼                  ▼
┌─────────────┐       ┌─────────────┐    ┌─────────────┐
│ ItemBarcode │       │StockBalance │    │StockMovement│
│  (Barkodlar)│       │  (Bakiye)   │    │ (Hareket)   │
└─────────────┘       └──────┬──────┘    └──────┬──────┘
                             │                  │
                             │ N:1              │ N:1
                             ▼                  ▼
                      ┌─────────────┐    ┌─────────────┐
                      │  Warehouse  │←──→│  Warehouse  │
                      │   (Depo)    │    │  Location   │
                      └─────────────┘    └─────────────┘
```

---

### 2.2. Tablolar ve Alanlar

#### `items` (Stok Kartları)
Ana ürün/malzeme tanım tablosu. **60+ alan** içerir.

| Alan | Tip | Açıklama |
|------|-----|----------|
| `code` | String(50), UNIQUE | Stok kodu (Örn: STK000001) |
| `name` | String(300) | Ürün adı |
| `item_type` | Enum(ItemType) | Tür: `hammadde`, `mamul`, `yari_mamul`, `ambalaj`, `sarf`, `ticari`, `hizmet`, `diger` |
| `unit_id` | FK → units | Temel ölçü birimi |
| `category_id` | FK → item_categories | Kategori |
| `barcode` | String(100), INDEX | Ana barkod |
| `purchase_price` | Numeric(18,4) | Alış fiyatı |
| `sale_price` | Numeric(18,4) | Satış fiyatı |
| `min_stock` | Numeric(18,4) | Minimum stok seviyesi |
| `reorder_point` | Numeric(18,4) | Yeniden sipariş noktası |
| `track_lot` | Boolean | Lot takibi açık mı? |
| `track_serial` | Boolean | Seri numarası takibi |
| `track_expiry` | Boolean | Son kullanma tarihi takibi |

**Hesaplanan Özellikler (Properties):**
```python
@property
def total_stock(self) -> Decimal:
    """Tüm depolardaki toplam stok"""
    return sum((b.quantity for b in self.stock_balances))

@property
def stock_status(self) -> str:
    """Stok durumu: 'normal', 'low', 'critical', 'out_of_stock'"""
```

---

#### `stock_balances` (Stok Bakiyeleri)
Anlık stok durumunu tutan özet tablo. **Her item + warehouse + (opsiyonel) location** kombinasyonu için bir kayıt.

| Alan | Tip | Açıklama |
|------|-----|----------|
| `item_id` | FK → items | Stok kartı |
| `warehouse_id` | FK → warehouses | Depo |
| `location_id` | FK → warehouse_locations | Lokasyon (opsiyonel) |
| `quantity` | Numeric(18,4) | Mevcut miktar |
| `reserved_quantity` | Numeric(18,4) | Rezerve miktar |
| `unit_cost` | Numeric(18,4) | Birim maliyet (ağırlıklı ortalama) |
| `secondary_quantity` | Numeric(18,4) | İkincil birim miktarı (Dual-Unit) |
| `secondary_unit_id` | FK → units | İkincil birim |
| `lot_number` | String(100) | Lot numarası |
| `expiry_date` | DateTime | Son kullanma tarihi |

**Önemli:** Bu tablo doğrudan GÜNCELLENMEZ. Yalnızca `StockMovementService.create_movement()` üzerinden transaction içinde güncellenir.

---

#### `stock_movements` (Stok Hareketleri)
Tüm giriş/çıkış kayıtlarının tutulduğu **immutable** log tablosu.

| Alan | Tip | Açıklama |
|------|-----|----------|
| `movement_type` | Enum(StockMovementType) | Hareket türü |
| `movement_date` | DateTime | Hareket tarihi |
| `item_id` | FK → items | Stok kartı |
| `from_warehouse_id` | FK → warehouses | Kaynak depo (çıkışlarda) |
| `to_warehouse_id` | FK → warehouses | Hedef depo (girişlerde) |
| `quantity` | Numeric(18,4) | Miktar (her zaman pozitif) |
| `unit_price` | Numeric(18,4) | Birim fiyat/maliyet |
| `document_no` | String(50) | Belge numarası |
| `lot_number` | String(100) | Lot numarası |

**Hareket Türleri (`StockMovementType` Enum):**
```python
class StockMovementType(enum.Enum):
    # GİRİŞLER (to_warehouse zorunlu)
    GIRIS = "giris"
    SATIN_ALMA = "satin_alma"
    URETIM_GIRIS = "uretim_giris"
    SAYIM_FAZLA = "sayim_fazla"
    IADE_ALIS = "iade_alis"
    
    # ÇIKIŞLAR (from_warehouse zorunlu)
    CIKIS = "cikis"
    SATIS = "satis"
    URETIM_CIKIS = "uretim_cikis"
    SAYIM_EKSIK = "sayim_eksik"
    FIRE = "fire"
    IADE_SATIS = "iade_satis"
    
    # TRANSFER (her iki depo da zorunlu)
    TRANSFER = "transfer"
```

---

#### `warehouses` (Depolar)
| Alan | Tip | Açıklama |
|------|-----|----------|
| `code` | String(50), UNIQUE | Depo kodu |
| `name` | String(200) | Depo adı |
| `warehouse_type` | String(50) | Tür: `general`, `raw`, `finished`, `cold`, `bonded` |
| `is_default` | Boolean | Varsayılan depo mu? (Sistem genelinde tek olabilir) |
| `allow_negative` | Boolean | Eksi stoğa izin verilsin mi? |

---

#### `warehouse_locations` (Lokasyonlar)
| Alan | Tip | Açıklama |
|------|-----|----------|
| `warehouse_id` | FK → warehouses | Üst depo |
| `code` | String(50) | Lokasyon kodu (Örn: A-01-03) |
| `aisle`, `rack`, `shelf`, `bin` | String | Koridor/Raf/Kat/Hücre |
| `barcode` | String(50), UNIQUE | Lokasyon barkodu (LOC-XXXXXX) |
| `location_type` | Enum(LocationType) | `normal`, `quarantine`, `scrap`, `transit` |

---

## 3. Servis Katmanı

Tüm iş mantığı `modules/inventory/services/base.py` içindedir.

### 3.1. ServiceBase Sınıfı
```python
class ServiceBase:
    def __init__(self):
        self.session: Session = get_session()
    
    def close(self):
        if self.session:
            self.session.close()
    
    # Context manager desteği
    def __enter__(self): return self
    def __exit__(self, ...): self.close()
```

**Kullanım:**
```python
with ItemService() as service:
    items = service.get_all()
```

---

### 3.2. StockMovementService (KRİTİK)
Modülün kalbidir. Stok hareketlerini yönetir ve bakiyeleri günceller.

#### `create_movement()` Metodu
```python
def create_movement(
    self,
    item_id: int,
    movement_type: StockMovementType,
    quantity: Decimal,
    from_warehouse_id: int = None,
    to_warehouse_id: int = None,
    unit_price: Decimal = None,
    document_no: str = None,
    lot_number: str = None,
    secondary_quantity: Decimal = None,  # Dual-Unit
    secondary_unit_id: int = None,
) -> StockMovement:
```

**İş Mantığı:**

1. **Validasyon:**
   - `quantity > 0` kontrolü
   - Giriş işlemlerinde `to_warehouse_id` zorunlu
   - Çıkış işlemlerinde `from_warehouse_id` zorunlu
   - Transfer işlemlerinde her ikisi de zorunlu

2. **Negatif Stok Kontrolü:**
   - Çıkış ve transfer işlemlerinde `get_available_quantity()` ile mevcut stok kontrol edilir
   - Depo ayarında `allow_negative=True` değilse ve stok yetersizse `NegativeStockError` fırlatılır

3. **Maliyet Belirleme:**
   - **Giriş:** `unit_price` parametresi kullanılır
   - **Çıkış:** `get_current_cost()` ile mevcut stok maliyeti alınır (ağırlıklı ortalama)
   - **Transfer:** Kaynak depodaki maliyet aktarılır

4. **Transaction Yönetimi:**
   - Hareket kaydı ve bakiye güncellemesi **ATOMİK** yapılır
   - Hata durumunda `session.rollback()` ile tüm işlem geri alınır

**Örnek Kullanım:**
```python
from modules.inventory.services import StockMovementService
from database.models import StockMovementType
from decimal import Decimal

service = StockMovementService()

try:
    movement = service.create_movement(
        item_id=1,
        movement_type=StockMovementType.SATIN_ALMA,
        quantity=Decimal("100"),
        to_warehouse_id=2,
        unit_price=Decimal("50.00"),
        document_no="IRS-2026-0001",
        description="Tedarikçi girişi"
    )
    print(f"Hareket #{movement.id} oluşturuldu")
except NegativeStockError as e:
    print(f"Stok yetersiz: {e}")
finally:
    service.close()
```

---

#### `_update_balances()` (Dahili Metot)
Ağırlıklı ortalama maliyet hesaplamasını yapar:

```python
if new_quantity > 0:
    old_value = old_quantity * old_cost
    new_value = quantity * unit_cost
    to_balance.unit_cost = (old_value + new_value) / new_quantity
```

---

### 3.3. ItemService
| Metot | Açıklama |
|-------|----------|
| `get_all(active_only=True)` | Tüm stok kartlarını listele |
| `get_by_id(item_id)` | ID ile getir |
| `get_by_barcode(barcode)` | Barkod ile getir |
| `check_unique_code(code, exclude_id)` | Kod benzersizlik kontrolü |
| `create(**kwargs)` | Yeni kart oluştur (unique kontrollü) |
| `update(item_id, **kwargs)` | Güncelle |
| `search(keyword, item_type, limit)` | Arama |
| `get_next_code(prefix="STK")` | Otomatik kod üret |

---

### 3.4. Özel Exception Sınıfları
```python
class NegativeStockError(Exception):
    """Stok yetersizliği hatası"""
    def __init__(self, item_code, warehouse_name, available, requested):
        ...

class DuplicateCodeError(Exception):
    """Tekrarlayan kod/barkod hatası"""
    def __init__(self, field, value):
        ...
```

---

## 4. UI Mimarisi (PyQt6)

### 4.1. Signal/Slot Yapısı
Her view kendi sinyallerini tanımlar:

```python
class StockListPage(QWidget):
    # Sinyaller
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)    # item_id
    delete_clicked = pyqtSignal(int)  # item_id
    refresh_requested = pyqtSignal()
```

Ana modül (`InventoryModule`) bu sinyalleri yakalar:
```python
self.list_page.add_clicked.connect(self.show_add_form)
self.list_page.edit_clicked.connect(self.show_edit_form)
```

---

### 4.2. Servis Yaşam Döngüsü (Lazy Loading)
```python
class InventoryModule(QWidget):
    def _get_services(self):
        """Servisleri al (lazy loading)"""
        if self.item_service is None:
            self.item_service = ItemService()
    
    def _close_services(self):
        """Servisleri kapat"""
        if self.item_service:
            self.item_service.close()
            self.item_service = None
    
    def load_data(self):
        try:
            self._get_services()
            items = self.item_service.get_all()
            self.list_page.load_data(items)
        finally:
            self._close_services()  # Her zaman kapat!
```

---

### 4.3. Stacked Widget Pattern
Liste ve form sayfaları arasında geçiş için `QStackedWidget` kullanılır:

```python
self.stack = QStackedWidget()
self.stack.addWidget(self.list_page)    # index 0
# Form dinamik olarak eklenir/kaldırılır  # index 1

def show_list(self):
    self.stack.setCurrentIndex(0)
```

---

## 5. Best Practices

### Transaction Yönetimi
```python
try:
    # İş mantığı
    self.session.commit()
except Exception as e:
    self.session.rollback()
    raise e
```

### Decimal Kullanımı
Parasal ve miktar değerleri için **asla float kullanmayın**:
```python
from decimal import Decimal
quantity = Decimal("100.50")  # Doğru
quantity = 100.50              # YANLIŞ
```

### Unique Kontrolleri
Kayıt öncesi mutlaka kontrol edin:
```python
if not self.check_unique_code(code, exclude_id=item_id):
    raise DuplicateCodeError("Stok Kodu", code)
```

---

## 6. Modülü Genişletme

Yeni bir alt modül eklemek için:

1. **View Oluştur:** `views/new_feature.py`
2. **Export Et:** `views/__init__.py` ve `__init__.py`'e ekle
3. **Route Ekle:** `ui/main_window.py` içinde `MENU_DATA` ve page routing
4. **Servis Yazın:** İş mantığını `services/` altına ekleyin

---

## 7. Testler

Stok hareketi akışını test eden script:
```bash
python scripts/test_stock_flow.py
```

---

## 8. Sık Yapılan Hatalar

| Hata | Açıklama | Çözüm |
|------|----------|-------|
| `session.close()` unutuldu | Memory leak ve bağlantı tükenmesi | `try-finally` veya `with` kullan |
| `float` kullanımı | Parasal hesaplamalarda hata | `Decimal` kullan |
| Unique kontrolü yapılmadı | `IntegrityError` | `check_unique_*` metodlarını çağır |
| Bakiye direkt güncellendi | Tutarsızlık | Yalnızca `create_movement()` kullan |
