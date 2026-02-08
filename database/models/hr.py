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
    manager = relationship(
        "Employee",
        foreign_keys=[manager_id],
        post_update=True,
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
    user = relationship("User", foreign_keys=[user_id])

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


class PayrollStatus(enum.Enum):
    """Bordro durumu"""

    DRAFT = "draft"  # Taslak
    CALCULATED = "calculated"  # Hesaplandı
    APPROVED = "approved"  # Onaylandı
    PAID = "paid"  # Ödendi
    CANCELLED = "cancelled"  # İptal


class Payroll(BaseModel):
    """Maaş Tahakkuk Tablosu - Genişletilmiş"""

    __tablename__ = "payrolls"

    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=False)

    # Brüt ve Net Maaş
    base_salary = Column(Numeric(15, 2), nullable=False)
    gross_salary = Column(Numeric(15, 2), nullable=True)  # Brüt maaş
    net_salary = Column(Numeric(15, 2), nullable=False)

    # SGK Kesintileri
    sgk_employee = Column(Numeric(15, 2), default=0)  # SGK işçi payı (%14)
    sgk_employer = Column(Numeric(15, 2), default=0)  # SGK işveren payı (%20.5)
    unemployment_employee = Column(Numeric(15, 2), default=0)  # İşsizlik işçi (%1)
    unemployment_employer = Column(Numeric(15, 2), default=0)  # İşsizlik işveren (%2)

    # Vergiler
    income_tax = Column(Numeric(15, 2), default=0)  # Gelir vergisi
    stamp_tax = Column(Numeric(15, 2), default=0)  # Damga vergisi (%0.759)
    cumulative_tax_base = Column(Numeric(18, 2), default=0)  # Kümülatif matrah

    # Ek ödemeler
    overtime_pay = Column(Numeric(15, 2), default=0)  # Fazla mesai
    bonus = Column(Numeric(15, 2), default=0)  # Prim/ikramiye
    deductions = Column(Numeric(15, 2), default=0)  # Diğer kesintiler

    # Puantaj verileri
    total_work_days = Column(Integer, default=0)  # Çalışılan gün
    absent_days = Column(Integer, default=0)  # Devamsızlık günü
    late_count = Column(Integer, default=0)  # Geç kalma sayısı
    overtime_hours = Column(Numeric(6, 2), default=0)  # Fazla mesai saat

    # Durum
    status = Column(Enum(PayrollStatus), default=PayrollStatus.DRAFT)

    # Ödeme bilgileri
    is_paid = Column(Boolean, default=False)
    paid_date = Column(Date, nullable=True)

    # Muhasebe entegrasyonu
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)

    # Açıklama
    notes = Column(Text, nullable=True)

    # İlişkiler
    employee = relationship("Employee")
    journal_entry = relationship("JournalEntry", foreign_keys=[journal_entry_id])

    __table_args__ = (
        Index("idx_payroll_period", "period_year", "period_month"),
        Index("idx_payroll_emp", "employee_id"),
        Index("idx_payroll_status", "status"),
        Index(
            "idx_payroll_unique",
            "employee_id",
            "period_year",
            "period_month",
            unique=True,
        ),
    )

    def __repr__(self):
        return f"<Payroll {self.employee_id} {self.period_year}/{self.period_month}>"


class JobPostingStatus(enum.Enum):
    """İş ilanı durumu"""

    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    FILLED = "filled"
    CANCELLED = "cancelled"


class ApplicationStatus(enum.Enum):
    """Başvuru durumu"""

    NEW = "new"
    SCREENING = "screening"
    INTERVIEW = "interview"
    ASSESSMENT = "assessment"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class JobPosting(BaseModel):
    """İş ilanları tablosu"""

    __tablename__ = "job_postings"

    code = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    position = Column(String(100), nullable=False)
    headcount = Column(Integer, default=1)
    status = Column(Enum(JobPostingStatus), default=JobPostingStatus.DRAFT)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    salary_min = Column(Numeric(15, 2), nullable=True)
    salary_max = Column(Numeric(15, 2), nullable=True)
    posted_at = Column(DateTime, nullable=True)
    deadline = Column(Date, nullable=True)
    created_by = Column(Integer, ForeignKey("employees.id"), nullable=True)

    # İlişkiler
    department = relationship("Department")
    applications = relationship("JobApplication", back_populates="posting")
    creator = relationship("Employee", foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_job_code", "code"),
        Index("idx_job_dept", "department_id"),
        Index("idx_job_status", "status"),
    )

    def __repr__(self):
        return f"<JobPosting(code={self.code}, title={self.title})>"


class JobApplication(BaseModel):
    """İş başvuruları tablosu"""

    __tablename__ = "job_applications"

    code = Column(String(20), unique=True, nullable=False, index=True)
    posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.NEW)

    # Aday bilgileri
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    resume_path = Column(String(255), nullable=True)  # DMS referansı
    cover_letter = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)  # kariyer.net, linkedin, vb.

    applied_at = Column(DateTime, default=datetime.now)
    rating = Column(Integer, default=0)  # 1-5 arası
    notes = Column(Text, nullable=True)

    # İlişkileer
    posting = relationship("JobPosting", back_populates="applications")
    interviews = relationship("Interview", back_populates="application")

    __table_args__ = (
        Index("idx_app_code", "code"),
        Index("idx_app_posting", "posting_id"),
        Index("idx_app_status", "status"),
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<JobApplication(code={self.code}, name={self.full_name})>"


class Interview(BaseModel):
    """Mülakatlar tablosu"""

    __tablename__ = "interviews"

    application_id = Column(Integer, ForeignKey("job_applications.id"), nullable=False)
    interviewer_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    duration_min = Column(Integer, default=30)
    interview_type = Column(String(50), nullable=True)  # teknik, İK, video, vb.
    location = Column(String(100), nullable=True)
    status = Column(String(20), default="scheduled")  # scheduled, completed, cancelled
    rating = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)
    result = Column(String(20), nullable=True)  # pass, fail, pending

    # İlişkiler
    application = relationship("JobApplication", back_populates="interviews")
    interviewer = relationship("Employee")

    def __repr__(self):
        return f"<Interview(app_id={self.application_id}, date={self.scheduled_at})>"
