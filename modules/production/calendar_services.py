"""
Akıllı İş - Üretim Takvimi Servisleri
"""

from datetime import date, datetime, time, timedelta
from typing import List, Optional, Dict
from sqlalchemy import and_, or_
from database.base import get_session
from database.models.calendar import (
    ProductionShift,
    ProductionHoliday,
    WorkstationSchedule,
)
from database.models.shift_teams import ShiftTeam, RotationPattern, RotationSchedule


class ShiftService:
    """Vardiya servisi"""

    def __init__(self):
        self.session = get_session()

    def get_all(self, active_only: bool = True) -> List[ProductionShift]:
        """Tüm vardiyaları getir"""
        query = self.session.query(ProductionShift)
        if active_only:
            query = query.filter(ProductionShift.is_active == True)
        return query.order_by(ProductionShift.start_time).all()

    def get_by_id(self, shift_id: int) -> Optional[ProductionShift]:
        """ID ile vardiya getir"""
        return (
            self.session.query(ProductionShift)
            .filter(ProductionShift.id == shift_id)
            .first()
        )

    def get_by_code(self, code: str) -> Optional[ProductionShift]:
        """Kod ile vardiya getir"""
        return (
            self.session.query(ProductionShift)
            .filter(ProductionShift.code == code)
            .first()
        )

    def create(
        self,
        code: str,
        name: str,
        start_time: time,
        end_time: time,
        break_minutes: int = 0,
    ) -> ProductionShift:
        """Yeni vardiya oluştur"""
        shift = ProductionShift(
            code=code,
            name=name,
            start_time=start_time,
            end_time=end_time,
            break_minutes=break_minutes,
        )
        self.session.add(shift)
        self.session.commit()
        return shift

    def update(self, shift_id: int, **kwargs) -> Optional[ProductionShift]:
        """Vardiya güncelle"""
        shift = self.get_by_id(shift_id)
        if shift:
            for key, value in kwargs.items():
                if hasattr(shift, key):
                    setattr(shift, key, value)
            self.session.commit()
        return shift

    def delete(self, shift_id: int) -> bool:
        """Vardiya sil"""
        shift = self.get_by_id(shift_id)
        if shift:
            self.session.delete(shift)
            self.session.commit()
            return True
        return False


class HolidayService:
    """Tatil günleri servisi"""

    def __init__(self):
        self.session = get_session()

    def get_all(self, year: int = None) -> List[ProductionHoliday]:
        """Tüm tatilleri getir"""
        query = self.session.query(ProductionHoliday)
        if year:
            query = query.filter(
                ProductionHoliday.date >= date(year, 1, 1),
                ProductionHoliday.date <= date(year, 12, 31),
            )
        return query.order_by(ProductionHoliday.date).all()

    def get_by_id(self, holiday_id: int) -> Optional[ProductionHoliday]:
        """ID ile tatil getir"""
        return (
            self.session.query(ProductionHoliday)
            .filter(ProductionHoliday.id == holiday_id)
            .first()
        )

    def get_by_date(self, check_date: date) -> Optional[ProductionHoliday]:
        """Tarih ile tatil getir"""
        return (
            self.session.query(ProductionHoliday)
            .filter(ProductionHoliday.date == check_date)
            .first()
        )

    def is_holiday(self, check_date: date) -> bool:
        """Belirtilen tarih tatil mi?"""
        return self.get_by_date(check_date) is not None

    def create(
        self,
        holiday_date: date,
        name: str,
        is_half_day: bool = False,
        applies_to_all: bool = True,
    ) -> ProductionHoliday:
        """Yeni tatil ekle"""
        holiday = ProductionHoliday(
            date=holiday_date,
            name=name,
            is_half_day=is_half_day,
            applies_to_all=applies_to_all,
        )
        self.session.add(holiday)
        self.session.commit()
        return holiday

    def update(self, holiday_id: int, **kwargs) -> Optional[ProductionHoliday]:
        """Tatil güncelle"""
        holiday = self.get_by_id(holiday_id)
        if holiday:
            for key, value in kwargs.items():
                if hasattr(holiday, key):
                    setattr(holiday, key, value)
            self.session.commit()
        return holiday

    def delete(self, holiday_id: int) -> bool:
        """Tatil sil"""
        holiday = self.get_by_id(holiday_id)
        if holiday:
            self.session.delete(holiday)
            self.session.commit()
            return True
        return False

    def get_holidays_in_range(
        self, start_date: date, end_date: date
    ) -> List[ProductionHoliday]:
        """Tarih aralığındaki tatilleri getir"""
        return (
            self.session.query(ProductionHoliday)
            .filter(
                ProductionHoliday.date >= start_date, ProductionHoliday.date <= end_date
            )
            .order_by(ProductionHoliday.date)
            .all()
        )


class WorkstationScheduleService:
    """İş istasyonu çalışma takvimi servisi"""

    def __init__(self):
        self.session = get_session()

    def get_by_workstation(self, work_station_id: int) -> List[WorkstationSchedule]:
        """İş istasyonunun takvimini getir"""
        return (
            self.session.query(WorkstationSchedule)
            .filter(WorkstationSchedule.work_station_id == work_station_id)
            .order_by(WorkstationSchedule.day_of_week, WorkstationSchedule.shift_id)
            .all()
        )

    def get_schedule(
        self, work_station_id: int, day_of_week: int
    ) -> List[WorkstationSchedule]:
        """Belirli gün için takvimi getir"""
        return (
            self.session.query(WorkstationSchedule)
            .filter(
                WorkstationSchedule.work_station_id == work_station_id,
                WorkstationSchedule.day_of_week == day_of_week,
                WorkstationSchedule.is_working == True,
            )
            .all()
        )

    def set_schedule(
        self, work_station_id: int, day_of_week: int, shift_ids: List[int]
    ) -> List[WorkstationSchedule]:
        """İş istasyonu için gün takvimini ayarla"""
        # Mevcut kayıtları sil
        self.session.query(WorkstationSchedule).filter(
            WorkstationSchedule.work_station_id == work_station_id,
            WorkstationSchedule.day_of_week == day_of_week,
        ).delete()

        # Yeni kayıtları ekle
        schedules = []
        for shift_id in shift_ids:
            schedule = WorkstationSchedule(
                work_station_id=work_station_id,
                day_of_week=day_of_week,
                shift_id=shift_id,
                is_working=True,
            )
            self.session.add(schedule)
            schedules.append(schedule)

        self.session.commit()
        return schedules

    def set_weekly_schedule(
        self, work_station_id: int, schedule: Dict[int, List[int]]
    ) -> None:
        """
        Haftalık takvim ayarla
        schedule: {0: [1,2,3], 1: [1,2,3], ...}  # gün: [vardiya_id'leri]
        """
        for day_of_week, shift_ids in schedule.items():
            self.set_schedule(work_station_id, day_of_week, shift_ids)

    def copy_schedule(self, from_station_id: int, to_station_id: int) -> None:
        """Bir istasyonun takvimini diğerine kopyala"""
        source_schedules = self.get_by_workstation(from_station_id)

        # Hedef istasyonun mevcut takvimini sil
        self.session.query(WorkstationSchedule).filter(
            WorkstationSchedule.work_station_id == to_station_id
        ).delete()

        # Kopyala
        for s in source_schedules:
            new_schedule = WorkstationSchedule(
                work_station_id=to_station_id,
                day_of_week=s.day_of_week,
                shift_id=s.shift_id,
                is_working=s.is_working,
            )
            self.session.add(new_schedule)

        self.session.commit()


class ProductionCalendarService:
    """Üretim takvimi ana servisi - Kapasite hesaplama"""

    def __init__(self):
        self.session = get_session()
        self.shift_service = ShiftService()
        self.holiday_service = HolidayService()
        self.schedule_service = WorkstationScheduleService()

    def get_working_hours(self, work_station_id: int, target_date: date) -> float:
        """
        Belirli bir tarihte iş istasyonunun çalışma saatini hesapla
        """
        # Tatil kontrolü
        if self.holiday_service.is_holiday(target_date):
            holiday = self.holiday_service.get_by_date(target_date)
            if holiday.applies_to_all:
                return (
                    0
                    if not holiday.is_half_day
                    else self._get_half_day_hours(work_station_id, target_date)
                )

        # Haftanın günü (0=Pazartesi)
        day_of_week = target_date.weekday()

        # O gün için vardiyaları al
        schedules = self.schedule_service.get_schedule(work_station_id, day_of_week)

        if not schedules:
            # Takvim tanımlı değilse varsayılan: Pzt-Cmt 8 saat
            if day_of_week < 6:  # Pazar hariç
                return 8.0
            return 0

        # Toplam çalışma saati
        total_hours = 0
        for schedule in schedules:
            if schedule.shift:
                total_hours += schedule.shift.duration_hours

        return total_hours

    def _get_half_day_hours(self, work_station_id: int, target_date: date) -> float:
        """Yarım gün çalışma saati"""
        return self.get_working_hours(work_station_id, target_date) / 2

    def get_working_minutes(self, work_station_id: int, target_date: date) -> int:
        """Belirli bir tarihte çalışma dakikası"""
        return int(self.get_working_hours(work_station_id, target_date) * 60)

    def calculate_end_date(
        self, work_station_id: int, start_date: datetime, duration_minutes: int
    ) -> datetime:
        """
        Başlangıç tarihi ve süre verildiğinde bitiş tarihini hesapla
        Tatilleri ve çalışma takvimini dikkate alır
        """
        remaining_minutes = duration_minutes
        current_date = start_date.date()

        # Maksimum 365 gün kontrol
        max_days = 365
        days_checked = 0

        while remaining_minutes > 0 and days_checked < max_days:
            daily_minutes = self.get_working_minutes(work_station_id, current_date)

            if daily_minutes > 0:
                if remaining_minutes <= daily_minutes:
                    # Bu gün içinde bitiyor
                    return datetime.combine(
                        current_date, start_date.time()
                    ) + timedelta(minutes=remaining_minutes)
                else:
                    remaining_minutes -= daily_minutes

            current_date += timedelta(days=1)
            days_checked += 1

        return datetime.combine(current_date, start_date.time())

    def get_capacity_in_range(
        self, work_station_id: int, start_date: date, end_date: date
    ) -> Dict:
        """
        Tarih aralığında kapasite özeti
        """
        total_hours = 0
        working_days = 0
        holidays = 0

        current = start_date
        while current <= end_date:
            hours = self.get_working_hours(work_station_id, current)
            if hours > 0:
                total_hours += hours
                working_days += 1
            elif self.holiday_service.is_holiday(current):
                holidays += 1
            current += timedelta(days=1)

        return {
            "total_hours": total_hours,
            "total_minutes": int(total_hours * 60),
            "working_days": working_days,
            "holidays": holidays,
            "calendar_days": (end_date - start_date).days + 1,
        }


class ShiftTeamService:
    """Vardiya ekibi servisi"""

    def __init__(self):
        self.session = get_session()

    def get_all(self, active_only: bool = True) -> List[ShiftTeam]:
        """Tüm ekipleri getir"""
        query = self.session.query(ShiftTeam)
        if active_only:
            query = query.filter(ShiftTeam.is_active == True)
        return query.order_by(ShiftTeam.code).all()

    def get_by_id(self, team_id: int) -> Optional[ShiftTeam]:
        """ID ile ekip getir"""
        return self.session.query(ShiftTeam).filter(ShiftTeam.id == team_id).first()

    def get_by_code(self, code: str) -> Optional[ShiftTeam]:
        """Kod ile ekip getir"""
        return self.session.query(ShiftTeam).filter(ShiftTeam.code == code).first()

    def create(
        self, code: str, name: str, color: str = "#6366f1", description: str = None
    ) -> ShiftTeam:
        """Yeni ekip oluştur"""
        team = ShiftTeam(code=code, name=name, color=color, description=description)
        self.session.add(team)
        self.session.commit()
        return team

    def update(self, team_id: int, **kwargs) -> Optional[ShiftTeam]:
        """Ekip güncelle"""
        team = self.get_by_id(team_id)
        if team:
            for key, value in kwargs.items():
                if hasattr(team, key):
                    setattr(team, key, value)
            self.session.commit()
        return team

    def delete(self, team_id: int) -> bool:
        """Ekip sil"""
        team = self.get_by_id(team_id)
        if team:
            self.session.delete(team)
            self.session.commit()
            return True
        return False


class RotationPatternService:
    """Rotasyon şablonu servisi"""

    def __init__(self):
        self.session = get_session()
        self.shift_service = ShiftService()

    def get_all(self, active_only: bool = True) -> List[RotationPattern]:
        """Tüm şablonları getir"""
        query = self.session.query(RotationPattern)
        if active_only:
            query = query.filter(RotationPattern.is_active == True)
        return query.order_by(RotationPattern.code).all()

    def get_by_id(self, pattern_id: int) -> Optional[RotationPattern]:
        """ID ile şablon getir"""
        return (
            self.session.query(RotationPattern)
            .filter(RotationPattern.id == pattern_id)
            .first()
        )

    def get_by_code(self, code: str) -> Optional[RotationPattern]:
        """Kod ile şablon getir"""
        return (
            self.session.query(RotationPattern)
            .filter(RotationPattern.code == code)
            .first()
        )

    def create(
        self,
        code: str,
        name: str,
        cycle_days: int = 6,
        shifts_per_day: int = 2,
        description: str = None,
    ) -> RotationPattern:
        """Yeni şablon oluştur"""
        pattern = RotationPattern(
            code=code,
            name=name,
            cycle_days=cycle_days,
            shifts_per_day=shifts_per_day,
            description=description,
        )
        self.session.add(pattern)
        self.session.commit()
        return pattern

    def update(self, pattern_id: int, **kwargs) -> Optional[RotationPattern]:
        """Şablon güncelle"""
        pattern = self.get_by_id(pattern_id)
        if pattern:
            for key, value in kwargs.items():
                if hasattr(pattern, key):
                    setattr(pattern, key, value)
            self.session.commit()
        return pattern

    def delete(self, pattern_id: int) -> bool:
        """Şablon sil (schedule'lar CASCADE ile silinir)"""
        pattern = self.get_by_id(pattern_id)
        if pattern:
            self.session.delete(pattern)
            self.session.commit()
            return True
        return False

    def get_schedules(self, pattern_id: int) -> List[RotationSchedule]:
        """Şablonun takvimini getir"""
        return (
            self.session.query(RotationSchedule)
            .filter(RotationSchedule.pattern_id == pattern_id)
            .order_by(RotationSchedule.day_in_cycle, RotationSchedule.shift_id)
            .all()
        )

    def set_schedule(
        self, pattern_id: int, day_in_cycle: int, shift_id: int, team_id: int = None
    ) -> RotationSchedule:
        """Bir gün/vardiya için ekip ata"""
        # Mevcut kaydı bul veya oluştur
        schedule = (
            self.session.query(RotationSchedule)
            .filter(
                RotationSchedule.pattern_id == pattern_id,
                RotationSchedule.day_in_cycle == day_in_cycle,
                RotationSchedule.shift_id == shift_id,
            )
            .first()
        )

        if schedule:
            schedule.team_id = team_id
        else:
            schedule = RotationSchedule(
                pattern_id=pattern_id,
                day_in_cycle=day_in_cycle,
                shift_id=shift_id,
                team_id=team_id,
            )
            self.session.add(schedule)

        self.session.commit()
        return schedule

    def clear_schedules(self, pattern_id: int):
        """Şablonun tüm takvimini temizle"""
        self.session.query(RotationSchedule).filter(
            RotationSchedule.pattern_id == pattern_id
        ).delete()
        self.session.commit()

    def get_team_for_date(
        self, pattern_id: int, target_date: date, shift_id: int, start_date: date = None
    ) -> Optional[ShiftTeam]:
        """
        Belirli tarih ve vardiya için hangi ekibin çalıştığını bul.
        start_date: Rotasyonun başlangıç tarihi (varsayılan: yılbaşı)
        """
        pattern = self.get_by_id(pattern_id)
        if not pattern:
            return None

        # Başlangıç tarihi belirlenmemişse yılın başı
        if start_date is None:
            start_date = date(target_date.year, 1, 1)

        # Döngü içindeki gün (1'den başlar)
        days_since_start = (target_date - start_date).days
        day_in_cycle = (days_since_start % pattern.cycle_days) + 1

        # O gün ve vardiya için schedule'ı bul
        schedule = (
            self.session.query(RotationSchedule)
            .filter(
                RotationSchedule.pattern_id == pattern_id,
                RotationSchedule.day_in_cycle == day_in_cycle,
                RotationSchedule.shift_id == shift_id,
            )
            .first()
        )

        if schedule and schedule.team_id:
            return (
                self.session.query(ShiftTeam)
                .filter(ShiftTeam.id == schedule.team_id)
                .first()
            )

        return None

    def generate_calendar_preview(
        self, pattern_id: int, start_date: date, days: int = 14
    ) -> List[Dict]:
        """
        Belirli tarih aralığı için takvim önizlemesi oluştur.
        Her gün için hangi ekibin hangi vardiyada çalıştığını gösterir.
        """
        pattern = self.get_by_id(pattern_id)
        if not pattern:
            return []

        shifts = self.shift_service.get_all()
        result = []

        for i in range(days):
            current_date = start_date + timedelta(days=i)
            day_in_cycle = (i % pattern.cycle_days) + 1

            day_data = {
                "date": current_date,
                "day_name": current_date.strftime("%A"),
                "day_in_cycle": day_in_cycle,
                "shifts": [],
            }

            for shift in shifts:
                schedule = (
                    self.session.query(RotationSchedule)
                    .filter(
                        RotationSchedule.pattern_id == pattern_id,
                        RotationSchedule.day_in_cycle == day_in_cycle,
                        RotationSchedule.shift_id == shift.id,
                    )
                    .first()
                )

                team = None
                if schedule and schedule.team_id:
                    team = (
                        self.session.query(ShiftTeam)
                        .filter(ShiftTeam.id == schedule.team_id)
                        .first()
                    )

                day_data["shifts"].append({"shift": shift, "team": team})

            result.append(day_data)

        return result
