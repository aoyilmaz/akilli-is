# e-Dönüşüm — Kullanıcı El Kitabı

> Bu bölüm, e-Fatura ve e-Arşiv Fatura süreçlerini anlatır.

---

## e-Dönüşüm Modülü Ne İşe Yarar?

Türk vergi mevzuatı kapsamında Gelir İdaresi Başkanlığı'na (GİB) elektronik ortamda fatura gönderip almayı sağlar. Kağıt fatura yerine geçen yasal bir belgedir.

**Temel kavramlar:**

| Kavram | Açıklama |
|--------|---------|
| **e-Fatura** | GİB sistemine kayıtlı firmalar arasında gönderilen elektronik fatura |
| **e-Arşiv** | GİB'e kayıtlı olmayan alıcılara veya bireysel müşterilere gönderilen elektronik fatura |
| **e-İrsaliye** | Elektronik sevk irsaliyesi |
| **GİB** | Gelir İdaresi Başkanlığı — faturaların onaylandığı devlet kurumu |

> ⚠️ **Dikkat:** e-Fatura mükellefi olmak için GİB'e başvuru yapılmış ve sistem entegrasyonu tamamlanmış olmalıdır. Bu kurulum sistem yöneticiniz veya muhasebeci tarafından yapılır.

---

## Arayüze İlk Bakış

Sol menüde **e-DÖNÜŞÜM** altındaki sayfalar:

| Sayfa | Ne İçin |
|-------|---------|
| e-Faturalar | Gönderilen ve alınan e-Fatura listesi |

---

## Bölüm 1: e-Fatura Gönderme

### 1.1 Akış

```
Satış Faturası Oluştur (Satış Modülü)
            ↓
        Faturayı Onayla
            ↓
    e-Faturaya Dönüştür
            ↓
  GİB'e Gönder → Yanıt Bekle
            ↓
  Kabul / Ret → Müşteriye İlet
```

---

### 1.2 Satış Faturasından e-Fatura Oluşturma

1. Satış modülünde faturayı oluşturun ve onaylayın
2. Faturayı açın → **e-Fatura Gönder** butonuna tıklayın
3. Fatura türü seçin:
   - **e-Fatura:** Alıcı GİB sisteminde kayıtlıysa (müşteri VKN'si sorgulanır)
   - **e-Arşiv:** Alıcı GİB'de kayıtlı değilse
4. Belge tipi seçin: **Satış** / **İhracat** / **İstisna** / **Özel Matrah**
5. **Gönder**

> 💡 **İpucu:** Sistem müşterinin e-Fatura mükellefiyetini otomatik sorgular. e-Fatura mükellefiyse e-Fatura, değilse e-Arşiv gönderilmesi gerekir. Sistem bunu size belirtir.

---

### 1.3 Gönderim Durumları

| Durum | Anlamı |
|-------|--------|
| **Bekliyor** | GİB'e iletilmedi |
| **Gönderildi** | GİB'e iletildi, yanıt bekleniyor |
| **Kabul Edildi** | GİB onayladı, müşteriye ulaştı |
| **Reddedildi** | GİB hata bildirdi |
| **İptal Edildi** | Fatura iptal edildi |

---

### 1.4 Reddedilen Fatura

Fatura GİB tarafından reddedilirse:
1. **e-Faturalar** listesinde "Reddedildi" durumundaki faturayı açın
2. Red nedenini görün
3. Satış modülünde faturayı düzeltin (iptal edip yeniden oluşturun)
4. Yeni faturayı tekrar gönderin

---

## Bölüm 2: e-Fatura Alma (Gelen Faturalar)

### 2.1 Gelen Fatura Akışı

Tedarikçiniz size e-Fatura gönderdiğinde sistem otomatik alır:

```
Tedarikçi GİB'e fatura gönderir
           ↓
  Sistem gelen kutusuna düşer
           ↓
   Kabul veya Ret kararı ver
           ↓
  Satın alma faturasına aktar
```

---

### 2.2 Gelen Faturaları Görüntüleme

1. **e-Faturalar** sayfasına gidin
2. **Gelen Faturalar** filtresini seçin
3. Yeni gelen faturalar listelenir

---

### 2.3 Gelen Faturayı Kabul Etme

1. İlgili faturayı açın
2. Tutarları ve kalemleri kontrol edin
3. **Kabul Et** butonuna tıklayın
4. Satın alma modülüne aktarmak isteyip istemediğiniz sorulur → **Evet**

---

### 2.4 Gelen Faturayı Reddetme

Faturada hata varsa (yanlış tutar, yanlış KDV, yanlış alıcı vb.):
1. **Reddet** butonuna tıklayın
2. Ret nedenini yazın → **Gönder**
3. Sistem red yanıtını GİB'e iletir, tedarikçi haberdâr olur

> ⚠️ **Dikkat:** Gelen e-Faturayı reddetmek için GİB'in belirlediği süre (genellikle 8 gün) içinde işlem yapılmalıdır. Süresi geçen fatura otomatik kabul sayılır.

---

## Bölüm 3: e-Fatura Listesi ve Filtreleme

**e-Faturalar** listesinde:

| Filtre | Açıklama |
|--------|---------|
| Gönderilen / Gelen | Yön filtresi |
| Tarih Aralığı | Dönem filtresi |
| Durum | Bekliyor / Kabul / Ret |
| Müşteri / Tedarikçi | Firma filtresi |

**Dışa Aktarma:** Seçilen döneme ait faturaları Excel veya PDF olarak indirin.

---

## Bölüm 4: Sık Sorulan Sorular

**e-Fatura ile normal fatura arasındaki fark nedir?**
e-Fatura yasal olarak kağıt fatura ile aynı değerdedir. Fark: elektronik olarak gönderilir, arşivlenir ve GİB sistemi üzerinden onaylanır. Kağıt basmanıza gerek yoktur.

**Müşterim e-Fatura mükellefiyse kağıt fatura gönderebilir miyim?**
Hayır. GİB'e kayıtlı mükelleflere mutlaka e-Fatura gönderilmesi zorunludur.

**e-Faturayı iptal etmem gerekirse ne yapmalıyım?**
Gönderilen gün içinde GİB'e "İptal" bildirimi yapılabilir. Aynı gün geçmişse "iade faturası" kesilmesi gerekir. Muhasebecinizvarsayılanınızla iletin.

**GİB'e bağlantı kesilirse ne olur?**
Sistem faturayı "Bekliyor" olarak tutar. Bağlantı tekrar sağlandığında otomatik iletir.

---

## Bölüm 5: Diğer Modüllerle Bağlantı

| Modül | Bağlantı |
|-------|---------|
| **Satış** | Onaylanan satış faturası → e-Faturaya dönüştürülür |
| **Satınalma** | Gelen e-Fatura → satın alma faturasına aktarılır |
| **Muhasebe** | e-Fatura kabul → muhasebe kaydı oluşur |

---

*Önceki: [Proje Yönetimi ←](13-proje.md) | Sonraki: [Sistem Ayarları →](15-sistem.md)*
