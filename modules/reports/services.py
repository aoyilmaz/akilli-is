"""
Akıllı İş - Raporlama Servisleri

Tüm raporlar için merkezi servis katmanı.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from sqlalchemy import func, and_, or_, desc, extract, cast, String
from sqlalchemy.orm import Session

from database.base import get_session
from database.models import Item, StockMovement, StockBalance, Warehouse
from database.models.sales import Customer, Invoice, InvoiceItem, InvoiceStatus
from database.models.purchasing import (
    Supplier,
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
)
from database.models.production import WorkOrder, WorkOrderStatus


class ReportsService:
    """Merkezi raporlama servisi"""

    def __init__(self):
        self.session: Session = get_session()

    def close(self):
        if self.session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # =====================
    # SATIŞ RAPORLARI
    # =====================

    def get_sales_by_customer(
        self, start_date: date = None, end_date: date = None, limit: int = 50
    ) -> List[Dict]:
        """Müşteri bazlı satış raporu"""
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()

        query = (
            self.session.query(
                Customer.id,
                Customer.code,
                Customer.name,
                func.count(Invoice.id).label("invoice_count"),
                func.sum(Invoice.total).label("total_amount"),
                func.max(Invoice.invoice_date).label("last_invoice"),
            )
            .outerjoin(
                Invoice,
                and_(
                    Invoice.customer_id == Customer.id,
                    Invoice.invoice_date >= start_date,
                    Invoice.invoice_date <= end_date,
                    Invoice.status != InvoiceStatus.CANCELLED,
                ),
            )
            .group_by(Customer.id, Customer.code, Customer.name)
            .order_by(desc("total_amount"))
            .limit(limit)
        )

        results = []
        for row in query.all():
            results.append(
                {
                    "id": row.id,
                    "code": row.code,
                    "name": row.name,
                    "invoice_count": row.invoice_count or 0,
                    "total_amount": float(row.total_amount or 0),
                    "last_invoice": row.last_invoice,
                }
            )
        return results

    def get_sales_by_product(
        self, start_date: date = None, end_date: date = None, limit: int = 50
    ) -> List[Dict]:
        """Ürün bazlı satış raporu"""
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()

        query = (
            self.session.query(
                Item.id,
                Item.code,
                Item.name,
                func.sum(InvoiceItem.quantity).label("total_qty"),
                func.sum(InvoiceItem.line_total).label("total_amount"),
                func.count(InvoiceItem.id).label("sale_count"),
            )
            .join(InvoiceItem, InvoiceItem.item_id == Item.id)
            .join(
                Invoice,
                and_(
                    Invoice.id == InvoiceItem.invoice_id,
                    Invoice.invoice_date >= start_date,
                    Invoice.invoice_date <= end_date,
                    Invoice.status != InvoiceStatus.CANCELLED,
                ),
            )
            .group_by(Item.id, Item.code, Item.name)
            .order_by(desc("total_amount"))
            .limit(limit)
        )

        results = []
        for row in query.all():
            results.append(
                {
                    "id": row.id,
                    "code": row.code,
                    "name": row.name,
                    "total_qty": float(row.total_qty or 0),
                    "total_amount": float(row.total_amount or 0),
                    "sale_count": row.sale_count or 0,
                }
            )
        return results

    def get_sales_by_period(
        self, period: str = "monthly", months: int = 12
    ) -> List[Dict]:
        """Dönemsel satış raporu"""
        end_date = date.today()

        if period == "daily":
            start_date = end_date - timedelta(days=30)
            # PostgreSQL: date olarak grupla
            group_func = cast(Invoice.invoice_date, String)
        elif period == "weekly":
            start_date = end_date - timedelta(weeks=12)
            # PostgreSQL: to_char ile haftalık
            group_func = func.to_char(Invoice.invoice_date, "IYYY-IW")
        else:  # monthly
            start_date = end_date - timedelta(days=30 * months)
            # PostgreSQL: to_char ile aylık
            group_func = func.to_char(Invoice.invoice_date, "YYYY-MM")

        query = (
            self.session.query(
                group_func.label("period"),
                func.count(Invoice.id).label("invoice_count"),
                func.sum(Invoice.total).label("total_amount"),
            )
            .filter(
                Invoice.invoice_date >= start_date,
                Invoice.invoice_date <= end_date,
                Invoice.status != InvoiceStatus.CANCELLED,
            )
            .group_by("period")
            .order_by("period")
        )

        results = []
        for row in query.all():
            results.append(
                {
                    "period": row.period,
                    "invoice_count": row.invoice_count or 0,
                    "total_amount": float(row.total_amount or 0),
                }
            )
        return results

    # =====================
    # STOK YAŞLANDIRMA
    # =====================

    def get_stock_aging(self, warehouse_id: int = None) -> Dict:
        """Stok yaşlandırma raporu"""
        today = date.today()
        aging_groups = {
            "0-30": {"min": 0, "max": 30, "items": [], "value": Decimal(0)},
            "31-60": {"min": 31, "max": 60, "items": [], "value": Decimal(0)},
            "61-90": {"min": 61, "max": 90, "items": [], "value": Decimal(0)},
            "90+": {"min": 91, "max": 9999, "items": [], "value": Decimal(0)},
        }

        # Stok bakiyesi olan ürünleri al
        query = self.session.query(StockBalance).filter(StockBalance.quantity > 0)
        if warehouse_id:
            query = query.filter(StockBalance.warehouse_id == warehouse_id)

        for balance in query.all():
            # Son giriş hareketi bul
            last_entry = (
                self.session.query(StockMovement)
                .filter(
                    StockMovement.item_id == balance.item_id,
                    StockMovement.to_warehouse_id == balance.warehouse_id,
                )
                .order_by(StockMovement.movement_date.desc())
                .first()
            )

            if last_entry and last_entry.movement_date:
                if isinstance(last_entry.movement_date, datetime):
                    entry_date = last_entry.movement_date.date()
                else:
                    entry_date = last_entry.movement_date
                days_old = (today - entry_date).days
            else:
                days_old = 999  # Hareket yoksa eski say

            item_value = balance.quantity * (balance.unit_cost or Decimal(0))

            item_data = {
                "item_id": balance.item_id,
                "item_code": balance.item.code if balance.item else "",
                "item_name": balance.item.name if balance.item else "",
                "warehouse": balance.warehouse.name if balance.warehouse else "",
                "quantity": float(balance.quantity),
                "unit_cost": float(balance.unit_cost or 0),
                "total_value": float(item_value),
                "days_old": days_old,
                "last_entry": last_entry.movement_date if last_entry else None,
            }

            # Gruba ekle
            for group_name, group_data in aging_groups.items():
                if group_data["min"] <= days_old <= group_data["max"]:
                    group_data["items"].append(item_data)
                    group_data["value"] += item_value
                    break

        # Özet
        summary = {
            "total_value": sum(float(g["value"]) for g in aging_groups.values()),
            "total_items": sum(len(g["items"]) for g in aging_groups.values()),
            "groups": {
                k: {
                    "count": len(v["items"]),
                    "value": float(v["value"]),
                    "items": v["items"],
                }
                for k, v in aging_groups.items()
            },
        }

        return summary

    # =====================
    # ÜRETİM OEE
    # =====================

    def get_production_oee(
        self, start_date: date = None, end_date: date = None
    ) -> Dict:
        """Üretim performans raporu (OEE)"""
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()

        # Tamamlanan iş emirleri
        work_orders = (
            self.session.query(WorkOrder)
            .filter(
                WorkOrder.status == WorkOrderStatus.COMPLETED,
                WorkOrder.actual_end >= start_date,
                WorkOrder.actual_end <= end_date,
            )
            .all()
        )

        if not work_orders:
            return {
                "availability": 0,
                "performance": 0,
                "quality": 100,
                "oee": 0,
                "total_orders": 0,
                "details": [],
            }

        total_planned_qty = Decimal(0)
        total_actual_qty = Decimal(0)
        total_good_qty = Decimal(0)
        on_time_count = 0

        details = []
        for wo in work_orders:
            planned = wo.quantity or Decimal(0)
            actual = wo.completed_quantity or Decimal(0)
            # Kabul edilen = tamamlanan (kalite kontrolü varsa ayarlanabilir)
            good = actual

            total_planned_qty += planned
            total_actual_qty += actual
            total_good_qty += good

            # Zamanında tamamlandı mı?
            if wo.planned_end and wo.actual_end:
                if wo.actual_end <= wo.planned_end:
                    on_time_count += 1

            details.append(
                {
                    "work_order_no": wo.work_order_no,
                    "item_name": wo.item.name if wo.item else "",
                    "planned_qty": float(planned),
                    "actual_qty": float(actual),
                    "performance": float(actual / planned * 100) if planned > 0 else 0,
                }
            )

        # OEE Hesaplama
        # Kullanılabilirlik = Zamanında tamamlanan / Toplam
        availability = (on_time_count / len(work_orders) * 100) if work_orders else 0

        # Performans = Gerçek Üretim / Planlanan Üretim
        performance = (
            float(total_actual_qty / total_planned_qty * 100)
            if total_planned_qty > 0
            else 0
        )

        # Kalite = Kabul Edilen / Toplam Üretim
        quality = (
            float(total_good_qty / total_actual_qty * 100)
            if total_actual_qty > 0
            else 100
        )

        # OEE = Kullanılabilirlik x Performans x Kalite / 10000
        oee = (availability * performance * quality) / 10000

        return {
            "availability": round(availability, 1),
            "performance": round(performance, 1),
            "quality": round(quality, 1),
            "oee": round(oee, 1),
            "total_orders": len(work_orders),
            "on_time_count": on_time_count,
            "total_planned": float(total_planned_qty),
            "total_actual": float(total_actual_qty),
            "details": details,
        }

    # =====================
    # TEDARİKÇİ PERFORMANS
    # =====================

    def get_supplier_performance(self) -> List[Dict]:
        """Tedarikçi performans raporu"""
        suppliers = (
            self.session.query(Supplier).filter(Supplier.is_active == True).all()
        )

        results = []
        for supplier in suppliers:
            # Mal kabul sayıları
            receipts = (
                self.session.query(GoodsReceipt)
                .filter(GoodsReceipt.supplier_id == supplier.id)
                .all()
            )

            total_receipts = len(receipts)
            if total_receipts == 0:
                results.append(
                    {
                        "id": supplier.id,
                        "code": supplier.code,
                        "name": supplier.name,
                        "total_receipts": 0,
                        "on_time_rate": 0,
                        "quality_rate": 100,
                        "total_orders": 0,
                        "open_balance": 0,
                        "score": 0,
                    }
                )
                continue

            # Zamanında teslimat (sipariş varsa kontrol et)
            on_time = 0
            total_accepted = Decimal(0)
            total_received = Decimal(0)

            for receipt in receipts:
                for item in receipt.items:
                    total_received += item.quantity or Decimal(0)
                    total_accepted += item.accepted_quantity or Decimal(0)

            # Kalite oranı
            quality_rate = (
                float(total_accepted / total_received * 100)
                if total_received > 0
                else 100
            )

            # Sipariş sayısı
            order_count = (
                self.session.query(PurchaseOrder)
                .filter(PurchaseOrder.supplier_id == supplier.id)
                .count()
            )

            # Açık bakiye (varsa)
            open_balance = 0  # PurchaseInvoice ile hesaplanabilir

            # Genel puan (basit ortalama)
            score = quality_rate

            results.append(
                {
                    "id": supplier.id,
                    "code": supplier.code,
                    "name": supplier.name,
                    "total_receipts": total_receipts,
                    "on_time_rate": 0,  # Teslimat tarihi takibi için ek alan gerekli
                    "quality_rate": round(quality_rate, 1),
                    "total_orders": order_count,
                    "open_balance": open_balance,
                    "score": round(score, 1),
                }
            )

        # Puana göre sırala
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    # =====================
    # ALACAK YAŞLANDIRMA
    # =====================

    def get_receivables_aging(self) -> Dict:
        """Alacak yaşlandırma raporu"""
        today = date.today()

        aging_groups = {
            "0-30": {
                "label": "0-30 Gün",
                "risk": "normal",
                "customers": [],
                "total": Decimal(0),
            },
            "31-60": {
                "label": "31-60 Gün",
                "risk": "watch",
                "customers": [],
                "total": Decimal(0),
            },
            "61-90": {
                "label": "61-90 Gün",
                "risk": "risky",
                "customers": [],
                "total": Decimal(0),
            },
            "90+": {
                "label": "90+ Gün",
                "risk": "critical",
                "customers": [],
                "total": Decimal(0),
            },
        }

        # Açık faturalar (tam ödenmemiş)
        open_invoices = (
            self.session.query(Invoice)
            .filter(
                Invoice.status.in_(
                    [InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE]
                ),
                Invoice.balance > 0,
            )
            .all()
        )

        customer_balances = {}

        for invoice in open_invoices:
            # Vade tarihi veya fatura tarihi
            due = invoice.due_date or invoice.invoice_date
            if isinstance(due, datetime):
                due = due.date()

            days_overdue = (today - due).days if today > due else 0
            balance = invoice.balance or Decimal(0)

            # Müşteriyi grupla
            cust_id = invoice.customer_id
            if cust_id not in customer_balances:
                customer_balances[cust_id] = {
                    "customer_id": cust_id,
                    "customer_name": invoice.customer.name if invoice.customer else "",
                    "customer_code": invoice.customer.code if invoice.customer else "",
                    "invoices": [],
                    "total_balance": Decimal(0),
                    "max_days": 0,
                }

            customer_balances[cust_id]["invoices"].append(
                {
                    "invoice_no": invoice.invoice_no,
                    "invoice_date": invoice.invoice_date,
                    "due_date": due,
                    "total": float(invoice.total or 0),
                    "balance": float(balance),
                    "days_overdue": days_overdue,
                }
            )
            customer_balances[cust_id]["total_balance"] += balance
            customer_balances[cust_id]["max_days"] = max(
                customer_balances[cust_id]["max_days"], days_overdue
            )

        # Müşterileri gruplara ayır
        for cust_data in customer_balances.values():
            days = cust_data["max_days"]
            balance = cust_data["total_balance"]

            if days <= 30:
                group = "0-30"
            elif days <= 60:
                group = "31-60"
            elif days <= 90:
                group = "61-90"
            else:
                group = "90+"

            aging_groups[group]["customers"].append(
                {
                    "customer_id": cust_data["customer_id"],
                    "customer_code": cust_data["customer_code"],
                    "customer_name": cust_data["customer_name"],
                    "total_balance": float(balance),
                    "max_days": days,
                    "invoice_count": len(cust_data["invoices"]),
                }
            )
            aging_groups[group]["total"] += balance

        # Özet
        summary = {
            "total_receivables": sum(float(g["total"]) for g in aging_groups.values()),
            "total_customers": len(customer_balances),
            "groups": {
                k: {
                    "label": v["label"],
                    "risk": v["risk"],
                    "count": len(v["customers"]),
                    "total": float(v["total"]),
                    "customers": v["customers"],
                }
                for k, v in aging_groups.items()
            },
        }

        return summary

    # =====================
    # DASHBOARD ÖZETİ
    # =====================

    def get_reports_summary(self) -> Dict:
        """Tüm raporların özeti"""
        today = date.today()
        month_start = today.replace(day=1)

        # Aylık satış
        monthly_sales = (
            self.session.query(func.sum(Invoice.total))
            .filter(
                Invoice.invoice_date >= month_start,
                Invoice.status != InvoiceStatus.CANCELLED,
            )
            .scalar()
            or 0
        )

        # Toplam alacak
        total_receivables = (
            self.session.query(func.sum(Invoice.balance))
            .filter(Invoice.balance > 0)
            .scalar()
            or 0
        )

        # Kritik alacak (90+ gün)
        critical_date = today - timedelta(days=90)
        critical_receivables = (
            self.session.query(func.sum(Invoice.balance))
            .filter(Invoice.balance > 0, Invoice.due_date < critical_date)
            .scalar()
            or 0
        )

        # Stok değeri
        stock_value = (
            self.session.query(
                func.sum(StockBalance.quantity * StockBalance.unit_cost)
            ).scalar()
            or 0
        )

        return {
            "monthly_sales": float(monthly_sales),
            "total_receivables": float(total_receivables),
            "critical_receivables": float(critical_receivables),
            "stock_value": float(stock_value),
        }
