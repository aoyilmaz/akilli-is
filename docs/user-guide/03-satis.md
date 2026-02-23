# Satış Yönetimi — Kullanıcı El Kitabı

> Bu bölüm, müşteriye teklif vermekten fatura kesmek ve iade almaya kadar tüm satış sürecini anlatır.

---

## Satış Modülü Ne İşe Yarar?

Müşterilere ürün ve hizmet satma sürecinin tamamı bu modülden yönetilir. Bir teklifin nasıl siparişe, siparişin irsaliyeye, irsaliyenin faturaya dönüştüğünü adım adım takip edebilirsiniz.

**Temel akış:**

```
Müşteri Kaydı
      ↓
Teklif
      ↓
Satış Siparişi
      ↓
İrsaliye (Mal Çıkışı)
      ↓
Fatura
      ↓
Tahsilat (Finans Modülü)
```

---

## Arayüze İlk Bakış

Sol menüde **SATIŞ YÖNETİMİ** altındaki sayfalar:

| Sayfa | Ne İçin |
|-------|---------|
| Müşteriler | Müşteri firma ve kişi kartları |
| Teklifler | Müşteriye gönderilen fiyat teklifleri |
| Siparişler | Onaylanan satış siparişleri |
| İadeler | Müşterinin geri gönderdiği ürünler |
| Sözleşmeler | Çerçeve satış sözleşmeleri |
| İrsaliyeler | Mal çıkış belgeleri |
| Faturalar | Müşteriye kesilen faturalar |
| Fiyat Listeleri | Müşteri/dönem bazlı fiyat tanımları |

---

## Bölüm 1: Müşteriler

### 1.1 Yeni Müşteri Oluşturma

1. **Müşteriler** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama | Zorunlu |
|------|---------|---------|
| Müşteri Adı | Firma veya kişi adı | Evet |
| Müşteri Tipi | Kurumsal / Bireysel | Evet |
| Vergi No | Kurumsal müşteriler için | Koşullu |
| Vergi Dairesi | Kurumsal müşteriler için | Koşullu |
| Telefon | İletişim numarası | Hayır |
| E-posta | Fatura/yazışma e-postası | Hayır |
| Fatura Adresi | Resmi fatura adresi | Hayır |
| Teslimat Adresi | Ürünün gönderileceği adres | Hayır |
| Ödeme Vadesi | Varsayılan vade (gün) | Hayır |
| Para Birimi | Varsayılan para birimi | Hayır |
| Satış Temsilcisi | Sorumlu personel | Hayır |
| Kredi Limiti | Maksimum açık bakiye tutarı | Hayır |

3. **Kaydet**

---

### 1.2 Müşteri Kartında Neler Görülür?

Bir müşteriyi açtığınızda şu sekmeleri görürsünüz:

| Sekme | İçerik |
|-------|--------|
| Genel Bilgiler | Adres, iletişim, ticari bilgiler |
| Hareketler | Tüm satış belgeleri (tekliften faturaya) |
| Bakiye | Açık bakiye ve vadeleri |
| İstatistikler | Toplam satış, en çok alınan ürünler |
| Notlar | Özel notlar ve hatırlatmalar |

---

### Sık Sorulan Sorular

**Müşteriyi sildim, ne olur?**
Pasif hale gelir. Geçmiş belgeleri korunur, yeni işlem yapılamaz.

**Kredi limiti dolduğunda ne olur?**
Sistem uyarı verir; onay verme yetkisi olan kullanıcı geçebilir.

---

## Bölüm 2: Fiyat Listeleri

### 2.1 Fiyat Listesi Nedir?

Belirli müşterilere veya belirli dönemlere özel indirimli ya da farklı fiyat uygulamak için kullanılır.

### 2.2 Yeni Fiyat Listesi Oluşturma

1. **Fiyat Listeleri** → **Yeni Ekle**
2. Ad ve para birimi girin
3. **Geçerlilik tarihi** belirleyin
4. **Kalem Ekle** → Stok kartı ve fiyat girin
5. **Kaydet**

Fiyat listesi bir müşteriye atandığında, o müşteri için teklif ve sipariş oluştururken fiyatlar otomatik gelir.

---

## Bölüm 3: Teklifler

### Teklif Nedir?

Müşteriye "şu ürünleri şu fiyata alabileceğinizi" bildiren belgedir. Teklif onaylanırsa siparişe dönüştürülür.

---

### 3.1 Yeni Teklif Oluşturma

1. **Teklifler** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Müşteri | Teklif verilecek firma |
| Teklif Tarihi | Bugün |
| Geçerlilik Tarihi | Teklifin kaçıncı güne kadar geçerli olduğu |
| Para Birimi | TL, USD, EUR |
| Ödeme Koşulları | Peşin / 30 gün / vb. |

3. **Kalem Ekle**:
   - Stok kartı seçin
   - Miktar, birim fiyat, KDV oranı, iskonto (%) girin
4. Alt toplamlar (Ara Toplam, KDV, Genel Toplam) otomatik hesaplanır
5. **Kaydet**

---

### 3.2 Teklifi Yazdırma / Müşteriye Gönderme

1. Teklifi açın → **Yazdır** veya **E-posta Gönder**
2. Teklif PDF'i müşteriye iletilir

---

### 3.3 Tekliften Sipariş Oluşturma

1. Onaylanan teklifi açın
2. **Siparişe Dönüştür** butonuna tıklayın
3. Kontrol edip **Kaydet**

> 💡 **İpucu:** Müşteri teklifi kısmen kabul ettiyse, kalem miktarlarını azaltarak sipariş oluşturabilirsiniz.

---

### 3.4 Teklif Durumları

| Durum | Anlamı |
|-------|--------|
| **Taslak** | Henüz gönderilmedi |
| **Gönderildi** | Müşteriye iletildi |
| **Revize Edildi** | Güncelleme yapıldı |
| **Onaylandı** | Müşteri kabul etti |
| **Reddedildi** | Müşteri kabul etmedi |
| **Siparişe Dönüştürüldü** | İşlem tamamlandı |
| **Süresi Doldu** | Geçerlilik tarihi geçti |

---

## Bölüm 4: Satış Siparişleri

### 4.1 Yeni Sipariş Oluşturma

Doğrudan sipariş girilebilir veya onaylanan tekliften dönüştürülebilir.

1. **Siparişler** → **Yeni Ekle**
2. Müşteri, tarih, teslimat tarihi ve adresi seçin
3. Kalemler ekleyin
4. **Kaydet**

---

### 4.2 Sipariş Durumları

| Durum | Anlamı |
|-------|--------|
| **Taslak** | Onay bekliyor |
| **Onaylandı** | İrsaliye kesilebilir |
| **Kısmi Sevk** | Bir kısmı gönderildi |
| **Tamamlandı** | Tüm kalemler sevk edildi |
| **İptal** | İptal edildi |

---

### 4.3 Siparişten İrsaliye Oluşturma

1. Siparişi açın
2. **İrsaliye Oluştur** butonuna tıklayın
3. Gönderilecek miktarları kontrol edin
4. Çıkış deposunu seçin
5. **Kaydet** — stok otomatik düşer

---

## Bölüm 5: İrsaliyeler

### İrsaliye Nedir?

Malın müşteriye fiziksel olarak gönderildiğini belgeleyen sevk irsaliyesidir. İrsaliye kaydedildiğinde stok otomatik güncellenir.

---

### 5.1 İrsaliye Oluşturma

Genellikle siparişten oluşturulur (bkz. Bölüm 4.3). Doğrudan da oluşturulabilir:

1. **İrsaliyeler** → **Yeni Ekle**
2. Müşteri ve ilgili siparişi seçin
3. Kalemleri ve miktarları girin
4. Çıkış deposunu seçin
5. **Kaydet**

---

### 5.2 İrsaliyeyi Yazdırma

İrsaliye kaydedildikten sonra **Yazdır** butonuyla imzalı belge üretilir. Sürücüye veya müşteriye verilir.

---

### 5.3 İrsaliyeden Fatura Oluşturma

1. İrsaliyeyi açın → **Fatura Oluştur**
2. Kalemler otomatik gelir
3. Fatura numarası ve tarihini kontrol edin
4. **Kaydet**

---

## Bölüm 6: Faturalar

### 6.1 Fatura Oluşturma

Genellikle irsaliyeden dönüştürülür. Doğrudan da oluşturulabilir:

1. **Faturalar** → **Yeni Ekle**
2. Müşteri, fatura no, tarih ve vade tarihi girin
3. Kalemleri ekleyin
4. **Kaydet**

---

### 6.2 Fatura Onaylama

Faturayı **Onayla** butonuyla onayladığınızda:
- Muhasebe modülünde otomatik yevmiye fişi oluşur
- Müşterinin cari hesabı güncellenir
- e-Fatura için hazır hale gelir

> ⚠️ **Dikkat:** Onaylanan fatura düzenlenemez. Düzeltme için iade/alacak faturası kullanın.

---

### 6.3 Fatura Durumları

| Durum | Anlamı |
|-------|--------|
| **Taslak** | Onaylanmadı |
| **Onaylandı** | Muhasebe kaydı oluşturuldu |
| **Kısmi Tahsil** | Bir kısmı ödendi |
| **Tahsil Edildi** | Tamamen ödendi |
| **İptal** | İptal edildi |

---

## Bölüm 7: İadeler

### 7.1 Müşteri İadesi Oluşturma

1. **İadeler** → **Yeni Ekle**
2. Müşteri ve iade edilecek kalemler ile miktarları girin
3. **İade Nedeni** seçin (kalite sorunu, yanlış ürün, hasar vb.)
4. Ürünün hangi depoya gireceğini seçin
5. **Kaydet** — stok otomatik güncellenir

---

### 7.2 İade Sonrası İşlemler

İade onaylandığında:
- Stok geri girer
- Müşteri için alacak faturası (iade faturası) oluşturulabilir
- Muhasebe otomatik güncellenir

---

## Bölüm 8: Sözleşmeler

### 8.1 Sözleşme Ne İçin?

Belirli bir dönem için müşteriye özel fiyat, miktar taahhüdü veya ticari koşulları belgelemek için kullanılır.

1. **Sözleşmeler** → **Yeni Ekle**
2. Müşteri, başlangıç/bitiş tarihi, ödeme koşulları girin
3. Sözleşme kalemlerini (ürün, fiyat, miktar taahhüdü) ekleyin
4. **Kaydet**

Sözleşme aktifken bu müşteriye sipariş oluştururken sözleşme fiyatları otomatik uygulanır.

---

## Bölüm 9: Diğer Modüllerle Bağlantı

| Modül | Bağlantı |
|-------|---------|
| **Stok** | İrsaliyede otomatik stok çıkışı |
| **Muhasebe** | Fatura onayında otomatik yevmiye |
| **Finans** | Fatura vadesi → tahsilat planı |
| **CRM** | Teklifler CRM'deki fırsatlardan oluşturulabilir |
| **Sevkiyat** | İrsaliye → sevkiyat planı |
| **e-Dönüşüm** | Onaylanan fatura e-Faturaya dönüştürülebilir |

---

## Hızlı Başlangıç Listesi

- [ ] Müşteri kartlarını oluşturun
- [ ] Fiyat listelerini tanımlayın (isteğe bağlı)
- [ ] İlk teklifi oluşturun ve müşteriye gönderin
- [ ] Teklifi siparişe dönüştürün
- [ ] Siparişten irsaliye oluşturun
- [ ] İrsaliyeden fatura kesin ve onaylayın

---

*Önceki: [Satınalma ←](02-satin-alma.md) | Sonraki: [Üretim →](04-uretim.md)*
