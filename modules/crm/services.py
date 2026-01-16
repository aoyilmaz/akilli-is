"""
Akıllı İş - CRM Servis Katmanı
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from database.models.crm import (
    Lead,
    LeadStatus,
    Opportunity,
    OpportunityStage,
    Activity,
    ActivityType,
)
from database.models.sales import Customer
from database.models.user import User


class CRMService:
    def __init__(self, session: Session):
        self.session = session

    # === LEAD (ADAY MÜŞTERİ) ===

    def create_lead(self, data: Dict[str, Any]) -> Lead:
        """Yeni aday müşteri oluşturur"""
        lead = Lead(**data)
        self.session.add(lead)
        self.session.commit()
        self.session.refresh(lead)
        return lead

    def get_lead(self, lead_id: int) -> Optional[Lead]:
        """ID'ye göre aday müşteri getirir"""
        return self.session.query(Lead).get(lead_id)

    def list_leads(self, status: Optional[LeadStatus] = None) -> List[Lead]:
        """Aday müşterileri listeler"""
        query = self.session.query(Lead)
        if status:
            query = query.filter(Lead.status == status)
        return query.order_by(desc(Lead.created_at)).all()

    def update_lead(self, lead_id: int, data: Dict[str, Any]) -> Optional[Lead]:
        """Aday müşteri bilgilerini günceller"""
        lead = self.get_lead(lead_id)
        if not lead:
            return None

        for key, value in data.items():
            if hasattr(lead, key):
                setattr(lead, key, value)

        self.session.commit()
        self.session.refresh(lead)
        return lead

    def search_leads(self, query: str) -> List[Lead]:
        """İsim veya şirket ismine göre arama yapar"""
        search_term = f"%{query}%"
        return (
            self.session.query(Lead)
            .filter(
                (Lead.first_name.ilike(search_term))
                | (Lead.last_name.ilike(search_term))
                | (Lead.company_name.ilike(search_term))
            )
            .all()
        )

    def convert_lead_to_customer(self, lead_id: int) -> Optional[Customer]:
        """
        Aday müşteriyi (Lead) gerçek müşteriye (Customer) dönüştürür.
        1. Lead status 'CONVERTED' yapılır.
        2. Customer tablosunda yeni kayıt oluşturulur.
        """
        lead = self.get_lead(lead_id)
        if not lead or lead.status == LeadStatus.CONVERTED:
            return None

        # Müşteri kodu üret (basit mantık, sequence kullanılabilir ileride)
        import random

        customer_code = f"CUST-{datetime.now().year}-{random.randint(1000, 9999)}"

        customer = Customer(
            code=customer_code,
            name=lead.company_name or f"{lead.first_name} {lead.last_name}",
            short_name=lead.company_name,
            contact_person=f"{lead.first_name} {lead.last_name}",
            email=lead.email,
            phone=lead.phone,
            mobile=lead.mobile,
            website=lead.website,
            address=lead.address,
            city=lead.city,
            country=lead.country,
            notes=f"Converted from Lead #{lead.id}. {lead.notes or ''}",
        )

        self.session.add(customer)
        lead.status = LeadStatus.CONVERTED
        self.session.commit()
        self.session.refresh(customer)
        return customer

    # === OPPORTUNITY (FIRSAT) ===

    def create_opportunity(self, data: Dict[str, Any]) -> Opportunity:
        """Yeni fırsat oluşturur"""
        opp = Opportunity(**data)
        self.session.add(opp)
        self.session.commit()
        self.session.refresh(opp)
        return opp

    def get_opportunity(self, opp_id: int) -> Optional[Opportunity]:
        """ID'ye göre fırsat getirir"""
        return (
            self.session.query(Opportunity)
            .options(
                joinedload(Opportunity.lead),
                joinedload(Opportunity.customer),
                joinedload(Opportunity.assigned_to),
            )
            .get(opp_id)
        )

    def list_opportunities(
        self, stage: Optional[OpportunityStage] = None
    ) -> List[Opportunity]:
        """Fırsatları listeler"""
        query = self.session.query(Opportunity)
        if stage:
            query = query.filter(Opportunity.stage == stage)
        return query.order_by(desc(Opportunity.created_at)).all()

    def update_opportunity_stage(
        self, opp_id: int, stage: OpportunityStage
    ) -> Optional[Opportunity]:
        """Fırsat aşamasını günceller"""
        opp = self.get_opportunity(opp_id)
        if not opp:
            return None

        opp.stage = stage
        self.session.commit()
        self.session.refresh(opp)
        return opp

    # === ACTIVITY (AKTİVİTE) ===

    def create_activity(self, data: Dict[str, Any]) -> Activity:
        """Yeni aktivite oluşturur"""
        activity = Activity(**data)
        self.session.add(activity)
        self.session.commit()
        self.session.refresh(activity)
        return activity

    def get_lead_activities(self, lead_id: int) -> List[Activity]:
        """Bir aday müşteriye ait aktiviteleri getirir"""
        return (
            self.session.query(Activity)
            .filter(Activity.lead_id == lead_id)
            .order_by(desc(Activity.due_date))
            .all()
        )

    def get_opportunity_activities(self, opp_id: int) -> List[Activity]:
        """Bir fırsata ait aktiviteleri getirir"""
        return (
            self.session.query(Activity)
            .filter(Activity.opportunity_id == opp_id)
            .order_by(desc(Activity.due_date))
            .all()
        )
