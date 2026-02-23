# Satınalma — Kullanıcı El Kitabı

> Bu bölüm, tedarikçiden ürün veya hizmet satın alma sürecini baştan sona anlatır.

---

## Satınalma Modülü Ne İşe Yarar?

İşletmenizin dışarıdan temin ettiği her ürün ve hizmet bu modül üzerinden yönetilir. Süreci adım adım takip ederek hangi siparişin verildiğini, neyin teslim alındığını ve hangi faturanın ödendiğini her zaman görebilirsiniz.

**Temel akış:**

```
Satın Alma Talebi
       ↓
Teklif Talebi (RFQ) — isteğe bağlı
       ↓
Satın Alma Siparişi
       ↓
Mal Kabul (Teslim Alma)
       ↓
Satın Alma Faturası
       ↓
Ödeme (Finans Modülü)
```

---

## Arayüze İlk Bakış

Sol menüde **SATINALMA** başlığı altındaki sayfalar:

| Sayfa | Ne İçin |
|-------|---------|
| Tedarikçiler | Tedarikçi firma kartları |
| Talepler | Satın alınması istenen ürünlerin listesi |
| Siparişler | Tedarikçiye verilen siparişler |
| Mal Kabul | Gelen malın teslim alınması |
| Faturalar | Tedarikçiden gelen faturalar |
| Teklif Talepleri (RFQ) | Birden fazla tedarikçiden fiyat isteme |

---

## Bölüm 1: Tedarikçiler

### Tedarikçi Nedir?

Sizden ürün veya hizmet satın alan firma müşteriyken, size satan firma **tedarikçidir**. Tüm satın alma işlemlerinde mutlaka bir tedarikçi seçilir.

---

### 1.1 Yeni Tedarikçi Oluşturma

1. **Tedarikçiler** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama | Zorunlu |
|------|---------|---------|
| Firma Adı | Tedarikçinin tam ticari unvanı | Evet |
| Vergi No | 10 haneli vergi kimlik numarası | Evet |
| Vergi Dairesi | Bağlı olduğu vergi dairesi | Evet |
| Telefon | İletişim numarası | Hayır |
| E-posta | Fatura/yazışma e-postası | Hayır |
| Adres | Fatura adresi | Hayır |
| Ödeme Vadesi | Varsayılan ödeme günü (örn: 30 gün) | Hayır |
| Para Birimi | TL, USD, EUR | Hayır |
| Banka Hesabı | IBAN bilgisi | Hayır |

3. **Kaydet**

---

### 1.2 Tedarikçi Fiyat Listesi

Tedarikçiden belirli ürünleri belirli fiyatlardan aldığınızı sisteme kaydedebilirsiniz. Bu sayede sipariş oluştururken fiyat otomatik gelir.

1. Tedarikçiyi açın → **Fiyat Listesi** sekmesi
2. **Ekle** → Stok kartı, fiyat, para birimi, geçerlilik tarihi girin
3. **Kaydet**

---

### Sık Sorulan Sorular

**Aynı firmadan hem alıyorum hem satıyorum; hem müşteri hem tedarikçi olarak girebilir miyim?**
Evet, ayrı kayıtlar açmanız gerekir: biri Satış modülünde müşteri, biri Satınalma modülünde tedarikçi.

---

## Bölüm 2: Satın Alma Talepleri

### Talep Nedir?

Bir çalışan "şu ürüne ihtiyacımız var" dediğinde bunu sisteme **talep** olarak girer. Talep onaylandıktan sonra satın alma siparişine dönüşür.

---

### 2.1 Yeni Talep Oluşturma

1. **Talepler** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Talep Tarihi | Bugünkü tarih |
| İhtiyaç Tarihi | Ürünün ne zamana kadar gelmesi gerektiği |
| Açıklama | Talep neden yapılıyor? |

3. **Talep Kalemleri** bölümünde **Kalem Ekle**:
   - Stok kartı seçin
   - Miktar ve birimi girin
   - Hedef depoyu seçin
4. **Kaydet**

---

### 2.2 Talep Durumları

| Durum | Anlamı |
|-------|--------|
| **Taslak** | Henüz gönderilmedi |
| **Onay Bekliyor** | Yöneticiye gönderildi |
| **Onaylandı** | Sipariş oluşturulabilir |
| **Reddedildi** | Onaylanmadı |
| **Siparişe Dönüştürüldü** | İşlem tamamlandı |

---

### 2.3 Talepten Sipariş Oluşturma

1. Onaylanan talebi açın
2. **Siparişe Dönüştür** butonuna tıklayın
3. Tedarikçi seçin
4. Sistem otomatik sipariş formu açar — kontrol edip **Kaydet**

---

## Bölüm 3: Satın Alma Siparişleri

### Sipariş Nedir?

Tedarikçiye gönderilen resmi satın alma taahhüdüdür. Onaylanan sipariş tedarikçiye e-posta ile gönderilebilir ya da yazdırılabilir.

---

### 3.1 Yeni Sipariş Oluşturma

1. **Siparişler** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Tedarikçi | Siparişi vereceğiniz firma |
| Sipariş Tarihi | Bugün |
| Teslim Tarihi | Beklenen teslimat tarihi |
| Teslim Yeri | Hangi depoya gelecek |
| Ödeme Koşulları | Peşin / 30 gün / 60 gün |
| Para Birimi | TL, USD, EUR |

3. **Kalem Ekle**:
   - Stok kartı seçin
   - Miktar, birim fiyat, KDV oranı girin
4. **Kaydet**

---

### 3.2 Sipariş Durumları

| Durum | Anlamı |
|-------|--------|
| **Taslak** | Henüz onaylanmadı |
| **Onaylandı** | Tedarikçiye gönderilebilir |
| **Kısmi Teslim** | Bir kısmı geldi |
| **Tamamlandı** | Tüm kalemler teslim alındı |
| **İptal** | Sipariş iptal edildi |

---

### 3.3 Siparişi Yazdırma / Gönderme

1. Siparişi açın
2. **Yazdır** → PDF oluşturur
3. **E-posta Gönder** → Tedarikçinin e-postasına gönderir

---

### Sık Sorulan Sorular

**Siparişi onayladıktan sonra değişiklik yapabilir miyim?**
Onaylanan siparişe kalem eklenebilir veya miktar artırılabilir, ancak mevcut onaylı kalemler değiştirilemez. Değişiklik için iptal edip yeniden oluşturmanız gerekir.

**Birden fazla siparişi birleştirerek tek mal kabul yapabilir miyim?**
Evet, Mal Kabul sayfasında birden fazla siparişten kalem seçebilirsiniz.

---

## Bölüm 4: Mal Kabul

### Mal Kabul Nedir?

Tedarikçiden gelen malı fiziksel olarak teslim aldığınızda sisteme girdiğiniz belgedir. Mal kabul yapıldığında stok otomatik güncellenir.

---

### 4.1 Mal Kabul Oluşturma (Adım Adım)

1. **Mal Kabul** → **Yeni Ekle**
2. **Sipariş** seçin (açılır listeden ilgili satın alma siparişi)
3. Sipariş kalemleri otomatik dolar
4. Her kalem için **Gelen Miktar** girin (siparişten az geldiyse azaltın)
5. Lot takipli ürünler için **Parti Numarası** ve varsa **Son Kullanma Tarihi** girin
6. **Teslim Depo** ve **Lokasyon** seçin
7. **Kaydet**

> 💡 **İpucu:** Mal kabul kaydedildiği anda stok hareketi (Giriş) otomatik oluşur. Ayrıca hareket oluşturmanıza gerek yoktur.

---

### 4.2 Kısmi Teslim

Siparişin tamamı gelmezse yalnızca gelen miktarı girin. Kalan miktar sipariş üzerinde "Bekleyen" olarak kalır. Bir sonraki teslimat için tekrar mal kabul oluşturabilirsiniz.

---

### 4.3 İade

Teslim alınan malda sorun varsa:
1. Mal kabulü açın → **İade Oluştur**
2. İade edilecek kalemleri ve miktarı girin
3. **Kaydet** — stok otomatik düşer

---

### Sık Sorulan Sorular

**Mal kabulü kaydetmeden önce kalite kontrolü gerekiyor; nasıl yapmalıyım?**
Mal kabul kaydedilirken depo olarak "Karantina" deposu seçin. Kalite onayından sonra normal depoya transfer yapın.

**Fatura mal kabulden önce geldi; ne yapmalıyım?**
Sisteme önce mal kabulü girin, ardından faturayı işleyin.

---

## Bölüm 5: Satın Alma Faturaları

### 5.1 Fatura Oluşturma

1. **Faturalar** → **Yeni Ekle**
2. **Tedarikçi** ve ilgili **Mal Kabul** veya **Sipariş** seçin
3. Kalemler otomatik dolar
4. **Fatura No** ve **Fatura Tarihi** girin
5. **Vade Tarihi** girin
6. **Kaydet**

---

### 5.2 Fatura Durumları

| Durum | Anlamı |
|-------|--------|
| **Taslak** | Henüz onaylanmadı |
| **Onaylandı** | Muhasebe kaydı oluşturuldu |
| **Kısmi Ödendi** | Bir kısmı ödendi |
| **Ödendi** | Tamamen ödendi |
| **İptal** | İptal edildi |

> 💡 **İpucu:** Fatura onaylandığında muhasebe modülünde otomatik yevmiye fişi oluşturulur.

---

## Bölüm 6: Teklif Talepleri (RFQ)

### RFQ Nedir?

Birden fazla tedarikçiden aynı ürün için fiyat teklifi istediğinizde kullanılır. Teklifler karşılaştırılarak en uygun tedarikçi seçilir.

---

### 6.1 RFQ Oluşturma

1. **Teklif Talepleri** → **Yeni Ekle**
2. **Ürün kalemlerini** ekleyin (stok kartı, miktar, ihtiyaç tarihi)
3. Teklife davet edecek **Tedarikçileri** seçin
4. **Teklif Son Tarihi** girin
5. **Kaydet** → Tedarikçilere sistem üzerinden veya e-posta ile davet gönderilebilir

---

### 6.2 Teklifleri Karşılaştırma

1. RFQ'yu açın → **Teklifler** sekmesi
2. Her tedarikçinin teklif fiyatları yan yana görüntülenir
3. Uygun tedarikçiyi seçin → **Siparişe Dönüştür**

---

## Bölüm 7: Diğer Modüllerle Bağlantı

| Modül | Bağlantı |
|-------|---------|
| **Stok** | Mal kabulde otomatik stok girişi |
| **Muhasebe** | Fatura onayında otomatik yevmiye |
| **Finans** | Fatura vadesi → ödeme planı |
| **Planlama** | MRP siparişe dönüştürme önerileri |
| **Kalite** | Mal kabulde giriş kalite kontrolü |

---

## Hızlı Başlangıç Listesi

- [ ] Tedarikçi kartlarını oluşturun
- [ ] Tedarikçi fiyat listelerini girin (isteğe bağlı)
- [ ] İlk satın alma talebini oluşturun
- [ ] Talebi onaylayıp siparişe dönüştürün
- [ ] Mal kabulü yapın
- [ ] Faturayı girin ve onaylayın

---

*Önceki: [Stok Yönetimi ←](01-stok.md) | Sonraki: [Satış Yönetimi →](03-satis.md)*
