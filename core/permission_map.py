"""
Akıllı İş ERP - Permission Map
Sayfa ID'lerini izin kodlarına eşleyen harita
"""

from typing import Optional

# Sayfa ID -> Gerekli izin
# None: Herkese açık
# str: Tek izin gerekli
# list: Herhangi biri yeterli
PAGE_PERMISSIONS = {
    # Dashboard - herkese açık
    "dashboard": None,
    # Stok Yönetimi
    "stock-cards": "inventory.view",
    "categories": "inventory.view",
    "units": "inventory.view",
    "warehouses": "inventory.view",
    "movements": "inventory.movement",
    "stock-count": "inventory.view",
    "stock-reports": ["inventory.view", "reports.view"],
    # Üretim
    "work-orders": "production.view",
    "bom": "production.view",
    "planning": "production.view",
    "work-stations": "production.view",
    "calendar": "production.view",
    "mrp": "production.view",
    # Satın Alma
    "suppliers": "purchase.view",
    "purchase-requests": "purchase.view",
    "purchase-orders": "purchase.view",
    "goods-receipts": "purchase.view",
    "purchase-invoices": "purchase.view",
    # Satış
    "customers": "sales.view",
    "sales-quotes": "sales.view",
    "sales-orders": "sales.view",
    "delivery-notes": "sales.view",
    "invoices": "sales.view",
    "price-lists": "sales.view",
    # Muhasebe
    "accounts": "accounting.view",
    "journals": "accounting.view",
    "accounting-reports": ["accounting.view", "reports.view"],
    # Finans
    "receipts": "finance.view",
    "payments": "finance.view",
    "reconciliation": "finance.view",
    "account-statements": "finance.view",
    # Raporlar
    "sales-reports": "reports.view",
    "stock-aging": "reports.view",
    "production-oee": "reports.view",
    "supplier-performance": "reports.view",
    "receivables-aging": "reports.view",
    # İnsan Kaynakları
    "employees": "hr.view",
    "departments": "hr.view",
    "positions": "hr.view",
    "leaves": "hr.view",
    "org-chart": "hr.view",
    "shift-teams": "hr.view",
    # Geliştirme - sadece adminler
    "error-logs": "system.settings",
    # Kullanıcı Yönetimi
    "users": "system.users",
    # İşlem Geçmişi (Audit Log)
    "audit-logs": "system.audit",
    # Sistem Ayarları
    "settings": "system.settings",
}

# Rol bazlı modül erişimi
# "*" tüm modüllere erişim demek
ROLE_MODULES = {
    "ADMIN": ["*"],
    "MANAGER": ["*"],
    "ACCOUNTANT": ["finance", "accounting", "reports", "dashboard"],
    "WAREHOUSE": ["inventory", "dashboard"],
    "SALES": ["sales", "inventory", "dashboard"],
    "PURCHASE": ["purchasing", "inventory", "dashboard"],
    "PRODUCTION": ["production", "inventory", "dashboard"],
    "HR": ["hr", "dashboard"],
    "VIEWER": ["dashboard"],
}

# Menü ID -> Modül eşlemesi
MENU_TO_MODULE = {
    "dashboard": "dashboard",
    "inventory": "inventory",
    "production": "production",
    "purchasing": "purchasing",
    "sales": "sales",
    "finance": "finance",
    "accounting": "accounting",
    "hr": "hr",
    "reports": "reports",
    "settings": "system",
    "development": "system",
}


# Modül bazlı sayfa tanımları (UI'da gösterilecek)
# Her modül altındaki sayfalar ve Türkçe isimleri
PAGE_DEFINITIONS = {
    "inventory": {
        "name": "Stok Yönetimi",
        "icon": "fa5s.boxes",
        "pages": [
            ("stock-cards", "Stok Kartları"),
            ("categories", "Kategoriler"),
            ("units", "Birimler"),
            ("warehouses", "Depolar"),
            ("movements", "Stok Hareketleri"),
            ("stock-count", "Sayım"),
            ("stock-reports", "Stok Raporları"),
        ],
    },
    "production": {
        "name": "Üretim",
        "icon": "fa5s.industry",
        "pages": [
            ("work-orders", "İş Emirleri"),
            ("bom", "Ürün Ağaçları"),
            ("planning", "Planlama"),
            ("work-stations", "İş İstasyonları"),
            ("calendar", "Üretim Takvimi"),
            ("mrp", "MRP"),
        ],
    },
    "purchasing": {
        "name": "Satın Alma",
        "icon": "fa5s.shopping-cart",
        "pages": [
            ("suppliers", "Tedarikçiler"),
            ("purchase-requests", "Satın Alma Talepleri"),
            ("purchase-orders", "Satın Alma Siparişleri"),
            ("goods-receipts", "Mal Kabul"),
            ("purchase-invoices", "Satın Alma Faturaları"),
        ],
    },
    "sales": {
        "name": "Satış",
        "icon": "fa5s.chart-line",
        "pages": [
            ("customers", "Müşteriler"),
            ("sales-quotes", "Teklifler"),
            ("sales-orders", "Satış Siparişleri"),
            ("delivery-notes", "İrsaliyeler"),
            ("invoices", "Faturalar"),
            ("price-lists", "Fiyat Listeleri"),
        ],
    },
    "finance": {
        "name": "Finans",
        "icon": "fa5s.money-bill-wave",
        "pages": [
            ("receipts", "Tahsilatlar"),
            ("payments", "Ödemeler"),
            ("reconciliation", "Mutabakat"),
            ("account-statements", "Hesap Ekstresi"),
        ],
    },
    "accounting": {
        "name": "Muhasebe",
        "icon": "fa5s.calculator",
        "pages": [
            ("accounts", "Hesap Planı"),
            ("journals", "Yevmiye"),
            ("accounting-reports", "Muhasebe Raporları"),
        ],
    },
    "hr": {
        "name": "İnsan Kaynakları",
        "icon": "fa5s.users",
        "pages": [
            ("employees", "Çalışanlar"),
            ("departments", "Departmanlar"),
            ("positions", "Pozisyonlar"),
            ("leaves", "İzin Yönetimi"),
            ("org-chart", "Organizasyon"),
            ("shift-teams", "Vardiya Ekipleri"),
        ],
    },
    "maintenance": {
        "name": "Bakım",
        "icon": "fa5s.tools",
        "pages": [
            ("equipments", "Ekipmanlar"),
            ("maintenance-requests", "Bakım Talepleri"),
            ("maintenance-work-orders", "Bakım İş Emirleri"),
            ("maintenance-plans", "Bakım Planları"),
            ("maintenance-reports", "Bakım Raporları"),
        ],
    },
    "crm": {
        "name": "CRM",
        "icon": "fa5s.handshake",
        "pages": [
            ("leads", "Potansiyel Müşteriler"),
            ("opportunities", "Fırsatlar"),
            ("activities", "Aktiviteler"),
        ],
    },
    "reports": {
        "name": "Raporlar",
        "icon": "fa5s.chart-bar",
        "pages": [
            ("sales-reports", "Satış Raporları"),
            ("stock-aging", "Stok Yaşlandırma"),
            ("production-oee", "Üretim OEE"),
            ("supplier-performance", "Tedarikçi Performansı"),
            ("receivables-aging", "Alacak Yaşlandırma"),
        ],
    },
    "system": {
        "name": "Sistem",
        "icon": "fa5s.cog",
        "pages": [
            ("users", "Kullanıcı Yönetimi"),
            ("audit-logs", "İşlem Geçmişi"),
            ("settings", "Genel Ayarlar"),
            ("label-templates", "Yazdırma Şablonları"),
            ("error-logs", "Hata Kayıtları"),
        ],
    },
}


def get_menu_permission(menu_id: str) -> Optional[str]:
    """
    Menü ID'si için gerekli modül iznini döndür
    Örn: 'inventory' -> 'inventory.view'
    """
    module = MENU_TO_MODULE.get(menu_id)
    if module is None:
        return None
    if module == "dashboard":
        return None  # Herkese açık
    if module == "system":
        return "system.settings"
    return f"{module}.view"


def get_all_pages() -> list:
    """Tüm sayfa ID'lerini döndürür"""
    pages = []
    for module_data in PAGE_DEFINITIONS.values():
        for page_id, _ in module_data["pages"]:
            pages.append(page_id)
    return pages


def get_page_name(page_id: str) -> Optional[str]:
    """Sayfa ID'sinden Türkçe ismini döndürür"""
    for module_data in PAGE_DEFINITIONS.values():
        for pid, name in module_data["pages"]:
            if pid == page_id:
                return name
    return None
