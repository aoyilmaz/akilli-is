"""
Akıllı İş - Bordro Hesaplama Servisi

SGK, gelir vergisi ve puantaj verilerini kullanarak bordro hesaplar.
2024/2025 Türkiye vergi mevzuatına uygun.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_

from database.base import get_session
from database.models.hr import (
    Employee,
    Payroll,
    PayrollStatus,
    Attendance,
    AttendanceStatus,
)


@dataclass
class PayrollParameters:
    """
    Bordro Parametreleri - 2024/2025 Türkiye

    Bu değerler SGK ve Maliye tarafından her yıl güncellenir.
    """

    # SGK tavan/taban (2024)
    sgk_ceiling: Decimal = Decimal("150891.00")  # SGK tavan
    sgk_floor: Decimal = Decimal("20002.50")  # Asgari ücret brüt (SGK taban)

    # SGK oranları
    sgk_employee_rate: Decimal = Decimal("0.14")  # %14 işçi
    sgk_employer_rate: Decimal = Decimal("0.2075")  # %20.75 işveren (5510 sk 81/ı)

    # İşsizlik sigortası
    unemployment_employee_rate: Decimal = Decimal("0.01")  # %1 işçi
    unemployment_employer_rate: Decimal = Decimal("0.02")  # %2 işveren

    # Damga vergisi
    stamp_tax_rate: Decimal = Decimal("0.00759")  # %0.759

    # Gelir vergisi dilimleri (2024)
    income_tax_brackets: List[Tuple[Decimal, Decimal]] = None

    # Asgari geçim indirimi (AGİ) - 2024'te kaldırıldı, 0 olarak bırakılır
    agi_rate: Decimal = Decimal("0")

    def __post_init__(self):
        # 2024 Gelir Vergisi Dilimleri
        if self.income_tax_brackets is None:
            self.income_tax_brackets = [
                (Decimal("110000"), Decimal("0.15")),  # 0 - 110.000: %15
                (Decimal("230000"), Decimal("0.20")),  # 110.001 - 230.000: %20
                (Decimal("580000"), Decimal("0.27")),  # 230.001 - 580.000: %27
                (Decimal("3000000"), Decimal("0.35")),  # 580.001 - 3.000.000: %35
                (Decimal("999999999"), Decimal("0.40")),  # 3.000.001+: %40
            ]


class PayrollService:
    """
    Bordro Hesaplama Servisi

    Puantaj verilerinden bordro oluşturur, SGK ve vergi kesintilerini hesaplar.
    """

    def __init__(self, session: Session = None, params: PayrollParameters = None):
        self.session = session or get_session()
        self.params = params or PayrollParameters()

    def calculate_payroll(
        self, employee_id: int, year: int, month: int, force_recalculate: bool = False
    ) -> Payroll:
        """
        Belirli bir çalışan için bordro hesapla

        Args:
            employee_id: Çalışan ID
            year: Yıl
            month: Ay
            force_recalculate: Mevcut hesaplamayı sil ve yeniden hesapla

        Returns:
            Hesaplanmış Payroll kaydı
        """
        # Çalışanı getir
        employee = (
            self.session.query(Employee).filter(Employee.id == employee_id).first()
        )

        if not employee:
            raise ValueError(f"Çalışan bulunamadı: {employee_id}")

        if not employee.salary:
            raise ValueError(f"{employee.full_name} için maaş tanımlanmamış")

        # Mevcut bordro kontrolü
        existing = (
            self.session.query(Payroll)
            .filter(
                Payroll.employee_id == employee_id,
                Payroll.period_year == year,
                Payroll.period_month == month,
            )
            .first()
        )

        if existing:
            if existing.status in [PayrollStatus.APPROVED, PayrollStatus.PAID]:
                raise ValueError("Onaylanmış/ödenmiş bordro yeniden hesaplanamaz")
            if not force_recalculate:
                return existing
            # Yeniden hesapla
            payroll = existing
        else:
            payroll = Payroll(
                employee_id=employee_id, period_year=year, period_month=month
            )

        # Puantaj verilerini al
        attendance_data = self._get_attendance_data(employee_id, year, month)

        # Kümülatif vergi matrahını al (önceki ayların toplamı)
        cumulative_base = self._get_cumulative_tax_base(employee_id, year, month)

        # Hesaplamaları yap
        base_salary = Decimal(str(employee.salary))

        # Gün kesintisi (devamsızlık varsa)
        work_days_in_month = self._get_work_days_in_month(year, month)
        daily_rate = base_salary / Decimal(work_days_in_month)

        absent_deduction = daily_rate * Decimal(attendance_data["absent_days"])
        adjusted_salary = base_salary - absent_deduction

        # Fazla mesai ücreti
        overtime_pay = self._calculate_overtime_pay(
            base_salary, attendance_data["overtime_hours"], work_days_in_month
        )

        # Brüt maaş
        bonus = Decimal(str(payroll.bonus or 0))
        gross_salary = adjusted_salary + overtime_pay + bonus

        # SGK kesintileri (tavan kontrolü ile)
        sgk_base = min(gross_salary, self.params.sgk_ceiling)

        sgk_employee = sgk_base * self.params.sgk_employee_rate
        sgk_employer = sgk_base * self.params.sgk_employer_rate
        unemployment_employee = sgk_base * self.params.unemployment_employee_rate
        unemployment_employer = sgk_base * self.params.unemployment_employer_rate

        # Gelir vergisi matrahı
        tax_base = gross_salary - sgk_employee - unemployment_employee

        # Gelir vergisi (kümülatif dilim hesabı)
        income_tax = self._calculate_income_tax(tax_base, cumulative_base)

        # Damga vergisi
        stamp_tax = gross_salary * self.params.stamp_tax_rate

        # Net maaş
        deductions = Decimal(str(payroll.deductions or 0))
        total_deductions = (
            sgk_employee + unemployment_employee + income_tax + stamp_tax + deductions
        )
        net_salary = gross_salary - total_deductions

        # Payroll'u güncelle
        payroll.base_salary = base_salary
        payroll.gross_salary = gross_salary.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        payroll.net_salary = net_salary.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        payroll.sgk_employee = sgk_employee.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        payroll.sgk_employer = sgk_employer.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        payroll.unemployment_employee = unemployment_employee.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        payroll.unemployment_employer = unemployment_employer.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        payroll.income_tax = income_tax.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        payroll.stamp_tax = stamp_tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        payroll.cumulative_tax_base = (cumulative_base + tax_base).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        payroll.overtime_pay = overtime_pay.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        payroll.total_work_days = attendance_data["present_days"]
        payroll.absent_days = attendance_data["absent_days"]
        payroll.late_count = attendance_data["late_count"]
        payroll.overtime_hours = Decimal(str(attendance_data["overtime_hours"]))

        payroll.status = PayrollStatus.CALCULATED

        if not existing:
            self.session.add(payroll)

        self.session.commit()
        self.session.refresh(payroll)

        return payroll

    def calculate_all_payrolls(
        self, year: int, month: int, department_id: int = None
    ) -> Tuple[int, int, List[str]]:
        """
        Tüm aktif çalışanlar için bordro hesapla

        Returns:
            (başarılı, hatalı, hata_mesajları)
        """
        query = self.session.query(Employee).filter(
            Employee.is_active == True, Employee.exit_date.is_(None)
        )

        if department_id:
            query = query.filter(Employee.department_id == department_id)

        employees = query.all()

        success = 0
        failed = 0
        errors = []

        for emp in employees:
            try:
                self.calculate_payroll(emp.id, year, month)
                success += 1
            except Exception as e:
                failed += 1
                errors.append(f"{emp.full_name}: {str(e)}")

        return success, failed, errors

    def approve_payroll(self, payroll_id: int) -> Payroll:
        """Bordroyu onayla"""
        payroll = self.session.query(Payroll).filter(Payroll.id == payroll_id).first()

        if not payroll:
            raise ValueError("Bordro bulunamadı")

        if payroll.status != PayrollStatus.CALCULATED:
            raise ValueError("Sadece hesaplanmış bordrolar onaylanabilir")

        payroll.status = PayrollStatus.APPROVED
        self.session.commit()

        return payroll

    def mark_as_paid(self, payroll_id: int, paid_date: date = None) -> Payroll:
        """Bordroyu ödendi olarak işaretle"""
        payroll = self.session.query(Payroll).filter(Payroll.id == payroll_id).first()

        if not payroll:
            raise ValueError("Bordro bulunamadı")

        if payroll.status != PayrollStatus.APPROVED:
            raise ValueError("Sadece onaylanmış bordrolar ödenebilir")

        payroll.status = PayrollStatus.PAID
        payroll.is_paid = True
        payroll.paid_date = paid_date or date.today()
        self.session.commit()

        return payroll

    def get_payrolls(
        self,
        year: int,
        month: int,
        department_id: int = None,
        status: PayrollStatus = None,
    ) -> List[Payroll]:
        """Bordro listesini getir"""
        query = self.session.query(Payroll).filter(
            Payroll.period_year == year, Payroll.period_month == month
        )

        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)

        if status:
            query = query.filter(Payroll.status == status)

        return query.all()

    def get_payroll_summary(self, year: int, month: int) -> Dict:
        """Bordro özeti (toplam maliyetler)"""
        payrolls = self.get_payrolls(year, month)

        total_gross = sum(p.gross_salary or 0 for p in payrolls)
        total_net = sum(p.net_salary or 0 for p in payrolls)
        total_sgk_emp = sum(p.sgk_employee or 0 for p in payrolls)
        total_sgk_employer = sum(p.sgk_employer or 0 for p in payrolls)
        total_unemployment_emp = sum(p.unemployment_employee or 0 for p in payrolls)
        total_unemployment_employer = sum(
            p.unemployment_employer or 0 for p in payrolls
        )
        total_income_tax = sum(p.income_tax or 0 for p in payrolls)
        total_stamp_tax = sum(p.stamp_tax or 0 for p in payrolls)

        total_employer_cost = (
            total_gross + total_sgk_employer + total_unemployment_employer
        )

        return {
            "period": f"{month:02d}/{year}",
            "employee_count": len(payrolls),
            "total_gross": total_gross,
            "total_net": total_net,
            "total_sgk_employee": total_sgk_emp,
            "total_sgk_employer": total_sgk_employer,
            "total_unemployment_employee": total_unemployment_emp,
            "total_unemployment_employer": total_unemployment_employer,
            "total_income_tax": total_income_tax,
            "total_stamp_tax": total_stamp_tax,
            "total_employer_cost": total_employer_cost,
        }

    # ========== Yardımcı Metodlar ==========

    def _get_attendance_data(self, employee_id: int, year: int, month: int) -> Dict:
        """Puantaj verilerini getir"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        attendances = (
            self.session.query(Attendance)
            .filter(
                Attendance.employee_id == employee_id,
                Attendance.date >= start_date,
                Attendance.date < end_date,
            )
            .all()
        )

        present = sum(
            1
            for a in attendances
            if a.status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE]
        )
        late = sum(1 for a in attendances if a.status == AttendanceStatus.LATE)
        absent = sum(1 for a in attendances if a.status == AttendanceStatus.ABSENT)
        overtime = sum(a.overtime_minutes or 0 for a in attendances) / 60

        return {
            "present_days": present,
            "late_count": late,
            "absent_days": absent,
            "overtime_hours": overtime,
        }

    def _get_cumulative_tax_base(
        self, employee_id: int, year: int, month: int
    ) -> Decimal:
        """Yıl başından bu aya kadar kümülatif vergi matrahı"""
        prev_payrolls = (
            self.session.query(Payroll)
            .filter(
                Payroll.employee_id == employee_id,
                Payroll.period_year == year,
                Payroll.period_month < month,
                Payroll.status.in_(
                    [
                        PayrollStatus.CALCULATED,
                        PayrollStatus.APPROVED,
                        PayrollStatus.PAID,
                    ]
                ),
            )
            .all()
        )

        if not prev_payrolls:
            return Decimal("0")

        # Son ayın kümülatif matrahını döndür
        last = max(prev_payrolls, key=lambda p: p.period_month)
        return last.cumulative_tax_base or Decimal("0")

    def _get_work_days_in_month(self, year: int, month: int) -> int:
        """Aydaki iş günü sayısı (hafta sonları hariç)"""
        import calendar

        cal = calendar.Calendar()
        work_days = 0
        for day in cal.itermonthdays2(year, month):
            if day[0] != 0 and day[1] < 5:  # Haftaiçi (Pzt-Cuma)
                work_days += 1
        return work_days

    def _calculate_overtime_pay(
        self, base_salary: Decimal, overtime_hours: float, work_days: int
    ) -> Decimal:
        """Fazla mesai ücreti hesapla (%50 zamlı)"""
        if overtime_hours <= 0:
            return Decimal("0")

        # Günlük 7.5 saat varsayımıyla saatlik ücret
        daily_hours = Decimal("7.5")
        hourly_rate = base_salary / (Decimal(work_days) * daily_hours)

        # %50 zamlı fazla mesai
        overtime_rate = hourly_rate * Decimal("1.5")

        return overtime_rate * Decimal(str(overtime_hours))

    def _calculate_income_tax(
        self, tax_base: Decimal, cumulative_base: Decimal
    ) -> Decimal:
        """
        Gelir vergisi hesapla (kümülatif dilim yöntemi)

        Türkiye'de gelir vergisi yıllık bazda kümülatif hesaplanır.
        Her ay, yılbaşından bu aya kadar olan toplam matrah üzerinden
        vergi hesaplanir ve önceki aylarda ödenen vergi düşülür.
        """
        new_cumulative = cumulative_base + tax_base

        # Yeni kümülatif matrah için vergi
        tax_at_new = self._calculate_tax_at_bracket(new_cumulative)

        # Eski kümülatif matrah için vergi
        tax_at_old = self._calculate_tax_at_bracket(cumulative_base)

        # Fark bu ayın vergisi
        return tax_at_new - tax_at_old

    def _calculate_tax_at_bracket(self, amount: Decimal) -> Decimal:
        """Belirli bir tutar için dilimli vergi hesapla"""
        if amount <= 0:
            return Decimal("0")

        tax = Decimal("0")
        remaining = amount
        prev_bracket = Decimal("0")

        for bracket_limit, rate in self.params.income_tax_brackets:
            bracket_size = bracket_limit - prev_bracket

            if remaining <= 0:
                break

            taxable_in_bracket = min(remaining, bracket_size)
            tax += taxable_in_bracket * rate
            remaining -= taxable_in_bracket
            prev_bracket = bracket_limit

        return tax

    def close(self):
        """Session kapat"""
        if self.session:
            self.session.close()
