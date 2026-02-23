# Akıllı İş ERP — Kullanıcı El Kitabı Giriş

> Bu el kitabı, **Akıllı İş ERP** programını ilk kez kullananlar için hazırlanmıştır.
> Her bölüm bağımsız okunabilir; doğrudan ilgilendiğiniz modüle atlayabilirsiniz.

---

## ERP Nedir? Neden Kullanırız?

ERP (Kurumsal Kaynak Planlama), bir işletmenin tüm departmanlarının tek bir programdan yönetilmesini sağlar. Satın alınan malzemeden müşteriye gönderilen ürüne, maaş ödemesinden kalite kontrolüne kadar her işlem bu sistemde kayıt altına alınır.

**Kağıt ya da Excel ile fark nedir?**

| Eski Yöntem | ERP ile |
|-------------|---------|
| Her departman kendi tablosunu tutar | Herkes aynı veriyi görür |
| Stok miktarı tahmine dayanır | Anlık stok takibi |
| Fatura elle kesilir, muhasebe geç aktarır | Fatura kesilince muhasebe otomatik güncellenir |
| Raporlar haftalarca gecikmeli | Anlık raporlar |

---

## Programa Giriş

1. Masaüstündeki **Akıllı İş** simgesine çift tıklayın
2. **Kullanıcı adı** ve **şifrenizi** girin
3. **Giriş Yap** butonuna tıklayın

> ⚠️ **Dikkat:** Şifrenizi kimseyle paylaşmayın. Sistemdeki her işlem kullanıcı adınıza kaydedilir.

> 💡 **İpucu:** Şifrenizi unutursanız sistem yöneticinize başvurun.

---

## Ana Ekranın Yapısı

Program açıldığında üç ana bölüm görürsünüz:

```
┌─────────────────────────────────────────────────┐
│  Üst Çubuk: Bildirimler | Kullanıcı Adı | Çıkış │
├──────────────┬──────────────────────────────────┤
│              │                                  │
│  Sol Menü    │      İçerik Alanı                │
│  (Modüller)  │      (Açık Sekmeler)             │
│              │                                  │
└──────────────┴──────────────────────────────────┘
```

### Sol Menü

Tüm modüller sol menüde gruplar halinde listelenir:
- **GENEL BAKIŞ** — Dashboard (özet gösterge paneli)
- **STOK YÖNETİMİ** — Ürün ve malzeme takibi
- **SATINALMA** — Tedarikçi ve sipariş yönetimi
- **SATIŞ YÖNETİMİ** — Müşteri ve satış işlemleri
- ve diğer modüller…

Bir menü öğesine tıkladığınızda sağ tarafta yeni sekme açılır.

### Sekmeler

Birden fazla sayfayı aynı anda açık tutabilirsiniz. Bir sekmeyi kapatmak için üzerindeki **×** simgesine tıklayın.

### Üst Çubuk

- **Zil simgesi:** Sistem bildirimleri (onay bekleyen belgeler, uyarılar)
- **Kullanıcı adı:** Profil bilgileri
- **Çıkış:** Programdan güvenli çıkış

---

## Ortak Ekran Öğeleri

Her liste sayfasında aynı bileşenler bulunur:

### Arama Kutusu
Sayfanın üst kısmındadır. Yazdıkça liste anında filtrelenir. Kod, ad veya herhangi bir metin aranabilir.

### Yeni Ekle Butonu
Yeni kayıt oluşturmak için kullanılır. Genellikle sayfanın sağ üst köşesindedir.

### Tablo

| Öğe | Açıklama |
|-----|---------|
| Sütun başlığına tıkla | O sütuna göre sıralar |
| Satır üzerindeki kalem | Kaydı düzenler |
| Satır üzerindeki çöp kutusu | Kaydı pasif yapar |
| Satıra çift tıkla | Kaydı görüntüler/açar |

### Filtreler
Tablonun üzerinde tür, durum veya tarih gibi hızlı filtreler bulunabilir.

### Alt Bilgi (Footer)
Tablo altında kayıt sayısı ve özet istatistik kartları gösterilir.

---

## Ortak Butonlar ve Anlamları

| Buton / Simge | Ne Yapar |
|--------------|---------|
| **Yeni Ekle** | Yeni kayıt formu açar |
| **Kaydet** | Formdaki değişiklikleri kaydeder |
| **İptal** | Formu kapatır, değişiklikleri atar |
| **Düzenle** (kalem) | Seçili kaydı düzenler |
| **Sil** (çöp kutusu) | Kaydı pasif yapar (silmez) |
| **Dışa Aktar** | Excel veya PDF olarak indirir |
| **Yenile** | Sayfayı güncel verilerle yeniler |

---

## Silme Kavramı: Pasif Yapma

Akıllı İş'te hiçbir kayıt gerçekten silinmez. "Sil" butonuna bastığınızda kayıt **pasif** duruma geçer:

- Aktif listelerde görünmez
- Geçmiş belgelerde ve raporlarda korunur
- Sistem yöneticisi tarafından tekrar aktif yapılabilir

Bu sayede geçmiş veriler her zaman erişilebilir kalır.

---

## Formlar

Bir kayıt oluşturma veya düzenleme formu açıldığında:

1. **Zorunlu alanlar** kırmızı yıldız (\*) ile işaretlidir
2. Formlarda birden fazla **sekme** olabilir (Temel Bilgiler, Detaylar, Notlar vb.)
3. **Kaydet** butonuna basmadan önce tüm zorunlu alanları doldurun
4. Hatalı alan varsa sistem uyarı verir ve ilgili alanı işaretler

---

## Bildirimler

Üst çubukta zil simgesi yanındaki sayı, okunmamış bildirim sayısını gösterir.

Bildirimler şunları içerebilir:
- Onayınızı bekleyen belgeler
- Kritik stok seviyesine düşen ürünler
- Size atanan görevler
- Sistem uyarıları

---

## Dashboard (Genel Bakış)

Program açılışında ilk görünen sayfa Dashboard'dur. Buradan:

- Bugünkü satış ve satın alma özetlerini
- Kritik stok uyarılarını
- Onay bekleyen belge sayısını
- Son işlemlerin özetini görürsünüz

---

## Modüller ve El Kitabı Bölümleri

| Bölüm | Konu |
|-------|------|
| [01 — Stok Yönetimi](01-stok.md) | Ürün ve malzeme takibi |
| [02 — Satınalma](02-satin-alma.md) | Tedarikçi, sipariş, mal kabul |
| [03 — Satış](03-satis.md) | Müşteri, teklif, sipariş, fatura |
| [04 — Üretim](04-uretim.md) | İş emirleri, operatör paneli |
| [05 — Planlama](05-planlama.md) | MPS, MRP, kapasite |
| [06 — Kalite Kontrol](06-kalite.md) | Denetim, uygunsuzluk, CAPA |
| [07 — Bakım & Onarım](07-bakim.md) | Ekipman ve bakım planları |
| [08 — Sevkiyat](08-sevkiyat.md) | Sevkiyat ve araç takibi |
| [09 — Finans](09-finans.md) | Tahsilat ve ödeme |
| [10 — Muhasebe](10-muhasebe.md) | Hesap planı, yevmiye, raporlar |
| [11 — İnsan Kaynakları](11-ik.md) | Personel, izin, puantaj |
| [12 — CRM](12-crm.md) | Potansiyel müşteri, fırsat, aktivite |
| [13 — Proje Yönetimi](13-proje.md) | Proje ve görev takibi |
| [14 — e-Dönüşüm](14-efatura.md) | e-Fatura, e-Arşiv |
| [15 — Sistem Ayarları](15-sistem.md) | Kullanıcılar, roller, ayarlar |

---

*Bir sonraki bölüm: [Stok Yönetimi →](01-stok.md)*
