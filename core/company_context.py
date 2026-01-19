"""
Akıllı İş - Firma Context Servisi
Uygulama genelinde aktif firmayı yönetir
"""

from typing import Optional
from database.base import get_session
from database.models.company import Company, CompanySettings


class CompanyContext:
    """
    Singleton firma context - uygulama genelinde aktif firmayı tutar
    """

    _instance = None
    _company: Optional[Company] = None
    _settings: Optional[CompanySettings] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._company is None:
            self._load_default_company()

    def _load_default_company(self):
        """Varsayılan (ilk aktif) firmayı yükle"""
        session = get_session()
        try:
            self._company = (
                session.query(Company)
                .filter(Company.is_active == True)  # noqa: E712
                .first()
            )
            if self._company:
                self._settings = (
                    session.query(CompanySettings)
                    .filter(CompanySettings.company_id == self._company.id)
                    .first()
                )
        finally:
            session.close()

    def set_company(self, company_id: int):
        """Aktif firmayı değiştir"""
        session = get_session()
        try:
            self._company = session.query(Company).get(company_id)
            if self._company:
                self._settings = (
                    session.query(CompanySettings)
                    .filter(CompanySettings.company_id == company_id)
                    .first()
                )
        finally:
            session.close()

    def refresh(self):
        """Firma bilgilerini yeniden yükle"""
        if self._company:
            self.set_company(self._company.id)
        else:
            self._load_default_company()

    @property
    def company(self) -> Optional[Company]:
        """Aktif firma"""
        return self._company

    @property
    def settings(self) -> Optional[CompanySettings]:
        """Aktif firma ayarları"""
        return self._settings

    @property
    def company_id(self) -> Optional[int]:
        """Aktif firma ID"""
        return self._company.id if self._company else None

    # === KISA ERIŞIM METODLARI ===

    @property
    def name(self) -> str:
        """Firma adı"""
        return self._company.name if self._company else ""

    @property
    def legal_name(self) -> str:
        """Ticari ünvan"""
        if self._company and self._company.legal_name:
            return self._company.legal_name
        return self.name

    @property
    def tax_office(self) -> str:
        """Vergi dairesi"""
        return self._company.tax_office if self._company else ""

    @property
    def tax_number(self) -> str:
        """Vergi no"""
        return self._company.tax_number if self._company else ""

    @property
    def phone(self) -> str:
        """Telefon"""
        return self._company.phone if self._company else ""

    @property
    def email(self) -> str:
        """E-posta"""
        return self._company.email if self._company else ""

    @property
    def website(self) -> str:
        """Web sitesi"""
        return self._company.website if self._company else ""

    # === AYAR KISA ERİŞİMLERİ ===

    @property
    def currency(self) -> str:
        """Para birimi"""
        return self._settings.currency if self._settings else "TRY"

    @property
    def default_vat_rate(self) -> float:
        """Varsayılan KDV oranı"""
        if self._settings and self._settings.default_vat_rate:
            return float(self._settings.default_vat_rate)
        return 20.0

    @property
    def invoice_prefix(self) -> str:
        """Fatura numarası öneki"""
        return self._settings.invoice_prefix if self._settings else "FTR"

    @property
    def order_prefix(self) -> str:
        """Sipariş numarası öneki"""
        return self._settings.order_prefix if self._settings else "SIP"

    @property
    def delivery_prefix(self) -> str:
        """İrsaliye numarası öneki"""
        return self._settings.delivery_prefix if self._settings else "IRS"

    @property
    def purchase_prefix(self) -> str:
        """Satınalma numarası öneki"""
        return self._settings.purchase_prefix if self._settings else "SAT"

    @property
    def has_lot_tracking(self) -> bool:
        """Lot takibi aktif mi"""
        return self._settings.has_lot_tracking if self._settings else False

    @property
    def has_serial_tracking(self) -> bool:
        """Seri takibi aktif mi"""
        return self._settings.has_serial_tracking if self._settings else False

    # === ADRES VE BANKA BİLGİLERİ ===

    def get_default_address(self) -> dict:
        """Varsayılan adresi döndür"""
        if not self._company:
            return {}

        from database.models.company import CompanyAddress

        session = get_session()
        try:
            addr = (
                session.query(CompanyAddress)
                .filter(
                    CompanyAddress.company_id == self._company.id,
                    CompanyAddress.is_default == True,  # noqa: E712
                )
                .first()
            )
            if not addr:
                addr = (
                    session.query(CompanyAddress)
                    .filter(CompanyAddress.company_id == self._company.id)
                    .first()
                )
            if addr:
                return {
                    "city": addr.city or "",
                    "district": addr.district or "",
                    "address": addr.address or "",
                    "postal_code": addr.postal_code or "",
                    "country": addr.country or "Türkiye",
                    "full": f"{addr.address}, {addr.district}/{addr.city}",
                }
        finally:
            session.close()
        return {}

    def get_default_bank(self) -> dict:
        """Varsayılan banka hesabını döndür"""
        if not self._company:
            return {}

        from database.models.company import CompanyBank

        session = get_session()
        try:
            bank = (
                session.query(CompanyBank)
                .filter(
                    CompanyBank.company_id == self._company.id,
                    CompanyBank.is_default == True,  # noqa: E712
                )
                .first()
            )
            if not bank:
                bank = (
                    session.query(CompanyBank)
                    .filter(CompanyBank.company_id == self._company.id)
                    .first()
                )
            if bank:
                return {
                    "bank_name": bank.bank_name or "",
                    "branch": bank.branch or "",
                    "account_holder": bank.account_holder or "",
                    "iban": bank.iban or "",
                    "account_no": bank.account_no or "",
                }
        finally:
            session.close()
        return {}

    def get_logo_path(self) -> str:
        """Firma logo dosya yolunu döndür"""
        if not self._company:
            return ""

        from database.models.company import CompanyDocument

        session = get_session()
        try:
            doc = (
                session.query(CompanyDocument)
                .filter(
                    CompanyDocument.company_id == self._company.id,
                    CompanyDocument.doc_type == "logo",
                    CompanyDocument.is_active == True,  # noqa: E712
                )
                .first()
            )
            if doc and doc.file_path:
                return doc.file_path
        finally:
            session.close()
        return ""


# === GLOBAL ERİŞİM FONKSİYONLARI ===

_context: Optional[CompanyContext] = None


def get_company_context() -> CompanyContext:
    """Firma context singleton'ını döndür"""
    global _context
    if _context is None:
        _context = CompanyContext()
    return _context


def get_active_company() -> Optional[Company]:
    """Aktif firmayı döndür"""
    return get_company_context().company


def get_company_settings() -> Optional[CompanySettings]:
    """Aktif firma ayarlarını döndür"""
    return get_company_context().settings


def get_company_id() -> Optional[int]:
    """Aktif firma ID döndür"""
    return get_company_context().company_id


def set_active_company(company_id: int):
    """Aktif firmayı değiştir"""
    get_company_context().set_company(company_id)


def refresh_company_context():
    """Firma bilgilerini yeniden yükle"""
    get_company_context().refresh()
