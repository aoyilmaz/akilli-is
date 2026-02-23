# Stok Yönetimi — Kullanıcı El Kitabı

> Bu bölüm, **Stok Yönetimi** modülünü hiç kullanmamış kullanıcılar için hazırlanmıştır.
> Teknik bilgiye gerek yoktur; adımları sırasıyla takip etmeniz yeterlidir.

---

## Stok Modülü Ne İşe Yarar?

İşletmenizde sahip olduğunuz her türlü ürün, malzeme, sarf malzeme veya hizmet bir **stok kartı** ile sisteme girilir. Bu modül:

- Deponuzda ne kadar ürün olduğunu gösterir
- Hangi ürün nerede durduğunu takip eder
- Stok giriş ve çıkışlarını kayıt altına alır
- Kritik seviyenin altına düşen ürünleri bildirir
- Satınalma, Satış ve Üretim modüllerine stok bilgisi sağlar

**Bu modül olmadan:** Hangi üründen ne kadar kaldığını bilemezsiniz, sipariş verirken tahmin yürütmek zorunda kalırsınız, üretim beklenmedik anda durabilir.

---

## Arayüze İlk Bakış

Sol menüde **STOK YÖNETİMİ** başlığı altında şu sayfalar bulunur:

| Sayfa | Ne İçin Kullanılır |
|-------|--------------------|
| Stok Kartları | Ürün ve malzeme kimlikleri |
| Kategoriler | Stok kartlarını gruplandırma |
| Birimler | Ölçüm birimleri (Adet, Kg, Lt…) |
| Depolar | Fiziksel depo alanları |
| Lokasyonlar | Depo içi raf/göz sistemi |
| Hareketler | Giriş, çıkış, transfer kayıtları |
| Sayım İşlemleri | Fiziksel sayım ve fark kapatma |
| Taşıma Birimleri (SSCC) | Palet ve koli takibi |
| Depocu Paneli | Depo çalışanları için basit arayüz |
| Raporlar | Stok durumu ve hareket raporları |

Bir sayfaya tıkladığınızda yeni bir sekme olarak açılır. Birden fazla sekme aynı anda açık kalabilir.

**Ortak ekran öğeleri:**
- **Üst kısım:** Başlık, arama kutusu, "Yeni Ekle" ve diğer butonlar
- **Orta kısım:** Kayıt listesi (tablo)
- **Alt kısım:** Toplam kayıt sayısı ve özet istatistik kartları
- **Satır üzerinde:** Her satırın sağ tarafında Düzenle (kalem) ve Sil (çöp kutusu) simgeleri

---

## Bölüm 1: Stok Kartları

### Stok Kartı Nedir?

Deponuzda takip ettiğiniz her ürün, malzeme veya hizmetin sisteme tanıtım kartıdır. Bir stok kartı olmadan o ürünü sisteme giremez, hareket yaptıramazsınız.

---

### 1.1 Stok Kartları Listesi

1. Sol menüden **Stok Kartları** tıklayın
2. Tüm kayıtlı ürünler tabloda listelenir
3. Tablodaki sütunlar: **Kod**, **Ad**, **Tür**, **Birim**, **Kategori**, **Durum**
4. Alt kısımdaki kartlarda toplam, aktif, kritik stok ve sıfır stoklu ürün sayıları görünür

**Arama:** Üst kısımdaki arama kutusuna ürün kodu, adı veya barkodu yazın — liste anında filtrelenir.

**Filtreleme:** Tablonun üzerindeki filtre seçenekleriyle türe, kategoriye veya duruma göre daraltabilirsiniz.

**Sıralama:** Herhangi bir sütun başlığına tıklayarak tabloya göre sıralayabilirsiniz.

---

### 1.2 Yeni Stok Kartı Oluşturma

1. **Yeni Ekle** butonuna tıklayın
2. Açılan formda aşağıdaki sekmeleri doldurun:

**Temel Bilgiler sekmesi:**

| Alan | Açıklama | Zorunlu mu? |
|------|---------|------------|
| Stok Kodu | Benzersiz kimlik kodu (örn: HM-001) | Evet |
| Stok Adı | Ürünün tam adı | Evet |
| Tür | Hammadde, Mamul, Yarı Mamul… (bkz. tablo aşağıda) | Evet |
| Kategori | Ürünün ait olduğu grup | Hayır |
| Birim | Ölçüm birimi (Adet, Kg, Lt…) | Evet |
| Kısa Açıklama | İsteğe bağlı açıklama | Hayır |
| Barkod | EAN-13 veya benzeri barkod | Hayır |

**Fiyatlar sekmesi:**

| Alan | Açıklama |
|------|---------|
| Alış Fiyatı | Son alış fiyatınız |
| Satış Fiyatı | Müşteriye önerilen fiyat |
| KDV Oranı | %0, %10, %20 |
| Para Birimi | TL, USD, EUR |

**Stok Ayarları sekmesi:**

| Alan | Açıklama |
|------|---------|
| Minimum Stok | Bu miktarın altına düşünce uyarı verilir |
| Maksimum Stok | Depo kapasitesi üst sınırı |
| Yeniden Sipariş Noktası | Sipariş tetikleme seviyesi |
| Tedarik Süresi (Gün) | Siparişten teslimata kadar geçen süre |

**Takip Ayarları sekmesi:**

| Seçenek | Ne Zaman Açılır |
|---------|----------------|
| Parti (Lot) Takibi | Üretim tarihi/parti bazında izleme gerekiyorsa |
| Seri No Takibi | Her birimin kendi seri nosu varsa (elektronik, makine vb.) |
| Son Kullanma Tarihi | Gıda, ilaç, kimyasal gibi ürünler için |

3. Tüm alanları doldurunca **Kaydet** butonuna tıklayın

> 💡 **İpucu:** Stok kodlarını tutarlı bir sistemle oluşturun. Örnek:
> - **HM-** ile başlayanlar → Hammadde
> - **MM-** ile başlayanlar → Mamul
> - **SF-** ile başlayanlar → Sarf
>
> Bu sayede kod bakarak türü anlayabilirsiniz.

> ⚠️ **Dikkat:** Stok kodu bir kez kaydedildiğinde değiştirilemez. Doğru girdiğinizden emin olun.

---

### 1.3 Stok Kartı Türleri

| Tür | Açıklama | Örnek |
|-----|---------|-------|
| **Hammadde** | Üretimde kullanılan ham malzeme | Çelik sac, un, pamuk ipliği |
| **Mamul** | Kendi ürettiğiniz bitmiş ürün | Montajlı makine, kek, dikiş |
| **Yarı Mamul** | Üretim sürecindeki ara ürün | İşlenmiş ama paketlenmemiş |
| **Ambalaj** | Paketleme malzemeleri | Kutu, poşet, etiket |
| **Sarf** | Tüketime giren yardımcı malzeme | Boya, yağ, temizlik malz. |
| **Ticari** | Alıp sattığınız ürün (üretim yok) | Yeniden satılan mallar |
| **Hizmet** | Fiziksel olmayan hizmet kalemi | Nakliye, danışmanlık, montaj |

---

### 1.4 Stok Kartı Düzenleme

1. Listeden ilgili satırı bulun
2. Satırın sağındaki **Düzenle** (kalem) simgesine tıklayın
3. Değişiklikleri yapın → **Kaydet**

---

### 1.5 Stok Kartı Pasif Yapma

Sil simgesine tıkladığınızda kart **silinmez**, **pasif** hale gelir.

- Pasif kartlar listede görünmez (filtreden "Pasif" seçerek görüntülenebilir)
- Pasif karta yeni hareket yapılamaz
- Geçmişteki tüm hareketler ve belgeler korunur

> ⚠️ **Dikkat:** Pasif yapmak geri alınabilir; kartı tekrar "Aktif" duruma getirebilirsiniz.

---

### 1.6 Barkod Ekleme

Bir stok kartına birden fazla barkod tanımlanabilir (örneğin hem kendi barkodunuz hem tedarikçinin barkodu).

1. Stok kartını **Düzenle** ile açın
2. **Barkodlar** sekmesine geçin
3. **Barkod Ekle** → barkod değeri ve türünü girin (EAN-13, QR, Code-128…)
4. **Kaydet**

---

### Sık Sorulan Sorular

**Stok kartını sildim, ne oldu?**
Kart silinmedi, pasif yapıldı. Filtrede "Pasif" seçerek görebilir, "Aktif" yapabilirsiniz.

**Aynı ürünü hem satıp hem üretiyorum; hangi türü seçeyim?**
Kendi ürettiğiniz ürünse **Mamul** seçin.

**Birim seçmeyi unuttuysam, sonradan değiştirebilir miyim?**
Ürüne henüz hareket yapılmamışsa evet. Hareket yapıldıktan sonra birim değiştirilemez.

**Stok kartını oluştururken fiyat girmek zorunda mıyım?**
Hayır, fiyat alanları isteğe bağlıdır. Sonradan eklenebilir.

---

## Bölüm 2: Kategoriler

### Kategori Ne İşe Yarar?

Stok kartlarını gruplandırmak için kullanılır. Raporları kategoriye göre filtreleyebilir, menülerde düzenli görünüm sağlayabilirsiniz.

---

### 2.1 Kategori Ağacı

Kategoriler hiyerarşik yapıdadır; ana kategorinin altına alt kategoriler eklenebilir.

**Örnek:**
```
Hammaddeler
  └── Metal
        ├── Çelik
        └── Alüminyum
  └── Plastik
Ambalaj Malzemeleri
  └── Kutu
  └── Poşet
```

---

### 2.2 Yeni Kategori Oluşturma

1. **Kategoriler** sayfasına gidin → **Yeni Ekle**
2. **Kod** ve **Ad** girin (örn: Kod: METAL, Ad: Metal Malzemeler)
3. **Üst Kategori** seçin — boş bırakırsanız kök (ana) kategori olur
4. **Kaydet**

> 💡 **İpucu:** Kategori yapısını raporlarda nasıl görmek istediğinize göre tasarlayın. 5 seviyeden derin hiyerarşi yönetimi zorlaştırır.

---

### Sık Sorulan Sorular

**Kategori silersem stok kartları ne olur?**
Stok kartları silinmez; kategorisiz kalır. Silmeden önce kartları başka bir kategoriye taşımanız önerilir.

---

## Bölüm 3: Birimler

### Birim Ne İşe Yarar?

Ürünlerin nasıl ölçüldüğünü tanımlar. Sistem varsayılan olarak yaygın birimleri (ADET, KG, LT, M, M2…) hazır getirir.

---

### 3.1 Yeni Birim Oluşturma

1. **Birimler** → **Yeni Ekle**
2. **Kod** (örn: KOLİ), **Ad** (örn: Koli) ve isteğe bağlı **Kısa Ad** girin
3. **Kaydet**

---

### 3.2 Birim Dönüşümleri

Aynı ürünü farklı birimlerle alıp satabilirsiniz. Örneğin: tedarikçiden **Koli** olarak alıp müşteriye **Adet** olarak satmak.

1. Stok kartını **Düzenle** ile açın
2. **Birim Dönüşümleri** sekmesine geçin
3. **Ekle** → Kaynak birim, hedef birim ve çarpan girin
   - Örn: 1 Koli = 12 Adet → Kaynak: KOLİ, Hedef: ADET, Çarpan: 12
4. **Kaydet**

> ⚠️ **Dikkat:** Bir stok kartına atanan ana birim, o karta hareket yapıldıktan sonra değiştirilemez.

---

## Bölüm 4: Depolar

### Depo Ne İşe Yarar?

Fiziksel olarak farklı konumlardaki depo ve üretim alanlarını sisteme tanıtmak için kullanılır. Her stok hareketi mutlaka bir depoya bağlıdır.

---

### 4.1 Yeni Depo Oluşturma

1. **Depolar** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Kod | Kısa benzersiz kod (örn: D-01) |
| Ad | Deponun tam adı (örn: Ana Depo) |
| Adres | Fiziksel adres (isteğe bağlı) |
| Sorumlu Kişi | Depo yöneticisi |
| **Varsayılan Depo** | İşaretlenirse yeni hareketlerde otomatik seçilir |
| **Üretim Deposu** | İşaretlenirse üretim iş emirleri bu depodan malzeme çeker |
| **Negatif Stoka İzin Ver** | Stok yokken çıkış yapılmasına izin verir |

3. **Kaydet**

> ⚠️ **Dikkat:** "Negatif Stoka İzin Ver" seçeneğini yalnızca zorunlu durumlarda açın. Yanlış stok bakiyelerine yol açabilir.

---

### Sık Sorulan Sorular

**Birden fazla depo tanımlayabilir miyim?**
Evet, sınırsız sayıda depo tanımlanabilir.

**Bir stok kartı hangi depoda ne kadar var, nasıl görürüm?**
Stok kartını açın; **Stok Durumu** sekmesinde depo bazında miktarlar listelenir.

---

## Bölüm 5: Lokasyonlar (Raf / Göz Sistemi)

### Lokasyon Ne İşe Yarar?

Bir depodaki koridorları, rafları, katları ve gözleri sisteme tanımlamak için kullanılır. "Hangi ürün tam olarak nerede?" sorusunu yanıtlar.

> 💡 **İpucu:** Lokasyon bazlı takip kullanmıyorsanız, depoya tek bir "Genel" lokasyon tanımlayabilirsiniz.

---

### 5.1 Lokasyon Yapısı

Bir lokasyon dört bileşenden oluşur:

```
Koridor → Raf → Kat → Göz
  A     →  3  →  2  →  B
```

Sistem bu bilgilerden otomatik lokasyon kodu üretir: **A-3-2-B**

---

### 5.2 Lokasyon Türleri

| Tür | Açıklama |
|-----|---------|
| **Normal** | Standart depolama alanı |
| **Karantina** | Kalite onayı bekleyen ürünler için |
| **Hurda** | Bozuk veya imha edilecek ürünler için |
| **Transit** | Geçici depolama (sevkiyat bekliyorsa) |

---

### 5.3 Yeni Lokasyon Oluşturma

1. **Depolar** listesinden ilgili depoyu açın
2. **Lokasyonlar** sekmesine geçin → **Yeni Ekle**
3. Koridor, Raf, Kat, Göz bilgilerini girin
4. **Tür** seçin → **Kaydet**

---

## Bölüm 6: Stok Hareketleri

### Hareket Ne İşe Yarar?

Depoya giren, çıkan veya aktarılan her stoğun kaydını tutar.

> 💡 **Önemli Not:** Çoğu stok hareketi **otomatik oluşur**:
> - Mal kabul yapıldığında → otomatik **Giriş** hareketi
> - Satış irsaliyesi kesildiğinde → otomatik **Çıkış** hareketi
> - Üretimde malzeme sarf edildiğinde → otomatik **Çıkış** hareketi
>
> Bu sayfadan genellikle **manuel düzeltme** veya **düzeltici giriş/çıkış** yapılır.

---

### 6.1 Hareket Türleri

| Hareket Türü | Açıklama | Tipik Kullanım |
|-------------|---------|---------------|
| **Giriş** | Depoya stok ekler | Düzeltme girişleri |
| **Çıkış** | Depodan stok düşer | Kayıp, fire, düzeltme |
| **Transfer** | Depo → Depo aktarım | Şubeler arası transfer |
| **Sayım Fazlası** | Sayımda fazla çıkan miktar | Sayım onayında otomatik |
| **Sayım Eksiği** | Sayımda eksik çıkan miktar | Sayım onayında otomatik |
| **Fire** | Bozulan veya imha edilen ürün | Hasar, son kullanım geçmesi |

---

### 6.2 Manuel Stok Girişi (Adım Adım)

1. **Hareketler** → **Yeni Ekle**
2. **Hareket Türü:** Giriş seçin
3. **Stok Kartı** seçin
4. **Depo** ve **Lokasyon** seçin
5. **Miktar** ve **Birim Maliyet** girin
6. Parti takibi açıksa **Parti Numarası (Lot No)** girin
7. **Referans No** (varsa, satın alma sipariş numarası gibi) girin
8. **Kaydet**

---

### 6.3 Depo Transferi (Adım Adım)

1. **Hareketler** → **Yeni Ekle**
2. **Hareket Türü:** Transfer seçin
3. **Kaynak Depo** ve **Hedef Depo** seçin
4. **Stok Kartı** ve **Miktar** girin
5. **Kaydet**

---

### 6.4 Geçmiş Hareketleri Görüntüleme

- Tüm hareketler tarih, tür, stok kartı ve miktar bilgisiyle listelenir
- Filtreler: **Tarih aralığı**, **Hareket türü**, **Depo**, **Stok kartı**

> ⚠️ **Dikkat:** Kaydedilen bir hareket **silinemez ve düzenlenemez**. Yanlış giriş yaptıysanız ters yönde bir düzeltme hareketi oluşturun.

---

### Sık Sorulan Sorular

**Mal kabulden gelen giriş hareketi nerede görünür?**
Hareketler listesinde görünür. Filtreden hareket türü olarak "Satın Alma Girişi" seçin.

**Yanlış miktarda giriş yaptım, ne yapmalıyım?**
Aynı miktarı **Çıkış** hareketi olarak girin. Ardından doğru miktarı yeniden **Giriş** hareketi olarak girin.

**Stok miktarı neden negatif gösteriyor?**
İlgili depoda "Negatif Stoka İzin Ver" seçeneği açık olduğundan çıkış yapılabilmiş. Düzeltme girişi yaparak bakiyeyi sıfırlayın.

---

## Bölüm 7: Sayım İşlemleri

### Sayım Nedir?

Depodaki fiziksel ürün miktarıyla sistemdeki kayıtlı miktarın karşılaştırılması işlemidir. Fark varsa sistem otomatik düzeltme hareketi oluşturur.

---

### 7.1 Sayım Süreci

```
Sayım Oluştur
     ↓
Sayım Formu Yazdır (isteğe bağlı)
     ↓
Fiziksel Sayımı Yap
     ↓
Sonuçları Sisteme Gir
     ↓
Farkları İncele
     ↓
Onayla → Stok Bakiyeleri Güncellenir
```

---

### 7.2 Yeni Sayım Başlatma

1. **Sayım İşlemleri** → **Yeni Sayım**
2. **Depo** seçin
3. **Kapsam** belirleyin:
   - Tam Sayım (tüm depo)
   - Kategori Bazlı (seçili kategoriler)
   - Lokasyon Bazlı (seçili raflar)
4. **Sayım Tarihi** girin → **Oluştur**

---

### 7.3 Sayım Sonuçlarını Girme

1. Oluşturulan sayımı açın
2. Her stok kartı için fiziksel saydığınız miktarı **Sayılan Miktar** sütununa girin
3. **Fark** sütunu otomatik hesaplanır (Sistem Miktarı − Sayılan Miktar)

---

### 7.4 Sayımı Onaylama

1. Tüm sayım sonuçlarını girdikten sonra **Onayla** butonuna tıklayın
2. Sistem fark miktarlarını otomatik hareket olarak yazar:
   - Fazla çıkan ürünler → **Sayım Fazlası** hareketi
   - Eksik çıkan ürünler → **Sayım Eksiği** hareketi
3. Stok bakiyeleri güncellenir

> ⚠️ **Dikkat:** Sayım onaylandıktan sonra **geri alınamaz**. Onaylamadan önce tüm sonuçları kontrol edin.

> 💡 **İpucu:** Büyük depolarda sayımı birden fazla ekibe bölebilirsiniz. Her ekip kendi lokasyonlarını sayar, sistem tek sayımda birleştirir.

---

### Sık Sorulan Sorular

**Sayım sırasında stok hareketi yapılabilir mi?**
Teknik olarak yapılabilir, ancak sayım doğruluğu bozulur. Sayım süresince hareket yapılmaması önerilir.

**Önceki sayımları görebilir miyim?**
Evet, Sayım İşlemleri listesinde geçmiş sayımlar tarih ve durum bilgisiyle listelenir.

---

## Bölüm 8: Taşıma Birimleri (SSCC / Palet)

### SSCC Nedir?

SSCC (Seri Sevkiyat Konteyner Kodu), her palet veya koliye verilen 18 haneli benzersiz bir GS1 kodudur. Tedarik zincirinde paletleri uçtan uca izlemek için kullanılır.

> 💡 **İpucu:** Uluslararası tedarik zinciriyle çalışmıyorsanız bu bölümü şimdilik atlayabilirsiniz.

---

### 8.1 Yeni Taşıma Birimi Oluşturma

1. **Taşıma Birimleri (SSCC)** → **Yeni Ekle**
2. **Tür** seçin: Palet / Koli / Konteyner
3. **Depo** ve **Lokasyon** seçin
4. Sistem otomatik SSCC kodu üretir
5. **Kaydet**

---

### 8.2 Taşıma Birimine Ürün Ekleme

1. İlgili SSCC kaydını açın
2. **Ürün Ekle** → Stok kartı, miktar, lot numarası girin
3. **Kaydet**

---

### 8.3 Etiket Yazdırma

1. Listede ilgili SSCC satırını seçin
2. **Etiket Yazdır** butonuna tıklayın
3. SSCC barkodlu palet etiketi yazdırılır

---

## Bölüm 9: Depocu Paneli

### Depocu Paneli Ne İşe Yarar?

Depo çalışanlarının, dokunmatik ekran veya el terminaliyle hızlıca iş yapabilmesi için tasarlanmış basitleştirilmiş bir arayüzdür.

**Özellikleri:**
- Büyük ve kolay tıklanabilir butonlar
- Barkod okuyucu ile ürün arama
- Stok giriş/çıkış onaylama
- Parti no ve seri no girişi
- SSCC palet yönetimi

> 💡 **İpucu:** Ofis bilgisayarındaki tam arayüz yerine depo çalışanlarına bu paneli kullandırmanız önerilir; hata yapma ihtimali daha düşüktür.

---

## Bölüm 10: Raporlar

### 10.1 Mevcut Stok Raporu

Tüm stok kartlarının anlık depo miktarlarını gösterir.

- **Filtreler:** Depo, kategori, tür, minimum stok altında olanlar
- **Dışa Aktarma:** Excel veya PDF olarak indirilebilir

---

### 10.2 Stok Hareket Raporu

Seçilen tarih aralığındaki tüm hareketleri listeler.

- **Filtreler:** Tarih aralığı, hareket türü, depo, stok kartı

---

### 10.3 Kritik Stok Raporu

Minimum stok seviyesinin altına düşen ürünleri listeler. Bu raporu düzenli kontrol ederek satın alma taleplerini zamanında oluşturabilirsiniz.

---

### 10.4 Stok Yaşlandırma Raporu

Hangi ürünlerin uzun süredir hareketsiz kaldığını ve son kullanma tarihi yaklaşanları gösterir. Bu rapor **Raporlar** modülü altındadır.

---

## Bölüm 11: Diğer Modüllerle Bağlantı

Stok modülü diğer modüllerle doğrudan entegre çalışır:

| Modül | Bağlantı Şekli |
|-------|---------------|
| **Satınalma** | Mal kabul yapıldığında otomatik stok girişi oluşur |
| **Satış** | İrsaliye kesildiğinde otomatik stok çıkışı oluşur |
| **Üretim** | Malzeme sarf → otomatik çıkış; ürün tamamlama → otomatik giriş |
| **Kalite Kontrol** | Mal kabulden sonra ürün karantinaya alınabilir |
| **Planlama (MRP)** | Minimum stok seviyeleri kullanılarak satın alma önerisi üretilir |
| **Sevkiyat** | Sevkiyat oluşturulduğunda stok rezervasyonu yapılır |

---

## Hızlı Başlangıç Listesi

Stok modülünü ilk kez kuracaksanız şu sırayla ilerleyin:

- [ ] **1. Birimler** oluşturun (KG, ADET, LT… — genellikle hazır gelir)
- [ ] **2. Kategoriler** oluşturun (Hammadde, Mamul, Sarf…)
- [ ] **3. Depolar** oluşturun
- [ ] **4. Lokasyonlar** ekleyin (isteğe bağlı)
- [ ] **5. Stok Kartları** oluşturun
- [ ] **6. Açılış Sayımı** yapın (mevcut stoğu sisteme girin)

Açılış sayımı için şu yolu izleyin: Sayım İşlemleri → Yeni Sayım → Tüm depoyu seç → Mevcut miktarları gir → Onayla

---

*Sonraki bölüm: [Satınalma Modülü →](02-satin-alma.md)*
