# Akıllı İş ERP

<p align="center">
  <img src="ui/resources/icons/logo.svg" width="120" alt="Akıllı İş Logo">
</p>

<p align="center">
  <strong>Küçük ve Orta Ölçekli İşletmeler için Modern ERP Sistemi</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PyQt6-6.4+-green.svg" alt="PyQt6">
  <img src="https://img.shields.io/badge/PostgreSQL-13+-orange.svg" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

---

## 🚀 Özellikler

- ✅ **Modern Arayüz** - Dark theme, kullanıcı dostu ve hızlı PyQt6 arayüzü
- ✅ **Modüler Mimari** - Genişletilebilir ve bakımı kolay yapı (Solid prensipleri)
- ✅ **Merkezi Hata Yönetimi** - Veritabanı tabanlı loglama ve UI üzerinden hata takibi
- ✅ **Türkçe** - Tam Türkçe dil desteği
- ✅ **ORM Altyapısı** - SQLAlchemy 2.0+ ile güvenli veritabanı işlemleri

## 📦 Modüller

### 🏭 Üretim Yönetimi (Production)
* **Reçete (BOM) Yönetimi:** Versiyonlama, revizyon takibi, alt reçete desteği.
* **İş Emirleri:** Stok entegrasyonlu iş emri takibi, malzeme rezervasyonu.
* **Planlama:** Makine bazlı Gantt şeması, kapasite doluluk takibi.
* **Takvim & Vardiya:** Vardiya tanımları, tatil günleri ve net çalışma saati hesaplama.

### 🛒 Satınalma (Purchasing)
* **Tedarikçi Yönetimi:** Cari kartlar, iletişim bilgileri.
* **Talep Yönetimi:** Departman bazlı satınalma talepleri ve onay mekanizması.
* **Sipariş Yönetimi:** Tekliften siparişe dönüşüm, parçalı teslimat desteği.
* **Mal Kabul:** İrsaliye ile depoya giriş, kalite kontrol (planlanan).

### 📦 Stok Yönetimi (Inventory)
* **Stok Kartları:** Barkod, birim çevrimleri, kritik stok seviyeleri.
* **Hareketler:** Giriş, Çıkış, Transfer, Fire, Sayım Fazlası/Eksiği.
* **Depo Yönetimi:** Çoklu depo ve lokasyon takibi.
* **Maliyetlendirme:** Ağırlıklı Ortalama Maliyet (Moving Average) yöntemi.

### 🛠 Geliştirme Araçları (Development)
* **Error Handler:** Hataların detaylı traceback ile veritabanına kaydı.
* **Log İzleme:** Hata kayıtlarını filtreleme, inceleme ve çözümleme ekranı.
* **Migration:** Alembic ile veritabanı şema versiyonlama.

### 🚧 Planlanan Modüller
- Satış Yönetimi (Teklif, Sipariş)
- Finans & Muhasebe (Cari Hesap, Fatura, Kasa/Banka)
- İK (Personel Takibi)

## 🛠 Kurulum

### Gereksinimler
- Python 3.9+
- PostgreSQL 13+
- PyQt6

### Adımlar

```bash
# 1. Repoyu klonlayın
git clone [https://github.com/kullanici/akilli-is.git](https://github.com/kullanici/akilli-is.git)
cd akilli-is

# 2. Virtual environment oluşturun
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. Veritabanını oluşturun (PostgreSQL)
createdb akilli_is

# 5. .env dosyasını ayarlayın
cp .env.example .env
# .env dosyasındaki DATABASE_URL'i kendi ayarlarınıza göre güncelleyin

# 6. Tabloları oluşturun ve Migration'ları çalıştırın
# Alembic tabloları güncel hale getirecektir
python -m alembic upgrade head

# (Alternatif) Temel verileri yüklemek için
python init_db.py

# 7. Uygulamayı başlatın
python main.py
