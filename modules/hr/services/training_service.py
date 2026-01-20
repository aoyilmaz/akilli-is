"""
Akıllı İş - Eğitim Takibi Servisi

Eğitim planlaması, katılım takibi ve sertifika yönetimi.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional

from sqlalchemy.orm import Session

from database.base import get_session
from database.models.training import (
    Training,
    TrainingSession,
    TrainingParticipant,
    EmployeeCertificate,
    TrainingStatus,
    TrainingType,
    CertificateStatus,
)
from database.models.hr import Employee


class TrainingService:
    """
    Eğitim Takibi Servisi

    Eğitim planlaması, katılım ve sertifika yönetimi.
    """

    def __init__(self, session: Session = None):
        self.session = session or get_session()

    # ========== Eğitim Yönetimi ==========

    def create_training(
        self,
        name: str,
        training_type: TrainingType = TrainingType.INTERNAL,
        description: str = None,
        duration_hours: float = None,
        trainer_name: str = None,
        has_certificate: bool = False,
        certificate_validity_months: int = None,
        cost: float = None,
    ) -> Training:
        """Yeni eğitim tanımla"""
        training = Training(
            name=name,
            training_type=training_type,
            description=description,
            duration_hours=Decimal(str(duration_hours)) if duration_hours else None,
            trainer_name=trainer_name,
            has_certificate=has_certificate,
            certificate_validity_months=certificate_validity_months,
            cost=Decimal(str(cost)) if cost else None,
            is_active=True,
        )
        self.session.add(training)
        self.session.commit()
        self.session.refresh(training)
        return training

    def get_trainings(self, active_only: bool = True) -> List[Training]:
        """Eğitim listesi"""
        query = self.session.query(Training)
        if active_only:
            query = query.filter(Training.is_active == True)
        return query.order_by(Training.name).all()

    # ========== Oturum Yönetimi ==========

    def create_session(
        self,
        training_id: int,
        planned_date: date,
        location: str = None,
        is_online: bool = False,
        max_participants: int = None,
    ) -> TrainingSession:
        """Eğitim oturumu planla"""
        session_obj = TrainingSession(
            training_id=training_id,
            planned_date=planned_date,
            location=location,
            is_online=is_online,
            max_participants=max_participants,
            status=TrainingStatus.PLANNED,
        )
        self.session.add(session_obj)
        self.session.commit()
        self.session.refresh(session_obj)
        return session_obj

    def get_upcoming_sessions(self, days_ahead: int = 30) -> List[TrainingSession]:
        """Yaklaşan eğitim oturumları"""
        end_date = date.today() + timedelta(days=days_ahead)
        return (
            self.session.query(TrainingSession)
            .filter(
                TrainingSession.planned_date >= date.today(),
                TrainingSession.planned_date <= end_date,
                TrainingSession.status == TrainingStatus.PLANNED,
            )
            .order_by(TrainingSession.planned_date)
            .all()
        )

    def add_participant(self, session_id: int, employee_id: int) -> TrainingParticipant:
        """Oturuma katılımcı ekle"""
        participant = TrainingParticipant(
            session_id=session_id,
            employee_id=employee_id,
            attended=False,
        )
        self.session.add(participant)
        self.session.commit()
        self.session.refresh(participant)
        return participant

    def record_attendance(
        self,
        participant_id: int,
        attended: bool,
        attendance_hours: float = None,
        score: float = None,
        passed: bool = None,
        feedback: str = None,
    ) -> TrainingParticipant:
        """Katılım kaydı"""
        participant = (
            self.session.query(TrainingParticipant)
            .filter(TrainingParticipant.id == participant_id)
            .first()
        )

        if not participant:
            raise ValueError("Katılımcı bulunamadı")

        participant.attended = attended
        if attendance_hours:
            participant.attendance_hours = Decimal(str(attendance_hours))
        if score:
            participant.score = Decimal(str(score))
        if passed is not None:
            participant.passed = passed
        if feedback:
            participant.feedback = feedback

        self.session.commit()
        self.session.refresh(participant)
        return participant

    def complete_session(self, session_id: int) -> TrainingSession:
        """Oturumu tamamla"""
        session_obj = (
            self.session.query(TrainingSession)
            .filter(TrainingSession.id == session_id)
            .first()
        )

        if not session_obj:
            raise ValueError("Oturum bulunamadı")

        session_obj.status = TrainingStatus.COMPLETED
        session_obj.actual_date = date.today()

        self.session.commit()
        return session_obj

    # ========== Sertifika Yönetimi ==========

    def issue_certificate(
        self,
        employee_id: int,
        name: str,
        issue_date: date,
        expiry_date: date = None,
        issuing_authority: str = None,
        certificate_number: str = None,
        training_id: int = None,
        document_path: str = None,
    ) -> EmployeeCertificate:
        """Sertifika kaydet"""
        cert = EmployeeCertificate(
            employee_id=employee_id,
            name=name,
            issue_date=issue_date,
            expiry_date=expiry_date,
            issuing_authority=issuing_authority,
            certificate_number=certificate_number,
            training_id=training_id,
            document_path=document_path,
            status=CertificateStatus.VALID,
        )
        self.session.add(cert)
        self.session.commit()
        self.session.refresh(cert)
        return cert

    def get_employee_certificates(self, employee_id: int) -> List[EmployeeCertificate]:
        """Çalışan sertifikaları"""
        return (
            self.session.query(EmployeeCertificate)
            .filter(EmployeeCertificate.employee_id == employee_id)
            .order_by(EmployeeCertificate.expiry_date.desc())
            .all()
        )

    def get_expiring_certificates(
        self, days_ahead: int = 30
    ) -> List[EmployeeCertificate]:
        """Süresi yaklaşan sertifikalar"""
        end_date = date.today() + timedelta(days=days_ahead)
        return (
            self.session.query(EmployeeCertificate)
            .filter(
                EmployeeCertificate.expiry_date.isnot(None),
                EmployeeCertificate.expiry_date <= end_date,
                EmployeeCertificate.status == CertificateStatus.VALID,
            )
            .order_by(EmployeeCertificate.expiry_date)
            .all()
        )

    def update_certificate_statuses(self) -> int:
        """Sertifika durumlarını güncelle"""
        today = date.today()
        warning_date = today + timedelta(days=30)
        updated = 0

        # Süresi dolmuşlar
        expired = (
            self.session.query(EmployeeCertificate)
            .filter(
                EmployeeCertificate.expiry_date < today,
                EmployeeCertificate.status != CertificateStatus.EXPIRED,
            )
            .all()
        )

        for cert in expired:
            cert.status = CertificateStatus.EXPIRED
            updated += 1

        # Yaklaşanlar
        expiring = (
            self.session.query(EmployeeCertificate)
            .filter(
                EmployeeCertificate.expiry_date >= today,
                EmployeeCertificate.expiry_date <= warning_date,
                EmployeeCertificate.status == CertificateStatus.VALID,
            )
            .all()
        )

        for cert in expiring:
            cert.status = CertificateStatus.EXPIRING_SOON
            updated += 1

        self.session.commit()
        return updated

    # ========== Raporlar ==========

    def get_training_summary(self, year: int = None) -> Dict:
        """Eğitim özeti"""
        year = year or date.today().year

        sessions = (
            self.session.query(TrainingSession)
            .filter(
                TrainingSession.planned_date >= date(year, 1, 1),
                TrainingSession.planned_date <= date(year, 12, 31),
            )
            .all()
        )

        total_sessions = len(sessions)
        completed = sum(1 for s in sessions if s.status == TrainingStatus.COMPLETED)
        total_participants = sum(len(s.participants) for s in sessions)
        total_attended = sum(
            sum(1 for p in s.participants if p.attended) for s in sessions
        )

        return {
            "year": year,
            "total_sessions": total_sessions,
            "completed_sessions": completed,
            "total_participants": total_participants,
            "total_attended": total_attended,
            "attendance_rate": (
                round(total_attended / total_participants * 100, 1)
                if total_participants > 0
                else 0
            ),
        }

    def get_employee_training_history(self, employee_id: int) -> List[Dict]:
        """Çalışan eğitim geçmişi"""
        participations = (
            self.session.query(TrainingParticipant)
            .filter(TrainingParticipant.employee_id == employee_id)
            .all()
        )

        history = []
        for p in participations:
            session = p.session
            training = session.training
            history.append(
                {
                    "training_name": training.name,
                    "training_type": training.training_type.value,
                    "date": session.actual_date or session.planned_date,
                    "attended": p.attended,
                    "score": float(p.score) if p.score else None,
                    "passed": p.passed,
                    "certificate_issued": p.certificate_issued,
                }
            )

        return sorted(history, key=lambda x: x["date"], reverse=True)

    def close(self):
        """Session kapat"""
        if self.session:
            self.session.close()
