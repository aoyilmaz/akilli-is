"""
Akıllı İş - İşe Alım (Recruitment) Servisi
"""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models.hr import (
    JobPosting,
    JobPostingStatus,
    JobApplication,
    ApplicationStatus,
    Interview,
    Employee,
    Department,
    Position,
    EmploymentType,
)


class RecruitmentService:
    def __init__(self, db: Session):
        self.db = db

    # --- İŞ İLANI YÖNETİMİ ---

    def create_posting(self, data: dict) -> JobPosting:
        """Yeni iş ilanı oluşturur"""
        # Kod üretimi (ILN-YYMM-XXX)
        year_month = datetime.now().strftime("%y%m")
        count = (
            self.db.query(func.count(JobPosting.id))
            .filter(JobPosting.code.like(f"ILN{year_month}-%"))
            .scalar()
        )
        data["code"] = f"ILN{year_month}-{count + 1:03d}"

        posting = JobPosting(**data)
        self.db.add(posting)
        self.db.commit()
        self.db.refresh(posting)
        return posting

    def open_posting(self, posting_id: int):
        """İlanı yayına alır"""
        posting = self.db.query(JobPosting).get(posting_id)
        if posting:
            posting.status = JobPostingStatus.OPEN
            posting.posted_at = datetime.now()
            self.db.commit()
        return posting

    def close_posting(self, posting_id: int, status=JobPostingStatus.CLOSED):
        """İlanı kapatır"""
        posting = self.db.query(JobPosting).get(posting_id)
        if posting:
            posting.status = status
            self.db.commit()
        return posting

    def get_active_postings(self):
        """Aktif ilanları listeler"""
        return (
            self.db.query(JobPosting)
            .filter(JobPosting.status == JobPostingStatus.OPEN)
            .all()
        )

    # --- BAŞVURU YÖNETİMİ ---

    def create_application(self, data: dict) -> JobApplication:
        """Yeni başvuru kaydı oluşturur"""
        # Kod üretimi (BSV-YYMM-XXX)
        year_month = datetime.now().strftime("%y%m")
        count = (
            self.db.query(func.count(JobApplication.id))
            .filter(JobApplication.code.like(f"BSV{year_month}-%"))
            .scalar()
        )
        data["code"] = f"BSV{year_month}-{count + 1:03d}"

        application = JobApplication(**data)
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application

    def advance_stage(self, application_id: int) -> JobApplication:
        """Başvuru aşamasını bir sonraki adıma taşır"""
        app = self.db.query(JobApplication).get(application_id)
        if not app:
            return None

        stages = list(ApplicationStatus)
        current_idx = stages.index(app.status)
        if current_idx < len(stages) - 1:
            # Mantıksal sıralama: NEW -> SCREENING -> INTERVIEW -> ASSESSMENT -> OFFER -> HIRED
            # REJECTED ve WITHDRAWN sona eklenmiş olabilir, kontrol etmeliyiz.
            next_status = stages[current_idx + 1]
            if next_status not in [
                ApplicationStatus.REJECTED,
                ApplicationStatus.WITHDRAWN,
            ]:
                app.status = next_status
                self.db.commit()
        return app

    def reject_application(self, application_id: int, reason: str = None):
        """Başvuruyu reddeder"""
        app = self.db.query(JobApplication).get(application_id)
        if app:
            app.status = ApplicationStatus.REJECTED
            if reason:
                if app.notes:
                    app.notes += f"\nRed Sebebi: {reason}"
                else:
                    app.notes = f"Red Sebebi: {reason}"
            self.db.commit()
        return app

    def hire_candidate(self, application_id: int) -> Employee:
        """Adayı işe alır ve Employee kaydı oluşturur"""
        app = self.db.query(JobApplication).get(application_id)
        if not app or app.status == ApplicationStatus.HIRED:
            return None

        posting = app.posting

        # Yeni personel numarası üret (PERS-XXXX)
        count = self.db.query(func.count(Employee.id)).scalar()
        emp_no = f"PERS-{count + 1001:04d}"

        # Pozisyonu bul veya oluştur
        pos = self.db.query(Position).filter_by(name=posting.position).first()
        if not pos:
            pos = Position(
                code=f"POS-{posting.position[:3].upper()}",
                name=posting.position,
                department_id=posting.department_id,
            )
            self.db.add(pos)
            self.db.flush()

        employee = Employee(
            employee_no=emp_no,
            first_name=app.first_name,
            last_name=app.last_name,
            email=app.email,
            phone=app.phone,
            department_id=posting.department_id,
            position_id=pos.id,
            hire_date=datetime.now().date(),
            employment_type=EmploymentType.FULL_TIME,
        )
        self.db.add(employee)

        # Başvuru durumunu güncelle
        app.status = ApplicationStatus.HIRED

        self.db.commit()
        self.db.refresh(employee)
        return employee

    # --- MÜLAKAT YÖNETİMİ ---

    def schedule_interview(self, data: dict) -> Interview:
        """Mülakat planlar"""
        interview = Interview(**data)
        self.db.add(interview)

        # Başvuru durumunu INTERVIEW yap (eğer henüz değilse)
        app = self.db.query(JobApplication).get(data["application_id"])
        if app and app.status.value == "screening":
            app.status = ApplicationStatus.INTERVIEW

        self.db.commit()
        self.db.refresh(interview)
        return interview

    def complete_interview(
        self, interview_id: int, rating: int, feedback: str, result: str
    ):
        """Mülakatı sonuçlandırır"""
        interview = self.db.query(Interview).get(interview_id)
        if interview:
            interview.status = "completed"
            interview.rating = rating
            interview.feedback = feedback
            interview.result = result

            # Adayın genel puanını güncelle (basit ortalama veya son mülakat)
            app = interview.application
            app.rating = rating

            self.db.commit()
        return interview

    # --- ANALİZ VE METRİKLER ---

    def get_pipeline(self, posting_id: int):
        """İlan bazlı aday boru hattı (pipeline) verisi döner"""
        results = (
            self.db.query(JobApplication.status, func.count(JobApplication.id))
            .filter(JobApplication.posting_id == posting_id)
            .group_by(JobApplication.status)
            .all()
        )

        return {status.value: count for status, count in results}

    def get_recruitment_metrics(self):
        """Genel işe alım metrikleri"""
        total_open = (
            self.db.query(func.count(JobPosting.id))
            .filter_by(status=JobPostingStatus.OPEN)
            .scalar()
        )
        total_apps = self.db.query(func.count(JobApplication.id)).scalar()
        total_hired = (
            self.db.query(func.count(JobApplication.id))
            .filter_by(status=ApplicationStatus.HIRED)
            .scalar()
        )

        return {
            "total_open_postings": total_open,
            "total_applications": total_apps,
            "total_hired": total_hired,
            "conversion_rate": (
                (total_hired / total_apps * 100) if total_apps > 0 else 0
            ),
        }
