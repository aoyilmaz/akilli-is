# Proje Yönetimi — Kullanıcı El Kitabı

> Bu bölüm, proje ve görev takibini anlatır.

---

## Proje Yönetimi Modülü Ne İşe Yarar?

Belirli bir hedefe ulaşmak için yapılan işleri organize eder. Proje ne zaman başlar, ne zaman biter, kim ne yapacak ve hangi aşamada tamamlanacak — bunların hepsini takip eder.

**Kullanım alanları:**
- Fabrika kurulum projeleri
- Yazılım veya ürün geliştirme
- Müşteri projesi yönetimi
- Herhangi bir çok adımlı iş

---

## Arayüze İlk Bakış

Sol menüde **PROJE YÖNETİMİ** altındaki sayfalar:

| Sayfa | Ne İçin |
|-------|---------|
| Proje Masası | Tüm projelerin özeti ve görev panosu |

---

## Bölüm 1: Projeler

### 1.1 Yeni Proje Oluşturma

1. **Proje Masası** → **Yeni Proje**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Proje Adı | Kısa açıklayıcı ad |
| Açıklama | Projenin amacı |
| Müşteri | İlgili müşteri (varsa) |
| Proje Yöneticisi | Projeyi koordine eden kişi |
| Başlangıç Tarihi | Projenin başlayacağı tarih |
| Bitiş Tarihi | Hedeflenen teslim tarihi |
| Öncelik | Düşük / Normal / Yüksek / Kritik |
| Bütçe | Proje toplam bütçesi (isteğe bağlı) |

3. **Kaydet**

---

### 1.2 Proje Durumları

| Durum | Anlamı |
|-------|--------|
| **Planlama** | Hazırlık aşamasında |
| **Aktif** | Çalışmalar devam ediyor |
| **Askıda** | Geçici olarak durduruldu |
| **Tamamlandı** | Proje bitti |
| **İptal** | İptal edildi |

---

## Bölüm 2: Görevler

### 2.1 Göreve Nedir?

Projeyi oluşturan en küçük iş birimidir. Her görevin bir sorumlusu, başlangıç/bitiş tarihi ve durumu vardır.

---

### 2.2 Yeni Görev Oluşturma

1. Projeyi açın → **Görevler** sekmesi → **Görev Ekle**
2. Doldurun:

| Alan | Açıklama |
|------|---------|
| Görev Adı | Ne yapılacak |
| Açıklama | Detaylı açıklama |
| Atanan Kişi | Görevi yapacak çalışan |
| Başlangıç Tarihi | |
| Son Tarih | Teslim tarihi |
| Öncelik | Düşük / Normal / Yüksek |
| Üst Görev | Alt görev oluşturulacaksa |

3. **Kaydet**

---

### 2.3 Görev Durumları

| Durum | Anlamı |
|-------|--------|
| **Yapılacak** | Henüz başlanmadı |
| **Devam Ediyor** | Üzerinde çalışılıyor |
| **İncelemede** | Onay bekliyor |
| **Tamamlandı** | Bitti |
| **İptal** | Kaldırıldı |

---

### 2.4 Görev Güncellemesi

Atanan kişi:
1. Görevini açar
2. Durum günceller (Yapılacak → Devam Ediyor → Tamamlandı)
3. Yorum ekleyebilir (ne yapıldı, ne engel var)
4. **Kaydet**

---

## Bölüm 3: Proje Masası (Kanban Görünümü)

**Proje Masası** sayfasında tüm görevler sütunlar halinde gösterilir:

```
| Yapılacak | Devam Ediyor | İncelemede | Tamamlandı |
|-----------|--------------|-----------|------------|
| Görev A   | Görev B      | Görev C   | Görev D    |
| Görev E   |              |           |            |
```

Görev kartlarını sürükleyip bırakarak durum değiştirebilirsiniz.

---

## Bölüm 4: Gantt Takvimi

Projeyi açın → **Gantt** sekmesi: görevler zaman çizelgesi üzerinde çubuklar halinde görünür. Geciken görevler kırmızı renge döner.

---

## Bölüm 5: Proje Raporları

**Proje Masası** özet sayfasında:
- Toplam görev sayısı
- Tamamlanan/devam eden/geciken görev sayısı
- Kişi başına iş yükü
- Bütçe kullanımı (bütçe girilmişse)

---

## Bölüm 6: Diğer Modüllerle Bağlantı

| Modül | Bağlantı |
|-------|---------|
| **İK** | Çalışanlara proje görevi atanır |
| **Satış** | Müşteri projesi satış siparişine bağlanabilir |
| **Muhasebe** | Proje harcamaları maliyet merkezine kaydedilebilir |

---

## Hızlı Başlangıç Listesi

- [ ] İlk projeyi oluşturun
- [ ] Projeye görevler ekleyin
- [ ] Görevlere sorumlu atayın
- [ ] Proje masasından ilerlemeyi takip edin

---

*Önceki: [CRM ←](12-crm.md) | Sonraki: [e-Dönüşüm →](14-efatura.md)*
