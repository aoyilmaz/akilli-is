"""
Akıllı İş - Profesyonelleşme Fazı Test Modülü
"""

import sys
import os
from datetime import date, datetime
from decimal import Decimal

# Test renkleri
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = 0
        self.failed = 0

    def success(self, msg: str):
        self.passed += 1
        print(f"  {GREEN}✓{RESET} {msg}")

    def fail(self, msg: str, error: str = None):
        self.failed += 1
        print(f"  {RED}✗{RESET} {msg}")
        if error:
            print(f"    {RED}→ {error}{RESET}")


class ProPhaseTests:
    def __init__(self):
        self.session = None
        self.setup_db()

    def setup_db(self):
        from database.base import get_session

        self.session = get_session()

    def test_stock_quality_bridge(self):
        result = TestResult("Stok & Kalite Bridge")
        print(f"\n{BOLD}Testing StockQualityService...{RESET}")
        try:
            from modules.inventory.services.stock_quality_bridge import (
                StockQualityService,
            )
            from database.models.inventory import (
                Item,
                ItemType,
                Warehouse,
                WarehouseLocation,
                LocationType,
            )
            from database.models.purchasing import GoodsReceipt, GoodsReceiptItem
            from database.models import Unit

            # 1. QC zorunlu bir item oluştur
            unit = self.session.query(Unit).first()
            warehouse = self.session.query(Warehouse).first()

            qc_item = Item(
                code="QC-TEST-001",
                name="QC Zorunlu Test Ürünü",
                is_qc_required=True,
                item_type=ItemType.HAMMADDE,
                unit_id=unit.id,
            )
            self.session.add(qc_item)
            self.session.flush()

            # 2. Mal Kabul Oluştur
            gr = GoodsReceipt(
                receipt_no="GR-QC-001",
                receipt_date=date.today(),
                supplier_id=1,
                warehouse_id=warehouse.id,
                created_by=1,
            )
            self.session.add(gr)
            self.session.flush()

            gr_item = GoodsReceiptItem(
                receipt_id=gr.id,
                item_id=qc_item.id,
                quantity=Decimal("100"),
                unit_id=unit.id,
            )
            self.session.add(gr_item)
            self.session.flush()

            # 3. Servisi Çalıştır
            StockQualityService.handle_goods_receipt(self.session, gr)

            # 4. Doğrula: Karantina lokasyonuna girdi mi?
            from database.models.inventory import StockBalance

            balance = (
                self.session.query(StockBalance)
                .join(WarehouseLocation)
                .filter(
                    StockBalance.item_id == qc_item.id,
                    WarehouseLocation.location_type == LocationType.QUARANTINE,
                )
                .first()
            )

            if balance and balance.quantity == Decimal("100"):
                result.success("QC zorunlu ürün karantinaya yönlendirildi.")
            else:
                result.fail("Ürün karantinaya yönlendirilemedi!")

        except Exception as e:
            result.fail("StockQualityService hatası", str(e))
        return result

    def test_accounting_bridge(self):
        result = TestResult("Muhasebe Bridge")
        print(f"\n{BOLD}Testing AccountingBridge...{RESET}")
        try:
            from modules.finance.services.accounting_bridge import AccountingBridge
            from database.models.sales import Invoice, Customer

            # Test Faturası
            customer = self.session.query(Customer).first()
            inv = Invoice(
                invoice_no="INV-TEST-001",
                invoice_date=date.today(),
                customer_id=customer.id,
                subtotal=Decimal("1000.00"),
                tax_amount=Decimal("180.00"),
                total=Decimal("1180.00"),
            )
            self.session.add(inv)
            self.session.flush()

            bridge = AccountingBridge(self.session)
            entry = bridge.create_invoice_journal(inv)

            if entry and entry.id:
                result.success(f"Otomatik yevmiye fişi oluşturuldu: {entry.entry_no}")
                if len(entry.lines) >= 2:
                    result.success(
                        f"Fiş kalemleri oluşturuldu: {len(entry.lines)} kalem"
                    )
                else:
                    result.fail("Fiş kalemleri eksik!")
            else:
                result.fail("Yevmiye fişi oluşturulamadı!")

        except Exception as e:
            result.fail("AccountingBridge hatası", str(e))
        return result

    def test_ubl_generator(self):
        result = TestResult("UBL XML Generator")
        print(f"\n{BOLD}Testing UBLGenerator...{RESET}")
        try:
            from modules.finance.utils.ubl_generator import UBLGenerator

            data = {
                "invoice_no": "FT-2026-0001",
                "customer_name": "Test Müşteri Ltd. Şti.",
                "tax_office": "Boğaziçi",
                "total_tax": "180.00",
                "subtotal": "1000.00",
                "total": "1180.00",
                "items": [
                    {
                        "name": "Ürün A",
                        "quantity": 10,
                        "unit_price": 100,
                        "line_total": 1000,
                    }
                ],
            }
            xml = UBLGenerator.generate_xml(data)
            if "<cbc:ID>FT-2026-0001</cbc:ID>" in xml and "<cbc:UUID>" in xml:
                result.success("UBL 2.1 XML başarıyla üretildi.")
            else:
                result.fail("UBL XML içeriği hatalı!")
        except Exception as e:
            result.fail("UBLGenerator hatası", str(e))
        return result

    def test_report_service(self):
        result = TestResult("Rapor Servisi")
        print(f"\n{BOLD}Testing ReportService...{RESET}")
        try:
            from core.reporting.report_service import ReportService
            from core.reporting.report_service import DEFAULT_INVOICE_TEMPLATE

            # Şablon dosyasını oluştur
            service = ReportService()
            template_path = os.path.join(service.template_dir, "test_invoice.html")
            with open(template_path, "w") as f:
                f.write(DEFAULT_INVOICE_TEMPLATE)

            data = {
                "company_name": "Akıllı İş",
                "customer_name": "Test Müşteri",
                "invoice_no": "FT-001",
                "invoice_date": "18.01.2026",
                "items": [
                    {
                        "name": "Test",
                        "quantity": 1,
                        "unit_price": 100,
                        "line_total": 100,
                    }
                ],
                "subtotal": 100,
                "tax_total": 18,
                "total": 118,
            }

            success = service.generate_pdf("test_invoice.html", data, "test_output.pdf")
            if success:
                result.success("Rapor HTML/Render işlemi başarılı.")
            else:
                result.fail("Rapor render edilemedi.")
        except Exception as e:
            result.fail("ReportService hatası", str(e))
        return result

    def test_worker_manager(self):
        result = TestResult("Worker Manager")
        print(f"\n{BOLD}Testing WorkerManager...{RESET}")
        try:
            from core.threads.worker_manager import WorkerManager
            from PyQt6.QtWidgets import QApplication

            # QApplication gerekli (sinyaller için)
            app = QApplication.instance() or QApplication([])

            manager = WorkerManager()

            def sample_task(x, y):
                return x + y

            def on_result(res):
                nonlocal result_value
                result_value = res

            result_value = None
            worker = manager.run_task(sample_task, 2, 3, on_result=on_result)

            # Thread'in bitmesini bekle (Gümlememesi için kısa bir süre)
            import time

            loop_count = 0
            while result_value is None and loop_count < 10:
                app.processEvents()
                time.sleep(0.1)
                loop_count += 1

            if result_value == 5:
                result.success("Asenkron görev başarıyla tamamlandı (Result: 5).")
            else:
                result.fail(f"Asenkron görev sonucu hatalı: {result_value}")

        except Exception as e:
            result.fail("WorkerManager hatası", str(e))
        return result

    def run_all(self):
        results = [
            self.test_stock_quality_bridge(),
            self.test_accounting_bridge(),
            self.test_ubl_generator(),
            self.test_report_service(),
            # self.test_worker_manager() # GUI thread bağımlılığı nedeniyle bazen headlessly sıkıntı olabilir
        ]

        print(f"\n{'='*40}")
        print(f"{BOLD}PRO PHASE TEST ÖZETİ{RESET}")
        print(f"{'='*40}")
        for r in results:
            status = f"{GREEN}PASS{RESET}" if r.failed == 0 else f"{RED}FAIL{RESET}"
            print(f"{r.name:25} : {status} (✓:{r.passed}, ✗:{r.failed})")

        self.session.rollback()  # Test verilerini temizle
        self.session.close()


if __name__ == "__main__":
    tests = ProPhaseTests()
    tests.run_all()
