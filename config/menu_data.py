"""
Uygulama menü yapısı ve ikon tanımları.
Tek bir noktadan yönetilebilir menü sistemi.
"""

MENU_DATA = {
    "dashboard": {
        "title": "GENEL BAKIŞ",
        "items": [("Dashboard", "ph.house", "dashboard")],
    },
    "inventory": {
        "title": "STOK YÖNETİMİ",
        "items": [
            ("Stok Kartları", "ph.tag", "stock-cards"),
            ("Kategoriler", "ph.squares-four", "categories"),
            ("Birimler", "ph.ruler", "units"),
            ("Depolar", "ph.buildings", "warehouses"),
            ("Lokasyonlar", "ph.map-pin", "locations"),
            ("Hareketler", "ph.arrows-left-right", "movements"),
            ("Sayım İşlemleri", "ph.list-dashes", "stock-count"),
            ("Taşıma Birimleri (SSCC)", "ph.cube", "sscc-units"),
            ("Depocu Paneli", "ph.user-gear", "warehouse-operator"),
            ("Raporlar", "ph.chart-bar", "stock-reports"),
        ],
    },
    "purchasing": {
        "title": "SATINALMA",
        "items": [
            ("Tedarikçiler", "ph.truck", "suppliers"),
            ("Talepler", "ph.file-text", "purchase-requests"),
            ("Siparişler", "ph.receipt", "purchase-orders"),
            ("Mal Kabul", "ph.package", "goods-receipts"),
            ("Faturalar", "ph.file-text", "purchase-invoices"),
            ("Teklif Talepleri (RFQ)", "ph.chat-circle-dots", "rfq"),
        ],
    },
    "planning": {
        "title": "PLANLAMA",
        "items": [
            ("MPS Kokpit", "ph.chart-bar", "mps-cockpit"),
            ("Üretim Planları", "ph.list-dashes", "plan-list"),
            ("Kapasite Analizi", "ph.gauge", "capacity-analysis"),
            ("MRP", "ph.tree-structure", "mrp"),
            ("Üretim Planlama", "ph.calendar-check", "planning"),
            ("Ürün Reçeteleri", "ph.file-text", "bom"),
            ("İş İstasyonları", "ph.factory", "work-stations"),
            ("Takvim", "ph.calendar-blank", "calendar"),
        ],
    },
    "production": {
        "title": "ÜRETİM (İMALAT)",
        "items": [
            ("İş Emirleri", "ph.clipboard-text", "work-orders"),
            ("Operatör Paneli", "ph.desktop", "operator-panel"),
            ("Canlı OEE İzleme", "ph.monitor", "oee-monitoring"),
        ],
    },
    "quality": {
        "title": "KALİTE KONTROL",
        "items": [
            ("Denetimler", "ph.check-square", "quality-inspections"),
            ("Uygunsuzluklar (NCR)", "ph.warning-octagon", "quality-ncr"),
            ("Müşteri Şikayetleri", "ph.user-focus", "quality-complaints"),
            (
                "Düzeltici Önleyici Faal. (CAPA)",
                "ph.arrows-counter-clockwise",
                "quality-capa",
            ),
            ("Denetim Şablonları", "ph.clipboard-text", "quality-templates"),
            ("SPC (İstatistiksel Kontrol)", "ph.chart-line-up", "quality-spc"),
        ],
    },
    "maintenance": {
        "title": "BAKIM & ONARIM",
        "items": [
            ("Ekipmanlar", "ph.wrench", "equipments"),
            ("Arıza Talepleri", "ph.warning", "maintenance-requests"),
            ("İş Emirleri", "ph.clipboard", "maintenance-work-orders"),
            ("Bakım Planları", "ph.calendar", "maintenance-plans"),
            ("Raporlar", "ph.chart-pie", "maintenance-reports"),
        ],
    },
    "crm": {
        "title": "CRM",
        "items": [
            ("Potansiyel Müşteriler (Leads)", "ph.user-plus", "leads"),
            ("Fırsatlar", "ph.lightbulb", "opportunities"),
            ("Aktiviteler", "ph.list-dashes", "activities"),
            ("Teklifler", "ph.file-text", "sales-quotes"),
            ("Siparişler", "ph.shopping-bag", "sales-orders"),
        ],
    },
    "sales": {
        "title": "SATIŞ YÖNETİMİ",
        "items": [
            ("Müşteriler", "ph.user-circle", "customers"),
            ("Teklifler", "ph.chat-dots", "sales-quotes"),
            ("Siparişler", "ph.shopping-cart", "sales-orders"),
            ("İadeler", "ph.arrow-u-up-left", "sales-returns"),
            ("Sözleşmeler", "ph.file-text", "sales-contracts"),
            ("İrsaliyeler", "ph.truck", "delivery-notes"),
            ("Faturalar", "ph.receipt", "invoices"),
            ("Fiyat Listeleri", "ph.list", "price-lists"),
        ],
    },
    "shipping": {
        "title": "SEVKİYAT",
        "items": [
            ("Sevkiyatlar", "ph.truck", "shipping"),
            ("Araç ve Sürücüler", "ph.car", "fleet-management"),
        ],
    },
    "einvoice": {
        "title": "e-DÖNÜŞÜM",
        "items": [
            ("e-Faturalar", "ph.receipt", "einvoices"),
        ],
    },
    "accounting": {
        "title": "MUHASEBE",
        "items": [
            ("Hesap Planı", "ph.tree-structure", "accounts"),
            ("Yevmiye Fişleri", "ph.book", "journals"),
            ("Muhasebe Raporları", "ph.file", "accounting-reports"),
            ("Sabit Kıymetler", "ph.armchair", "fixed-assets"),
            ("Bütçe Yönetimi", "ph.chart-pie", "budgets"),
        ],
    },
    "finance": {
        "title": "FİNANS",
        "items": [
            ("Tahsilatlar", "ph.money", "receipts"),
            ("Ödemeler", "ph.money", "payments"),
            ("Mutabakat", "ph.scales", "reconciliation"),
            ("Cari Hesaplar", "ph.address-book", "account-statements"),
        ],
    },
    "hr": {
        "title": "İNSAN KAYNAKLARI",
        "items": [
            ("İK Dashboard", "ph.gauge", "hr-dashboard"),
            ("Çalışanlar", "ph.user", "employees"),
            ("Departmanlar", "ph.buildings", "departments"),
            ("Pozisyonlar", "ph.tag", "positions"),
            ("Puantaj", "ph.clock", "attendance"),
            ("İzin Yönetimi", "ph.calendar-x", "leaves"),
            ("Organizasyon", "ph.tree-structure", "org-chart"),
            ("Vardiya Ekipleri", "ph.users-three", "shift-teams"),
            ("Performans", "ph.chart-line", "performance"),
            ("Eğitim", "ph.graduation-cap", "trainings"),
            ("Özlük Dosyası", "ph.folder", "personnel"),
            ("Vardiya Planlama", "ph.calendar", "shift-planning"),
            ("İşe Alım", "ph.user-plus", "hr-recruitment"),
        ],
    },
    "projects": {
        "title": "PROJE YÖNETİMİ",
        "items": [
            ("Proje Masası", "ph.briefcase", "project-management"),
        ],
    },
    "reports": {
        "title": "RAPORLAR",
        "items": [
            ("Satış Raporları", "ph.chart-line", "sales-reports"),
            ("Stok Yaşlandırma", "ph.hourglass", "stock-aging"),
            ("Üretim OEE", "ph.gauge", "production-oee"),
            ("Tedarikçi Performans", "ph.star", "supplier-performance"),
            ("Alacak Yaşlandırma", "ph.credit-card", "receivables-aging"),
        ],
    },
    "settings": {
        "title": "GELİŞTİRME",
        "items": [
            ("Firma Kartı", "ph.buildings", "company-card"),
            ("Kullanıcı Yönetimi", "ph.users-three", "users"),
            ("İş Akışları", "ph.flow-arrow", "workflow-admin"),
            ("Tema Ayarları", "ph.palette", "theme-settings"),
            ("İşlem Geçmişi", "ph.clock-counter-clockwise", "audit-logs"),
            ("Yazdırma Şablonları", "ph.printer", "label-templates"),
            ("Hata Kayıtları", "ph.bug", "error-logs"),
            ("Trace Görüntüle", "ph.activity", "trace-viewer"),
        ],
    },
}
