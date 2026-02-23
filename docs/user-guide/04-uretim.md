# Üretim (İmalat) — Kullanıcı El Kitabı

> Bu bölüm, hammaddeden mamul ürün üretme sürecinin sisteme nasıl yansıtıldığını anlatır.

---

## Üretim Modülü Ne İşe Yarar?

Fabrika veya atölyenizde gerçekleştirdiğiniz her üretim faaliyeti bu modülden takip edilir. Hangi ürünü, ne zaman, hangi kaynaklarla ürettiğinizi kaydeder; malzeme sarf miktarlarını ve üretim sürelerini izler.

**Temel akış:**

```
Satış Siparişi / Planlama
          ↓
    İş Emri Oluşturma
          ↓
    Malzeme Hazırlama
          ↓
  Üretim Başlatma / Operasyon
          ↓
    Üretim Tamamlama
          ↓
  Mamul Stoka Alınma
```

---

## Arayüze İlk Bakış

Sol menüde **ÜRETİM (İMALAT)** altındaki sayfalar:

| Sayfa | Ne İçin |
|-------|---------|
| İş Emirleri | Üretim emirlerinin oluşturulması ve takibi |
| Operatör Paneli | Makine başındaki çalışan arayüzü |
| Canlı OEE İzleme | Makine ve hat verimliliği |

---

## Bölüm 1: Ürün Reçetesi (BOM) — Ön Koşul

Üretim başlatmadan önce üretmek istediğiniz ürünün **Ürün Reçetesi** tanımlı olmalıdır. Ürün reçetesi **Planlama** modülü altında bulunur (bkz. [Planlama El Kitabı](05-planlama.md)).

Ürün reçetesi şunları tanımlar:
- Hangi hammadde veya yarı mamuller kullanılacak
- Her bileşenin miktarı
- Hangi operasyonlar yapılacak
- Her operasyonun süresi

---

## Bölüm 2: İş Emirleri

### İş Emri Nedir?

"Şu ürünü, şu miktarda üret" komutudur. Bir iş emri oluşturduğunuzda sistem:
- Gerekli malzemeleri hesaplar
- Operasyonları sıralar
- Malzeme yeterliliğini kontrol eder

---

### 2.1 Yeni İş Emri Oluşturma

1. **İş Emirleri** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Mamul | Üretilecek ürün (stok kartı — Mamul türü) |
| Miktar | Kaç adet üretilecek |
| Ürün Reçetesi | Kullanılacak reçete (otomatik gelir) |
| Planlanan Başlangıç | Ne zaman başlanacak |
| Planlanan Bitiş | Ne zaman tamamlanacak |
| Öncelik | Düşük / Normal / Yüksek / Acil |
| Hedef Depo | Mamulün konulacağı depo |

3. **Kaydet** — sistem malzeme listesini otomatik doldurur

---

### 2.2 İş Emri Durumları

| Durum | Anlamı |
|-------|--------|
| **Taslak** | Henüz onaylanmadı |
| **Planlandı** | Malzeme ve kapasite ayrıldı |
| **Malzeme Hazır** | Tüm malzemeler ayrıldı |
| **Devam Ediyor** | Üretim başladı |
| **Tamamlandı** | Üretim bitti, mamul stoka alındı |
| **İptal** | İptal edildi |

---

### 2.3 Malzeme Kontrolü

İş emrini açtığınızda **Malzemeler** sekmesinde:
- Gereken malzeme listesi
- Depodaki mevcut miktar
- Eksik olan miktar görünür

> ⚠️ **Dikkat:** Malzeme yetersizse üretim başlatılamaz. Önce satın alma talebi oluşturun.

---

### 2.4 Üretimi Başlatma

1. İş emrini açın
2. Durum **Planlandı** veya **Malzeme Hazır** olmalı
3. **Başlat** butonuna tıklayın
4. Malzemeler otomatik depolardan düşülür (sarf hareketi oluşur)

---

### 2.5 Üretimi Tamamlama

1. Üretim bittiğinde iş emrini açın
2. **Tamamla** butonuna tıklayın
3. **Gerçekleşen Miktar** girin (planlananla farklıysa)
4. Mamulün konulacağı depo ve lokasyonu seçin
5. **Kaydet** — mamul stoka girer

---

### 2.6 Kısmi Tamamlama (Parçalı Üretim)

Tüm miktar bir anda tamamlanmazsa:
1. **Kısmi Tamamla** butonuna tıklayın
2. Tamamlanan miktarı girin
3. Kalan miktar iş emrinde devam eder

---

### 2.7 Fire ve Hurda

Üretim sırasında kullanılamaz hale gelen malzeme veya yarı mamul için:
1. İş emrini açın → **Fire Gir**
2. Fire miktarı ve nedeni girin
3. **Kaydet** — sistem fire miktarını stoktan düşer

---

### Sık Sorulan Sorular

**İş emrini iptal edersem stok ne olur?**
Malzeme düşülmemişse bir şey olmaz. Malzeme düşüldüyse iade hareketi oluşturmanız gerekir.

**Aynı ürün için iki farklı reçete kullanabilir miyim?**
Evet, iş emri oluştururken hangi reçetenin kullanılacağını seçebilirsiniz.

**Üretim sırasında malzeme değişikliği yapabilir miyim?**
Evet, iş emrindeki malzeme listesini onay yetkisi olan kullanıcı değiştirebilir.

---

## Bölüm 3: Operatör Paneli

### 3.1 Panel Ne İçin?

Makine başında çalışan operatörlerin, masaüstü bilgisayar veya dokunmatik ekranla hızlıca işlem yapması için tasarlanmış basit bir arayüzdür.

**Operatör panelinden yapılabilecekler:**
- Üstlenilen iş emirlerini görme
- Operasyona başlama ve bitirme
- Üretim miktarı ve fire girişi
- Makine duruşu bildirimi

---

### 3.2 Operatöre İş Emri Atama

1. İş emrini açın → **Operasyon** sekmesi
2. Her operasyon satırında **Operatör Ata**
3. Çalışanı seçin → **Kaydet**

---

### 3.3 Operatör Olarak Giriş Yapma

1. Operatör panelini açın (Sol menü → Operatör Paneli)
2. Adınıza atanan iş emirleri listelenir
3. **Başla** → üretim süresi sayılmaya başlar
4. **Tamamla** → süre kaydedilir, miktar girilir

---

## Bölüm 4: Canlı OEE İzleme

### OEE Nedir?

OEE (Genel Ekipman Verimliliği), bir makinenin ne kadar verimli çalıştığını ölçen bir göstergedir. 3 bileşenden oluşur:

| Bileşen | Soru | Yüksek Olması İçin |
|---------|------|-------------------|
| **Kullanılabilirlik** | Makine planlanan zamanda çalıştı mı? | Arıza az olmalı |
| **Performans** | Hızı nominal hıza ne kadar yakın? | Yavaşlama az olmalı |
| **Kalite** | Üretilen kaçı hatalısız? | Fire az olmalı |

OEE = Kullanılabilirlik × Performans × Kalite

---

### 4.1 OEE İzleme Sayfası

- **Canlı OEE İzleme** sayfasında tüm makineler anlık durum kartlarıyla gösterilir
- Yeşil: Çalışıyor | Sarı: Planlı Duruş | Kırmızı: Arıza
- Seçilen tarih aralığında OEE trendi grafiği izlenebilir

---

## Bölüm 5: Diğer Modüllerle Bağlantı

| Modül | Bağlantı |
|-------|---------|
| **Stok** | Malzeme sarf → otomatik çıkış; mamul tamamlama → otomatik giriş |
| **Planlama** | MPS/MRP'den iş emirleri otomatik oluşturulabilir |
| **Bakım** | Makine arızası → bakım talebi oluşturur |
| **Kalite** | Üretim tamamlamada kalite kontrolü tetiklenebilir |
| **İK** | Operatör çalışma süreleri puantaja aktarılabilir |

---

## Hızlı Başlangıç Listesi

- [ ] Planlama modülünde Ürün Reçetelerini tanımlayın
- [ ] Planlama modülünde İş İstasyonlarını tanımlayın
- [ ] İlk iş emrini oluşturun
- [ ] Malzeme durumunu kontrol edin
- [ ] Üretimi başlatın
- [ ] Operatör panelinden operasyonları kaydedin
- [ ] Üretimi tamamlayın

---

*Önceki: [Satış ←](03-satis.md) | Sonraki: [Planlama →](05-planlama.md)*
