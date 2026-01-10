"""
Akıllı İş - Muhasebe Modülü Veritabanı Modelleri

Türkiye Tekdüzen Hesap Planı'na uygun muhasebe modeli.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    Date,
    DateTime,
    Numeric,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from database.base import Base


class AccountType(str, Enum):
    """Hesap türleri"""

    ASSET = "asset"  # 1-2 Dönen/Duran Varlıklar
    LIABILITY = "liability"  # 3-4 Kısa/Uzun Vadeli Borçlar
    EQUITY = "equity"  # 5 Özkaynaklar
    REVENUE = "revenue"  # 6 Gelirler
    EXPENSE = "expense"  # 7 Giderler
    COST = "cost"  # 7 Maliyet Hesapları


class JournalEntryStatus(str, Enum):
    """Yevmiye durumları"""

    DRAFT = "draft"  # Taslak
    POSTED = "posted"  # Deftere işlendi
    CANCELLED = "cancelled"  # İptal edildi


class Account(Base):
    """
    Hesap Planı

    Tekdüzen Hesap Planı yapısına uygun hiyerarşik hesap kartları.
    Örnek: 100 Kasa, 120 Alıcılar, 320 Satıcılar
    """

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)

    # Hesap kodu (100, 120.01, 600.01.001)
    code = Column(String(20), unique=True, nullable=False, index=True)

    # Hesap adı
    name = Column(String(200), nullable=False)

    # Hesap türü
    account_type = Column(
        SQLEnum(AccountType), nullable=False, default=AccountType.ASSET
    )

    # Üst hesap (hiyerarşi için)
    parent_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    parent = relationship("Account", remote_side=[id], backref="children")

    # Hesap seviyesi (1=Ana grup, 2=Alt grup, 3=Detay)
    level = Column(Integer, default=1)

    # Pasif/aktif durumu
    is_active = Column(Boolean, default=True)

    # Bakiye kaydı için mi? (Alt hesabı olmayan)
    is_detail = Column(Boolean, default=True)

    # Açılış bakiyeleri
    opening_debit = Column(Numeric(18, 2), default=Decimal("0"))
    opening_credit = Column(Numeric(18, 2), default=Decimal("0"))

    # Açıklama
    description = Column(Text, nullable=True)

    # Zaman damgaları
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # İlişkiler
    journal_lines = relationship("JournalEntryLine", back_populates="account")

    __table_args__ = (
        Index("idx_account_type", "account_type"),
        Index("idx_account_parent", "parent_id"),
    )

    def __repr__(self):
        return f"<Account {self.code} - {self.name}>"

    @property
    def full_name(self) -> str:
        """Tam hesap adı (kod + ad)"""
        return f"{self.code} - {self.name}"

    @property
    def balance(self) -> Decimal:
        """Güncel bakiye hesapla"""
        debit = sum(
            line.debit or Decimal(0)
            for line in self.journal_lines
            if line.journal_entry.status == JournalEntryStatus.POSTED
        )
        credit = sum(
            line.credit or Decimal(0)
            for line in self.journal_lines
            if line.journal_entry.status == JournalEntryStatus.POSTED
        )

        # Varlık ve gider hesapları: Borç - Alacak
        # Borç, özkaynak ve gelir hesapları: Alacak - Borç
        if self.account_type in [
            AccountType.ASSET,
            AccountType.EXPENSE,
            AccountType.COST,
        ]:
            return (self.opening_debit - self.opening_credit) + (debit - credit)
        else:
            return (self.opening_credit - self.opening_debit) + (credit - debit)


class FiscalPeriod(Base):
    """
    Mali Dönem

    Aylık dönem kapanışları için.
    """

    __tablename__ = "fiscal_periods"

    id = Column(Integer, primary_key=True)

    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    # Dönem adı
    name = Column(String(50))  # "Ocak 2026"

    # Kapanış durumu
    is_closed = Column(Boolean, default=False)
    closed_at = Column(DateTime, nullable=True)
    closed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (Index("idx_fiscal_year_month", "year", "month", unique=True),)


class JournalEntry(Base):
    """
    Yevmiye Fişi

    Çift taraflı kayıt sistemi. Her fişte toplam borç = toplam alacak olmalı.
    """

    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True)

    # Fiş numarası (YV-2026-00001)
    entry_no = Column(String(30), unique=True, nullable=False, index=True)

    # Fiş tarihi
    entry_date = Column(Date, nullable=False, default=date.today)

    # Açıklama
    description = Column(Text, nullable=True)

    # Referans belgesi
    reference_type = Column(
        String(50), nullable=True
    )  # invoice, receipt, payment, manual
    reference_id = Column(Integer, nullable=True)
    reference_no = Column(String(50), nullable=True)

    # Durum
    status = Column(
        SQLEnum(JournalEntryStatus), nullable=False, default=JournalEntryStatus.DRAFT
    )

    # İşlem bilgileri
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    posted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    posted_at = Column(DateTime, nullable=True)

    cancelled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancel_reason = Column(Text, nullable=True)

    # İlişkiler
    lines = relationship(
        "JournalEntryLine",
        back_populates="journal_entry",
        cascade="all, delete-orphan",
        order_by="JournalEntryLine.line_order",
    )

    __table_args__ = (
        Index("idx_journal_date", "entry_date"),
        Index("idx_journal_status", "status"),
        Index("idx_journal_ref", "reference_type", "reference_id"),
    )

    def __repr__(self):
        return f"<JournalEntry {self.entry_no}>"

    @property
    def total_debit(self) -> Decimal:
        """Toplam borç"""
        return sum(line.debit or Decimal(0) for line in self.lines)

    @property
    def total_credit(self) -> Decimal:
        """Toplam alacak"""
        return sum(line.credit or Decimal(0) for line in self.lines)

    @property
    def is_balanced(self) -> bool:
        """Borç = Alacak mı?"""
        return self.total_debit == self.total_credit


class JournalEntryLine(Base):
    """
    Yevmiye Satırı

    Her satır ya borç ya da alacak içerir (ikisi birden değil).
    """

    __tablename__ = "journal_entry_lines"

    id = Column(Integer, primary_key=True)

    # Bağlı fiş
    journal_entry_id = Column(
        Integer, ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False
    )
    journal_entry = relationship("JournalEntry", back_populates="lines")

    # Hesap
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    account = relationship("Account", back_populates="journal_lines")

    # Tutar (biri 0 olmalı)
    debit = Column(Numeric(18, 2), default=Decimal("0"))
    credit = Column(Numeric(18, 2), default=Decimal("0"))

    # Satır açıklaması
    description = Column(String(500), nullable=True)

    # Sıra numarası
    line_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_jel_entry", "journal_entry_id"),
        Index("idx_jel_account", "account_id"),
    )

    def __repr__(self):
        return f"<JournalEntryLine {self.account.code if self.account else '?'} B:{self.debit} A:{self.credit}>"
