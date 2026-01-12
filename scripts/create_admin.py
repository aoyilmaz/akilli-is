#!/usr/bin/env python3
"""
Akıllı İş ERP - Admin Kullanıcı Oluşturma
Bu script veritabanında admin kullanıcı oluşturur
"""

import sys
from pathlib import Path

# Proje kök dizinini Python path'ine ekle
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from database.base import get_session, init_database
from database.models.user import User, Role, Permission


def create_admin_user():
    """Admin kullanıcı oluştur"""
    session = get_session()

    try:
        # Veritabanını başlat (roller ve izinler oluşsun)
        from database.base import Base, get_engine
        from database.models import user, common, inventory

        Base.metadata.create_all(bind=get_engine())

        # Admin rolünü bul veya oluştur
        admin_role = session.query(Role).filter(Role.code == "ADMIN").first()
        if not admin_role:
            admin_role = Role(
                code="ADMIN",
                name="Sistem Yöneticisi",
                description="Tüm yetkilere sahip",
                level=100,
            )
            session.add(admin_role)
            session.flush()
            print("✓ Admin rolü oluşturuldu")

        # Tüm izinleri admin rolüne ata
        all_permissions = session.query(Permission).all()
        for perm in all_permissions:
            if perm not in admin_role.permissions:
                admin_role.permissions.append(perm)
        print(f"✓ {len(all_permissions)} izin admin rolüne atandı")

        # Admin kullanıcı var mı kontrol et
        admin_user = session.query(User).filter(User.username == "admin").first()

        if admin_user:
            print(f"⚠ Admin kullanıcı zaten mevcut: {admin_user.email}")
            # Şifreyi güncelle
            admin_user.set_password("admin123")
            # Rolü ekle
            if admin_role not in admin_user.roles:
                admin_user.roles.append(admin_role)
            admin_user.is_superuser = True
            admin_user.is_active = True
            session.commit()
            print("✓ Admin kullanıcı güncellendi")
        else:
            # Yeni admin oluştur
            admin_user = User(
                username="admin",
                email="admin@akilli.is",
                first_name="Admin",
                last_name="Kullanıcı",
                is_superuser=True,
                is_active=True,
                is_verified=True,
            )
            admin_user.set_password("admin123")
            admin_user.roles.append(admin_role)
            session.add(admin_user)
            session.commit()
            print("✓ Admin kullanıcı oluşturuldu")

        print("\n" + "=" * 50)
        print("ADMİN GİRİŞ BİLGİLERİ:")
        print("=" * 50)
        print(f"Kullanıcı Adı: admin")
        print(f"Şifre: admin123")
        print(f"E-posta: admin@akilli.is")
        print("=" * 50)

        return True

    except Exception as e:
        session.rollback()
        print(f"✗ Hata: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        session.close()


def add_hr_permissions():
    """HR modülü için izinleri ekle"""
    session = get_session()

    try:
        hr_permissions = [
            {"code": "hr.view", "name": "İK Görüntüleme", "module": "hr"},
            {"code": "hr.create", "name": "İK Kayıt Ekleme", "module": "hr"},
            {"code": "hr.edit", "name": "İK Kayıt Düzenleme", "module": "hr"},
            {"code": "hr.delete", "name": "İK Kayıt Silme", "module": "hr"},
        ]

        for perm_data in hr_permissions:
            exists = (
                session.query(Permission)
                .filter(Permission.code == perm_data["code"])
                .first()
            )
            if not exists:
                session.add(Permission(**perm_data))
                print(f"✓ İzin eklendi: {perm_data['code']}")

        # Accounting izinleri de ekle
        accounting_permissions = [
            {
                "code": "accounting.view",
                "name": "Muhasebe Görüntüleme",
                "module": "accounting",
            },
            {
                "code": "accounting.create",
                "name": "Muhasebe İşlem Ekleme",
                "module": "accounting",
            },
            {
                "code": "accounting.edit",
                "name": "Muhasebe Düzenleme",
                "module": "accounting",
            },
        ]

        for perm_data in accounting_permissions:
            exists = (
                session.query(Permission)
                .filter(Permission.code == perm_data["code"])
                .first()
            )
            if not exists:
                session.add(Permission(**perm_data))
                print(f"✓ İzin eklendi: {perm_data['code']}")

        session.commit()
        print("✓ İzinler başarıyla eklendi")

    except Exception as e:
        session.rollback()
        print(f"✗ İzin ekleme hatası: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Akıllı İş ERP - Admin Kullanıcı Oluşturma")
    print("=" * 50)

    # Önce HR ve Accounting izinlerini ekle
    add_hr_permissions()

    # Sonra admin kullanıcı oluştur
    success = create_admin_user()

    sys.exit(0 if success else 1)
