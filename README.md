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
* **APS (İleri Planlama):** Sonlu kapasite çizelgeleme ve darboğaz analizi.
* **Operatör Paneli:** Saha çalışanları için basitleştirilmiş üretim takip ve duruş girişi ekranı.
* **OEE Raporlama:** Ekipman verimliliği, duruş nedenleri ve verimlilik analizleri.
* **İzlenebilirlik (Traceability):** Lot ve Seri numarası bazlı uçtan uca (Hammadde -> Mamül) soyağacı takibi.

### 📦 Stok ve Depo Yönetimi (Inventory)

* **Çoklu Lokasyon:** Hiyerarşik depo ve raf bazlı adresleme sistemi.
* **SSCC Takibi:** Palet ve taşıma birimi bazlı lojistik yönetim.
* **Maliyetlendirme:** Ağırlıklı Ortalama Maliyet (Moving Average) ve envanter yaşlandırma raporları.
* **Kalite Entegrasyonu:** Mal kabul ve üretim süreçlerinde numune alma, NCR ve karantina yönetimi.
* **SPC (İstatistiksel Proses Kontrol):** X-bar/R grafikleri ile süreç yeterlilik (Cp, Cpk) analizi.

### 💰 Finans ve Muhasebe (Finance/Accounting)

* **Genel Muhasebe:** Tekdüzen hesap planı ve otomatik yevmiye fişi entegrasyonu.
* **Bütçe ve Maliyet:** Dönemsel bütçe planlama, kalem bazlı gerçekleşme ve varyans analizi.
* **Cari Yönetimi:** Müşteri/Tedarikçi bakiyeleri, yaşlandırma raporları.
* **Döviz:** TCMB entegrasyonlu canlı döviz kurları.
* **E-Belge:** E-Fatura, E-Arşiv ve E-İrsaliye oluşturma ve görüntüleme.

### 🤝 Satış ve Tedarik Zinciri (Sales & SCM)

* **CRM:** Satış hunisi, fırsat ve aday müşteri (Lead) yönetimi.
* **Sipariş Yönetimi:** Teklif -> Sipariş -> İrsaliye -> Fatura döngüsü.
* **Sözleşme Yönetimi:** Müşteri ve tedarikçi sözleşmeleri, vade takibi.
* **İade Yönetimi (RMA):** Satış ve satınalma iadeleri, neden analizleri.
* **RFQ (Teklif Talebi):** Tedarikçilerden çoklu teklif toplama ve karşılaştırma matrisi.
* **Tedarikçi Değerlendirme:** Kalite, teslimat ve fiyat performansına göre otomatik puanlama.

### 👥 İnsan Kaynakları ve Proje (HR & Project)

* **Bordro:** Parametrik bordro hesaplama ve muhasebe entegrasyonu.
* **İşe Alım (Recruitment):** İş ilanı, aday havuzu, mülakat takvimi ve işe alım hunisi.
* **Performans Yönetimi:** Dönemsel değerlendirmeler, yetkinlik ve hedef bazlı skorlama.
* **Eğitim:** Personel eğitim planları ve sertifika takibi.
* **Proje Yönetimi:** Kanban panosu, Gantt şeması, kaynak planlama ve efor takibi.

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
* `database/`: Veri modelleri, `AuditEngine` ve Repository katmanı.
* `modules/`: İş mantığı modülleri (Inventory, Production, Finance, HR, vb.).
* `ui/`: PyQt6 tabanlı modern arayüz bileşenleri, `LabelDesigner` ve raporlama araçları.
* `tests/`: Kapsamlı test altyapısı (Unit, Integration, E2E) ve doğrulama scriptleri.

## 🚧 Yol Haritası (Gelecek Planlar)

* [ ] **B2B / Müşteri Portali:** Müşterilerin kendi siparişlerini takip edebileceği web arayüzü.
* [ ] **IoT Gateway:** Makinelerden PLC verilerinin anlık olarak OEE modülüne aktarılması.
* [ ] **Mobil Uygulama (Flutter/React Native):** Depo işlemleri için el terminali desteği.
* [ ] **BI Dashboard:** Yönetim için gelişmiş iş zekası panoları.

---

### **Son Güncelleme (v2.1):**

1. **APS & SPC:** İleri planlama ve istatistiksel kalite kontrol modülleri eklendi.
2. **HR Suite:** İşe alım, performans ve eğitim modülleri ile İK süreçleri tamamlandı.
3. **Proje Yönetimi:** Dahili proje ve görev takip sistemi (Kanban/Gantt) geliştirildi.
4. **SCM Genişlemesi:** Sözleşme, İade, RFQ ve Tedarikçi Değerlendirme özellikleri eklendi.
5. **Test Altyapısı:** Tüm modüller için `tests/scripts` altında doğrulama mekanizmaları kuruldu.