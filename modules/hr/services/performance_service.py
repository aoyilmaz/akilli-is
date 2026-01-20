"""
Akıllı İş - Performans Değerlendirme Servisi

Performans değerlendirme dönemleri, yetkinlikler ve değerlendirme süreçlerini yönetir.
"""

from datetime import date
from decimal import Decimal
from typing import List, Dict, Optional

from sqlalchemy.orm import Session

from database.base import get_session
from database.models.performance import (
    EvaluationPeriod,
    EvaluationPeriodType,
    EvaluationStatus,
    Competency,
    CompetencyCategory,
    PerformanceEvaluation,
    CompetencyScore,
    PerformanceGoal,
    PerformanceRating,
)
from database.models.hr import Employee


class PerformanceService:
    """
    Performans Değerlendirme Servisi

    Dönem oluşturma, değerlendirme başlatma, puan hesaplama işlemlerini yönetir.
    """

    def __init__(self, session: Session = None):
        self.session = session or get_session()

    # ========== Dönem Yönetimi ==========

    def create_period(
        self,
        name: str,
        period_type: EvaluationPeriodType,
        start_date: date,
        end_date: date,
        evaluation_start: date = None,
        evaluation_end: date = None,
        description: str = None,
    ) -> EvaluationPeriod:
        """Yeni değerlendirme dönemi oluştur"""
        period = EvaluationPeriod(
            name=name,
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            evaluation_start=evaluation_start,
            evaluation_end=evaluation_end,
            description=description,
            is_active=True,
        )
        self.session.add(period)
        self.session.commit()
        self.session.refresh(period)
        return period

    def get_active_periods(self) -> List[EvaluationPeriod]:
        """Aktif değerlendirme dönemlerini getir"""
        return (
            self.session.query(EvaluationPeriod)
            .filter(EvaluationPeriod.is_active == True)
            .order_by(EvaluationPeriod.start_date.desc())
            .all()
        )

    def get_period(self, period_id: int) -> Optional[EvaluationPeriod]:
        """Belirli dönemi getir"""
        return (
            self.session.query(EvaluationPeriod)
            .filter(EvaluationPeriod.id == period_id)
            .first()
        )

    # ========== Yetkinlik Yönetimi ==========

    def create_competency(
        self,
        name: str,
        category: CompetencyCategory,
        description: str = None,
        weight: float = 1.0,
    ) -> Competency:
        """Yeni yetkinlik tanımla"""
        competency = Competency(
            name=name,
            category=category,
            description=description,
            weight=Decimal(str(weight)),
            is_active=True,
        )
        self.session.add(competency)
        self.session.commit()
        self.session.refresh(competency)
        return competency

    def get_competencies(self, category: CompetencyCategory = None) -> List[Competency]:
        """Yetkinlikleri getir"""
        query = self.session.query(Competency).filter(Competency.is_active == True)
        if category:
            query = query.filter(Competency.category == category)
        return query.order_by(Competency.sort_order).all()

    # ========== Değerlendirme Yönetimi ==========

    def start_evaluation(
        self, employee_id: int, period_id: int, evaluator_id: int = None
    ) -> PerformanceEvaluation:
        """Çalışan için değerlendirme başlat"""
        # Mevcut kontrol
        existing = (
            self.session.query(PerformanceEvaluation)
            .filter(
                PerformanceEvaluation.employee_id == employee_id,
                PerformanceEvaluation.period_id == period_id,
            )
            .first()
        )

        if existing:
            return existing

        evaluation = PerformanceEvaluation(
            employee_id=employee_id,
            period_id=period_id,
            evaluator_id=evaluator_id,
            status=EvaluationStatus.PENDING_SELF,
        )
        self.session.add(evaluation)

        # Varsayılan yetkinlik puanlarını oluştur
        competencies = self.get_competencies()
        for comp in competencies:
            score = CompetencyScore(
                evaluation=evaluation,
                competency_id=comp.id,
            )
            self.session.add(score)

        self.session.commit()
        self.session.refresh(evaluation)
        return evaluation

    def start_evaluations_for_period(
        self, period_id: int, department_id: int = None
    ) -> tuple:
        """Dönem için toplu değerlendirme başlat"""
        query = self.session.query(Employee).filter(
            Employee.is_active == True, Employee.exit_date.is_(None)
        )

        if department_id:
            query = query.filter(Employee.department_id == department_id)

        employees = query.all()

        created = 0
        skipped = 0

        for emp in employees:
            # Yöneticiyi bul (manager_id varsa)
            evaluator_id = emp.manager_id if hasattr(emp, "manager_id") else None

            try:
                eval_obj = self.start_evaluation(emp.id, period_id, evaluator_id)
                if eval_obj:
                    created += 1
            except Exception:
                skipped += 1

        return created, skipped

    def get_evaluation(self, evaluation_id: int) -> Optional[PerformanceEvaluation]:
        """Değerlendirme detayını getir"""
        return (
            self.session.query(PerformanceEvaluation)
            .filter(PerformanceEvaluation.id == evaluation_id)
            .first()
        )

    def get_evaluations(
        self,
        period_id: int = None,
        employee_id: int = None,
        status: EvaluationStatus = None,
    ) -> List[PerformanceEvaluation]:
        """Değerlendirme listesi getir"""
        query = self.session.query(PerformanceEvaluation)

        if period_id:
            query = query.filter(PerformanceEvaluation.period_id == period_id)
        if employee_id:
            query = query.filter(PerformanceEvaluation.employee_id == employee_id)
        if status:
            query = query.filter(PerformanceEvaluation.status == status)

        return query.all()

    def submit_self_evaluation(
        self,
        evaluation_id: int,
        scores: Dict[int, float],  # competency_id -> score
        comments: str = None,
    ) -> PerformanceEvaluation:
        """Özdeğerlendirme gönder"""
        evaluation = self.get_evaluation(evaluation_id)
        if not evaluation:
            raise ValueError("Değerlendirme bulunamadı")

        if evaluation.status not in [
            EvaluationStatus.DRAFT,
            EvaluationStatus.PENDING_SELF,
        ]:
            raise ValueError("Bu değerlendirme özdeğerlendirme aşamasında değil")

        # Yetkinlik puanlarını güncelle
        total_score = Decimal("0")
        count = 0

        for comp_score in evaluation.competency_scores:
            if comp_score.competency_id in scores:
                comp_score.self_score = Decimal(str(scores[comp_score.competency_id]))
                total_score += comp_score.self_score
                count += 1

        # Ortalama hesapla
        if count > 0:
            evaluation.self_rating = (total_score / count).quantize(Decimal("0.01"))

        evaluation.self_comments = comments
        evaluation.self_evaluation_date = date.today()
        evaluation.status = EvaluationStatus.PENDING_MANAGER

        self.session.commit()
        self.session.refresh(evaluation)
        return evaluation

    def submit_manager_evaluation(
        self,
        evaluation_id: int,
        scores: Dict[int, float],
        comments: str = None,
        strengths: str = None,
        areas_for_improvement: str = None,
    ) -> PerformanceEvaluation:
        """Yönetici değerlendirmesi gönder"""
        evaluation = self.get_evaluation(evaluation_id)
        if not evaluation:
            raise ValueError("Değerlendirme bulunamadı")

        if evaluation.status != EvaluationStatus.PENDING_MANAGER:
            raise ValueError("Bu değerlendirme yönetici aşamasında değil")

        # Yetkinlik puanlarını güncelle
        total_score = Decimal("0")
        count = 0

        for comp_score in evaluation.competency_scores:
            if comp_score.competency_id in scores:
                comp_score.manager_score = Decimal(
                    str(scores[comp_score.competency_id])
                )
                total_score += comp_score.manager_score
                count += 1

        # Ortalama hesapla
        if count > 0:
            evaluation.manager_rating = (total_score / count).quantize(Decimal("0.01"))

        evaluation.manager_comments = comments
        evaluation.strengths = strengths
        evaluation.areas_for_improvement = areas_for_improvement
        evaluation.manager_evaluation_date = date.today()
        evaluation.status = EvaluationStatus.PENDING_HR

        self.session.commit()
        self.session.refresh(evaluation)
        return evaluation

    def complete_evaluation(
        self,
        evaluation_id: int,
        hr_user_id: int,
        final_rating: float = None,
        hr_comments: str = None,
        development_plan: str = None,
    ) -> PerformanceEvaluation:
        """Değerlendirmeyi tamamla (İK onayı)"""
        evaluation = self.get_evaluation(evaluation_id)
        if not evaluation:
            raise ValueError("Değerlendirme bulunamadı")

        # Nihai puan (verilmezse yönetici puanını al)
        if final_rating:
            evaluation.final_rating = Decimal(str(final_rating))
        elif evaluation.manager_rating:
            evaluation.final_rating = evaluation.manager_rating

        # Sonucu belirle
        if evaluation.final_rating:
            rating = float(evaluation.final_rating)
            if rating >= 4.5:
                evaluation.overall_result = PerformanceRating.EXCEPTIONAL
            elif rating >= 3.5:
                evaluation.overall_result = PerformanceRating.EXCEEDS
            elif rating >= 2.5:
                evaluation.overall_result = PerformanceRating.MEETS
            elif rating >= 1.5:
                evaluation.overall_result = PerformanceRating.NEEDS_IMPROVEMENT
            else:
                evaluation.overall_result = PerformanceRating.UNSATISFACTORY

        evaluation.hr_comments = hr_comments
        evaluation.development_plan = development_plan
        evaluation.hr_approved_by = hr_user_id
        evaluation.hr_approved_date = date.today()
        evaluation.status = EvaluationStatus.COMPLETED

        self.session.commit()
        self.session.refresh(evaluation)
        return evaluation

    # ========== Hedef Yönetimi ==========

    def add_goal(
        self,
        evaluation_id: int,
        title: str,
        description: str = None,
        weight: float = 20,
        target_value: float = None,
        due_date: date = None,
    ) -> PerformanceGoal:
        """Değerlendirmeye hedef ekle"""
        goal = PerformanceGoal(
            evaluation_id=evaluation_id,
            title=title,
            description=description,
            weight=Decimal(str(weight)),
            target_value=Decimal(str(target_value)) if target_value else None,
            due_date=due_date,
        )
        self.session.add(goal)
        self.session.commit()
        self.session.refresh(goal)
        return goal

    def update_goal_progress(
        self,
        goal_id: int,
        actual_value: float = None,
        score: float = None,
        employee_comment: str = None,
        manager_comment: str = None,
    ) -> PerformanceGoal:
        """Hedef ilerlemesini güncelle"""
        goal = (
            self.session.query(PerformanceGoal)
            .filter(PerformanceGoal.id == goal_id)
            .first()
        )

        if not goal:
            raise ValueError("Hedef bulunamadı")

        if actual_value is not None:
            goal.actual_value = Decimal(str(actual_value))
            # Gerçekleşme oranı hesapla
            if goal.target_value and goal.target_value > 0:
                rate = (goal.actual_value / goal.target_value) * 100
                goal.achievement_rate = rate.quantize(Decimal("0.01"))

        if score is not None:
            goal.score = Decimal(str(score))

        if employee_comment:
            goal.employee_comment = employee_comment

        if manager_comment:
            goal.manager_comment = manager_comment

        self.session.commit()
        self.session.refresh(goal)
        return goal

    # ========== Raporlar ==========

    def get_period_summary(self, period_id: int) -> Dict:
        """Dönem özeti"""
        evaluations = self.get_evaluations(period_id=period_id)

        by_status = {}
        by_rating = {}
        total_completed = 0
        avg_rating = Decimal("0")

        for ev in evaluations:
            # Durum dağılımı
            status = ev.status.value
            by_status[status] = by_status.get(status, 0) + 1

            # Sonuç dağılımı
            if ev.overall_result:
                result = ev.overall_result.value
                by_rating[result] = by_rating.get(result, 0) + 1
                total_completed += 1
                if ev.final_rating:
                    avg_rating += ev.final_rating

        if total_completed > 0:
            avg_rating = (avg_rating / total_completed).quantize(Decimal("0.01"))

        return {
            "total_evaluations": len(evaluations),
            "completed": total_completed,
            "by_status": by_status,
            "by_rating": by_rating,
            "average_rating": float(avg_rating),
        }

    def close(self):
        """Session kapat"""
        if self.session:
            self.session.close()
