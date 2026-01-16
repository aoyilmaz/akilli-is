import sys
import os

# Proje kök dizinini path'e ekle
sys.path.append(os.getcwd())

from sqlalchemy.orm import Session
from database.base import get_session
from database.models.hr import Department, Position, Employee


def setup_maintenance_org():
    db: Session = get_session()

    print("--- Bakım Organizasyonu Kurulumu Başladı ---")

    # 1. Bakım Departmanını Oluştur/Bul
    dept = db.query(Department).filter(Department.code == "MAINT").first()
    if not dept:
        dept = Department(
            code="MAINT",
            name="Bakım ve Onarım",
            description="Tüm fabrika bakım, onarım ve arıza süreçlerinden sorumlu departman.",
        )
        db.add(dept)
        db.commit()
        db.refresh(dept)
        print("✓ 'Bakım ve Onarım' departmanı oluşturuldu.")
    else:
        print("✓ 'Bakım ve Onarım' departmanı zaten mevcut.")

    # 2. Pozisyonları Oluştur
    positions_data = [
        {
            "code": "MAINT_MGR",
            "name": "Bakım Müdürü",
            "description": "Bakım departmanı yöneticisi",
            "min_salary": 45000,
            "max_salary": 75000,
        },
        {
            "code": "MAINT_CHIEF",
            "name": "Bakım Şefi",
            "description": "Bakım ekibi saha sorumlusu",
            "min_salary": 35000,
            "max_salary": 50000,
        },
        {
            "code": "MAINT_TECH",
            "name": "Bakım Teknisyeni",
            "description": "Bakım ve onarım işlerini yapan teknik personel",
            "min_salary": 25000,
            "max_salary": 40000,
        },
    ]

    for p_data in positions_data:
        pos = db.query(Position).filter(Position.code == p_data["code"]).first()
        if not pos:
            pos = Position(
                code=p_data["code"],
                name=p_data["name"],
                description=p_data["description"],
                min_salary=p_data["min_salary"],
                max_salary=p_data["max_salary"],
                department_id=dept.id,
            )
            db.add(pos)
            print(f"✓ '{p_data['name']}' pozisyonu oluşturuldu.")
        else:
            # Departman ilişkisini güncelle (eğer yoksa)
            if pos.department_id != dept.id:
                pos.department_id = dept.id
                print(f"✓ '{p_data['name']}' pozisyonu departmanı güncellendi.")
            print(f"✓ '{p_data['name']}' pozisyonu zaten mevcut.")

    db.commit()
    print("--- Kurulum Tamamlandı ---")


if __name__ == "__main__":
    setup_maintenance_org()
