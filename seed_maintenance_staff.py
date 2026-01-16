import sys
import os
import bcrypt

# Proje kök dizinini path'e ekle
sys.path.append(os.getcwd())

from sqlalchemy.orm import Session
from database.base import get_session
from database.models.user import User, Role
from database.models.hr import Department, Position, Employee, EmploymentType, Gender


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode("utf-8")


def seed_maintenance_staff():
    db: Session = get_session()
    print("--- Bakım Personeli Veri Girişi Başladı ---")

    # 1. Gerekli Departman ve Pozisyonları Getir
    dept = db.query(Department).filter(Department.code == "MAINT").first()
    if not dept:
        print(
            "HATA: 'MAINT' departmanı bulunamadı! Lütfen önce setup_maintenance_org.py çalıştırın."
        )
        return

    pos_mgr = db.query(Position).filter(Position.code == "MAINT_MGR").first()
    pos_chief = db.query(Position).filter(Position.code == "MAINT_CHIEF").first()
    pos_tech = db.query(Position).filter(Position.code == "MAINT_TECH").first()

    if not (pos_mgr and pos_chief and pos_tech):
        print(
            "HATA: Pozisyonlar eksik! Lütfen önce setup_maintenance_org.py çalıştırın."
        )
        return

    # 2. Maintenance Rolünü Bul/Oluştur
    role_maint = db.query(Role).filter(Role.code == "MAINTENANCE").first()
    if not role_maint:
        role_maint = Role(
            code="MAINTENANCE",
            name="Bakım Personeli",
            description="Bakım modülü erişimi",
        )
        db.add(role_maint)
        db.commit()

    role_manager = db.query(Role).filter(Role.code == "MANAGER").first()

    # Ortak Şifre
    hashed_pwd = get_password_hash("password123")

    # --- Personel Listesi ---
    staff_data = [
        # Müdür
        {
            "username": "ali.yilmaz",
            "first_name": "Ali",
            "last_name": "Yılmaz",
            "email": "ali.yilmaz@akilli-is.com",
            "position": pos_mgr,
            "roles": [role_maint, role_manager],
            "gender": Gender.MALE,
        },
        # Şefler
        {
            "username": "can.demir",  # Makine Müh.
            "first_name": "Can",
            "last_name": "Demir",
            "email": "can.demir@akilli-is.com",
            "position": pos_chief,
            "roles": [role_maint],
            "gender": Gender.MALE,
            "title_suffix": "(Makine Müh.)",
        },
        {
            "username": "zeynep.kaya",  # Elektrik Müh.
            "first_name": "Zeynep",
            "last_name": "Kaya",
            "email": "zeynep.kaya@akilli-is.com",
            "position": pos_chief,
            "roles": [role_maint],
            "gender": Gender.FEMALE,
            "title_suffix": "(Elk-Elektronik Müh.)",
        },
    ]

    # 10 Teknisyen
    for i in range(1, 11):
        staff_data.append(
            {
                "username": f"teknisyen.{i}",
                "first_name": "Teknisyen",
                "last_name": str(i),
                "email": f"teknisyen.{i}@akilli-is.com",
                "position": pos_tech,
                "roles": [role_maint],
                "gender": Gender.MALE,
            }
        )

    # --- Döngü İle Oluşturma ---
    for data in staff_data:
        # Kullanıcı var mı kontrol et
        user = db.query(User).filter(User.username == data["username"]).first()
        if not user:
            # User Oluştur
            user = User(
                username=data["username"],
                email=data["email"],
                password_hash=hashed_pwd,
                first_name=data["first_name"],
                last_name=data["last_name"],
                is_active=True,
                is_verified=True,
                language="tr",
                theme="dark",
            )
            for r in data["roles"]:
                if r:
                    user.roles.append(r)

            db.add(user)
            db.commit()  # ID almak için commit
            db.refresh(user)

            # Employee Oluştur
            emp = Employee(
                employee_no=f"EMP-{user.id:04d}",
                first_name=data["first_name"],
                last_name=data["last_name"]
                + f" {data.get('title_suffix', '')}".strip(),
                email=data["email"],
                user_id=user.id,
                department_id=dept.id,
                position_id=data["position"].id,
                gender=data["gender"],
                employment_type=EmploymentType.FULL_TIME,
            )
            db.add(emp)
            print(
                f"✓ Kullanıcı ve Çalışan oluşturuldu: {data['first_name']} {data['last_name']}"
            )
        else:
            print(f"✓ Kullanıcı zaten var: {data['username']}")

    db.commit()
    print("--- Veri Girişi Tamamlandı ---")
    print("Not: Tüm kullanıcıların şifresi 'password123' olarak ayarlanmıştır.")


if __name__ == "__main__":
    seed_maintenance_staff()
