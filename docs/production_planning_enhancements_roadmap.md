# Üretim + Planlama Modülü Geliştirme Roadmap (1–2 Sprint)

Bu doküman, mevcut üretim ve planlama modüllerini daha kurumsal seviyeye taşıyacak
ek geliştirmeleri 1–2 sprintlik bir plan halinde özetler.

## Sprint 1 (2–3 hafta) — Hızlı ve Düşük Maliyetli Kazanımlar

### Üretim
- Operasyon bazlı WIP takibi (op status: waiting / in_progress / done)
- Basit OEE KPI’ları (availability, performance, quality)
- Work order gecikme riski flag’i (delay risk göstergesi)

### Planlama
- Plan satırı risk/öncelik renklendirme
- Incoming ve MPS veri doğrulama raporu (sapma kontrolü)
- Backward schedule ekranında özet kapasite görünümü

### UI / Raporlama
- Üretim dashboard KPI widget’ları (lead time, WIP, backlog)
- Planlama özet raporu (toplam yük, darboğaz istasyonlar)

---

## Sprint 2 (2–4 hafta) — Kurumsal Seviye İyileştirmeler

### Üretim
- Rework / tamir akışları (QC reddi → rework → yeniden QC)
- Operasyon bazlı backflush (ops completion ile malzeme düşümü)
- İş istasyonu takvim entegrasyonu (vardiya bazlı kapasite)

### Planlama
- Pegging görünümü (plan satırı → satış siparişi → iş emri ilişkisi)
- What-if simülasyon (teslim/kapasite değişikliği etkisi)
- Gantt / Drag-drop planlama ekranı (temel)

---

## Opsiyonel (3. Sprint / Sonrası)
- Gelişmiş finite scheduling (slot bazlı gerçek takvim)
- MRP entegrasyonu (hammadde ve satın alma önerileri)
- Gerçek zamanlı OEE ekranları

---

## Notlar
- Önce “ölçülebilir KPI” ve görünürlük iyileştirmeleri gelir.
- Ardından “akış düzeltme” (rework, op-based backflush).
- En sonda “optimizasyon” (finite scheduling, MRP).
