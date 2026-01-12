import sys
import os

# Proje kök dizinini yola ekle
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from database.base import get_session
from database.models.user import Role, Permission


def update_role_permissions():
    """
    Rollerin izinlerini varsayılan ayarlara göre günceller.
    """
    session = get_session()
    try:
        # İzinleri kategorize et
        all_perms = session.query(Permission).all()
        perms_by_module = {}
        for perm in all_perms:
            module = perm.code.split(".")[0]
            if module not in perms_by_module:
                perms_by_module[module] = []
            perms_by_module[module].append(perm)

        # Rol tanımları ve yetkili oldukları modüller
        role_definitions = {
            "ACCOUNTANT": ["finance", "accounting", "reports"],
            "HR": ["hr"],
            "SALES": ["sales"],
            "PURCHASE": ["purchase"],
            "WAREHOUSE": ["inventory"],
            "PRODUCTION": ["production"],
            "MANAGER": ["*"],  # Tüm modüller (ama admin değil, sadece işlevsel)
            "VIEWER": [],  # Sadece dashboard
        }

        roles = session.query(Role).all()

        print("=== ROL İZİNLERİ GÜNCELLENİYOR ===")

        for role in roles:
            if role.code == "ADMIN":
                continue  # Admin'e dokunma

            required_modules = role_definitions.get(role.code)
            if required_modules is None:
                print(f"⚠️ {role.code} için tanım bulunamadı, geçiliyor.")
                continue

            print(f"\n{role.name} ({role.code}) izinleri güncelleniyor...")

            permissions_to_add = []

            if "*" in required_modules:
                permissions_to_add = all_perms
            else:
                for module in required_modules:
                    if module in perms_by_module:
                        permissions_to_add.extend(perms_by_module[module])
                    # Accounting için ek kontrol (bazı izinler finance altında olabilir)
                    if module == "accounting":
                        if "finance" in perms_by_module:
                            # Sadece view yetkilerini al veya hepsini al? Muhasebeciye finance full verebiliriz.
                            permissions_to_add.extend(perms_by_module["finance"])

            # Dashboard izni herkese verilsin mi? Genelde kod içinde hallediliyor ama
            # veritabanına da ekleyebiliriz eğer permission varsa. Yoksa geç.

            count = 0
            for perm in permissions_to_add:
                if perm not in role.permissions:
                    role.permissions.append(perm)
                    count += 1

            print(f"  ✓ {count} yeni izin eklendi. Toplam: {len(role.permissions)}")

        session.commit()
        print("\n✅ İşlem tamamlandı.")

    except Exception as e:
        session.rollback()
        print(f"❌ HATA: {str(e)}")
    finally:
        session.close()


if __name__ == "__main__":
    update_role_permissions()
