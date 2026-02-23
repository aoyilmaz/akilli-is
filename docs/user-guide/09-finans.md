# Finans — Kullanıcı El Kitabı

> Bu bölüm, müşterilerden tahsilat yapma ve tedarikçilere ödeme gerçekleştirme süreçlerini anlatır.

---

## Finans Modülü Ne İşe Yarar?

Para giriş ve çıkışlarını takip eder. Hangi faturanın ödendiğini, hangi müşterinin borcunu ne zaman ödeyeceğini ve kasa/banka bakiyelerini gösterir.

---

## Arayüze İlk Bakış

Sol menüde **FİNANS** altındaki sayfalar:

| Sayfa | Ne İçin |
|-------|---------|
| Tahsilatlar | Müşteriden gelen ödemeler |
| Ödemeler | Tedarikçiye yapılan ödemeler |
| Mutabakat | Banka ekstresi ile sistem kaydının eşleştirilmesi |
| Cari Hesaplar | Müşteri ve tedarikçi bakiyeleri |

---

## Bölüm 1: Cari Hesaplar

### 1.1 Cari Hesap Nedir?

Bir müşteri veya tedarikçiyle olan toplam borç/alacak durumunun özeti.

- **Müşteri cari:** Müşterinin size ne kadar borcu olduğu
- **Tedarikçi cari:** Siz tedarikçiye ne kadar borçlusunuz

---

### 1.2 Cari Hesap Görüntüleme

1. **Cari Hesaplar** sayfasına gidin
2. Müşteri veya tedarikçiyi arayın
3. Tıklayın → ekstresi açılır:
   - Her fatura, ödeme ve tahsilat ayrı satır olarak görünür
   - Bakiye sürekli güncellenir

---

### 1.3 Vadesi Geçen Alacaklar

Cari hesaplar listesinde **Vadesi Geçenler** filtresini açın. Kırmızıyla işaretlenen satırlar vadesi dolmuş alacaklardır.

---

## Bölüm 2: Tahsilatlar

### 2.1 Tahsilat Nedir?

Müşteriden para aldığınızda sisteme girdiğiniz kayıttır. Bir veya birden fazla faturaya karşılık gelebilir.

---

### 2.2 Yeni Tahsilat Girişi (Adım Adım)

1. **Tahsilatlar** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Müşteri | Parayı ödeyen firma |
| Tarih | Ödemenin geldiği tarih |
| Tutar | Alınan para miktarı |
| Para Birimi | TL / USD / EUR |
| Ödeme Yöntemi | Nakit / Havale / EFT / Çek / Kredi Kartı |
| Banka / Kasa | Paranın girdiği hesap |
| Referans No | Havale dekontu no veya çek no |

3. **Faturalara Uygula**:
   - Müşterinin açık faturaları listelenir
   - Hangi faturalara uygulanacağını seçin
   - Kısmi ödeme yapılabilir
4. **Kaydet**

---

### 2.3 Çek / Senet Takibi

Çek veya senet alındığında:
1. Ödeme yöntemi olarak **Çek** seçin
2. Çek bilgilerini girin:
   - Çek No
   - Kesen Banka
   - Vade Tarihi
   - Nominal Tutar
3. **Kaydet** — çek portföyüne eklenir

Vade geldiğinde çekin tahsil edildiğini işaretlemeniz gerekir.

---

### Sık Sorulan Sorular

**Müşteri yanlış tutarda ödeme yaptı; ne yapmalıyım?**
Gelen tutarı tahsilat olarak kaydedin. Fark için müşteriye bilgi verin; eksik kalan tutar faturada açık kalmaya devam eder.

**Avans olarak ödeme aldım; nasıl girerim?**
Tahsilat girişinde **Faturalara Uygulama** yapmadan kaydedin — avans olarak açıkta kalır. Fatura kesildiğinde uygulanır.

---

## Bölüm 3: Ödemeler

### 3.1 Yeni Ödeme Girişi (Adım Adım)

1. **Ödemeler** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Tedarikçi | Ödeme yapılacak firma |
| Tarih | Ödeme tarihi |
| Tutar | Ödenen miktar |
| Ödeme Yöntemi | Nakit / Havale / EFT / Çek |
| Banka / Kasa | Paranın çıktığı hesap |
| Referans No | EFT referans numarası |

3. **Faturalara Uygula** → hangi satın alma faturasına karşılık geldiğini seçin
4. **Kaydet**

---

### 3.2 Ödeme Planı (Vadeli Ödemeler)

Tedarikçiye vadelide ödeyecekseniz:
1. Satın alma faturasını açın → **Ödeme Planı** sekmesi
2. Vadeleri ve tutarları girin
3. Ödeme tarihi geldiğinde bildirim alırsınız

---

## Bölüm 4: Mutabakat

### 4.1 Mutabakat Nedir?

Banka hesap ekstrenizle sistemdeki kayıtların karşılaştırılmasıdır. Sistemde kayıtlı olmayan banka hareketleri tespit edilir.

---

### 4.2 Mutabakat Yapma

1. **Mutabakat** sayfasına gidin
2. Banka hesabını seçin ve dönem belirleyin
3. Banka ekstresini sisteme yükleyin (Excel veya CSV) ya da hareketleri elle girin
4. Sistem otomatik olarak eşleşenleri ve eşleşmeyenleri gösterir
5. Eşleşmeyen hareketler için kayıt oluşturun veya farkın nedenini not düşün

---

## Bölüm 5: Diğer Modüllerle Bağlantı

| Modül | Bağlantı |
|-------|---------|
| **Satış** | Fatura onayı → müşteri cari hesabı açılır |
| **Satınalma** | Fatura onayı → tedarikçi cari hesabı açılır |
| **Muhasebe** | Tahsilat/ödeme → otomatik yevmiye fişi |

---

## Hızlı Başlangıç Listesi

- [ ] Kasa ve banka hesaplarını sistem yöneticinize tanımlatın
- [ ] Müşteri cari bakiyelerini kontrol edin
- [ ] Vadesi yaklaşan faturaları filtreleyin
- [ ] İlk tahsilatı girin
- [ ] İlk ödemeyi girin

---

*Önceki: [Sevkiyat ←](08-sevkiyat.md) | Sonraki: [Muhasebe →](10-muhasebe.md)*
