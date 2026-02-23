# Kalite Kontrol — Kullanıcı El Kitabı

> Bu bölüm, ürün ve süreç kalitesini izlemek, uygunsuzlukları kayıt altına almak ve düzeltici faaliyetleri yönetmek için kullanılan Kalite Kontrol modülünü anlatır.

---

## Kalite Kontrol Modülü Ne İşe Yarar?

Üretimde veya mal kabulde ürün kalitesini ölçer, eksiklikleri kayıt altına alır ve bunları gidermek için sistematik bir süreç yürütür.

**Kapsam:**
- Giriş kalite kontrolü (mal kabulde)
- Üretim içi kalite kontrol
- Bitmiş ürün kalite kontrolü
- Müşteri şikayeti yönetimi
- Düzeltici ve önleyici faaliyetler (CAPA)
- İstatistiksel proses kontrolü (SPC)

---

## Arayüze İlk Bakış

Sol menüde **KALİTE KONTROL** altındaki sayfalar:

| Sayfa | Ne İçin |
|-------|---------|
| Denetimler | Kalite kontrol kayıtları |
| Uygunsuzluklar (NCR) | Standartların dışındaki durumlar |
| Müşteri Şikayetleri | Müşteriden gelen geri bildirimler |
| Düzeltici Önleyici Faaliyetler (CAPA) | Sorunların kalıcı çözümü |
| Denetim Şablonları | Tekrar kullanılan kontrol listeleri |
| SPC (İstatistiksel Kontrol) | Süreç istatistikleri ve kontrol grafikleri |

---

## Bölüm 1: Denetim Şablonları

### 1.1 Şablon Nedir?

Her denetimde aynı soruların/kontrollerin sorulması için önceden hazırlanan kontrol listesidir.

### 1.2 Yeni Şablon Oluşturma

1. **Denetim Şablonları** → **Yeni Ekle**
2. Şablon adı ve türünü girin (Giriş Kontrolü / Proses Kontrolü / Çıkış Kontrolü)
3. **Kontrol Maddeleri Ekle**:
   - Kontrol adı (örn: "Boyut toleransı")
   - Kontrol türü: Sayısal / Evet-Hayır / Görsel
   - Sayısal kontrolse: Min/Maks değer ve birim girin
4. **Kaydet**

---

## Bölüm 2: Denetimler

### 2.1 Yeni Denetim Oluşturma

1. **Denetimler** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Denetim Türü | Giriş / Proses / Çıkış / Periyodik |
| Şablon | Kullanılacak kontrol listesi |
| Ürün / Mal Kabul | Hangi ürün veya kabul için |
| Lot No | Kontrol edilen parti numarası |
| Numune Miktarı | Kaç adet inceleniyor |
| Denetçi | Kontrolü yapan kişi |

3. **Kontrol Sonuçlarını Girin**:
   - Her kontrol maddesi için değer veya Geçti/Kaldı seçin
4. **Kaydet**

---

### 2.2 Denetim Sonuçları

| Sonuç | Anlamı | Yapılacak |
|-------|--------|----------|
| **Geçti** | Tüm kontroller başarılı | Ürün normal süreçte devam eder |
| **Kaldı** | En az bir kontrol başarısız | NCR (Uygunsuzluk) oluştur |
| **Koşullu Kabul** | Ufak sapma var, kabul kararı verildi | Notla belge |

---

## Bölüm 3: Uygunsuzluklar (NCR)

### NCR Nedir?

NCR (Non-Conformity Report — Uygunsuzluk Raporu), bir ürünün, malzemenin veya sürecin istenen standartta olmadığını belgeleyen kayıttır.

---

### 3.1 Yeni NCR Oluşturma

1. **Uygunsuzluklar** → **Yeni Ekle**
   (veya denetim sonucunda otomatik oluşturulabilir)
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Uygunsuzluk Türü | Ürün / Süreç / Malzeme / Belge |
| Kaynak | Mal Kabul / Üretim / Müşteri |
| Etkilenen Lot/Ürün | Hangi parti etkileniyor |
| Açıklama | Uygunsuzluğun detayı |
| Tespit Eden | Kaydı açan kişi |
| Öncelik | Düşük / Orta / Yüksek / Kritik |

3. **Kaydet**

---

### 3.2 NCR Karar Seçenekleri

NCR incelendikten sonra karar verilir:

| Karar | Açıklama |
|-------|---------|
| **Kabul** | Ürün olduğu gibi kullanılacak |
| **Yeniden İşle** | Düzeltilip tekrar kontrol edilecek |
| **İade** | Tedarikçiye iade edilecek |
| **Hurda** | İmha edilecek |
| **Koşullu Kabul** | Müşteri onayıyla kullanılacak |

---

### 3.3 NCR Takibi

NCR listesinde açık/kapalı durumu, sorumlu kişi ve karar tarihine göre filtreyebilirsiniz.

---

## Bölüm 4: Müşteri Şikayetleri

### 4.1 Yeni Şikayet Kaydı

1. **Müşteri Şikayetleri** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Müşteri | Şikayeti bildiren firma |
| Tarih | Şikayet tarihi |
| Ürün / Sipariş | Şikayetin ilgili olduğu ürün |
| Şikayet Açıklaması | Müşterinin bildirdiği sorun |
| Kategori | Kalite / Teslimat / Fatura / Diğer |
| Öncelik | Normal / Acil |

3. **Kaydet**

---

### 4.2 Şikayet Çözüm Süreci

1. Şikayeti **Analiz Et** — kök nedenini araştırın
2. **CAPA Oluştur** — kalıcı çözüm için düzeltici faaliyet başlatın
3. Müşteriye geri bildirim verin
4. **Kapat**

---

## Bölüm 5: Düzeltici ve Önleyici Faaliyetler (CAPA)

### CAPA Nedir?

Bir sorunun tekrarlanmaması için kök nedeni bulan ve kalıcı çözüm üretilen sistematik faaliyet sürecidir.

- **Düzeltici Faaliyet:** Gerçekleşmiş bir sorunu gidermek için
- **Önleyici Faaliyet:** Henüz gerçekleşmemiş ancak riski görülen sorunları önlemek için

---

### 5.1 Yeni CAPA Oluşturma

1. **CAPA** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Tür | Düzeltici / Önleyici |
| Başlangıç Kaynağı | NCR / Şikayet / Denetim / Risk |
| Kök Neden Analizi | 5-Neden veya Balık Kılçığı sonucu |
| Planlanan Faaliyetler | Yapılacaklar listesi |
| Sorumlu Kişi | Faaliyeti yürütecek kişi |
| Hedef Tamamlanma Tarihi | Son tarih |

3. **Kaydet**

---

### 5.2 CAPA Doğrulama

Faaliyetler tamamlandıktan sonra:
1. **Doğrula** butonuna tıklayın
2. Etkinliği değerlendirin: sorun tekrar oluştu mu?
3. **Kapat** — CAPA tamamlandı

---

## Bölüm 6: SPC (İstatistiksel Proses Kontrolü)

### SPC Nedir?

Üretim sürecinde ölçülen değerlerin (ağırlık, boyut, sıcaklık vb.) kontrol sınırları içinde kalıp kalmadığını istatistiksel yöntemlerle izler.

---

### 6.1 Kontrol Grafiği Oluşturma

1. **SPC** → **Yeni Grafik**
2. Ölçüm türü ve birim girin
3. Alt ve üst kontrol sınırlarını belirleyin
4. Hedef değeri girin
5. **Kaydet**

Ölçüm değerleri girildiğinde grafik otomatik çizilir; sınır dışı noktalar kırmızı işaretlenir.

---

## Bölüm 7: Diğer Modüllerle Bağlantı

| Modül | Bağlantı |
|-------|---------|
| **Stok** | Karantina deposu — kalite onayı bekleyen ürünler |
| **Satınalma** | Mal kabulde giriş kalite kontrolü |
| **Üretim** | Proses ve çıkış kontrolü, fire kaydı |
| **Bakım** | Makine sorunu → NCR → CAPA döngüsü |

---

## Hızlı Başlangıç Listesi

- [ ] Denetim şablonlarını oluşturun
- [ ] İlk denetimi yapın (mal kabulden)
- [ ] Tespit edilen uygunsuzluk için NCR açın
- [ ] NCR için karar verin
- [ ] Tekrarlayan sorunlar için CAPA başlatın

---

*Önceki: [Planlama ←](05-planlama.md) | Sonraki: [Bakım & Onarım →](07-bakim.md)*
