import sys
import os

# Proje kök dizinini yola ekle
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from database.base import get_session
from database.models.user import User, Role, Permission


def check_permissions():
    session = get_session()
    try:
        print("=== ROLLER VE İZİNLER ===")
        roles = session.query(Role).all()
        for role in roles:
            print(f"\nRol: {role.name} ({role.code})")
            perms = role.permissions
            if not perms:
                print("  ⚠️ HİÇ İZNİ YOK!")
            else:
                print(f"  Toplam {len(perms)} izin:")
                accounting_perms = [
                    p.code
                    for p in perms
                    if "accounting" in p.code or "finance" in p.code
                ]
                if accounting_perms:
                    print(
                        f"  - Muhasebe/Finans İzinleri: {', '.join(accounting_perms)}"
                    )
                else:
                    print("  ⚠️ Muhasebe/Finans izni YOK")

        print("\n=== KULLANICILAR ===")
        users = session.query(User).all()
        for user in users:
            print(f"\nKullanıcı: {user.username} (Superuser: {user.is_superuser})")
            for role in user.roles:
                print(f"  - Rol: {role.name} ({role.code})")

    finally:
        session.close()


if __name__ == "__main__":
    check_permissions()
