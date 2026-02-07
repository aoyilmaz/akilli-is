# Akıllı İş ERP

<p align="center">
<img src="ui/resources/icons/logo.svg" width="120" alt="Akıllı İş Logo">
</p>

<p align="center">
<strong> Orta ve Büyük Ölçekli İşletmeler için Modern ERP Ekosistemi </strong>
</p>

<p align="center">
<img src="https://img.shields.io/badge/Python-3.12-blue.svg" alt="Python">
<img src="https://img.shields.io/badge/PyQt6-6.4+-green.svg" alt="PyQt6">
<img src="https://img.shields.io/badge/PostgreSQL-13+-orange.svg" alt="PostgreSQL">
<img src="https://img.shields.io/badge/Architecture-Modular_Bridge-red.svg" alt="Architecture">
</p>

---

## 🚀 Öne Çıkan Kurumsal Özellikler

* ✅ **Bridge Mimarisi:** Modüller arası bağımlılığı azaltan, veriyi temiz bir şekilde transfer eden köprü servisleri (Örn: Bordro-Muhasebe, Kalite-Stok).
* ✅ **Audit Engine (All-Seeing Eye):** Veritabanı seviyesinde her değişikliği (Kim, ne zaman, hangi JSON farkıyla) otomatik loglayan denetim motoru.
* ✅ **E-Dönüşüm Altyapısı:** GİB standartlarında UBL 2.1 formatında E-Fatura XML üretimi.
* ✅ **Lojistik Standartları:** SSCC (Taşıma Birimi) ve Dual-Unit (Çift Birim) desteği ile uçtan uca izlenebilirlik.
* ✅ **Zeki Bildirim Sistemi:** Kritik olaylarda (Düşük stok, onay bekleyen işler) anlık uygulama içi ve badge bildirimleri.

## 📦 Aktif Modüller

### 🏭 Üretim ve Planlama (Production/MRP)

* **MRP II:** Malzeme ihtiyaç planlaması ve satın alma/üretim önerileri.
* **Operatör Paneli:** Saha çalışanları için basitleştirilmiş üretim takip ve duruş girişi ekranı.
* **OEE Raporlama:** Ekipman verimliliği, duruş nedenleri ve verimlilik analizleri.

### 📦 Stok ve Depo Yönetimi (Inventory)

* **Çoklu Lokasyon:** Hiyerarşik depo ve raf bazlı adresleme sistemi.
* **SSCC Takibi:** Palet ve taşıma birimi bazlı lojistik yönetim.
* **Maliyetlendirme:** Ağırlıklı Ortalama Maliyet (Moving Average) ve envanter yaşlandırma raporları.

### 💰 Finans ve Muhasebe (Finance/Accounting)

* **Genel Muhasebe:** Tekdüzen hesap planı ve otomatik yevmiye fişi entegrasyonu.
* **Bütçe Yönetimi:** Dönemsel bütçe planlama, kalem bazlı gerçekleşme takibi ve varyans raporlama.
* **Cari Yönetimi:** Müşteri/Tedarikçi bakiyeleri, yaşlandırma ve mutabakat araçları.
* **Döviz:** TCMB entegrasyonlu canlı döviz kurları ve kur farkı yönetimi.

### 🤝 CRM ve Satış (Sales)

* **Satış Hunisi:** Kanban tabanlı fırsat ve aday müşteri (Lead) yönetimi.
* **Tekliften Faturaya:** Teklif -> Sipariş -> İrsaliye -> Fatura tam zinciri.

### 👥 İnsan Kaynakları (HR)

* **Bordro:** Parametrik bordro hesaplama ve muhasebe tahakkuku.
* **Performans:** 360 derece performans değerlendirme ve yetkinlik takibi.
* **Eğitim:** Personel eğitim planları ve sertifika yönetimi.

### ✅ Kalite ve Bakım (Quality/Maintenance)

* **Kalite Kontrol:** Mal kabul ve üretim aşamalarında muayene, NCR ve CAPA süreçleri.
* **Bakım:** Makine ekipman kartları, periyodik bakım planları ve arıza müdahale takibi.

## 🛠️ Teknik Kurulum

### Gereksinimler

* Python 3.12+
* PostgreSQL 13+
* PyQt6

### Hızlı Başlangıç

```bash
# 1. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 2. Veritabanı şemasını güncelleyin
python -m alembic upgrade head

# 3. Yönetici kullanıcısını oluşturun
python scripts/create_admin.py

# 4. Uygulamayı başlatın
python main.py

```

## 📁 Proje Yapısı

* `core/`: API entegrasyonları, yetkilendirme ve ortak thread yönetimi.
* `database/`: Veri modelleri ve SQLAlchemy `AuditEngine`.
* `modules/`: İş mantığı modülleri (Inventory, Production, Finance, vb.).
* `ui/`: PyQt6 tabanlı modern arayüz bileşenleri ve `LabelDesigner`.

## 🚧 Yol Haritası (Gelecek Planlar)

* [ ] **B2B / Müşteri Portali:** Müşterilerin kendi siparişlerini takip edebileceği web arayüzü.
* [ ] **IoT Gateway:** Makinelerden PLC verilerinin anlık olarak OEE modülüne aktarılması.
* [ ] **Mobil Uygulama (Flutter/React Native):** Depo işlemleri için el terminali desteği.
* [ ] **E-Defter Entegrasyonu:** Resmi muhasebe beratlarının gönderimi.

---

### **Düzenleme Notları:**

1. **Bütçe Yönetimi:** Muhasebe modülüne bütçe planlama ve gerçekleşme raporlama özellikleri eklendi.
2. **Hata Giderildi:** Eski README'deki "Planlanan Modüller" kısmındaki Finance, CRM ve HR modülleri artık aktif oldukları için ana listeye taşındı.
3. **Teknik Detay eklendi:** Python versiyonu 3.12'ye güncellendi.
4. **İzlenebilirlik:** SSCC ve Dual-Unit gibi ileri seviye lojistik özellikler eklendi.
5. **Güvenlik:** `AuditEngine` ve `AuthService` yapıları vurgulandı.