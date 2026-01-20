"""
Akıllı İş - İK Dashboard Servisi

İnsan Kaynakları için özet metrikler ve dashboard verileri.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from database.base import get_session
from database.models.hr import (
    Employee,
    Department,
    Leave,
    Attendance,
    AttendanceStatus,
    LeaveStatus,
)


class HRDashboardService:
    """
    İK Dashboard Servisi

    Genel İK metrikleri ve özet veriler sağlar.
    """

    def __init__(self, session: Session = None):
        self.session = session or get_session()

    def get_employee_counts(self) -> Dict:
        """Çalışan sayıları"""
        total = self.session.query(Employee).filter(Employee.is_active == True).count()

        by_department = (
            self.session.query(Department.name, func.count(Employee.id))
            .join(Employee, Employee.department_id == Department.id)
            .filter(Employee.is_active == True)
            .group_by(Department.name)
            .all()
        )

        return {
            "total": total,
            "by_department": {d[0]: d[1] for d in by_department},
        }

    def get_attendance_summary(self, date_val: date = None) -> Dict:
        """Günlük devam özeti"""
        date_val = date_val or date.today()

        attendances = (
            self.session.query(Attendance).filter(Attendance.date == date_val).all()
        )

        total_employees = (
            self.session.query(Employee).filter(Employee.is_active == True).count()
        )

        present = sum(1 for a in attendances if a.status == AttendanceStatus.PRESENT)
        absent = sum(1 for a in attendances if a.status == AttendanceStatus.ABSENT)
        late = sum(1 for a in attendances if a.status == AttendanceStatus.LATE)
        on_leave = sum(1 for a in attendances if a.status == AttendanceStatus.ON_LEAVE)

        return {
            "date": date_val.isoformat(),
            "total_employees": total_employees,
            "present": present,
            "absent": absent,
            "late": late,
            "on_leave": on_leave,
            "attendance_rate": (
                round(present / total_employees * 100, 1) if total_employees > 0 else 0
            ),
        }

    def get_leave_summary(self, year: int = None) -> Dict:
        """İzin özeti"""
        year = year or date.today().year
        start = date(year, 1, 1)
        end = date(year, 12, 31)

        leaves = (
            self.session.query(Leave)
            .filter(
                Leave.start_date >= start,
                Leave.start_date <= end,
            )
            .all()
        )

        total_requests = len(leaves)
        pending = sum(1 for l in leaves if l.status == LeaveStatus.PENDING)
        approved = sum(1 for l in leaves if l.status == LeaveStatus.APPROVED)
        rejected = sum(1 for l in leaves if l.status == LeaveStatus.REJECTED)

        return {
            "year": year,
            "total_requests": total_requests,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
        }

    def get_upcoming_birthdays(self, days: int = 30) -> List[Dict]:
        """Yaklaşan doğum günleri"""
        today = date.today()
        employees = (
            self.session.query(Employee)
            .filter(Employee.is_active == True, Employee.birth_date.isnot(None))
            .all()
        )

        birthdays = []
        for emp in employees:
            if emp.birth_date:
                # Bu yılki doğum günü
                this_year_bd = emp.birth_date.replace(year=today.year)
                if this_year_bd < today:
                    this_year_bd = this_year_bd.replace(year=today.year + 1)

                days_until = (this_year_bd - today).days
                if 0 <= days_until <= days:
                    birthdays.append(
                        {
                            "employee_id": emp.id,
                            "name": f"{emp.first_name} {emp.last_name}",
                            "birth_date": this_year_bd.isoformat(),
                            "days_until": days_until,
                        }
                    )

        return sorted(birthdays, key=lambda x: x["days_until"])

    def get_new_hires(self, days: int = 30) -> List[Dict]:
        """Son işe alınanlar"""
        cutoff = date.today() - timedelta(days=days)

        employees = (
            self.session.query(Employee)
            .filter(Employee.is_active == True, Employee.hire_date >= cutoff)
            .order_by(Employee.hire_date.desc())
            .all()
        )

        return [
            {
                "employee_id": emp.id,
                "name": f"{emp.first_name} {emp.last_name}",
                "hire_date": emp.hire_date.isoformat() if emp.hire_date else None,
                "department": emp.department.name if emp.department else None,
                "position": emp.position.name if emp.position else None,
            }
            for emp in employees
        ]

    def get_tenure_distribution(self) -> Dict:
        """Kıdem dağılımı"""
        today = date.today()
        employees = (
            self.session.query(Employee)
            .filter(Employee.is_active == True, Employee.hire_date.isnot(None))
            .all()
        )

        distribution = {
            "0-1": 0,
            "1-3": 0,
            "3-5": 0,
            "5-10": 0,
            "10+": 0,
        }

        for emp in employees:
            if emp.hire_date:
                years = (today - emp.hire_date).days / 365
                if years < 1:
                    distribution["0-1"] += 1
                elif years < 3:
                    distribution["1-3"] += 1
                elif years < 5:
                    distribution["3-5"] += 1
                elif years < 10:
                    distribution["5-10"] += 1
                else:
                    distribution["10+"] += 1

        return distribution

    def get_dashboard_data(self) -> Dict:
        """Tüm dashboard verileri"""
        return {
            "employee_counts": self.get_employee_counts(),
            "attendance_summary": self.get_attendance_summary(),
            "leave_summary": self.get_leave_summary(),
            "upcoming_birthdays": self.get_upcoming_birthdays(),
            "new_hires": self.get_new_hires(),
            "tenure_distribution": self.get_tenure_distribution(),
        }

    def close(self):
        """Session kapat"""
        if self.session:
            self.session.close()
