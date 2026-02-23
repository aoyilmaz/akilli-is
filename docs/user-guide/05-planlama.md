# Planlama — Kullanıcı El Kitabı

> Bu bölüm, üretim planlaması, ürün reçeteleri, malzeme ihtiyaç hesaplama (MRP) ve kapasite analizini anlatır.

---

## Planlama Modülü Ne İşe Yarar?

"Ne kadar üretmeliyim? Hangi malzemeyi, ne zaman satın almalıyım? Kapasitem yeterli mi?" sorularını yanıtlar. İki temel plan türü kullanılır:

| Plan Türü | Açıklama |
|-----------|---------|
| **MPS** (Ana Üretim Programı) | Ne üretileceğini ve ne zaman üretileceğini belirler |
| **MRP** (Malzeme İhtiyaç Planlaması) | MPS'e göre malzeme gereksinimlerini hesaplar ve satın alma/üretim önerileri üretir |

---

## Arayüze İlk Bakış

Sol menüde **PLANLAMA** altındaki sayfalar:

| Sayfa | Ne İçin |
|-------|---------|
| MPS Kokpit | Ana üretim programı özeti |
| Üretim Planları | Plan listesi ve yönetimi |
| Kapasite Analizi | İş istasyonu yük/kapasite grafiği |
| MRP | Malzeme ihtiyaç hesaplama |
| Üretim Planlama | Gantt takvim görünümü |
| Ürün Reçeteleri (BOM) | Ürün bileşen ağaçları |
| İş İstasyonları | Makineler ve çalışma saatleri |
| Takvim | Çalışma takvimi tanımları |

---

## Bölüm 1: İş İstasyonları

### 1.1 İş İstasyonu Nedir?

Üretim yapılan makine veya çalışma alanıdır. Kapasite ve MRP hesaplamalarının doğru olması için her üretim noktasının sisteme tanıtılması gerekir.

### 1.2 Yeni İş İstasyonu Oluşturma

1. **İş İstasyonları** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Kod | Kısa benzersiz kod (örn: TK-01) |
| Ad | İstasyon adı (örn: Torna Tezgahı 1) |
| Tür | Makine / İnsan / Hat |
| Kapasite (saat/gün) | Günlük çalışma kapasitesi |
| Saat Maliyeti | Makine başına saatlik maliyet |
| Çalışma Takvimi | Hangi günler, kaç saat çalışıyor |

3. **Kaydet**

---

## Bölüm 2: Çalışma Takvimi

### 2.1 Takvim Nedir?

İş istasyonlarının hangi günler ve saatler arasında çalıştığını tanımlar. Tatil günleri, mesai saatleri ve vardiya düzenini içerir.

### 2.2 Yeni Takvim Oluşturma

1. **Takvim** → **Yeni Ekle**
2. Haftalık çalışma günlerini ve saatlerini girin
3. Resmi tatil günlerini ekleyin
4. **Kaydet**

---

## Bölüm 3: Ürün Reçeteleri (BOM)

### Ürün Reçetesi Nedir?

Bir ürünü üretmek için gereken tüm malzemeler, yarı mamuller ve yapılacak operasyonların listesidir. Üretim modülünün çalışması için zorunludur.

---

### 3.1 Yeni Ürün Reçetesi Oluşturma

1. **Ürün Reçeteleri** → **Yeni Ekle**
2. **Mamul** seçin (üretilecek ürün)
3. **Versiyon** ve **Revizyon** numarası girin (örn: V1.0)
4. **Geçerlilik Tarihi** girin
5. Doldurun:

**Bileşenler sekmesi:**
- **Kalem Ekle** → Hammadde veya yarı mamul seçin
- Miktar, birim girin
- Sarf edildiği operasyon adımını seçin

**Operasyonlar sekmesi:**
- **Operasyon Ekle** → Sıra no, ad, iş istasyonu seçin
- Planlanan süre girin (dakika/adet)

**Yan Ürünler sekmesi** (isteğe bağlı):
- Üretim sırasında ortaya çıkan yan ürünler

6. **Kaydet**

---

### 3.2 BOM Ağacı Görüntüleme

Karmaşık ürünlerde bileşenler birden fazla seviye derinleşebilir (yarı mamulün de kendi reçetesi vardır). **BOM Ağacı** görünümüyle tüm bileşenleri hiyerarşik olarak görebilirsiniz.

> 💡 **İpucu:** BOM değişikliği yaparken yeni versiyon oluşturun. Eski versiyonu silmeyin — üretilen geçmiş siparişlerin hangi reçeteyle üretildiği kaybolur.

---

### Sık Sorulan Sorular

**Ürün reçetesini güncelledim, açık iş emirleri etkilenir mi?**
Hayır. Açık iş emirleri oluşturulduklarındaki reçeteyi kullanmaya devam eder.

---

## Bölüm 4: MPS (Ana Üretim Programı)

### MPS Nedir?

Belirli bir dönemde hangi üründen ne kadar üretileceğini planlayan çizelgedir. Satış siparişlerini, tahminleri ve stok seviyelerini dikkate alarak üretim hedefleri belirler.

---

### 4.1 Üretim Planı Oluşturma

1. **Üretim Planları** → **Yeni Ekle**
2. Dönem başlangıç ve bitiş tarihini girin
3. Her mamul için planlama satırı ekleyin:
   - Mamul seçin
   - Dönem içindeki hedef miktarı girin
   - Haftalık veya günlük dağılım yapın
4. **Kaydet**

---

### 4.2 MPS Kokpit

MPS Kokpit sayfası planlamacıya özet bir bakış sunar:
- Bu hafta üretilmesi gerekenler
- Tamamlanan ve devam eden iş emirleri
- Geciken emirler
- Kapasite kullanım oranı

---

## Bölüm 5: Kapasite Analizi

### 5.1 Kapasite Nedir?

Her iş istasyonunun günlük/haftalık karşılayabileceği maksimum iş yükü miktarıdır.

### 5.2 Kapasite Analizi Sayfası

- **Kapasite Analizi** sayfasında her iş istasyonu için yük/kapasite çubuk grafikleri görüntülenir
- **Mavi çubuk:** Planlanan yük
- **Turuncu çizgi:** Mevcut kapasite

İş istasyonu kapasitesini aşarsa kırmızıya döner; planlama yeniden düzenlenmelidir.

---

## Bölüm 6: MRP (Malzeme İhtiyaç Planlaması)

### MRP Nedir?

Üretim planındaki mamulleri üretmek için gereken malzemeleri hesaplar ve yetersiz olanlar için satın alma veya üretim önerisi oluşturur.

**MRP Hesaplama Mantığı:**

```
Brüt İhtiyaç (Üretilmesi Gereken)
        -
Mevcut Stok + Bekleyen Siparişler
        =
Net İhtiyaç
        ↓
Satın Alma Önerisi / Üretim Önerisi
```

---

### 6.1 MRP Çalıştırma

1. **MRP** sayfasına gidin
2. Hesaplama dönemi girin (başlangıç — bitiş)
3. **Hesapla** butonuna tıklayın
4. Sistem birkaç dakika içinde sonuçları listeler

---

### 6.2 MRP Sonuçlarını Değerlendirme

| Öneri Türü | Anlamı | Yapılacak İşlem |
|-----------|--------|----------------|
| **Satın Al** | Bu malzeme satın alınmalı | Satın alma talebi oluştur |
| **Üret** | Bu yarı mamul üretilmeli | İş emri oluştur |
| **Transfer Et** | Başka depodan getir | Transfer hareketi yap |
| **İptal Et** | Açık sipariş fazla, iptal gerekiyor | Siparişi iptal et |

---

### 6.3 MRP'den Sipariş Oluşturma

1. MRP sonuçlarında ilgili "Satın Al" satırını seçin
2. **Satın Alma Talebi Oluştur** butonuna tıklayın
3. Sistem otomatik talep oluşturur
4. Talep onaylandıktan sonra satın alma siparişine dönüştürülür

---

## Bölüm 7: Üretim Planlama (Gantt Görünümü)

Gantt görünümünde iş emirleri takvim üzerinde çubuklar halinde gösterilir. Çubukları sürükleyerek tarih değiştirebilir, iş istasyonları arasında taşıyabilirsiniz.

> 💡 **İpucu:** Bu görünüm özellikle kısa dönemli ince ayar yapmak için kullanışlıdır.

---

## Bölüm 8: Diğer Modüllerle Bağlantı

| Modül | Bağlantı |
|-------|---------|
| **Üretim** | MRP'den iş emirleri; BOM'dan malzeme listesi |
| **Satınalma** | MRP satın alma önerileri → talep/sipariş |
| **Stok** | Mevcut stok seviyeleri MRP hesabına girer |
| **Satış** | Satış siparişleri MPS'e otomatik girer |
| **Bakım** | İş istasyonu bakımda → kapasite azalır |

---

## Hızlı Başlangıç Listesi

- [ ] İş istasyonlarını tanımlayın
- [ ] Çalışma takvimini oluşturun
- [ ] Ürün reçetelerini oluşturun
- [ ] İlk üretim planını oluşturun (MPS)
- [ ] MRP'yi çalıştırın ve önerileri değerlendirin

---

*Önceki: [Üretim ←](04-uretim.md) | Sonraki: [Kalite Kontrol →](06-kalite.md)*
