"""
Akıllı İş - Ortak Tablolar
"""

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, Boolean,
    DateTime, Date, ForeignKey, Index
)
from sqlalchemy.orm import relationship

from database.base import Base, BaseModel


class Currency(BaseModel):
    """Para birimleri tablosu"""
    __tablename__ = 'currencies'
    
    code = Column(String(3), unique=True, nullable=False, index=True)  # TRY, USD, EUR
    name = Column(String(100), nullable=False)
    symbol = Column(String(10), nullable=False)  # ₺, $, €
    decimal_places = Column(Integer, default=2)
    is_default = Column(Boolean, default=False)
    
    # Format
    thousand_separator = Column(String(1), default='.')
    decimal_separator = Column(String(1), default=',')
    symbol_position = Column(String(10), default='after')  # before, after
    
    # İlişkiler
    items = relationship("Item", back_populates="currency")
    exchange_rates = relationship("ExchangeRate", back_populates="currency")
    
    def format_amount(self, amount: Decimal) -> str:
        """Tutarı formatla"""
        formatted = f"{amount:,.{self.decimal_places}f}"
        formatted = formatted.replace(',', 'X').replace('.', self.decimal_separator).replace('X', self.thousand_separator)
        
        if self.symbol_position == 'before':
            return f"{self.symbol}{formatted}"
        return f"{formatted} {self.symbol}"
    
    def __repr__(self):
        return f"<Currency(code={self.code}, name={self.name})>"


class ExchangeRate(BaseModel):
    """Döviz kurları tablosu"""
    __tablename__ = 'exchange_rates'
    
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    rate_date = Column(Date, nullable=False, index=True)
    
    # Kurlar (TRY bazlı)
    buying_rate = Column(Numeric(18, 6), nullable=False)  # Alış kuru
    selling_rate = Column(Numeric(18, 6), nullable=False)  # Satış kuru
    effective_rate = Column(Numeric(18, 6), nullable=True)  # Efektif kur
    
    # Kaynak
    source = Column(String(50), default='TCMB')  # TCMB, manual
    
    # İlişkiler
    currency = relationship("Currency", back_populates="exchange_rates")
    
    # Unique constraint
    __table_args__ = (
        Index('idx_exchange_currency_date', 'currency_id', 'rate_date', unique=True),
    )
    
    def __repr__(self):
        return f"<ExchangeRate(currency={self.currency_id}, date={self.rate_date}, rate={self.buying_rate})>"


class Country(Base):
    """Ülkeler tablosu"""
    __tablename__ = 'countries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(3), unique=True, nullable=False, index=True)  # TR, US, DE
    name = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=True)
    phone_code = Column(String(10), nullable=True)  # +90
    is_active = Column(Boolean, default=True)
    
    # İlişkiler
    cities = relationship("City", back_populates="country")
    
    def __repr__(self):
        return f"<Country(code={self.code}, name={self.name})>"


class City(Base):
    """Şehirler tablosu"""
    __tablename__ = 'cities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    country_id = Column(Integer, ForeignKey('countries.id'), nullable=False)
    code = Column(String(10), nullable=True)  # Plaka kodu
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # İlişkiler
    country = relationship("Country", back_populates="cities")
    districts = relationship("District", back_populates="city")
    
    # Index
    __table_args__ = (
        Index('idx_city_country', 'country_id'),
    )
    
    def __repr__(self):
        return f"<City(name={self.name})>"


class District(Base):
    """İlçeler tablosu"""
    __tablename__ = 'districts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(Integer, ForeignKey('cities.id'), nullable=False)
    name = Column(String(100), nullable=False)
    postal_code = Column(String(10), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # İlişkiler
    city = relationship("City", back_populates="districts")
    
    # Index
    __table_args__ = (
        Index('idx_district_city', 'city_id'),
    )
    
    def __repr__(self):
        return f"<District(name={self.name})>"


class Attachment(BaseModel):
    """Dosya ekleri tablosu (tüm modüller için)"""
    __tablename__ = 'attachments'
    
    # Hangi kayda ait
    module = Column(String(50), nullable=False, index=True)  # inventory, sales, purchase
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=False)
    
    # Dosya bilgileri
    file_name = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # Byte
    mime_type = Column(String(100), nullable=True)
    file_extension = Column(String(20), nullable=True)
    
    # Açıklama
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    
    # Kim yükledi
    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Index
    __table_args__ = (
        Index('idx_attachment_record', 'module', 'table_name', 'record_id'),
    )
    
    def __repr__(self):
        return f"<Attachment(module={self.module}, file={self.file_name})>"


class Note(BaseModel):
    """Notlar tablosu (tüm modüller için)"""
    __tablename__ = 'notes'
    
    # Hangi kayda ait
    module = Column(String(50), nullable=False, index=True)
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=False)
    
    # Not içeriği
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default='general')  # general, warning, info, reminder
    
    # Hatırlatma
    reminder_date = Column(DateTime, nullable=True)
    is_reminder_sent = Column(Boolean, default=False)
    
    # Kim yazdı
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Index
    __table_args__ = (
        Index('idx_note_record', 'module', 'table_name', 'record_id'),
        Index('idx_note_reminder', 'reminder_date', 'is_reminder_sent'),
    )
    
    def __repr__(self):
        return f"<Note(module={self.module}, record_id={self.record_id})>"
