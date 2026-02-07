# Akilli Is ERP - Gelistirme Yol Haritasi

> **Olusturma Tarihi:** 2026-02-07
> **Guncelleme:** 2026-02-07
> **Mevcut Durum:** 22 modul, ~180K satir kod, ~200 tablo
> **Hedef:** 25 yeni modul/ozellik, 63 yeni tablo, ~301 yeni dosya
> **Sorumluluk:** Tum gelistirme adimlari Claude tarafindan yapilacaktir.

---

## Modul Gruplari

| Grup | Moduller | Modul Sayisi |
|------|----------|--------------|
| A. Yasal Uyum & Muhasebe | e-Fatura, Sabit Kiymet, KDV & Vergi, Maliyet Muhasebesi, Butce | 5 |
| B. Satis & Tedarik | Iade Yonetimi, Sozlesme, RFQ, Tedarikci Degerlendirme | 4 |
| C. Uretim & Kalite | Lot/Seri Izlenebilirlik, APS Motoru, SPC | 3 |
| D. IK & Organizasyon | Ise Alim, Proje Yonetimi | 2 |
| E. Altyapi & Platform | Test Altyapisi, Workflow Tasarimcisi, Bildirim Motoru, REST API, Cok Sirketli Yapi | 5 |
| F. Dis Entegrasyon | EDI, Web Arayuz, Mobil Uygulama, Portal | 4 |
| G. Analiz & Bakim | BI Raporlama, Kestirimci Bakim | 2 |
| **TOPLAM** | | **25** |

### Bagimlilik Haritasi

```
e-Fatura ← Satis/SatinAlma (mevcut)
Sabit Kiymet ← Muhasebe (mevcut)
Maliyet Muh. ← Muhasebe + Uretim (mevcut)
Iade ← Satis + SatinAlma + Stok (mevcut)
REST API ← Tum servisler (mevcut)
Web UI ← REST API
Mobil ← REST API
Portal ← Web UI + REST API
APS ← Uretim + Planlama (mevcut)
SPC ← Kalite (mevcut)
Kestirimci Bakim ← Bakim (mevcut)
```

### Onerilen Uygulama Sirasi

```
1. Test Altyapisi (tum diger modullerin temelini olusturur)
2. e-Fatura / Sabit Kiymet / KDV & Vergi (yasal zorunluluk)
3. Maliyet Muhasebesi / Butce (finansal olgunluk)
4. Iade / Sozlesme / RFQ / Tedarikci Deg. (operasyonel derinlik)
5. Lot/Seri / APS / SPC (uretim derinlik)
6. Ise Alim / Proje Yonetimi (IK/organizasyon)
7. Workflow / Bildirim / Cok Sirketli (platform)
8. REST API → Web → Mobil → Portal (entegrasyon)
9. EDI / BI / Kestirimci Bakim (ileri moduller)
```

---

# A. YASAL UYUM & MUHASEBE MODULLERI

---

## A1. e-Fatura / e-Arsiv / e-Irsaliye

**Oncelik:** KRITIK (Yasal zorunluluk)
**Tahmini Efor:** 4-6 hafta

### Dosya Yapisi

```
modules/einvoice/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── base.py              # EInvoiceService
│   ├── integrator_client.py  # Ozel Entegrator API istemcisi
│   ├── ubl_builder.py       # UBL-TR XML olusturucu
│   ├── xml_validator.py     # lxml ile XSD validasyon
│   └── gib_registry.py      # VKN kayit listesi cache
├── views/
│   ├── __init__.py
│   ├── einvoice_module.py   # Ana modul sayfasi
│   ├── outgoing_list.py     # Giden faturalar listesi
│   ├── incoming_list.py     # Gelen faturalar listesi
│   ├── einvoice_detail.py   # Fatura detay/onizleme
│   ├── settings_module.py   # Entegrator ayarlari
│   └── status_monitor.py    # Durum takip paneli
└── templates/
    ├── invoice_ubl.xml.j2   # e-Fatura Jinja2 sablonu
    └── despatch_ubl.xml.j2  # e-Irsaliye sablonu
```

### Veritabani Modeli

```python
# database/models/einvoice.py

class EInvoiceDirection(str, Enum):
    OUTGOING = "outgoing"
    INCOMING = "incoming"

class EInvoiceType(str, Enum):
    EINVOICE = "einvoice"       # e-Fatura (kayitli mukelleflere)
    EARCHIVE = "earchive"       # e-Arsiv (kayitsiz mukelleflere)
    EDESPATCH = "edespatch"     # e-Irsaliye

class EInvoiceStatus(str, Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ERROR = "error"

class EInvoice(BaseModel):
    __tablename__ = 'einvoices'
    uuid: str                   # GIB UUID (GUID)
    invoice_id: int             # FK -> invoices / purchase_invoices
    direction: EInvoiceDirection
    type: EInvoiceType
    status: EInvoiceStatus
    ettn: str                   # Evrensel Tekil Tanimlama No
    invoice_number: str         # GIB fatura no (ABC2026000001)
    series: str                 # Fatura serisi
    profile: str                # TEMELFATURA / TICARIFATURA
    sender_vkn: str
    receiver_vkn: str
    xml_content: Text           # UBL-TR XML
    pdf_content: LargeBinary
    envelope_id: str
    sent_at: DateTime
    response_at: DateTime
    error_message: str
    gib_response: JSON

class EInvoiceSeries(BaseModel):
    __tablename__ = 'einvoice_series'
    series_prefix: str          # ABC, XYZ
    type: EInvoiceType
    last_number: int
    year: int
    is_active: bool

class EInvoiceSettings(BaseModel):
    __tablename__ = 'einvoice_settings'
    integrator: str             # foriba, efinans, logo
    api_url: str
    api_key: str
    username: str
    password_encrypted: str
    sender_alias: str
    default_series: str
    auto_send: bool
```

### Servis Metotlari

```python
class EInvoiceService:
    # Giden
    create_from_invoice(invoice_id) -> EInvoice
    create_from_purchase(pinvoice_id) -> EInvoice
    build_ubl_xml(einvoice) -> str
    send_invoice(einvoice_id) -> bool
    batch_send(einvoice_ids) -> Dict
    check_status(einvoice_id) -> EInvoiceStatus
    cancel_invoice(einvoice_id, reason) -> bool

    # Gelen
    fetch_incoming() -> List[EInvoice]
    accept_invoice(einvoice_id) -> bool
    reject_invoice(einvoice_id, reason) -> bool

    # e-Arsiv
    create_earchive(invoice_id) -> EInvoice
    generate_pdf(einvoice_id) -> bytes

    # e-Irsaliye
    create_edespatch(delivery_note_id) -> EInvoice

    # Seri
    get_next_number(series, type) -> str

    # Rapor
    get_monthly_summary(year, month) -> Dict
```

### Teknik Notlar

- **Format:** UBL-TR 1.2.1 (Jinja2 sablonla olusturulacak)
- **Validasyon:** lxml ile XSD kontrolu (lxml requirements.txt'ye eklenecek)
- **Iletisim:** Ozel Entegrator REST API (httpx - zaten mevcut)
- **KDV Oranlari:** %20 (genel), %10 (indirimli), %1 (super indirimli)
- **Karar Akisi:** VKN kayitli → e-Fatura, kayitsiz → e-Arsiv
- **ONEMLI:** Mevcut tax_rate default 18 → 20'ye guncellenecek

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | `database/models/einvoice.py` + Alembic migration | 0.5 gun |
| 2 | UBL-TR Jinja2 sablonlari (invoice + despatch) | 2 gun |
| 3 | `ubl_builder.py` - XML olusturma + XSD validasyon | 1 gun |
| 4 | `integrator_client.py` - REST API istemcisi (httpx) | 1.5 gun |
| 5 | `gib_registry.py` - VKN kayit cache | 0.5 gun |
| 6 | `base.py` - EInvoiceService tum is mantigi | 2 gun |
| 7 | `einvoice_module.py` - Ana modul UI (QStackedWidget) | 1 gun |
| 8 | `outgoing_list.py` - Giden fatura listesi (BaseListPage) | 1 gun |
| 9 | `incoming_list.py` - Gelen fatura listesi | 1 gun |
| 10 | `settings_module.py` - Entegrator ayar ekrani | 0.5 gun |
| 11 | `status_monitor.py` - Durum takip paneli | 0.5 gun |
| 12 | Satis fatura onay butonuna e-Fatura hook | 0.5 gun |
| 13 | Irsaliye sevk butonuna e-Irsaliye hook | 0.5 gun |
| 14 | Menu + ikon kaydi (menu_data.py, icons.py) | 0.25 gun |
| 15 | Test: XML sema + servis akis testleri | 1 gun |
| 16 | GIB test ortaminda entegrasyon testi | 1 gun |

---

## A2. Sabit Kiymet Yonetimi (Fixed Assets)

**Oncelik:** YUKSEK
**Tahmini Efor:** 3-4 hafta

### Dosya Yapisi

```
modules/assets/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── base.py              # AssetService
│   ├── depreciation.py      # DepreciationService
│   └── accounting_bridge.py # Muhasebe entegrasyonu
├── views/
│   ├── __init__.py
│   ├── asset_module.py      # Ana modul
│   ├── asset_form.py        # Kiymet kayit formu
│   ├── asset_list.py        # Kiymet listesi
│   ├── depreciation_module.py  # Amortisman isleme
│   ├── disposal_form.py     # Satis/hurda formu
│   └── reports_module.py    # Raporlar
```

### Veritabani Modeli

```python
# database/models/assets.py

class AssetStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DISPOSED = "disposed"
    SCRAPPED = "scrapped"
    TRANSFERRED = "transferred"

class DepreciationMethod(str, Enum):
    STRAIGHT_LINE = "straight_line"
    DECLINING_BALANCE = "declining"
    DOUBLE_DECLINING = "double_declining"

class AssetCategory(BaseModel):
    __tablename__ = 'asset_categories'
    code: str
    name: str
    useful_life_years: int
    depreciation_method: DepreciationMethod
    depreciation_rate: Numeric(5,2)
    account_asset_id: int       # 255.xx Demirbas
    account_depreciation_id: int # 257.xx Birikmis Amort.
    account_expense_id: int     # 770.xx Amort. Gideri
    is_active: bool

class FixedAsset(BaseModel):
    __tablename__ = 'fixed_assets'
    code: str                    # DMB2602-0001
    name: str
    description: str
    category_id: int             # FK -> asset_categories
    status: AssetStatus
    purchase_date: Date
    purchase_price: Numeric(14,2)
    purchase_invoice_id: int     # FK -> purchase_invoices
    supplier_id: int             # FK -> suppliers
    department_id: int           # FK -> departments
    employee_id: int             # FK -> employees (zimmet)
    location: str
    depreciation_method: DepreciationMethod
    useful_life_months: int
    salvage_value: Numeric(14,2)
    depreciation_start_date: Date
    accumulated_depreciation: Numeric(14,2)
    net_book_value: Numeric(14,2)
    disposal_date: Date
    disposal_amount: Numeric(14,2)
    disposal_reason: str
    barcode: str
    serial_number: str
    warranty_end: Date
    notes: Text

class DepreciationEntry(BaseModel):
    __tablename__ = 'depreciation_entries'
    asset_id: int               # FK -> fixed_assets
    period_date: Date           # Amortisman donemi (2026-01)
    amount: Numeric(14,2)
    accumulated: Numeric(14,2)
    net_book_value: Numeric(14,2)
    journal_entry_id: int       # FK -> journal_entries
    is_posted: bool
```

### Servis Metotlari

```python
class AssetService:
    create(data) -> FixedAsset
    update(id, data) -> FixedAsset
    get_by_id(id) -> FixedAsset
    get_all(filters) -> List[FixedAsset]
    generate_code(category_id) -> str
    dispose(id, amount, reason) -> FixedAsset
    transfer(id, new_dept, new_employee) -> FixedAsset
    get_by_barcode(barcode) -> FixedAsset

class DepreciationService:
    calculate_monthly(asset) -> Numeric
    calculate_straight_line(asset) -> Numeric
    calculate_declining(asset) -> Numeric
    run_monthly_depreciation(period_date) -> List[DepreciationEntry]
    run_for_asset(asset_id, period_date) -> DepreciationEntry
    get_schedule(asset_id) -> List[DepreciationEntry]
    post_to_accounting(entries) -> bool
    reverse_entry(entry_id) -> bool
    get_yearly_summary(year) -> Dict
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | `database/models/assets.py` + Alembic migration | 0.5 gun |
| 2 | `base.py` - AssetService CRUD + kod uretimi | 1 gun |
| 3 | `depreciation.py` - 3 amortisman metodu hesaplama | 2 gun |
| 4 | `accounting_bridge.py` - Muhasebe fis entegrasyonu | 1 gun |
| 5 | `asset_module.py` + `asset_list.py` - Liste UI | 1 gun |
| 6 | `asset_form.py` - Kayit formu (QTabWidget) | 1 gun |
| 7 | `depreciation_module.py` - Toplu amortisman isleme UI | 1 gun |
| 8 | `disposal_form.py` - Satis/hurda isleme | 0.5 gun |
| 9 | `reports_module.py` - Envanter + amortisman rapor | 1 gun |
| 10 | SatinAlma fatura onayinda otomatik kiymet olusturma | 0.5 gun |
| 11 | Menu + ikon kaydi | 0.25 gun |
| 12 | Test: Amortisman hesaplama + muhasebe entegrasyon | 1 gun |

---

## A3. KDV & Vergi Raporlari

**Oncelik:** YUKSEK (Yasal zorunluluk)
**Tahmini Efor:** 2-3 hafta

### Dosya Yapisi

```
modules/tax/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── base.py              # TaxService
│   ├── kdv_calculator.py    # KDV hesaplama motoru
│   ├── withholding.py       # Stopaj hesaplama
│   └── declaration.py       # Beyanname hazirlama
├── views/
│   ├── __init__.py
│   ├── tax_module.py        # Ana modul
│   ├── kdv_report.py        # KDV beyanname raporu
│   ├── withholding_report.py # Stopaj raporu
│   ├── ba_bs_report.py      # Ba-Bs formlari
│   └── settings_page.py     # Vergi ayarlari
```

### Veritabani Modeli

```python
# database/models/tax.py

class TaxType(str, Enum):
    KDV = "kdv"
    STOPAJ = "stopaj"
    OTV = "otv"
    DAMGA = "damga"

class TaxRate(BaseModel):
    __tablename__ = 'tax_rates'
    tax_type: TaxType
    rate: Numeric(5,2)
    description: str
    effective_from: Date
    effective_to: Date
    is_default: bool

class TaxDeclaration(BaseModel):
    __tablename__ = 'tax_declarations'
    period_year: int
    period_month: int
    declaration_type: str       # KDV1, KDV2, MUHTASAR, BABS
    sales_total: Numeric(14,2)
    purchase_total: Numeric(14,2)
    tax_payable: Numeric(14,2)
    tax_deductible: Numeric(14,2)
    net_tax: Numeric(14,2)
    status: str                 # draft, submitted, paid
    submitted_at: DateTime
    details: JSON

class WithholdingRate(BaseModel):
    __tablename__ = 'withholding_rates'
    code: str                   # 601, 602, vb.
    description: str
    rate: Numeric(5,2)
    kdv_rate: Numeric(5,2)
    is_active: bool
```

### Servis Metotlari

```python
class TaxService:
    get_applicable_rate(tax_type, date) -> Numeric
    calculate_kdv(amount, rate) -> Dict
    calculate_withholding(amount, code) -> Dict

class KDVCalculator:
    get_period_sales(year, month) -> List
    get_period_purchases(year, month) -> List
    calculate_kdv1(year, month) -> Dict
    calculate_kdv2(year, month) -> Dict
    generate_ba_form(year, month) -> List  # 5000 TL ustu alislar
    generate_bs_form(year, month) -> List  # 5000 TL ustu satislar

class DeclarationService:
    create_declaration(type, year, month) -> TaxDeclaration
    submit_declaration(id) -> bool
    get_history(year) -> List[TaxDeclaration]
    export_xml(declaration_id) -> str  # GIB beyanname XML
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | `database/models/tax.py` + Alembic migration | 0.5 gun |
| 2 | `kdv_calculator.py` - KDV1/KDV2 hesaplama | 2 gun |
| 3 | `withholding.py` - Stopaj hesaplama | 1 gun |
| 4 | `declaration.py` - Beyanname hazirlama + XML export | 1.5 gun |
| 5 | `base.py` - TaxService genel vergi islemleri | 1 gun |
| 6 | `tax_module.py` + `kdv_report.py` - KDV rapor UI | 1 gun |
| 7 | `ba_bs_report.py` - Ba-Bs form UI | 1 gun |
| 8 | `withholding_report.py` - Stopaj rapor UI | 0.5 gun |
| 9 | `settings_page.py` - Vergi orani ayarlari | 0.5 gun |
| 10 | Mevcut tax_rate 18 → 20 guncelleme (tum modul taramasi) | 0.5 gun |
| 11 | Menu + ikon kaydi | 0.25 gun |
| 12 | Test: KDV hesaplama + Ba-Bs uretimi | 1 gun |

---

## A4. Maliyet Muhasebesi

**Oncelik:** YUKSEK
**Tahmini Efor:** 4-5 hafta

### Dosya Yapisi

```
modules/costing/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── base.py              # CostingService
│   ├── standard_cost.py     # Standart maliyet hesaplama
│   ├── actual_cost.py       # Gerceklesen maliyet
│   ├── variance.py          # Sapma analizi
│   └── accounting_bridge.py # Muhasebe entegrasyonu
├── views/
│   ├── __init__.py
│   ├── costing_module.py    # Ana modul
│   ├── cost_center_list.py  # Maliyet merkezi listesi
│   ├── cost_center_form.py  # Maliyet merkezi formu
│   ├── product_costing.py   # Urun maliyet hesaplama
│   ├── variance_report.py   # Sapma raporu
│   └── period_closing.py    # Donem kapatma
```

### Veritabani Modeli

```python
# database/models/costing.py

class CostType(str, Enum):
    DIRECT_MATERIAL = "direct_material"
    DIRECT_LABOR = "direct_labor"
    OVERHEAD = "overhead"
    SUBCONTRACT = "subcontract"

class CostCenter(BaseModel):
    __tablename__ = 'cost_centers'
    code: str                    # MM001
    name: str
    parent_id: int               # FK -> cost_centers (hiyerarsik)
    department_id: int           # FK -> departments
    manager_id: int              # FK -> employees
    budget_annual: Numeric(14,2)
    is_production: bool          # Uretim maliyet merkezi mi?
    is_active: bool

class CostAllocation(BaseModel):
    __tablename__ = 'cost_allocations'
    cost_center_id: int
    target_center_id: int
    allocation_rate: Numeric(5,2)  # % dagilim
    period_year: int
    period_month: int

class ProductCost(BaseModel):
    __tablename__ = 'product_costs'
    product_id: int              # FK -> products
    period_year: int
    period_month: int
    standard_material: Numeric(14,4)
    standard_labor: Numeric(14,4)
    standard_overhead: Numeric(14,4)
    actual_material: Numeric(14,4)
    actual_labor: Numeric(14,4)
    actual_overhead: Numeric(14,4)
    standard_total: Numeric(14,4)
    actual_total: Numeric(14,4)
    variance: Numeric(14,4)
    unit_cost: Numeric(14,4)

class CostTransaction(BaseModel):
    __tablename__ = 'cost_transactions'
    cost_center_id: int
    cost_type: CostType
    amount: Numeric(14,2)
    period_year: int
    period_month: int
    source_type: str             # work_order, purchase, payroll
    source_id: int
    description: str
```

### Servis Metotlari

```python
class CostingService:
    get_cost_centers(filters) -> List[CostCenter]
    create_cost_center(data) -> CostCenter
    record_transaction(data) -> CostTransaction

class StandardCostService:
    calculate_bom_cost(product_id) -> Dict      # BOM'dan malzeme maliyeti
    calculate_routing_cost(product_id) -> Dict   # Rotalamadan iscilik
    calculate_overhead_rate(center_id, period) -> Numeric
    update_standard_costs(period) -> int         # Toplu guncelle

class ActualCostService:
    collect_material_costs(wo_id) -> Numeric     # Is emrinden malzeme
    collect_labor_costs(wo_id) -> Numeric        # PDKS'den iscilik
    collect_overhead(center_id, period) -> Numeric
    calculate_wo_cost(wo_id) -> Dict             # Is emri maliyet

class VarianceService:
    calculate_material_variance(product_id, period) -> Dict
    calculate_labor_variance(product_id, period) -> Dict
    calculate_overhead_variance(center_id, period) -> Dict
    generate_variance_report(period) -> List[Dict]
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | `database/models/costing.py` + Alembic migration | 0.5 gun |
| 2 | `base.py` - CostingService CRUD | 1 gun |
| 3 | `standard_cost.py` - BOM + rotalama maliyet hesaplama | 2 gun |
| 4 | `actual_cost.py` - Is emri gerceklesen maliyet | 2 gun |
| 5 | `variance.py` - Sapma analizi (malzeme/iscilik/GGG) | 1.5 gun |
| 6 | `accounting_bridge.py` - Muhasebe fis entegrasyonu | 1 gun |
| 7 | `costing_module.py` + `cost_center_list.py` - UI | 1 gun |
| 8 | `cost_center_form.py` - Maliyet merkezi formu | 0.5 gun |
| 9 | `product_costing.py` - Urun maliyet ekrani | 1 gun |
| 10 | `variance_report.py` - Sapma rapor UI | 1 gun |
| 11 | `period_closing.py` - Donem kapatma islemi | 1 gun |
| 12 | Menu + ikon kaydi | 0.25 gun |
| 13 | Test: Maliyet hesaplama + sapma analizi | 1.5 gun |

---

## A5. Butce Yonetimi

**Oncelik:** ORTA
**Tahmini Efor:** 3-4 hafta

### Dosya Yapisi

```
modules/budget/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── base.py              # BudgetService
│   ├── comparison.py        # Butce-Gerceklesen karsilastirma
│   └── forecast.py          # Tahmin/projeksiyon
├── views/
│   ├── __init__.py
│   ├── budget_module.py     # Ana modul
│   ├── budget_list.py       # Butce listesi
│   ├── budget_form.py       # Butce tanimlama
│   ├── comparison_report.py # Karsilastirma raporu
│   └── forecast_page.py     # Tahmin sayfasi
```

### Veritabani Modeli

```python
# database/models/budget.py

class BudgetPeriod(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class Budget(BaseModel):
    __tablename__ = 'budgets'
    code: str
    name: str
    year: int
    department_id: int           # FK -> departments
    cost_center_id: int          # FK -> cost_centers
    period_type: BudgetPeriod
    total_amount: Numeric(14,2)
    status: str                  # draft, approved, closed
    approved_by: int             # FK -> users
    approved_at: DateTime
    notes: Text

class BudgetLine(BaseModel):
    __tablename__ = 'budget_lines'
    budget_id: int               # FK -> budgets
    account_id: int              # FK -> chart_of_accounts
    month_1: Numeric(14,2)       # Ocak
    month_2: Numeric(14,2)       # Subat
    month_3: Numeric(14,2)
    month_4: Numeric(14,2)
    month_5: Numeric(14,2)
    month_6: Numeric(14,2)
    month_7: Numeric(14,2)
    month_8: Numeric(14,2)
    month_9: Numeric(14,2)
    month_10: Numeric(14,2)
    month_11: Numeric(14,2)
    month_12: Numeric(14,2)      # Aralik
    total: Numeric(14,2)
    notes: str

class BudgetRevision(BaseModel):
    __tablename__ = 'budget_revisions'
    budget_id: int
    revision_no: int
    revised_by: int
    revised_at: DateTime
    reason: str
    changes: JSON                # Degisen satirlar
```

### Servis Metotlari

```python
class BudgetService:
    create(data) -> Budget
    update(id, data) -> Budget
    approve(id, user_id) -> Budget
    get_by_department(dept_id, year) -> List[Budget]
    copy_from_previous(budget_id) -> Budget
    create_revision(budget_id, changes) -> BudgetRevision

class ComparisonService:
    get_actual_vs_budget(budget_id, month) -> Dict
    get_department_summary(dept_id, year) -> Dict
    get_variance_analysis(budget_id) -> List[Dict]
    check_budget_exceeded(account_id, amount) -> bool

class ForecastService:
    linear_forecast(budget_id, months_ahead) -> List[Dict]
    trend_analysis(budget_id) -> Dict
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | `database/models/budget.py` + Alembic migration | 0.5 gun |
| 2 | `base.py` - BudgetService CRUD + onay akisi | 1 gun |
| 3 | `comparison.py` - Butce/gerceklesen karsilastirma | 1.5 gun |
| 4 | `forecast.py` - Lineer tahmin + trend analizi | 1 gun |
| 5 | `budget_module.py` + `budget_list.py` - UI | 1 gun |
| 6 | `budget_form.py` - 12 aylik butce giris formu | 1.5 gun |
| 7 | `comparison_report.py` - Grafik + tablo rapor | 1 gun |
| 8 | `forecast_page.py` - Tahmin/projeksiyon sayfasi | 1 gun |
| 9 | SatinAlma'da butce kontrolu entegrasyonu | 0.5 gun |
| 10 | Menu + ikon kaydi | 0.25 gun |
| 11 | Test: Karsilastirma + tahmin hesaplama | 1 gun |

---

# B. SATIS & TEDARIK MODULLERI

---

## B1. Iade Yonetimi

**Oncelik:** YUKSEK
**Tahmini Efor:** 3-4 hafta

### Dosya Yapisi

```
modules/returns/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── base.py              # ReturnService
│   ├── sales_return.py      # Satis iade
│   ├── purchase_return.py   # Satin alma iade
│   └── stock_bridge.py      # Stok hareketi entegrasyonu
├── views/
│   ├── __init__.py
│   ├── return_module.py     # Ana modul
│   ├── sales_return_list.py
│   ├── sales_return_form.py
│   ├── purchase_return_list.py
│   ├── purchase_return_form.py
│   └── return_reports.py
```

### Veritabani Modeli

```python
# database/models/returns.py

class ReturnType(str, Enum):
    SALES = "sales"
    PURCHASE = "purchase"

class ReturnReason(str, Enum):
    DEFECTIVE = "defective"
    WRONG_ITEM = "wrong_item"
    EXCESS = "excess"
    DAMAGED = "damaged"
    CUSTOMER_REQUEST = "customer_request"
    OTHER = "other"

class ReturnStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending"
    APPROVED = "approved"
    RECEIVED = "received"      # Iade alindi
    INSPECTED = "inspected"    # Kontrol edildi
    COMPLETED = "completed"
    REJECTED = "rejected"

class ReturnOrder(BaseModel):
    __tablename__ = 'return_orders'
    code: str                    # SIA2602-0001 / AIA2602-0001
    type: ReturnType
    status: ReturnStatus
    reason: ReturnReason
    original_invoice_id: int     # FK -> ilgili fatura
    customer_id: int             # (satis iade icin)
    supplier_id: int             # (satin alma iade icin)
    return_date: Date
    total_amount: Numeric(14,2)
    credit_note_id: int          # Olusturulan iade faturasi
    stock_movement_id: int       # Stok hareketi
    notes: Text
    approved_by: int
    approved_at: DateTime

class ReturnOrderLine(BaseModel):
    __tablename__ = 'return_order_lines'
    return_order_id: int
    product_id: int
    quantity: Numeric(14,3)
    unit_price: Numeric(14,4)
    line_total: Numeric(14,2)
    reason: ReturnReason
    condition: str               # iyi, hasarli, kullanilmis
    warehouse_id: int            # Iade deposu
```

### Servis Metotlari

```python
class ReturnService:
    generate_code(type) -> str
    get_all(filters) -> List[ReturnOrder]
    get_by_id(id) -> ReturnOrder

class SalesReturnService(ReturnService):
    create_from_invoice(invoice_id, lines) -> ReturnOrder
    approve(id) -> ReturnOrder
    receive(id) -> ReturnOrder       # Stok girisi yapar
    complete(id) -> ReturnOrder      # Iade faturasi olusturur
    get_customer_returns(customer_id) -> List

class PurchaseReturnService(ReturnService):
    create_from_purchase(pinvoice_id, lines) -> ReturnOrder
    approve(id) -> ReturnOrder
    ship(id) -> ReturnOrder          # Stok cikisi yapar
    complete(id) -> ReturnOrder      # Iade faturasi olusturur
    get_supplier_returns(supplier_id) -> List
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | `database/models/returns.py` + Alembic migration | 0.5 gun |
| 2 | `base.py` - ReturnService ortak islemler | 0.5 gun |
| 3 | `sales_return.py` - Satis iade is mantigi | 1.5 gun |
| 4 | `purchase_return.py` - Satin alma iade is mantigi | 1.5 gun |
| 5 | `stock_bridge.py` - Stok hareketi entegrasyonu | 1 gun |
| 6 | `return_module.py` - Ana modul UI | 0.5 gun |
| 7 | `sales_return_list.py` + `sales_return_form.py` | 1.5 gun |
| 8 | `purchase_return_list.py` + `purchase_return_form.py` | 1.5 gun |
| 9 | `return_reports.py` - Iade istatistik raporu | 0.5 gun |
| 10 | Muhasebe entegrasyonu (iade fatura fisi) | 1 gun |
| 11 | Menu + ikon kaydi | 0.25 gun |
| 12 | Test: Iade akisi + stok hareketi | 1 gun |

---

## B2. Sozlesme Yonetimi

**Oncelik:** ORTA
**Tahmini Efor:** 3-4 hafta

### Dosya Yapisi

```
modules/contracts/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── base.py              # ContractService
│   ├── renewal.py           # Yenileme/uzatma
│   └── alert.py             # Sure/limit uyarilari
├── views/
│   ├── __init__.py
│   ├── contract_module.py
│   ├── contract_list.py
│   ├── contract_form.py
│   ├── renewal_page.py
│   └── contract_reports.py
```

### Veritabani Modeli

```python
# database/models/contracts.py

class ContractType(str, Enum):
    SALES = "sales"
    PURCHASE = "purchase"
    SERVICE = "service"
    LEASE = "lease"
    MAINTENANCE = "maintenance"

class ContractStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    RENEWED = "renewed"

class Contract(BaseModel):
    __tablename__ = 'contracts'
    code: str                    # SZL2602-0001
    type: ContractType
    status: ContractStatus
    title: str
    customer_id: int
    supplier_id: int
    start_date: Date
    end_date: Date
    total_value: Numeric(14,2)
    currency: str                # TRY, USD, EUR
    payment_terms: str
    auto_renew: bool
    renewal_period_months: int
    notice_period_days: int
    terms_text: Text
    signed_at: DateTime
    signed_by: int
    attachment_ids: JSON         # DMS dosya referanslari

class ContractLine(BaseModel):
    __tablename__ = 'contract_lines'
    contract_id: int
    product_id: int
    description: str
    quantity: Numeric(14,3)
    unit_price: Numeric(14,4)
    line_total: Numeric(14,2)
    delivery_schedule: JSON      # Teslimat plani

class ContractMilestone(BaseModel):
    __tablename__ = 'contract_milestones'
    contract_id: int
    title: str
    due_date: Date
    amount: Numeric(14,2)
    status: str                  # pending, completed, overdue
    completed_at: DateTime
    invoice_id: int              # Olusturulan fatura
```

### Servis Metotlari

```python
class ContractService:
    create(data) -> Contract
    update(id, data) -> Contract
    activate(id) -> Contract
    terminate(id, reason) -> Contract
    get_expiring(days_ahead) -> List[Contract]
    get_by_customer(customer_id) -> List
    get_by_supplier(supplier_id) -> List
    check_value_limit(contract_id, amount) -> bool
    generate_invoice_from_milestone(milestone_id) -> int

class RenewalService:
    check_renewals() -> List[Contract]
    renew(contract_id) -> Contract
    extend(contract_id, months) -> Contract

class AlertService:
    check_expiring_contracts() -> List[Dict]
    check_milestone_deadlines() -> List[Dict]
    check_budget_limits() -> List[Dict]
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | `database/models/contracts.py` + Alembic migration | 0.5 gun |
| 2 | `base.py` - ContractService CRUD + durum yonetimi | 1.5 gun |
| 3 | `renewal.py` - Otomatik yenileme mantigi | 1 gun |
| 4 | `alert.py` - Sure/limit uyari servisi | 1 gun |
| 5 | `contract_module.py` + `contract_list.py` - UI | 1 gun |
| 6 | `contract_form.py` - Coklu tab sozlesme formu | 1.5 gun |
| 7 | `renewal_page.py` - Yenileme yonetim ekrani | 0.5 gun |
| 8 | `contract_reports.py` - Ozet + vade raporu | 1 gun |
| 9 | Satis/SatinAlma faturalarinda sozlesme baglantisi | 0.5 gun |
| 10 | Menu + ikon kaydi | 0.25 gun |
| 11 | Test: Yenileme + limit kontrol + uyari | 1 gun |

---

## B3. RFQ - Teklif Talebi (Request for Quotation)

**Oncelik:** ORTA
**Tahmini Efor:** 2-3 hafta

### Dosya Yapisi

```
modules/purchasing/services/rfq.py      # Mevcut purchasing modulu icine
modules/purchasing/views/rfq_list.py
modules/purchasing/views/rfq_form.py
modules/purchasing/views/rfq_comparison.py  # Teklif karsilastirma
```

### Veritabani Modeli

```python
# database/models/purchasing.py icine eklenir

class RFQStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    RECEIVED = "received"       # Teklifler alindi
    EVALUATED = "evaluated"
    AWARDED = "awarded"         # Siparis olusturuldu
    CANCELLED = "cancelled"

class RFQ(BaseModel):
    __tablename__ = 'rfqs'
    code: str                    # RFQ2602-0001
    title: str
    status: RFQStatus
    deadline: DateTime
    required_date: Date          # Malzeme gereken tarih
    notes: Text
    created_by: int

class RFQLine(BaseModel):
    __tablename__ = 'rfq_lines'
    rfq_id: int
    product_id: int
    quantity: Numeric(14,3)
    unit: str
    specifications: Text

class RFQVendor(BaseModel):
    __tablename__ = 'rfq_vendors'
    rfq_id: int
    supplier_id: int
    sent_at: DateTime
    response_at: DateTime
    status: str                  # pending, quoted, declined

class RFQQuotation(BaseModel):
    __tablename__ = 'rfq_quotations'
    rfq_vendor_id: int
    rfq_line_id: int
    unit_price: Numeric(14,4)
    currency: str
    lead_time_days: int
    notes: str
    is_selected: bool
```

### Servis Metotlari

```python
class RFQService:
    create(data) -> RFQ
    add_vendors(rfq_id, supplier_ids) -> List[RFQVendor]
    send_to_vendors(rfq_id) -> bool
    record_quotation(vendor_id, line_id, data) -> RFQQuotation
    compare_quotations(rfq_id) -> Dict  # Fiyat/vade/puan karsilastirma
    award(rfq_id, selections) -> int    # PurchaseOrder olusturur
    get_best_price(rfq_id, line_id) -> RFQQuotation
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | RFQ tablolari + Alembic migration | 0.5 gun |
| 2 | `rfq.py` - RFQService is mantigi | 1.5 gun |
| 3 | `rfq_list.py` - RFQ listesi UI | 0.5 gun |
| 4 | `rfq_form.py` - RFQ olusturma formu | 1 gun |
| 5 | `rfq_comparison.py` - Teklif karsilastirma tablosu | 1.5 gun |
| 6 | RFQ → SatinAlma Siparisi otomatik donusturme | 0.5 gun |
| 7 | MRP'den otomatik RFQ olusturma entegrasyonu | 0.5 gun |
| 8 | Menu + ikon kaydi | 0.25 gun |
| 9 | Test: Teklif karsilastirma + siparis donusumu | 1 gun |

---

## B4. Tedarikci Degerlendirme

**Oncelik:** ORTA
**Tahmini Efor:** 2-3 hafta

### Dosya Yapisi

```
modules/purchasing/services/vendor_rating.py
modules/purchasing/views/vendor_rating_list.py
modules/purchasing/views/vendor_rating_detail.py
modules/purchasing/views/vendor_scorecard.py
```

### Veritabani Modeli

```python
# database/models/purchasing.py icine eklenir

class VendorRatingCriteria(BaseModel):
    __tablename__ = 'vendor_rating_criteria'
    code: str
    name: str                    # Fiyat, Kalite, Teslimat, vb.
    weight: Numeric(5,2)         # Agirlik %
    is_auto: bool                # Otomatik hesaplanan mi?
    is_active: bool

class VendorRating(BaseModel):
    __tablename__ = 'vendor_ratings'
    supplier_id: int             # FK -> suppliers
    period_year: int
    period_quarter: int          # Q1-Q4
    overall_score: Numeric(5,2)  # 0-100
    grade: str                   # A, B, C, D, F
    evaluated_by: int
    evaluated_at: DateTime
    notes: Text

class VendorRatingDetail(BaseModel):
    __tablename__ = 'vendor_rating_details'
    rating_id: int
    criteria_id: int
    score: Numeric(5,2)          # 0-100
    weighted_score: Numeric(5,2)
    auto_value: Numeric(14,4)    # Otomatik hesaplanan deger
    notes: str
```

### Servis Metotlari

```python
class VendorRatingService:
    calculate_auto_scores(supplier_id, period) -> Dict
    # Otomatik metrikler:
    #   - Teslimat zamanliligi: on_time_count / total_deliveries
    #   - Kalite skoru: accepted_qty / total_qty (kalite kontrol)
    #   - Fiyat rekabetciligi: avg_price vs market_avg
    #   - Iade orani: return_qty / total_qty

    create_rating(supplier_id, period, scores) -> VendorRating
    get_supplier_history(supplier_id) -> List[VendorRating]
    get_top_suppliers(category, n) -> List
    get_blacklist_candidates() -> List  # F dereceli tedarikciler
    generate_scorecard(supplier_id) -> Dict
    compare_suppliers(supplier_ids) -> Dict
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | Rating tablolari + Alembic migration | 0.5 gun |
| 2 | `vendor_rating.py` - Otomatik skor hesaplama motoru | 2 gun |
| 3 | `vendor_rating_list.py` - Degerlendirme listesi | 0.5 gun |
| 4 | `vendor_rating_detail.py` - Detay + el ile skor giris | 1 gun |
| 5 | `vendor_scorecard.py` - Tedarikci karnesi (grafik) | 1 gun |
| 6 | SatinAlma siparis ekraninda tedarikci skoru gosterimi | 0.5 gun |
| 7 | Menu + ikon kaydi | 0.25 gun |
| 8 | Test: Otomatik skor hesaplama | 1 gun |

---

# C. URETIM & KALITE MODULLERI

---

## C1. Lot/Seri Izlenebilirlik

**Oncelik:** YUKSEK
**Tahmini Efor:** 3-4 hafta

### Dosya Yapisi

```
modules/traceability/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── base.py              # TraceabilityService
│   ├── lot_service.py       # Lot yonetimi
│   ├── serial_service.py    # Seri no yonetimi
│   └── trace_engine.py      # Ileri/geri izleme motoru
├── views/
│   ├── __init__.py
│   ├── trace_module.py
│   ├── lot_list.py
│   ├── lot_form.py
│   ├── serial_list.py
│   ├── trace_tree.py        # Agac gorunumu (ileri/geri)
│   └── trace_report.py
```

### Veritabani Modeli

```python
# database/models/traceability.py

class LotStatus(str, Enum):
    ACTIVE = "active"
    QUARANTINE = "quarantine"
    BLOCKED = "blocked"
    EXPIRED = "expired"
    CONSUMED = "consumed"

class Lot(BaseModel):
    __tablename__ = 'lots'
    lot_number: str              # LOT2602-0001
    product_id: int
    status: LotStatus
    quantity: Numeric(14,3)
    remaining_qty: Numeric(14,3)
    production_date: Date
    expiry_date: Date
    work_order_id: int           # Ureten is emri
    supplier_lot: str            # Tedarikci lot no
    purchase_order_id: int
    warehouse_id: int
    location_id: int
    notes: Text

class SerialNumber(BaseModel):
    __tablename__ = 'serial_numbers'
    serial: str                  # Unique seri no
    product_id: int
    lot_id: int                  # FK -> lots (opsiyonel)
    status: str                  # in_stock, sold, returned, scrapped
    work_order_id: int
    customer_id: int             # Satilan musteri
    sale_date: Date
    warranty_start: Date
    warranty_end: Date

class TraceLink(BaseModel):
    __tablename__ = 'trace_links'
    parent_lot_id: int           # Girdi lot
    child_lot_id: int            # Cikti lot
    work_order_id: int
    quantity_used: Numeric(14,3)
    created_at: DateTime
```

### Servis Metotlari

```python
class LotService:
    create_lot(data) -> Lot
    generate_lot_number(product_id) -> str
    split_lot(lot_id, quantities) -> List[Lot]
    merge_lots(lot_ids) -> Lot
    quarantine(lot_id, reason) -> Lot
    release(lot_id) -> Lot
    check_expiry() -> List[Lot]
    get_stock_by_lot(product_id) -> List[Dict]

class SerialService:
    generate_serials(product_id, count) -> List[SerialNumber]
    register_sale(serial, customer_id) -> SerialNumber
    register_return(serial) -> SerialNumber
    get_history(serial) -> List[Dict]

class TraceEngine:
    trace_forward(lot_id) -> Dict   # Bu lot nereye gitti?
    trace_backward(lot_id) -> Dict  # Bu lot nereden geldi?
    get_affected_lots(lot_id) -> List[Lot]  # Geri cagirma icin
    build_trace_tree(lot_id, direction) -> Dict  # Agac yapisi
    get_full_genealogy(lot_id) -> Dict
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | `database/models/traceability.py` + Alembic migration | 0.5 gun |
| 2 | `lot_service.py` - Lot CRUD + split/merge | 1.5 gun |
| 3 | `serial_service.py` - Seri no yonetimi | 1 gun |
| 4 | `trace_engine.py` - Ileri/geri izleme motoru | 2 gun |
| 5 | `trace_module.py` + `lot_list.py` - UI | 1 gun |
| 6 | `lot_form.py` - Lot kayit/duzenleme formu | 0.5 gun |
| 7 | `serial_list.py` - Seri no listesi + arama | 0.5 gun |
| 8 | `trace_tree.py` - QTreeWidget ile izleme agaci | 1.5 gun |
| 9 | `trace_report.py` - Izlenebilirlik raporu | 0.5 gun |
| 10 | Uretim is emri kapatmada otomatik lot olusturma | 0.5 gun |
| 11 | Stok hareketlerinde lot secimi entegrasyonu | 1 gun |
| 12 | Menu + ikon kaydi | 0.25 gun |
| 13 | Test: Izleme motoru + lot islemleri | 1.5 gun |

---

## C2. APS Motoru (Advanced Planning & Scheduling)

**Oncelik:** YUKSEK
**Tahmini Efor:** 5-6 hafta
**Not:** Mevcut `modules/aps/` iskelet olarak var (services.py 766 satir), genisletilecek.

### Dosya Yapisi

```
modules/aps/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── base.py              # APSService (mevcut services.py'den refactor)
│   ├── scheduler.py         # Cizelgeleme motoru
│   ├── capacity.py          # Kapasite planlama
│   ├── constraint.py        # Kisit yonetimi
│   └── optimizer.py         # Optimizasyon algoritmalari
├── views/
│   ├── __init__.py
│   ├── aps_module.py
│   ├── gantt_chart.py       # Gantt diyagrami
│   ├── capacity_view.py     # Kapasite gorunumu
│   ├── schedule_list.py     # Cizelge listesi
│   └── what_if.py           # Ne-olur-ise senaryolari
```

### Veritabani Modeli

```python
# database/models/aps.py

class ScheduleStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ACTIVE = "active"
    COMPLETED = "completed"

class ProductionSchedule(BaseModel):
    __tablename__ = 'production_schedules'
    code: str
    name: str
    status: ScheduleStatus
    start_date: DateTime
    end_date: DateTime
    created_by: int
    published_at: DateTime
    is_frozen: bool              # Donmus donem

class ScheduleItem(BaseModel):
    __tablename__ = 'schedule_items'
    schedule_id: int
    work_order_id: int
    operation_id: int
    work_station_id: int
    planned_start: DateTime
    planned_end: DateTime
    setup_time_min: int
    processing_time_min: int
    sequence: int                # Siralama
    is_locked: bool              # Manuel kilit

class CapacityBucket(BaseModel):
    __tablename__ = 'capacity_buckets'
    work_station_id: int
    date: Date
    shift: int
    total_minutes: int
    allocated_minutes: int
    available_minutes: int
    efficiency_rate: Numeric(5,2)

class ScheduleConstraint(BaseModel):
    __tablename__ = 'schedule_constraints'
    name: str
    constraint_type: str         # capacity, material, sequence, setup
    priority: int
    parameters: JSON
    is_active: bool
```

### Servis Metotlari

```python
class APSService:
    create_schedule(data) -> ProductionSchedule
    publish(schedule_id) -> bool
    get_current_schedule() -> ProductionSchedule

class SchedulerService:
    schedule_forward(work_orders, start_date) -> List[ScheduleItem]
    schedule_backward(work_orders, due_date) -> List[ScheduleItem]
    reschedule(schedule_id, changes) -> List[ScheduleItem]
    handle_disruption(wo_id, delay_minutes) -> List[ScheduleItem]
    optimize_sequence(schedule_id, objective) -> List[ScheduleItem]
    # objective: minimize_makespan, minimize_setup, minimize_tardiness

class CapacityService:
    calculate_available(ws_id, date_range) -> List[CapacityBucket]
    check_overload(schedule_id) -> List[Dict]
    suggest_alternatives(ws_id, date) -> List[Dict]
    get_utilization_report(date_range) -> Dict

class OptimizerService:
    minimize_setup_time(schedule_id) -> List[ScheduleItem]
    balance_workload(schedule_id) -> List[ScheduleItem]
    what_if_analysis(schedule_id, scenario) -> Dict
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | `database/models/aps.py` + Alembic migration | 0.5 gun |
| 2 | Mevcut `services.py` → `base.py` refactor | 1 gun |
| 3 | `scheduler.py` - Ileri/geri cizelgeleme | 3 gun |
| 4 | `capacity.py` - Kapasite hesaplama + doluluk | 2 gun |
| 5 | `constraint.py` - Kisit motoru | 1.5 gun |
| 6 | `optimizer.py` - Setup minimizasyonu + yuk dengeleme | 2 gun |
| 7 | `aps_module.py` - Ana modul UI | 0.5 gun |
| 8 | `gantt_chart.py` - QPainter ile Gantt cizimi | 3 gun |
| 9 | `capacity_view.py` - Kapasite gorsel rapor | 1 gun |
| 10 | `schedule_list.py` - Cizelge listesi + filtreleme | 0.5 gun |
| 11 | `what_if.py` - Senaryo karsilastirma UI | 1 gun |
| 12 | Uretim planlama modulu entegrasyonu | 1 gun |
| 13 | Menu + ikon kaydi | 0.25 gun |
| 14 | Test: Cizelgeleme + kapasite + optimizasyon | 2 gun |

---

## C3. SPC - Istatistiksel Proses Kontrol

**Oncelik:** ORTA
**Tahmini Efor:** 3-4 hafta

### Dosya Yapisi

```
modules/quality/services/spc.py         # Mevcut quality modulu icine
modules/quality/views/spc_module.py
modules/quality/views/spc_chart.py      # Kontrol grafikleri
modules/quality/views/spc_setup.py      # Olcum tanimlama
modules/quality/views/capability.py     # Proses yeterlilik
```

### Veritabani Modeli

```python
# database/models/quality.py icine eklenir

class SPCChartType(str, Enum):
    XBAR_R = "xbar_r"
    XBAR_S = "xbar_s"
    P_CHART = "p_chart"
    C_CHART = "c_chart"
    NP_CHART = "np_chart"

class SPCCharacteristic(BaseModel):
    __tablename__ = 'spc_characteristics'
    product_id: int
    operation_id: int
    name: str                    # Orn: "Cap (mm)"
    nominal: Numeric(14,6)
    upper_spec: Numeric(14,6)   # USL
    lower_spec: Numeric(14,6)   # LSL
    chart_type: SPCChartType
    sample_size: int
    sample_frequency: int        # Dakikada bir olcum
    is_active: bool

class SPCMeasurement(BaseModel):
    __tablename__ = 'spc_measurements'
    characteristic_id: int
    work_order_id: int
    sample_group: int            # Alt grup no
    values: JSON                 # [10.02, 10.01, 10.03, ...]
    mean: Numeric(14,6)
    range_val: Numeric(14,6)
    std_dev: Numeric(14,6)
    measured_by: int
    measured_at: DateTime
    is_out_of_control: bool

class SPCControlLimit(BaseModel):
    __tablename__ = 'spc_control_limits'
    characteristic_id: int
    ucl: Numeric(14,6)          # Upper Control Limit
    lcl: Numeric(14,6)          # Lower Control Limit
    center_line: Numeric(14,6)  # Ortalama
    calculated_at: DateTime
    sample_count: int            # Kac ornekten hesaplandi
```

### Servis Metotlari

```python
class SPCService:
    create_characteristic(data) -> SPCCharacteristic
    record_measurement(char_id, values) -> SPCMeasurement
    calculate_control_limits(char_id, n_samples) -> SPCControlLimit
    check_rules(char_id) -> List[Dict]  # Western Electric kurallari
    # Kural 1: 1 nokta 3σ disinda
    # Kural 2: 9 ardisik nokta ayni tarafta
    # Kural 3: 6 ardisik artan/azalan
    # Kural 4: 14 ardisik zigzag
    calculate_cpk(char_id, n_samples) -> Dict  # Cp, Cpk, Pp, Ppk
    get_chart_data(char_id, date_range) -> Dict
    get_capability_report(char_id) -> Dict
    get_ooc_history(char_id) -> List[SPCMeasurement]  # Out of control
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | SPC tablolari + Alembic migration | 0.5 gun |
| 2 | `spc.py` - Kontrol limiti hesaplama + WE kurallari | 2.5 gun |
| 3 | `spc.py` - Cpk/Ppk proses yeterlilik hesaplama | 1 gun |
| 4 | `spc_module.py` - Ana SPC modulu UI | 0.5 gun |
| 5 | `spc_chart.py` - QPainter ile kontrol grafikleri | 2 gun |
| 6 | `spc_setup.py` - Karakteristik tanimlama formu | 0.5 gun |
| 7 | `capability.py` - Proses yeterlilik rapor UI | 1 gun |
| 8 | Operator panelinde SPC olcum girisi entegrasyonu | 1 gun |
| 9 | Menu + ikon kaydi | 0.25 gun |
| 10 | Test: Kontrol limiti + WE kurallari + Cpk | 1.5 gun |

---

# D. IK & ORGANIZASYON MODULLERI

---

## D1. Ise Alim (Recruitment)

**Oncelik:** ORTA
**Tahmini Efor:** 3-4 hafta

### Dosya Yapisi

```
modules/hr/services/recruitment.py      # Mevcut HR modulu icine
modules/hr/views/recruitment_module.py
modules/hr/views/job_posting_list.py
modules/hr/views/job_posting_form.py
modules/hr/views/application_list.py
modules/hr/views/application_form.py
modules/hr/views/interview_page.py
```

### Veritabani Modeli

```python
# database/models/hr.py icine eklenir

class JobPostingStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    FILLED = "filled"
    CANCELLED = "cancelled"

class ApplicationStatus(str, Enum):
    NEW = "new"
    SCREENING = "screening"
    INTERVIEW = "interview"
    ASSESSMENT = "assessment"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

class JobPosting(BaseModel):
    __tablename__ = 'job_postings'
    code: str                    # ILN2602-0001
    title: str
    department_id: int
    position: str
    headcount: int
    status: JobPostingStatus
    description: Text
    requirements: Text
    salary_min: Numeric(14,2)
    salary_max: Numeric(14,2)
    posted_at: DateTime
    deadline: Date
    created_by: int

class JobApplication(BaseModel):
    __tablename__ = 'job_applications'
    code: str                    # BSV2602-0001
    posting_id: int
    status: ApplicationStatus
    first_name: str
    last_name: str
    email: str
    phone: str
    resume_path: str             # DMS referansi
    cover_letter: Text
    source: str                  # kariyer.net, linkedin, referans
    applied_at: DateTime
    rating: int                  # 1-5 degerlendirme
    notes: Text

class Interview(BaseModel):
    __tablename__ = 'interviews'
    application_id: int
    interviewer_id: int          # FK -> employees
    scheduled_at: DateTime
    duration_min: int
    interview_type: str          # phone, video, onsite, technical
    location: str
    status: str                  # scheduled, completed, cancelled
    rating: int                  # 1-5
    feedback: Text
    result: str                  # pass, fail, pending
```

### Servis Metotlari

```python
class RecruitmentService:
    # Ilan
    create_posting(data) -> JobPosting
    open_posting(id) -> JobPosting
    close_posting(id) -> JobPosting
    get_active_postings() -> List[JobPosting]

    # Basvuru
    create_application(data) -> JobApplication
    advance_stage(app_id) -> JobApplication  # Sonraki asama
    reject(app_id, reason) -> JobApplication
    hire(app_id) -> int  # Employee olusturur, id doner

    # Mulakat
    schedule_interview(data) -> Interview
    complete_interview(id, rating, feedback) -> Interview
    get_pipeline(posting_id) -> Dict  # Asamalara gore aday dagilimi

    # Rapor
    get_recruitment_metrics() -> Dict
    # time_to_hire, cost_per_hire, source_effectiveness
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | Ise alim tablolari + Alembic migration | 0.5 gun |
| 2 | `recruitment.py` - Tum is mantigi | 2 gun |
| 3 | `recruitment_module.py` - Ana modul UI | 0.5 gun |
| 4 | `job_posting_list.py` + `job_posting_form.py` | 1.5 gun |
| 5 | `application_list.py` + `application_form.py` | 1.5 gun |
| 6 | `interview_page.py` - Mulakat takvimi + degerlendirme | 1 gun |
| 7 | Basvurudan personel kaydi otomatik olusturma | 0.5 gun |
| 8 | Menu + ikon kaydi | 0.25 gun |
| 9 | Test: Ise alim akisi + asama gecisleri | 1 gun |

---

## D2. Proje Yonetimi

**Oncelik:** ORTA
**Tahmini Efor:** 4-5 hafta

### Dosya Yapisi

```
modules/projects/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── base.py              # ProjectService
│   ├── task_service.py      # Gorev yonetimi
│   ├── resource.py          # Kaynak atama
│   └── costing_bridge.py    # Proje maliyeti
├── views/
│   ├── __init__.py
│   ├── project_module.py
│   ├── project_list.py
│   ├── project_form.py
│   ├── task_board.py        # Kanban gorunumu
│   ├── gantt_view.py        # Proje Gantt
│   ├── resource_view.py     # Kaynak gorunumu
│   └── project_dashboard.py # Proje ozet paneli
```

### Veritabani Modeli

```python
# database/models/projects.py

class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"

class Project(BaseModel):
    __tablename__ = 'projects'
    code: str                    # PRJ2602-0001
    name: str
    description: Text
    status: ProjectStatus
    customer_id: int             # Musteri projesi
    manager_id: int              # FK -> employees
    start_date: Date
    planned_end: Date
    actual_end: Date
    budget: Numeric(14,2)
    actual_cost: Numeric(14,2)
    progress: Numeric(5,2)       # % tamamlanma
    priority: int

class ProjectTask(BaseModel):
    __tablename__ = 'project_tasks'
    project_id: int
    parent_task_id: int          # Alt gorev
    code: str
    title: str
    description: Text
    status: TaskStatus
    assignee_id: int             # FK -> employees
    start_date: Date
    due_date: Date
    completed_at: DateTime
    estimated_hours: Numeric(8,2)
    actual_hours: Numeric(8,2)
    progress: Numeric(5,2)
    priority: int
    dependencies: JSON           # Oncul gorev id'leri

class ProjectResource(BaseModel):
    __tablename__ = 'project_resources'
    project_id: int
    employee_id: int
    role: str                    # proje_yoneticisi, gelistirici, vb.
    allocation_percent: Numeric(5,2)  # % atama
    start_date: Date
    end_date: Date
    hourly_rate: Numeric(10,2)

class ProjectTimeEntry(BaseModel):
    __tablename__ = 'project_time_entries'
    task_id: int
    employee_id: int
    date: Date
    hours: Numeric(8,2)
    description: str
```

### Servis Metotlari

```python
class ProjectService:
    create(data) -> Project
    update(id, data) -> Project
    update_progress(id) -> Project       # Alt gorevlerden otomatik
    get_dashboard(id) -> Dict            # Ozet bilgiler
    get_by_customer(customer_id) -> List
    get_active_projects() -> List

class TaskService:
    create(data) -> ProjectTask
    update_status(id, status) -> ProjectTask
    assign(id, employee_id) -> ProjectTask
    get_kanban_data(project_id) -> Dict  # Statuslere gore gruplu
    get_critical_path(project_id) -> List[ProjectTask]
    get_overdue_tasks() -> List[ProjectTask]

class ResourceService:
    assign(project_id, employee_id, data) -> ProjectResource
    get_utilization(employee_id, date_range) -> Dict
    get_availability(date_range) -> List[Dict]
    log_time(task_id, employee_id, hours) -> ProjectTimeEntry
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | `database/models/projects.py` + Alembic migration | 0.5 gun |
| 2 | `base.py` - ProjectService CRUD + ilerleme hesaplama | 1.5 gun |
| 3 | `task_service.py` - Gorev yonetimi + kritik yol | 2 gun |
| 4 | `resource.py` - Kaynak atama + kullanim raporu | 1 gun |
| 5 | `costing_bridge.py` - Maliyet muhasebesi entegrasyonu | 0.5 gun |
| 6 | `project_module.py` + `project_list.py` - UI | 1 gun |
| 7 | `project_form.py` - Proje kayit formu | 1 gun |
| 8 | `task_board.py` - Kanban gorunumu (drag-drop) | 2 gun |
| 9 | `gantt_view.py` - QPainter ile Gantt | 2 gun |
| 10 | `resource_view.py` - Kaynak gorunumu | 0.5 gun |
| 11 | `project_dashboard.py` - Proje ozet paneli | 1 gun |
| 12 | Menu + ikon kaydi | 0.25 gun |
| 13 | Test: Gorev akisi + ilerleme + kritik yol | 1.5 gun |

---

# E. ALTYAPI & PLATFORM MODULLERI

---

## E1. Test Altyapisi

**Oncelik:** KRITIK (Tum diger modullerin temeli)
**Tahmini Efor:** 2 hafta
**Not:** 17 test dosyasi mevcut (~7,750 satir), conftest.py ve pytest.ini yok.

### Dosya Yapisi

```
tests/
├── conftest.py              # YENI: Global fixture'lar
├── pytest.ini               # YENI: pytest konfigurasyonu
├── factories/
│   ├── __init__.py
│   ├── base.py              # BaseFactory
│   ├── product_factory.py
│   ├── customer_factory.py
│   ├── order_factory.py
│   └── ...                  # Her modul icin factory
├── fixtures/
│   ├── __init__.py
│   ├── db_fixtures.py       # DB session fixture
│   └── sample_data.py       # Ornek veri seti
├── unit/
│   ├── test_einvoice_service.py
│   ├── test_depreciation.py
│   ├── test_costing.py
│   └── ...
├── integration/
│   ├── test_sales_flow.py
│   ├── test_production_flow.py
│   └── ...
└── e2e/
    └── ...                  # Mevcut test dosyalari buraya tasinir
```

### Konfigurasyonlar

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
```

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def db_engine():
    """Test icin ayri PostgreSQL veritabani"""

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Her test icin temiz session (rollback)"""

@pytest.fixture
def sample_product(db_session):
    """Ornek urun"""

@pytest.fixture
def sample_customer(db_session):
    """Ornek musteri"""

@pytest.fixture
def sample_work_order(db_session, sample_product):
    """Ornek is emri"""
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | `pytest.ini` konfigurasyonu | 0.25 gun |
| 2 | `conftest.py` - DB session fixture (rollback stratejisi) | 1 gun |
| 3 | `factories/base.py` - BaseFactory pattern | 0.5 gun |
| 4 | Temel factory'ler (product, customer, order, wo) | 1 gun |
| 5 | `fixtures/db_fixtures.py` - Ortak DB fixture'lar | 0.5 gun |
| 6 | Mevcut 17 test dosyasini unit/integration/e2e'ye siniflandirma | 1 gun |
| 7 | Her yeni modul icin test sablonu olusturma | 0.5 gun |
| 8 | CI/CD test calistirma scripti | 0.5 gun |
| 9 | Test coverage rapor ayari | 0.25 gun |

---

## E2. Workflow Tasarimcisi

**Oncelik:** ORTA
**Tahmini Efor:** 4-5 hafta
**Not:** Mevcut `modules/workflow/` (3 view, services.py 998 satir) genisletilecek.

### Dosya Yapisi

```
modules/workflow/
├── services/
│   ├── base.py              # Mevcut services.py'den refactor
│   ├── engine.py            # Is akisi motoru
│   ├── designer.py          # Tasarimci servisi
│   └── notification_bridge.py
├── views/
│   ├── workflow_module.py   # Mevcut genisletilecek
│   ├── designer_page.py     # Gorsel tasarimci
│   ├── template_list.py     # Sablon listesi
│   ├── instance_list.py     # Aktif akislar
│   └── approval_inbox.py    # Onay kutusu
```

### Veritabani Modeli

```python
# database/models/workflow.py genisletilir

class WorkflowNodeType(str, Enum):
    START = "start"
    END = "end"
    APPROVAL = "approval"
    CONDITION = "condition"
    ACTION = "action"
    NOTIFICATION = "notification"
    TIMER = "timer"

class WorkflowTemplate(BaseModel):
    __tablename__ = 'workflow_templates'
    code: str
    name: str
    description: str
    entity_type: str             # sales_order, purchase_order, vb.
    nodes: JSON                  # Node tanimlari
    edges: JSON                  # Baglanti tanimlari
    is_active: bool
    version: int

class WorkflowInstance(BaseModel):
    __tablename__ = 'workflow_instances'
    template_id: int
    entity_type: str
    entity_id: int
    current_node: str
    status: str                  # running, completed, cancelled, error
    started_at: DateTime
    completed_at: DateTime
    started_by: int
    variables: JSON              # Calisma zamani degiskenler

class WorkflowAction(BaseModel):
    __tablename__ = 'workflow_actions'
    instance_id: int
    node_id: str
    action_type: str             # approve, reject, delegate, escalate
    acted_by: int
    acted_at: DateTime
    comment: str
    result: JSON
```

### Servis Metotlari

```python
class WorkflowEngine:
    start(template_id, entity_type, entity_id) -> WorkflowInstance
    advance(instance_id, action, user_id) -> WorkflowInstance
    evaluate_condition(instance_id, node_id) -> bool
    execute_action(instance_id, node_id) -> bool
    escalate(instance_id) -> bool
    cancel(instance_id) -> bool
    get_pending_approvals(user_id) -> List[WorkflowInstance]

class DesignerService:
    create_template(data) -> WorkflowTemplate
    validate_template(template_id) -> List[str]  # Hata listesi
    duplicate_template(template_id) -> WorkflowTemplate
    export_template(template_id) -> Dict
    import_template(data) -> WorkflowTemplate
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | Workflow tablolari genisletme + Alembic migration | 0.5 gun |
| 2 | Mevcut `services.py` → `base.py` + `engine.py` refactor | 1.5 gun |
| 3 | `engine.py` - Is akisi motoru (kosul/aksiyon/zamanlayici) | 3 gun |
| 4 | `designer.py` - Sablon yonetimi + validasyon | 1 gun |
| 5 | `notification_bridge.py` - Bildirim entegrasyonu | 0.5 gun |
| 6 | `designer_page.py` - Gorsel is akisi tasarimcisi (QGraphicsScene) | 3 gun |
| 7 | `template_list.py` - Sablon listesi UI | 0.5 gun |
| 8 | `instance_list.py` - Aktif akislar UI | 0.5 gun |
| 9 | `approval_inbox.py` - Onay kutusu UI | 1 gun |
| 10 | Satis/SatinAlma siparis onay akisi entegrasyonu | 1 gun |
| 11 | Menu + ikon kaydi | 0.25 gun |
| 12 | Test: Motor + kosul degerlendirme + escalation | 1.5 gun |

---

## E3. Bildirim Motoru

**Oncelik:** ORTA
**Tahmini Efor:** 2-3 hafta
**Not:** Mevcut `modules/notifications/` (services.py 417 satir) genisletilecek.

### Dosya Yapisi

```
modules/notifications/
├── services/
│   ├── base.py              # Mevcut services.py'den refactor
│   ├── channels/
│   │   ├── in_app.py        # Uygulama ici bildirim
│   │   ├── email.py         # E-posta
│   │   └── sms.py           # SMS (opsiyonel)
│   ├── template_service.py  # Bildirim sablonlari
│   └── scheduler.py         # Zamanlanmis bildirimler
├── views/
│   ├── notification_module.py
│   ├── notification_list.py   # Bildirim listesi
│   ├── notification_settings.py # Kullanici tercihleri
│   └── template_manager.py    # Sablon yonetimi
```

### Veritabani Modeli

```python
# database/models/notifications.py genisletilir

class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"

class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationTemplate(BaseModel):
    __tablename__ = 'notification_templates'
    code: str                    # ORDER_APPROVED, STOCK_LOW, vb.
    name: str
    channel: NotificationChannel
    subject_template: str        # Jinja2 sablon
    body_template: Text          # Jinja2 sablon
    is_active: bool

class Notification(BaseModel):
    __tablename__ = 'notifications'
    user_id: int
    channel: NotificationChannel
    priority: NotificationPriority
    title: str
    body: Text
    entity_type: str
    entity_id: int
    is_read: bool
    read_at: DateTime
    sent_at: DateTime
    template_id: int

class NotificationPreference(BaseModel):
    __tablename__ = 'notification_preferences'
    user_id: int
    event_type: str              # order_approved, stock_low, vb.
    channel_in_app: bool
    channel_email: bool
    channel_sms: bool
    is_active: bool
```

### Servis Metotlari

```python
class NotificationService:
    send(user_id, template_code, context, channel) -> Notification
    send_bulk(user_ids, template_code, context) -> List[Notification]
    mark_read(notification_id) -> bool
    mark_all_read(user_id) -> int
    get_unread_count(user_id) -> int
    get_user_notifications(user_id, page, size) -> List[Notification]

class TemplateService:
    render(template_code, context) -> Dict  # {subject, body}
    create_template(data) -> NotificationTemplate
    get_all_templates() -> List

class SchedulerService:
    schedule(user_id, template_code, context, send_at) -> bool
    check_stock_alerts() -> int        # Dusuk stok uyarilari
    check_overdue_tasks() -> int       # Geciken gorevler
    check_contract_expiry() -> int     # Biten sozlesmeler
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | Bildirim tablolari genisletme + Alembic migration | 0.5 gun |
| 2 | Mevcut `services.py` → `base.py` refactor | 0.5 gun |
| 3 | `in_app.py` - Uygulama ici bildirim kanali | 0.5 gun |
| 4 | `email.py` - E-posta kanali (smtplib) | 1 gun |
| 5 | `template_service.py` - Jinja2 sablon yonetimi | 0.5 gun |
| 6 | `scheduler.py` - Zamanlanmis kontroller | 1 gun |
| 7 | `notification_module.py` + `notification_list.py` - UI | 1 gun |
| 8 | `notification_settings.py` - Kullanici tercihleri UI | 0.5 gun |
| 9 | `template_manager.py` - Sablon yonetim UI | 0.5 gun |
| 10 | StatusBar'a bildirim ikonu + popup | 0.5 gun |
| 11 | Mevcut modullere bildirim trigger'lari ekleme | 1 gun |
| 12 | Menu + ikon kaydi | 0.25 gun |
| 13 | Test: Bildirim gonderme + sablon render + zamanlayici | 1 gun |

---

## E4. REST API Katmani

**Oncelik:** YUKSEK
**Tahmini Efor:** 5-6 hafta
**Not:** FastAPI 0.128.0 + uvicorn zaten requirements.txt'de mevcut.

### Dosya Yapisi

```
api/
├── __init__.py
├── main.py                  # FastAPI app + uvicorn runner
├── config.py                # API konfigurasyonu
├── auth/
│   ├── __init__.py
│   ├── jwt.py               # JWT token islemleri
│   ├── middleware.py         # Auth middleware
│   └── permissions.py       # Yetki kontrol
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py       # Login/logout/refresh
│   ├── sales_routes.py
│   ├── purchasing_routes.py
│   ├── inventory_routes.py
│   ├── production_routes.py
│   ├── hr_routes.py
│   ├── accounting_routes.py
│   └── ...                  # Her modul icin route
├── schemas/
│   ├── __init__.py
│   ├── auth.py              # Pydantic auth modelleri
│   ├── sales.py
│   ├── common.py            # Ortak response/pagination
│   └── ...
├── middleware/
│   ├── cors.py
│   ├── rate_limit.py
│   └── logging.py
└── utils/
    ├── pagination.py
    └── response.py
```

### Teknik Detaylar

```python
# api/main.py
from fastapi import FastAPI
from api.auth.middleware import JWTMiddleware
from api.middleware.cors import setup_cors

app = FastAPI(
    title="Akilli Is ERP API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# api/auth/jwt.py
class JWTService:
    create_access_token(user_id, roles) -> str
    create_refresh_token(user_id) -> str
    verify_token(token) -> Dict
    refresh(refresh_token) -> Dict

# api/schemas/common.py
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

class APIResponse(BaseModel):
    success: bool
    data: Any
    message: str
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | `api/main.py` - FastAPI app yapilandirma | 0.5 gun |
| 2 | `api/config.py` - API konfigurasyonu | 0.25 gun |
| 3 | `jwt.py` - JWT token olusturma/dogrulama (PyJWT) | 1 gun |
| 4 | `middleware.py` - Auth middleware | 0.5 gun |
| 5 | `permissions.py` - Rol bazli yetki kontrol | 1 gun |
| 6 | `schemas/common.py` - Ortak Pydantic schemalar | 0.5 gun |
| 7 | `auth_routes.py` - Login/logout/refresh endpoint'leri | 0.5 gun |
| 8 | `sales_routes.py` - Satis CRUD endpoint'leri | 1 gun |
| 9 | `purchasing_routes.py` - SatinAlma endpoint'leri | 1 gun |
| 10 | `inventory_routes.py` - Stok endpoint'leri | 1 gun |
| 11 | `production_routes.py` - Uretim endpoint'leri | 1 gun |
| 12 | `hr_routes.py` - IK endpoint'leri | 0.5 gun |
| 13 | `accounting_routes.py` - Muhasebe endpoint'leri | 0.5 gun |
| 14 | `middleware/cors.py` + `rate_limit.py` + `logging.py` | 1 gun |
| 15 | `utils/pagination.py` + `response.py` | 0.5 gun |
| 16 | OpenAPI dokumantasyon ayarlari | 0.25 gun |
| 17 | PyJWT requirements.txt'ye ekleme | 0.1 gun |
| 18 | Test: Auth + CRUD + pagination + rate limit | 2 gun |

---

## E5. Cok Sirketli Yapi (Multi-Company)

**Oncelik:** DUSUK
**Tahmini Efor:** 3-4 hafta

### Dosya Yapisi

```
modules/system/services/multi_company.py
modules/system/views/company_list.py
modules/system/views/company_form.py
modules/system/views/company_switch.py   # Sirket degistirme
```

### Veritabani Modeli

```python
# database/models/system.py icine eklenir

class Company(BaseModel):
    __tablename__ = 'companies'
    code: str                    # SRK001
    name: str
    tax_number: str
    tax_office: str
    address: Text
    phone: str
    email: str
    currency: str                # TRY, USD, EUR
    logo_path: str
    is_default: bool
    is_active: bool

class CompanyUser(BaseModel):
    __tablename__ = 'company_users'
    company_id: int
    user_id: int
    role: str
    is_default: bool             # Giris yapinca bu sirket acilsin
```

### Teknik Yaklasim

```
Yaklasim: Schema-per-company (PostgreSQL schema)
- Her sirket icin ayri PostgreSQL schema
- Ortak tablolar public schema'da (users, companies)
- Session basina aktif company_id
- Tum servisler company_id filtrelemesi yapacak
- Middleware: set_active_company(company_id)
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | Company tablolari + Alembic migration | 0.5 gun |
| 2 | `multi_company.py` - Sirket yonetim servisi | 1 gun |
| 3 | PostgreSQL schema-per-company altyapisi | 2 gun |
| 4 | Session middleware - aktif sirket yonetimi | 1 gun |
| 5 | Mevcut servislere company_id filtresi ekleme | 2 gun |
| 6 | `company_list.py` + `company_form.py` - UI | 1 gun |
| 7 | `company_switch.py` - Sirket degistirme UI | 0.5 gun |
| 8 | Ana pencerede aktif sirket gosterimi | 0.25 gun |
| 9 | Menu + ikon kaydi | 0.25 gun |
| 10 | Test: Schema isolation + sirket degistirme | 1.5 gun |

---

# F. DIS ENTEGRASYON MODULLERI

---

## F1. EDI Entegrasyon

**Oncelik:** DUSUK
**Tahmini Efor:** 3-4 hafta

### Dosya Yapisi

```
modules/edi/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── base.py              # EDIService
│   ├── parser.py            # Mesaj ayristirici
│   ├── builder.py           # Mesaj olusturucu
│   └── connector.py         # FTP/SFTP/AS2 baglantisi
├── views/
│   ├── __init__.py
│   ├── edi_module.py
│   ├── message_list.py      # Mesaj listesi
│   ├── partner_list.py      # Is ortagi listesi
│   ├── partner_form.py
│   └── mapping_page.py      # Alan esleme
```

### Veritabani Modeli

```python
# database/models/edi.py

class EDIStandard(str, Enum):
    EDIFACT = "edifact"
    X12 = "x12"
    XML = "xml"
    CSV = "csv"

class EDIPartner(BaseModel):
    __tablename__ = 'edi_partners'
    code: str
    name: str
    customer_id: int
    supplier_id: int
    standard: EDIStandard
    connection_type: str         # ftp, sftp, as2, api
    connection_config: JSON      # Host, port, credentials
    is_active: bool

class EDIMessage(BaseModel):
    __tablename__ = 'edi_messages'
    partner_id: int
    direction: str               # inbound, outbound
    message_type: str            # ORDER, DESADV, INVOIC
    status: str                  # received, parsed, processed, error
    raw_content: Text
    parsed_data: JSON
    entity_type: str             # sales_order, invoice, vb.
    entity_id: int
    received_at: DateTime
    processed_at: DateTime
    error_message: str

class EDIMapping(BaseModel):
    __tablename__ = 'edi_mappings'
    partner_id: int
    message_type: str
    field_mappings: JSON         # {edi_field: erp_field}
    transformation_rules: JSON
    is_active: bool
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | `database/models/edi.py` + Alembic migration | 0.5 gun |
| 2 | `parser.py` - EDIFACT/XML mesaj ayristirma | 2 gun |
| 3 | `builder.py` - Mesaj olusturma | 1.5 gun |
| 4 | `connector.py` - FTP/SFTP baglantisi | 1 gun |
| 5 | `base.py` - EDIService is mantigi | 1.5 gun |
| 6 | `edi_module.py` + `message_list.py` - UI | 1 gun |
| 7 | `partner_list.py` + `partner_form.py` - UI | 1 gun |
| 8 | `mapping_page.py` - Alan esleme UI | 1 gun |
| 9 | Satis/SatinAlma siparis otomatik olusturma | 1 gun |
| 10 | Menu + ikon kaydi | 0.25 gun |
| 11 | Test: Parser + builder + connector | 1.5 gun |

---

## F2. Web Arayuz

**Oncelik:** ORTA
**Tahmini Efor:** 8-10 hafta
**Bagimlilik:** REST API (E4) tamamlanmis olmali

### Dosya Yapisi

```
web/
├── package.json
├── vite.config.ts
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   ├── client.ts         # Axios/fetch wrapper
│   │   └── endpoints.ts      # API endpoint tanimlari
│   ├── auth/
│   │   ├── AuthProvider.tsx
│   │   └── ProtectedRoute.tsx
│   ├── components/
│   │   ├── Layout/
│   │   ├── DataTable/
│   │   ├── Form/
│   │   └── Charts/
│   ├── pages/
│   │   ├── Dashboard/
│   │   ├── Sales/
│   │   ├── Inventory/
│   │   ├── Production/
│   │   └── ...
│   └── store/                # State management
│       └── ...
```

### Teknik Yaklasim

```
Framework: React + TypeScript + Vite
UI Library: Ant Design veya MUI
State: React Query (server state) + Zustand (client state)
Charts: Recharts veya Chart.js
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | Proje scaffolding (Vite + React + TS) | 0.5 gun |
| 2 | Auth sistemi (JWT login/refresh) | 2 gun |
| 3 | Layout + navigasyon + tema | 2 gun |
| 4 | DataTable bileşeni (siralama/filtreleme/pagination) | 2 gun |
| 5 | Form bileşenleri (input/select/date) | 1.5 gun |
| 6 | Dashboard sayfasi | 2 gun |
| 7 | Satis modulu sayfalari | 3 gun |
| 8 | Stok modulu sayfalari | 2 gun |
| 9 | Uretim modulu sayfalari | 2 gun |
| 10 | Diger modul sayfalari (IK, Muhasebe, vb.) | 5 gun |
| 11 | Grafik/rapor bileşenleri | 2 gun |
| 12 | Responsive tasarim | 1 gun |
| 13 | Test: Component + integration | 2 gun |

---

## F3. Mobil Uygulama

**Oncelik:** DUSUK
**Tahmini Efor:** 6-8 hafta
**Bagimlilik:** REST API (E4) tamamlanmis olmali

### Teknik Yaklasim

```
Framework: React Native veya Flutter
Oncelikli Ekranlar:
  - Dashboard (ozet bilgiler)
  - Stok sorgulama + barkod okuma
  - Is emri goruntuleme + durum guncelleme
  - Onay kutusu (siparis/iade onaylama)
  - Bildirimler
  - Depo sayim
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | Proje scaffolding + navigasyon | 1 gun |
| 2 | Auth (JWT + biometric) | 1.5 gun |
| 3 | Dashboard ekrani | 2 gun |
| 4 | Stok sorgulama + barkod tarayici | 2 gun |
| 5 | Is emri goruntuleyici | 1.5 gun |
| 6 | Onay kutusu ekrani | 1 gun |
| 7 | Bildirim entegrasyonu (push) | 1.5 gun |
| 8 | Depo sayim modulu | 2 gun |
| 9 | Offline calisma destegi | 2 gun |
| 10 | Test: E2E mobil testleri | 1.5 gun |

---

## F4. Portal (Musteri/Tedarikci)

**Oncelik:** DUSUK
**Tahmini Efor:** 4-5 hafta
**Bagimlilik:** Web Arayuz (F2) + REST API (E4) tamamlanmis olmali

### Teknik Yaklasim

```
Musteri Portali:
  - Siparis verme / siparis takibi
  - Fatura goruntuleme
  - Destek talebi olusturma
  - Urun katalogu

Tedarikci Portali:
  - RFQ'lara teklif verme
  - Siparis goruntuleme
  - Fatura yukleme
  - Teslimat bildirimi
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | Portal auth (davetiye bazli kayit) | 1 gun |
| 2 | Musteri portali - siparis + fatura | 3 gun |
| 3 | Musteri portali - destek + katalog | 2 gun |
| 4 | Tedarikci portali - RFQ + teklif | 2 gun |
| 5 | Tedarikci portali - siparis + teslimat | 2 gun |
| 6 | Ortak: Dashboard + bildirimler | 1 gun |
| 7 | Guvenlik: Veri izolasyonu + yetkilendirme | 1 gun |
| 8 | Test: Portal akislari | 1 gun |

---

# G. ANALIZ & BAKIM MODULLERI

---

## G1. BI Raporlama

**Oncelik:** ORTA
**Tahmini Efor:** 3-4 hafta

### Dosya Yapisi

```
modules/reports/services/bi.py          # Mevcut reports modulu icine
modules/reports/views/bi_module.py
modules/reports/views/bi_dashboard.py    # Ozel BI dashboard
modules/reports/views/report_builder.py  # Rapor tasarimcisi
modules/reports/views/kpi_module.py      # KPI tanimlama
```

### Veritabani Modeli

```python
# database/models/reports.py icine eklenir

class KPIDefinition(BaseModel):
    __tablename__ = 'kpi_definitions'
    code: str
    name: str
    description: str
    module: str                  # sales, production, inventory, vb.
    formula: str                 # SQL veya Python ifade
    target_value: Numeric(14,4)
    unit: str                    # %, TRY, adet, gun
    frequency: str               # daily, weekly, monthly
    is_active: bool

class KPIValue(BaseModel):
    __tablename__ = 'kpi_values'
    kpi_id: int
    period_date: Date
    value: Numeric(14,4)
    target: Numeric(14,4)
    achievement: Numeric(5,2)    # % hedefe ulasilma
    calculated_at: DateTime

class SavedReport(BaseModel):
    __tablename__ = 'saved_reports'
    code: str
    name: str
    description: str
    query: Text                  # SQL sorgusu
    parameters: JSON
    chart_config: JSON           # Grafik ayarlari
    created_by: int
    is_shared: bool
```

### Servis Metotlari

```python
class BIService:
    calculate_kpi(kpi_id, date) -> KPIValue
    calculate_all_kpis(date) -> List[KPIValue]
    get_kpi_trend(kpi_id, date_range) -> List[KPIValue]
    get_dashboard_data() -> Dict

    # Hazir raporlar
    get_sales_analysis(filters) -> Dict
    get_production_efficiency(filters) -> Dict
    get_inventory_turnover(filters) -> Dict
    get_financial_summary(filters) -> Dict
    get_hr_metrics(filters) -> Dict

    # Rapor olusturucu
    execute_report(report_id, params) -> Dict
    save_report(data) -> SavedReport
    export_report(report_id, format) -> bytes  # PDF, Excel
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | KPI/Report tablolari + Alembic migration | 0.5 gun |
| 2 | `bi.py` - KPI hesaplama motoru | 2 gun |
| 3 | `bi.py` - Hazir analiz raporlari (satis/uretim/stok) | 2 gun |
| 4 | `bi_module.py` + `bi_dashboard.py` - Dashboard UI | 1.5 gun |
| 5 | `report_builder.py` - SQL tabanli rapor tasarimcisi | 2 gun |
| 6 | `kpi_module.py` - KPI tanimlama + goruntuleme | 1 gun |
| 7 | Grafik bilesenleri (QPainter / matplotlib) | 1.5 gun |
| 8 | PDF/Excel export | 1 gun |
| 9 | Menu + ikon kaydi | 0.25 gun |
| 10 | Test: KPI hesaplama + rapor calistirma | 1 gun |

---

## G2. Kestirimci Bakim (Predictive Maintenance)

**Oncelik:** DUSUK
**Tahmini Efor:** 3-4 hafta

### Dosya Yapisi

```
modules/maintenance/services/predictive.py  # Mevcut maintenance icine
modules/maintenance/views/predictive_module.py
modules/maintenance/views/prediction_dashboard.py
modules/maintenance/views/sensor_config.py
```

### Veritabani Modeli

```python
# database/models/maintenance.py icine eklenir

class SensorReading(BaseModel):
    __tablename__ = 'sensor_readings'
    equipment_id: int
    sensor_type: str             # temperature, vibration, pressure
    value: Numeric(14,4)
    unit: str
    recorded_at: DateTime
    is_anomaly: bool

class PredictionModel(BaseModel):
    __tablename__ = 'prediction_models'
    equipment_id: int
    model_type: str              # linear, moving_avg, threshold
    parameters: JSON
    trained_at: DateTime
    accuracy: Numeric(5,2)
    is_active: bool

class MaintenancePrediction(BaseModel):
    __tablename__ = 'maintenance_predictions'
    equipment_id: int
    model_id: int
    predicted_failure_date: Date
    confidence: Numeric(5,2)
    risk_level: str              # low, medium, high, critical
    recommended_action: str
    created_at: DateTime
    is_acknowledged: bool
```

### Servis Metotlari

```python
class PredictiveService:
    record_reading(equipment_id, sensor_type, value) -> SensorReading
    detect_anomaly(equipment_id, readings) -> bool
    train_model(equipment_id, model_type) -> PredictionModel
    predict_failure(equipment_id) -> MaintenancePrediction
    get_risk_dashboard() -> Dict
    get_equipment_health(equipment_id) -> Dict
    suggest_maintenance_schedule(equipment_id) -> Dict
    calculate_mtbf(equipment_id) -> Numeric  # Mean Time Between Failures
    calculate_mttr(equipment_id) -> Numeric  # Mean Time To Repair
```

### Gorevler

| # | Gorev | Efor |
|---|-------|------|
| 1 | Sensor/Prediction tablolari + Alembic migration | 0.5 gun |
| 2 | `predictive.py` - Sensor veri kayit + anomali tespit | 1.5 gun |
| 3 | `predictive.py` - Basit tahmin modelleri (esik/trend) | 2 gun |
| 4 | `predictive.py` - MTBF/MTTR hesaplama | 1 gun |
| 5 | `predictive_module.py` + `prediction_dashboard.py` - UI | 1.5 gun |
| 6 | `sensor_config.py` - Sensor tanimlama UI | 0.5 gun |
| 7 | Risk gorunumu + uyari entegrasyonu | 1 gun |
| 8 | Mevcut bakim planlarina tahmin entegrasyonu | 0.5 gun |
| 9 | Menu + ikon kaydi | 0.25 gun |
| 10 | Test: Anomali tespit + tahmin + MTBF | 1 gun |

---

# OZET TABLO

| Modul | Tahmini Efor | Oncelik |
|-------|-------------|---------|
| **A1.** e-Fatura / e-Arsiv / e-Irsaliye | 4-6 hafta | KRITIK |
| **A2.** Sabit Kiymet Yonetimi | 3-4 hafta | YUKSEK |
| **A3.** KDV & Vergi Raporlari | 2-3 hafta | YUKSEK |
| **A4.** Maliyet Muhasebesi | 4-5 hafta | YUKSEK |
| **A5.** Butce Yonetimi | 3-4 hafta | ORTA |
| **B1.** Iade Yonetimi | 3-4 hafta | YUKSEK |
| **B2.** Sozlesme Yonetimi | 3-4 hafta | ORTA |
| **B3.** RFQ (Teklif Talebi) | 2-3 hafta | ORTA |
| **B4.** Tedarikci Degerlendirme | 2-3 hafta | ORTA |
| **C1.** Lot/Seri Izlenebilirlik | 3-4 hafta | YUKSEK |
| **C2.** APS Motoru | 5-6 hafta | YUKSEK |
| **C3.** SPC | 3-4 hafta | ORTA |
| **D1.** Ise Alim | 3-4 hafta | ORTA |
| **D2.** Proje Yonetimi | 4-5 hafta | ORTA |
| **E1.** Test Altyapisi | 2 hafta | KRITIK |
| **E2.** Workflow Tasarimcisi | 4-5 hafta | ORTA |
| **E3.** Bildirim Motoru | 2-3 hafta | ORTA |
| **E4.** REST API Katmani | 5-6 hafta | YUKSEK |
| **E5.** Cok Sirketli Yapi | 3-4 hafta | DUSUK |
| **F1.** EDI Entegrasyon | 3-4 hafta | DUSUK |
| **F2.** Web Arayuz | 8-10 hafta | ORTA |
| **F3.** Mobil Uygulama | 6-8 hafta | DUSUK |
| **F4.** Portal | 4-5 hafta | DUSUK |
| **G1.** BI Raporlama | 3-4 hafta | ORTA |
| **G2.** Kestirimci Bakim | 3-4 hafta | DUSUK |

---

# TEKNIK NOTLAR

## Mevcut Teknoloji Yigini

| Teknoloji | Versiyon | Durum |
|-----------|---------|-------|
| Python | 3.10+ | Mevcut |
| PyQt6 | 6.10.1 | Mevcut |
| PostgreSQL | - | Mevcut |
| SQLAlchemy | 2.0.45 | Mevcut |
| Alembic | 1.17.2 | Mevcut |
| FastAPI | 0.128.0 | Mevcut (requirements.txt'de) |
| uvicorn | 0.40.0 | Mevcut |
| Pydantic | 2.12.5 | Mevcut |
| httpx | 0.28.1 | Mevcut |
| Jinja2 | 3.1.6 | Mevcut |
| WeasyPrint | 67.0 | Mevcut |
| reportlab | 4.4.7 | Mevcut |
| pytest | 9.0.2 | Mevcut |
| pandas | 2.3.3 | Mevcut |
| numpy | 2.4.1 | Mevcut |

## Eklenecek Bagimliliklar

| Paket | Amac |
|-------|------|
| lxml | e-Fatura XSD validasyonu |
| PyJWT | REST API JWT token |
| python-multipart | FastAPI dosya yukleme |
| paramiko | SFTP baglantisi (EDI) |

## Mevcut Mimari Kaliplar

- **Service Pattern:** `__init__ → self.session = get_session()` + CRUD metotlari
- **View Pattern:** Module (QStackedWidget) → List (BaseListPage) → Form (QTabWidget + pyqtSignal)
- **Bridge Pattern:** `modules/<source>/services/<target>_bridge.py` + `@staticmethod`
- **Model Pattern:** Enum → `(str, Enum)`, tablolar → `BaseModel` (id, created_at, updated_at, is_active)
- **Kod Uretimi:** PREFIX + YYMM + 4-hane sira numarasi
- **Menu:** `config/menu_data.py`
- **Ikonlar:** `config/icons.py`
