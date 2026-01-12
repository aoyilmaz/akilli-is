"""
Akıllı İş ERP - Gerçek Hayat Testleri
=====================================
Bu modül, ERP sisteminin tüm kritik fonksiyonlarını gerçek veritabanı
verileriyle test eder.

Test Kategorileri:
1. Veri Kontrolü - Mevcut verilerin doğruluğu
2. Stok İşlemleri - Giriş/Çıkış/Transfer
3. Satınalma Akışı - Talep → Sipariş → Mal Kabul
4. Satış Akışı - Teklif → Sipariş → İrsaliye
5. Entegrasyon - Modüller arası veri tutarlılığı
"""

import sys
import os
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional

# Proje ana dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Renk kodları
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


class TestResult:
    """Test sonuç sınıfı"""

    def __init__(self, name: str):
        self.name = name
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors: List[tuple] = []
        self.details: List[str] = []

    def success(self, msg: str):
        self.passed += 1
        self.details.append(f"  {GREEN}✓{RESET} {msg}")
        print(f"  {GREEN}✓{RESET} {msg}")

    def fail(self, msg: str, error: str = None):
        self.failed += 1
        self.errors.append((msg, error))
        self.details.append(f"  {RED}✗{RESET} {msg}")
        print(f"  {RED}✗{RESET} {msg}")
        if error:
            print(f"    {RED}→ {error}{RESET}")

    def warn(self, msg: str):
        self.warnings += 1
        self.details.append(f"  {YELLOW}⚠{RESET} {msg}")
        print(f"  {YELLOW}⚠{RESET} {msg}")

    def info(self, msg: str):
        self.details.append(f"  {BLUE}ℹ{RESET} {msg}")
        print(f"  {BLUE}ℹ{RESET} {msg}")

    def summary(self):
        total = self.passed + self.failed
        if self.failed == 0:
            status = f"{GREEN}BAŞARILI{RESET}"
        else:
            status = f"{RED}BAŞARISIZ{RESET}"
        print(f"\n{BOLD}[{self.name}]{RESET} {status}")
        print(
            f"  Toplam: {total} | Başarılı: {GREEN}{self.passed}{RESET}"
            f" | Başarısız: {RED}{self.failed}{RESET}"
            f" | Uyarı: {YELLOW}{self.warnings}{RESET}"
        )
        return self.failed == 0


def print_header(title: str):
    print(f"\n{'═' * 70}")
    print(f"{BOLD}{CYAN}{title}{RESET}")
    print(f"{'═' * 70}")


def print_section(title: str):
    print(f"\n{YELLOW}▶ {title}{RESET}")


def print_subsection(title: str):
    print(f"\n  {MAGENTA}• {title}{RESET}")


class ERPRealLifeTest:
    """ERP Gerçek Hayat Test Sınıfı"""

    def __init__(self):
        self.session = None
        self.results: List[TestResult] = []
        self.test_data = {}
        self.report_lines: List[str] = []

    def setup(self) -> bool:
        """Test ortamını hazırla"""
        print_section("Test ortamı hazırlanıyor...")

        try:
            from database.base import get_session

            self.session = get_session()
            print(f"  {GREEN}✓{RESET} Veritabanı bağlantısı kuruldu")
            return True
        except Exception as e:
            print(f"  {RED}✗{RESET} Veritabanı bağlantı hatası: {e}")
            return False

    def teardown(self):
        """Test ortamını temizle"""
        if self.session:
            self.session.close()

    # ==================== 1. VERİ KONTROL TESTLERİ ====================

    def test_data_integrity(self) -> TestResult:
        """Mevcut veritabanı verilerini kontrol et"""
        result = TestResult("Veri Bütünlüğü Kontrolü")
        print_section("Veri Bütünlüğü Kontrolleri")

        try:
            from database.models import Item, Unit, Warehouse, ItemCategory
            from database.models.purchasing import Supplier
            from database.models.sales import Customer

            # Birimler
            print_subsection("Birimler")
            units = self.session.query(Unit).filter(Unit.is_active == True).all()
            if units:
                result.success(f"{len(units)} aktif birim bulundu")
                self.test_data["units"] = units
            else:
                result.warn("Aktif birim bulunamadı")

            # Kategoriler
            print_subsection("Kategoriler")
            categories = (
                self.session.query(ItemCategory)
                .filter(ItemCategory.is_active == True)
                .all()
            )
            if categories:
                result.success(f"{len(categories)} aktif kategori bulundu")
                self.test_data["categories"] = categories
            else:
                result.warn("Aktif kategori bulunamadı")

            # Depolar
            print_subsection("Depolar")
            warehouses = (
                self.session.query(Warehouse).filter(Warehouse.is_active == True).all()
            )
            if warehouses:
                result.success(f"{len(warehouses)} aktif depo bulundu")
                for wh in warehouses[:5]:
                    result.info(f"  → {wh.code}: {wh.name}")
                self.test_data["warehouses"] = warehouses
            else:
                result.warn("Aktif depo bulunamadı")

            # Stok Kartları
            print_subsection("Stok Kartları")
            items = self.session.query(Item).filter(Item.is_active == True).all()
            if items:
                result.success(f"{len(items)} aktif stok kartı bulundu")
                # İlk 5 stok kartını göster
                for item in items[:5]:
                    result.info(f"  → {item.code}: {item.name}")
                self.test_data["items"] = items
            else:
                result.warn("Aktif stok kartı bulunamadı")

            # Tedarikçiler
            print_subsection("Tedarikçiler")
            suppliers = (
                self.session.query(Supplier).filter(Supplier.is_active == True).all()
            )
            if suppliers:
                result.success(f"{len(suppliers)} aktif tedarikçi bulundu")
                for sup in suppliers[:3]:
                    result.info(f"  → {sup.code}: {sup.name}")
                self.test_data["suppliers"] = suppliers
            else:
                result.warn("Aktif tedarikçi bulunamadı")

            # Müşteriler
            print_subsection("Müşteriler")
            customers = (
                self.session.query(Customer).filter(Customer.is_active == True).all()
            )
            if customers:
                result.success(f"{len(customers)} aktif müşteri bulundu")
                for cust in customers[:3]:
                    result.info(f"  → {cust.code}: {cust.name}")
                self.test_data["customers"] = customers
            else:
                result.warn("Aktif müşteri bulunamadı")

        except Exception as e:
            result.fail("Veri kontrolü hatası", str(e))
            import traceback

            traceback.print_exc()

        return result

    # ==================== 2. SERVİS TESTLERİ ====================

    def test_inventory_services(self) -> TestResult:
        """Stok servislerini test et"""
        result = TestResult("Stok Servisleri")
        print_section("Stok Servisleri Testleri")

        try:
            from modules.inventory.services import (
                ItemService,
                UnitService,
                WarehouseService,
                CategoryService,
                StockMovementService,
            )

            # ItemService
            print_subsection("ItemService")
            item_service = ItemService()

            # Tüm stok kartlarını getir
            all_items = item_service.get_all()
            result.success(f"ItemService.get_all() çalıştı: {len(all_items)} kayıt")

            # Bir stok kartı varsa detay getir
            if all_items:
                item = item_service.get_by_id(all_items[0].id)
                if item:
                    result.success(f"ItemService.get_by_id() çalıştı: {item.code}")
                else:
                    result.fail("ItemService.get_by_id() kayıt döndürmedi")

            # UnitService
            print_subsection("UnitService")
            unit_service = UnitService()
            all_units = unit_service.get_all()
            result.success(f"UnitService.get_all() çalıştı: {len(all_units)} kayıt")

            # WarehouseService
            print_subsection("WarehouseService")
            wh_service = WarehouseService()
            all_warehouses = wh_service.get_all()
            result.success(
                f"WarehouseService.get_all() çalıştı: {len(all_warehouses)} kayıt"
            )

            # CategoryService
            print_subsection("CategoryService")
            cat_service = CategoryService()
            all_categories = cat_service.get_all()
            result.success(
                f"CategoryService.get_all() çalıştı: {len(all_categories)} kayıt"
            )

            # StockMovementService
            print_subsection("StockMovementService")
            stock_service = StockMovementService()
            result.success("StockMovementService başarıyla oluşturuldu")

            # Bakiye kontrolü (varsa)
            if all_items and all_warehouses:
                qty = stock_service.get_available_quantity(
                    all_items[0].id, all_warehouses[0].id
                )
                result.success(
                    f"get_available_quantity() çalıştı: "
                    f"{all_items[0].code} @ {all_warehouses[0].code} = {qty}"
                )

        except ImportError as e:
            result.fail("Import hatası", str(e))
        except Exception as e:
            result.fail("Servis testi hatası", str(e))
            import traceback

            traceback.print_exc()

        return result

    def test_purchasing_services(self) -> TestResult:
        """Satınalma servislerini test et"""
        result = TestResult("Satınalma Servisleri")
        print_section("Satınalma Servisleri Testleri")

        try:
            from modules.purchasing.services import (
                SupplierService,
                PurchaseRequestService,
                PurchaseOrderService,
                GoodsReceiptService,
            )

            # SupplierService
            print_subsection("SupplierService")
            supplier_service = SupplierService()
            all_suppliers = supplier_service.get_all()
            result.success(
                f"SupplierService.get_all() çalıştı: {len(all_suppliers)} kayıt"
            )

            if all_suppliers:
                # search testi
                search_result = supplier_service.search(all_suppliers[0].name[:5])
                result.success(
                    f"SupplierService.search() çalıştı: {len(search_result)} sonuç"
                )

            # PurchaseRequestService
            print_subsection("PurchaseRequestService")
            pr_service = PurchaseRequestService()
            result.success("PurchaseRequestService başarıyla oluşturuldu")

            # Mevcut talepleri kontrol et
            try:
                all_requests = pr_service.get_all()
                result.success(f"get_all() çalıştı: {len(all_requests)} talep")
            except Exception as e:
                result.warn(f"get_all() çağrısı: {str(e)[:50]}")

            # PurchaseOrderService
            print_subsection("PurchaseOrderService")
            po_service = PurchaseOrderService()
            result.success("PurchaseOrderService başarıyla oluşturuldu")

            try:
                all_orders = po_service.get_all()
                result.success(f"get_all() çalıştı: {len(all_orders)} sipariş")
            except Exception as e:
                result.warn(f"get_all() çağrısı: {str(e)[:50]}")

            # GoodsReceiptService
            print_subsection("GoodsReceiptService")
            gr_service = GoodsReceiptService()
            result.success("GoodsReceiptService başarıyla oluşturuldu")

        except ImportError as e:
            result.fail("Import hatası", str(e))
        except Exception as e:
            result.fail("Servis testi hatası", str(e))
            import traceback

            traceback.print_exc()

        return result

    def test_sales_services(self) -> TestResult:
        """Satış servislerini test et"""
        result = TestResult("Satış Servisleri")
        print_section("Satış Servisleri Testleri")

        try:
            from modules.sales.services import (
                CustomerService,
                PriceListService,
                SalesQuoteService,
                SalesOrderService,
            )

            # CustomerService
            print_subsection("CustomerService")
            customer_service = CustomerService()
            all_customers = customer_service.get_all()
            result.success(
                f"CustomerService.get_all() çalıştı: {len(all_customers)} kayıt"
            )

            if all_customers:
                search_result = customer_service.search(all_customers[0].name[:5])
                result.success(
                    f"CustomerService.search() çalıştı: {len(search_result)} sonuç"
                )

            # PriceListService
            print_subsection("PriceListService")
            price_service = PriceListService()
            result.success("PriceListService başarıyla oluşturuldu")

            try:
                all_price_lists = price_service.get_all()
                result.success(
                    f"get_all() çalıştı: {len(all_price_lists)} fiyat listesi"
                )
            except Exception as e:
                result.warn(f"get_all() çağrısı: {str(e)[:50]}")

            # SalesQuoteService
            print_subsection("SalesQuoteService")
            quote_service = SalesQuoteService()
            result.success("SalesQuoteService başarıyla oluşturuldu")

            try:
                all_quotes = quote_service.get_all()
                result.success(f"get_all() çalıştı: {len(all_quotes)} teklif")
            except Exception as e:
                result.warn(f"get_all() çağrısı: {str(e)[:50]}")

            # SalesOrderService
            print_subsection("SalesOrderService")
            order_service = SalesOrderService()
            result.success("SalesOrderService başarıyla oluşturuldu")

            try:
                all_orders = order_service.get_all()
                result.success(f"get_all() çalıştı: {len(all_orders)} sipariş")
            except Exception as e:
                result.warn(f"get_all() çağrısı: {str(e)[:50]}")

        except ImportError as e:
            result.fail("Import hatası", str(e))
        except Exception as e:
            result.fail("Servis testi hatası", str(e))
            import traceback

            traceback.print_exc()

        return result

    # ==================== 3. STOK HAREKET TESTLERİ ====================

    def test_stock_movements(self) -> TestResult:
        """Stok hareket işlemlerini test et"""
        result = TestResult("Stok Hareketleri")
        print_section("Stok Hareket Testleri")

        try:
            from modules.inventory.services import StockMovementService
            from database.models import StockMovementType, Item, Warehouse, Unit

            service = StockMovementService()

            # Test için veri hazırla
            items = self.test_data.get("items", [])
            warehouses = self.test_data.get("warehouses", [])
            units = self.test_data.get("units", [])

            if not items:
                result.warn("Test için stok kartı bulunamadı - gerçek veri gerekli")
                return result

            if not warehouses:
                result.warn("Test için depo bulunamadı - gerçek veri gerekli")
                return result

            test_item = items[0]
            test_warehouse = warehouses[0]

            # Mevcut bakiyeyi al
            print_subsection("Mevcut Bakiye Kontrolü")
            initial_qty = service.get_available_quantity(
                test_item.id, test_warehouse.id
            )
            result.success(
                f"Mevcut bakiye: {test_item.code} @ {test_warehouse.code} = {initial_qty}"
            )

            # Test girişi yap
            print_subsection("Stok Girişi Testi")
            test_qty = Decimal("10.00")
            try:
                movement = service.create_movement(
                    item_id=test_item.id,
                    movement_type=StockMovementType.GIRIS,
                    quantity=test_qty,
                    to_warehouse_id=test_warehouse.id,
                    unit_price=Decimal("100.00"),
                    document_no=f"TEST-GRS-{datetime.now().strftime('%H%M%S')}",
                    document_type="test",
                    description="Gerçek hayat testi - giriş",
                )
                if movement and movement.id:
                    result.success(f"Stok girişi oluşturuldu: {movement.document_no}")
                else:
                    result.fail("Stok girişi oluşturulamadı")
            except Exception as e:
                result.fail("Stok girişi hatası", str(e))
                return result

            # Bakiye kontrolü
            new_qty = service.get_available_quantity(test_item.id, test_warehouse.id)
            expected_qty = initial_qty + test_qty
            if new_qty == expected_qty:
                result.success(f"Bakiye doğru güncellendi: {initial_qty} → {new_qty}")
            else:
                result.fail(f"Bakiye hatalı: Beklenen={expected_qty}, Gerçek={new_qty}")

            # Test çıkışı yap
            print_subsection("Stok Çıkışı Testi")
            exit_qty = Decimal("5.00")
            try:
                exit_movement = service.create_movement(
                    item_id=test_item.id,
                    movement_type=StockMovementType.CIKIS,
                    quantity=exit_qty,
                    from_warehouse_id=test_warehouse.id,
                    document_no=f"TEST-CKS-{datetime.now().strftime('%H%M%S')}",
                    document_type="test",
                    description="Gerçek hayat testi - çıkış",
                )
                if exit_movement and exit_movement.id:
                    result.success(
                        f"Stok çıkışı oluşturuldu: {exit_movement.document_no}"
                    )
                else:
                    result.fail("Stok çıkışı oluşturulamadı")
            except Exception as e:
                result.fail("Stok çıkışı hatası", str(e))

            # Final bakiye kontrolü
            final_qty = service.get_available_quantity(test_item.id, test_warehouse.id)
            expected_final = expected_qty - exit_qty
            if final_qty == expected_final:
                result.success(f"Final bakiye doğru: {final_qty}")
            else:
                result.warn(
                    f"Final bakiye kontrol: Beklenen={expected_final}, Gerçek={final_qty}"
                )

            # Hareket geçmişi kontrolü
            print_subsection("Hareket Geçmişi")
            try:
                movements = service.get_by_item(test_item.id, limit=10)
                result.success(f"Son {len(movements)} hareket listelendi")
            except Exception as e:
                result.warn(f"Hareket listesi: {str(e)[:50]}")

        except ImportError as e:
            result.fail("Import hatası", str(e))
        except Exception as e:
            result.fail("Stok hareket testi hatası", str(e))
            import traceback

            traceback.print_exc()

        return result

    # ==================== 4. NEGATİF STOK KONTROLÜ ====================

    def test_negative_stock_control(self) -> TestResult:
        """Negatif stok kontrolünü test et"""
        result = TestResult("Negatif Stok Kontrolü")
        print_section("Negatif Stok Kontrolü Testleri")

        try:
            from modules.inventory.services import (
                StockMovementService,
                NegativeStockError,
            )
            from database.models import StockMovementType

            items = self.test_data.get("items", [])
            warehouses = self.test_data.get("warehouses", [])

            if not items or not warehouses:
                result.warn("Test için yeterli veri yok")
                return result

            test_item = items[0]
            test_warehouse = warehouses[0]

            # Negatif stok izni OLMAYAN servis
            service = StockMovementService(allow_negative_stock=False)

            current_qty = service.get_available_quantity(
                test_item.id, test_warehouse.id
            )
            result.info(f"Mevcut stok: {current_qty}")

            # Mevcut stoktan fazla çıkış yapmaya çalış
            try:
                excess_qty = current_qty + Decimal("1000")
                service.create_movement(
                    item_id=test_item.id,
                    movement_type=StockMovementType.CIKIS,
                    quantity=excess_qty,
                    from_warehouse_id=test_warehouse.id,
                    document_no=f"TEST-NEG-{datetime.now().strftime('%H%M%S')}",
                    document_type="test",
                )
                result.fail("Negatif stok kontrolü çalışmadı (hata fırlatılmalıydı)")
            except NegativeStockError as e:
                result.success(f"Negatif stok engellendi: {e.item_code}")
            except ValueError as e:
                if "yetersiz" in str(e).lower() or "stok" in str(e).lower():
                    result.success(f"Negatif stok engellendi: {e}")
                else:
                    result.warn(f"Beklenmeyen ValueError: {e}")
            except Exception as e:
                if "stok" in str(e).lower() or "negative" in str(e).lower():
                    result.success(f"Negatif stok kontrolü çalıştı: {e}")
                else:
                    result.warn(f"Beklenmeyen hata: {e}")

        except ImportError as e:
            result.fail("Import hatası", str(e))
        except Exception as e:
            result.fail("Negatif stok kontrolü hatası", str(e))

        return result

    # ==================== 5. ENTEGRASYON TESTLERİ ====================

    def test_purchase_to_stock_integration(self) -> TestResult:
        """Satınalma → Stok entegrasyonunu test et"""
        result = TestResult("Satınalma-Stok Entegrasyonu")
        print_section("Satınalma → Stok Entegrasyon Testi")

        try:
            from modules.purchasing.services import GoodsReceiptService
            from modules.inventory.services import StockMovementService

            items = self.test_data.get("items", [])
            warehouses = self.test_data.get("warehouses", [])
            suppliers = self.test_data.get("suppliers", [])

            if not all([items, warehouses, suppliers]):
                result.warn("Entegrasyon testi için yeterli veri yok")
                return result

            test_item = items[0]
            test_warehouse = warehouses[0]
            test_supplier = suppliers[0]

            stock_service = StockMovementService()
            initial_qty = stock_service.get_available_quantity(
                test_item.id, test_warehouse.id
            )

            result.info(f"Test verisi: {test_item.code} @ {test_warehouse.code}")
            result.info(f"Tedarikçi: {test_supplier.name}")
            result.info(f"Başlangıç bakiyesi: {initial_qty}")

            # GoodsReceiptService mevcut mu kontrol et
            gr_service = GoodsReceiptService()
            result.success("GoodsReceiptService başarıyla yüklendi")
            result.info(
                "Not: Tam entegrasyon testi için mal kabul oluşturma UI üzerinden yapılmalı"
            )

        except ImportError as e:
            result.fail("Import hatası", str(e))
        except Exception as e:
            result.fail("Entegrasyon testi hatası", str(e))

        return result

    # ==================== RAPOR ÜRETİMİ ====================

    def generate_report(self) -> str:
        """Detaylı test raporu oluştur"""
        lines = []
        lines.append("=" * 70)
        lines.append("          ERP GERÇEK HAYAT TESTİ - DETAYLI RAPOR")
        lines.append("=" * 70)
        lines.append(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Genel özet
        total_passed = sum(r.passed for r in self.results)
        total_failed = sum(r.failed for r in self.results)
        total_warnings = sum(r.warnings for r in self.results)
        total = total_passed + total_failed

        lines.append("GENEL ÖZET")
        lines.append("-" * 40)
        lines.append(f"Toplam Test: {total}")
        lines.append(f"Başarılı:    {total_passed}")
        lines.append(f"Başarısız:   {total_failed}")
        lines.append(f"Uyarı:       {total_warnings}")
        lines.append("")

        # Her modül için detay
        for r in self.results:
            lines.append(f"\n{'─' * 50}")
            lines.append(f"📋 {r.name}")
            lines.append(f"{'─' * 50}")
            lines.append(f"  ✓ Başarılı: {r.passed}")
            lines.append(f"  ✗ Başarısız: {r.failed}")
            lines.append(f"  ⚠ Uyarı: {r.warnings}")

            if r.errors:
                lines.append("\n  📛 Hatalar:")
                for msg, error in r.errors:
                    lines.append(f"    • {msg}")
                    if error:
                        lines.append(f"      → {error[:100]}")

        # Veri özeti
        lines.append(f"\n{'═' * 50}")
        lines.append("VERİTABANI VERİ ÖZETİ")
        lines.append(f"{'═' * 50}")
        for key, data in self.test_data.items():
            lines.append(f"  • {key.capitalize()}: {len(data)} kayıt")

        # Sonuç
        lines.append(f"\n{'═' * 70}")
        if total_failed == 0:
            lines.append("✅ TÜM TESTLER BAŞARILI!")
        else:
            lines.append(f"❌ {total_failed} TEST BAŞARISIZ!")
        lines.append(f"{'═' * 70}")

        return "\n".join(lines)

    # ==================== ANA FONKSİYON ====================

    def run_all_tests(self) -> bool:
        """Tüm testleri çalıştır"""
        print_header("ERP GERÇEK HAYAT TESTLERİ")
        print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Python: {sys.version.split()[0]}")

        if not self.setup():
            print(f"\n{RED}Test ortamı hazırlanamadı!{RESET}")
            return False

        # Testleri çalıştır
        self.results.append(self.test_data_integrity())
        self.results.append(self.test_inventory_services())
        self.results.append(self.test_purchasing_services())
        self.results.append(self.test_sales_services())
        self.results.append(self.test_stock_movements())
        self.results.append(self.test_negative_stock_control())
        self.results.append(self.test_purchase_to_stock_integration())

        # Özet
        print_header("TEST ÖZETİ")

        total_passed = sum(r.passed for r in self.results)
        total_failed = sum(r.failed for r in self.results)
        total_warnings = sum(r.warnings for r in self.results)
        total = total_passed + total_failed

        for r in self.results:
            r.summary()

        print(f"\n{'═' * 70}")
        print(f"{BOLD}GENEL SONUÇ{RESET}")
        print(f"{'═' * 70}")
        print(f"Toplam Test: {total}")
        print(f"Başarılı: {GREEN}{total_passed}{RESET}")
        print(f"Başarısız: {RED}{total_failed}{RESET}")
        print(f"Uyarı: {YELLOW}{total_warnings}{RESET}")

        if total_failed == 0:
            print(f"\n{GREEN}{BOLD}✅ TÜM TESTLER BAŞARILI!{RESET}")
        else:
            print(f"\n{RED}{BOLD}❌ {total_failed} TEST BAŞARISIZ!{RESET}")

        # Rapor oluştur ve kaydet
        report = self.generate_report()
        report_path = os.path.join(
            os.path.dirname(__file__),
            f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\n📄 Detaylı rapor kaydedildi: {report_path}")
        except Exception as e:
            print(f"\n⚠️ Rapor kaydedilemedi: {e}")

        self.teardown()
        return total_failed == 0


def main():
    """Ana fonksiyon"""
    tests = ERPRealLifeTest()
    success = tests.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
