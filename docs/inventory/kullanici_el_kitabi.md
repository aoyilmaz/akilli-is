# Akıllı İş - Stok Modülü Kullanıcı El Kitabı

---

## 1. Giriş

Stok Modülü, işletmenizin tüm malzeme ve ürün akışını yöneten merkezi sistemdir. Her türlü ürün (hammadde, yarı mamul, mamul, ticari mal) bu modül üzerinden takip edilir.

### Temel Prensipler
*   **Her Şey Bir "Stok Kartı"dır:** Sistemде takip edilecek her varlık bir stok kartı olarak tanımlanmalıdır.
*   **Hareket Esastır:** Stok miktarları elle değiştirilemez. Her artış veya azalış bir "Hareket Fişi" ile kayıt altına alınır.
*   **Depo ve Lokasyon:** Ürünler bir deponun belirlenen raflarında durur. Sistem bu lokasyonları takip eder.
*   **Maliyet Takibi:** Sistem ağırlıklı ortalama maliyet yöntemini otomatik kullanır.

---

## 2. Sayfa Açıklamaları

### 2.1. Stok Kartları Listesi
**Amaç:** Sistemdeki tüm ürünlerin listelendiği ana ekrandır.

**Özellikler:**
*   **Filtreleme:** Üst kısımdan "Tür" (Hammadde, Mamul vb.) ve "Durum" (Normal, Kritik, Stok Yok) seçenekleriyle listeyi daraltabilirsiniz.
*   **Arama:** Barkod, stok kodu veya ürün adı ile hızlı arama yapabilirsiniz.
*   **Renkli Gösterim:** 🔴 Kırmızı = Kritik, 🟡 Sarı = Düşük, ✅ Yeşil = Normal.
*   **İşlem Menüsü:** Satıra sağ tıklayarak Düzenle, Sil, Hareket Geçmişi'ne ulaşabilirsiniz.
*   **Dışa Aktarım:** Excel/PDF veya ürün etiketi (barkod) alabilirsiniz.

**İstatistik Kartları:** Ekranın üst kısmında Toplam Ürün, Normal, Düşük Stok ve Kritik Stok sayıları anlık gösterilir.

---

### 2.2. Stok Kartı Formu (Yeni/Düzenle)
**Amaç:** Yeni ürün tanımlamak veya mevcut ürünü düzenlemek.

**4 Sekme:**

| Sekme | Alanlar |
| :--- | :--- |
| **Genel Bilgiler** | Stok Kodu*, Stok Adı*, Barkod, Tür*, Birim*, Kategori, Marka, Model |
| **Stok Ayarları** | Min. Stok, Maks. Stok, Yeniden Sipariş Noktası, Temin Süresi, Fiziksel Özellikler (Ağırlık, Hacim) |
| **Fiyatlandırma** | Alış Fiyatı, Satış Fiyatı, Liste Fiyatı, KDV Oranı, Tevkifat Oranı |
| **Takip** | Lot Takibi, Seri No Takibi, Son Kullanma Tarihi Takibi, Raf Ömrü |

`*` işaretli alanlar zorunludur.

---

### 2.3. Kategoriler
**Amaç:** Ürünleri gruplamak için hiyerarşik bir ağaç yapısı oluşturmak.

**Özellikler:**
*   **Ağaç Görünümü:** Kategoriler alt-üst ilişkili olarak (Elektronik > Bilgisayar > Laptop) görüntülenir.
*   **Alt Kategori Ekleme:** Bir kategoriye sağ tıklayın > "Alt Kategori Ekle".
*   **Ürün Sayısı:** Her kategorinin kaç ürün içerdiği görüntülenir.
*   **Tümünü Aç/Kapat:** Üst menüdeki butonlarla ağacı açıp kapatabilirsiniz.

---

### 2.4. Birimler
**Amaç:** Ürün takip birimlerini (Adet, Kg, Lt, Kutu vb.) tanımlamak ve birimler arası dönüşüm oranlarını belirlemek.

**İki Bölüm:**
1.  **Birimler Listesi:** Kod, Ad, Kısa Ad, Durum. Örn: `KG`, `Kilogram`, `kg`.
2.  **Birim Dönüşümleri:** Örn: 1 KUTU = 12 ADET. Bu tanım yapılınca sisteme "5 KUTU" girerseniz "60 ADET" olarak da gösterir.

---

### 2.5. Depolar
**Amaç:** Şirketin fiziksel depo tanımlarını yönetmek.

**Özellikler:**
*   **Depo Türleri:** Genel, Hammadde, Mamul, Soğuk, Antrepo.
*   **Varsayılan Depo:** Fişler açılırken öntanımlı gelecek depoyu işaretleyebilirsiniz.
*   **Lokasyonlar:** Her satıra sağ tıklayarak o deponun raf/göz planını yönetebilirsiniz.

---

### 2.6. Lokasyonlar
**Amaç:** Depo içi raf/koridor/göz adres sistemini kurmak.

**Format:** `Koridor-Raf-Kat` (Örn: `A-01-03`)

**Toplu Oluşturma:** "Toplu Ekle" seçeneğiyle A'dan Z'ye koridorlar, 1-10 arası raflar için yüzlerce lokasyonu tek seferde oluşturabilirsiniz. Sistem her lokasyona otomatik `LOC-XXXXXXXX` barkodu atar.

---

### 2.7. Stok Hareketleri
**Amaç:** Depoya giren/çıkan veya depolar arası transfer edilen her malzemenin kaydı.

**Hareket Türleri:**
*   📥 **Giriş Fişi:** Satın alma, üretimden giriş, sayım fazlası.
*   📤 **Çıkış Fişi:** Satış, üretime sevk, fire, sayım eksiği.
*   🔄 **Transfer:** Depo A'dan Depo B'ye.

**Filtreleme:** Tür, tarih aralığı ve arama kutusuyla hareketleri süzebilirsiniz.

**İstatistikler:** Toplam Hareket, Giriş Tutarı (₺), Çıkış Tutarı (₺) anlık gösterilir.

---

### 2.8. Stok Sayımı
**Amaç:** Fiili stok ile sistemdeki stoğu karşılaştırmak ve farkları düzeltmek.

**Sayım Durumları:**
| Durum | Açıklama |
| :--- | :--- |
| 🟡 Taslak | Sayım oluşturuldu, henüz sayılmadı. |
| 🔵 Devam Ediyor | Sayım başladı, ürünler giriliyor. |
| ✅ Tamamlandı | Sayım bitti, onay bekliyor. |
| 📥 Uygulandı | Farklar stoklara yansıtıldı. |

**Uygula İşlemi:** Sayım tamamlandıktan sonra sağ tık > "Stoklara Uygula" dediğinizde sistem otomatik olarak "Sayım Fazlası" veya "Sayım Eksiği" fişleri oluşturur.

---

### 2.9. Taşıma Birimleri (SSCC / Palet)
**Amaç:** Ürünleri palet veya koli bazında bir taşıma birimi (SSCC kodu) altında gruplamak.

**Durum Akışı:**
| Durum | Açıklama |
| :--- | :--- |
| 🔓 Açık | Palete ürün eklenebilir. |
| 🔒 Kapalı | Palet kapatıldı, ürün eklenemez. |
| 🚚 Sevk Edildi | Müşteriye gönderildi. |
| ❌ İptal | Kullanılmıyor. |

**Kullanım:** Üretimden çıkan mamulleri bir palet kodu altında toplar, depo lokasyonuna yerleştirir ve sevkiyat sırasında palet bazlı çıkış yaparsınız.

---

### 2.10. Stok Raporları
**Amaç:** Stok durumunu analiz etmek.

**4 Rapor Sekmesi:**
| Rapor | İçerik |
| :--- | :--- |
| **Stok Durumu** | Tüm ürünlerin anlık miktar, maliyet, toplam değer bilgisi. |
| **Kritik Stoklar** | Minimum seviyenin altındaki veya tükenmiş ürünler. |
| **Hareket Özeti** | Ürün bazlı Toplam Giriş, Çıkış, Net Değişim. |
| **Depo Raporu** | Depo bazlı stok dağılımı ve lokasyon detayı. |

---

### 2.11. Depocu Paneli
**Amaç:** Tablet/mobil uyumlu, büyük butonlu operasyon ekranı.

**Menü Seçenekleri:**
| Buton | Açıklama |
| :--- | :--- |
| 📥 Mal Kabul | Gelen malı okutup raflara yerleştirme (Put-away). |
| 📦 Toplama | Sipariş toplama listeleri (Picking). |
| 🔄 Transfer | Depolar arası ürün taşıma. |
| 📋 Sayım | Lokasyon bazlı hızlı sayım. |
| 🔍 Stok Sorgula | Barkod okutarak anlık stok bilgisi. |
| 📍 Adres Okut | Raf barkodunu okutarak içeriğini görme. |

**Kullanıcı Deneyimi:** El terminali veya tabletler için optimize edilmiş; barkod okutma odaklı.

---

## 3. İş Akışları

### 3.1. Mal Kabul (Satın Alma Girişi)
1.  Tedarikçiden mallar gelir, irsaliye kontrol edilir.
2.  **Stok Hareketleri > Giriş Fişi (📥)** açılır.
3.  Depo ve ürün seçilir, miktar girilir.
4.  (Opsiyonel) Lot numarası veya SKT girilir.
5.  Kaydet. → Stok artar, maliyet ortalaması güncellenir.

### 3.2. Satış Çıkışı
1.  Müşteri siparişi alınır.
2.  Mallar toplanır (Picking).
3.  **Stok Hareketleri > Çıkış Fişi (📤)** işlenir.
4.  Stok düşer.

### 3.3. Depolar Arası Transfer
1.  Merkez Depo > Şube Depo transfer edilecek.
2.  **Stok Hareketleri > Transfer (🔄)** açılır.
3.  Kaynak ve Hedef Depo seçilir, ürün/miktar girilir.
4.  Kaydet. → Kaynak depoda stok düşer, hedefte artar.

### 3.4. Stok Sayımı
1.  **Stok Sayımı > Yeni Sayım** açılır, depo seçilir.
2.  Ürünler fiziksel olarak sayılır, "Sayılan Miktar" girilir.
3.  Sayım tamamlandığında sağ tık > **Stoklara Uygula**.
4.  Sistem fark fişleri (Sayım Fazlası / Eksiği) otomatik oluşturur.

---

## 4. Sık Karşılaşılan Hatalar ve Çözümleri

| Hata | Sebep | Çözüm |
| :--- | :--- | :--- |
| **Negatif Stok Hatası** | Eldekinden fazla çıkış. | Önce fiziksel stoğu sayın; eksik ise giriş fişi kesin. |
| **Mükerrer Kod/Barkod** | Bu kod başka üründe var. | Mevcut ürünü arayın; yeni kart açmayın. |
| **Silme Başarısız** | Hareket görmüş kart silinemez. | Kartı **pasife** alın (Aktif kutusunu kaldırın). |
| **Birim Değiştirilemez** | Hareket görmüş kart. | Yeni stok kartı açın, eskisini pasife alın. |

---

## 5. İpuçları

*   📦 **Düzenli Sayım:** Ayda bir "Sayım Modülü"nü kullanarak tutarsızlıkları erken yakalayın.
*   🏷️ **Etiketleme:** Ürünleri rafa koymadan önce barkod etiketi yapıştırın.
*   📊 **Raporlar:** "Kritik Stoklar" raporunu haftada bir kontrol edin.
*   📍 **Lokasyon Kullanın:** Raf adresleri tanımlarsanız mal toplama süresi %50 düşer.
*   🔄 **Birim Dönüşümü:** Tedarikçi irsaliyesi "Koli" ama siz "Adet" takip ediyorsanız, dönüşüm oranını girin.
