# Akıllı İş - Stok Modülü Kullanıcı El Kitabı

## 1. Giriş ve Çalışma Mantığı

Akıllı İş Stok Modülü, işletmenizin tüm malzeme akışını (Hammadde > Üretim > Mamul > Satış) kayıt altına alan ve yöneten merkezi birimdir.

### Temel Prensipler
1.  **Her Şey Bir Karttır:** Sistemde takip edilecek her varlık (vida, bilgisayar, hizmet, koli) bir "Stok Kartı" olarak tanımlanmalıdır.
2.  **Hareket Esastır:** Stok miktarları elle değiştirilemez. Stok artışı için "Giriş Hareketi", azalışı için "Çıkış Hareketi" yapılmalıdır. Sistem bakiyeyi bu hareketlerden hesaplar.
3.  **Depo ve Lokasyon:** Ürünler havada durmaz; mutlaka bir "Depo" ve o deponun bir "Lokasyonu" (Raf/Göz) üzerinde dururlar.

---

## 2. İş Akışları

Aşağıda sistemdeki temel operasyonların nasıl yürüdüğü özetlenmiştir.

### 2.1. Mal Kabul (Satın Alma) Akışı
1.  Tedarikçiden malzemeler gelir.
2.  İrsaliye kontrol edilir.
3.  Sisteme **Satın Alma Giriş Fişi** işlenir.
4.  Malzemeler ilgili depoya ve raflara yerleştirilir.
5.  Stok miktarı artar ve maliyet ortalaması güncellenir.

### 2.2. Satış ve Sevk Akışı
1.  Müşteri siparişi gelir.
2.  Depodan mallar toplanır (Picking).
3.  Sisteme **Satış Çıkış Fişi** veya **İrsaliye** işlenir.
4.  Stok miktarı düşer.

### 2.3. Depo Transfer Akışı
1.  Merkez depodan Şube depoya mal gönderilecekse **Transfer Fişi** oluşturulur.
2.  Kaynak depodan stok düşer, hedef depoda henüz "Yolda" statüsüne geçer (veya anında artar, konfigürasyona bağlı).
3.  Mal fiziksel olarak ulaştığında işlem tamamlanır.

---

## 3. Ekran Kullanım Kılavuzu

### 3.1. Stok Kartları Listesi
Sisteme girdiğinizde karşınıza çıkan ana ekrandır. Tüm ürün envanterinizi buradan yönetirsiniz.

**Özellikler:**
*   **Filtreleme:** Üst kısımdaki "Tür" (Hammadde, Mamul vb.) ve "Durum" (Kritik, Normal) kutucukları ile listeyi daraltabilirsiniz.
*   **Arama:** Barkod, stok kodu veya ürün adı ile hızlı arama yapabilirsiniz.
*   **Renkli Gösterim:**
    *   🔴 Kırmızı satırlar: Kritik seviyenin altındaki veya tükenmiş ürünleri gösterir.
    *   🟣 Mor kodlar: Tıklanabilir stok detayını belirtir.
*   **İşlem Menüsü:** Herhangi bir satıra sağ tıklayarak "Düzenle", "Sil" veya "Hareket Geçmişi" seçeneklerine ulaşabilirsiniz.
*   **Dışa Aktar:** Listeyi Excel veya PDF olarak alabilir, ürün etiketleri (barkod) yazdırabilirsiniz.

### 3.2. Stok Kartı Formu (Yeni/Düzenle)
Yeni bir ürün tanımlarken veya mevcut ürünü düzenlerken kullanılan detaylı formdur. 4 ana sekmeden oluşur:

#### A. Genel Bilgiler
Bu sekme ürünün kimlik kartıdır.
*   **Stok Kodu:** Zorunludur. `STK001` gibi benzersiz bir kod. Yanındaki "🔄" butonuna basarsanız sistem otomatik verir.
*   **Barkod:** Ürün üzerindeki barkodu okutun. EAN-13 veya Code-128 destekler.
*   **Tür:** Raporlama için kritiktir. (Örn: Üretimde kullanılacaksa 'Hammadde', satılacaksa 'Mamul' seçin).
*   **Birim:** Ana takip birimi (Adet, Kg, Lt). Değiştirmek zordur, baştan doğru seçilmelidir.

#### B. Stok Ayarları (Limitler)
Otomatik uyarı mekanizmalarını buradan kurarsınız.
*   **Min. Stok:** "Elimde en az 10 tane kalsın" dediğiniz sınır. Altına düşerse liste kırmızı olur.
*   **Maks. Stok:** Depo kapasitesi veya bozulma riski nedeniyle aşılmaması gereken sınır.
*   **Raf Ömrü:** Gıda/İlaç gibi ürünler için gün sayısı (Örn: 90 gün).

#### C. Fiyatlandırma
*   **Alış/Satış Fiyatı:** Varsayılan fiyatlardır. Fatura keserken bu fiyatlar otomatik gelir ama değiştirilebilir.
*   **KDV Oranı:** %1, %10, %20 gibi vergi dilimi.

#### D. Takip & Durum
*   **Lot Takibi:** "Bu ürün partiler halinde gelir ve hangi partiden satış yaptığım önemlidir" diyorsanız işaretleyin.
*   **Seri No Takibi:** "Her ürünün kendine ait bir kimliği (S/N) var" diyorsanız işaretleyin (Telefon, Laptop vb.).

### 3.3. Stok Hareketleri Listesi
Depoya giren ve çıkan her şeyin kaydıdır. Burası değiştirilemez bir defter gibidir.
*   **Giriş Fişi (📥):** Dışarıdan veya üretimden gelen mallar için.
*   **Çıkış Fişi (📤):** Satılan, üretime giden veya bozulan (fire) mallar için.
*   **Transfer (🔄):** Depolar arası yer değişimi.

**Nasıl Hareket Eklerim?**
1.  Üstteki butonlardan işlem türünü seçin (Giriş / Çıkış).
2.  Açılan formda **Depo** seçin.
3.  Ürünleri ekleyin ve miktarları girin.
4. Kaydettiğiniz an stok bakiyesi güncellenir.

### 3.4. Stok Sayım Modülü
Gerçek stok ile sistem stoğunu eşitlemek için kullanılır.

**Sayım Süreci (Workflow):**
1.  **Taslak (🟡):** Yeni bir sayım fişi oluşturulur. Henüz sisteme etkisi yoktur.
2.  **Sayım Girişi:** Depodaki ürünler tek tek sayılır ve sisteme "Sayılan Miktar" olarak girilir.
3.  **Fark Analizi:** Sistem, "Sistemdeki Stok" ile "Sayılan" arasındaki farkı hesaplar ve parasal değerini gösterir.
4.  **Uygula (📥):** Sayım tamamlandığında sağ tıklayıp "Stoklara Uygula" denir. Sistem otomatik olarak aradaki fark kadar "Sayım Fazlası" veya "Sayım Eksiği" fişi keserek stoğu günceller.

### 3.5. Depo Yönetimi Ekranı
Firmanızın fiziksel depo yapılanmasını kurduğunuz yerdir.
*   **Depo Türleri:** Genel, Soğuk Hava Deposu, Antrepo vb. tipler seçilebilir.
*   **Lokasyonlar:** Her depo satırına sağ tıklayıp "Lokasyonlar" diyerek o deponun raf/göz planını yönetebilirsiniz.
*   **Varsayılan Depo:** En çok kullanılan deponuzu "Varsayılan" yaparak fişlerde otomatik gelmesini sağlayabilirsiniz.

---

## 4. Sık Karşılaşılan Hatalar ve Çözümleri

| Hata Mesajı | Olası Sebep | Çözüm |
| :--- | :--- | :--- |
| **Negatif Stok Hatası** | Depoda görünenden daha fazla çıkış yapmaya çalışıyorsunuz. | 1. Fiziksel stoğu sayın.<br>2. Eksik giriş varsa "Giriş Fişi" ile ekleyin.<br>3. Depo ayarlarından "Eksiye Düşmeye İzin Ver"i açabilirsiniz (Önerilmez). |
| **Mükerrer Kayıt (Duplicate Code)** | Bu stok kodu veya barkod başka ürün tarafından kullanılıyor. | Arama kutusuna bu kodu yazıp mevcut ürünü bulun. Aynı ürünü iki kere kaydetmeyin. |
| **Silme Başarısız** | "Hareket görmüş stok kartı silinemez" uyarısı. | Ürün geçmişte bir kez bile işlem gördüyse silinemez (muhasebe tutarlılığı için). Bunun yerine kartı düzenleyip **"Aktif"** kutucuğunu kaldırın (Pasife alın). |
| **Birim Değiştirilemiyor** | Kartta hareket var. | Hareket görmüş kartın birimi değişirse geçmiş hesaplar bozulur. Yeni bir stok kartı açın. |

---

## 5. İpuçları
*   📦 **Düzenli Sayım:** Ayda bir kez "Sayım Modülü"nü kullanarak sistem üzerindeki stokla gerçek stoğu karşılaştırın.
*   🏷️ **Etiketleme:** Ürünleri rafa koymadan önce üzerine sistemden aldığınız barkod etiketini yapıştırmak işleri %50 hızlandırır.
*   📊 **Raporlar:** "Hangi ürün ne kadar süredir hareketsiz?" sorusu için "Stok Yaşlandırma Raporu"nu kullanın.
