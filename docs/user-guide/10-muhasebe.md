# Muhasebe — Kullanıcı El Kitabı

> Bu bölüm, muhasebe kayıtlarını, hesap planını, yevmiye fişlerini ve mali raporları anlatır.

---

## Muhasebe Modülü Ne İşe Yarar?

İşletmenizin tüm mali işlemlerinin muhasebe kayıtlarını tutar. Fatura, tahsilat ve ödeme gibi işlemler diğer modüllerden otomatik olarak muhasebeye aktarılır. Muhasebeci bu aktarımları kontrol eder, ek fişler ekler ve mali tablolar üretir.

---

## Arayüze İlk Bakış

Sol menüde **MUHASEBE** altındaki sayfalar:

| Sayfa | Ne İçin |
|-------|---------|
| Hesap Planı | Muhasebe hesap numaraları ve adları |
| Yevmiye Fişleri | Borç/alacak kayıtları |
| Muhasebe Raporları | Mizan, bilanço, gelir tablosu |
| Sabit Kıymetler | Makine, araç, bina gibi uzun ömürlü varlıklar |
| Bütçe Yönetimi | Gelir/gider bütçe planları |

---

## Bölüm 1: Hesap Planı

### 1.1 Hesap Planı Nedir?

Türkiye'de Tekdüzen Muhasebe Sistemi (TDMS) çerçevesinde düzenlenmiş muhasebe hesap numaraları listesidir. Her hesabın bir kodu ve adı vardır (örn: 100 — Kasa, 120 — Alıcılar).

> 💡 **İpucu:** Hesap planı genellikle sistem kurulumunda muhasebeci tarafından bir kez ayarlanır. Günlük kullanımda doğrudan hesap planını değiştirmeniz gerekmez.

---

### 1.2 Hesap Planı Görüntüleme

1. **Hesap Planı** sayfasına gidin
2. Hesaplar hiyerarşik yapıda listelenir:
   - Ana Gruplar (1. Dönen Varlıklar, 2. Duran Varlıklar…)
   - Alt Hesaplar
   - Yardımcı Hesaplar

---

### 1.3 Yeni Hesap Ekleme

1. **Yeni Ekle**
2. Hesap kodu ve adı girin
3. Hesap türü seçin: Bilanço / Gelir-Gider
4. Üst hesabı seçin (hiyerarşiye göre)
5. **Kaydet**

---

## Bölüm 2: Yevmiye Fişleri

### 2.1 Yevmiye Fişi Nedir?

Her muhasebe işleminin borç ve alacak taraflarını gösteren belgedir. "Bu işlemde hangi hesap borçlandı, hangi hesap alacaklandı?" sorusunu yanıtlar.

**Örnekler:**
- Satış faturası → Alıcılar borç / Satış geliri alacak
- Tahsilat → Kasa/Banka borç / Alıcılar alacak
- Ödeme → Satıcılar borç / Kasa/Banka alacak

---

### 2.2 Otomatik Oluşan Fişler

Aşağıdaki işlemler sisteme girildiğinde yevmiye fişi **otomatik oluşur**:

| İşlem | Oluşan Fiş |
|-------|-----------|
| Satış faturası onayı | Satış muhasebe kaydı |
| Satın alma faturası onayı | Satın alma muhasebe kaydı |
| Tahsilat girişi | Nakit giriş kaydı |
| Ödeme girişi | Nakit çıkış kaydı |

---

### 2.3 Manuel Fiş Oluşturma

Otomatik oluşmayan işlemler (gider, amortisman, düzeltme vb.) için:

1. **Yevmiye Fişleri** → **Yeni Ekle**
2. Fiş türünü seçin (Mahsup / Nakit / Banka / Açılış)
3. Tarih ve açıklama girin
4. **Satır Ekle**:
   - Hesap seçin
   - Borç veya Alacak tutarını girin
5. Borç toplamı = Alacak toplamı olmalı (fiş dengelenmelidir)
6. **Kaydet**

> ⚠️ **Dikkat:** Borç ve alacak toplamları eşit olmadan fiş kaydedilemez.

---

### 2.4 Fiş Onaylama

Muhasebeci fişi kontrol ettikten sonra **Onayla** butonuna tıklar. Onaylanan fiş:
- Büyük deftere geçer
- Değiştirilemez hale gelir

---

## Bölüm 3: Muhasebe Raporları

### 3.1 Mizan

Tüm hesapların açılış, dönem borç/alacak ve kapanış bakiyelerini gösteren tablodur. Dönem sonu dengesini kontrol etmek için kullanılır.

1. **Muhasebe Raporları** → **Mizan**
2. Dönem seçin → **Oluştur**

---

### 3.2 Bilanço

İşletmenin varlıklarını ve borçlarını gösteren mali tablodur.

1. **Muhasebe Raporları** → **Bilanço**
2. Tarih seçin → **Oluştur**

---

### 3.3 Gelir Tablosu (Kâr-Zarar)

Dönem içindeki gelir ve giderleri karşılaştırarak net kâr veya zararı gösterir.

1. **Muhasebe Raporları** → **Gelir Tablosu**
2. Dönem seçin → **Oluştur**

---

## Bölüm 4: Sabit Kıymetler

### 4.1 Sabit Kıymet Nedir?

Makine, araç, bilgisayar, bina gibi uzun süreli kullanılan ve zamanla değeri azalan varlıklardır.

---

### 4.2 Yeni Sabit Kıymet Kaydı

1. **Sabit Kıymetler** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Ad | Varlığın adı (örn: Baskı Makinesi) |
| Kategori | Makine / Araç / Bilgisayar / Bina / Diğer |
| Alış Tarihi | Satın alma tarihi |
| Alış Fiyatı | Toplam maliyet |
| Ekonomik Ömür (Yıl) | Kaç yıl kullanılacak |
| Amortisman Yöntemi | Normal / Hızlandırılmış |

3. **Kaydet**

---

### 4.3 Amortisman

Sistem her dönem sonunda sabit kıymetlerin amortismanını otomatik hesaplar ve yevmiye fişi önerisi oluşturur.

1. **Sabit Kıymetler** → **Amortisman Hesapla**
2. Dönem seçin → **Hesapla**
3. Sonuçları kontrol edin → **Fişe Aktar**

---

## Bölüm 5: Bütçe Yönetimi

### 5.1 Bütçe Nedir?

Gelecek dönem için öngörülen gelir ve gider hedeflerinin planlanmasıdır.

---

### 5.2 Yeni Bütçe Oluşturma

1. **Bütçe Yönetimi** → **Yeni Ekle**
2. Bütçe dönemi ve adı girin
3. **Bütçe Kalemleri Ekle**:
   - Hesap seçin (gelir/gider hesabı)
   - Aylık bütçe tutarlarını girin
4. **Kaydet**

---

### 5.3 Bütçe Gerçekleşme Raporu

**Bütçe Yönetimi** → **Gerçekleşme** sayfasında bütçelenen ile gerçekleşen rakamlar yan yana gösterilir. Sapma tutarı ve yüzdesi otomatik hesaplanır.

---

## Bölüm 6: Diğer Modüllerle Bağlantı

| Modül | Bağlantı |
|-------|---------|
| **Satış** | Fatura → otomatik muhasebe kaydı |
| **Satınalma** | Fatura → otomatik muhasebe kaydı |
| **Finans** | Tahsilat/ödeme → otomatik muhasebe kaydı |
| **Bakım** | Bakım maliyeti → gider kaydı |
| **Üretim** | Üretim maliyetleri → maliyet muhasebesi |

---

## Hızlı Başlangıç Listesi

- [ ] Hesap planını kontrol edin (sistem yöneticisi ile birlikte)
- [ ] Açılış fişini oluşturun (başlangıç bakiyeleri)
- [ ] İlk otomatik fişleri inceleyin ve onaylayın
- [ ] Aylık mizan raporunu alın
- [ ] Dönem sonu bilanço ve gelir tablosu üretin

---

*Önceki: [Finans ←](09-finans.md) | Sonraki: [İnsan Kaynakları →](11-ik.md)*
