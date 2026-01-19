"""
Akıllı İş - Firma Servisi
"""

from typing import Optional, Dict, Any, List

from database.base import get_session
from database.models.company import (
    Company,
    CompanyAddress,
    CompanyBank,
    CompanyContact,
    CompanySettings,
    CompanyDocument,
)


class CompanyService:
    """Firma işlemleri servisi"""

    def __init__(self):
        self.session = get_session()

    def close(self):
        """Session kapat"""
        if self.session:
            self.session.close()

    # === FİRMA İŞLEMLERİ ===

    def get_company(self, company_id: int = None) -> Optional[Company]:
        """Firma bilgisini getir (varsayılan: ilk aktif firma)"""
        if company_id:
            return self.session.query(Company).get(company_id)
        return (
            self.session.query(Company)
            .filter(Company.is_active == True)  # noqa: E712
            .first()
        )

    def get_all_companies(self) -> List[Company]:
        """Tüm firmaları getir"""
        return self.session.query(Company).order_by(Company.name).all()

    def create_company(self, data: Dict[str, Any]) -> Company:
        """Yeni firma oluştur"""
        company = Company(**data)
        self.session.add(company)
        self.session.commit()
        self.session.refresh(company)

        # Varsayılan ayarlar oluştur
        settings = CompanySettings(company_id=company.id)
        self.session.add(settings)
        self.session.commit()

        return company

    def update_company(
        self, company_id: int, data: Dict[str, Any]
    ) -> Optional[Company]:
        """Firma güncelle"""
        company = self.session.query(Company).get(company_id)
        if company:
            for key, value in data.items():
                if hasattr(company, key):
                    setattr(company, key, value)
            self.session.commit()
            self.session.refresh(company)
        return company

    # === ADRES İŞLEMLERİ ===

    def get_addresses(self, company_id: int) -> List[CompanyAddress]:
        """Firma adreslerini getir"""
        return (
            self.session.query(CompanyAddress)
            .filter(CompanyAddress.company_id == company_id)
            .all()
        )

    def add_address(self, company_id: int, data: Dict[str, Any]) -> CompanyAddress:
        """Adres ekle"""
        address = CompanyAddress(company_id=company_id, **data)
        self.session.add(address)
        self.session.commit()
        self.session.refresh(address)
        return address

    def update_address(
        self, address_id: int, data: Dict[str, Any]
    ) -> Optional[CompanyAddress]:
        """Adres güncelle"""
        address = self.session.query(CompanyAddress).get(address_id)
        if address:
            for key, value in data.items():
                if hasattr(address, key):
                    setattr(address, key, value)
            self.session.commit()
            self.session.refresh(address)
        return address

    def delete_address(self, address_id: int) -> bool:
        """Adres sil"""
        address = self.session.query(CompanyAddress).get(address_id)
        if address:
            self.session.delete(address)
            self.session.commit()
            return True
        return False

    # === BANKA İŞLEMLERİ ===

    def get_banks(self, company_id: int) -> List[CompanyBank]:
        """Firma banka hesaplarını getir"""
        return (
            self.session.query(CompanyBank)
            .filter(CompanyBank.company_id == company_id)
            .all()
        )

    def add_bank(self, company_id: int, data: Dict[str, Any]) -> CompanyBank:
        """Banka hesabı ekle"""
        bank = CompanyBank(company_id=company_id, **data)
        self.session.add(bank)
        self.session.commit()
        self.session.refresh(bank)
        return bank

    def update_bank(self, bank_id: int, data: Dict[str, Any]) -> Optional[CompanyBank]:
        """Banka hesabı güncelle"""
        bank = self.session.query(CompanyBank).get(bank_id)
        if bank:
            for key, value in data.items():
                if hasattr(bank, key):
                    setattr(bank, key, value)
            self.session.commit()
            self.session.refresh(bank)
        return bank

    def delete_bank(self, bank_id: int) -> bool:
        """Banka hesabı sil"""
        bank = self.session.query(CompanyBank).get(bank_id)
        if bank:
            self.session.delete(bank)
            self.session.commit()
            return True
        return False

    # === YETKİLİ KİŞİLER ===

    def get_contacts(self, company_id: int) -> List[CompanyContact]:
        """Firma yetkili kişilerini getir"""
        return (
            self.session.query(CompanyContact)
            .filter(CompanyContact.company_id == company_id)
            .all()
        )

    def add_contact(self, company_id: int, data: Dict[str, Any]) -> CompanyContact:
        """Yetkili kişi ekle"""
        contact = CompanyContact(company_id=company_id, **data)
        self.session.add(contact)
        self.session.commit()
        self.session.refresh(contact)
        return contact

    def update_contact(
        self, contact_id: int, data: Dict[str, Any]
    ) -> Optional[CompanyContact]:
        """Yetkili kişi güncelle"""
        contact = self.session.query(CompanyContact).get(contact_id)
        if contact:
            for key, value in data.items():
                if hasattr(contact, key):
                    setattr(contact, key, value)
            self.session.commit()
            self.session.refresh(contact)
        return contact

    def delete_contact(self, contact_id: int) -> bool:
        """Yetkili kişi sil"""
        contact = self.session.query(CompanyContact).get(contact_id)
        if contact:
            self.session.delete(contact)
            self.session.commit()
            return True
        return False

    # === AYARLAR ===

    def get_settings(self, company_id: int) -> Optional[CompanySettings]:
        """Firma ayarlarını getir"""
        return (
            self.session.query(CompanySettings)
            .filter(CompanySettings.company_id == company_id)
            .first()
        )

    def update_settings(
        self, company_id: int, data: Dict[str, Any]
    ) -> Optional[CompanySettings]:
        """Firma ayarlarını güncelle"""
        settings = self.get_settings(company_id)
        if not settings:
            # Yoksa oluştur
            settings = CompanySettings(company_id=company_id, **data)
            self.session.add(settings)
        else:
            for key, value in data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)

        self.session.commit()
        self.session.refresh(settings)
        return settings

    # === DÖKÜMANLAR ===

    def get_documents(self, company_id: int) -> List[CompanyDocument]:
        """Firma dökümanlarını getir"""
        return (
            self.session.query(CompanyDocument)
            .filter(
                CompanyDocument.company_id == company_id,
                CompanyDocument.is_active == True,  # noqa: E712
            )
            .all()
        )

    def get_document(self, company_id: int, doc_type: str) -> Optional[CompanyDocument]:
        """Belirli tipte döküman getir (logo, stamp, vs)"""
        return (
            self.session.query(CompanyDocument)
            .filter(
                CompanyDocument.company_id == company_id,
                CompanyDocument.doc_type == doc_type,
                CompanyDocument.is_active == True,  # noqa: E712
            )
            .first()
        )

    def save_document(
        self, company_id: int, doc_type: str, file_path: str, file_name: str
    ) -> CompanyDocument:
        """Döküman kaydet (mevcut varsa güncelle)"""
        doc = self.get_document(company_id, doc_type)

        if doc:
            doc.file_path = file_path
            doc.file_name = file_name
        else:
            doc = CompanyDocument(
                company_id=company_id,
                doc_type=doc_type,
                file_path=file_path,
                file_name=file_name,
            )
            self.session.add(doc)

        self.session.commit()
        self.session.refresh(doc)
        return doc

    def delete_document(self, doc_id: int) -> bool:
        """Döküman sil"""
        doc = self.session.query(CompanyDocument).get(doc_id)
        if doc:
            doc.is_active = False
            self.session.commit()
            return True
        return False
