"""
Akıllı İş - Muhasebe Servisleri
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Optional
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database.base import get_session
from database.models.accounting import (
    Account,
    AccountType,
    JournalEntry,
    JournalEntryLine,
    JournalEntryStatus,
)
from database.models.sales import Invoice, InvoiceStatus
from database.models.purchasing import (
    PurchaseInvoice,
    PurchaseInvoiceStatus,
)
from modules.inventory.services import ServiceBase


class AccountingService(ServiceBase):
    """Muhasebe servisi"""

    def __init__(self):
        super().__init__()
        self.session: Session = get_session()

    # =====================
    # HESAP PLANI
    # =====================

    def get_all_accounts(self, active_only: bool = True) -> List[Account]:
        """Tüm hesapları getir"""
        query = self.session.query(Account)
        if active_only:
            query = query.filter(Account.is_active == True)
        return query.order_by(Account.code).all()

    def get_account_tree(self) -> List[Dict]:
        """Hiyerarşik hesap ağacı"""
        accounts = self.get_all_accounts()

        # Kök hesapları bul (parent_id = None)
        root_accounts = [a for a in accounts if a.parent_id is None]

        def build_tree(account):
            children = [a for a in accounts if a.parent_id == account.id]
            return {
                "id": account.id,
                "code": account.code,
                "name": account.name,
                "account_type": account.account_type.value,
                "level": account.level,
                "is_detail": account.is_detail,
                "children": [build_tree(c) for c in children],
            }

        return [build_tree(a) for a in root_accounts]

    def get_account_by_id(self, account_id: int) -> Optional[Account]:
        """ID ile hesap getir"""
        return self.session.query(Account).get(account_id)

    def get_account_by_code(self, code: str) -> Optional[Account]:
        """Kod ile hesap getir"""
        return self.session.query(Account).filter(Account.code == code).first()

    def create_account(self, data: Dict) -> Account:
        """Yeni hesap oluştur"""
        account = Account(**data)
        self.session.add(account)
        self.session.commit()
        return account

    def update_account(self, account_id: int, data: Dict) -> Account:
        """Hesap güncelle"""
        account = self.get_account_by_id(account_id)
        if account:
            for key, value in data.items():
                if hasattr(account, key):
                    setattr(account, key, value)
            self.session.commit()
        return account

    def delete_account(self, account_id: int) -> bool:
        """Hesap sil (hareketi yoksa)"""
        account = self.get_account_by_id(account_id)
        if account:
            # Hareket kontrolü
            line_count = (
                self.session.query(JournalEntryLine)
                .filter(JournalEntryLine.account_id == account_id)
                .count()
            )
            if line_count > 0:
                return False

            self.session.delete(account)
            self.session.commit()
            return True
        return False

    # =====================
    # YEVMİYE FİŞİ
    # =====================

    def get_all_journals(
        self,
        start_date: date = None,
        end_date: date = None,
        status: JournalEntryStatus = None,
        limit: int = 100,
    ) -> List[JournalEntry]:
        """Yevmiye fişlerini getir"""
        query = self.session.query(JournalEntry)

        if start_date:
            query = query.filter(JournalEntry.entry_date >= start_date)
        if end_date:
            query = query.filter(JournalEntry.entry_date <= end_date)
        if status:
            query = query.filter(JournalEntry.status == status)

        return (
            query.order_by(desc(JournalEntry.entry_date), desc(JournalEntry.entry_no))
            .limit(limit)
            .all()
        )

    def get_journal_by_id(self, journal_id: int) -> Optional[JournalEntry]:
        """ID ile yevmiye getir"""
        return self.session.query(JournalEntry).get(journal_id)

    def generate_journal_no(self) -> str:
        """Yevmiye numarası oluştur"""
        year = date.today().year
        prefix = f"YV-{year}-"

        last = (
            self.session.query(JournalEntry)
            .filter(JournalEntry.entry_no.like(f"{prefix}%"))
            .order_by(desc(JournalEntry.entry_no))
            .first()
        )

        if last:
            try:
                last_num = int(last.entry_no.replace(prefix, ""))
                return f"{prefix}{last_num + 1:05d}"
            except ValueError:
                pass

        return f"{prefix}00001"

    def create_journal(self, lines_data: List[Dict], **data) -> JournalEntry:
        """Yevmiye fişi oluştur"""
        # Numara ata
        data["entry_no"] = self.generate_journal_no()

        # Fiş oluştur
        journal = JournalEntry(**data)
        self.session.add(journal)
        self.session.flush()

        # Satırları ekle
        for i, line_data in enumerate(lines_data):
            # account_code varsa id'ye çevir
            if "account_code" in line_data:
                code = line_data.pop("account_code")
                account = self.get_account_by_code(code)
                if account:
                    line_data["account_id"] = account.id
                else:
                    # Hesap bulunamazsa sessizce devam et veya hata fırlat
                    # Şimdilik sessizce logluyoruz (modül bazlı)
                    print(f"[Muhasebe] Hesap bulunamadı: {code}")
                    continue

            line = JournalEntryLine(
                journal_entry_id=journal.id, line_order=i, **line_data
            )
            self.session.add(line)

        self.session.commit()
        return journal

    def post_journal(self, journal_id: int, user_id: int = None) -> bool:
        """Yevmiye fişini deftere işle"""
        journal = self.get_journal_by_id(journal_id)
        if not journal:
            return False

        if journal.status != JournalEntryStatus.DRAFT:
            return False

        # Borç = Alacak kontrolü
        if not journal.is_balanced:
            raise ValueError("Borç ve alacak toplamları eşit değil!")

        journal.status = JournalEntryStatus.POSTED
        journal.posted_by = user_id
        journal.posted_at = datetime.now()
        self.session.commit()
        return True

    def cancel_journal(self, journal_id: int, reason: str, user_id: int = None) -> bool:
        """Yevmiye fişini iptal et"""
        journal = self.get_journal_by_id(journal_id)
        if not journal:
            return False

        if journal.status == JournalEntryStatus.CANCELLED:
            return False

        journal.status = JournalEntryStatus.CANCELLED
        journal.cancelled_by = user_id
        journal.cancelled_at = datetime.now()
        journal.cancel_reason = reason
        self.session.commit()
        return True

    # =====================
    # RAPORLAR
    # =====================

    def get_ledger(
        self, account_id: int, start_date: date = None, end_date: date = None
    ) -> Dict:
        """Büyük defter (hesap ekstresı)"""
        account = self.get_account_by_id(account_id)
        if not account:
            return {}

        query = (
            self.session.query(JournalEntryLine)
            .join(JournalEntry)
            .filter(
                JournalEntryLine.account_id == account_id,
                JournalEntry.status == JournalEntryStatus.POSTED,
            )
        )

        if start_date:
            query = query.filter(JournalEntry.entry_date >= start_date)
        if end_date:
            query = query.filter(JournalEntry.entry_date <= end_date)

        lines = query.order_by(JournalEntry.entry_date, JournalEntry.entry_no).all()

        # Açılış bakiyesi
        opening = account.opening_debit - account.opening_credit
        if start_date:
            # Önceki dönem hareketlerini hesapla
            prev_lines = (
                self.session.query(JournalEntryLine)
                .join(JournalEntry)
                .filter(
                    JournalEntryLine.account_id == account_id,
                    JournalEntry.status == JournalEntryStatus.POSTED,
                    JournalEntry.entry_date < start_date,
                )
                .all()
            )
            for pl in prev_lines:
                opening += (pl.debit or 0) - (pl.credit or 0)

        # Hareket listesi
        movements = []
        running_balance = opening
        for line in lines:
            debit = line.debit or Decimal(0)
            credit = line.credit or Decimal(0)
            running_balance += debit - credit

            movements.append(
                {
                    "date": line.journal_entry.entry_date,
                    "entry_no": line.journal_entry.entry_no,
                    "description": line.description or line.journal_entry.description,
                    "debit": float(debit),
                    "credit": float(credit),
                    "balance": float(running_balance),
                }
            )

        return {
            "account": {
                "id": account.id,
                "code": account.code,
                "name": account.name,
            },
            "opening_balance": float(opening),
            "movements": movements,
            "closing_balance": float(running_balance),
            "total_debit": sum(m["debit"] for m in movements),
            "total_credit": sum(m["credit"] for m in movements),
        }

    def get_trial_balance(self, as_of_date: date = None) -> Dict:
        """Mizan raporu"""
        if not as_of_date:
            as_of_date = date.today()

        accounts = self.get_all_accounts()
        rows = []

        total_debit = Decimal(0)
        total_credit = Decimal(0)

        for account in accounts:
            # Sadece detay hesapları
            if not account.is_detail:
                continue

            # Açılış
            opening_d = account.opening_debit or Decimal(0)
            opening_c = account.opening_credit or Decimal(0)

            # Dönem hareketleri
            lines = (
                self.session.query(JournalEntryLine)
                .join(JournalEntry)
                .filter(
                    JournalEntryLine.account_id == account.id,
                    JournalEntry.status == JournalEntryStatus.POSTED,
                    JournalEntry.entry_date <= as_of_date,
                )
                .all()
            )

            period_debit = sum(l.debit or Decimal(0) for l in lines)
            period_credit = sum(l.credit or Decimal(0) for l in lines)

            # Kapanış bakiyesi
            closing_debit = opening_d + period_debit
            closing_credit = opening_c + period_credit

            # Bakiye (borç veya alacak)
            if closing_debit > closing_credit:
                balance_debit = closing_debit - closing_credit
                balance_credit = Decimal(0)
            else:
                balance_debit = Decimal(0)
                balance_credit = closing_credit - closing_debit

            if (
                period_debit > 0
                or period_credit > 0
                or balance_debit > 0
                or balance_credit > 0
            ):
                rows.append(
                    {
                        "code": account.code,
                        "name": account.name,
                        "opening_debit": float(opening_d),
                        "opening_credit": float(opening_c),
                        "period_debit": float(period_debit),
                        "period_credit": float(period_credit),
                        "closing_debit": float(balance_debit),
                        "closing_credit": float(balance_credit),
                    }
                )

                total_debit += balance_debit
                total_credit += balance_credit

        return {
            "as_of_date": as_of_date.isoformat(),
            "rows": rows,
            "totals": {
                "debit": float(total_debit),
                "credit": float(total_credit),
                "balanced": total_debit == total_credit,
            },
        }

    def get_balance_sheet(self, as_of_date: date = None) -> Dict:
        """Bilanço raporu"""
        if not as_of_date:
            as_of_date = date.today()

        def get_group_total(start_code: str) -> Decimal:
            """Belirli kodla başlayan hesapların toplamı"""
            accounts = (
                self.session.query(Account)
                .filter(Account.code.like(f"{start_code}%"))
                .all()
            )

            total = Decimal(0)
            for account in accounts:
                if not account.is_detail:
                    continue

                lines = (
                    self.session.query(JournalEntryLine)
                    .join(JournalEntry)
                    .filter(
                        JournalEntryLine.account_id == account.id,
                        JournalEntry.status == JournalEntryStatus.POSTED,
                        JournalEntry.entry_date <= as_of_date,
                    )
                    .all()
                )

                opening = (account.opening_debit or 0) - (account.opening_credit or 0)
                movements = sum((l.debit or 0) - (l.credit or 0) for l in lines)
                total += opening + movements

            return total

        # Varlıklar (1-2)
        assets = {
            "current": float(get_group_total("1")),  # Dönen
            "fixed": float(get_group_total("2")),  # Duran
        }
        assets["total"] = assets["current"] + assets["fixed"]

        # Borçlar (3-4)
        liabilities = {
            "short_term": float(-get_group_total("3")),  # Kısa vadeli
            "long_term": float(-get_group_total("4")),  # Uzun vadeli
        }
        liabilities["total"] = liabilities["short_term"] + liabilities["long_term"]

        # Özkaynaklar (5)
        equity = float(-get_group_total("5"))

        return {
            "as_of_date": as_of_date.isoformat(),
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "total_liabilities_equity": liabilities["total"] + equity,
            "balanced": abs(assets["total"] - (liabilities["total"] + equity)) < 0.01,
        }

    def get_tax_report(self, start_date: date, end_date: date) -> Dict:
        """KDV Raporu"""

        # 1. Satış Faturaları
        sales_invoices = (
            self.session.query(Invoice)
            .filter(
                Invoice.invoice_date.between(start_date, end_date),
                Invoice.status.notin_([InvoiceStatus.DRAFT, InvoiceStatus.CANCELLED]),
            )
            .all()
        )

        sales_data = {"base": Decimal(0), "tax": Decimal(0), "by_rate": {}}

        for inv in sales_invoices:
            rate = inv.exchange_rate or Decimal(1)

            # Invoice totals
            sales_data["base"] += (inv.subtotal or Decimal(0)) * rate
            sales_data["tax"] += (inv.tax_amount or Decimal(0)) * rate

            # Item breakdown
            if inv.items:
                for item in inv.items:
                    tax_rate = int(item.tax_rate or 0)
                    if tax_rate not in sales_data["by_rate"]:
                        sales_data["by_rate"][tax_rate] = {
                            "base": Decimal(0),
                            "tax": Decimal(0),
                        }

                    # Re-calculate line in base currency
                    qty = item.quantity or Decimal(0)
                    price = item.unit_price or Decimal(0)
                    disc = item.discount_rate or Decimal(0)

                    line_net = qty * price * (1 - disc / 100)
                    line_tax = line_net * Decimal(tax_rate) / 100

                    sales_data["by_rate"][tax_rate]["base"] += line_net * rate
                    sales_data["by_rate"][tax_rate]["tax"] += line_tax * rate

        # 2. Alış Faturaları
        purchase_invoices = (
            self.session.query(PurchaseInvoice)
            .filter(
                PurchaseInvoice.invoice_date.between(start_date, end_date),
                PurchaseInvoice.status.notin_(
                    [PurchaseInvoiceStatus.DRAFT, PurchaseInvoiceStatus.CANCELLED]
                ),
            )
            .all()
        )

        purchase_data = {"base": Decimal(0), "tax": Decimal(0), "by_rate": {}}

        for inv in purchase_invoices:
            rate = getattr(inv, "exchange_rate", Decimal(1)) or Decimal(1)

            purchase_data["base"] += (inv.subtotal or Decimal(0)) * rate
            purchase_data["tax"] += (inv.tax_amount or Decimal(0)) * rate

            if inv.items:
                for item in inv.items:
                    tax_rate = int(item.tax_rate or 0)
                    if tax_rate not in purchase_data["by_rate"]:
                        purchase_data["by_rate"][tax_rate] = {
                            "base": Decimal(0),
                            "tax": Decimal(0),
                        }

                    qty = item.quantity or Decimal(0)
                    price = item.unit_price or Decimal(0)
                    disc = item.discount_rate or Decimal(0)

                    line_net = qty * price * (1 - disc / 100)
                    line_tax = line_net * Decimal(tax_rate) / 100

                    purchase_data["by_rate"][tax_rate]["base"] += line_net * rate
                    purchase_data["by_rate"][tax_rate]["tax"] += line_tax * rate

        # Summary
        net_tax = sales_data["tax"] - purchase_data["tax"]

        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "sales": {
                "base": float(sales_data["base"]),
                "tax": float(sales_data["tax"]),
                "by_rate": sales_data["by_rate"],  # keys are int, values specific dict
            },
            "purchases": {
                "base": float(purchase_data["base"]),
                "tax": float(purchase_data["tax"]),
                "by_rate": purchase_data["by_rate"],
            },
            "net_tax": float(net_tax),
            "status": "ÖDENECEK" if net_tax >= 0 else "İADE/DEVREDEN",
        }

    # =====================
    # SEED DATA
    # =====================

    def seed_chart_of_accounts(self):
        """Tekdüzen Hesap Planı temel hesaplarını oluştur"""
        # Eğer hesap varsa atla
        if self.session.query(Account).count() > 0:
            return

        accounts = [
            # 1 DÖNEN VARLIKLAR
            ("1", "DÖNEN VARLIKLAR", AccountType.ASSET, None, 1, False),
            ("10", "Hazır Değerler", AccountType.ASSET, "1", 2, False),
            ("100", "Kasa", AccountType.ASSET, "10", 3, True),
            ("101", "Alınan Çekler", AccountType.ASSET, "10", 3, True),
            ("102", "Bankalar", AccountType.ASSET, "10", 3, True),
            ("103", "Verilen Çekler (-)", AccountType.ASSET, "10", 3, True),
            ("12", "Ticari Alacaklar", AccountType.ASSET, "1", 2, False),
            ("120", "Alıcılar", AccountType.ASSET, "12", 3, True),
            ("121", "Alacak Senetleri", AccountType.ASSET, "12", 3, True),
            ("15", "Stoklar", AccountType.ASSET, "1", 2, False),
            ("150", "İlk Madde ve Malzeme", AccountType.ASSET, "15", 3, True),
            ("151", "Yarı Mamuller", AccountType.ASSET, "15", 3, True),
            ("152", "Mamuller", AccountType.ASSET, "15", 3, True),
            ("153", "Ticari Mallar", AccountType.ASSET, "15", 3, True),
            ("19", "Diğer Dönen Varlıklar", AccountType.ASSET, "1", 2, False),
            ("190", "Devreden KDV", AccountType.ASSET, "19", 3, True),
            ("191", "İndirilecek KDV", AccountType.ASSET, "19", 3, True),
            # 3 KISA VADELİ BORÇLAR
            (
                "3",
                "KISA VADELİ YABANCI KAYNAKLAR",
                AccountType.LIABILITY,
                None,
                1,
                False,
            ),
            ("32", "Ticari Borçlar", AccountType.LIABILITY, "3", 2, False),
            ("320", "Satıcılar", AccountType.LIABILITY, "32", 3, True),
            ("321", "Borç Senetleri", AccountType.LIABILITY, "32", 3, True),
            ("36", "Ödenecek Vergi", AccountType.LIABILITY, "3", 2, False),
            ("360", "Ödenecek Vergi ve Fonlar", AccountType.LIABILITY, "36", 3, True),
            ("391", "Hesaplanan KDV", AccountType.LIABILITY, "3", 3, True),
            # 5 ÖZKAYNAKLAR
            ("5", "ÖZ KAYNAKLAR", AccountType.EQUITY, None, 1, False),
            ("50", "Ödenmiş Sermaye", AccountType.EQUITY, "5", 2, False),
            ("500", "Sermaye", AccountType.EQUITY, "50", 3, True),
            ("59", "Dönem Net Karı/Zararı", AccountType.EQUITY, "5", 2, False),
            ("590", "Dönem Net Karı", AccountType.EQUITY, "59", 3, True),
            ("591", "Dönem Net Zararı (-)", AccountType.EQUITY, "59", 3, True),
            # 6 GELİRLER
            ("6", "GELİR TABLOSU HESAPLARI", AccountType.REVENUE, None, 1, False),
            ("60", "Brüt Satışlar", AccountType.REVENUE, "6", 2, False),
            ("600", "Yurt İçi Satışlar", AccountType.REVENUE, "60", 3, True),
            ("601", "Yurt Dışı Satışlar", AccountType.REVENUE, "60", 3, True),
            ("62", "Satışların Maliyeti", AccountType.EXPENSE, "6", 2, False),
            ("620", "Satılan Mamuller Maliyeti", AccountType.EXPENSE, "62", 3, True),
            (
                "621",
                "Satılan Ticari Mallar Maliyeti",
                AccountType.EXPENSE,
                "62",
                3,
                True,
            ),
            # 7 MALİYET
            ("7", "MALİYET HESAPLARI", AccountType.COST, None, 1, False),
            ("71", "Direkt İlk Madde", AccountType.COST, "7", 2, False),
            (
                "710",
                "Direkt İlk Madde ve Malzeme Giderleri",
                AccountType.COST,
                "71",
                3,
                True,
            ),
            ("72", "Direkt İşçilik", AccountType.COST, "7", 2, False),
            ("720", "Direkt İşçilik Giderleri", AccountType.COST, "72", 3, True),
            ("73", "Genel Üretim", AccountType.COST, "7", 2, False),
            ("730", "Genel Üretim Giderleri", AccountType.COST, "73", 3, True),
        ]

        # Önce parent'sız olanları ekle
        code_to_id = {}
        for code, name, acc_type, parent_code, level, is_detail in accounts:
            parent_id = code_to_id.get(parent_code)
            account = Account(
                code=code,
                name=name,
                account_type=acc_type,
                parent_id=parent_id,
                level=level,
                is_detail=is_detail,
            )
            self.session.add(account)
            self.session.flush()
            code_to_id[code] = account.id

        self.session.commit()

    def close(self):
        if self.session:
            self.session.close()
