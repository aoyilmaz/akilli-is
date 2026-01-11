"""
Akıllı İş - Kalite Yönetim Servisleri
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Optional
from sqlalchemy import func, desc, or_
from sqlalchemy.orm import Session

from database.base import get_session
from database.models.quality import (
    InspectionTemplate,
    InspectionCriteria,
    Inspection,
    InspectionResult,
    NonConformance,
    CustomerComplaint,
    CAPA,
    Audit,
    InspectionType,
    InspectionStatus,
    NCRSeverity,
    NCRStatus,
    ComplaintCategory,
    ComplaintStatus,
    CAPAType,
    CAPASource,
    CAPAStatus,
    AuditType,
)


class QualityService:
    """Kalite Yönetim servisi"""

    def __init__(self):
        self.session: Session = get_session()

    # ========== KONTROL ŞABLONU İŞLEMLERİ ==========

    def get_all_templates(self, active_only: bool = True) -> List[InspectionTemplate]:
        """Tüm kontrol şablonlarını getir"""
        query = self.session.query(InspectionTemplate)
        if active_only:
            query = query.filter(InspectionTemplate.is_active == True)
        return query.order_by(InspectionTemplate.code).all()

    def get_template_by_id(self, template_id: int) -> Optional[InspectionTemplate]:
        """ID ile şablon getir"""
        return (
            self.session.query(InspectionTemplate)
            .filter(InspectionTemplate.id == template_id)
            .first()
        )

    def create_template(self, data: Dict) -> InspectionTemplate:
        """Yeni şablon oluştur"""
        template = InspectionTemplate(**data)
        self.session.add(template)
        self.session.commit()
        self.session.refresh(template)
        return template

    def add_criteria_to_template(
        self, template_id: int, criteria_data: List[Dict]
    ) -> List[InspectionCriteria]:
        """Şablona kriter ekle"""
        criteria_list = []
        for idx, data in enumerate(criteria_data):
            data["template_id"] = template_id
            data["sequence"] = idx + 1
            criteria = InspectionCriteria(**data)
            self.session.add(criteria)
            criteria_list.append(criteria)
        self.session.commit()
        return criteria_list

    # ========== KALİTE KONTROL İŞLEMLERİ ==========

    def get_all_inspections(
        self,
        status: InspectionStatus = None,
        start_date: date = None,
        end_date: date = None,
        limit: int = 100,
    ) -> List[Inspection]:
        """Kontrolleri getir"""
        query = self.session.query(Inspection).filter(Inspection.is_active == True)

        if status:
            query = query.filter(Inspection.status == status)
        if start_date:
            query = query.filter(Inspection.inspection_date >= start_date)
        if end_date:
            query = query.filter(Inspection.inspection_date <= end_date)

        return query.order_by(desc(Inspection.created_at)).limit(limit).all()

    def get_inspection_by_id(self, inspection_id: int) -> Optional[Inspection]:
        """ID ile kontrol getir"""
        return (
            self.session.query(Inspection)
            .filter(Inspection.id == inspection_id)
            .first()
        )

    def generate_inspection_no(self) -> str:
        """Otomatik kontrol numarası oluştur"""
        year = datetime.now().year
        prefix = f"INS{year}"
        last = (
            self.session.query(Inspection)
            .filter(Inspection.inspection_no.like(f"{prefix}%"))
            .order_by(desc(Inspection.inspection_no))
            .first()
        )

        if last:
            num = int(last.inspection_no[-4:]) + 1
        else:
            num = 1
        return f"{prefix}{num:04d}"

    def create_inspection(self, data: Dict) -> Inspection:
        """Yeni kontrol oluştur"""
        if "inspection_no" not in data:
            data["inspection_no"] = self.generate_inspection_no()

        inspection = Inspection(**data)
        self.session.add(inspection)
        self.session.commit()
        self.session.refresh(inspection)
        return inspection

    def record_inspection_result(
        self, inspection_id: int, criteria_id: int, result_data: Dict
    ) -> InspectionResult:
        """Kontrol sonucu kaydet"""
        result_data["inspection_id"] = inspection_id
        result_data["criteria_id"] = criteria_id
        result = InspectionResult(**result_data)
        self.session.add(result)
        self.session.commit()
        return result

    def complete_inspection(
        self, inspection_id: int, status: InspectionStatus, summary: str = None
    ) -> Inspection:
        """Kontrolü tamamla"""
        inspection = self.get_inspection_by_id(inspection_id)
        if inspection:
            inspection.status = status
            inspection.result_summary = summary
            self.session.commit()
            self.session.refresh(inspection)
        return inspection

    # ========== NCR İŞLEMLERİ ==========

    def get_all_ncrs(
        self, status: NCRStatus = None, severity: NCRSeverity = None, limit: int = 100
    ) -> List[NonConformance]:
        """NCR'leri getir"""
        query = self.session.query(NonConformance).filter(
            NonConformance.is_active == True
        )

        if status:
            query = query.filter(NonConformance.status == status)
        if severity:
            query = query.filter(NonConformance.severity == severity)

        return query.order_by(desc(NonConformance.created_at)).limit(limit).all()

    def get_ncr_by_id(self, ncr_id: int) -> Optional[NonConformance]:
        """ID ile NCR getir"""
        return (
            self.session.query(NonConformance)
            .filter(NonConformance.id == ncr_id)
            .first()
        )

    def generate_ncr_no(self) -> str:
        """Otomatik NCR numarası"""
        year = datetime.now().year
        prefix = f"NCR{year}"
        last = (
            self.session.query(NonConformance)
            .filter(NonConformance.ncr_no.like(f"{prefix}%"))
            .order_by(desc(NonConformance.ncr_no))
            .first()
        )

        if last:
            num = int(last.ncr_no[-4:]) + 1
        else:
            num = 1
        return f"{prefix}{num:04d}"

    def create_ncr(self, data: Dict) -> NonConformance:
        """Yeni NCR oluştur"""
        if "ncr_no" not in data:
            data["ncr_no"] = self.generate_ncr_no()

        ncr = NonConformance(**data)
        self.session.add(ncr)
        self.session.commit()
        self.session.refresh(ncr)
        return ncr

    def update_ncr_status(
        self, ncr_id: int, status: NCRStatus
    ) -> Optional[NonConformance]:
        """NCR durumunu güncelle"""
        ncr = self.get_ncr_by_id(ncr_id)
        if ncr:
            ncr.status = status
            if status == NCRStatus.CLOSED:
                ncr.closed_date = date.today()
            self.session.commit()
            self.session.refresh(ncr)
        return ncr

    # ========== MÜŞTERİ ŞİKAYETİ İŞLEMLERİ ==========

    def get_all_complaints(
        self,
        status: ComplaintStatus = None,
        category: ComplaintCategory = None,
        limit: int = 100,
    ) -> List[CustomerComplaint]:
        """Şikayetleri getir"""
        query = self.session.query(CustomerComplaint).filter(
            CustomerComplaint.is_active == True
        )

        if status:
            query = query.filter(CustomerComplaint.status == status)
        if category:
            query = query.filter(CustomerComplaint.category == category)

        return query.order_by(desc(CustomerComplaint.created_at)).limit(limit).all()

    def get_complaint_by_id(self, complaint_id: int) -> Optional[CustomerComplaint]:
        """ID ile şikayet getir"""
        return (
            self.session.query(CustomerComplaint)
            .filter(CustomerComplaint.id == complaint_id)
            .first()
        )

    def generate_complaint_no(self) -> str:
        """Otomatik şikayet numarası"""
        year = datetime.now().year
        prefix = f"CMP{year}"
        last = (
            self.session.query(CustomerComplaint)
            .filter(CustomerComplaint.complaint_no.like(f"{prefix}%"))
            .order_by(desc(CustomerComplaint.complaint_no))
            .first()
        )

        if last:
            num = int(last.complaint_no[-4:]) + 1
        else:
            num = 1
        return f"{prefix}{num:04d}"

    def create_complaint(self, data: Dict) -> CustomerComplaint:
        """Yeni şikayet oluştur"""
        if "complaint_no" not in data:
            data["complaint_no"] = self.generate_complaint_no()

        complaint = CustomerComplaint(**data)
        self.session.add(complaint)
        self.session.commit()
        self.session.refresh(complaint)
        return complaint

    def resolve_complaint(
        self, complaint_id: int, resolution: str, satisfaction: int = None
    ) -> Optional[CustomerComplaint]:
        """Şikayeti çöz"""
        complaint = self.get_complaint_by_id(complaint_id)
        if complaint:
            complaint.resolution = resolution
            complaint.resolution_date = date.today()
            complaint.status = ComplaintStatus.CLOSED
            if satisfaction:
                complaint.satisfaction_score = satisfaction
            self.session.commit()
            self.session.refresh(complaint)
        return complaint

    # ========== CAPA İŞLEMLERİ ==========

    def get_all_capas(
        self, status: CAPAStatus = None, capa_type: CAPAType = None, limit: int = 100
    ) -> List[CAPA]:
        """CAPA'ları getir"""
        query = self.session.query(CAPA).filter(CAPA.is_active == True)

        if status:
            query = query.filter(CAPA.status == status)
        if capa_type:
            query = query.filter(CAPA.capa_type == capa_type)

        return query.order_by(desc(CAPA.created_at)).limit(limit).all()

    def get_capa_by_id(self, capa_id: int) -> Optional[CAPA]:
        """ID ile CAPA getir"""
        return self.session.query(CAPA).filter(CAPA.id == capa_id).first()

    def generate_capa_no(self) -> str:
        """Otomatik CAPA numarası"""
        year = datetime.now().year
        prefix = f"CAPA{year}"
        last = (
            self.session.query(CAPA)
            .filter(CAPA.capa_no.like(f"{prefix}%"))
            .order_by(desc(CAPA.capa_no))
            .first()
        )

        if last:
            num = int(last.capa_no[-4:]) + 1
        else:
            num = 1
        return f"{prefix}{num:04d}"

    def create_capa(self, data: Dict) -> CAPA:
        """Yeni CAPA oluştur"""
        if "capa_no" not in data:
            data["capa_no"] = self.generate_capa_no()

        capa = CAPA(**data)
        self.session.add(capa)
        self.session.commit()
        self.session.refresh(capa)
        return capa

    def create_capa_from_ncr(self, ncr_id: int, capa_type: CAPAType) -> CAPA:
        """NCR'den CAPA oluştur"""
        ncr = self.get_ncr_by_id(ncr_id)
        if not ncr:
            raise ValueError("NCR bulunamadı")

        capa_data = {
            "capa_type": capa_type,
            "source": CAPASource.NCR,
            "ncr_id": ncr_id,
            "description": f"NCR {ncr.ncr_no} için {capa_type.value} faaliyet",
        }
        return self.create_capa(capa_data)

    def create_capa_from_complaint(
        self, complaint_id: int, capa_type: CAPAType
    ) -> CAPA:
        """Şikayetten CAPA oluştur"""
        complaint = self.get_complaint_by_id(complaint_id)
        if not complaint:
            raise ValueError("Şikayet bulunamadı")

        capa_data = {
            "capa_type": capa_type,
            "source": CAPASource.CUSTOMER_COMPLAINT,
            "complaint_id": complaint_id,
            "description": f"Şikayet {complaint.complaint_no} için faaliyet",
        }
        return self.create_capa(capa_data)

    def close_capa(
        self, capa_id: int, verification_result: str, verified_by: int
    ) -> Optional[CAPA]:
        """CAPA'yı kapat"""
        capa = self.get_capa_by_id(capa_id)
        if capa:
            capa.verification_result = verification_result
            capa.verified_by = verified_by
            capa.verification_date = date.today()
            capa.completion_date = date.today()
            capa.status = CAPAStatus.CLOSED
            self.session.commit()
            self.session.refresh(capa)
        return capa

    # ========== DENETİM İŞLEMLERİ ==========

    def get_all_audits(self, limit: int = 100) -> List[Audit]:
        """Denetimleri getir"""
        return (
            self.session.query(Audit)
            .filter(Audit.is_active == True)
            .order_by(desc(Audit.created_at))
            .limit(limit)
            .all()
        )

    def create_audit(self, data: Dict) -> Audit:
        """Yeni denetim oluştur"""
        if "audit_no" not in data:
            year = datetime.now().year
            prefix = f"AUD{year}"
            last = (
                self.session.query(Audit)
                .filter(Audit.audit_no.like(f"{prefix}%"))
                .order_by(desc(Audit.audit_no))
                .first()
            )
            num = int(last.audit_no[-4:]) + 1 if last else 1
            data["audit_no"] = f"{prefix}{num:04d}"

        audit = Audit(**data)
        self.session.add(audit)
        self.session.commit()
        self.session.refresh(audit)
        return audit

    def close(self):
        """Session kapat"""
        if self.session:
            self.session.close()
