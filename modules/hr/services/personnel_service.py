"""
Akıllı İş - Özlük ve İzin Hakediş Servisi

Personel belgeleri yönetimi ve yıllık izin hakediş otomasyonu.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional

from sqlalchemy.orm import Session

from database.base import get_session
from database.models.personnel import (
    EmployeeDocument,
    DocumentType,
    DocumentStatus,
    LeaveEntitlementRule,
    LeaveEntitlementType,
    LeaveBalance,
)
from database.models.hr import Employee


class PersonnelService:
    """
    Özlük Dosyası ve İzin Hakediş Servisi
    """

    def __init__(self, session: Session = None):
        self.session = session or get_session()

    # ========== Belge Yönetimi ==========

    def add_document(
        self,
        employee_id: int,
        document_type: DocumentType,
        name: str,
        file_path: str = None,
        issue_date: date = None,
        expiry_date: date = None,
        is_mandatory: bool = False,
        description: str = None,
    ) -> EmployeeDocument:
        """Çalışana belge ekle"""
        doc = EmployeeDocument(
            employee_id=employee_id,
            document_type=document_type,
            name=name,
            file_path=file_path,
            issue_date=issue_date,
            expiry_date=expiry_date,
            is_mandatory=is_mandatory,
            description=description,
            status=DocumentStatus.VALID,
        )
        self.session.add(doc)
        self.session.commit()
        self.session.refresh(doc)
        return doc

    def get_employee_documents(
        self, employee_id: int, doc_type: DocumentType = None
    ) -> List[EmployeeDocument]:
        """Çalışan belgelerini getir"""
        query = self.session.query(EmployeeDocument).filter(
            EmployeeDocument.employee_id == employee_id
        )
        if doc_type:
            query = query.filter(EmployeeDocument.document_type == doc_type)
        return query.order_by(EmployeeDocument.document_type).all()

    def get_expiring_documents(self, days_ahead: int = 30) -> List[EmployeeDocument]:
        """Süresi yaklaşan belgeler"""
        end_date = date.today() + timedelta(days=days_ahead)
        return (
            self.session.query(EmployeeDocument)
            .filter(
                EmployeeDocument.expiry_date.isnot(None),
                EmployeeDocument.expiry_date <= end_date,
                EmployeeDocument.status == DocumentStatus.VALID,
            )
            .order_by(EmployeeDocument.expiry_date)
            .all()
        )

    def get_missing_mandatory_documents(self, employee_id: int = None) -> List[Dict]:
        """Eksik zorunlu belgeler"""
        # Tüm zorunlu belge türleri
        mandatory_types = [
            DocumentType.CONTRACT,
            DocumentType.ID_CARD,
            DocumentType.HEALTH_REPORT,
            DocumentType.CRIMINAL_RECORD,
        ]

        if employee_id:
            employees = [self.session.query(Employee).get(employee_id)]
        else:
            employees = (
                self.session.query(Employee).filter(Employee.is_active == True).all()
            )

        missing = []
        for emp in employees:
            existing_types = {
                d.document_type
                for d in emp.documents
                if d.status == DocumentStatus.VALID
            }
            for dt in mandatory_types:
                if dt not in existing_types:
                    missing.append(
                        {
                            "employee_id": emp.id,
                            "employee_name": f"{emp.first_name} {emp.last_name}",
                            "document_type": dt.value,
                        }
                    )

        return missing

    def update_document_statuses(self) -> int:
        """Belge durumlarını güncelle"""
        today = date.today()
        warning_date = today + timedelta(days=30)
        updated = 0

        # Süresi dolmuşlar
        expired = (
            self.session.query(EmployeeDocument)
            .filter(
                EmployeeDocument.expiry_date < today,
                EmployeeDocument.status != DocumentStatus.EXPIRED,
            )
            .all()
        )

        for doc in expired:
            doc.status = DocumentStatus.EXPIRED
            updated += 1

        # Yaklaşanlar
        expiring = (
            self.session.query(EmployeeDocument)
            .filter(
                EmployeeDocument.expiry_date >= today,
                EmployeeDocument.expiry_date <= warning_date,
                EmployeeDocument.status == DocumentStatus.VALID,
            )
            .all()
        )

        for doc in expiring:
            doc.status = DocumentStatus.EXPIRING_SOON
            updated += 1

        self.session.commit()
        return updated

    # ========== İzin Hakediş Kuralları ==========

    def create_entitlement_rule(
        self,
        name: str,
        leave_type: LeaveEntitlementType,
        min_years: int,
        days_entitled: int,
        max_years: int = None,
        description: str = None,
    ) -> LeaveEntitlementRule:
        """İzin hakediş kuralı oluştur"""
        rule = LeaveEntitlementRule(
            name=name,
            leave_type=leave_type,
            min_years=min_years,
            max_years=max_years,
            days_entitled=days_entitled,
            description=description,
            is_active=True,
        )
        self.session.add(rule)
        self.session.commit()
        self.session.refresh(rule)
        return rule

    def get_entitlement_rules(
        self, leave_type: LeaveEntitlementType = None
    ) -> List[LeaveEntitlementRule]:
        """Hakediş kurallarını getir"""
        query = self.session.query(LeaveEntitlementRule).filter(
            LeaveEntitlementRule.is_active == True
        )
        if leave_type:
            query = query.filter(LeaveEntitlementRule.leave_type == leave_type)
        return query.order_by(
            LeaveEntitlementRule.leave_type, LeaveEntitlementRule.min_years
        ).all()

    def calculate_entitlement(
        self,
        employee: Employee,
        leave_type: LeaveEntitlementType = LeaveEntitlementType.ANNUAL,
    ) -> int:
        """Çalışan için izin hakedişini hesapla"""
        if not employee.hire_date:
            return 0

        # Kıdem yılı hesapla
        today = date.today()
        years = (today - employee.hire_date).days // 365

        # Uygun kuralı bul
        rules = self.get_entitlement_rules(leave_type)
        for rule in rules:
            min_ok = years >= rule.min_years
            max_ok = rule.max_years is None or years < rule.max_years
            if min_ok and max_ok:
                return rule.days_entitled

        return 0

    # ========== İzin Bakiyesi ==========

    def get_leave_balance(
        self,
        employee_id: int,
        year: int = None,
        leave_type: LeaveEntitlementType = LeaveEntitlementType.ANNUAL,
    ) -> Optional[LeaveBalance]:
        """Çalışan izin bakiyesi"""
        year = year or date.today().year
        return (
            self.session.query(LeaveBalance)
            .filter(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.year == year,
                LeaveBalance.leave_type == leave_type,
            )
            .first()
        )

    def calculate_all_entitlements(self, year: int = None) -> tuple:
        """Tüm çalışanlar için hakediş hesapla"""
        year = year or date.today().year

        employees = (
            self.session.query(Employee)
            .filter(Employee.is_active == True, Employee.exit_date.is_(None))
            .all()
        )

        created = 0
        updated = 0

        for emp in employees:
            entitlement = self.calculate_entitlement(emp)

            # Mevcut bakiye var mı?
            balance = self.get_leave_balance(emp.id, year, LeaveEntitlementType.ANNUAL)

            if balance:
                if float(balance.entitled) != entitlement:
                    balance.entitled = Decimal(str(entitlement))
                    updated += 1
            else:
                # Önceki yıldan devir
                prev_balance = self.get_leave_balance(
                    emp.id, year - 1, LeaveEntitlementType.ANNUAL
                )
                carried = 0
                if prev_balance:
                    # Maksimum 5 gün devir
                    available = prev_balance.available
                    carried = min(available, 5) if available > 0 else 0

                balance = LeaveBalance(
                    employee_id=emp.id,
                    year=year,
                    leave_type=LeaveEntitlementType.ANNUAL,
                    carried_over=Decimal(str(carried)),
                    entitled=Decimal(str(entitlement)),
                    used=Decimal("0"),
                    pending=Decimal("0"),
                )
                self.session.add(balance)
                created += 1

        self.session.commit()
        return created, updated

    def use_leave(
        self,
        employee_id: int,
        days: float,
        year: int = None,
        leave_type: LeaveEntitlementType = LeaveEntitlementType.ANNUAL,
    ) -> LeaveBalance:
        """İzin kullan"""
        year = year or date.today().year
        balance = self.get_leave_balance(employee_id, year, leave_type)

        if not balance:
            raise ValueError("İzin bakiyesi bulunamadı")

        if balance.available < days:
            raise ValueError(f"Yetersiz bakiye: {balance.available} gün mevcut")

        balance.used = Decimal(str(float(balance.used) + days))
        self.session.commit()
        self.session.refresh(balance)
        return balance

    # ========== Raporlar ==========

    def get_leave_summary(self, year: int = None) -> Dict:
        """İzin özeti"""
        year = year or date.today().year

        balances = (
            self.session.query(LeaveBalance)
            .filter(
                LeaveBalance.year == year,
                LeaveBalance.leave_type == LeaveEntitlementType.ANNUAL,
            )
            .all()
        )

        total_entitled = sum(float(b.entitled) for b in balances)
        total_used = sum(float(b.used) for b in balances)
        total_available = sum(b.available for b in balances)

        return {
            "year": year,
            "employee_count": len(balances),
            "total_entitled_days": total_entitled,
            "total_used_days": total_used,
            "total_available_days": total_available,
            "usage_rate": (
                round(total_used / total_entitled * 100, 1) if total_entitled > 0 else 0
            ),
        }

    def close(self):
        """Session kapat"""
        if self.session:
            self.session.close()
