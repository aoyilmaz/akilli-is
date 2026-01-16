"""
Akıllı İş - Veritabanı Bağlantısı ve Base Model
"""

from datetime import datetime
from typing import Any
from sqlalchemy import create_engine, Column, Integer, DateTime, Boolean, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session, scoped_session
from sqlalchemy.pool import QueuePool

from config import get_database_url

# Base model
Base = declarative_base()

# Engine ve Session (singleton)
_engine = None
_SessionFactory = None
_ScopedSession = None


def get_engine():
    """Veritabanı engine'i döndürür (singleton)"""
    global _engine
    if _engine is None:
        _engine = create_engine(
            get_database_url(),
            poolclass=QueuePool,
            pool_size=20,  # Artırıldı: 5 -> 20
            max_overflow=30,  # Artırıldı: 10 -> 30
            pool_timeout=60,  # Artırıldı: 30 -> 60
            pool_recycle=1800,
            pool_pre_ping=True,  # Bağlantı sağlığını kontrol et
            echo=False,
        )
    return _engine


def get_session() -> Session:
    """Yeni bir veritabanı session'ı döndürür (scoped)"""
    global _SessionFactory, _ScopedSession
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,  # Commit sonrası objeleri expire etme
        )
        _ScopedSession = scoped_session(_SessionFactory)
    return _ScopedSession()


# Geriye dönük uyumluluk için alias
SessionLocal = get_session


def init_database():
    """Veritabanı tablolarını oluşturur"""
    # Tüm modelleri import et
    from database.models import user, inventory, common

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("✓ Veritabanı tabloları oluşturuldu")

    # Varsayılan verileri ekle
    _create_default_data()


def _create_default_data():
    """Varsayılan verileri oluşturur"""
    session = get_session()

    try:
        from database.models.common import Currency
        from database.models.inventory import Unit
        from database.models.user import Role, Permission

        # Para birimleri
        currencies = [
            {"code": "TRY", "name": "Türk Lirası", "symbol": "₺", "is_default": True},
            {
                "code": "USD",
                "name": "Amerikan Doları",
                "symbol": "$",
                "is_default": False,
            },
            {"code": "EUR", "name": "Euro", "symbol": "€", "is_default": False},
            {
                "code": "GBP",
                "name": "İngiliz Sterlini",
                "symbol": "£",
                "is_default": False,
            },
        ]

        for curr_data in currencies:
            exists = (
                session.query(Currency)
                .filter(Currency.code == curr_data["code"])
                .first()
            )
            if not exists:
                session.add(Currency(**curr_data))

        # Birimler
        units = [
            {"code": "ADET", "name": "Adet"},
            {"code": "KG", "name": "Kilogram"},
            {"code": "GR", "name": "Gram"},
            {"code": "TON", "name": "Ton"},
            {"code": "LT", "name": "Litre"},
            {"code": "ML", "name": "Mililitre"},
            {"code": "MT", "name": "Metre"},
            {"code": "CM", "name": "Santimetre"},
            {"code": "MM", "name": "Milimetre"},
            {"code": "M2", "name": "Metrekare"},
            {"code": "M3", "name": "Metreküp"},
            {"code": "RULO", "name": "Rulo"},
            {"code": "PAKET", "name": "Paket"},
            {"code": "KUTU", "name": "Kutu"},
            {"code": "KOLI", "name": "Koli"},
            {"code": "PALET", "name": "Palet"},
        ]

        for unit_data in units:
            exists = session.query(Unit).filter(Unit.code == unit_data["code"]).first()
            if not exists:
                session.add(Unit(**unit_data))

        # Roller
        roles = [
            {
                "code": "ADMIN",
                "name": "Sistem Yöneticisi",
                "description": "Tüm yetkilere sahip",
            },
            {"code": "MANAGER", "name": "Yönetici", "description": "Yönetim yetkileri"},
            {
                "code": "ACCOUNTANT",
                "name": "Muhasebeci",
                "description": "Finans ve muhasebe yetkileri",
            },
            {
                "code": "WAREHOUSE",
                "name": "Depocu",
                "description": "Stok yönetimi yetkileri",
            },
            {
                "code": "SALES",
                "name": "Satış Temsilcisi",
                "description": "Satış yetkileri",
            },
            {
                "code": "PURCHASE",
                "name": "Satın Alma",
                "description": "Satın alma yetkileri",
            },
            {"code": "PRODUCTION", "name": "Üretim", "description": "Üretim yetkileri"},
            {
                "code": "VIEWER",
                "name": "İzleyici",
                "description": "Sadece görüntüleme yetkisi",
            },
        ]

        for role_data in roles:
            exists = session.query(Role).filter(Role.code == role_data["code"]).first()
            if not exists:
                session.add(Role(**role_data))

        # İzinler
        permissions = [
            # Stok izinleri
            {
                "code": "inventory.view",
                "name": "Stok Görüntüleme",
                "module": "inventory",
            },
            {"code": "inventory.create", "name": "Stok Ekleme", "module": "inventory"},
            {"code": "inventory.edit", "name": "Stok Düzenleme", "module": "inventory"},
            {"code": "inventory.delete", "name": "Stok Silme", "module": "inventory"},
            {
                "code": "inventory.movement",
                "name": "Stok Hareketi",
                "module": "inventory",
            },
            # Satış izinleri
            {"code": "sales.view", "name": "Satış Görüntüleme", "module": "sales"},
            {"code": "sales.create", "name": "Satış Oluşturma", "module": "sales"},
            {"code": "sales.edit", "name": "Satış Düzenleme", "module": "sales"},
            {"code": "sales.delete", "name": "Satış Silme", "module": "sales"},
            # Satın alma izinleri
            {
                "code": "purchase.view",
                "name": "Satın Alma Görüntüleme",
                "module": "purchase",
            },
            {
                "code": "purchase.create",
                "name": "Satın Alma Oluşturma",
                "module": "purchase",
            },
            {
                "code": "purchase.edit",
                "name": "Satın Alma Düzenleme",
                "module": "purchase",
            },
            {
                "code": "purchase.delete",
                "name": "Satın Alma Silme",
                "module": "purchase",
            },
            # Finans izinleri
            {"code": "finance.view", "name": "Finans Görüntüleme", "module": "finance"},
            {"code": "finance.create", "name": "Finans İşlemi", "module": "finance"},
            {"code": "finance.edit", "name": "Finans Düzenleme", "module": "finance"},
            {"code": "finance.delete", "name": "Finans Silme", "module": "finance"},
            # Üretim izinleri
            {
                "code": "production.view",
                "name": "Üretim Görüntüleme",
                "module": "production",
            },
            {
                "code": "production.create",
                "name": "Üretim Oluşturma",
                "module": "production",
            },
            {
                "code": "production.edit",
                "name": "Üretim Düzenleme",
                "module": "production",
            },
            {
                "code": "production.delete",
                "name": "Üretim Silme",
                "module": "production",
            },
            # Rapor izinleri
            {"code": "reports.view", "name": "Rapor Görüntüleme", "module": "reports"},
            {
                "code": "reports.export",
                "name": "Rapor Dışa Aktarma",
                "module": "reports",
            },
            # Sistem izinleri
            {"code": "system.settings", "name": "Sistem Ayarları", "module": "system"},
            {"code": "system.users", "name": "Kullanıcı Yönetimi", "module": "system"},
            {"code": "system.backup", "name": "Yedekleme", "module": "system"},
        ]

        for perm_data in permissions:
            exists = (
                session.query(Permission)
                .filter(Permission.code == perm_data["code"])
                .first()
            )
            if not exists:
                session.add(Permission(**perm_data))

        session.commit()
        print("✓ Varsayılan veriler oluşturuldu")

    except Exception as e:
        session.rollback()
        print(f"✗ Varsayılan veri hatası: {e}")
    finally:
        session.close()


class BaseModel(Base):
    """Tüm modeller için temel sınıf"""

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)

    def to_dict(self) -> dict:
        """Model'i dictionary'e çevirir"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"


class TimestampMixin:
    """Zaman damgası mixin'i"""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class SoftDeleteMixin:
    """Soft delete mixin'i"""

    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
