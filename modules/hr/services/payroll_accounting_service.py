"""
Akıllı İş - Bordro Muhasebe Tahakkuk Servisi

Onaylanmış bordrolardan otomatik yevmiye fişi oluşturur.
"""

from datetime import date
from decimal import Decimal
from typing import List, Dict, Optional
from pathlib import Path

import yaml
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database.base import get_session
from database.models.hr import Payroll, PayrollStatus, Employee
from database.models.accounting import Account, JournalEntry, JournalEntryLine


# Config dosyasını yükle
def _load_config() -> Dict:
    """Hesap eşleştirme config'ini yükle"""
    config_path = (
        Path(__file__).parent.parent.parent.parent / "config" / "payroll_accounts.yaml"
    )
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    # Varsayılan config
    return {
        "expense_accounts": {"default": "770", "production": "730"},
        "liability_accounts": {
            "net_salary": "335",
            "income_tax": "360",
            "stamp_tax": "360",
            "sgk_employee": "361",
            "sgk_employer": "361",
            "unemployment_employee": "361",
            "unemployment_employer": "361",
        },
        "department_mappings": {"default": "770"},
        "journal_description_template": "{period} Dönemi Personel Maaş Tahakkuku",
    }


class PayrollAccountingService:
    """
    Bordro Muhasebe Tahakkuk Servisi

    Onaylanmış bordroları alıp çift taraflı yevmiye fişi oluşturur.
    """

    def __init__(self, session: Session = None):
        self.session = session or get_session()
        self.config = _load_config()
        self._account_cache: Dict[str, Account] = {}

    def _get_account(self, code: str) -> Optional[Account]:
        """Hesabı cache'den veya DB'den getir"""
        if code not in self._account_cache:
            account = self.session.query(Account).filter(Account.code == code).first()
            self._account_cache[code] = account
        return self._account_cache.get(code)

    def _get_expense_account_code(self, employee: Employee) -> str:
        """Çalışana göre gider hesap kodunu belirle"""
        dept_mappings = self.config.get("department_mappings", {})

        # Departman eşleştirmesi
        if employee.department_id:
            dept_code = dept_mappings.get(str(employee.department_id))
            if dept_code:
                return dept_code

        # Varsayılan
        return self.config["expense_accounts"].get("default", "770")

    def create_accrual_entry(
        self, year: int, month: int, department_id: int = None, entry_date: date = None
    ) -> JournalEntry:
        """
        Belirli dönem için toplu bordro tahakkuk fişi oluştur

        Args:
            year: Bordro yılı
            month: Bordro ayı
            department_id: Opsiyonel departman filtresi
            entry_date: Fiş tarihi (varsayılan: ayın son günü)

        Returns:
            Oluşturulan JournalEntry
        """
        # Onaylanmış bordroları getir
        query = self.session.query(Payroll).filter(
            Payroll.period_year == year,
            Payroll.period_month == month,
            Payroll.status == PayrollStatus.APPROVED,
            Payroll.journal_entry_id.is_(None),  # Henüz tahakkuk edilmemiş
        )

        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)

        payrolls = query.all()

        if not payrolls:
            raise ValueError("Tahakkuk edilecek onaylanmış bordro bulunamadı")

        # Fiş tarihi
        if entry_date is None:
            # Ayın son günü
            if month == 12:
                entry_date = date(year + 1, 1, 1)
            else:
                entry_date = date(year, month + 1, 1)
            from datetime import timedelta

            entry_date = entry_date - timedelta(days=1)

        # Fiş numarası oluştur
        entry_no = self._generate_entry_no(entry_date)

        # Açıklama
        period_str = f"{month:02d}/{year}"
        description = self.config.get(
            "journal_description_template", "{period} Dönemi Personel Maaş Tahakkuku"
        ).format(period=period_str)

        # Yevmiye fişi oluştur
        journal_entry = JournalEntry(
            entry_no=entry_no,
            entry_date=entry_date,
            description=description,
        )
        self.session.add(journal_entry)
        self.session.flush()  # ID al

        # Toplam tutarları hesapla
        totals = self._calculate_totals(payrolls)

        # Fiş satırlarını oluştur
        lines = self._create_journal_lines(journal_entry.id, totals, payrolls)

        for line in lines:
            self.session.add(line)

        # Bordroları güncelle
        for payroll in payrolls:
            payroll.journal_entry_id = journal_entry.id

        self.session.commit()
        self.session.refresh(journal_entry)

        return journal_entry

    def _calculate_totals(self, payrolls: List[Payroll]) -> Dict:
        """Bordro toplamlarını hesapla"""
        totals = {
            "gross_salary": Decimal("0"),
            "overtime_pay": Decimal("0"),
            "bonus": Decimal("0"),
            "sgk_employee": Decimal("0"),
            "sgk_employer": Decimal("0"),
            "unemployment_employee": Decimal("0"),
            "unemployment_employer": Decimal("0"),
            "income_tax": Decimal("0"),
            "stamp_tax": Decimal("0"),
            "net_salary": Decimal("0"),
        }

        for p in payrolls:
            totals["gross_salary"] += p.gross_salary or Decimal("0")
            totals["overtime_pay"] += p.overtime_pay or Decimal("0")
            totals["bonus"] += p.bonus or Decimal("0")
            totals["sgk_employee"] += p.sgk_employee or Decimal("0")
            totals["sgk_employer"] += p.sgk_employer or Decimal("0")
            totals["unemployment_employee"] += p.unemployment_employee or Decimal("0")
            totals["unemployment_employer"] += p.unemployment_employer or Decimal("0")
            totals["income_tax"] += p.income_tax or Decimal("0")
            totals["stamp_tax"] += p.stamp_tax or Decimal("0")
            totals["net_salary"] += p.net_salary or Decimal("0")

        return totals

    def _create_journal_lines(
        self, journal_entry_id: int, totals: Dict, payrolls: List[Payroll]
    ) -> List[JournalEntryLine]:
        """Yevmiye satırlarını oluştur"""
        lines = []
        liability = self.config.get("liability_accounts", {})

        # ===== BORÇ (Gider) TARAFI =====
        # Brüt maaş + İşveren SGK payları gider olarak
        expense_code = self.config["expense_accounts"].get("default", "770")
        expense_account = self._get_account(expense_code)

        total_expense = (
            totals["gross_salary"]
            + totals["sgk_employer"]
            + totals["unemployment_employer"]
        )

        if expense_account and total_expense > 0:
            lines.append(
                JournalEntryLine(
                    journal_entry_id=journal_entry_id,
                    account_id=expense_account.id,
                    debit=total_expense,
                    credit=Decimal("0"),
                    description="Personel Giderleri (Brüt + İşveren SGK)",
                )
            )

        # ===== ALACAK TARAFI =====

        # 335 - Personele Borçlar (Net Maaş)
        net_account_code = liability.get("net_salary", "335")
        net_account = self._get_account(net_account_code)
        if net_account and totals["net_salary"] > 0:
            lines.append(
                JournalEntryLine(
                    journal_entry_id=journal_entry_id,
                    account_id=net_account.id,
                    debit=Decimal("0"),
                    credit=totals["net_salary"],
                    description="Personele Ödenecek Net Maaş",
                )
            )

        # 360 - Vergiler (Gelir + Damga)
        tax_account_code = liability.get("income_tax", "360")
        tax_account = self._get_account(tax_account_code)
        total_tax = totals["income_tax"] + totals["stamp_tax"]
        if tax_account and total_tax > 0:
            lines.append(
                JournalEntryLine(
                    journal_entry_id=journal_entry_id,
                    account_id=tax_account.id,
                    debit=Decimal("0"),
                    credit=total_tax,
                    description="Ödenecek Vergiler (Gelir + Damga)",
                )
            )

        # 361 - SGK Primleri (İşçi + İşveren)
        sgk_account_code = liability.get("sgk_employee", "361")
        sgk_account = self._get_account(sgk_account_code)
        total_sgk = (
            totals["sgk_employee"]
            + totals["sgk_employer"]
            + totals["unemployment_employee"]
            + totals["unemployment_employer"]
        )
        if sgk_account and total_sgk > 0:
            lines.append(
                JournalEntryLine(
                    journal_entry_id=journal_entry_id,
                    account_id=sgk_account.id,
                    debit=Decimal("0"),
                    credit=total_sgk,
                    description="Ödenecek SGK Primleri (İşçi + İşveren)",
                )
            )

        return lines

    def _generate_entry_no(self, entry_date: date) -> str:
        """Yevmiye fiş numarası oluştur"""
        prefix = f"BRD-{entry_date.year}-"

        # Mevcut en yüksek numarayı bul
        last = (
            self.session.query(JournalEntry)
            .filter(JournalEntry.entry_no.like(f"{prefix}%"))
            .order_by(JournalEntry.entry_no.desc())
            .first()
        )

        if last:
            try:
                num = int(last.entry_no.replace(prefix, "")) + 1
            except ValueError:
                num = 1
        else:
            num = 1

        return f"{prefix}{num:05d}"

    def reverse_accrual(self, journal_entry_id: int) -> bool:
        """Tahakkuk fişini iptal et (bordroları serbest bırak)"""
        # İlgili bordroları bul
        payrolls = (
            self.session.query(Payroll)
            .filter(Payroll.journal_entry_id == journal_entry_id)
            .all()
        )

        if not payrolls:
            return False

        # Bordroların bağını kopar
        for p in payrolls:
            p.journal_entry_id = None

        # Yevmiye fişini sil
        entry = (
            self.session.query(JournalEntry)
            .filter(JournalEntry.id == journal_entry_id)
            .first()
        )

        if entry:
            # Önce satırları sil
            self.session.query(JournalEntryLine).filter(
                JournalEntryLine.journal_entry_id == journal_entry_id
            ).delete()
            self.session.delete(entry)

        self.session.commit()
        return True

    def get_accrual_preview(
        self, year: int, month: int, department_id: int = None
    ) -> Dict:
        """
        Tahakkuk önizleme - commit etmeden göster

        Returns:
            Toplam tutarlar ve borç/alacak dağılımı
        """
        query = self.session.query(Payroll).filter(
            Payroll.period_year == year,
            Payroll.period_month == month,
            Payroll.status == PayrollStatus.APPROVED,
            Payroll.journal_entry_id.is_(None),
        )

        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)

        payrolls = query.all()

        if not payrolls:
            return {"error": "Tahakkuk edilecek bordro bulunamadı"}

        totals = self._calculate_totals(payrolls)

        liability = self.config.get("liability_accounts", {})
        expense_code = self.config["expense_accounts"].get("default", "770")

        total_expense = (
            totals["gross_salary"]
            + totals["sgk_employer"]
            + totals["unemployment_employer"]
        )
        total_tax = totals["income_tax"] + totals["stamp_tax"]
        total_sgk = (
            totals["sgk_employee"]
            + totals["sgk_employer"]
            + totals["unemployment_employee"]
            + totals["unemployment_employer"]
        )

        return {
            "period": f"{month:02d}/{year}",
            "payroll_count": len(payrolls),
            "totals": {
                "gross_salary": float(totals["gross_salary"]),
                "net_salary": float(totals["net_salary"]),
                "sgk_employee": float(totals["sgk_employee"]),
                "sgk_employer": float(totals["sgk_employer"]),
                "income_tax": float(totals["income_tax"]),
                "stamp_tax": float(totals["stamp_tax"]),
            },
            "journal_lines": {
                "debit": [
                    {
                        "account_code": expense_code,
                        "description": "Personel Giderleri",
                        "amount": float(total_expense),
                    }
                ],
                "credit": [
                    {
                        "account_code": liability.get("net_salary", "335"),
                        "description": "Personele Borçlar",
                        "amount": float(totals["net_salary"]),
                    },
                    {
                        "account_code": liability.get("income_tax", "360"),
                        "description": "Ödenecek Vergiler",
                        "amount": float(total_tax),
                    },
                    {
                        "account_code": liability.get("sgk_employee", "361"),
                        "description": "Ödenecek SGK Primleri",
                        "amount": float(total_sgk),
                    },
                ],
            },
        }

    def close(self):
        """Session kapat"""
        if self.session:
            self.session.close()
