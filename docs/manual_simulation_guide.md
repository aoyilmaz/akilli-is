# Gerçek Hayat Simülasyonu: "Özel Seri Yönetici Masası" (Executive Office Desk) - Detaylı Yönerge

Bu doküman, **Akıllı İş ERP** sisteminin tüm modüllerini kapsayan, en ince detayına kadar manuel olarak yürütülecek bir uçtan uca simülasyon senaryosudur. Amacımız, sistemi sadece "çalıştırmak" değil, "gerçek bir işletme gibi" tüm veri alanlarını doldurarak test etmektir.

**Senaryo:** "VIP Mobilya" müşterisinden gelen 10 adet özel tasarım yönetici masası siparişini (Make-to-Order) uçtan uca yöneteceğiz.

---

## 🏗 Kısım 1: Master Data Hazırlığı (Mühendislik & Stok)

### Adım 1.1: Stok Birimlerini Kontrol Edin
Sol Menü: **Stok Yönetimi > Birimler**
*   **Adet** biriminin olduğundan emin olun.
    *   **Kod:** `AD` | **Ad:** `Adet`
    *   *Yoksa:* **Yeni Ekle** butonuna basarak tanımlayın.

### Adım 1.2: Kategorileri Oluşturun
Sol Menü: **Stok Yönetimi > Kategoriler > Yeni Ekle**
1.  **Ad:** `Hammaddeler` | **Kod:** `CAT-RAW`
2.  **Ad:** `Mamüller` | **Kod:** `CAT-PRD`

### Adım 1.3: Stok Kartlarını (Items) Oluşturun
Sol Menü: **Stok Yönetimi > Stok Kartları > Yeni Ekle**

Aşağıdaki kartları **tüm detaylarıyla** girin:

#### A. Hammadde 1: Ceviz Kaplama
*   **Genel Bilgiler:**
    *   **Kod:** `RAW_WALNUT_001`
    *   **Ad:** Premium Ceviz Kaplama Tabla (200x100cm)
    *   **Kısa Ad:** Ceviz Kaplama
    *   **Tip:** Hammadde | **Kategori:** Hammaddeler
    *   **Birim:** Adet
    *   **KDV Oranı:** %20 | **Tevkifat:** %0
*   **Stok/Depo:**
    *   **Min Stok:** 10 | **Maks Stok:** 200
    *   **Raf Ömrü:** 365 Gün
    *   **Raf/Göz:** A-01-01 (Varsa)
*   **Fiyat:**
    *   **Alış Fiyatı:** 2.000 TL | **Para Birimi:** TRY
*   **MRP & Tedarik:**
    *   **Planlama Yöntemi:** Satınalma (Buy)
    *   **Temin Süresi:** 5 Gün
    *   **Min Sipariş:** 5 | **Sipariş Katı:** 1
    *   **Lot Takibi:** Evet (İzlenebilirlik için önemli - İşaretleyin)
*   **Boyutlar:**
    *   **Ağırlık:** 15 kg
    *   **Ebat:** 200x100x5 cm

#### B. Hammadde 2: Krom İskelet
*   **Genel Bilgiler:**
    *   **Kod:** `RAW_FRAME_X1`
    *   **Ad:** Krom Ayak İskeleti (X-Tipi)
    *   **Tip:** Hammadde | **Kategori:** Hammaddeler
    *   **Birim:** Adet
    *   **KDV:** %20
*   **Fiyat:**
    *   **Alış Fiyatı:** 1.500 TL
*   **MRP:**
    *   **Planlama:** Satınalma (Buy)
    *   **Temin Süresi:** 3 Gün
    *   **Min Sipariş:** 10
*   **Özellikler:**
    *   **Tedarikçi Kodu:** MTL-FRM-001
    *   **Marka:** MetalMaster
    *   **Kalite Kontrol:** Zorunlu (Girişte pas kontrolü için - İşaretleyin)

#### C. Yardımcı Malzeme: Vida Seti
*   **Kod:** `RAW_SCREW_SET`
*   **Ad:** Montaj Vida Seti (50'li Paket)
*   **Tip:** Hammadde | **Kategori:** Hammaddeler
*   **Alış Fiyatı:** 50 TL
*   **MRP:** Satınalma, Temin Süresi 1 Gün.

#### D. Mamül: Yönetici Masası
*   **Genel Bilgiler:**
    *   **Kod:** `PRD_EXEC_DESK_V1`
    *   **Ad:** Yönetici Masası (Premium - Ceviz)
    *   **Tip:** Mamül | **Kategori:** Mamüller
    *   **Birim:** Adet
*   **Fiyat:**
    *   **Satış Fiyatı:** 15.000 TL
*   **MRP:**
    *   **Planlama Yöntemi:** Üretim (Make)
    *   **Temin Süresi:** 3 Gün
    *   **Emniyet Stoğu:** 0 (Siparişe göre üretim yapacağız)

---

### Adım 1.4: İş İstasyonlarını (Work Stations) Tanımlayın
Sol Menü: **Üretim Yönetimi > İş İstasyonları > Yeni Ekle**

#### 1. İstasyon: CNC Merkezi
*   **Kod:** `WS_CNC_01`
*   **Ad:** CNC Kesim ve İşleme Merkezi
*   **Tip:** Makine
*   **Açıklama:** "Biesse Rover - 5 Eksen CNC"
*   **Lokasyon:** Üretim Holü A / Hat 1
*   **Kapasite/Gün:** 8 Saat (480 dk) | **Vardiya:** Tek Vardiya
*   **Verimlilik:** %90 (Beklenen OEE)
*   **Maliyetler:**
    *   **Saatlik Ücret (Labor):** 500 TL (Operatör maliyeti)
    *   **Genel Gider (Overhead):** 200 TL / Saat (Elektrik, amortisman vb.)

#### 2. İstasyon: Montaj Hattı
*   **Kod:** `WS_MONT_01`
*   **Ad:** Manuel Montaj Tezgahı
*   **Tip:** Montaj (İşçilik)
*   **Lokasyon:** Montaj Alanı (Kat 2)
*   **Kapasite/Gün:** 8 Saat
*   **Verimlilik:** %100 (Manuel işlem)
*   **Maliyetler:**
    *   **Saatlik Ücret:** 300 TL
    *   **Genel Gider:** 100 TL / Saat

---

### Adım 1.5: Ürün Reçetesi (BOM) Oluşturun
Sol Menü: **Üretim Yönetimi > Ürün Reçeteleri > Yeni Ekle**

*   **Başlık Bilgileri:**
    *   **Ürün:** `PRD_EXEC_DESK_V1` - Yönetici Masası
    *   **Reçete Kodu:** `BOM-EXEC-001`
    *   **Ad:** Standart Üretim Reçetesi
    *   **Tip:** Standart
    *   **Miktar:** 1 Adet
    *   **Durum:** Aktif
    *   **Revizyon:** 0 (Otomatik)

*   **Malzemeler (BOM Lines):**
    1.  **Ceviz Kaplama** (`RAW_WALNUT_001`):
        *   **Miktar:** 1 | **Birim:** Adet
        *   **Fire Oranı (Scrap):** %5 (Kesim firesi olarak planlanır)
    2.  **Krom İskelet** (`RAW_FRAME_X1`):
        *   **Miktar:** 1 | **Birim:** Adet
        *   **Fire Oranı:** %0
    3.  **Vida Seti** (`RAW_SCREW_SET`):
        *   **Miktar:** 1 | **Birim:** Adet (Paket)
        *   **Fire Oranı:** %0

*   **Operasyonlar (Rota/Routing):**
    *   **Operasyon 10: Tabla Kesim**
        *   **İşlem:** Kesim
        *   **İstasyon:** `WS_CNC_01`
        *   **Hazırlık Süresi (Setup):** 15 dk (Makine programlama)
        *   **İşlem Süresi (Run):** 45 dk (Parça başına net süre)
        *   **Açıklama:** "Desen yönüne dikkat edilecek."
    *   **Operasyon 20: Montaj**
        *   **İşlem:** Montaj
        *   **İstasyon:** `WS_MONT_01`
        *   **Hazırlık Süresi:** 10 dk (Tezgah hazırlığı)
        *   **İşlem Süresi:** 60 dk
        *   **Kalite Kontrol:** Evet (Montaj sonrası gözle kontrol - İşaretleyin)

*   **Kaydet** butonuna basın.

---

## 🛒 Kısım 2: Satış ve Talep (CRM & Sales)

### Adım 2.1: Müşteri Kartı
Sol Menü: **Satış Yönetimi > Müşteriler > Yeni Ekle**
*   **Firma Adı:** VIP Mobilya A.Ş.
*   **Kısa Ad:** VIP
*   **Vergi No:** 1234567890 | **Vergi Dairesi:** Beşiktaş
*   **İletişim:** Ahmet Demir
*   **E-Posta:** ahmet@vipmobilya.com
*   **Telefon:** 0555 123 45 67 | **Faks:** 0212 999 88 77
*   **Web:** www.vipmobilya.com
*   **Adres:** Mobilyacılar Sitesi, A Blok No:5
*   **Şehir:** İstanbul | **İlçe:** Başakşehir
*   **Ödeme Koşulu:** 30 Gün Vadeli
*   **Kredi Limiti:** 1.000.000 TL
*   **Para Birimi:** TRY
*   **Notlar:** Özel müşteri, teslimat öncesi randevu alınmalı.
*   **Kaydet.**

### Adım 2.2: Satış Siparişi (SO)
Sol Menü: **Satış Yönetimi > Satış Siparişleri > Yeni Ekle**
*   **Sipariş No:** (Otomatik)
*   **Müşteri:** VIP Mobilya A.Ş.
*   **Sipariş Tarihi:** Bugün
*   **Teslim Tarihi:** Bugünden 10 gün sonra.
*   **Kalemler:**
    *   **Ürün:** `PRD_EXEC_DESK_V1`
    *   **Miktar:** 10 Adet
    *   **Birim Fiyat:** 15.000 TL
    *   **KDV:** %20
    *   **Toplam:** 150.000 TL + KDV
*   **Açıklama:** "Acil sipariş, kalite kontrol raporu ile teslim edilecek."
*   **Kaydet.**
*   **Onayla (Confirm).** (Sipariş kesinleşmeden MRP görmez).

---

## 🧠 Kısım 3: Planlama (MRP)

### Adım 3.1: Stok Kontrolü (Simülasyon Öncesi)
Sol Menü: **Stok Yönetimi > Stok Kartları**.
*   Tüm hammaddelerin (`RAW_...`) stoğunun **0** olduğundan emin olun.

### Adım 3.2: MRP Çalıştırma
Sol Menü: **Üretim Yönetimi > MRP (Planlama) > Yeni MRP Çalıştır**
*   **Hazırlık (Horizon) Günü:** 30 Gün
*   **Depo:** Tümü (veya Ana Depo)
*   **Çalıştır**'a basın.

### Adım 3.3: Önerileri Analiz Etme
MRP sonuç ekranını inceleyin:
1.  **Üretim Önerisi:** 10 Adet `PRD_EXEC_DESK_V1` için "Planlı Sipariş" (Planned Order). Kaynağı: Satış Siparişi.
2.  **Satınalma Önerileri:**
    *   10 Adet `RAW_WALNUT_001` (Planlanan üretim için)
    *   10 Adet `RAW_FRAME_X1`
    *   10 Adet `RAW_SCREW_SET`

---

## 📦 Kısım 4: Satınalma (Tedarik)

### Adım 4.1: Tedarikçi Tanımlama
Sol Menü: **Satınalma > Tedarikçiler > Yeni Ekle**

#### 1. Tedarikçi: Hammadde Tedarik Ltd.
*   **Ad:** Hammadde Tedarik Ltd.Şti. | **Kısa Ad:** HM-TED
*   **Vergi No:** 5000000001 | **Vergi Dairesi:** Beşiktaş
*   **İletişim:** Kemal Yılmaz | **Tel:** 0212 999 99 99
*   **Adres:** Keresteciler Sitesi, No:12, İstanbul
*   **Notlar:** "Ana hammadde tedarikçisi. Vade: 60 Gün."

#### 2. Tedarikçi: Metal İşleri A.Ş.
*   **Ad:** Metal İşleri Sanayi A.Ş. | **Kısa Ad:** MTL-AS
*   **Vergi No:** 3000000002
*   **Tel:** 0216 888 88 88
*   **Adres:** İmes Sanayi Sitesi, B Blok, İstanbul

### Adım 4.2: Satınalma Siparişi (PO) Oluşturma
MRP önerilerini seçerek **"Siparişe Dönüştür"** diyebilir veya manuel oluşturabilirsiniz.

#### PO-001 (Ahşap ve Vida)
*   **Tedarikçi:** Hammadde Tedarik Ltd.
*   **Para Birimi:** TRY | **Ödeme:** 60 Gün Vadeli
*   **Termin:** +5 Gün
*   **Kalemler:**
    1.  `RAW_WALNUT_001`: 10 Adet | **Birim Fiyat:** 2.000 TL
    2.  `RAW_SCREW_SET`: 10 Adet | **Birim Fiyat:** 50 TL
*   **Toplam:** 20.500 TL + KDV
*   **Kaydet & Onayla.**

#### PO-002 (Metal İskelet)
*   **Tedarikçi:** Metal İşleri A.Ş.
*   **Kalemler:**
    1.  `RAW_FRAME_X1`: 10 Adet | **Birim Fiyat:** 1.500 TL
*   **Toplam:** 15.000 TL + KDV
*   **Kaydet & Onayla.**

### Adım 4.3: Depoya Mal Kabul (Goods Receipt)
Malzemeler fabrikaya geldiğinde:
Sol Menü: **Satınalma > Mal Kabul > Yeni Ekle**
*   **Kaynak:** Satınalma Siparişi
*   **Sipariş No:** Oluşturduğunuz PO'yu seçin (PO-001).
*   **İrsaliye No:** İRS-2026-A01
*   **Depo:** Ana Depo.
*   **Miktar Kontrolü:** 10/10 Adet (Tam Teslimat)
*   **Tarih:** Bugün
*   **Kaydet.** (Stoklara giriş yapılır).
*   *(Aynı işlemi Metal İskelet siparişi PO-002 için de yapın)*.

*Kontrol:* **Stok Yönetimi > Stok Kartları** listesinde hammaddelerin stok miktarının arttığını doğrulayın.

---

## 🏭 Kısım 5: Üretim Yürütme (Execution)

### Adım 5.1: İş Emri (WO) Oluşturma
Sol Menü: **Üretim Yönetimi > İş Emirleri > Yeni Ekle** (Veya MRP sonuçlarından dönüştür).
*   **Ürün:** `PRD_EXEC_DESK_V1`
*   **Miktar:** 10
*   **Kaynak Depo:** Ana Depo (Hammaddelerin olduğu yer)
*   **Hedef Depo:** Mamül Deposu (Varsayılan yoksa Ana Depo)
*   **Planlanan Başlangıç:** Bugün | **Bitiş:** +3 Gün
*   **Öncelik:** Acil (High)
*   **Açıklama:** "VIP Mobilya Siparişi - Termin kritik!"
*   **Kaydet.** (Durum: **Planned**)

### Adım 5.2: Hazırlık ve Rezervasyon
İş Emri detayına gidin:
1.  **Malzeme Durumu:** "Mevcut" (Tedarik yapıldığı için).
2.  **Yayınla (Release):** Butona basın.
    *   *Sistem Arkaplanda:* `RAW_` malzemeleri bu iş emrine rezerve eder (Reserve).
    *   *Durum:* **Released**.

### Adım 5.3: Üretimi Başlatma
*   **Başlat (Start Production):**
    *   *Sistem Arkaplanda:* Hammaddeler stoktan düşer (Work-Order-Issue / Backflush).
    *   *Durum:* **In Progress**.

### Adım 5.4: Operasyon Takibi (Saha Verisi)
**Operatör Paneli** veya İş Emri > **Operasyonlar** sekmesine gidin.

**1. Operasyon: Tabla Kesim (CNC)**
*   **Operatör:** (Kullanıcı seçin)
*   **Başlat:** Saati not edin (Örn: 09:00).
*   **Durdur/Tamamla:**
    *   **Bitiş:** 19:00 (10 saat çalışma)
    *   **Net Süre:** 600 dk (10 x 45 dk + 15 Setup + Beklemeler)
    *   **Üretilen:** 10 Adet
    *   **Fire:** 0
    *   **Not:** "Bıçak değişimi yapıldı."

**2. Operasyon: Montaj**
*   **Operatör:** (Başka kullanıcı veya aynı)
*   **Başlat.**
*   **Tamamla:**
    *   **Süre:** 700 dk (10 x 60 dk + Setup)
    *   **Üretilen:** 10 Adet.

### Adım 5.5: Üretimi Tamamlama (Receipt)
İş Emri detayında **Tamamla (Complete Production)** butonuna basın.
*   **Tamamlanan Miktar:** 10 Adet.
*   **Hedef Lokasyon:** Kalite Kontrol (veya Karantina)
    *   *Not:* Kalite modülü aktif olduğu için ürünler 'Stok'a değil 'Karantina'ya düşebilir.
*   **Kaydet.** (Durum: **Quality Check**).

---

## ✅ Kısım 6: Kalite Kontrol (QC) & Sevkiyat

### Adım 6.1: Kalite Kontrol (Opsiyonel)
Eğer sistem "Kalite Kontrol Gerekli" modundaysa:
1.  **Kalite (Quality)** modülüne gidin > **Muayene Emirleri**.
2.  İş Emrinden gelen kaydı açın.
3.  **Ölçüm Girişi:**
    *   **Yüzey Kontrolü:** "Pürüzsüz, çizik yok" -> **Geçer (Pass)**.
    *   **Ebat Kontrolü:** "200x100 (+- 1mm)" -> **Geçer**.
    *   **Denge Testi:** "Sallanma yok" -> **Geçer**.
4.  **Karar (Decision):**
    *   **Kabul:** 10 Adet.
    *   **Red (Scrap):** 0 Adet.
5.  **Onayla.** (Stok durumu: *Available - Kullanılabilir*).

### Adım 6.2: Sevkiyat (Delivery Note)
Sol Menü: **Satış Yönetimi > İrsaliyeler > Yeni Ekle**
*   **Müşteri:** VIP Mobilya.
*   **Sipariş:** İlgili Satış Siparişini seçin.
*   **Kalemler:** 10 Adet Masa, Miktar kontrol edin.
*   **Araç Plaka:** 34 VR 345
*   **Şoför:** Mehmet K.
*   **Kaydet.** (Stoktan `PRD_EXEC_DESK` tamamen düşer).
*   **Yazdır** (PDF Önizleme alın).

### Adım 6.3: Fatura (Invoice)
İrsaliye üzerindeyken veya Fatura menüsünden:
*   **Faturaya Dönüştür.**
*   **Onayla.**
*   Sonuç: Müşteri cari hesabına **150.000 TL + KDV** borç işlenir.

---

## 📊 Kısım 7: Raporlama ve Analiz
Son olarak ne yaptığımızı görelim.

1.  **Stok Raporu:**
    *   `RAW_...` ürünler (Ceviz, İskelet) bitmiş olmalı.
    *   `PRD_...` ürünler üretildi ve sevk edildiği için bitmiş olmalı.
2.  **Maliyet Analizi (Costing):**
    *   İş Emri detayında "Maliyetler" sekmesine bakın.
    *   **Malzeme Maliyeti:** (2000 + 1500 + 50) * 10 = **35.500 TL**
    *   **İşçilik Maliyeti:** (600dk/60 * 500TL) + (700dk/60 * 300TL) ~ **8.500 TL**
    *   **Genel Gider:** ~ **4.000 TL**
    *   **Toplam Maliyet:** ~ 48.000 TL
    *   **Birim Maliyet:** ~ 4.800 TL
    *   **Kârlılık:** Satış (15.000) - Maliyet (4.800) = **Oldukça yüksek!**

Bu simülasyonu tamamladığınızda, bir ERP sisteminin tüm temel fonksiyonlarını (P2P ve O2C süreçlerini) başarıyla yönetmiş olacaksınız.
