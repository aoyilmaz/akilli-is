# Sistem Ayarları — Kullanıcı El Kitabı

> Bu bölüm, kullanıcı yönetimini, yetki ayarlarını ve sistem genelindeki yapılandırmaları anlatır.
> Bu sayfalar genellikle **sistem yöneticisi** yetkisine sahip kişiler tarafından kullanılır.

---

## Sistem Ayarları Ne İçin?

Programın altyapısını yönetir: kimler sistemi kullanabilir, hangi yetkilerle, hangi firma bilgileriyle. Ayrıca hata kayıtları ve işlem geçmişi gibi teknik takip araçları da bu bölümde yer alır.

---

## Arayüze İlk Bakış

Sol menüde **GELİŞTİRME** (Sistem Ayarları) altındaki sayfalar:

| Sayfa | Ne İçin |
|-------|---------|
| Firma Kartı | Şirket bilgileri (logo, adres, vergi no) |
| Kullanıcı Yönetimi | Kullanıcı hesapları ve roller |
| İş Akışları | Onay süreçleri |
| Tema Ayarları | Renk teması seçimi |
| İşlem Geçmişi | Kim ne yaptı? |
| Yazdırma Şablonları | Fatura, irsaliye gibi belgeler |
| Hata Kayıtları | Sistem hataları |
| Trace Görüntüle | Teknik sorun izleme |

---

## Bölüm 1: Firma Kartı

### 1.1 Firma Bilgilerini Güncelleme

1. **Firma Kartı** sayfasına gidin
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Firma Adı | Yasal ticari unvan |
| Vergi Kimlik No | 10 haneli VKN |
| Vergi Dairesi | |
| Adres | Fatura adresi |
| Telefon / E-posta | |
| Web Sitesi | |
| Logo | Fatura ve belgelerde görünecek logo |
| e-Fatura Ayarları | GİB entegrasyon bilgileri |

3. **Kaydet**

> 💡 **İpucu:** Logo 300×100 piksel, PNG veya JPG formatında olması önerilir.

---

## Bölüm 2: Kullanıcı Yönetimi

### 2.1 Kullanıcı Nedir?

Sisteme giriş yapabilen her kişi bir kullanıcıdır. Her kullanıcının bir **rol** ve **yetki** seti vardır.

---

### 2.2 Yeni Kullanıcı Oluşturma

1. **Kullanıcı Yönetimi** → **Yeni Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Ad Soyad | |
| Kullanıcı Adı | Giriş için kullanılacak (küçük harf, boşluksuz) |
| E-posta | |
| Şifre | En az 8 karakter, büyük/küçük harf ve rakam içermeli |
| Rol | Yönetici, Muhasebeci, Depocu vb. |
| Aktif | Hesabın açık olup olmadığı |

3. **Kaydet**

> ⚠️ **Dikkat:** Yeni kullanıcıya ilk giriş şifresini güvenli bir kanaldan iletin. İlk girişte şifre değiştirmesi önerilir.

---

### 2.3 Sistem Rolleri

Sistem önceden tanımlı roller gelir:

| Rol | Kapsam |
|-----|--------|
| **Sistem Yöneticisi** | Tüm modüllere tam erişim |
| **Yönetici** | Raporları ve yönetim ekranlarını görür |
| **Muhasebeci** | Finans ve muhasebe modülleri |
| **Depocu** | Stok modülü ve depocu paneli |
| **Satış Temsilcisi** | Satış ve CRM modülleri |
| **Satın Alma** | Satınalma modülü |
| **Üretim** | Üretim ve planlama modülleri |
| **İzleyici** | Yalnızca görüntüleme, kayıt oluşturamaz |

---

### 2.4 Kullanıcıya Özel Yetki Ayarlama

Standart rol yetmiyorsa belirli modüller için ek yetki eklenebilir veya kaldırılabilir:

1. Kullanıcıyı açın → **Yetkiler** sekmesi
2. Modül bazında yetkiler listelenir:
   - `inventory.view` — Stok görüntüleme
   - `inventory.create` — Stok oluşturma
   - `sales.edit` — Satış düzenleme
   - vb.
3. İstenen yetkiyi açın/kapatın → **Kaydet**

---

### 2.5 Kullanıcı Hesabı Devre Dışı Bırakma

Bir çalışan ayrıldığında:
1. Kullanıcıyı açın
2. **Aktif** alanını **Hayır** yapın → **Kaydet**
3. Kullanıcı sisteme giremez, geçmiş işlemleri korunur

> ⚠️ **Dikkat:** Ayrılan çalışanın hesabını **hemen** devre dışı bırakın.

---

## Bölüm 3: İş Akışları (Onay Süreçleri)

### 3.1 İş Akışı Nedir?

Belirli belgelerin onay sürecini tanımlar. Örneğin: "1.000 TL üzeri satın alma talebi departman müdürü onayından geçmeli" gibi.

---

### 3.2 Onay Akışı Oluşturma

1. **İş Akışları** → **Yeni Ekle**
2. Hangi belge türü için (Satın Alma Talebi, Satış Teklifi vb.) seçin
3. Koşulları belirleyin (örn: tutar > 5.000 TL)
4. Onay adımlarını tanımlayın:
   - 1. Adım: Departman Yöneticisi
   - 2. Adım: Genel Müdür (tutar > 50.000 TL ise)
5. **Kaydet**

---

## Bölüm 4: Yazdırma Şablonları

### 4.1 Şablon Nedir?

Fatura, irsaliye, teklif gibi belgelerin basılı formatıdır. Logo, firma bilgisi ve belge kalemleri düzenlenebilir.

---

### 4.2 Şablon Seçme

1. **Yazdırma Şablonları** sayfasına gidin
2. Belge türünü seçin (Satış Faturası, Sevk İrsaliyesi, Teklif vb.)
3. Aktif şablonu seçin veya yeni şablon yükleyin
4. **Kaydet**

> 💡 **İpucu:** Şablon tasarımı için sistem yöneticinizden veya yazılım desteğinden yardım alın.

---

## Bölüm 5: Tema Ayarları

Programın renk temasını değiştirebilirsiniz:

1. **Tema Ayarları** sayfasına gidin
2. Hazır temalar arasından seçin (Açık / Koyu / Mavi / Yeşil vb.)
3. Ana rengi özelleştirin
4. **Uygula**

Tema değişikliği yalnızca kendi hesabınıza uygulanır.

---

## Bölüm 6: İşlem Geçmişi (Audit Log)

### 6.1 İşlem Geçmişi Nedir?

Sistemde gerçekleştirilen her değişiklik otomatik olarak kaydedilir: Kim, ne zaman, hangi kayıtta, ne değiştirdi.

---

### 6.2 İşlem Geçmişi Görüntüleme

1. **İşlem Geçmişi** sayfasına gidin
2. Filtreler:

| Filtre | Açıklama |
|--------|---------|
| Tarih Aralığı | Hangi dönem |
| Kullanıcı | Kimin işlemi |
| İşlem Türü | Oluşturma / Düzenleme / Silme |
| Modül | Hangi modül |

3. Bir kayda tıklayın → değişiklik öncesi ve sonrası değerler yan yana gösterilir

> 💡 **İpucu:** Bir kayıtta beklenmedik değişiklik fark ettiyseniz, işlem geçmişinden kim değiştirdi ve ne zaman sorularını yanıtlayabilirsiniz.

---

## Bölüm 7: Hata Kayıtları

Sistem bir hatayla karşılaştığında otomatik olarak kaydeder. Teknik destek alırken bu bilgileri paylaşın:

1. **Hata Kayıtları** sayfasına gidin
2. Hatanın oluştuğu tarih ve modülü filtreleyin
3. Hata detayını açın ve ekran görüntüsü alın
4. Destek ekibine gönderin

---

## Bölüm 8: Sık Sorulan Sorular

**Şifremi unuttum; ne yapmalıyım?**
Giriş ekranındaki "Şifremi Unuttum" seçeneği veya sistem yöneticinizle iletişime geçin.

**Başka bir kullanıcının hangi sayfaları görebildiğini nasıl kontrol ederim?**
Kullanıcı Yönetimi → ilgili kullanıcıyı açın → Yetkiler sekmesi.

**Yanlışlıkla bir kaydı sildim (pasif yaptım); geri alabilir miyim?**
Evet. İlgili modülde "Pasif" filtresini açın, kaydı bulun ve "Aktif Yap" butonuna tıklayın.

**Sistemin yavaşladığını fark ettim; ne yapmalıyım?**
Hata Kayıtları sayfasını kontrol edin. Sorun devam ederse sistem yöneticinize bildirin.

---

*Önceki: [e-Dönüşüm ←](14-efatura.md) | [Ana Sayfaya →](00-giris.md)*
