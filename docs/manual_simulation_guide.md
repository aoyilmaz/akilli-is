
# Gerçek Hayat Simülasyonu: "Özel Seri Yönetici Masası" (Executive Office Desk)

Bu doküman, **Akıllı İş ERP** sisteminin tüm modüllerini kapsayan, sizin tarafınızdan manuel olarak yürütülecek bir uçtan uca simülasyon senaryosudur.

**Hedef:** Bir müşteriden gelen özel siparişi yönetmek, malzeme eksiğini tedarik etmek, üretimi planlamak, üretmek ve sevk etmek.

---

## 🏗 Kısım 1: Master Data Hazırlığı (Mühendislik & Stok)
Sistemi üretime hazırlamak için gerekli tanımları yapacağız.

### Adım 1.1: Stok Kartlarını Oluşturun
Sol Menü: **Stok Yönetimi > Stok Kartları > Yeni Ekle**

Aşağıdaki ürünleri sırasıyla sisteme girin:

1.  **Hammadde 1 (Ahşap):**
    *   **Kod:** `RAW_WALNUT`
    *   **Ad:** Ceviz Kaplama Tabla
    *   **Tip:** Hammadde
    *   **Birim:** Adet
    *   **Alış Fiyatı:** 2000 TL

2.  **Hammadde 2 (Metal):**
    *   **Kod:** `RAW_FRAME`
    *   **Ad:** Krom Ayak İskeleti
    *   **Tip:** Hammadde
    *   **Birim:** Adet
    *   **Alış Fiyatı:** 1500 TL

3.  **Mamül (Ürün):**
    *   **Kod:** `PRD_EXEC_DESK`
    *   **Ad:** Yönetici Masası (Premium)
    *   **Tip:** Mamül
    *   **Birim:** Adet
    *   **Satış Fiyatı:** 15.000 TL
    *   **MRP Sekmesi:** "Üretim (Make)" seçili, Temin Süresi: 3 Gün.

### Adım 1.2: İş İstasyonlarını Tanımlayın
Sol Menü: **Üretim Yönetimi > İş İstasyonları > Yeni Ekle**

1.  **Kod:** `WS_CNC` | **Ad:** CNC Kesim | **Tip:** Makine | **Saatlik Ücret:** 500 TL
2.  **Kod:** `WS_MONT` | **Ad:** Montaj Masası | **Tip:** Montaj | **Saatlik Ücret:** 300 TL

### Adım 1.3: Ürün Reçetesi (BOM) Oluşturun
Sol Menü: **Üretim Yönetimi > Ürün Reçeteleri (BOM) > Yeni Ekle**

*   **Ürün:** `PRD_EXEC_DESK` (Yönetici Masası)
*   **Miktar:** 1 Adet
*   **Malzemeler (Alt kısım):**
    *   `RAW_WALNUT` - 1 Adet
    *   `RAW_FRAME` - 1 Adet
*   **Operasyonlar (Sağ sekme veya Alt kısım):**
    1.  **Kesim** -> `WS_CNC` -> Süre: 45 dk
    2.  **Montaj** -> `WS_MONT` -> Süre: 60 dk
*   **Kaydet** butonuna basın.

---

## 🛒 Kısım 2: Satış ve Talep (CRM & Sales)
Müşteri siparişi ile süreci başlatalım.

### Adım 2.1: Müşteri Tanımlayın
Sol Menü: **Satış Yönetimi > Müşteriler > Yeni Ekle**
*   **Firma Adı:** Global Holding A.Ş.
*   **Yetkili:** Ayşe Yılmaz
*   **Kaydet.**

### Adım 2.2: Satış Siparişi Oluşturun
Sol Menü: **Satış Yönetimi > Satış Siparişleri > Yeni Ekle**
*   **Müşteri:** Global Holding A.Ş.
*   **Ürün Ekle:** `PRD_EXEC_DESK`
*   **Miktar:** 5 Adet
*   **Birim Fiyat:** 15.000 TL (Otomatik gelebilir)
*   **Teslim Tarihi:** Bugünden 1 hafta sonrası.
*   **Kaydet.**
*   **Onayla (Confirm) butonuna basın.** (Durum: Confirmed olmalı)

---

## 🧠 Kısım 3: Planlama (MRP)
Sipariş geldi ama elimizde masa yok. Ayrıca `RAW_FRAME` stoğumuz da 0 olsun.

### Adım 3.1: MRP Çalıştırın
Sol Menü: **Üretim Yönetimi > MRP (Planlama) > Yeni MRP Çalıştır**
*   **Simülasyon Modu:** Kapalı (veya varsayılan).
*   **Çalıştır** butonuna basın.

### Adım 3.2: Sonuçları İnceleyin
Oluşan MRP kaydına çift tıklayın veya "Detay" deyin.
*   **Üretim Önerileri:** 5 Adet `PRD_EXEC_DESK` için "Planlı Sipariş" (Planned Order) oluşmalı.
*   **Satınalma Önerileri:** Stokta hiç `RAW_FRAME` ve `RAW_WALNUT` yoksa, bunlar için "Satınalma İsteği" (Purchase Request) önerisi görmelisiniz.

---

## 📦 Kısım 4: Satınalma (Tedarik)
MRP, hammadde eksiği uyarısı verdi. Malzemeleri alalım.

### Adım 4.1: Satınalma Siparişi (PO)
Sol Menü: **Satınalma > Siparişler > Yeni Ekle**
*   **Tedarikçi:** Yeni oluşturun -> "Hammadde Tedarik Ltd."
*   **Kalemler:**
    *   `RAW_WALNUT`: 10 Adet (Biraz fazla alalım)
    *   `RAW_FRAME`: 10 Adet
*   **Kaydet** ve **Onayla**.

### Adım 4.2: Mal Kabul (Goods Receipt)
Kamyon fabrikaya geldi, malzemeyi depoya alıyoruz.
Sol Menü: **Satınalma > Mal Kabul (İrsaliye) > Yeni Ekle**
*   **Sipariş Seç:** Az önce oluşturduğunuz PO'yu seçin.
*   **Depo:** Ana Depo (Varsayılan).
*   **Kaydet.**
*   *Kontrol:* **Stok Yönetimi > Stok Kartları** listesinde hammaddelerin miktarının arttığını doğrulayın.

---

## 🏭 Kısım 5: Üretim Yürütme (Shop Floor)
Malzemeler geldi, şimdi masaları üretelim.

### Adım 5.1: İş Emrine Dönüştürme
Sol Menü: **Planlama (MRP)** ekranına dönün veya **Üretim > İş Emirleri > Yeni Ekle**.
*   (Manuel Ekleme Yolu): **Ürün:** `PRD_EXEC_DESK`, **Miktar:** 5.
*   **Kaydet.** (Durum: Planned)

### Adım 5.2: Üretimi Başlatma
Oluşan İş Emrine (WO) gidin.
1.  **Malzeme Kontrol (Check):** Stok var mı? (Tedarik yapmıştık, olmalı).
2.  **Yayınla (Release):** Butona basın. (Malzemeler rezerve edilir).
3.  **Başlat (Start):** Üretim başlar. (Hammadde stoktan düşer - Work in Progress'e geçer).

### Adım 5.3: Operasyon Bildirimi (Terminal)
Sol Menü: **Üretim > Operatör Paneli (veya İş Emri Detayı > Operasyonlar)**
1.  **Kesim** operasyonu için "Başlat" deyin. Bir süre sonra "Tamamla" deyin. (Süre girişi yapın: örn. 220 dk).
2.  **Montaj** operasyonu için "Başlat" ve "Tamamla". (Süre: 300 dk).

### Adım 5.4: Üretimi Bitir
İş Emri detayında "Üretimi Tamamla" butonuna basın.
*   Üretilen Miktar: 5.
*   Hurda (Scrap): 0.
*   **Kaydet.** (Durum: Quality Check veya Completed olur).

---

## ✅ Kısım 6: Kalite ve Sevkiyat
Ürün bitti, son kontroller ve müşteriye gönderim.

### Adım 6.1: Kalite Kontrol (Opsiyonel)
Eğer sistem "Kalite Kontrol Gerekli" modundaysa:
*   İş Emri detayında "Kalite Onayı" sekmesine/butonuna gidin.
*   **Kabul Edilen:** 5.
*   **Onayla.**

### Adım 6.2: Sevkiyat (İrsaliye)
Sol Menü: **Satış Yönetimi > İrsaliyeler (Delivery Notes) > Yeni Ekle**
*   **Sipariş Seç:** Baştaki Global Holding siparişini seçin.
*   **Miktar:** 5 Adet (Otomatik dolmalı).
*   **Kaydet.** (Stoktan `PRD_EXEC_DESK` düşer).

### Adım 6.3: Fatura Kesimi
Sol Menü: **Satış Yönetimi > Faturalar > Yeni Ekle**
*   İrsaliyeyi seçerek faturaya dönüştürün.
*   **Kaydet.**

---

## 🎉 Sonuç
Tebrikler!
1.  Sıfırdan ürün tasarladınız (BOM).
2.  Sipariş aldınız.
3.  Eksik malzemeyi planlayıp satın aldınız.
4.  Üretimi gerçekleştirdiniz.
5.  Ürünü müşteriye teslim edip faturalandırdınız.

Veritabanında şu an:
*   `RAW_WALNUT` stoğu: 5 (10 alındı, 5 kullanıldı).
*   `PRD_EXEC_DESK` stoğu: 0 (5 üretildi, 5 satıldı).
*   Muhasebe tarafında Global Holding borçlandı.
