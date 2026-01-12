"""
Akıllı İş - İnsan Kaynakları Modelleri
"""

from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Numeric,
    Enum,
    Index,
)
from sqlalchemy.orm import relationship
import enum

from database.base import Base, BaseModel


class EmploymentType(enum.Enum):
    """İstihdam türü"""

    FULL_TIME = "full_time"  # Tam zamanlı
    PART_TIME = "part_time"  # Yarı zamanlı
    CONTRACT = "contract"  # Sözleşmeli
    INTERN = "intern"  # Stajyer
    TEMPORARY = "temporary"  # Geçici


class Gender(enum.Enum):
    """Cinsiyet"""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class LeaveType(enum.Enum):
    """İzin türü"""

    ANNUAL = "annual"  # Yıllık izin
    SICK = "sick"  # Hastalık izni
    MATERNITY = "maternity"  # Doğum izni
    PATERNITY = "paternity"  # Babalık izni
    MARRIAGE = "marriage"  # Evlilik izni
    BEREAVEMENT = "bereavement"  # Vefat izni
    UNPAID = "unpaid"  # Ücretsiz izin
    OTHER = "other"  # Diğer


class LeaveStatus(enum.Enum):
    """İzin durumu"""

    PENDING = "pending"  # Beklemede
    APPROVED = "approved"  # Onaylandı
    REJECTED = "rejected"  # Reddedildi
    CANCELLED = "cancelled"  # İptal edildi


class AttendanceStatus(enum.Enum):
    """Devam durumu"""

    PRESENT = "present"  # Mevcut
    ABSENT = "absent"  # Yok
    LATE = "late"  # Geç kaldı
    EARLY_LEAVE = "early_leave"  # Erken çıkış
    ON_LEAVE = "on_leave"  # İzinli
    HOLIDAY = "holiday"  # Tatil


class Department(BaseModel):
    """Departmanlar tablosu"""

    __tablename__ = "departments"

    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Hiyerarşi
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    level = Column(Integer, default=0)

    # Yönetici
    manager_id = Column(
        Integer, ForeignKey("employees.id", use_alter=True), nullable=True
    )

    # İlişkiler
    parent = relationship(
        "Department",
        remote_side="Department.id",
        backref="children",
        foreign_keys=[parent_id],
    )
    positions = relationship("Position", back_populates="department")
    employees = relationship(
        "Employee", back_populates="department", foreign_keys="Employee.department_id"
    )

    __table_args__ = (
        Index("idx_dept_code", "code"),
        Index("idx_dept_parent", "parent_id"),
    )

    def __repr__(self):
        return f"<Department(code={self.code}, name={self.name})>"


class Position(BaseModel):
    """Pozisyonlar tablosu"""

    __tablename__ = "positions"

    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Departman ilişkisi
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    # Maaş aralığı
    min_salary = Column(Numeric(15, 2), nullable=True)
    max_salary = Column(Numeric(15, 2), nullable=True)

    # İlişkiler
    department = relationship("Department", back_populates="positions")
    employees = relationship("Employee", back_populates="position")

    __table_args__ = (
        Index("idx_pos_code", "code"),
        Index("idx_pos_dept", "department_id"),
    )

    def __repr__(self):
        return f"<Position(code={self.code}, name={self.name})>"


class Employee(BaseModel):
    """Çalışanlar tablosu"""

    __tablename__ = "employees"

    # Temel bilgiler
    employee_no = Column(String(20), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    # İletişim bilgileri
    email = Column(String(255), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)
    mobile = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)

    # Kişisel bilgiler
    tc_no = Column(String(11), unique=True, nullable=True)  # TC Kimlik No
    birth_date = Column(Date, nullable=True)
    gender = Column(Enum(Gender), nullable=True)
    marital_status = Column(String(20), nullable=True)  # evli, bekar

    # Organizasyon bilgileri
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    shift_team_id = Column(Integer, ForeignKey("shift_teams.id"), nullable=True)

    # İş bilgileri
    hire_date = Column(Date, nullable=False, default=date.today)
    employment_type = Column(Enum(EmploymentType), default=EmploymentType.FULL_TIME)
    salary = Column(Numeric(15, 2), nullable=True)

    # Çıkış bilgileri
    exit_date = Column(Date, nullable=True)
    exit_reason = Column(Text, nullable=True)

    # Sistem kullanıcısı ilişkisi
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Fotoğraf
    photo = Column(String(255), nullable=True)

    # İlişkiler
    department = relationship(
        "Department", back_populates="employees", foreign_keys=[department_id]
    )
    position = relationship("Position", back_populates="employees")
    manager = relationship(
        "Employee",
        remote_side="Employee.id",
        backref="subordinates",
        foreign_keys=[manager_id],
    )
    leaves = relationship(
        "Leave", back_populates="employee", foreign_keys="Leave.employee_id"
    )
    attendances = relationship("Attendance", back_populates="employee")
    shift_team = relationship("ShiftTeam", back_populates="employees")

    __table_args__ = (
        Index("idx_emp_no", "employee_no"),
        Index("idx_emp_name", "first_name", "last_name"),
        Index("idx_emp_dept", "department_id"),
        Index("idx_emp_active", "is_active"),
    )

    @property
    def full_name(self) -> str:
        """Tam isim"""
        return f"{self.first_name} {self.last_name}"

    @property
    def initials(self) -> str:
        """Baş harfler"""
        return f"{self.first_name[0]}{self.last_name[0]}".upper()

    @property
    def is_employed(self) -> bool:
        """Hâlâ çalışıyor mu?"""
        return self.exit_date is None and self.is_active

    def __repr__(self):
        return f"<Employee(employee_no={self.employee_no}, name={self.full_name})>"


class Leave(BaseModel):
    """İzinler tablosu"""

    __tablename__ = "leaves"

    # Çalışan
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # İzin bilgileri
    leave_type = Column(Enum(LeaveType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Numeric(5, 1), nullable=False)  # Yarım gün desteği için

    # Durum
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING)

    # Onay bilgileri
    approved_by = Column(Integer, ForeignKey("employees.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Açıklama
    notes = Column(Text, nullable=True)

    # İlişkiler
    employee = relationship(
        "Employee", back_populates="leaves", foreign_keys=[employee_id]
    )
    approver = relationship("Employee", foreign_keys=[approved_by])

    __table_args__ = (
        Index("idx_leave_emp", "employee_id"),
        Index("idx_leave_dates", "start_date", "end_date"),
        Index("idx_leave_status", "status"),
    )

    def __repr__(self):
        return f"<Leave(employee_id={self.employee_id}, type={self.leave_type.value}, status={self.status.value})>"


class Attendance(BaseModel):
    """Devam/devamsızlık tablosu"""

    __tablename__ = "attendances"

    # Çalışan
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Tarih
    date = Column(Date, nullable=False)

    # Giriş/Çıkış
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)

    # Durum
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.PRESENT)

    # Çalışma saati (dakika)
    work_minutes = Column(Integer, nullable=True)
    overtime_minutes = Column(Integer, default=0)

    # Açıklama
    notes = Column(Text, nullable=True)

    # İlişkiler
    employee = relationship("Employee", back_populates="attendances")

    __table_args__ = (
        Index("idx_att_emp", "employee_id"),
        Index("idx_att_date", "date"),
        Index("idx_att_emp_date", "employee_id", "date", unique=True),
    )

    def __repr__(self):
        return f"<Attendance(employee_id={self.employee_id}, date={self.date}, status={self.status.value})>"
