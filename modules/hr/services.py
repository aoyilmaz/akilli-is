"""
Akıllı İş - İnsan Kaynakları Servisleri
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from sqlalchemy import func, and_, desc, or_
from sqlalchemy.orm import Session

from database.base import get_session
from database.models.hr import (
    Department,
    Position,
    Employee,
    Leave,
    Attendance,
    EmploymentType,
    Gender,
    LeaveType,
    LeaveStatus,
    AttendanceStatus,
)


class HRService:
    """İnsan Kaynakları servisi"""

    def __init__(self):
        self.session: Session = get_session()

    # ========== DEPARTMAN İŞLEMLERİ ==========

    def get_all_departments(self, active_only: bool = True) -> List[Department]:
        """Tüm departmanları getir"""
        query = self.session.query(Department)
        if active_only:
            query = query.filter(Department.is_active == True)
        return query.order_by(Department.code).all()

    def get_department_by_id(self, dept_id: int) -> Optional[Department]:
        """ID ile departman getir"""
        return self.session.query(Department).filter(Department.id == dept_id).first()

    def get_department_by_code(self, code: str) -> Optional[Department]:
        """Kod ile departman getir"""
        return self.session.query(Department).filter(Department.code == code).first()

    def create_department(self, data: Dict) -> Department:
        """Yeni departman oluştur"""
        dept = Department(**data)
        self.session.add(dept)
        self.session.commit()
        self.session.refresh(dept)
        return dept

    def update_department(self, dept_id: int, data: Dict) -> Optional[Department]:
        """Departman güncelle"""
        dept = self.get_department_by_id(dept_id)
        if dept:
            for key, value in data.items():
                if hasattr(dept, key):
                    setattr(dept, key, value)
            self.session.commit()
            self.session.refresh(dept)
        return dept

    def delete_department(self, dept_id: int) -> bool:
        """Departman sil (soft delete)"""
        dept = self.get_department_by_id(dept_id)
        if dept:
            # Çalışan kontrolü
            emp_count = (
                self.session.query(Employee)
                .filter(Employee.department_id == dept_id, Employee.is_active == True)
                .count()
            )
            if emp_count > 0:
                raise ValueError(
                    f"Bu departmanda {emp_count} aktif çalışan var. "
                    "Önce çalışanları başka departmana taşıyın."
                )
            dept.is_active = False
            self.session.commit()
            return True
        return False

    # ========== POZİSYON İŞLEMLERİ ==========

    def get_all_positions(self, active_only: bool = True) -> List[Position]:
        """Tüm pozisyonları getir"""
        query = self.session.query(Position)
        if active_only:
            query = query.filter(Position.is_active == True)
        return query.order_by(Position.code).all()

    def get_position_by_id(self, pos_id: int) -> Optional[Position]:
        """ID ile pozisyon getir"""
        return self.session.query(Position).filter(Position.id == pos_id).first()

    def get_positions_by_department(
        self, dept_id: int, active_only: bool = True
    ) -> List[Position]:
        """Departmana göre pozisyonları getir"""
        query = self.session.query(Position).filter(Position.department_id == dept_id)
        if active_only:
            query = query.filter(Position.is_active == True)
        return query.order_by(Position.code).all()

    def create_position(self, data: Dict) -> Position:
        """Yeni pozisyon oluştur"""
        pos = Position(**data)
        self.session.add(pos)
        self.session.commit()
        self.session.refresh(pos)
        return pos

    def update_position(self, pos_id: int, data: Dict) -> Optional[Position]:
        """Pozisyon güncelle"""
        pos = self.get_position_by_id(pos_id)
        if pos:
            for key, value in data.items():
                if hasattr(pos, key):
                    setattr(pos, key, value)
            self.session.commit()
            self.session.refresh(pos)
        return pos

    def delete_position(self, pos_id: int) -> bool:
        """Pozisyon sil (soft delete)"""
        pos = self.get_position_by_id(pos_id)
        if pos:
            emp_count = (
                self.session.query(Employee)
                .filter(Employee.position_id == pos_id, Employee.is_active == True)
                .count()
            )
            if emp_count > 0:
                raise ValueError(f"Bu pozisyonda {emp_count} aktif çalışan var.")
            pos.is_active = False
            self.session.commit()
            return True
        return False

    # ========== ÇALIŞAN İŞLEMLERİ ==========

    def get_all_employees(
        self,
        active_only: bool = True,
        department_id: int = None,
        position_id: int = None,
        search: str = None,
        limit: int = 100,
    ) -> List[Employee]:
        """Çalışanları getir"""
        query = self.session.query(Employee)

        if active_only:
            query = query.filter(
                Employee.is_active == True, Employee.exit_date.is_(None)
            )

        if department_id:
            query = query.filter(Employee.department_id == department_id)

        if position_id:
            query = query.filter(Employee.position_id == position_id)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Employee.employee_no.ilike(search_term),
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.email.ilike(search_term),
                )
            )

        return query.order_by(Employee.employee_no).limit(limit).all()

    def get_employee_by_id(self, emp_id: int) -> Optional[Employee]:
        """ID ile çalışan getir"""
        return self.session.query(Employee).filter(Employee.id == emp_id).first()

    def get_employee_by_no(self, employee_no: str) -> Optional[Employee]:
        """Sicil no ile çalışan getir"""
        return (
            self.session.query(Employee)
            .filter(Employee.employee_no == employee_no)
            .first()
        )

    def generate_employee_no(self) -> str:
        """Otomatik sicil numarası oluştur"""
        year = datetime.now().year
        prefix = f"EMP{year}"

        last = (
            self.session.query(Employee)
            .filter(Employee.employee_no.like(f"{prefix}%"))
            .order_by(desc(Employee.employee_no))
            .first()
        )

        if last:
            num = int(last.employee_no[-4:]) + 1
        else:
            num = 1

        return f"{prefix}{num:04d}"

    def create_employee(self, data: Dict) -> Employee:
        """Yeni çalışan oluştur"""
        if "employee_no" not in data or not data["employee_no"]:
            data["employee_no"] = self.generate_employee_no()

        emp = Employee(**data)
        self.session.add(emp)
        self.session.commit()
        self.session.refresh(emp)
        return emp

    def update_employee(self, emp_id: int, data: Dict) -> Optional[Employee]:
        """Çalışan güncelle"""
        emp = self.get_employee_by_id(emp_id)
        if emp:
            for key, value in data.items():
                if hasattr(emp, key):
                    setattr(emp, key, value)
            self.session.commit()
            self.session.refresh(emp)
        return emp

    def terminate_employee(
        self, emp_id: int, exit_date: date, reason: str = None
    ) -> Optional[Employee]:
        """Çalışan işten çıkar"""
        emp = self.get_employee_by_id(emp_id)
        if emp:
            emp.exit_date = exit_date
            emp.exit_reason = reason
            emp.is_active = False
            self.session.commit()
            self.session.refresh(emp)
        return emp

    def get_employee_count_by_department(self) -> List[Dict]:
        """Departmanlara göre çalışan sayısı"""
        result = (
            self.session.query(Department.name, func.count(Employee.id).label("count"))
            .outerjoin(
                Employee,
                and_(
                    Employee.department_id == Department.id,
                    Employee.is_active == True,
                    Employee.exit_date.is_(None),
                ),
            )
            .filter(Department.is_active == True)
            .group_by(Department.id, Department.name)
            .all()
        )

        return [{"department": r[0], "count": r[1]} for r in result]

    # ========== İZİN İŞLEMLERİ ==========

    def get_leaves(
        self,
        employee_id: int = None,
        status: LeaveStatus = None,
        start_date: date = None,
        end_date: date = None,
        limit: int = 100,
    ) -> List[Leave]:
        """İzinleri getir"""
        query = self.session.query(Leave).filter(Leave.is_active == True)

        if employee_id:
            query = query.filter(Leave.employee_id == employee_id)

        if status:
            query = query.filter(Leave.status == status)

        if start_date:
            query = query.filter(Leave.start_date >= start_date)

        if end_date:
            query = query.filter(Leave.end_date <= end_date)

        return query.order_by(desc(Leave.created_at)).limit(limit).all()

    def get_leave_by_id(self, leave_id: int) -> Optional[Leave]:
        """ID ile izin getir"""
        return self.session.query(Leave).filter(Leave.id == leave_id).first()

    def create_leave(self, data: Dict) -> Leave:
        """İzin talebi oluştur"""
        # Gün hesabı
        if "days" not in data:
            start = data["start_date"]
            end = data["end_date"]
            data["days"] = (end - start).days + 1

        leave = Leave(**data)
        self.session.add(leave)
        self.session.commit()
        self.session.refresh(leave)
        return leave

    def approve_leave(self, leave_id: int, approver_id: int) -> Optional[Leave]:
        """İzni onayla"""
        leave = self.get_leave_by_id(leave_id)
        if leave and leave.status == LeaveStatus.PENDING:
            leave.status = LeaveStatus.APPROVED
            leave.approved_by = approver_id
            leave.approved_at = datetime.now()
            self.session.commit()
            self.session.refresh(leave)
        return leave

    def reject_leave(
        self, leave_id: int, approver_id: int, reason: str = None
    ) -> Optional[Leave]:
        """İzni reddet"""
        leave = self.get_leave_by_id(leave_id)
        if leave and leave.status == LeaveStatus.PENDING:
            leave.status = LeaveStatus.REJECTED
            leave.approved_by = approver_id
            leave.approved_at = datetime.now()
            leave.rejection_reason = reason
            self.session.commit()
            self.session.refresh(leave)
        return leave

    def get_leave_balance(self, employee_id: int, year: int = None) -> Dict:
        """Çalışanın izin bakiyesi"""
        if year is None:
            year = datetime.now().year

        start = date(year, 1, 1)
        end = date(year, 12, 31)

        used = (
            self.session.query(func.sum(Leave.days))
            .filter(
                Leave.employee_id == employee_id,
                Leave.status == LeaveStatus.APPROVED,
                Leave.start_date >= start,
                Leave.end_date <= end,
                Leave.leave_type == LeaveType.ANNUAL,
            )
            .scalar()
            or 0
        )

        # Standart yıllık izin (gerçek uygulamada kıdeme göre hesaplanır)
        annual_quota = Decimal("14")

        return {
            "year": year,
            "quota": annual_quota,
            "used": Decimal(str(used)),
            "remaining": annual_quota - Decimal(str(used)),
        }

    # ========== DEVAM İŞLEMLERİ ==========

    def record_attendance(
        self,
        employee_id: int,
        attendance_date: date,
        check_in: datetime = None,
        check_out: datetime = None,
        status: AttendanceStatus = AttendanceStatus.PRESENT,
    ) -> Attendance:
        """Devam kaydı oluştur/güncelle"""
        existing = (
            self.session.query(Attendance)
            .filter(
                Attendance.employee_id == employee_id,
                Attendance.date == attendance_date,
            )
            .first()
        )

        if existing:
            if check_in:
                existing.check_in = check_in
            if check_out:
                existing.check_out = check_out
                # Çalışma süresini hesapla
                if existing.check_in:
                    diff = check_out - existing.check_in
                    existing.work_minutes = int(diff.total_seconds() / 60)
            existing.status = status
            self.session.commit()
            self.session.refresh(existing)
            return existing
        else:
            att = Attendance(
                employee_id=employee_id,
                date=attendance_date,
                check_in=check_in,
                check_out=check_out,
                status=status,
            )
            if check_in and check_out:
                diff = check_out - check_in
                att.work_minutes = int(diff.total_seconds() / 60)
            self.session.add(att)
            self.session.commit()
            self.session.refresh(att)
            return att

    def get_attendance(
        self,
        employee_id: int = None,
        start_date: date = None,
        end_date: date = None,
        status: AttendanceStatus = None,
    ) -> List[Attendance]:
        """Devam kayıtlarını getir"""
        query = self.session.query(Attendance)

        if employee_id:
            query = query.filter(Attendance.employee_id == employee_id)

        if start_date:
            query = query.filter(Attendance.date >= start_date)

        if end_date:
            query = query.filter(Attendance.date <= end_date)

        if status:
            query = query.filter(Attendance.status == status)

        return query.order_by(desc(Attendance.date)).all()

    def get_monthly_attendance_summary(
        self, employee_id: int, year: int, month: int
    ) -> Dict:
        """Aylık devam özeti"""
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month + 1, 1)

        records = (
            self.session.query(Attendance)
            .filter(
                Attendance.employee_id == employee_id,
                Attendance.date >= start,
                Attendance.date < end,
            )
            .all()
        )

        present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
        late = sum(1 for r in records if r.status == AttendanceStatus.LATE)
        absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
        on_leave = sum(1 for r in records if r.status == AttendanceStatus.ON_LEAVE)
        total_minutes = sum(r.work_minutes or 0 for r in records)

        return {
            "year": year,
            "month": month,
            "present_days": present,
            "late_days": late,
            "absent_days": absent,
            "leave_days": on_leave,
            "total_work_hours": round(total_minutes / 60, 1),
        }

    def close(self):
        """Session kapat"""
        if self.session:
            self.session.close()
