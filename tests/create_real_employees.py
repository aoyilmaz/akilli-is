"""
Akıllı İş - İK Test Verileri Oluşturma
Orta-Büyük Ölçekli Anonim Şirket Örneği
150 Çalışan + Departmanlar + Pozisyonlar + İzinler + Yoklama
"""

import sys
import os
import random
from datetime import datetime, date, timedelta
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.base import get_session
from sqlalchemy import text
from faker import Faker

fake = Faker("tr_TR")

# ============================================================
# ŞİRKET YAPISI - ORTA-BÜYÜK ÖLÇEKLİ A.Ş.
# ============================================================

# Departmanlar (Hiyerarşik)
DEPARTMENTS = [
    ("YK", "Yönetim Kurulu", "Şirket üst yönetimi", None, 0),
    ("GM", "Genel Müdürlük", "Genel müdürlük ve sekreterya", "YK", 1),
    ("FIN", "Finans ve Muhasebe", "Mali işler ve raporlama", "GM", 1),
    ("IK", "İnsan Kaynakları", "Personel yönetimi ve özlük işleri", "GM", 1),
    ("SAT", "Satış ve Pazarlama", "Yurtiçi ve yurtdışı satış operasyonları", "GM", 1),
    ("URT", "Üretim", "Üretim operasyonları", "GM", 1),
    ("KLT", "Kalite ve Ar-Ge", "Kalite kontrol ve araştırma geliştirme", "GM", 1),
    ("LOJ", "Lojistik", "Depo, sevkiyat ve tedarik zinciri", "GM", 1),
    ("BT", "Bilgi Teknolojileri", "IT altyapısı ve yazılım geliştirme", "GM", 1),
    ("HUK", "Hukuk ve Uyum", "Hukuki danışmanlık ve uyumluluk", "GM", 1),
    ("SAT-IC", "İç Satış", "Yurtiçi satış ekibi", "SAT", 2),
    ("SAT-DIS", "Dış Satış", "İhracat ve yurtdışı satış", "SAT", 2),
    ("SAT-PAZ", "Pazarlama", "Pazarlama ve dijital iletişim", "SAT", 2),
    ("URT-MON", "Montaj", "Montaj hattı operasyonları", "URT", 2),
    ("URT-MAK", "Makine", "Makine atölyesi", "URT", 2),
    ("URT-PLN", "Üretim Planlama", "Üretim planlama ve çizelgeleme", "URT", 2),
    ("LOJ-DEP", "Depo", "Depo yönetimi ve stok", "LOJ", 2),
    ("LOJ-SEV", "Sevkiyat", "Sevkiyat ve nakliye", "LOJ", 2),
]

# Pozisyonlar
POSITIONS = [
    ("CEO", "Genel Müdür", "GM", 180000, 250000),
    ("CFO", "Mali İşler Direktörü", "FIN", 140000, 180000),
    ("COO", "Operasyon Direktörü", "URT", 140000, 180000),
    ("CHRO", "İK Direktörü", "IK", 120000, 160000),
    ("CTO", "Teknoloji Direktörü", "BT", 130000, 170000),
    ("CMO", "Pazarlama Direktörü", "SAT", 120000, 160000),
    ("FIN-MD", "Finans Müdürü", "FIN", 70000, 100000),
    ("MUH-MD", "Muhasebe Müdürü", "FIN", 65000, 90000),
    ("IK-MD", "İK Müdürü", "IK", 60000, 85000),
    ("SAT-MD", "Satış Müdürü", "SAT", 65000, 95000),
    ("PAZ-MD", "Pazarlama Müdürü", "SAT-PAZ", 60000, 85000),
    ("URT-MD", "Üretim Müdürü", "URT", 70000, 100000),
    ("KLT-MD", "Kalite Müdürü", "KLT", 60000, 85000),
    ("ARGE-MD", "Ar-Ge Müdürü", "KLT", 70000, 95000),
    ("LOJ-MD", "Lojistik Müdürü", "LOJ", 55000, 80000),
    ("BT-MD", "IT Müdürü", "BT", 65000, 95000),
    ("HUK-MD", "Hukuk Müdürü", "HUK", 70000, 100000),
    ("URT-SF", "Üretim Şefi", "URT", 40000, 55000),
    ("MON-SF", "Montaj Şefi", "URT-MON", 38000, 52000),
    ("MAK-SF", "Makine Şefi", "URT-MAK", 38000, 52000),
    ("DEP-SF", "Depo Şefi", "LOJ-DEP", 35000, 48000),
    ("SEV-SF", "Sevkiyat Şefi", "LOJ-SEV", 35000, 48000),
    ("FIN-UZ", "Finans Uzmanı", "FIN", 35000, 55000),
    ("MUH-UZ", "Muhasebe Uzmanı", "FIN", 32000, 48000),
    ("IK-UZ", "İK Uzmanı", "IK", 30000, 45000),
    ("ISG-UZ", "İSG Uzmanı", "IK", 32000, 48000),
    ("SAT-UZ", "Satış Uzmanı", "SAT", 30000, 50000),
    ("PAZ-UZ", "Pazarlama Uzmanı", "SAT-PAZ", 28000, 45000),
    ("DIJ-UZ", "Dijital Pazarlama Uzmanı", "SAT-PAZ", 30000, 50000),
    ("KLT-UZ", "Kalite Uzmanı", "KLT", 30000, 48000),
    ("ARGE-UZ", "Ar-Ge Mühendisi", "KLT", 38000, 60000),
    ("BT-UZ", "Sistem Uzmanı", "BT", 35000, 55000),
    ("YZL-UZ", "Yazılım Geliştirici", "BT", 40000, 70000),
    ("HUK-UZ", "Hukuk Danışmanı", "HUK", 40000, 60000),
    ("URT-MH", "Üretim Mühendisi", "URT", 38000, 58000),
    ("END-MH", "Endüstri Mühendisi", "URT-PLN", 40000, 60000),
    ("MAK-MH", "Makine Mühendisi", "URT-MAK", 40000, 62000),
    ("ELK-MH", "Elektrik Mühendisi", "URT", 40000, 62000),
    ("SAT-TM", "Satış Temsilcisi", "SAT-IC", 22000, 38000),
    ("IHR-TM", "İhracat Temsilcisi", "SAT-DIS", 28000, 45000),
    ("DEP-EL", "Depo Elemanı", "LOJ-DEP", 18000, 26000),
    ("SEV-EL", "Sevkiyat Elemanı", "LOJ-SEV", 18000, 26000),
    ("FRK-OP", "Forklift Operatörü", "LOJ-DEP", 20000, 30000),
    ("URT-OP", "Makine Operatörü", "URT-MAK", 20000, 32000),
    ("MON-EL", "Montaj Elemanı", "URT-MON", 18000, 28000),
    ("KLT-KN", "Kalite Kontrolcü", "KLT", 22000, 35000),
    ("AST", "İdari Asistan", "GM", 20000, 32000),
    ("SKR", "Sekreter", "GM", 22000, 35000),
    ("RES", "Resepsiyonist", "GM", 18000, 26000),
    ("TEM", "Temizlik Personeli", "GM", 17000, 22000),
    ("GÜV", "Güvenlik Görevlisi", "GM", 18000, 25000),
]


def slugify(text):
    mapping = {
        "ş": "s",
        "ç": "c",
        "ğ": "g",
        "ü": "u",
        "ö": "o",
        "ı": "i",
        "İ": "i",
        "Ş": "S",
        "Ğ": "G",
        "Ç": "C",
        "Ö": "O",
        "Ü": "U",
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    return text.lower().replace(" ", ".")


def create_hr_seed_data():
    session = get_session()

    print("=" * 60)
    print("🏢 AKILLI İŞ A.Ş. - İK Verileri Oluşturuluyor")
    print("=" * 60)

    try:
        # 1. TABLOLARI SIFIRLA
        print("\n🗑️  Mevcut veriler temizleniyor...")
        session.execute(text("DELETE FROM attendances"))
        session.execute(text("DELETE FROM leaves"))
        session.execute(text("DELETE FROM employees"))
        session.execute(text("DELETE FROM positions"))
        session.execute(text("DELETE FROM departments"))
        session.commit()

        # Level sütunu eksikse ekle
        try:
            session.execute(
                text(
                    "ALTER TABLE departments ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 0"
                )
            )
            session.commit()
        except:
            pass

        # 2. DEPARTMANLAR
        print("\n🏢 Departmanlar oluşturuluyor...")
        dept_map = {}

        for code, name, desc, parent_code, level in DEPARTMENTS:
            parent_id = dept_map.get(parent_code) if parent_code else None
            sql = text(
                """
                INSERT INTO departments (code, name, description, parent_id, level, is_active, created_at, updated_at)
                VALUES (:code, :name, :desc, :parent_id, :level, true, NOW(), NOW())
                RETURNING id
            """
            )
            result = session.execute(
                sql,
                {
                    "code": code,
                    "name": name,
                    "desc": desc,
                    "parent_id": parent_id,
                    "level": level,
                },
            )
            dept_map[code] = result.scalar()

        session.commit()
        print(f"   ✓ {len(DEPARTMENTS)} departman oluşturuldu")

        # 3. POZİSYONLAR
        print("\n📋 Pozisyonlar oluşturuluyor...")
        pos_map = {}

        for code, name, dept_code, min_sal, max_sal in POSITIONS:
            dept_id = dept_map.get(dept_code, dept_map.get("GM"))
            sql = text(
                """
                INSERT INTO positions (code, name, department_id, min_salary, max_salary, is_active, created_at, updated_at)
                VALUES (:code, :name, :dept_id, :min_sal, :max_sal, true, NOW(), NOW())
                RETURNING id
            """
            )
            result = session.execute(
                sql,
                {
                    "code": code,
                    "name": name,
                    "dept_id": dept_id,
                    "min_sal": min_sal,
                    "max_sal": max_sal,
                },
            )
            pos_map[code] = {
                "id": result.scalar(),
                "min": min_sal,
                "max": max_sal,
                "dept_id": dept_id,
            }

        session.commit()
        print(f"   ✓ {len(POSITIONS)} pozisyon oluşturuldu")

        # 4. ÇALIŞANLAR (150 kişi)
        print("\n👥 150 çalışan oluşturuluyor...")

        employee_ids = []
        genders = ["MALE", "FEMALE"]
        marital_statuses = ["Evli", "Bekar"]
        emp_types = ["FULL_TIME", "FULL_TIME", "FULL_TIME", "PART_TIME", "CONTRACT"]

        position_weights = {
            "CEO": 1,
            "CFO": 1,
            "COO": 1,
            "CHRO": 1,
            "CTO": 1,
            "CMO": 1,
            "FIN-MD": 1,
            "MUH-MD": 1,
            "IK-MD": 1,
            "SAT-MD": 2,
            "PAZ-MD": 1,
            "URT-MD": 2,
            "KLT-MD": 1,
            "ARGE-MD": 1,
            "LOJ-MD": 1,
            "BT-MD": 1,
            "HUK-MD": 1,
            "URT-SF": 3,
            "MON-SF": 2,
            "MAK-SF": 2,
            "DEP-SF": 2,
            "SEV-SF": 2,
            "FIN-UZ": 3,
            "MUH-UZ": 4,
            "IK-UZ": 3,
            "ISG-UZ": 2,
            "SAT-UZ": 6,
            "PAZ-UZ": 3,
            "DIJ-UZ": 2,
            "KLT-UZ": 3,
            "ARGE-UZ": 4,
            "BT-UZ": 3,
            "YZL-UZ": 5,
            "HUK-UZ": 2,
            "URT-MH": 4,
            "END-MH": 3,
            "MAK-MH": 3,
            "ELK-MH": 3,
            "SAT-TM": 10,
            "IHR-TM": 5,
            "DEP-EL": 8,
            "SEV-EL": 6,
            "FRK-OP": 4,
            "URT-OP": 15,
            "MON-EL": 12,
            "KLT-KN": 6,
            "AST": 5,
            "SKR": 3,
            "RES": 2,
            "TEM": 4,
            "GÜV": 4,
        }

        weighted_positions = []
        for pos_code, weight in position_weights.items():
            if pos_code in pos_map:
                weighted_positions.extend([pos_code] * weight)

        for i in range(1, 151):
            first_name = fake.first_name()
            last_name = fake.last_name()
            emp_no = f"AIS{str(i).zfill(4)}"
            email = f"{slugify(first_name)}.{slugify(last_name)}{i}@akilliis.com.tr"

            pos_code = random.choice(weighted_positions)
            pos = pos_map[pos_code]
            salary = round(random.uniform(pos["min"], pos["max"]), 2)
            hire_date = fake.date_between(start_date="-15y", end_date="today")
            tc_no = str(random.randint(10000000000, 99999999999))

            sql = text(
                """
                INSERT INTO employees (
                    employee_no, first_name, last_name, email, phone, mobile, address,
                    tc_no, birth_date, gender, marital_status, department_id, position_id,
                    hire_date, employment_type, salary, is_active, created_at, updated_at
                )
                VALUES (
                    :emp_no, :first_name, :last_name, :email, :phone, :mobile, :address,
                    :tc_no, :birth_date, :gender, :marital_status, :dept_id, :pos_id,
                    :hire_date, :emp_type, :salary, true, NOW(), NOW()
                )
                RETURNING id
            """
            )

            result = session.execute(
                sql,
                {
                    "emp_no": emp_no,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": f"0{random.randint(500, 559)}{random.randint(1000000, 9999999)}",
                    "mobile": f"0{random.randint(530, 559)}{random.randint(1000000, 9999999)}",
                    "address": fake.address().replace("\n", ", ")[:200],
                    "tc_no": tc_no,
                    "birth_date": fake.date_of_birth(minimum_age=22, maximum_age=60),
                    "gender": random.choice(genders),
                    "marital_status": random.choice(marital_statuses),
                    "dept_id": pos["dept_id"],
                    "pos_id": pos["id"],
                    "hire_date": hire_date,
                    "emp_type": random.choice(emp_types),
                    "salary": salary,
                },
            )
            employee_ids.append(result.scalar())

        session.commit()
        print(f"   ✓ 150 çalışan oluşturuldu")

        # 5. YÖNETİCİ ATAMALARI
        print("\n👔 Yönetici atamaları yapılıyor...")
        manager_ids = employee_ids[:15]
        for emp_id in employee_ids[15:]:
            manager_id = random.choice(manager_ids)
            session.execute(
                text("UPDATE employees SET manager_id = :mgr WHERE id = :emp"),
                {"mgr": manager_id, "emp": emp_id},
            )
        session.commit()
        print(f"   ✓ Yönetici atamaları tamamlandı")

        # 6. İZİNLER
        print("\n🏖️  İzin kayıtları oluşturuluyor...")
        leave_types = [
            "ANNUAL",
            "ANNUAL",
            "ANNUAL",
            "SICK",
            "SICK",
            "MARRIAGE",
            "BEREAVEMENT",
            "UNPAID",
        ]
        leave_statuses = ["APPROVED", "APPROVED", "APPROVED", "PENDING", "REJECTED"]
        leave_count = 0

        for _ in range(300):
            emp_id = random.choice(employee_ids)
            approver_id = random.choice(manager_ids)
            leave_type = random.choice(leave_types)
            start_date = fake.date_between(start_date="-2y", end_date="+30d")

            if leave_type == "annual":
                days = random.randint(1, 14)
            elif leave_type == "sick":
                days = random.randint(1, 5)
            elif leave_type == "marriage":
                days = 7
            elif leave_type == "bereavement":
                days = random.randint(3, 7)
            else:
                days = random.randint(1, 30)

            end_date = start_date + timedelta(days=days - 1)
            status = random.choice(leave_statuses)
            approval_date = datetime.now() if status == "approved" else None

            sql = text(
                """
                INSERT INTO leaves (
                    employee_id, leave_type, start_date, end_date, days, status,
                    approved_by, approval_date, notes, created_at, updated_at
                )
                VALUES (
                    :emp_id, :leave_type, :start_date, :end_date, :days, :status,
                    :approver, :approval_date, :notes, NOW(), NOW()
                )
            """
            )

            try:
                session.execute(
                    sql,
                    {
                        "emp_id": emp_id,
                        "leave_type": leave_type,
                        "start_date": start_date,
                        "end_date": end_date,
                        "days": days,
                        "status": status,
                        "approver": approver_id if status == "approved" else None,
                        "approval_date": approval_date,
                        "notes": (
                            f"{leave_type.title()} izin talebi"
                            if random.random() > 0.7
                            else None
                        ),
                    },
                )
                leave_count += 1
            except Exception as e:
                print(f"   ! İzin hatası: {e}")

        session.commit()
        print(f"   ✓ {leave_count} izin kaydı oluşturuldu")

        # 7. YOKLAMA
        print("\n📅 Yoklama kayıtları oluşturuluyor...")
        attendance_statuses = [
            "present",
            "present",
            "present",
            "present",
            "late",
            "absent",
            "early_leave",
        ]
        attendance_count = 0

        today = date.today()
        work_days = []
        d = today - timedelta(days=45)
        while d <= today:
            if d.weekday() < 5:
                work_days.append(d)
            d += timedelta(days=1)

        for work_date in work_days[-30:]:
            for emp_id in random.sample(employee_ids, 100):
                status = random.choice(attendance_statuses)

                if status in ["present", "late", "early_leave"]:
                    if status == "present":
                        check_in = datetime.combine(
                            work_date,
                            datetime.strptime(
                                f"08:{random.randint(0, 15):02d}", "%H:%M"
                            ).time(),
                        )
                        check_out = datetime.combine(
                            work_date,
                            datetime.strptime(
                                f"17:{random.randint(30, 59):02d}", "%H:%M"
                            ).time(),
                        )
                    elif status == "late":
                        check_in = datetime.combine(
                            work_date,
                            datetime.strptime(
                                f"09:{random.randint(0, 45):02d}", "%H:%M"
                            ).time(),
                        )
                        check_out = datetime.combine(
                            work_date,
                            datetime.strptime(
                                f"18:{random.randint(0, 30):02d}", "%H:%M"
                            ).time(),
                        )
                    else:
                        check_in = datetime.combine(
                            work_date,
                            datetime.strptime(
                                f"08:{random.randint(0, 10):02d}", "%H:%M"
                            ).time(),
                        )
                        check_out = datetime.combine(
                            work_date,
                            datetime.strptime(
                                f"15:{random.randint(0, 59):02d}", "%H:%M"
                            ).time(),
                        )
                else:
                    check_in = None
                    check_out = None

                sql = text(
                    """
                    INSERT INTO attendances (employee_id, date, check_in, check_out, status, notes, created_at)
                    VALUES (:emp_id, :date, :check_in, :check_out, :status, :notes, NOW())
                """
                )

                try:
                    session.execute(
                        sql,
                        {
                            "emp_id": emp_id,
                            "date": work_date,
                            "check_in": check_in,
                            "check_out": check_out,
                            "status": status,
                            "notes": None,
                        },
                    )
                    attendance_count += 1
                except Exception as e:
                    pass

        session.commit()
        print(f"   ✓ {attendance_count} yoklama kaydı oluşturuldu")

        # ÖZET
        print("\n" + "=" * 60)
        print("✅ İK VERİLERİ BAŞARIYLA OLUŞTURULDU!")
        print("=" * 60)
        print(f"   • Departmanlar: {len(DEPARTMENTS)}")
        print(f"   • Pozisyonlar: {len(POSITIONS)}")
        print(f"   • Çalışanlar: 150")
        print(f"   • İzinler: {leave_count}")
        print(f"   • Yoklama: {attendance_count}")
        print("=" * 60)

    except Exception as e:
        session.rollback()
        print(f"\n❌ HATA: {e}")
        import traceback

        traceback.print_exc()
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    create_hr_seed_data()
