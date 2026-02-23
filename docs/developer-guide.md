# Akıllı İş ERP — Geliştirici Kılavuzu

> **Versiyon:** 1.0 | **Tarih:** Şubat 2026
> **Hedef Kitle:** Projeye katkı sağlayan geliştiriciler ve AI ajanlar

---

## İçindekiler

1. [Genel Bakış ve Mimari](#1-genel-bakış-ve-mimari)
2. [Uygulama Başlangıcı](#2-uygulama-başlangıcı)
3. [Veritabanı Katmanı](#3-veritabanı-katmanı)
4. [Modül Mimarisi](#4-modül-mimarisi)
5. [UI Bileşenleri](#5-ui-bileşenleri)
6. [Servis Katmanı Rehberi](#6-servis-katmanı-rehberi)
7. [Hata Yönetimi](#7-hata-yönetimi)
8. [Kimlik Doğrulama ve Yetkilendirme](#8-kimlik-doğrulama-ve-yetkilendirme)
9. [Migrasyon Yönetimi](#9-migrasyon-yönetimi)
10. [Test Altyapısı](#10-test-altyapısı)
11. [Core Servisler](#11-core-servisler)
12. [Özel Modüller — Detaylı Akış](#12-özel-modüller--detaylı-akış)

---

## 1. Genel Bakış ve Mimari

### 1.1 Proje Amacı

Akıllı İş, Türk işletmeleri için tasarlanmış, PyQt6 tabanlı masaüstü ERP uygulamasıdır. Stok, satış, satınalma, üretim, kalite, finans, muhasebe, İK ve lojistik gibi temel iş süreçlerini tek bir platformda yönetir. Türkiye'ye özgü gereksinimler (e-fatura/e-arşiv, KDV, PDKS, SGDP) doğrudan desteklenmektedir.

### 1.2 Teknoloji Yığını

| Katman | Teknoloji | Versiyon | Amaç |
|--------|-----------|---------|------|
| UI | PyQt6 | 6.10.1 | Masaüstü arayüz |
| ORM | SQLAlchemy | 2.0.45 | Veritabanı erişimi |
| Veritabanı | PostgreSQL | 14+ | Ana veri deposu |
| Migrasyon | Alembic | 1.17.2 | Şema versiyonlama |
| API | FastAPI + Uvicorn | 0.128 / 0.40 | REST API katmanı |
| PDF | ReportLab + WeasyPrint | 4.4.7 / 67.0 | Rapor/fatura çıktısı |
| Excel | OpenPyXL | 3.1.5 | Excel export |
| Şablonlar | Jinja2 | 3.1.6 | Rapor şablonları |
| Barkod | python-barcode + qrcode | 0.16.1 / 8.2 | Barkod/QR üretimi |
| İkonlar | QtAwesome | 1.4.0 | UI ikon seti |
| HTTP | httpx | 0.28.1 | AI / dış API çağrıları |
| AI | Anthropic Claude | claude-sonnet-4 | AI yardımcı |

### 1.3 Yüksek Seviye Mimari

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                              │
│               ApplicationController                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              ui/main_window.py  (MainWindow)                │
│   ┌──────────────┐         ┌────────────────────────────┐   │
│   │   SideBar    │ ──────► │      QTabWidget            │   │
│   │  (220px)     │         │  ┌──────────────────────┐  │   │
│   │ menu_data.py │         │  │  XxxModule (QWidget) │  │   │
│   └──────────────┘         │  └──────────────────────┘  │   │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              modules/<name>/views/                          │
│   XxxModule → QStackedWidget                                │
│                ├── XxxListPage  (BaseListPage)              │
│                └── XxxFormPage  (QWidget)                   │
└────────────────────────┬────────────────────────────────────┘
                         │  import
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              modules/<name>/services.py                     │
│       CRUD metotları + iş mantığı                           │
└────────────────────────┬────────────────────────────────────┘
                         │  SQLAlchemy
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              database/models/  +  database/base.py          │
│              PostgreSQL (QueuePool)                         │
└─────────────────────────────────────────────────────────────┘
```

### 1.4 Katman Sorumlulukları

| Katman | Konum | Kural |
|--------|-------|-------|
| **views/** | `modules/<name>/views/` | Sadece UI kodu. İş mantığı ve DB çağrısı yasak. |
| **services.py** | `modules/<name>/services.py` | DB işlemleri ve iş mantığı. |
| **models/** | `database/models/` | SQLAlchemy ORM tanımları. Sadece şema. |
| **config/** | `config/` | Sabitler, stiller, tema. Uygulama genelinde ortak. |
| **core/** | `core/` | Cross-cutting: auth, session, export, thread yönetimi. |

### 1.5 Dizin Yapısı

```
akilli-is/
├── main.py                    # Uygulama giriş noktası
├── init_db.py                 # Veritabanı başlatma scripti
├── alembic.ini                # Alembic yapılandırması
├── requirements.txt
│
├── config/                    # Uygulama yapılandırması
│   ├── settings.py            # DB URL, tema, dil, AI yapılandırması
│   ├── styles.py              # Renk/boyut sabitleri (QSS helpers)
│   ├── themes.py              # ThemeManager, DARK_THEME, MATERIAL_OCEAN
│   ├── theme_manager.py       # Runtime tema değiştirme
│   ├── icons.py               # İkon sabitleri (ICONS.ADD, ICONS.EDIT…)
│   ├── menu_data.py           # Sidebar menü yapısı
│   └── payroll_accounts.yaml  # Bordro muhasebe eşleştirmesi
│
├── core/                      # Cross-cutting servisler
│   ├── user_context.py        # get_current_user(), set_current_user()
│   ├── company_context.py     # Çok şirket context'i
│   ├── auth_service.py        # Kimlik doğrulama
│   ├── session_manager.py     # Oturum yönetimi
│   ├── permission_map.py      # Sayfa izin tanımları
│   ├── export_manager.py      # Excel/PDF export
│   ├── label_manager.py       # Barkod/etiket yazdırma
│   ├── threads/               # Arka plan thread yöneticisi
│   ├── api/main_api.py        # FastAPI REST API
│   ├── reporting/             # Rapor servisi
│   └── external_apis/         # Üçüncü taraf API entegrasyonları
│
├── database/
│   ├── base.py                # Engine, get_session(), BaseModel
│   ├── audit_engine.py        # SQLAlchemy audit event listeners
│   ├── seed_auth.py           # Admin kullanıcı seed scripti
│   └── models/                # 37 SQLAlchemy model dosyası
│
├── modules/                   # 33 iş modülü
│   └── <name>/
│       ├── services.py
│       └── views/
│
├── ui/
│   ├── main_window.py         # Ana pencere (1847 satır)
│   ├── widgets/
│   │   ├── sidebar.py         # Navigasyon sidebar'ı
│   │   └── header.py          # Üst başlık çubuğu
│   ├── components/            # Paylaşılan UI bileşenleri
│   └── pages/                 # Dashboard ve özel sayfalar
│
├── alembic/versions/          # 47 migrasyon dosyası
├── tests/                     # Unit, integration, e2e testler
├── utils/                     # barcode_utils.py
└── assets/                    # Görseller ve fontlar
```

---

## 2. Uygulama Başlangıcı

### 2.1 ApplicationController (`main.py`)

```python
# main.py → ApplicationController.__init__()

# 1. Audit event listenerları etkinleştir
audit_engine.init_listeners()

# 2. Dev modunda login ekranını atla, admin kullanıcıyı yükle
self._setup_dev_user_context()   # production'da: _show_login()

# 3. Ana pencereyi aç
self._show_main_window()         # → MainWindow()
```

`_setup_dev_user_context()`: DB'den admin kullanıcıyı çeker, `UserContext`'e atar, `ErrorHandler.set_current_user(user)` çağırır. **Production'da bu bypass kaldırılacak, login ekranı açılacak.**

### 2.2 MainWindow Başlangıç Adımları (`ui/main_window.py`)

```python
# MainWindow.__init__() — 4 adım

def __init__(self):
    self.setup_window()        # Adım 1: pencere boyutu/pozisyonu
    self.setup_pages_dict()    # Adım 2: TÜM modül widget'larını önceden oluştur
    self.setup_ui()            # Adım 3: SideBar + QTabWidget yerleştir
    self.connect_signals()     # Adım 4: sidebar.pageSelected → open_tab()
```

**`setup_pages_dict()`**: Uygulamanın tüm ~70 sayfa widget'ını `self.pages: dict[str, QWidget]` sözlüğüne eager-load eder. Anahtar, `menu_data.py`'deki sayfa kimliğidir (ör. `"customers"`, `"work-orders"`).

### 2.3 Navigasyon Mekanizması

```
Kullanıcı tıklaması
     │
     ▼
SideBar (QTreeWidget)
     │  pageSelected(page_id: str) sinyali
     ▼
MainWindow.open_tab(page_id)
     │  1. İzin kontrolü (permission_map.py)
     │  2. self.pages[page_id] ile widget al
     │  3. QTabWidget'a sekme ekle (max 10)
     ▼
XxxModule.showEvent() → _load_data()
```

**Önemli:** Router nesnesi yoktur. `self.pages` sözlüğü + `QTabWidget` navigasyonun tamamıdır. Bir sayfa zaten açıksa yeniden oluşturulmaz; sadece sekmeye odaklanılır.

### 2.4 Menü Yapısını Genişletme

Yeni bir sayfa eklemek için iki dosya güncellenmeli:

```python
# config/menu_data.py
MENU_DATA = {
    "my_module": {
        "title": "MODÜLÜm",
        "items": [
            ("Öğelerim", "ph.list", "my-items"),  # (görünen ad, ikon, page_id)
        ],
    },
}

# ui/main_window.py → setup_pages_dict()
self.pages["my-items"] = MyItemModule()
```

---

## 3. Veritabanı Katmanı

### 3.1 Engine ve Session (`database/base.py`)

```python
# Singleton engine — uygulama boyunca tek instance
def get_engine():
    _engine = create_engine(
        get_database_url(),
        poolclass=QueuePool,
        pool_size=20,       # Aynı anda maksimum 20 bağlantı
        max_overflow=30,    # +30 geçici bağlantı
        pool_timeout=60,
        pool_recycle=1800,  # 30 dakikada bir bağlantıyı yenile
        pool_pre_ping=True, # Bağlantı sağlığını kontrol et
    )

# Scoped session — thread-safe
def get_session() -> Session:
    _ScopedSession = scoped_session(
        sessionmaker(bind=get_engine(), expire_on_commit=False)
    )
    return _ScopedSession()
```

**`expire_on_commit=False`**: Commit sonrasında nesnelerin attribute'larına erişim için tekrar DB sorgusu yapılmaz. Performans açısından kritik.

### 3.2 BaseModel (`database/base.py:280`)

Tüm tablolar `BaseModel`'den türer:

```python
class BaseModel(Base):
    __abstract__ = True

    id         = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)
    is_active  = Column(Boolean, default=True, nullable=False)

    def to_dict(self) -> dict: ...    # Tüm kolonları dict'e çevirir
    def __repr__(self) -> str: ...    # "<ClassName(id=X)>"
```

**Soft Delete:** `is_active = False` yapılarak kayıt silinmiş sayılır. Gerçek `DELETE` sadece özel durumlarda kullanılır. Servisler genellikle `.filter(Model.is_active == True)` ile filtreler.

### 3.3 Audit Engine (`database/audit_engine.py`)

SQLAlchemy `before_flush` event listener'ları ile INSERT/UPDATE/DELETE olaylarını yakalar. Değişiklikleri `audit_logs` tablosuna yazar:

```
audit_logs: user_id, action, module, table_name, record_id,
            old_values (JSON), new_values (JSON)
```

`main.py`'de `audit_engine.init_listeners()` çağrısı ile aktif edilir.

### 3.4 Model Dosyaları Referans Tablosu

| Dosya | Alan | Temel Tablolar |
|-------|------|---------------|
| `user.py` | Kimlik doğrulama | `users`, `roles`, `permissions`, `audit_logs`, `settings`, `sequences`, `user_sessions`, `user_page_permissions` |
| `common.py` | Ortak varlıklar | `currencies`, `exchange_rates`, `countries`, `cities`, `districts`, `attachments`, `notes`, `notifications`, `label_templates` |
| `inventory.py` | Stok | `items`, `item_categories`, `units`, `unit_conversions`, `item_barcodes`, `warehouses`, `warehouse_locations`, `stock_balances`, `stock_movements`, `stock_requests` |
| `company.py` | Firma | `companies`, `company_addresses`, `company_banks`, `company_contacts`, `company_settings`, `company_documents` |
| `sales.py` | Satış | `customers`, `price_lists`, `price_list_items`, `sales_quotes`, `sales_orders`, `delivery_notes`, `invoices` + satır tabloları |
| `purchasing.py` | Satınalma | `suppliers`, `purchase_requests`, `purchase_orders`, `goods_receipts`, `purchase_invoices`, `vendor_ratings` + satır tabloları |
| `production.py` | Üretim | `bill_of_materials`, `bom_lines`, `bom_operations`, `bom_by_products`, `work_stations`, `work_orders`, `work_order_lines`, `work_order_operations`, `production_plans`, `production_downtimes` |
| `mrp.py` | MRP | `mrp_runs`, `mrp_lines` |
| `accounting.py` | Muhasebe | `accounts`, `fiscal_periods`, `journal_entries`, `journal_entry_lines`, `budgets`, `budget_lines` |
| `finance.py` | Finans | `account_transactions`, `receipts`, `receipt_allocations`, `payments`, `payment_allocations` |
| `hr.py` | İnsan Kaynakları | `departments`, `positions`, `employees`, `leaves`, `attendances`, `payrolls`, `job_postings`, `job_applications`, `interviews` |
| `personnel.py` | Personel ek | `employee_documents`, `leave_entitlement_rules`, `leave_balances` |
| `quality.py` | Kalite | `inspection_templates`, `inspection_criteria`, `inspections`, `inspection_results`, `spc_observations`, `spc_control_limits`, `non_conformances`, `customer_complaints`, `capas`, `audits` |
| `maintenance.py` | Bakım | `equipments`, `maintenance_categories`, `maintenance_requests`, `maintenance_work_orders`, `maintenance_plans`, `maintenance_checklists` |
| `shipping.py` | Sevkiyat | `vehicles`, `drivers`, `shipments`, `shipment_items`, `shipment_loads` |
| `transport_unit.py` | SSCC | `transport_units`, `transport_unit_items` |
| `traceability.py` | İzlenebilirlik | `lots`, `serial_numbers`, `trace_links` |
| `crm.py` | CRM | `leads`, `opportunities`, `activities` |
| `contracts.py` | Sözleşme | `contracts`, `contract_lines` |
| `project.py` | Proje | `projects`, `project_tasks`, `task_dependencies`, `project_resources`, `project_time_entries` |
| `einvoice.py` | E-Fatura | `einvoices`, `einvoice_series`, `einvoice_settings` |
| `fixed_asset.py` | Sabit Kıymet | `fixed_assets`, `depreciation_entries` |
| `returns.py` | İadeler | `return_orders`, `return_order_lines` |
| `rfq.py` | Teklif Talebi | `rfqs`, `rfq_items`, `supplier_offers`, `supplier_offer_items` |
| `messaging.py` | Mesajlaşma | `conversations`, `conversation_participants`, `messages`, `message_attachments`, `message_stars`, `notification_preferences` |
| `aps.py` | İleri Planlama | `aps_scenarios`, `aps_planned_tasks` |
| `calendar.py` | Takvim | `production_shifts`, `production_holidays`, `workstation_schedules` |
| `shift_teams.py` | Vardiya | `shift_teams`, `rotation_patterns`, `rotation_schedules` |
| `route.py` | Rota | `routes`, `route_stops` |
| `dashboard.py` | Dashboard | `dashboard_widgets`, `role_default_layouts`, `user_dashboard_layouts` |
| `dms.py` | Belge Yönetimi | `documents`, `document_relations` |
| `performance.py` | Performans | `evaluation_periods`, `competencies`, `performance_evaluations`, `competency_scores`, `performance_goals` |
| `training.py` | Eğitim | `trainings`, `training_sessions`, `training_participants`, `employee_certificates` |
| `development.py` | Geliştirici | `error_logs`, `trace_sessions`, `trace_events` |

### 3.5 Çapraz Modül Tablo İlişkileri

En sık referans alınan 5 merkezi tablo:

```
items (inventory)
  ← sales_order_items, delivery_note_items, invoice_items
  ← purchase_order_items, goods_receipt_items, purchase_invoice_items
  ← bom_lines, work_order_lines, work_order_by_products
  ← stock_balances, stock_movements
  ← inspection_templates, non_conformances, customer_complaints
  ← lots, serial_numbers
  ← equipment_spare_parts, maintenance_work_order_parts
  ← transport_unit_items, contract_lines, rfq_items

customers (sales)
  ← sales_quotes, sales_orders, delivery_notes, invoices
  ← opportunities (crm), customer_complaints (quality)
  ← receipts, account_transactions
  ← contracts, return_orders, projects

suppliers (purchasing)
  ← purchase_orders, goods_receipts, purchase_invoices
  ← vendor_ratings, equipment (outsourcing FK)
  ← payments, account_transactions
  ← contracts, return_orders

employees (hr)
  ← work_order_operation_personnel (production)
  ← inspections, ncrs, capas, audits (quality)
  ← training_participants, employee_certificates
  ← performance_evaluations, competency_scores
  ← project_tasks, project_resources, time_entries
  ← interviews

users (auth)
  ← stock_movements (created_by, approved_by)
  ← work_orders (created_by, released_by)
  ← journal_entries (created_by, posted_by)
  ← workflow_instances / workflow_actions
  ← maintenance_work_orders, error_logs, trace_sessions
  ← conversations, messages, notification_preferences
  ← audit_logs
```

### 3.6 Temel ER Diyagramı (Satış Döngüsü)

```
leads ──► opportunities ──► sales_quotes ──► sales_orders
                                                   │
                              customers ───────────┘
                                   │
                           delivery_notes ──► shipments
                                   │
                               invoices ──► receipts
                                   │
                          account_transactions
                                   │
                           journal_entries (muhasebe köprüsü)
```

---

## 4. Modül Mimarisi

### 4.1 Standart Modül Yapısı

```
modules/<name>/
├── __init__.py              # Servisleri dışa aktar
├── services.py              # VEYA services/ klasörü (karmaşık modüllerde)
│   └── base.py, xyz_service.py
└── views/
    ├── __init__.py
    ├── <entity>_module.py   # Container widget (MainWindow.pages'e kayıtlı)
    ├── <entity>_list.py     # BaseListPage alt sınıfı
    └── <entity>_form.py     # Form/detay sayfası
```

### 4.2 Modül Kataloğu

| Modül | Alan | Servis Dosyaları |
|-------|------|-----------------|
| `accounting` | Muhasebe | `services.py`, `budget_service.py`, `cost_service.py` |
| `aps` | İleri Planlama | `services.py` |
| `auth` | Kimlik doğrulama | `services.py`, `decorators.py`, `exceptions.py` |
| `contracts` | Sözleşmeler | `services/contract_service.py` |
| `crm` | CRM | `services.py` |
| `dashboard` | Dashboard | `services.py` |
| `development` | Geliştirici araçları | `services.py`, `error_handler.py`, `event_interceptor.py`, `log_tracer.py`, `sql_tracer.py`, `trace_service.py` |
| `einvoice` | E-Fatura | `services/base.py`, `ubl_builder.py`, `integrator/` |
| `finance` | Finans | `services/base.py`, `currency_service.py`, `accounting_bridge.py` |
| `fixed_assets` | Sabit Kıymetler | `services/asset_service.py` |
| `hr` | İnsan Kaynakları | `services/base.py`, `payroll_service.py`, `performance_service.py`, `personnel_service.py`, `recruitment.py`, `training_service.py`, `hr_bridge.py`, `pdks_service.py`, `payroll_accounting_service.py` |
| `inventory` | Stok | `services/base.py`, `location_service.py`, `sscc_service.py`, `stock_quality_bridge.py`, `stock_request_service.py` |
| `maintenance` | Bakım | `services.py` |
| `messaging` | Mesajlaşma | `services.py` |
| `mrp` | MRP | `services.py` |
| `notifications` | Bildirimler | `services.py` |
| `planning` | MPS/Planlama | `services.py` |
| `production` | Üretim | `services/base.py`, `capacity_service.py`, `scheduler_service.py`, `calendar_services.py` |
| `project` | Proje Yönetimi | `services/project_service.py` |
| `purchasing` | Satınalma | `services/` (çok dosya) |
| `quality` | Kalite | `services.py`, `spc_service.py` |
| `reports` | Raporlama | `services.py`, `analytics.py` |
| `returns` | İadeler | `services/base.py`, `purchase_return.py`, `sales_return.py` |
| `rfq` | Teklif Talebi | `services/rfq_service.py` |
| `sales` | Satış | `services/base.py`, `sales_production_bridge.py` |
| `shipping` | Sevkiyat/Filo | `services/base.py`, `accounting.py`, `route.py` |
| `system` | Sistem yönetimi | `services/company_service.py`, `dms_service.py`, `notification_service.py` |
| `traceability` | İzlenebilirlik | `services/lot_service.py`, `serial_service.py`, `trace_engine.py` |
| `workflow` | İş Akışı | `services.py`, `bridge.py` |

### 4.3 Çapraz Modül Bağımlılık Kuralları

**Altın Kural:** Modüller birbirinin `views/` klasörünü import etmez. Yalnızca `services.py` import edilir.

```python
# ✅ DOĞRU — sadece servis import et
from modules.inventory.services import ItemService

# ❌ YANLIŞ — view import etme
from modules.inventory.views.stock_module import StockModule
```

**Circular import önlemek için lazy import kalıbı** (method içinde import):

```python
# modules/production/views/work_order_module.py
def _ensure_service(self):
    if not self.item_service:
        from modules.inventory.services import ItemService  # Lazy!
        self.item_service = ItemService()
```

**Evrensel bağımlılık:** Tüm modüller `ErrorHandler`'ı import eder:

```python
from modules.development import ErrorHandler
```

---

## 5. UI Bileşenleri

### 5.1 Stil Sistemi (`config/styles.py`)

Tüm renkler ve boyutlar bu dosyadan alınır — **hardcode yasak**.

**Renk Sabitleri:**

| Grup | Sabitler | Örnek Değer |
|------|---------|------------|
| Arka plan | `BG_PRIMARY`, `BG_SECONDARY`, `BG_TERTIARY`, `BG_HOVER`, `BG_SELECTED` | `#1e1e1e` |
| Kenarlık | `BORDER`, `BORDER_LIGHT` | `#3e3e42` |
| Metin | `TEXT_PRIMARY`, `TEXT_SECONDARY`, `TEXT_MUTED`, `TEXT_ACCENT` | `#cccccc` |
| Vurgu | `ACCENT`, `ACCENT_SECONDARY` | `#007acc`, `#5e3b8e` |
| Durum | `SUCCESS`, `WARNING`, `ERROR`, `INFO` | `#4ec9b0`, `#f14c4c` |
| Tablo | `TABLE_BG`, `TABLE_HEADER_BG`, `TABLE_SELECTED` | BG_ ile aynı |
| Input | `INPUT_BG`, `INPUT_BORDER`, `INPUT_FOCUS` | `#3c3c3c` |
| Buton | `BTN_PRIMARY_BG/HOVER`, `BTN_DANGER_BG`, `BTN_ADD_BG`, `BTN_REFRESH_BG`, `BTN_PRINT_BG`, `BTN_SEARCH_BG`, `BTN_FILTER_BG`, `BTN_EXPORT_BG` | Semantik renkler |
| Boyut | `BTN_HEIGHT_NORMAL=36`, `BTN_HEIGHT_SMALL=28`, `BTN_MIN_WIDTH=100` | px |

**Buton Stili Almak:**

```python
from config.styles import get_button_style

btn = QPushButton("Kaydet")
btn.setStyleSheet(get_button_style("primary"))
# Seçenekler: "primary", "secondary", "danger", "success",
#             "add", "refresh", "print", "search", "filter"
```

**Tema Değiştirme (`config/themes.py`):**

```python
from config.theme_manager import ThemeManager

# Tema değişikliğinde callback kaydet
ThemeManager.register_callback(self._on_theme_changed)

# Temayı değiştir
ThemeManager.set_theme(ThemeType.DARK)       # VS Code Dark
ThemeManager.set_theme(ThemeType.MATERIAL_OCEAN)
```

### 5.2 BaseListPage (`ui/components/base_list_page.py:20`)

Tüm liste sayfalarının temel sınıfı. `PageHeader + EnhancedTableWidget + TableFooter` üçlüsünü kurar.

**İmza:**

```python
class BaseListPage(QWidget):
    def __init__(
        self,
        title: str,              # Sayfa başlığı
        icon: str,               # qtawesome ikon kodu (ör. ICONS.USERS)
        table_id: str,           # Benzersiz tablo kimliği (kolon ayarları için)
        columns: List[ColumnConfig],
        user_id: Optional[int] = None,
        show_stats: bool = True,    # Footer istatistik kartları
        show_search: bool = True,   # Arama kutusu
        show_refresh: bool = False, # Manuel yenile butonu
        show_add: bool = True,      # "Yeni Ekle" butonu
        show_export: bool = False,  # Export butonu
        add_text: str = "Yeni Ekle",
        search_placeholder: str = "Ara...",
        auto_refresh: bool = True,          # 30 sn'de bir otomatik yenile
        auto_refresh_interval: int = None,  # ms, varsayılan 30000
        count_label_text: str = "kayıt",
    )
```

**Sinyaller:**

```python
refresh_requested = pyqtSignal()     # Yenile isteği
add_clicked       = pyqtSignal()     # "Yeni Ekle" tıklandı
edit_clicked      = pyqtSignal(int)  # Düzenle (kayıt id)
delete_clicked    = pyqtSignal(int)  # Sil (kayıt id)
view_clicked      = pyqtSignal(int)  # Görüntüle (kayıt id)
export_clicked    = pyqtSignal()     # Export
next_page_clicked = pyqtSignal()     # Sonraki sayfa
prev_page_clicked = pyqtSignal()     # Önceki sayfa
page_size_changed = pyqtSignal(int)  # Sayfa boyutu değişti
```

**Kullanım Örneği:**

```python
class CustomerListPage(BaseListPage):
    def __init__(self, parent=None):
        columns = [
            ColumnConfig("code", "Kod", width=100),
            ColumnConfig("name", "Müşteri Adı", width=200, stretch=True),
            ColumnConfig("phone", "Telefon", width=130),
            ColumnConfig("actions", "İşlemler", width=120,
                         resizable=False, movable=False, hideable=False),
        ]
        super().__init__(
            title="Müşteriler",
            icon=ICONS.USERS,
            table_id="customers",
            columns=columns,
        )
        self._setup_stat_cards()

    def _setup_stat_cards(self):
        self.add_stat_card("total",  "Toplam", "0",   "info",    ICONS.USERS)
        self.add_stat_card("active", "Aktif",  "0",   "success", ICONS.CHECK)
        self.add_stat_card("credit", "Limit",  "₺0",  "primary", ICONS.MONEY)

    def load_data(self, customers: list):
        self.clear_table()
        for c in customers:
            self.add_row(c)   # EnhancedTableWidget.add_row()
        self.update_count(len(customers))
```

### 5.3 ColumnConfig (`ui/components/enhanced_table.py:54`)

```python
ColumnConfig(
    key: str,                    # Veri sözlüğündeki anahtar
    title: str,                  # Başlık metni
    width: int = 100,            # Piksel genişlik
    stretch: bool = False,       # Kalan alanı doldur
    visible: bool = True,        # Görünür başlat
    filterable: bool = True,     # Filtre ikonu göster
    filter_type: str = "text",   # "text", "number", "date", "select"
    resizable: bool = True,
    movable: bool = True,
    hideable: bool = True,       # Sağ tık ile gizlenebilir
    sortable: bool = True,
    align: Qt.AlignmentFlag = None,
)
```

### 5.4 Diğer Bileşenler

| Bileşen | Dosya | Kullanım |
|---------|-------|---------|
| `PageHeader` | `ui/components/page_header.py` | Başlık çubuğu (42px yükseklik, başlık + arama + butonlar) |
| `ActionButtons` | `ui/components/action_buttons.py` | `create_view_button()`, `create_edit_button()`, `create_delete_button()`, `create_add_button()` — qtawesome ikonlu QPushButton döndürür |
| `show_toast()` | `ui/components/toast.py` | `show_toast(parent, "Mesaj", "success")` — ekranın sağ altında 3 sn görünen bildirim |
| `EmptyStateWidget` | `ui/components/empty_state.py` | Sekme açık değilken gösterilen yer tutucu |
| `FilterPopup` | `ui/components/filter_popup.py` | Sütun filtre popup'ı |
| `ActiveFiltersBar` | `ui/components/active_filters_bar.py` | Aktif filtreleri "pill" olarak gösterir |
| `WorkflowTimeline` | `ui/components/workflow_timeline.py` | İş akışı/onay zinciri görselleştirmesi |

### 5.5 Yeni Modül Yazma — Adım Adım Kılavuz

**Adım 1: Dizin oluştur**

```
modules/my_module/
├── __init__.py
├── services.py
└── views/
    ├── __init__.py
    ├── my_entity_module.py
    ├── my_entity_list.py
    └── my_entity_form.py
```

**Adım 2: Model tanımla** (`database/models/my_module.py`)

```python
from database.base import BaseModel
from sqlalchemy import Column, String, Integer, ForeignKey

class MyEntity(BaseModel):
    __tablename__ = "my_entities"

    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    # is_active, created_at, updated_at — BaseModel'den gelir
```

**Adım 3: Servis yaz** (`modules/my_module/services.py`)

```python
from database.base import get_session
from database.models.my_module import MyEntity

class MyEntityService:
    def __init__(self):
        self.session = get_session()

    def get_all(self, active_only: bool = True):
        q = self.session.query(MyEntity)
        if active_only:
            q = q.filter(MyEntity.is_active == True)
        return q.order_by(MyEntity.name).all()

    def get_by_id(self, entity_id: int):
        return self.session.query(MyEntity).filter(MyEntity.id == entity_id).first()

    def create(self, **kwargs) -> MyEntity:
        entity = MyEntity(**kwargs)
        self.session.add(entity)
        self.session.commit()
        return entity

    def update(self, entity_id: int, **kwargs) -> MyEntity:
        entity = self.get_by_id(entity_id)
        for key, value in kwargs.items():
            setattr(entity, key, value)
        self.session.commit()
        return entity

    def delete(self, entity_id: int) -> bool:
        entity = self.get_by_id(entity_id)
        entity.is_active = False  # Soft delete
        self.session.commit()
        return True
```

**Adım 4: Liste sayfası** (`views/my_entity_list.py`)

```python
from ui.components import BaseListPage, ColumnConfig
from config.icons import ICONS

class MyEntityListPage(BaseListPage):
    def __init__(self, parent=None):
        columns = [
            ColumnConfig("code", "Kod", width=100),
            ColumnConfig("name", "Ad",  width=250, stretch=True),
            ColumnConfig("actions", "İşlemler", width=120,
                         resizable=False, movable=False, hideable=False),
        ]
        super().__init__(
            title="Varlıklarım", icon=ICONS.LIST,
            table_id="my_entities", columns=columns,
        )

    def load_data(self, items: list):
        self.clear_table()
        for item in items:
            self.add_row(item)
        self.update_count(len(items))
```

**Adım 5: Form sayfası** (`views/my_entity_form.py`)

```python
from PyQt6.QtWidgets import QWidget, QFormLayout, QLineEdit, QPushButton
from PyQt6.QtCore import pyqtSignal

class MyEntityFormPage(QWidget):
    saved     = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(self, entity=None, parent=None):
        super().__init__(parent)
        self.entity = entity
        self._setup_ui()
        if entity:
            self._fill_form(entity)

    def _setup_ui(self):
        layout = QFormLayout(self)
        self.code_input = QLineEdit()
        self.name_input = QLineEdit()
        layout.addRow("Kod:", self.code_input)
        layout.addRow("Ad:", self.name_input)
        # Kaydet / İptal butonları...

    def _get_data(self) -> dict:
        return {"code": self.code_input.text(), "name": self.name_input.text()}
```

**Adım 6: Modül container** (`views/my_entity_module.py`)

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from .my_entity_list import MyEntityListPage
from .my_entity_form import MyEntityFormPage
from modules.development import ErrorHandler

class MyEntityModule(QWidget):
    page_title = "Varlıklarım"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()

        self.list_page = MyEntityListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete)
        self.list_page.refresh_requested.connect(self._load_data)
        self.stack.addWidget(self.list_page)
        layout.addWidget(self.stack)

    def showEvent(self, event):
        super().showEvent(event)
        if not self.service:
            from modules.my_module.services import MyEntityService
            self.service = MyEntityService()
        self._load_data()

    def _load_data(self):
        try:
            items = self.service.get_all()
            data = [{"id": i.id, "code": i.code, "name": i.name} for i in items]
            self.list_page.load_data(data)
        except Exception as e:
            ErrorHandler.handle_error(e, "my_module", "MyEntityModule",
                                       "_load_data", parent_widget=self)
```

**Adım 7: Menüye ekle**

```python
# config/menu_data.py
"my_module": {
    "title": "MODÜLÜm",
    "items": [("Varlıklarım", "ph.list", "my-entities")],
},

# ui/main_window.py → setup_pages_dict()
self.pages["my-entities"] = MyEntityModule()
```

**Adım 8: Migrasyon oluştur**

```bash
alembic revision --autogenerate -m "add_my_entities_table"
alembic upgrade head
```

---

## 6. Servis Katmanı Rehberi

### 6.1 Session Kullanım Kalıbı

```python
class MyService:
    def __init__(self):
        # Singleton scoped session — tüm metotlarda aynı session kullanılır
        self.session = get_session()

    def get_all(self):
        return self.session.query(MyModel).filter(MyModel.is_active == True).all()

    def create(self, **kwargs) -> MyModel:
        obj = MyModel(**kwargs)
        self.session.add(obj)
        self.session.commit()
        return obj  # expire_on_commit=False sayesinde commit sonra da erişilebilir
```

**Session kapatma:** Scoped session kullanıldığından manuel `session.close()` genellikle gerekmez. Uygulama kapanışında otomatik temizlenir.

### 6.2 Sayfalama Kalıbı

```python
def get_paginated(self, offset: int = 0, limit: int = 50,
                  search: str = None) -> tuple[list, int]:
    q = self.session.query(MyModel).filter(MyModel.is_active == True)
    if search:
        q = q.filter(
            or_(MyModel.name.ilike(f"%{search}%"),
                MyModel.code.ilike(f"%{search}%"))
        )
    total = q.count()
    items = q.order_by(MyModel.name).offset(offset).limit(limit).all()
    return items, total
```

### 6.3 İlişkili Veri Yükleme

```python
from sqlalchemy.orm import joinedload, selectinload

# joinedload: tek sorgu (JOIN) — 1:1 ve many:1 için ideal
items = (self.session.query(SalesOrder)
         .options(joinedload(SalesOrder.customer))
         .filter(SalesOrder.status == SalesOrderStatus.OPEN)
         .all())

# selectinload: ikinci sorgu — 1:many koleksiyonlar için ideal
bom = (self.session.query(BillOfMaterials)
       .options(selectinload(BillOfMaterials.lines).joinedload(BOMLine.item))
       .filter(BillOfMaterials.id == bom_id)
       .first())
```

### 6.4 Hata Yönetimi — Servis mi View mi?

**Kural:** DB exception'ları view katmanında yakalanır; servis katmanı exception'ı yukarı fırlatır.

```python
# services.py — exception fırlat
def create(self, **kwargs) -> MyModel:
    obj = MyModel(**kwargs)
    self.session.add(obj)
    self.session.commit()  # IntegrityError buradan fırlayabilir
    return obj

# views/module.py — exception yakala
def _save(self, data: dict):
    try:
        self.service.create(**data)
        from ui.components.toast import show_toast
        show_toast(self, "Kayıt eklendi", "success")
        self._load_data()
    except Exception as e:
        ErrorHandler.handle_error(e, "my_module", "MyModule",
                                   "_save", parent_widget=self)
```

---

## 7. Hata Yönetimi

### 7.1 ErrorHandler (`modules/development/error_handler.py:35`)

Tüm modüllerin kullandığı merkezi hata yönetimi sınıfı. Instance gerekmez, classmethod.

```python
from modules.development import ErrorHandler

try:
    result = self.service.save(data)
except Exception as e:
    ErrorHandler.handle_error(
        exception=e,
        module="sales",           # modül adı (string)
        screen="CustomerModule",  # widget sınıfı adı
        function="_save_customer",# method adı
        show_message=True,        # QMessageBox göster?
        severity="error",         # "critical", "error", "warning", "info"
        parent_widget=self,       # QMessageBox parent'ı
    )
```

### 7.2 ErrorHandler İç Akışı

```
1. traceback.extract_tb() → dosya/satır bilgisi al
2. rich.console.print()   → renkli terminal çıktısı (varsa)
3. ErrorLogService.log()  → error_logs tablosuna yaz
4. QMessageBox.warning()  → kullanıcıya göster (show_message=True ise)
5. TraceService kontrolü  → aktif trace session varsa olayı kaydet
```

**`error_logs` tablosu alanları:**
- `user_id`, `module_name`, `screen_name`, `function_name`
- `error_type` (exception sınıf adı), `error_message`, `error_traceback`
- `severity`, `is_resolved`, `resolved_by`, `resolved_at`

### 7.3 Kullanıcı Ayarı

Login başarılı olduğunda bir kez çağrılır:

```python
ErrorHandler.set_current_user(user)  # main.py'de çağrılır
```

---

## 8. Kimlik Doğrulama ve Yetkilendirme

### 8.1 UserContext (`core/user_context.py`)

Thread-safe `ContextVar` tabanlı global kullanıcı bağlamı.

```python
from core.user_context import get_current_user, set_current_user

# Mevcut kullanıcıyı al
ctx = get_current_user()
print(ctx.user_id, ctx.username, ctx.is_superuser)

# İzin kontrolü
if ctx.has_permission("inventory.delete"):
    # silme işlemi...

if ctx.is_authenticated:
    # oturum açık...
```

**UserContext alanları:**

```python
@dataclass
class UserContext:
    user_id: Optional[int]
    username: Optional[str]
    full_name: Optional[str]
    email: Optional[str]
    roles: Set[str]                # Rol kodları
    permissions: Set[str]          # İzin kodları (cache)
    session_id: Optional[int]
    session_token: Optional[str]
    login_time: Optional[datetime]
    is_superuser: bool

    # Metodlar
    def has_permission(self, code: str) -> bool
    def has_any_permission(self, *codes: str) -> bool
    def has_all_permissions(self, *codes: str) -> bool
    def is_authenticated: bool  # property
```

### 8.2 Rol ve İzin Modeli

```
users ──M:M──► roles ──M:M──► permissions

UserPagePermission: user_id + page_id (granüler sayfa erişimi)
```

**İzin kodu formatı:** `module.action` — örn. `inventory.create`, `sales.delete`, `accounting.post`

### 8.3 Sayfa Bazlı İzinler (`core/permission_map.py`)

```python
# Her page_id için gerekli izinler tanımlanır
PERMISSION_MAP = {
    "work-orders": ["production.view"],
    "journal-entries": ["accounting.view"],
    ...
}
```

`MainWindow.open_tab()` her sekme açılışında bu haritayı kontrol eder.

### 8.4 Dev Mode Bypass

```python
# main.py → _setup_dev_user_context()
# Admin kullanıcıyı DB'den çeker, login ekranını atlar
# PRODUCTION'da bu metot kaldırılacak, _show_login() çalışacak
```

---

## 9. Migrasyon Yönetimi

### 9.1 Temel Komutlar

```bash
# Tüm migrasyonları uygula
alembic upgrade head

# Yeni migrasyon oluştur (model değişikliklerinden otomatik üret)
alembic revision --autogenerate -m "add_my_table"

# Son migrasyonu geri al
alembic downgrade -1

# Mevcut durumu görüntüle
alembic current

# Migrasyon geçmişi
alembic history --verbose
```

### 9.2 Dosya Adlandırma Kuralı

```
alembic/versions/YYYYMMDD_NNN_description.py

Örnekler:
  20260101_001_initial_schema.py
  20260109_007_finance_module.py
  20260221_001_messaging_tables.py
```

### 9.3 Mevcut Migrasyon Kronolojisi (47 migrasyon)

| Tarih | Migrasyon | Kapsam |
|-------|-----------|--------|
| 2026-01-01 | `001` | İlk şema (items, warehouses, users) |
| 2026-01-08 | `005` | Satış modülü |
| 2026-01-09 | `006-007` | Fiyat listeleri, finans |
| 2026-01-09 | `2324` | Muhasebe (çift taraflı kayıt) |
| 2026-01-09 | `2341` | MRP |
| 2026-01-12 | `001` | Vardiya ekipleri |
| 2026-01-15 | `001` | Bakım geliştirmeleri |
| 2026-01-16 | `001,004` | Kullanıcı oturumları, dashboard tabloları |
| 2026-01-19 | — | Eğitim + personel tabloları |
| 2026-01-20 | `001` | Dual-unit (ikincil birim) |
| 2026-01-20 | `002` | SSCC / taşıma birimleri |
| 2026-01-22 | — | Sevkiyat modülü |
| 2026-01-25 | — | MPS tabloları |
| 2026-01-26 | — | İş akışı tabloları |
| 2026-02-03 | — | Şema düzeltmeleri |
| 2026-02-05 | — | Trace tabloları |
| 2026-02-08 | — | İade modülü |
| 2026-02-21 | `001` | Mesajlaşma tabloları (son) |

---

## 10. Test Altyapısı

### 10.1 Dizin Yapısı

```
tests/
├── conftest.py              # Pytest fixture'ları (DB session, factory'ler)
├── pytest.ini
├── unit/                    # Birim testler
│   ├── test_bom_management.py
│   ├── test_capacity_planning.py
│   ├── test_item_expansion.py
│   ├── test_material_mrp.py
│   ├── test_planning_risks.py
│   ├── test_production_kpis.py
│   ├── test_routing.py
│   ├── test_stock_form.py
│   ├── test_wip_tracking_mock.py
│   └── test_work_center.py
├── integration/             # Entegrasyon testler
│   ├── test_mrp_integration.py
│   ├── test_pro_phase.py
│   ├── test_stock_comprehensive.py
│   ├── test_stock_integration.py
│   └── test_work_order_integration.py
├── e2e/                     # Uçtan uca testler
├── factories/               # Test veri factory'leri
└── fixtures/                # Test fixture dosyaları
```

### 10.2 Test Çalıştırma

```bash
# Tüm testler
./run_tests.sh

# Sadece birim testler
pytest tests/unit/ -v

# Belirli bir modül
pytest tests/unit/test_bom_management.py -v

# Coverage raporu
pytest tests/ --cov=modules --cov-report=html
```

### 10.3 Yeni Test Yazma

```python
# tests/unit/test_my_module.py
import pytest
from modules.my_module.services import MyEntityService

class TestMyEntityService:
    def test_create_entity(self, db_session):  # conftest fixture
        service = MyEntityService()
        entity = service.create(code="TEST01", name="Test Varlığı")
        assert entity.id is not None
        assert entity.code == "TEST01"

    def test_soft_delete(self, db_session):
        service = MyEntityService()
        entity = service.create(code="DEL01", name="Silinecek")
        service.delete(entity.id)
        result = service.get_by_id(entity.id)
        assert result.is_active == False
```

---

## 11. Core Servisler

### 11.1 Export Manager (`core/export_manager.py`)

Excel ve PDF export işlemleri için merkezi servis.

```python
from core.export_manager import ExportManager

# Excel export
ExportManager.export_to_excel(
    data=rows,          # list[dict]
    columns=columns,    # list[str] — başlıklar
    filename="rapor.xlsx",
    sheet_name="Veriler",
)

# PDF export (ReportLab)
ExportManager.export_to_pdf(
    template="reports/invoice.html",  # Jinja2 şablonu
    context={"invoice": invoice_data},
    output_path="cikti/fatura.pdf",
)
```

### 11.2 Label Manager (`core/label_manager.py`)

Barkod etiketi yazdırma ve QR kod üretimi.

```python
from core.label_manager import LabelManager

LabelManager.print_label(
    template_code="ITEM_LABEL",
    data={"code": "ITEM001", "name": "Ürün Adı", "barcode": "1234567890"},
    copies=3,
)
```

### 11.3 Worker Manager (`core/threads/worker_manager.py`)

UI donmasını önlemek için arka plan thread'leri.

```python
from core.threads.worker_manager import WorkerManager

# Ağır işlemi arka planda çalıştır
def heavy_task():
    return expensive_computation()

def on_complete(result):
    self.list_page.load_data(result)

WorkerManager.run(heavy_task, callback=on_complete, error_callback=on_error)
```

### 11.4 FastAPI REST API (`core/api/main_api.py`)

Qt masaüstü uygulamasının yanında çalışan REST API katmanı. Harici entegrasyonlar ve web erişimi için kullanılır.

```bash
# API'yi başlat
uvicorn core.api.main_api:app --host 0.0.0.0 --port 8000

# Swagger UI
http://localhost:8000/docs
```

### 11.5 Barkod Yardımcıları (`utils/barcode_utils.py`)

```python
from utils.barcode_utils import generate_barcode, generate_qr_code

# EAN-13 barkod görüntüsü oluştur
img = generate_barcode("1234567890123", barcode_type="EAN13")

# QR kod oluştur
qr_img = generate_qr_code("https://example.com", size=200)
```

---

## 12. Özel Modüller — Detaylı Akış

### 12.1 Muhasebe — Çift Taraflı Kayıt

**Tablo hiyerarşisi:**

```
accounts (Hesap planı — ağaç yapısı)
  └── journal_entries (Yevmiye fişleri)
        └── journal_entry_lines (Borç/Alacak satırları)
              └── accounts (FK)

budgets → budget_lines → accounts
fiscal_periods (Dönem kapama)
```

**Yevmiye fişi dengesi:** Her `JournalEntry` için `SUM(debit) == SUM(credit)` koşulu sağlanmalıdır. `journal_entry_lines` tablosunda `debit` ve `credit` alanları kullanılır.

**Muhasebe köprüleri:** Satış, satınalma ve bordro modülleri kendi servislerinden muhasebe fişi oluşturmak için `accounting_bridge.py` veya `payroll_accounting_service.py`'yi kullanır.

### 12.2 Üretim — BOM → İş Emri Akışı

```
BillOfMaterials (Ürün Reçetesi)
  ├── bom_lines      → hangi malzemeler gerekli
  ├── bom_operations → hangi iş istasyonlarında, hangi sırada
  └── bom_by_products → yan ürünler

WorkOrder (İş Emri)
  ├── work_order_lines      → BOM satırlarından kopyalanan malzemeler
  ├── work_order_operations → BOM operasyonlarından kopyalanan operasyonlar
  │     └── work_order_operation_personnel → operatör ataması
  ├── work_order_by_products
  └── production_downtimes   → duruş kayıtları
```

**İş emri durumu geçişleri:**
`DRAFT → RELEASED → IN_PROGRESS → COMPLETED / CANCELLED`

**Alt iş emirleri:** `work_orders.parent_work_order_id` self-FK ile alt üretim emirleri desteklenir.

### 12.3 MRP — Gereksinim Hesaplama

```
Tetikleyiciler: satış siparişleri + minimum stok seviyeleri
     │
     ▼
MRPRun (hesaplama oturumu)
  └── MRPLine: her kalem için
        brüt gereksinim - eldeki stok - açık siparişler
        = net gereksinim → öneri türü (üretim/satınalma)
```

`mrp_lines.suggestion_type`: `PURCHASE_ORDER`, `WORK_ORDER`, `TRANSFER`

### 12.4 E-Fatura

**Tablo akışı:**

```
Invoice (satış faturası) veya PurchaseInvoice
    │
    ▼
EInvoice (UBL 2.1 XML içeriği)
    ├── direction: OUTGOING / INCOMING
    ├── type: EFATURA / EARSIVA
    ├── status: DRAFT → SENT → ACCEPTED / REJECTED
    └── xml_content: tam UBL XML

EInvoiceSettings (entegratör bağlantı bilgileri)
EInvoiceSeries (fatura seri/sıra yönetimi)
```

**UBL oluşturucu:** `modules/einvoice/services/ubl_builder.py` fatura verisini UBL 2.1 XML'e çevirir. Entegratör API çağrıları `modules/einvoice/services/integrator/` altındadır.

### 12.5 İzlenebilirlik — Lot/Seri Takibi

```
Lot (parti numarası)
  ├── product_id → items
  ├── work_order_id → üretime bağlı lot
  ├── purchase_order_id → alıma bağlı lot
  └── warehouse_id, location_id → konum

SerialNumber (seri numarası)
  └── lot_id → ait olduğu lot

TraceLink (lot zinciri)
  ├── parent_lot_id → üst lot
  ├── child_lot_id  → alt lot (malzeme)
  └── work_order_id → dönüşüm iş emri
```

`trace_engine.py` bu zinciri geriye/ileriye doğru takip ederek etkilenen ürün/parti listesini çıkarır.

### 12.6 Mesajlaşma — Conversation Modeli

```
Conversation (konuşma)
  ├── conversation_type: DIRECT, GROUP, DEPARTMENT, RECORD
  ├── entity_type + entity_id: polimorfik bağlantı (ör. iş emrine bağlı konuşma)
  └── ConversationParticipant (katılımcılar)
        └── user_id, role, last_read_at, unread_count

Message (mesaj)
  ├── conversation_id
  ├── sender_id
  ├── reply_to_id (self-FK — iç içe yanıtlar)
  ├── priority: NORMAL, HIGH, URGENT
  └── MessageAttachment (dosya ekleri)

MessageStar (yıldızlı mesajlar — user_id + message_id unique)
NotificationPreference (bildirim tercihleri — kullanıcı başına)
```

**Record Messaging:** Herhangi bir kayda (iş emri, satış siparişi vb.) bağlı konuşma açılabilir. `entity_type` + `entity_id` polimorfik FK ile sağlanır. `modules/messaging/views/record_messaging_button.py` bileşeni bu özelliği UI'a ekler.

---

## Ek: Sık Kullanılan Import Kalıpları

```python
# Veritabanı
from database.base import get_session, BaseModel

# Stiller
from config.styles import get_button_style, BG_PRIMARY, TEXT_PRIMARY
from config.icons import ICONS
from config.theme_manager import ThemeManager

# UI bileşenleri
from ui.components import BaseListPage, ColumnConfig
from ui.components.action_buttons import create_edit_button, create_delete_button
from ui.components.toast import show_toast
from ui.components.page_header import PageHeader

# Hata yönetimi
from modules.development import ErrorHandler

# Kullanıcı context
from core.user_context import get_current_user

# Export
from core.export_manager import ExportManager
```

---

---

## 13. Veritabanı Tabloları — Tam Referans

Bu bölüm tüm tabloları, tuttukları veriyi ve birbirleriyle ilişkilerini açıklar. Tablolar domain'e göre gruplanmıştır.

> **Okuma kılavuzu:** `→` işareti "FK referansı" anlamına gelir.
> Tüm tablolarda `id (PK)`, `created_at`, `updated_at`, `is_active` alanları BaseModel'den gelir (aksi belirtilmedikçe).

---

### 13.1 Kimlik Doğrulama ve Yetkilendirme

#### `users` — Sistem Kullanıcıları

Uygulamaya giriş yapan tüm kullanıcıları tutar. Sistem yöneticileri, muhasebeciler, depo personeli gibi tüm roller buradan yönetilir.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `username` | String(50) UNIQUE | Giriş kullanıcı adı |
| `email` | String(255) UNIQUE | E-posta (ikincil giriş yöntemi) |
| `password_hash` | String(255) | bcrypt hash |
| `first_name`, `last_name` | String(100) | Ad soyad |
| `phone` | String(20) | Telefon |
| `avatar` | String(255) | Profil fotoğrafı dosya yolu |
| `is_superuser` | Boolean | Tüm izinlere sahip süper admin |
| `is_verified` | Boolean | E-posta doğrulandı mı |
| `last_login` | DateTime | Son giriş zamanı |
| `failed_login_attempts` | Integer | Başarısız giriş sayacı |
| `locked_until` | DateTime | Hesap kilidi bitiş zamanı |
| `language` | String(5) | Arayüz dili (tr, en) |
| `theme` | String(20) | Tema tercihi (dark, light) |
| `preferences` | JSON | Ek kullanıcı tercihleri |

**İlişkiler:** `users` ←M:M→ `roles` (user_roles ara tablo)

---

#### `roles` — Roller

Yetki gruplarını tanımlar. Hiyerarşik yapı desteklenir (üst rol, alt rol).

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String(50) UNIQUE | Rol kodu (ADMIN, MUHASEBE, DEPO…) |
| `name` | String(100) | Görünen ad |
| `description` | Text | Açıklama |
| `parent_id` | → `roles.id` | Üst rol (hiyerarşi) |
| `level` | Integer | Yetki seviyesi (0 = en yüksek) |

**İlişkiler:** `roles` ←M:M→ `permissions` (role_permissions ara tablo)

---

#### `permissions` — İzinler

Sistem genelindeki tekil izin tanımları.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String(100) UNIQUE | İzin kodu (inventory.create, sales.delete…) |
| `name` | String(200) | Görünen ad |
| `module` | String(50) | Hangi modüle ait (inventory, sales…) |

---

#### `user_roles` — Kullanıcı-Rol İlişkisi (M:M ara tablo)

| Alan | Açıklama |
|------|---------|
| `user_id` → `users.id` | Kullanıcı |
| `role_id` → `roles.id` | Rol |
| `created_at` | Atama zamanı |

---

#### `role_permissions` — Rol-İzin İlişkisi (M:M ara tablo)

| Alan | Açıklama |
|------|---------|
| `role_id` → `roles.id` | Rol |
| `permission_id` → `permissions.id` | İzin |

---

#### `user_page_permissions` — Kullanıcı Sayfa İzinleri

Belirli bir kullanıcıya granüler sayfa erişimi vermek için kullanılır (rol bazlı erişimin üzerinde).

| Alan | Tür | Açıklama |
|------|-----|---------|
| `user_id` | → `users.id` | Kullanıcı |
| `page_id` | String | menu_data.py'deki sayfa kimliği |
| `granted_by` | → `users.id` | İzni veren kullanıcı |

---

#### `user_sessions` — Kullanıcı Oturumları

Aktif giriş oturumlarını takip eder. Çok cihazlı oturum yönetimi ve zorla çıkış için kullanılır.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `user_id` | → `users.id` | Kullanıcı |
| `session_token` | String UNIQUE | Oturum jetonu |
| `expires_at` | DateTime | Geçerlilik süresi |
| `device_name` | String | Cihaz adı |
| `ip_address` | String | IP adresi |
| `is_revoked` | Boolean | Oturum iptal edildi mi |

---

#### `audit_logs` — Denetim Kayıtları

Sistemdeki tüm veri değişikliklerini (INSERT/UPDATE/DELETE) otomatik kaydeder. `audit_engine.py` tarafından SQLAlchemy event listener ile doldurulur.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `user_id` | → `users.id` | İşlemi yapan kullanıcı |
| `action` | String | INSERT / UPDATE / DELETE |
| `module` | String | Hangi modül (sales, inventory…) |
| `table_name` | String | Değişen tablo adı |
| `record_id` | Integer | Değişen kaydın id'si |
| `old_values` | JSON | Değişmeden önceki değerler |
| `new_values` | JSON | Değişen yeni değerler |
| `ip_address` | String | İşlemi yapan IP |

---

#### `settings` — Uygulama Ayarları

Anahtar-değer tabanlı sistem ayarları.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `key` | String UNIQUE | Ayar anahtarı |
| `value` | Text | Ayar değeri |
| `value_type` | String | Değer türü (string, integer, boolean, json) |
| `category` | String | Kategori (general, email, print…) |
| `updated_by` | → `users.id` | Son güncelleyen kullanıcı |

---

#### `sequences` — Sıra Numaraları

Sipariş no, fatura no gibi belge numaralarını yönetir.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | Sıra kodu (SALES_ORDER, INVOICE…) |
| `prefix` | String | Ön ek (SO, INV, PO…) |
| `current_value` | Integer | Mevcut sayaç değeri |
| `step` | Integer | Artış miktarı (genellikle 1) |
| `min_digits` | Integer | Minimum basamak sayısı (5 → 00001) |
| `reset_period` | String | Sıfırlama periyodu (YEARLY, MONTHLY, NEVER) |

---

### 13.2 Ortak (Common) Tablolar

#### `currencies` — Para Birimleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String(3) UNIQUE | ISO kodu (TRY, USD, EUR, GBP) |
| `name` | String | Tam ad |
| `symbol` | String | Sembol (₺, $, €) |
| `is_default` | Boolean | Varsayılan para birimi mi |

---

#### `exchange_rates` — Döviz Kurları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `currency_id` | → `currencies.id` | Para birimi |
| `rate_date` | Date | Kur tarihi |
| `buying_rate` | Numeric(10,4) | Alış kuru |
| `selling_rate` | Numeric(10,4) | Satış kuru |
| `source` | String | Kaynak (TCMB, MANUAL…) |

---

#### `countries`, `cities`, `districts` — Adres Hiyerarşisi

```
countries (ülke)
  └── cities (şehir, country_id → countries.id)
        └── districts (ilçe, city_id → cities.id, postal_code)
```

---

#### `attachments` — Dosya Ekleri (Polimorfik)

Herhangi bir kayda dosya eklemek için polimorfik yapı kullanır.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `module` | String | Modül adı (sales, production…) |
| `table_name` | String | Tablo adı (sales_orders, work_orders…) |
| `record_id` | Integer | İlgili kayıt id'si |
| `file_name` | String | Dosya adı |
| `file_path` | String | Sunucudaki dosya yolu |
| `file_size` | Integer | Boyut (byte) |
| `mime_type` | String | MIME türü |
| `uploaded_by` | → `users.id` | Yükleyen kullanıcı |

---

#### `notes` — Notlar (Polimorfik)

Herhangi bir kayda not eklemek için polimorfik yapı.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `module` | String | Modül adı |
| `table_name` | String | Tablo adı |
| `record_id` | Integer | İlgili kayıt id'si |
| `content` | Text | Not içeriği |
| `created_by` | → `users.id` | Notu yazan kullanıcı |

---

#### `notifications` — Sistem Bildirimleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `user_id` | → `users.id` | Bildirim alıcısı |
| `title` | String | Başlık |
| `message` | Text | Mesaj içeriği |
| `notification_type` | String | Tür (info, warning, success, error) |
| `is_read` | Boolean | Okundu mu |
| `related_module` | String | İlgili modül |
| `related_record_id` | Integer | İlgili kayıt |

---

#### `label_templates` — Etiket Şablonları

Barkod ve ürün etiket şablonlarını saklar.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | Şablon kodu |
| `name` | String | Şablon adı |
| `template_type` | String | Tür (ITEM_LABEL, PALLET, SHIPMENT…) |
| `content` | Text | ZPL/HTML şablon içeriği |
| `width_mm` | Numeric | Etiket genişliği (mm) |
| `height_mm` | Numeric | Etiket yüksekliği (mm) |

---

### 13.3 Stok Yönetimi (Inventory)

#### `units` — Ölçü Birimleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String(20) UNIQUE | Kod (ADET, KG, LT, M2…) |
| `name` | String(100) | Tam ad (Adet, Kilogram…) |
| `short_name` | String(20) | Kısa ad (pcs, kg, l) |

---

#### `unit_conversions` — Birim Dönüşümleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `from_unit_id` | → `units.id` | Kaynak birim |
| `to_unit_id` | → `units.id` | Hedef birim |
| `multiplier` | Numeric(18,6) | Dönüşüm katsayısı (1 kg = 1000 gr → 1000) |
| `item_id` | → `items.id` (nullable) | Stok kartına özel dönüşüm (opsiyonel) |

UNIQUE kısıt: `(from_unit_id, to_unit_id, item_id)`

---

#### `item_categories` — Stok Kategorileri

Hiyerarşik kategori ağacı. Sonsuz derinlik desteklenir.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String(50) UNIQUE | Kategori kodu |
| `name` | String(200) | Kategori adı |
| `parent_id` | → `item_categories.id` | Üst kategori (self-FK) |
| `level` | Integer | Ağaç derinliği (0 = kök) |
| `path` | String(500) | Tam yol (ör. "Hammadde/Metal/Çelik") |
| `icon` | String(50) | İkon kodu |
| `color` | String(7) | HEX renk (#FF0000) |

---

#### `items` — Stok Kartları ⭐ (Merkezi tablo)

Tüm malzeme, ürün ve hizmetlerin ana kartı. Sistemdeki en fazla referans alınan tablo.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String(50) UNIQUE | Stok kodu |
| `name` | String(300) | Stok adı |
| `short_name` | String(100) | Kısa ad |
| `item_type` | Enum | hammadde, mamul, yari_mamul, ambalaj, sarf, ticari, hizmet, diger |
| `category_id` | → `item_categories.id` | Kategori |
| `unit_id` | → `units.id` | Ana ölçü birimi |
| `barcode` | String(100) | Ana barkod |
| `barcode_ean` | String(20) UNIQUE | EAN/GTIN barkodu |
| `manufacturer_code` | String(100) | Üretici kodu |
| `supplier_code` | String(100) | Tedarikçi kodu |
| `gtip_code` | String(20) | Gümrük tarife kodu |
| `purchase_price` | Numeric(18,4) | Alış fiyatı |
| `sale_price` | Numeric(18,4) | Satış fiyatı |
| `list_price` | Numeric(18,4) | Liste fiyatı |
| `min_sale_price` | Numeric(18,4) | Minimum satış fiyatı |
| `currency_id` | → `currencies.id` | Fiyat para birimi |
| `vat_rate` | Numeric(5,2) | KDV oranı (%) |
| `valuation_method` | Enum | AVERAGE (ort. maliyet), STANDARD |
| `min_stock` | Numeric(18,4) | Minimum stok seviyesi |
| `max_stock` | Numeric(18,4) | Maksimum stok seviyesi |
| `reorder_point` | Numeric(18,4) | Yeniden sipariş noktası |
| `reorder_quantity` | Numeric(18,4) | Yeniden sipariş miktarı |
| `safety_stock` | Numeric(18,4) | Güvenlik stoğu |
| `lead_time_days` | Integer | Tedarik süresi (gün) |
| `mrp_type` | Enum | AUTO, MANUAL, ROP |
| `lot_size_policy` | Enum | LFL (ihtiyaç kadar), FIXED |
| `min_order_qty` | Numeric(18,4) | Minimum sipariş miktarı |
| `order_multiple` | Numeric(18,4) | Sipariş katı |
| `procurement_type` | String | purchase / manufacture |
| `planning_time_fence` | Integer | Planlama zaman sınırı (gün) |
| `track_lot` | Boolean | Parti takibi aktif mi |
| `track_serial` | Boolean | Seri no takibi aktif mi |
| `track_expiry` | Boolean | Son kullanma tarihi takibi |
| `shelf_life_days` | Integer | Raf ömrü (gün) |
| `weight` / `net_weight` / `gross_weight` | Numeric | Ağırlıklar (kg) |
| `volume`, `width`, `height`, `depth` | Numeric | Fiziksel boyutlar |
| `brand`, `model` | String | Marka ve model |
| `origin_country` | String | Menşei ülke |
| `is_purchasable` | Boolean | Satın alınabilir mi |
| `is_saleable` | Boolean | Satılabilir mi |
| `is_producible` | Boolean | Üretilebilir mi |
| `is_qc_required` | Boolean | Kalite kontrolü zorunlu mu |

**Bu tabloya referans veren tablolar (14 farklı modül):**
`sales_order_items`, `delivery_note_items`, `invoice_items`, `purchase_order_items`, `goods_receipt_items`, `purchase_invoice_items`, `bom_lines`, `work_order_lines`, `stock_balances`, `stock_movements`, `inspection_templates`, `lots`, `equipment_spare_parts`, `transport_unit_items`, `rfq_items`, `contract_lines`, `price_list_items`

---

#### `item_barcodes` — Stok Kartı Barkodları

Bir stok kartına birden fazla barkod tanımlamak için.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `item_id` | → `items.id` | Stok kartı |
| `barcode` | String(100) | Barkod değeri |
| `barcode_type` | String(20) | Tür (EAN13, QR, Code128…) |
| `unit_id` | → `units.id` | Bu barkodun geçerli olduğu birim |
| `is_primary` | Boolean | Birincil barkod mu |

---

#### `warehouses` — Depolar

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String(20) UNIQUE | Depo kodu |
| `name` | String(100) | Depo adı |
| `address` | Text | Depo adresi |
| `is_default` | Boolean | Varsayılan depo mu |
| `is_production` | Boolean | Üretim deposu mu |
| `allow_negative` | Boolean | Negatif stoka izin ver |

---

#### `warehouse_locations` — Depo Lokasyonları

Bir deponun raf/koridor/göz yapısını tanımlar.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `warehouse_id` | → `warehouses.id` | Ait olduğu depo |
| `code` | String(50) | Lokasyon kodu |
| `aisle` | String(20) | Koridor |
| `rack` | String(20) | Raf |
| `shelf` | String(20) | Kat |
| `bin` | String(20) | Göz |
| `location_type` | Enum | normal, quarantine, scrap, transit |
| `barcode` | String(100) UNIQUE | Lokasyon barkodu |
| `max_weight` | Numeric | Maksimum yük (kg) |
| `max_volume` | Numeric | Maksimum hacim (m³) |

---

#### `stock_balances` — Stok Bakiyeleri

Her stok kartının depo/lokasyon bazında anlık miktarını gösterir.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `item_id` | → `items.id` | Stok kartı |
| `warehouse_id` | → `warehouses.id` | Depo |
| `location_id` | → `warehouse_locations.id` | Lokasyon (nullable) |
| `quantity` | Numeric(18,4) | Mevcut miktar |
| `reserved_quantity` | Numeric(18,4) | Rezerve miktar |
| `lot_number` | String | Parti numarası |
| `expiry_date` | Date | Son kullanma tarihi |
| `unit_cost` | Numeric(18,4) | Birim maliyet |
| `secondary_unit_id` | → `units.id` | İkincil birim |
| `secondary_quantity` | Numeric | İkincil birim miktarı |

**Hesaplanan:** `available_quantity = quantity - reserved_quantity`

---

#### `stock_movements` — Stok Hareketleri

Her stok giriş/çıkış/transferini kayıt altına alır. Tam denetim izleme için kullanılır.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `movement_type` | Enum | giris, cikis, satin_alma, satis, uretim_giris, uretim_cikis, transfer, sayim_fazla, sayim_eksik, fire, iade_alis, iade_satis |
| `item_id` | → `items.id` | Stok kartı |
| `from_warehouse_id` | → `warehouses.id` | Çıkış deposu |
| `to_warehouse_id` | → `warehouses.id` | Giriş deposu |
| `from_location_id` | → `warehouse_locations.id` | Çıkış lokasyonu |
| `to_location_id` | → `warehouse_locations.id` | Giriş lokasyonu |
| `quantity` | Numeric(18,4) | Hareket miktarı |
| `unit_id` | → `units.id` | Birim |
| `unit_cost` | Numeric(18,4) | Birim maliyet |
| `total_cost` | Numeric(18,4) | Toplam maliyet |
| `currency_id` | → `currencies.id` | Para birimi |
| `lot_number` | String | Parti numarası |
| `serial_number` | String | Seri numarası |
| `reference_type` | String | Belge türü (sales_order, work_order…) |
| `reference_id` | Integer | Belge id'si |
| `notes` | Text | Açıklama |
| `created_by` | → `users.id` | Oluşturan kullanıcı |
| `approved_by` | → `users.id` | Onaylayan kullanıcı |

---

#### `stock_requests` — Stok Kartı Talepleri

Depoda karşılığı olmayan malzeme için yeni stok kartı oluşturma talebi.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `requester_id` | → `users.id` | Talep eden kullanıcı |
| `proposed_name` | String | Önerilen stok kartı adı |
| `item_type` | Enum | Önerilen tür |
| `status` | Enum | pending, approved, rejected |
| `created_stock_id` | → `items.id` | Onaylandıktan sonra oluşturulan stok kartı |

---

### 13.4 Firma Yönetimi (Company)

#### `companies` — Firmalar

Çok firma desteği için. Hem kendi firmalarımızı hem de müşteri/tedarikçi firma profillerini tutar.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | Firma kodu |
| `name` | String | Firma adı |
| `company_type` | Enum | OWN (kendi firma), CUSTOMER, SUPPLIER, SUBSIDIARY |
| `parent_id` | → `companies.id` | Üst şirket (grup yapısı) |
| `tax_number` | String | Vergi numarası |
| `tax_office` | String | Vergi dairesi |
| `is_efatura` | Boolean | E-fatura mükellefi mi |
| `is_earsiv` | Boolean | E-arşiv mükellefi mi |

**Alt tablolar:**
- `company_addresses`: Fatura, teslimat adresleri
- `company_banks`: IBAN ve banka bilgileri
- `company_contacts`: Yetkili kişiler
- `company_settings`: Varsayılan KDV, fatura prefix, döviz, üretim tipi
- `company_documents`: İmza sirküleri, yetki belgesi vb.

---

### 13.5 Satış (Sales)

#### `price_lists` — Fiyat Listeleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String(20) UNIQUE | Liste kodu |
| `name` | String | Liste adı |
| `list_type` | Enum | sales / purchase |
| `currency` | String(10) | Para birimi |
| `valid_from`, `valid_until` | Date | Geçerlilik tarihleri |
| `is_default` | Boolean | Varsayılan liste mi |
| `priority` | Integer | Öncelik (düşük = yüksek öncelik) |

---

#### `price_list_items` — Fiyat Listesi Kalemleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `price_list_id` | → `price_lists.id` | Fiyat listesi |
| `item_id` | → `items.id` | Stok kartı |
| `unit_price` | Numeric(18,4) | Birim fiyat |
| `min_quantity` | Numeric(18,4) | Bu fiyatın geçerli olduğu minimum miktar |
| `discount_rate` | Numeric(5,2) | İndirim oranı (%) |

UNIQUE: `(price_list_id, item_id, min_quantity)`

---

#### `customers` — Müşteriler ⭐

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String(20) UNIQUE | Müşteri kodu |
| `name` | String(200) | Müşteri adı |
| `tax_number` | String(20) | Vergi numarası |
| `tax_office` | String(100) | Vergi dairesi |
| `contact_person` | String | Yetkili kişi |
| `phone`, `mobile`, `fax`, `email`, `website` | String | İletişim |
| `address`, `city`, `district`, `postal_code`, `country` | String/Text | Adres |
| `payment_term_days` | Integer | Vade günü |
| `credit_limit` | Numeric(15,2) | Kredi limiti |
| `currency` | String(10) | Varsayılan para birimi |
| `price_list_id` | → `price_lists.id` | Müşterinin fiyat listesi |
| `bank_name`, `iban` | String | Banka bilgileri |
| `rating` | Integer | Müşteri puanı (0-5) |

---

#### `sales_quotes` — Satış Teklifleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `quote_no` | String(20) UNIQUE | Teklif numarası |
| `quote_date` | Date | Teklif tarihi |
| `customer_id` | → `customers.id` | Müşteri |
| `opportunity_id` | → `opportunities.id` | CRM fırsatı (nullable) |
| `status` | Enum | draft, sent, accepted, rejected, ordered, expired, cancelled |
| `valid_until` | Date | Geçerlilik tarihi |
| `currency` | String | Para birimi |
| `exchange_rate` | Numeric | Kur |
| `subtotal`, `discount_amount`, `tax_amount`, `total` | Numeric | Tutar hesaplamaları |
| `rejection_reason` | Text | Red gerekçesi |

---

#### `sales_quote_items` — Teklif Satırları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `quote_id` | → `sales_quotes.id` | Teklif |
| `item_id` | → `items.id` | Stok kartı |
| `unit_id` | → `units.id` | Birim |
| `quantity` | Numeric | Miktar |
| `unit_price` | Numeric | Birim fiyat |
| `discount_rate` | Numeric(5,2) | İndirim oranı |
| `tax_rate` | Numeric(5,2) | KDV oranı |
| `line_total` | Numeric | Satır toplamı |

---

#### `sales_orders` — Satış Siparişleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `order_no` | String UNIQUE | Sipariş numarası |
| `order_date` | Date | Sipariş tarihi |
| `customer_id` | → `customers.id` | Müşteri |
| `status` | Enum | draft, confirmed, partial, delivered, closed, cancelled |
| `quote_id` | → `sales_quotes.id` | Kaynak teklif (nullable) |
| `source_warehouse_id` | → `warehouses.id` | Sevk deposu |
| `currency`, `exchange_rate` | — | Para birimi bilgileri |
| `payment_type` | Enum | pesin, vadeli, kapida |
| `required_date` | Date | İstenen teslim tarihi |
| `subtotal`, `tax_amount`, `total` | Numeric | Tutarlar |
| `shipment_readiness` | Enum | bekliyor, odeme, onay, stok, uretim, hazir |
| `created_by` | → `users.id` | Oluşturan kullanıcı |

---

#### `sales_order_items` — Sipariş Satırları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `order_id` | → `sales_orders.id` | Sipariş |
| `item_id` | → `items.id` | Stok kartı |
| `unit_id` | → `units.id` | Birim |
| `quantity` | Numeric | Sipariş miktarı |
| `unit_price` | Numeric | Birim fiyat |
| `discount_rate` | Numeric | İndirim oranı |
| `tax_rate` | Numeric | KDV oranı |
| `delivered_quantity` | Numeric | Teslim edilen miktar |
| `invoiced_quantity` | Numeric | Faturalandırılan miktar |

---

#### `delivery_notes` — Teslimat İrsaliyeleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `delivery_no` | String UNIQUE | İrsaliye numarası |
| `delivery_date` | Date | Sevk tarihi |
| `sales_order_id` | → `sales_orders.id` | Kaynak sipariş |
| `customer_id` | → `customers.id` | Müşteri |
| `status` | Enum | draft, shipped, delivered, cancelled |
| `source_warehouse_id` | → `warehouses.id` | Kaynak depo |
| `shipping_address` | Text | Teslimat adresi |
| `driver_name`, `plate_no` | String | Taşıma bilgileri |

---

#### `delivery_note_items` — İrsaliye Satırları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `delivery_note_id` | → `delivery_notes.id` | İrsaliye |
| `item_id` | → `items.id` | Stok kartı |
| `so_item_id` | → `sales_order_items.id` | Sipariş satırı |
| `unit_id` | → `units.id` | Birim |
| `quantity` | Numeric | Sevk miktarı |
| `lot_number` | String | Parti numarası |

---

#### `invoices` — Satış Faturaları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `invoice_no` | String UNIQUE | Fatura numarası |
| `invoice_date` | Date | Fatura tarihi |
| `customer_id` | → `customers.id` | Müşteri |
| `sales_order_id` | → `sales_orders.id` | Kaynak sipariş |
| `delivery_note_id` | → `delivery_notes.id` | Kaynak irsaliye |
| `status` | Enum | draft, issued, partial, paid, overdue, cancelled |
| `currency`, `exchange_rate` | — | Para birimi |
| `subtotal`, `discount_amount`, `tax_amount`, `total` | Numeric | Tutarlar |
| `paid_amount` | Numeric | Ödenen miktar |
| `due_date` | Date | Vade tarihi |

---

#### `invoice_items` — Fatura Satırları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `invoice_id` | → `invoices.id` | Fatura |
| `item_id` | → `items.id` | Stok kartı |
| `unit_id` | → `units.id` | Birim |
| `quantity` | Numeric | Miktar |
| `unit_price` | Numeric | Birim fiyat |
| `discount_rate` | Numeric | İndirim |
| `tax_rate` | Numeric | KDV oranı |
| `tax_amount`, `line_total` | Numeric | Satır tutarları |

---

### 13.6 Satınalma (Purchasing)

#### `suppliers` — Tedarikçiler ⭐

Müşteriler (`customers`) tablosuyla simetrik yapı. Aynı alanları içerir.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String(20) UNIQUE | Tedarikçi kodu |
| `name` | String(200) | Tedarikçi adı |
| `tax_number`, `tax_office` | String | Vergi bilgileri |
| `payment_term_days` | Integer | Vade günü |
| `credit_limit` | Numeric | Kredi limiti |
| `currency` | Enum | TRY, USD, EUR, GBP |
| `rating` | Integer | Tedarikçi puanı (0-5) |
| _İletişim ve adres alanları_ | — | customers ile aynı yapı |

---

#### `purchase_requests` — Satınalma Talepleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `request_no` | String UNIQUE | Talep numarası |
| `request_date` | Date | Talep tarihi |
| `requested_by` | String | Talep eden kişi adı |
| `department` | String | Departman adı |
| `status` | Enum | draft, pending, approved, rejected, ordered, cancelled |
| `priority` | Integer | Öncelik (1=düşük, 3=acil) |
| `required_date` | Date | İstenen teslim tarihi |
| `approved_by` | String | Onaylayan kişi |
| `rejection_reason` | Text | Red gerekçesi |

---

#### `purchase_request_items` — Talep Satırları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `request_id` | → `purchase_requests.id` | Talep |
| `item_id` | → `items.id` (nullable) | Stok kartı |
| `quantity` | Numeric | Talep miktarı |
| `unit_id` | → `units.id` | Birim |
| `suggested_supplier_id` | → `suppliers.id` | Önerilen tedarikçi |
| `notes` | Text | Açıklama |

---

#### `purchase_orders` — Satınalma Siparişleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `order_no` | String UNIQUE | Sipariş numarası |
| `order_date` | Date | Sipariş tarihi |
| `supplier_id` | → `suppliers.id` | Tedarikçi |
| `status` | Enum | draft, sent, confirmed, partial, received, closed, cancelled |
| `delivery_warehouse_id` | → `warehouses.id` | Teslim deposu |
| `request_id` | → `purchase_requests.id` | Kaynak talep (nullable) |
| `currency`, `exchange_rate` | — | Para birimi |
| `subtotal`, `tax_amount`, `total` | Numeric | Tutarlar |
| `expected_delivery_date` | Date | Beklenen teslim tarihi |

---

#### `purchase_order_items` — Sipariş Satırları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `order_id` | → `purchase_orders.id` | Sipariş |
| `item_id` | → `items.id` | Stok kartı |
| `unit_id` | → `units.id` | Birim |
| `quantity` | Numeric | Sipariş miktarı |
| `unit_price` | Numeric | Birim fiyat |
| `tax_rate` | Numeric | KDV oranı |
| `received_quantity` | Numeric | Teslim alınan miktar |
| `invoiced_quantity` | Numeric | Faturalandırılan miktar |

---

#### `goods_receipts` — Mal Kabuller

| Alan | Tür | Açıklama |
|------|-----|---------|
| `receipt_no` | String UNIQUE | Mal kabul numarası |
| `receipt_date` | Date | Tarih |
| `purchase_order_id` | → `purchase_orders.id` | Kaynak sipariş |
| `supplier_id` | → `suppliers.id` | Tedarikçi |
| `warehouse_id` | → `warehouses.id` | Teslim alınan depo |
| `status` | Enum | draft, completed, cancelled |
| `vehicle_plate` | String | Araç plakası |
| `driver_name` | String | Sürücü adı |

---

#### `goods_receipt_items` — Mal Kabul Satırları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `receipt_id` | → `goods_receipts.id` | Mal kabul |
| `item_id` | → `items.id` | Stok kartı |
| `po_item_id` | → `purchase_order_items.id` | Sipariş satırı |
| `unit_id` | → `units.id` | Birim |
| `ordered_quantity` | Numeric | Siparişteki miktar |
| `accepted_quantity` | Numeric | Kabul edilen miktar |
| `rejected_quantity` | Numeric | Reddedilen miktar |
| `lot_number` | String | Parti numarası |
| `expiry_date` | Date | Son kullanma tarihi |

---

#### `purchase_invoices` — Satınalma Faturaları

Müşterilerden gelen faturalar. `invoices` ile simetrik yapı.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `invoice_no` | String UNIQUE | Tedarikçi fatura numarası |
| `invoice_date` | Date | Fatura tarihi |
| `supplier_id` | → `suppliers.id` | Tedarikçi |
| `purchase_order_id` | → `purchase_orders.id` | Kaynak sipariş |
| `goods_receipt_id` | → `goods_receipts.id` | Kaynak mal kabul |
| `status` | Enum | draft, posted, partial, paid, overdue, cancelled |
| `subtotal`, `tax_amount`, `total` | Numeric | Tutarlar |
| `paid_amount` | Numeric | Ödenen miktar |
| `due_date` | Date | Vade tarihi |

---

#### `vendor_ratings` — Tedarikçi Değerlendirmeleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `supplier_id` | → `suppliers.id` | Tedarikçi |
| `rating_date` | Date | Değerlendirme tarihi |
| `quality_score` | Numeric(3,1) | Kalite puanı (0-10) |
| `delivery_score` | Numeric(3,1) | Teslimat puanı (0-10) |
| `cost_score` | Numeric(3,1) | Maliyet puanı (0-10) |
| `total_score` | Numeric(3,1) | Genel puan |
| `evaluator_id` | → `users.id` | Değerlendiren kullanıcı |

---

### 13.7 Üretim (Production)

#### `bill_of_materials` — Ürün Reçeteleri (BOM)

| Alan | Tür | Açıklama |
|------|-----|---------|
| `item_id` | → `items.id` | Üretilecek ürün |
| `code` | String UNIQUE | Reçete kodu |
| `name` | String | Reçete adı |
| `version` | Integer | Versiyon numarası |
| `revision` | String | Revizyon (A, B, C…) |
| `status` | Enum | draft, active, revision, obsolete |
| `bom_type` | Enum | standard, formula |
| `base_quantity` | Numeric(18,4) | Üretim miktarı (reçetenin temel birimi) |
| `unit_id` | → `units.id` | Birim |
| `lead_time_days` | Integer | Üretim temin süresi |
| `setup_time_minutes` | Integer | Hazırlık süresi (dk) |
| `production_time_minutes` | Integer | Üretim süresi (dk) |
| `labor_cost` | Numeric | İşçilik maliyeti |
| `overhead_cost` | Numeric | Genel gider maliyeti |
| `valid_from`, `valid_to` | Date | Geçerlilik dönemi |

---

#### `bom_lines` — Reçete Malzeme Satırları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `bom_id` | → `bill_of_materials.id` | Ürün reçetesi |
| `item_id` | → `items.id` | Kullanılacak malzeme |
| `quantity` | Numeric(18,6) | Miktar |
| `unit_id` | → `units.id` | Birim |
| `scrap_rate` | Numeric(5,2) | Fire oranı (%) |
| `line_no` | Integer | Satır sırası |
| `is_optional` | Boolean | Opsiyonel malzeme mi |
| `is_alternative` | Boolean | Alternatif malzeme mi |
| `backflush_mode` | Enum | on_start, on_complete, manual |

---

#### `bom_operations` — Reçete Operasyonları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `bom_id` | → `bill_of_materials.id` | Reçete |
| `work_station_id` | → `work_stations.id` | İş istasyonu |
| `sequence` | Integer | İşlem sırası |
| `predecessor_id` | → `bom_operations.id` | Önceki operasyon (self-FK) |
| `setup_time_minutes` | Integer | Hazırlık süresi |
| `run_time_minutes` | Numeric | Çalışma süresi (adet başına) |
| `description` | Text | Operasyon açıklaması |

---

#### `bom_by_products` — Reçete Yan Ürünleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `bom_id` | → `bill_of_materials.id` | Reçete |
| `item_id` | → `items.id` | Yan ürün |
| `quantity` | Numeric | Beklenen miktar |
| `unit_id` | → `units.id` | Birim |

---

#### `work_stations` — İş İstasyonları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | İstasyon kodu |
| `name` | String | İstasyon adı |
| `type` | Enum | machine, workstation, assembly, manual |
| `warehouse_id` | → `warehouses.id` | Bulunduğu depo/alan |
| `supplier_id` | → `suppliers.id` | Dış kaynak tedarikçisi (fason için) |
| `capacity_per_hour` | Numeric | Saatlik kapasite |
| `hourly_cost` | Numeric | Saatlik maliyet |
| `setup_cost` | Numeric | Hazırlık maliyeti |

**M:M:** `work_station_alternatives` (alternatif istasyonlar)

---

#### `work_orders` — İş Emirleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `work_order_no` | String UNIQUE | İş emri numarası |
| `item_id` | → `items.id` | Üretilecek ürün |
| `bom_id` | → `bill_of_materials.id` | Kullanılan reçete |
| `status` | Enum | draft, pending, planned, released, in_progress, quality_check, completed, closed, cancelled |
| `priority` | Enum | low, normal, high, urgent |
| `planned_quantity` | Numeric | Planlanan miktar |
| `produced_quantity` | Numeric | Üretilen miktar |
| `scrap_quantity` | Numeric | Fire miktarı |
| `unit_id` | → `units.id` | Birim |
| `source_warehouse_id` | → `warehouses.id` | Malzeme çekme deposu |
| `target_warehouse_id` | → `warehouses.id` | Ürün giriş deposu |
| `planned_start`, `planned_end` | DateTime | Planlanan başlangıç/bitiş |
| `actual_start`, `actual_end` | DateTime | Gerçek başlangıç/bitiş |
| `parent_work_order_id` | → `work_orders.id` | Üst iş emri (self-FK, alt üretim için) |
| `production_plan_line_id` | → `production_plan_lines.id` | MPS satırı |
| `created_by`, `released_by` | → `users.id` | Oluşturan/serbest bırakan kullanıcı |

---

#### `work_order_lines` — İş Emri Malzeme Satırları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `work_order_id` | → `work_orders.id` | İş emri |
| `bom_line_id` | → `bom_lines.id` | Kaynak reçete satırı |
| `item_id` | → `items.id` | Malzeme |
| `planned_quantity` | Numeric | Planlanan miktar |
| `issued_quantity` | Numeric | Çekilen miktar |
| `unit_id` | → `units.id` | Birim |
| `warehouse_id` | → `warehouses.id` | Malzeme çekme deposu |

---

#### `work_order_operations` — İş Emri Operasyonları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `work_order_id` | → `work_orders.id` | İş emri |
| `bom_operation_id` | → `bom_operations.id` | Kaynak operasyon |
| `work_station_id` | → `work_stations.id` | İş istasyonu |
| `status` | Enum | waiting, pending, in_progress, completed, paused, cancelled |
| `sequence` | Integer | İşlem sırası |
| `planned_start`, `planned_end` | DateTime | Planlanan süreler |
| `actual_start`, `actual_end` | DateTime | Gerçek süreler |
| `setup_time_actual` | Integer | Gerçek hazırlık süresi (dk) |
| `run_time_actual` | Numeric | Gerçek çalışma süresi |
| `purchase_order_id` | → `purchase_orders.id` | Fason sipariş (dış kaynak için) |

---

#### `work_order_operation_personnel` — Operasyon Personeli

| Alan | Tür | Açıklama |
|------|-----|---------|
| `operation_id` | → `work_order_operations.id` | Operasyon |
| `user_id` | → `users.id` | Kullanıcı |
| `employee_id` | → `employees.id` | Çalışan |
| `start_time`, `end_time` | DateTime | Çalışma süreleri |

---

#### `production_downtimes` — Üretim Duruşları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `work_order_id` | → `work_orders.id` | İş emri |
| `operation_id` | → `work_order_operations.id` | Operasyon |
| `work_station_id` | → `work_stations.id` | İş istasyonu |
| `reason` | Enum | breakdown, setup, material_wait, op_absence, power_failure, meal_break, quality_issue, other |
| `start_time`, `end_time` | DateTime | Duruş başlangıç/bitiş |
| `duration_minutes` | Integer | Toplam süre (dk) |
| `notes` | Text | Açıklama |

---

#### `production_plans` — Üretim Planları (MPS)

| Alan | Tür | Açıklama |
|------|-----|---------|
| `plan_no` | String UNIQUE | Plan numarası |
| `name` | String | Plan adı |
| `plan_start`, `plan_end` | Date | Planlama dönemi |
| `status` | Enum | draft, approved, released, completed, cancelled |
| `approved_by` | → `users.id` | Onaylayan kullanıcı |

---

#### `production_plan_lines` — Üretim Planı Satırları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `plan_id` | → `production_plans.id` | Üretim planı |
| `item_id` | → `items.id` | Üretilecek ürün |
| `planned_quantity` | Numeric | Planlanan miktar |
| `planned_date` | Date | Planlanan tarih |
| `sales_order_id` | → `sales_orders.id` | Kaynak satış siparişi |
| `work_order_id` | → `work_orders.id` | Oluşturulan iş emri |

---

### 13.8 MRP (Material Requirements Planning)

#### `mrp_runs` — MRP Hesaplama Oturumları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `run_no` | String UNIQUE | Hesaplama numarası |
| `run_date` | DateTime | Çalıştırma zamanı |
| `planning_horizon_days` | Integer | Planlama ufku (gün) |
| `status` | Enum | running, completed, failed |
| `created_by` | → `users.id` | Tetikleyen kullanıcı |

---

#### `mrp_lines` — MRP Hesaplama Sonuçları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `mrp_run_id` | → `mrp_runs.id` | MRP oturumu |
| `item_id` | → `items.id` | Stok kartı |
| `requirement_date` | Date | Gereksinim tarihi |
| `gross_requirement` | Numeric | Brüt gereksinim |
| `scheduled_receipts` | Numeric | Planlı girişler (açık sipariş) |
| `projected_on_hand` | Numeric | Tahmini eldeki stok |
| `net_requirement` | Numeric | Net gereksinim |
| `planned_order_receipt` | Numeric | Planlı sipariş miktarı |
| `suggestion_type` | Enum | PURCHASE_ORDER, WORK_ORDER, TRANSFER |
| `is_processed` | Boolean | İşleme alındı mı |

---

### 13.9 Muhasebe (Accounting)

#### `accounts` — Hesap Planı

Türkiye Tekdüzen Hesap Planı'na uygun hiyerarşik hesap kartları.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String(20) UNIQUE | Hesap kodu (100, 120.01, 600.01.001) |
| `name` | String(200) | Hesap adı |
| `account_type` | Enum | asset, liability, equity, revenue, expense, cost |
| `parent_id` | → `accounts.id` | Üst hesap (self-FK hiyerarşi) |
| `level` | Integer | Seviye (1=Ana grup, 2=Alt grup, 3=Detay) |
| `is_detail` | Boolean | Hareket yapılabilir hesap mı |
| `opening_debit` | Numeric(18,2) | Açılış borç bakiyesi |
| `opening_credit` | Numeric(18,2) | Açılış alacak bakiyesi |

**Bakiye hesaplama kuralı:**
- Varlık ve gider hesapları: `bakiye = (açılış_borç - açılış_alacak) + (borç - alacak)`
- Borç, özkaynak ve gelir hesapları: `bakiye = (açılış_alacak - açılış_borç) + (alacak - borç)`

---

#### `fiscal_periods` — Mali Dönemler

| Alan | Tür | Açıklama |
|------|-----|---------|
| `year` | Integer | Yıl |
| `month` | Integer | Ay |
| `name` | String | Dönem adı ("Ocak 2026") |
| `is_closed` | Boolean | Dönem kapatıldı mı |
| `closed_at` | DateTime | Kapanış zamanı |
| `closed_by` | → `users.id` | Kapatan kullanıcı |

UNIQUE: `(year, month)`

---

#### `journal_entries` — Yevmiye Fişleri

Her çift taraflı muhasebe kaydının başlığı. **Kural: SUM(debit) = SUM(credit)**

| Alan | Tür | Açıklama |
|------|-----|---------|
| `entry_no` | String UNIQUE | Fiş numarası (YV-2026-00001) |
| `entry_date` | Date | Fiş tarihi |
| `description` | String | Açıklama |
| `status` | Enum | draft, posted, cancelled |
| `reference_type` | String | Belge türü (invoice, payment, payroll…) |
| `reference_id` | Integer | Belge id'si |
| `created_by` | → `users.id` | Oluşturan |
| `posted_by` | → `users.id` | Deftere işleyen |
| `cancelled_by` | → `users.id` | İptal eden |

---

#### `journal_entry_lines` — Yevmiye Fiş Satırları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `journal_entry_id` | → `journal_entries.id` | Fiş |
| `account_id` | → `accounts.id` | Hesap |
| `debit` | Numeric(18,2) | Borç tutarı |
| `credit` | Numeric(18,2) | Alacak tutarı |
| `line_order` | Integer | Satır sırası |
| `description` | String | Satır açıklaması |
| `cost_center` | String | Maliyet merkezi |

---

#### `budgets` — Bütçeler

| Alan | Tür | Açıklama |
|------|-----|---------|
| `name` | String | Bütçe adı |
| `period_year` | Integer | Bütçe yılı |
| `start_date`, `end_date` | Date | Bütçe dönemi |
| `status` | Enum | draft, approved, active, closed |
| `total_amount` | Numeric | Toplam bütçe tutarı |
| `created_by` | → `users.id` | Oluşturan kullanıcı |

---

#### `budget_lines` — Bütçe Satırları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `budget_id` | → `budgets.id` | Bütçe |
| `account_id` | → `accounts.id` | Hesap |
| `planned_amount` | Numeric | Planlanan tutar |
| `actual_amount` | Numeric | Gerçekleşen tutar (hesaplanan) |

---

### 13.10 Finans (Finance)

#### `account_transactions` — Cari Hesap Hareketleri

Müşteri ve tedarikçi cari hesaplarındaki tüm borç/alacak hareketleri.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `transaction_no` | String UNIQUE | Hareket numarası |
| `transaction_date` | Date | Hareket tarihi |
| `transaction_type` | Enum | invoice, purchase_invoice, payment, receipt, opening, adjustment |
| `customer_id` | → `customers.id` (nullable) | Müşteri |
| `supplier_id` | → `suppliers.id` (nullable) | Tedarikçi |
| `invoice_id` | → `invoices.id` | Satış faturası |
| `purchase_invoice_id` | → `purchase_invoices.id` | Alış faturası |
| `receipt_id` | → `receipts.id` | Tahsilat |
| `payment_id` | → `payments.id` | Ödeme |
| `journal_entry_id` | → `journal_entries.id` | Muhasebe fişi |
| `debit` | Numeric(15,2) | Borç |
| `credit` | Numeric(15,2) | Alacak |
| `payment_method` | Enum | cash, bank_transfer, check, credit_card, promissory_note |
| `reference_no` | String | Çek no, dekont no vb. |

---

#### `receipts` — Tahsilatlar (Müşterilerden)

| Alan | Tür | Açıklama |
|------|-----|---------|
| `receipt_no` | String UNIQUE | Tahsilat numarası |
| `receipt_date` | Date | Tahsilat tarihi |
| `customer_id` | → `customers.id` | Müşteri |
| `amount` | Numeric(15,2) | Tahsilat tutarı |
| `currency` | String | Para birimi |
| `exchange_rate` | Numeric | Kur |
| `payment_method` | Enum | Ödeme yöntemi |
| `reference_no` | String | Referans no |
| `status` | Enum | pending, completed, cancelled |

---

#### `receipt_allocations` — Tahsilat Fatura Eşleştirmeleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `receipt_id` | → `receipts.id` | Tahsilat |
| `invoice_id` | → `invoices.id` | Fatura |
| `amount` | Numeric | Eşleştirilen tutar |

---

#### `payments` — Ödemeler (Tedarikçilere)

`receipts` tablosuyla simetrik yapı.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `payment_no` | String UNIQUE | Ödeme numarası |
| `payment_date` | Date | Ödeme tarihi |
| `supplier_id` | → `suppliers.id` | Tedarikçi |
| `amount` | Numeric(15,2) | Ödeme tutarı |
| `payment_method` | Enum | Ödeme yöntemi |
| `status` | Enum | pending, completed, cancelled |

---

#### `payment_allocations` — Ödeme Fatura Eşleştirmeleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `payment_id` | → `payments.id` | Ödeme |
| `reference_type` | String | Belge türü (purchase_invoice…) |
| `reference_id` | Integer | Belge id'si |
| `amount` | Numeric | Eşleştirilen tutar |

---

### 13.11 İnsan Kaynakları (HR)

#### `departments` — Departmanlar

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | Departman kodu |
| `name` | String | Departman adı |
| `parent_id` | → `departments.id` | Üst departman (self-FK hiyerarşi) |
| `level` | Integer | Hiyerarşi seviyesi |
| `manager_id` | → `employees.id` | Departman yöneticisi |

---

#### `positions` — Pozisyonlar/Unvanlar

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | Pozisyon kodu |
| `name` | String | Pozisyon adı |
| `department_id` | → `departments.id` | Bağlı departman |
| `min_salary` | Numeric | Minimum maaş |
| `max_salary` | Numeric | Maksimum maaş |

---

#### `employees` — Çalışanlar ⭐

| Alan | Tür | Açıklama |
|------|-----|---------|
| `employee_no` | String UNIQUE | Sicil numarası |
| `first_name`, `last_name` | String | Ad soyad |
| `tc_no` | String(11) UNIQUE | T.C. kimlik numarası |
| `birth_date` | Date | Doğum tarihi |
| `gender` | Enum | male, female, other |
| `marital_status` | String | Medeni durum |
| `department_id` | → `departments.id` | Departman |
| `position_id` | → `positions.id` | Pozisyon |
| `manager_id` | → `employees.id` | Yöneticisi (self-FK) |
| `shift_team_id` | → `shift_teams.id` | Vardiya ekibi |
| `user_id` | → `users.id` | Sistem kullanıcısı (nullable) |
| `hire_date` | Date | İşe giriş tarihi |
| `termination_date` | Date | İşten ayrılış tarihi |
| `employment_type` | Enum | full_time, part_time, contract, intern, temporary |
| `base_salary` | Numeric | Temel maaş |
| `sgk_no` | String | SGK sicil numarası |
| `bank_iban` | String | IBAN |

---

#### `leaves` — İzinler

| Alan | Tür | Açıklama |
|------|-----|---------|
| `employee_id` | → `employees.id` | Çalışan |
| `leave_type` | Enum | annual, sick, maternity, paternity, marriage, bereavement, unpaid, other |
| `start_date`, `end_date` | Date | İzin dönemi |
| `working_days` | Integer | İş günü sayısı |
| `status` | Enum | pending, approved, rejected, cancelled |
| `approved_by` | → `employees.id` | Onaylayan yönetici |
| `notes` | Text | Açıklama |

---

#### `attendances` — Devam Takibi (PDKS)

| Alan | Tür | Açıklama |
|------|-----|---------|
| `employee_id` | → `employees.id` | Çalışan |
| `date` | Date | Tarih |
| `check_in` | DateTime | Giriş zamanı |
| `check_out` | DateTime | Çıkış zamanı |
| `status` | Enum | present, absent, late, early_leave, on_leave, holiday |
| `overtime_hours` | Numeric | Fazla mesai saati |
| `notes` | String | Açıklama |

UNIQUE: `(employee_id, date)`

---

#### `payrolls` — Bordro

| Alan | Tür | Açıklama |
|------|-----|---------|
| `employee_id` | → `employees.id` | Çalışan |
| `period_year` | Integer | Bordrolu yıl |
| `period_month` | Integer | Bordrolu ay |
| `base_salary` | Numeric | Brüt maaş |
| `overtime_pay` | Numeric | Fazla mesai ücreti |
| `bonus` | Numeric | Prim |
| `deductions` | Numeric | Kesintiler |
| `sgk_employee` | Numeric | SGK işçi payı |
| `sgk_employer` | Numeric | SGK işveren payı |
| `income_tax` | Numeric | Gelir vergisi |
| `stamp_tax` | Numeric | Damga vergisi |
| `net_salary` | Numeric | Net maaş |
| `status` | Enum | draft, calculated, approved, paid |
| `journal_entry_id` | → `journal_entries.id` | Muhasebe fişi |

UNIQUE: `(employee_id, period_year, period_month)`

---

#### `leave_balances` — İzin Bakiyeleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `employee_id` | → `employees.id` | Çalışan |
| `year` | Integer | Yıl |
| `leave_type` | Enum | İzin türü |
| `carried_over` | Numeric | Devredilen gün |
| `entitled` | Numeric | Hak edilen gün |
| `used` | Numeric | Kullanılan gün |
| `pending` | Numeric | Onay bekleyen gün |

---

#### `job_postings` — İş İlanları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | İlan kodu |
| `title` | String | İlan başlığı |
| `department_id` | → `departments.id` | Departman |
| `position_id` | → `positions.id` | Pozisyon |
| `status` | Enum | draft, published, closed |
| `closing_date` | Date | Başvuru son tarihi |
| `created_by` | → `employees.id` | Oluşturan |

---

#### `job_applications` — İş Başvuruları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | Başvuru kodu |
| `posting_id` | → `job_postings.id` | İlan |
| `first_name`, `last_name` | String | Aday adı |
| `email`, `phone` | String | İletişim |
| `status` | Enum | new, screening, interview, offer, hired, rejected |
| `cv_path` | String | CV dosya yolu |

---

#### `interviews` — Mülakatlar

| Alan | Tür | Açıklama |
|------|-----|---------|
| `application_id` | → `job_applications.id` | Başvuru |
| `interviewer_id` | → `employees.id` | Mülakat yapan |
| `scheduled_at` | DateTime | Planlanan zaman |
| `status` | Enum | scheduled, completed, cancelled |
| `score` | Integer | Puan (1-10) |
| `notes` | Text | Notlar |

---

### 13.12 Kalite Yönetimi (Quality)

#### `inspection_templates` — Kontrol Şablonları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | Şablon kodu |
| `name` | String | Şablon adı |
| `inspection_type` | Enum | incoming, in_process, final, periodic |
| `item_id` | → `items.id` (nullable) | Stok kartına özel şablon |

---

#### `inspection_criteria` — Kontrol Kriterleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `template_id` | → `inspection_templates.id` | Şablon |
| `name` | String | Kriter adı |
| `criteria_type` | Enum | visual, measurement, functional, document |
| `unit` | String | Ölçüm birimi |
| `tolerance_min`, `tolerance_max` | Numeric | Tolerans aralığı |
| `is_spc` | Boolean | SPC (İstatistiksel Proses Kontrolü) kriteri mi |

---

#### `inspections` — Kontroller

| Alan | Tür | Açıklama |
|------|-----|---------|
| `inspection_no` | String UNIQUE | Kontrol numarası |
| `template_id` | → `inspection_templates.id` | Şablon |
| `source_type` | String | Kaynak (goods_receipt, work_order, periodic…) |
| `source_id` | Integer | Kaynak belge id'si |
| `item_id` | → `items.id` | Kontrol edilen ürün |
| `lot_number` | String | Parti numarası |
| `quantity` | Numeric | Kontrol miktarı |
| `status` | Enum | pending, passed, failed, conditional |
| `inspector_id` | → `employees.id` | Kontrolü yapan |
| `inspection_date` | Date | Kontrol tarihi |

---

#### `inspection_results` — Kontrol Sonuçları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `inspection_id` | → `inspections.id` | Kontrol |
| `criteria_id` | → `inspection_criteria.id` | Kriter |
| `result_value` | String | Ölçüm sonucu |
| `is_passed` | Boolean | Kriteri geçti mi |
| `notes` | Text | Notlar |

---

#### `spc_observations` ve `spc_control_limits` — İstatistiksel Proses Kontrolü

```
spc_observations:
  result_id → inspection_results.id
  observation_no, value, timestamp

spc_control_limits:
  item_id → items.id
  criteria_id → inspection_criteria.id
  ucl (üst kontrol sınırı), lcl (alt kontrol sınırı), cl (orta hat)
```

---

#### `non_conformances` — Uygunsuzluk Raporları (NCR)

| Alan | Tür | Açıklama |
|------|-----|---------|
| `ncr_no` | String UNIQUE | NCR numarası |
| `inspection_id` | → `inspections.id` | Kaynak kontrol |
| `item_id` | → `items.id` | Uygunsuz ürün |
| `quantity` | Numeric | Uygunsuz miktar |
| `severity` | Enum | minor, major, critical |
| `disposition` | Enum | rework, scrap, use_as_is, return |
| `status` | Enum | open, analysis, action, verification, closed |
| `reported_by` | → `employees.id` | Rapor eden |
| `assigned_to` | → `employees.id` | Atanan kişi |
| `root_cause` | Text | Kök neden analizi |

---

#### `customer_complaints` — Müşteri Şikayetleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `complaint_no` | String UNIQUE | Şikayet numarası |
| `customer_id` | → `customers.id` | Müşteri |
| `item_id` | → `items.id` | Şikayet konusu ürün |
| `category` | Enum | quality, delivery, service, documentation, other |
| `priority` | Enum | low, medium, high, critical |
| `status` | Enum | open, investigation, resolution, closed |
| `assigned_to` | → `employees.id` | Atanan kişi |
| `resolution_date` | Date | Çözüm tarihi |

---

#### `capas` — Düzeltici/Önleyici Faaliyetler

| Alan | Tür | Açıklama |
|------|-----|---------|
| `capa_no` | String UNIQUE | CAPA numarası |
| `capa_type` | Enum | corrective (düzeltici), preventive (önleyici) |
| `source` | Enum | ncr, audit, customer_complaint |
| `ncr_id` | → `non_conformances.id` | Kaynak NCR |
| `complaint_id` | → `customer_complaints.id` | Kaynak şikayet |
| `audit_id` | → `audits.id` | Kaynak denetim |
| `responsible_id` | → `employees.id` | Sorumlu kişi |
| `verified_by` | → `employees.id` | Doğrulayan |
| `due_date` | Date | Hedef tarih |
| `effectiveness_verified` | Boolean | Etkinlik doğrulandı mı |

---

### 13.13 Bakım (Maintenance)

#### `equipments` — Ekipmanlar

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | Ekipman kodu |
| `name` | String | Ekipman adı |
| `parent_id` | → `equipments.id` | Ana ekipman (self-FK, alt ekipman için) |
| `brand`, `model`, `serial_number` | String | Kimlik bilgileri |
| `criticality` | Enum | low, medium, high, critical |
| `current_status` | Enum | running, idle, maintenance, breakdown, decommissioned |
| `work_station_id` | → `work_stations.id` | Bağlı iş istasyonu |
| `supplier_id` | → `suppliers.id` | Tedarikçi/servis firması |
| `purchase_date` | Date | Satın alma tarihi |
| `warranty_expiry` | Date | Garanti bitiş tarihi |

---

#### `maintenance_work_orders` — Bakım İş Emirleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `order_no` | String UNIQUE | İş emri numarası |
| `request_id` | → `maintenance_requests.id` | Kaynak talep |
| `equipment_id` | → `equipments.id` | Ekipman |
| `maintenance_type` | Enum | preventive, corrective, predictive |
| `assigned_to_id` | → `users.id` | Atanan teknisyen |
| `checklist_id` | → `maintenance_checklists.id` | Kontrol listesi |
| `status` | Enum | open, in_progress, completed, cancelled |
| `start_time`, `end_time` | DateTime | Çalışma süresi |
| `downtime_minutes` | Integer | Ekipman duruş süresi |

---

#### `maintenance_plans` — Bakım Planları (Önleyici Bakım)

| Alan | Tür | Açıklama |
|------|-----|---------|
| `equipment_id` | → `equipments.id` | Ekipman |
| `frequency_type` | String | Periyot türü (daily, weekly, monthly, yearly) |
| `frequency_value` | Integer | Sıklık (her 3 ayda bir = 3) |
| `is_counter_based` | Boolean | Sayaç bazlı mı (km, çevrim sayısı) |
| `counter_interval` | Numeric | Sayaç aralığı |
| `checklist_id` | → `maintenance_checklists.id` | Kontrol listesi |
| `last_done_date` | Date | Son yapılan tarih |
| `next_due_date` | Date | Sonraki planlanan tarih |

---

### 13.14 Lojistik ve Sevkiyat (Shipping)

#### `vehicles` — Araçlar

| Alan | Tür | Açıklama |
|------|-----|---------|
| `plate_no` | String UNIQUE | Plaka numarası |
| `vehicle_type` | Enum | truck, van, pickup, motorcycle |
| `status` | Enum | available, on_route, maintenance, inactive |
| `capacity_kg` | Numeric | Yük kapasitesi (kg) |
| `capacity_m3` | Numeric | Hacim kapasitesi (m³) |
| `brand`, `model` | String | Araç bilgileri |

---

#### `drivers` — Sürücüler

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | Sürücü kodu |
| `name` | String | Sürücü adı |
| `phone` | String | Telefon |
| `license_type` | String | Ehliyet sınıfı |
| `license_expiry` | Date | Ehliyet bitiş tarihi |
| `default_vehicle_id` | → `vehicles.id` | Varsayılan araç |
| `status` | Enum | available, on_route, off_duty |

---

#### `shipments` — Sevkiyatlar

| Alan | Tür | Açıklama |
|------|-----|---------|
| `shipment_no` | String UNIQUE | Sevkiyat numarası |
| `vehicle_id` | → `vehicles.id` | Araç |
| `driver_id` | → `drivers.id` | Sürücü |
| `status` | Enum | draft, loading, in_transit, delivered, returned |
| `departure_time`, `arrival_time` | DateTime | Çıkış/varış zamanı |
| `in_transit_warehouse_id` | → `warehouses.id` | Transit depo |
| `total_weight` | Numeric | Toplam yük (kg) |

---

#### `shipment_items` — Sevkiyat Kalemleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `shipment_id` | → `shipments.id` | Sevkiyat |
| `delivery_note_id` | → `delivery_notes.id` | İrsaliye |

---

#### `transport_units` — Taşıma Birimleri (SSCC/Palet)

| Alan | Tür | Açıklama |
|------|-----|---------|
| `sscc` | String UNIQUE | SSCC kodu (18 haneli GS1 kodu) |
| `unit_type` | Enum | pallet, box, container |
| `status` | Enum | empty, in_use, shipped, received |
| `warehouse_id` | → `warehouses.id` | Bulunduğu depo |
| `location_id` | → `warehouse_locations.id` | Lokasyon |

---

#### `transport_unit_items` — Taşıma Birimi İçerikleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `transport_unit_id` | → `transport_units.id` | Taşıma birimi |
| `item_id` | → `items.id` | Stok kartı |
| `unit_id` | → `units.id` | Birim |
| `quantity` | Numeric | Miktar |
| `lot_number` | String | Parti numarası |
| `serial_number` | String | Seri numarası |
| `added_by` | → `users.id` | Ekleyen kullanıcı |

---

### 13.15 İzlenebilirlik (Traceability)

#### `lots` — Parti Numaraları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `lot_number` | String UNIQUE | Parti numarası |
| `product_id` | → `items.id` | Ürün |
| `status` | Enum | active, quarantine, released, consumed, expired |
| `work_order_id` | → `work_orders.id` | Üretim iş emri (üretimden oluşanlar için) |
| `purchase_order_id` | → `purchase_orders.id` | Satınalma siparişi (alımdan oluşanlar için) |
| `expiry_date` | Date | Son kullanma tarihi |
| `warehouse_id` | → `warehouses.id` | Depo |
| `location_id` | → `warehouse_locations.id` | Lokasyon |
| `quantity` | Numeric | Mevcut miktar |

---

#### `serial_numbers` — Seri Numaraları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `serial` | String UNIQUE | Seri numarası |
| `product_id` | → `items.id` | Ürün |
| `lot_id` | → `lots.id` | Bağlı lot |
| `status` | Enum | in_stock, sold, in_service, returned, scrapped |
| `customer_id` | → `customers.id` | Satıldığı müşteri |
| `work_order_id` | → `work_orders.id` | Üretim iş emri |
| `sale_date` | Date | Satış tarihi |

---

#### `trace_links` — İzleme Zinciri

Bir partinin hangi partilerden üretildiğini/dönüştürüldüğünü gösterir. İleri/geri izleme için kullanılır.

| Alan | Tür | Açıklama |
|------|-----|---------|
| `parent_lot_id` | → `lots.id` | Üst parti (gelen malzeme) |
| `child_lot_id` | → `lots.id` | Alt parti (üretilen ürün) |
| `work_order_id` | → `work_orders.id` | Dönüşüm iş emri |
| `quantity_used` | Numeric | Kullanılan miktar |

---

### 13.16 CRM

#### `leads` — Potansiyel Müşteriler

| Alan | Tür | Açıklama |
|------|-----|---------|
| `first_name`, `last_name` | String | Kişi adı |
| `company_name` | String | Şirket adı |
| `email`, `phone` | String | İletişim |
| `status` | Enum | new, contacted, qualified, unqualified, converted |
| `source` | Enum | website, referral, cold_call, email, social_media, exhibition |
| `assigned_to_id` | → `users.id` | Atanan kullanıcı |
| `notes` | Text | Notlar |

---

#### `opportunities` — Satış Fırsatları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `name` | String | Fırsat adı |
| `lead_id` | → `leads.id` | Kaynak müşteri adayı |
| `customer_id` | → `customers.id` | Dönüşen müşteri |
| `stage` | Enum | qualification, proposal, negotiation, closed_won, closed_lost |
| `expected_revenue` | Numeric | Beklenen gelir |
| `probability` | Integer | Kazanma olasılığı (%) |
| `closing_date` | Date | Beklenen kapanış tarihi |
| `assigned_to_id` | → `users.id` | Atanan kullanıcı |

---

#### `activities` — CRM Aktiviteleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `subject` | String | Aktivite konusu |
| `activity_type` | Enum | call, email, meeting, demo, follow_up, other |
| `lead_id` | → `leads.id` | İlgili lead |
| `opportunity_id` | → `opportunities.id` | İlgili fırsat |
| `customer_id` | → `customers.id` | İlgili müşteri |
| `due_date` | DateTime | Hedef tarih |
| `is_done` | Boolean | Tamamlandı mı |
| `assigned_to_id` | → `users.id` | Sorumlu kullanıcı |

---

### 13.17 Proje Yönetimi

#### `projects` — Projeler

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | Proje kodu |
| `name` | String | Proje adı |
| `customer_id` | → `customers.id` | Müşteri (nullable) |
| `status` | Enum | planning, active, on_hold, completed, cancelled |
| `start_date`, `end_date` | Date | Proje dönemi |
| `budget` | Numeric | Bütçe |
| `currency_id` | → `currencies.id` | Para birimi |
| `manager_id` | → `employees.id` | Proje yöneticisi |

---

#### `project_tasks` — Görevler

| Alan | Tür | Açıklama |
|------|-----|---------|
| `project_id` | → `projects.id` | Proje |
| `title` | String | Görev başlığı |
| `status` | Enum | todo, in_progress, review, done |
| `priority` | Enum | low, medium, high, critical |
| `assigned_to` | → `employees.id` | Atanan çalışan |
| `start_date`, `end_date` | Date | Görev dönemi |
| `estimated_hours` | Numeric | Tahmini süre |
| `actual_hours` | Numeric | Gerçekleşen süre |
| `progress` | Integer | Tamamlanma % |

---

#### `task_dependencies` — Görev Bağımlılıkları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `task_id` | → `project_tasks.id` | Görev |
| `predecessor_id` | → `project_tasks.id` | Önceki görev |
| `dependency_type` | Enum | FS (Finish-Start), SS, FF, SF |
| `lag_days` | Integer | Gecikme günü |

---

### 13.18 E-Fatura

#### `einvoices` — E-Fatura Kayıtları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `uuid` | String UNIQUE | UBL UUID |
| `direction` | Enum | OUTGOING (giden), INCOMING (gelen) |
| `type` | Enum | EFATURA, EARSIVA |
| `status` | Enum | DRAFT, SENT, ACCEPTED, REJECTED, CANCELLED |
| `invoice_id` | → `invoices.id` | Satış faturası |
| `purchase_invoice_id` | → `purchase_invoices.id` | Alış faturası |
| `sender_vkn` | String | Gönderen VKN |
| `receiver_vkn` | String | Alıcı VKN |
| `xml_content` | Text | Tam UBL 2.1 XML içeriği |
| `ettn` | String | E-Fatura takip numarası |
| `sent_at` | DateTime | Gönderim zamanı |
| `response_code` | String | GİB yanıt kodu |

---

### 13.19 Sabit Kıymetler

#### `fixed_assets` — Sabit Kıymetler

| Alan | Tür | Açıklama |
|------|-----|---------|
| `name` | String | Kıymet adı |
| `category` | Enum | land, building, machinery, vehicle, furniture, it_equipment, other |
| `status` | Enum | active, disposed, under_maintenance |
| `purchase_date` | Date | Satın alma tarihi |
| `purchase_price` | Numeric | Satın alma bedeli |
| `depreciation_method` | Enum | straight_line, declining_balance |
| `useful_life_years` | Integer | Faydalı ömür (yıl) |
| `salvage_value` | Numeric | Hurda değeri |
| `current_value` | Numeric | Güncel defter değeri |
| `supplier_id` | → `suppliers.id` | Satın alınan tedarikçi |

---

#### `depreciation_entries` — Amortisman Kayıtları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `fixed_asset_id` | → `fixed_assets.id` | Sabit kıymet |
| `period` | String | Dönem (2026-01) |
| `amount` | Numeric | Dönem amortismanı |
| `accumulated_amount` | Numeric | Birikmiş amortisman |
| `book_value` | Numeric | Kalan defter değeri |

---

### 13.20 İadeler

#### `return_orders` — İade Emirleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | İade kodu |
| `type` | Enum | SALES_RETURN (satış iadesi), PURCHASE_RETURN (alış iadesi) |
| `status` | Enum | draft, approved, completed, cancelled |
| `reason` | Enum | defective, wrong_item, overdelivery, customer_request, other |
| `customer_id` | → `customers.id` | Müşteri (satış iadesi için) |
| `supplier_id` | → `suppliers.id` | Tedarikçi (alış iadesi için) |
| `related_sale_order_id` | → `sales_orders.id` | İlgili satış siparişi |
| `related_purchase_order_id` | → `purchase_orders.id` | İlgili satınalma siparişi |
| `stock_movement_id` | → `stock_movements.id` | Oluşan stok hareketi |
| `created_by`, `approved_by` | → `users.id` | Kullanıcılar |

---

### 13.21 Teklif Talebi (RFQ)

#### `rfqs` — Teklif Talepleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `rfq_no` | String UNIQUE | Teklif talebi numarası |
| `title` | String | Başlık |
| `date` | Date | Talep tarihi |
| `deadline` | Date | Tekliflerin son tarihi |
| `status` | Enum | draft, sent, received, evaluated, closed |

---

#### `rfq_items` — Teklif Talebi Kalemleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `rfq_id` | → `rfqs.id` | Teklif talebi |
| `item_id` | → `items.id` | Stok kartı |
| `unit_id` | → `units.id` | Birim |
| `quantity` | Numeric | Talep miktarı |
| `purchase_request_item_id` | → `purchase_request_items.id` | Kaynak satınalma talebi |

---

#### `supplier_offers` ve `supplier_offer_items` — Tedarikçi Teklifleri

```
supplier_offers:
  rfq_id → rfqs.id
  supplier_id → suppliers.id
  offer_date, status, grand_total

supplier_offer_items:
  offer_id → supplier_offers.id
  rfq_item_id → rfq_items.id
  quantity, unit_price, delivery_date
```

---

### 13.22 Mesajlaşma (Messaging)

#### `conversations` — Konuşmalar

| Alan | Tür | Açıklama |
|------|-----|---------|
| `title` | String | Başlık (grup sohbetleri için) |
| `conversation_type` | Enum | direct (1:1), group, department, record (kayda bağlı), system |
| `department_id` | → `departments.id` | Departman kanalı için |
| `entity_type` | String | Polimorfik tablo adı (work_orders, sales_orders…) |
| `entity_id` | Integer | Polimorfik kayıt id'si |
| `created_by` | → `users.id` | Oluşturan kullanıcı |
| `last_message_at` | DateTime | Son mesaj zamanı |
| `last_message_preview` | String | Son mesaj önizlemesi |
| `is_pinned` | Boolean | Sabitlenmiş mi |

---

#### `conversation_participants` — Katılımcılar

| Alan | Tür | Açıklama |
|------|-----|---------|
| `conversation_id` | → `conversations.id` | Konuşma |
| `user_id` | → `users.id` | Kullanıcı |
| `role` | String | Rol (admin, member) |
| `last_read_at` | DateTime | Son okuma zamanı |
| `unread_count` | Integer | Okunmamış mesaj sayısı |
| `is_muted` | Boolean | Bildirimler kapatıldı mı |

---

#### `messages` — Mesajlar

| Alan | Tür | Açıklama |
|------|-----|---------|
| `conversation_id` | → `conversations.id` | Konuşma |
| `sender_id` | → `users.id` | Gönderen |
| `content` | Text | Mesaj içeriği |
| `reply_to_id` | → `messages.id` | Yanıtlanan mesaj (self-FK) |
| `priority` | Enum | low, normal, high, urgent |
| `is_deleted` | Boolean | Silindi mi (soft delete) |
| `deleted_at` | DateTime | Silinme zamanı |

---

#### `message_attachments` — Mesaj Ekleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `message_id` | → `messages.id` | Mesaj |
| `file_path` | String | Dosya yolu |
| `file_name` | String | Dosya adı |
| `file_size` | Integer | Boyut (byte) |
| `mime_type` | String | MIME türü |

---

#### `message_stars` — Yıldızlı Mesajlar

| Alan | Tür | Açıklama |
|------|-----|---------|
| `message_id` | → `messages.id` | Mesaj |
| `user_id` | → `users.id` | Yıldızlayan kullanıcı |

UNIQUE: `(message_id, user_id)`

---

#### `notification_preferences` — Bildirim Tercihleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `user_id` | → `users.id` | Kullanıcı |
| `event_type` | String | Olay türü (message_received, mention…) |
| `in_app` | Boolean | Uygulama içi bildirim |
| `in_message` | Boolean | Mesaj olarak bildirim |
| `quiet_start`, `quiet_end` | Time | Sessiz saat aralığı |

UNIQUE: `(user_id, event_type)`

---

### 13.23 Vardiya ve Takvim

#### `shift_teams` — Vardiya Ekipleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | Ekip kodu |
| `name` | String | Ekip adı |
| `color` | String | Renk kodu (UI'da göstermek için) |

---

#### `production_shifts` — Vardiyalar

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | Vardiya kodu (A, B, C…) |
| `name` | String | Vardiya adı |
| `start_time` | Time | Başlangıç saati |
| `end_time` | Time | Bitiş saati |
| `break_minutes` | Integer | Toplam mola süresi (dk) |

---

#### `production_holidays` — Tatil Günleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `date` | Date UNIQUE | Tarih |
| `name` | String | Tatil adı |
| `is_half_day` | Boolean | Yarım gün mü |

---

#### `workstation_schedules` — İş İstasyonu Takvimleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `work_station_id` | → `work_stations.id` | İş istasyonu |
| `day_of_week` | Integer | Gün (0=Pazartesi, 6=Pazar) |
| `shift_id` | → `production_shifts.id` | Vardiya |
| `is_working` | Boolean | Çalışıyor mu |

---

#### `rotation_patterns` ve `rotation_schedules` — Vardiya Rotasyon Şemaları

```
rotation_patterns:
  code (UNIQUE), name, cycle_days, shifts_per_day

rotation_schedules:
  pattern_id → rotation_patterns.id
  day_in_cycle, shift_id → production_shifts.id
  team_id → shift_teams.id
```

---

### 13.24 İleri Planlama (APS)

#### `aps_scenarios` — APS Senaryoları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `name` | String | Senaryo adı |
| `is_active` | Boolean | Aktif senaryo mu |
| `start_date`, `end_date` | Date | Planlama dönemi |
| `settings` | JSON | APS parametreleri |

---

#### `aps_planned_tasks` — Planlanmış Görevler

| Alan | Tür | Açıklama |
|------|-----|---------|
| `scenario_id` | → `aps_scenarios.id` | Senaryo |
| `work_order_id` | → `work_orders.id` | İş emri |
| `operation_id` | → `work_order_operations.id` | Operasyon |
| `work_station_id` | → `work_stations.id` | İş istasyonu |
| `planned_start`, `planned_end` | DateTime | Planlanan süre |
| `is_locked` | Boolean | Kilitlendi mi (değiştirilemez) |

---

### 13.25 Sözleşmeler

#### `contracts` — Sözleşmeler

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | Sözleşme kodu |
| `contract_type` | Enum | sales, purchase, service, nda, other |
| `customer_id` | → `customers.id` | Müşteri (nullable) |
| `supplier_id` | → `suppliers.id` | Tedarikçi (nullable) |
| `start_date`, `end_date` | Date | Sözleşme dönemi |
| `status` | Enum | draft, active, expired, terminated |
| `total_amount` | Numeric | Sözleşme tutarı |
| `renewal_reminder_days` | Integer | Yenileme hatırlatma (gün) |

---

### 13.26 Eğitim

#### `trainings` — Eğitim Tanımları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `name` | String | Eğitim adı |
| `training_type` | Enum | internal, external, online |
| `duration_hours` | Numeric | Süre (saat) |
| `has_certificate` | Boolean | Sertifika verilecek mi |
| `certificate_validity_months` | Integer | Sertifika geçerlilik süresi |

---

#### `training_sessions` — Eğitim Oturumları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `training_id` | → `trainings.id` | Eğitim |
| `planned_date` | Date | Planlanan tarih |
| `status` | Enum | planned, in_progress, completed, cancelled |
| `instructor` | String | Eğitmen adı |
| `location` | String | Lokasyon |
| `max_participants` | Integer | Maksimum katılımcı |

---

#### `training_participants` — Katılımcılar

| Alan | Tür | Açıklama |
|------|-----|---------|
| `session_id` | → `training_sessions.id` | Oturum |
| `employee_id` | → `employees.id` | Çalışan |
| `attended` | Boolean | Katıldı mı |
| `score` | Numeric | Sınav puanı |
| `certificate_issued` | Boolean | Sertifika verildi mi |

---

#### `employee_certificates` — Çalışan Sertifikaları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `employee_id` | → `employees.id` | Çalışan |
| `name` | String | Sertifika adı |
| `issue_date` | Date | Veriliş tarihi |
| `expiry_date` | Date | Geçerlilik bitiş tarihi |
| `status` | Enum | valid, expired, revoked |
| `training_id` | → `trainings.id` | Bağlı eğitim (nullable) |

---

### 13.27 Performans Değerlendirmesi

#### `evaluation_periods` — Değerlendirme Dönemleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `name` | String | Dönem adı ("2026 Yılsonu") |
| `period_type` | Enum | quarterly, semi_annual, annual |
| `start_date`, `end_date` | Date | Dönem tarihleri |
| `is_active` | Boolean | Aktif dönem mi |

---

#### `performance_evaluations` — Performans Değerlendirmeleri

| Alan | Tür | Açıklama |
|------|-----|---------|
| `employee_id` | → `employees.id` | Değerlendirilen çalışan |
| `period_id` | → `evaluation_periods.id` | Dönem |
| `evaluator_id` | → `employees.id` | Değerlendiren yönetici |
| `status` | Enum | draft, self_evaluation, manager_evaluation, hr_review, completed |
| `self_rating` | Numeric(3,1) | Öz değerlendirme puanı |
| `manager_rating` | Numeric(3,1) | Yönetici değerlendirme puanı |
| `final_rating` | Numeric(3,1) | Kesinleşmiş puan |
| `hr_approved_by` | → `employees.id` | İK onaylayan |

---

### 13.28 Dashboard ve Sistem Tabloları

#### `dashboard_widgets` — Dashboard Widget Tanımları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `code` | String UNIQUE | Widget kodu |
| `name` | String | Widget adı |
| `widget_type` | String | Tür (chart, kpi, table…) |
| `default_width`, `default_height` | Integer | Varsayılan boyutlar |
| `config_schema` | JSON | Yapılandırma şeması |
| `required_permission` | String | Gerekli izin kodu |
| `allowed_roles` | JSON | İzin verilen roller |

---

#### `user_dashboard_layouts` ve `role_default_layouts` — Dashboard Düzenleri

```
user_dashboard_layouts:
  user_id → users.id (UNIQUE)
  layout (JSON)  ← kullanıcıya özel düzenleme

role_default_layouts:
  role_id → roles.id (UNIQUE)
  layout (JSON)  ← rol için varsayılan düzen
```

---

#### `documents` — Belge Yönetimi (DMS)

| Alan | Tür | Açıklama |
|------|-----|---------|
| `filename` | String | Orijinal dosya adı |
| `physical_name` | String | Sunucudaki dosya adı (UUID) |
| `file_path` | String | Tam dosya yolu |
| `mime_type` | String | MIME türü |
| `file_size` | Integer | Boyut (byte) |
| `created_by` | → `users.id` | Yükleyen kullanıcı |

---

#### `document_relations` — Belge-Kayıt İlişkisi (Polimorfik)

| Alan | Tür | Açıklama |
|------|-----|---------|
| `document_id` | → `documents.id` | Belge |
| `target_table` | String | İlgili tablo adı |
| `target_id` | Integer | İlgili kayıt id'si |
| `relation_type` | String | İlişki türü (attachment, reference…) |

---

#### `error_logs` — Hata Kayıtları

| Alan | Tür | Açıklama |
|------|-----|---------|
| `user_id` | → `users.id` | Hatayı tetikleyen kullanıcı |
| `module_name` | String | Modül adı |
| `screen_name` | String | Ekran/widget adı |
| `function_name` | String | Method adı |
| `error_type` | String | Exception sınıfı |
| `error_message` | String | Hata mesajı |
| `error_traceback` | Text | Tam traceback |
| `severity` | Enum | critical, error, warning, info |
| `is_resolved` | Boolean | Çözüldü mü |
| `resolved_by` | → `users.id` | Çözen kullanıcı |
| `resolved_at` | DateTime | Çözüm zamanı |

---

### 13.29 Kapsamlı İlişki Özeti

Aşağıdaki diagram tüm domain'lerin birbirine nasıl bağlandığını gösterir:

```
                    ┌──────────────┐
                    │     items    │ ← Merkezi tablo
                    └──────┬───────┘
          ┌─────────────────┼─────────────────────┐
          │                 │                     │
    ┌─────▼─────┐   ┌───────▼───────┐   ┌────────▼────────┐
    │  sales    │   │  purchasing   │   │   production    │
    │ (orders,  │   │ (PO, GR,      │   │ (BOM, work      │
    │  invoices)│   │  invoices)    │   │  orders, ops)   │
    └─────┬─────┘   └───────┬───────┘   └────────┬────────┘
          │                 │                     │
    ┌─────▼─────┐   ┌───────▼───────┐   ┌────────▼────────┐
    │ customers │   │   suppliers   │   │   traceability  │
    └─────┬─────┘   └───────┬───────┘   │ (lots, serials, │
          │                 │           │  trace_links)   │
    ┌─────▼─────────────────▼───────┐   └─────────────────┘
    │           finance             │
    │  (receipts, payments,         │
    │   account_transactions)       │
    └───────────────┬───────────────┘
                    │
    ┌───────────────▼───────────────┐
    │           accounting          │
    │  (accounts, journal_entries,  │
    │   budgets, fiscal_periods)    │
    └───────────────────────────────┘

    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │     hr       │    │   quality    │    │  maintenance │
    │ (employees,  │    │ (inspections,│    │ (equipments, │
    │  payroll,    │    │  ncr, capa)  │    │  work orders)│
    │  leaves)     │    └──────┬───────┘    └──────────────┘
    └──────┬───────┘           │
           │                   │
    ┌──────▼───────────────────▼────┐
    │             users             │ ← Auth merkezi
    │   (roles, permissions,        │
    │    sessions, audit_logs)      │
    └───────────────────────────────┘

    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │   shipping   │    │  messaging   │    │     crm      │
    │ (vehicles,   │    │(conversations│    │ (leads,      │
    │  drivers,    │    │ messages)    │    │  opportunities│
    │  shipments)  │    └──────────────┘    └──────────────┘
    └──────────────┘
```

---

*Bu döküman `docs/developer-guide.md` dosyasında saklanır. Yeni modül veya önemli mimari değişikliklerde güncellenmesi gerekir.*
