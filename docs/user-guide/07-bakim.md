# Bakım & Onarım — Kullanıcı El Kitabı

> Bu bölüm, ekipman ve makine bakımını planlamayı, arıza takibini ve bakım geçmişini yönetmeyi anlatır.

---

## Bakım & Onarım Modülü Ne İşe Yarar?

Fabrikanızdaki makine ve ekipmanların bakımını planlar, arızaları kayıt altına alır ve geçmiş bakım bilgilerini tutar.

**Kapsam:**
- Ekipman/makine kartları
- Arıza talepleri (bakım çağrısı)
- Bakım iş emirleri
- Periyodik bakım planları
- Bakım raporları

---

## Arayüze İlk Bakış

Sol menüde **BAKIM & ONARIM** altındaki sayfalar:

| Sayfa | Ne İçin |
|-------|---------|
| Ekipmanlar | Makine ve ekipman kartları |
| Arıza Talepleri | Bozulma/arıza bildirimleri |
| İş Emirleri | Bakım/onarım görevleri |
| Bakım Planları | Periyodik bakım programları |
| Raporlar | Bakım ve arıza istatistikleri |

---

## Bölüm 1: Ekipmanlar

### 1.1 Ekipman Kartı Nedir?

Her makine, araç veya tesisata ait kimlik kartıdır. Bakım geçmişi, arıza sayısı ve bakım maliyeti bu kart üzerinde izlenir.

---

### 1.2 Yeni Ekipman Kartı Oluşturma

1. **Ekipmanlar** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Kod | Benzersiz ekipman kodu (örn: MKN-001) |
| Ad | Makinenin adı (örn: CNC Torna Tezgahı) |
| Kategori | Tezgah / Araç / Altyapı / Diğer |
| Marka / Model | Üretici bilgisi |
| Seri No | Üreticinin seri numarası |
| Satın Alma Tarihi | Ne zaman alındı |
| Garanti Bitiş Tarihi | Garanti sona erme tarihi |
| Lokasyon | Hangi alanda/binada |
| Sorumlu Kişi | Bakım sorumlusu |
| Çalışma Saatleri | Günlük çalışma süresi |

3. **Kaydet**

---

### 1.3 Ekipman Kartında Neler Görülür?

| Sekme | İçerik |
|-------|--------|
| Genel Bilgiler | Teknik detaylar |
| Bakım Geçmişi | Yapılan tüm bakım ve onarımlar |
| Arızalar | Geçmiş arıza kayıtları |
| Bakım Planları | Atanmış periyodik planlar |
| Belgeler | Teknik manuel, şema vb. dosyalar |

---

## Bölüm 2: Arıza Talepleri

### 2.1 Arıza Bildirimi Nedir?

Bir makine arızalandığında veya beklenmeyen bir sorun çıktığında oluşturulan acil bakım isteğidir.

---

### 2.2 Yeni Arıza Talebi Oluşturma

1. **Arıza Talepleri** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Ekipman | Arızalanan makine |
| Arıza Açıklaması | Ne olduğunu kısaca anlatın |
| Tespit Tarihi/Saati | Ne zaman fark edildi |
| Aciliyet | Düşük / Normal / Yüksek / Kritik (makine durmak üzere) |
| Bildiren Kişi | Arızayı fark eden operatör |

3. **Kaydet**

> 💡 **İpucu:** Arıza talep oluşturduktan sonra bakım ekibine bildirim gönderilir. Ayrıca aramak gerekmez.

---

### 2.3 Talep Durumları

| Durum | Anlamı |
|-------|--------|
| **Açık** | Henüz işleme alınmadı |
| **İşlemde** | Bakım ekibi çalışıyor |
| **Bekliyor** | Yedek parça bekleniyor |
| **Kapatıldı** | Sorun giderildi |

---

## Bölüm 3: Bakım İş Emirleri

### 3.1 İş Emri Nedir?

Bakım ekibine verilen "şu makinenin şu bakımını yap" görevidir. Arıza talebinden veya bakım planından otomatik oluşabilir ya da doğrudan açılabilir.

---

### 3.2 Yeni Bakım İş Emri Oluşturma

1. **İş Emirleri** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Ekipman | Bakım yapılacak makine |
| Tür | Arıza / Önleyici / Periyodik / Kalib. |
| Açıklama | Yapılacak bakım veya onarım |
| Atanan Teknisyen | İşi yapacak kişi |
| Planlanan Tarih | İş ne zaman yapılacak |
| Tahmini Süre | Kaç saat sürecek |
| Kullanılacak Malzeme | Yedek parça listesi |

3. **Kaydet**

---

### 3.3 İş Emrini Tamamlama

1. Bakım iş emrini açın
2. **Tamamla** butonuna tıklayın
3. Gerçek harcanan süreyi girin
4. Kullanılan parça ve malzemeleri girin
5. Bakım notu ve gözlemleri ekleyin
6. **Kaydet**

> 💡 **İpucu:** Kullanılan malzemeler stok modülünden otomatik düşülür.

---

## Bölüm 4: Bakım Planları

### 4.1 Periyodik Bakım Nedir?

Makine arızalanmadan önce düzenli aralıklarla yapılan koruyucu bakımlardır. Örneğin: "Her 3 ayda bir yağlama yap" veya "500 çalışma saatinde filtre değiştir".

---

### 4.2 Yeni Bakım Planı Oluşturma

1. **Bakım Planları** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Ekipman | Plan atanacak makine |
| Bakım Türü | Önleyici / Yağlama / Kalibrasyon / Genel |
| Tekrar Sıklığı | Günlük / Haftalık / Aylık / Yıllık / Saat Bazlı |
| Sıklık Değeri | Örn: Her 3 ayda bir |
| Yapılacak İşler | Kontrol listesi |
| Sorumlu Kişi | Plan sahibi teknisyen |
| Tahmini Süre | Her seferinde ne kadar sürer |

3. **Kaydet**

---

### 4.3 Bakım Planı Hatırlatmaları

Planlı bakım tarihi geldiğinde sistem:
- İlgili teknisyene bildirim gönderir
- Bakım iş emrini otomatik oluşturur (ayarlıysa)

---

## Bölüm 5: Raporlar

### 5.1 Arıza Raporu
- Dönem içindeki toplam arıza sayısı
- Makine bazında arıza sıklığı
- Ortalama arıza giderme süresi (MTTR)

### 5.2 Bakım Maliyet Raporu
- İşçilik ve malzeme maliyetleri
- Ekipman bazında bakım harcamaları

### 5.3 Bakım Uyum Raporu
- Planlanan bakımların ne kadarı zamanında yapıldı

---

## Bölüm 6: Diğer Modüllerle Bağlantı

| Modül | Bağlantı |
|-------|---------|
| **Stok** | Yedek parça malzemeleri stoktan düşer |
| **Üretim** | Makine arızası → iş emri duraksatılır |
| **Kalite** | Makine sorunu NCR'a bağlanabilir |
| **İK** | Teknisyen çalışma saatleri puantaja gider |
| **Planlama** | Bakımda olan makine kapasiteden düşülür |

---

## Hızlı Başlangıç Listesi

- [ ] Ekipman kartlarını oluşturun
- [ ] Kritik makineler için bakım planları tanımlayın
- [ ] İlk arıza bildirimini girin
- [ ] Bakım iş emri oluşturup tamamlayın
- [ ] Bakım raporlarını inceleyin

---

*Önceki: [Kalite Kontrol ←](06-kalite.md) | Sonraki: [Sevkiyat →](08-sevkiyat.md)*
