"""
Akıllı İş ERP - Permission Map
Sayfa ID'lerini izin kodlarına eşleyen harita
"""

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


def get_menu_permission(menu_id: str) -> str | None:
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
