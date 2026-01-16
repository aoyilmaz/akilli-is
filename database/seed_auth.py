"""
Akıllı İş - Auth Seed Data

Varsayılan roller, izinler ve rol-izin eşleştirmelerini oluşturur.
Admin kullanıcısı da oluşturulur.
"""

from database.base import get_session
from database.models.user import User, Role, Permission


# İzin tanımları (modül bazlı)
PERMISSIONS = [
    # Stok izinleri
    {"code": "inventory.view", "name": "Stok Görüntüleme", "module": "inventory"},
    {"code": "inventory.create", "name": "Stok Ekleme", "module": "inventory"},
    {"code": "inventory.edit", "name": "Stok Düzenleme", "module": "inventory"},
    {"code": "inventory.delete", "name": "Stok Silme", "module": "inventory"},
    {"code": "inventory.movement", "name": "Stok Hareketi", "module": "inventory"},
    # Satış izinleri
    {"code": "sales.view", "name": "Satış Görüntüleme", "module": "sales"},
    {"code": "sales.create", "name": "Satış Oluşturma", "module": "sales"},
    {"code": "sales.edit", "name": "Satış Düzenleme", "module": "sales"},
    {"code": "sales.delete", "name": "Satış Silme", "module": "sales"},
    # Satın alma izinleri
    {"code": "purchase.view", "name": "Satın Alma Görüntüleme", "module": "purchase"},
    {"code": "purchase.create", "name": "Satın Alma Oluşturma", "module": "purchase"},
    {"code": "purchase.edit", "name": "Satın Alma Düzenleme", "module": "purchase"},
    {"code": "purchase.delete", "name": "Satın Alma Silme", "module": "purchase"},
    # Finans izinleri
    {"code": "finance.view", "name": "Finans Görüntüleme", "module": "finance"},
    {"code": "finance.create", "name": "Finans İşlemi", "module": "finance"},
    {"code": "finance.edit", "name": "Finans Düzenleme", "module": "finance"},
    {"code": "finance.delete", "name": "Finans Silme", "module": "finance"},
    # Muhasebe izinleri
    {"code": "accounting.view", "name": "Muhasebe Görüntüleme", "module": "accounting"},
    {"code": "accounting.create", "name": "Muhasebe Kayıt", "module": "accounting"},
    {"code": "accounting.edit", "name": "Muhasebe Düzenleme", "module": "accounting"},
    {"code": "accounting.delete", "name": "Muhasebe Silme", "module": "accounting"},
    # Üretim izinleri
    {"code": "production.view", "name": "Üretim Görüntüleme", "module": "production"},
    {"code": "production.create", "name": "Üretim Oluşturma", "module": "production"},
    {"code": "production.edit", "name": "Üretim Düzenleme", "module": "production"},
    {"code": "production.delete", "name": "Üretim Silme", "module": "production"},
    # İK izinleri
    {"code": "hr.view", "name": "İK Görüntüleme", "module": "hr"},
    {"code": "hr.create", "name": "İK Oluşturma", "module": "hr"},
    {"code": "hr.edit", "name": "İK Düzenleme", "module": "hr"},
    {"code": "hr.delete", "name": "İK Silme", "module": "hr"},
    # CRM izinleri
    {"code": "crm.view", "name": "CRM Görüntüleme", "module": "crm"},
    {"code": "crm.create", "name": "CRM Oluşturma", "module": "crm"},
    {"code": "crm.edit", "name": "CRM Düzenleme", "module": "crm"},
    {"code": "crm.delete", "name": "CRM Silme", "module": "crm"},
    # Bakım izinleri
    {"code": "maintenance.view", "name": "Bakım Görüntüleme", "module": "maintenance"},
    {"code": "maintenance.create", "name": "Bakım Oluşturma", "module": "maintenance"},
    {"code": "maintenance.edit", "name": "Bakım Düzenleme", "module": "maintenance"},
    {"code": "maintenance.delete", "name": "Bakım Silme", "module": "maintenance"},
    # Rapor izinleri
    {"code": "reports.view", "name": "Rapor Görüntüleme", "module": "reports"},
    {"code": "reports.export", "name": "Rapor Dışa Aktarma", "module": "reports"},
    # Sistem izinleri
    {"code": "system.settings", "name": "Sistem Ayarları", "module": "system"},
    {"code": "system.users", "name": "Kullanıcı Yönetimi", "module": "system"},
    {"code": "system.backup", "name": "Yedekleme", "module": "system"},
    {"code": "system.audit", "name": "Denetim Günlüğü", "module": "system"},
]

# Rol tanımları
ROLES = [
    {"code": "ADMIN", "name": "Sistem Yöneticisi", "description": "Tüm yetkilere sahip", "level": 100},
    {"code": "MANAGER", "name": "Yönetici", "description": "Yönetim yetkileri", "level": 90},
    {"code": "HR", "name": "İnsan Kaynakları", "description": "İK yetkileri", "level": 50},
    {"code": "ACCOUNTANT", "name": "Muhasebeci", "description": "Finans ve muhasebe yetkileri", "level": 50},
    {"code": "WAREHOUSE", "name": "Depocu", "description": "Stok yönetimi yetkileri", "level": 30},
    {"code": "SALES", "name": "Satış Temsilcisi", "description": "Satış yetkileri", "level": 30},
    {"code": "PURCHASE", "name": "Satın Alma", "description": "Satın alma yetkileri", "level": 30},
    {"code": "PRODUCTION", "name": "Üretim", "description": "Üretim yetkileri", "level": 30},
    {"code": "MAINTENANCE", "name": "Bakım", "description": "Bakım yetkileri", "level": 30},
    {"code": "VIEWER", "name": "İzleyici", "description": "Sadece görüntüleme yetkisi", "level": 10},
]

# Rol-İzin eşleştirmesi
ROLE_PERMISSIONS = {
    # ADMIN - tüm izinler
    "ADMIN": ["*"],  # Özel işaret: tüm izinler
    # MANAGER - çoğu izin (sistem hariç)
    "MANAGER": [
        "inventory.*", "sales.*", "purchase.*", "finance.*", "accounting.*",
        "production.*", "hr.view", "hr.edit", "crm.*", "maintenance.*",
        "reports.*",
    ],
    # HR
    "HR": ["hr.*", "reports.view"],
    # ACCOUNTANT
    "ACCOUNTANT": ["finance.*", "accounting.*", "reports.*", "sales.view", "purchase.view"],
    # WAREHOUSE
    "WAREHOUSE": ["inventory.*", "production.view"],
    # SALES
    "SALES": ["sales.*", "inventory.view", "crm.*", "reports.view"],
    # PURCHASE
    "PURCHASE": ["purchase.*", "inventory.view", "reports.view"],
    # PRODUCTION
    "PRODUCTION": ["production.*", "inventory.view", "maintenance.view", "reports.view"],
    # MAINTENANCE
    "MAINTENANCE": ["maintenance.*", "inventory.view", "production.view"],
    # VIEWER - sadece görüntüleme
    "VIEWER": [
        "inventory.view", "sales.view", "purchase.view", "finance.view",
        "accounting.view", "production.view", "reports.view",
    ],
}


def expand_permission_pattern(pattern: str, all_permission_codes: list) -> list:
    """
    İzin kalıbını genişletir.

    Örnekler:
        "*" -> tüm izinler
        "inventory.*" -> inventory.view, inventory.create, ...
        "inventory.view" -> inventory.view
    """
    if pattern == "*":
        return all_permission_codes

    if pattern.endswith(".*"):
        module = pattern[:-2]
        return [p for p in all_permission_codes if p.startswith(f"{module}.")]

    return [pattern] if pattern in all_permission_codes else []


def seed_permissions(session) -> dict:
    """İzinleri oluşturur ve döndürür"""
    permission_map = {}

    for perm_data in PERMISSIONS:
        existing = session.query(Permission).filter(Permission.code == perm_data["code"]).first()
        if existing:
            permission_map[perm_data["code"]] = existing
        else:
            perm = Permission(**perm_data)
            session.add(perm)
            session.flush()
            permission_map[perm_data["code"]] = perm
            print(f"  + İzin oluşturuldu: {perm_data['code']}")

    return permission_map


def seed_roles(session, permission_map: dict) -> dict:
    """Rolleri ve izin eşleştirmelerini oluşturur"""
    role_map = {}
    all_permission_codes = list(permission_map.keys())

    for role_data in ROLES:
        existing = session.query(Role).filter(Role.code == role_data["code"]).first()

        if existing:
            role = existing
        else:
            role = Role(**role_data)
            session.add(role)
            session.flush()
            print(f"  + Rol oluşturuldu: {role_data['code']}")

        role_map[role_data["code"]] = role

        # İzinleri eşleştir
        patterns = ROLE_PERMISSIONS.get(role_data["code"], [])
        permission_codes = []

        for pattern in patterns:
            permission_codes.extend(expand_permission_pattern(pattern, all_permission_codes))

        # Mevcut izinleri temizle ve yeniden ata
        role.permissions = []
        for code in set(permission_codes):
            if code in permission_map:
                role.permissions.append(permission_map[code])

        print(f"    → {role_data['code']}: {len(role.permissions)} izin atandı")

    return role_map


def seed_admin_user(session, role_map: dict):
    """Varsayılan admin kullanıcısını oluşturur"""
    admin = session.query(User).filter(User.username == "admin").first()

    if admin:
        print("  ! Admin kullanıcısı zaten mevcut")
        return admin

    admin = User(
        username="admin",
        email="admin@akilli-is.local",
        first_name="Sistem",
        last_name="Yöneticisi",
        is_superuser=True,
        is_verified=True,
    )
    admin.set_password("admin123")  # Varsayılan şifre - değiştirilmeli!

    if "ADMIN" in role_map:
        admin.roles.append(role_map["ADMIN"])

    session.add(admin)
    print("  + Admin kullanıcısı oluşturuldu (admin / admin123)")

    return admin


def run_seed():
    """Seed işlemini çalıştırır"""
    print("\n" + "=" * 60)
    print("Auth Seed Data - Başlatılıyor")
    print("=" * 60)

    session = get_session()

    try:
        # Audit engine'i geçici olarak devre dışı bırak
        from database.audit_engine import audit_engine
        audit_engine.disable()

        print("\n[1/3] İzinler oluşturuluyor...")
        permission_map = seed_permissions(session)
        print(f"      Toplam: {len(permission_map)} izin")

        print("\n[2/3] Roller oluşturuluyor...")
        role_map = seed_roles(session, permission_map)
        print(f"      Toplam: {len(role_map)} rol")

        print("\n[3/3] Admin kullanıcısı oluşturuluyor...")
        seed_admin_user(session, role_map)

        session.commit()

        # Audit engine'i tekrar etkinleştir
        audit_engine.enable()

        print("\n" + "=" * 60)
        print("✓ Auth Seed Data - Tamamlandı")
        print("=" * 60 + "\n")

    except Exception as e:
        session.rollback()
        print(f"\n✗ Hata: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_seed()
