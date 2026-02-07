# İleri Seviye Stok Modülü Planı

Bu doküman, mevcut stok modülünü büyük ölçekli ERP seviyesine taşımak için eksikleri ve önerilen iyileştirmeleri detaylandırır.

## 1. İzlenebilirlik ve Lot/Seri Yönetimi
- Lot/seri zorunluluğu: `track_lot`, `track_serial` açık ürünlerde hareket ekranları lot/seri olmadan kayıt kabul etmemeli.
- FEFO/FIFO: lot ve expiry üzerinden çıkış önceliklendirme (özellikle gıda/ilaç).
- Karantina / kalite serbest bırakma: `LocationType.QUARANTINE` için ayrı statü ve sadece QC onayıyla serbest bırakma akışı.
- Lot/seri bazlı bakiye: `StockBalance` lot ve seri alanları ile parçalanabilmeli (lot/seri bazlı stok).
- Lot birleştirme/ayırma: barkod/lot birimleme işlemleri için operasyonlar.

## 2. Gelişmiş Depo Yönetimi (WMS)
- Putaway stratejileri: ürün tipi, kategori, çevrim hızı, sıcak/tehlikeli bölge kuralları.
- Picking stratejileri: zone picking, wave picking, batch picking.
- Slotting optimizasyonu: yüksek çıkan ürünleri erişim kolay lokasyonlara taşıma önerileri.
- Lokasyon kapasite kontrolleri: ağırlık, hacim, maksimum ürün adedi bazında kısıt.
- Lokasyon doluluk ve blokaj yönetimi: dolu, geçici bloklu, bakımda.

## 3. Sayım Süreçleri ve İç Kontrol
- Cycle count: belirli periyotlarda otomatik sayım görevleri.
- Blind count: sistemdeki miktarı gizleyerek sayım.
- Variance workflow: sapma tespiti -> onay -> stok düzeltme hareketi.
- Sayım raporları: sapma oranı, kritik sapma ürünleri.

## 4. Costing ve Finansal Derinlik
- FIFO/LIFO/Standard Costing opsiyonları (ürün bazında seçilebilir).
- Cost layer (katman) takibi.
- Revaluation: fiyat değişimlerinde stok yeniden değerleme.
- Kur farkı hesapları ve raporlanması.

## 5. Çoklu Şirket / Çoklu Tesis
- Multi-company destek: şirket bazlı stok kartı ve depo ayrımı.
- Intercompany transfer: şirketler arası transfer ve otomatik muhasebe fişi.
- Multi-plant: tesis bazlı planlama ve stok segmentasyonu.

## 6. KPI ve Analitik
- ABC/XYZ analizi.
- Dead stock raporu.
- Stock turnover (devir hızı).
- Service level (stok bulunurluk oranı).
- Aging raporu (stok yaşlandırma).

## 7. Operasyonel Verimlilik
- Barkod/RF terminal entegrasyonu.
- Mobil depo uygulaması.
- Otomatik replenishment (min/reorder bazlı öneriler).
- Stok tahsis (allocation) ve backorder yönetimi.

## 8. UI/UX İyileştirmeleri
- Hareket ekranında lot/seri zorunluluğu için dinamik alanlar.
- Lokasyon bazlı stok görünümü (depo -> raf -> lot -> seri).
- Dashboard’da stok KPI widget’ları.

## 9. Entegrasyonlar
- Üretim modülü ile otomatik hammadde çıkışı (backflush).
- Satış modülü ile otomatik rezerv ve sevk onayı.
- Satın alma ile giriş onay ve kalite kontrol.

## 10. Güvenlik ve Yetkilendirme
- Hareket tipine göre granular permission.
- Stok düzeltme/sayım işlemlerinde çift onay.
- Kritik ürünlerde ekstra denetim (audit log).

---

### Öncelik Önerisi
1. Lot/Seri + FEFO/FIFO
2. Sayım süreçleri (cycle/blind count)
3. WMS (putaway/picking)
4. Costing seçenekleri
5. Multi-company / KPI & Analitik

---

## Fazlı Yol Haritası ve Ayrıntılı Görev Listesi

### Faz 1 — İzlenebilirlik ve Sayım (Core Stability)
- Lot/seri zorunluluğu: `track_lot/track_serial` açık ürünlerde hareket ekranında validasyon.
- Lot/seri bazlı `StockBalance` parçalama (lot/seri anahtarına göre ayrı satır).
- FEFO/FIFO çıkış önerisi: expiry/lot sırasına göre otomatik öneri.
- Cycle count: periyodik sayım görevleri, planlama ekranı, görev atama.
- Blind count: sistem miktarı gizli sayım modu.
- Variance workflow: sapma tespiti → onay → otomatik düzeltme hareketi.
- Sayım raporu: sapma oranı, kritik sapmalar, sorumlu kullanıcı.

### Faz 2 — WMS Temelleri
- Putaway stratejileri: ürün tipi/kategori/zone bazlı lokasyon önerisi.
- Picking stratejileri: zone picking, batch picking, wave picking.
- Slotting optimizasyonu: yüksek çıkış ürünleri için öneri listeleri.
- Lokasyon kapasite kontrolü: ağırlık/hacim/ürün adedi sınırları.
- Lokasyon doluluk ve blokaj yönetimi: dolu/boş, bakımda, geçici blokaj.
- Mobil/RF ekranları için temel API endpointleri.

### Faz 3 — Costing ve Finans Derinliği
- FIFO/LIFO/Standard Costing seçenekleri (ürün bazında).
- Cost layer takibi ve raporlanması.
- Revaluation: fiyat değişimi sonrası stok yeniden değerleme.
- Kur farkı hesapları (dövizli stoklarda).
- Muhasebe entegrasyonu: otomatik fiş önerisi.

### Faz 4 — Multi-Company / Multi-Plant
- Multi-company veri ayrımı (company_id).
- Intercompany transfer akışı + otomatik muhasebe fişi.
- Multi-plant: depo ve stok kartı segmentasyonu.
- Şirketler arası fiyat/kur politikası yönetimi.

### Faz 5 — KPI ve Analitik
- ABC/XYZ analizi.
- Dead stock raporu ve uyarı sistemi.
- Stock turnover ve service level KPI’ları.
- Aging raporu (stok yaşlandırma).
- Dashboard KPI widget’ları.
