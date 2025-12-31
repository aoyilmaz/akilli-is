"""
Akıllı İş - Veritabanı Bağlantısı ve Base Model
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import QueuePool

from config.settings import get_database_url

# Base model
Base = declarative_base()

# Engine ve Session
_engine = None
_SessionLocal = None


def get_engine():
    """Veritabanı engine'i döndürür (singleton)"""
    global _engine
    if _engine is None:
        _engine = create_engine(
            get_database_url(),
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            echo=False  # SQL logları için True yap
        )
    return _engine


def get_session() -> Session:
    """Yeni bir veritabanı session'ı döndürür"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False
        )
    return _SessionLocal()


def init_database():
    """Veritabanı tablolarını oluşturur"""
    from database.models import *  # Tüm modelleri import et
    Base.metadata.create_all(bind=get_engine())
    print("✓ Veritabanı tabloları oluşturuldu")


class BaseModel(Base):
    """Tüm modeller için temel sınıf"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def to_dict(self) -> dict:
        """Model'i dictionary'e çevirir"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
