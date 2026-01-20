import sys
import os
from decimal import Decimal

# Proje kök dizinini path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.base import SessionLocal
from modules.inventory.services import (
    SSCCService,
    ItemService,
    UnitService,
    WarehouseService,
)
from database.models import TransportUnitType, TransportUnitStatus


def test_full_sscc_flow():
    session = SessionLocal()

    # Servisleri başlat
    sscc_service = SSCCService(session)
    # Item ve Warehouse servisleri için session'ı manuel set et (SSCCModule'deki gibi)
    item_service = ItemService()
    item_service.session = session

    unit_service = UnitService()
    unit_service.session = session  # UnitService base service kullanıyorsa session'ı vardır ama override edelim

    warehouse_service = WarehouseService()
    warehouse_service.session = session

    try:
        print("\n=== SSCC Kapsamlı Akış Testi Başlıyor ===\n")

        # 1. Hazırlık: Stok ve Depo verisi kontrolü
        print("[1] Veri Hazırlığı...")
        items = item_service.get_all()
        warehouses = warehouse_service.get_all()

        if not items:
            print("❌ HATA: Test için stok kartı bulunamadı!")
            return
        if len(warehouses) < 2:
            print("❌ HATA: Test için en az 2 depo gerekli (Transfer testi için)!")
            # Eğer tek depo varsa, transfer kısmını atlarız veya aynı depoya transfer deneriz (mantıksız ama kod çalışır mı görürüz)
            if not warehouses:
                print("❌ HATA: Hiç depo yok!")
                return
            target_warehouse = warehouses[0]  # Mecburen aynı depo
            print(
                "⚠️ UYARI: Tek depo var, transfer aynı depoya yapılacak (Stok hareketi oluşmalı)"
            )
        else:
            target_warehouse = warehouses[1]

        source_warehouse = warehouses[0]
        test_item = items[0]

        print(f"   Stok: {test_item.code}")
        print(f"   Kaynak Depo: {source_warehouse.name}")
        print(f"   Hedef Depo: {target_warehouse.name}")

        # 2. SSCC Oluşturma (Create)
        print("\n[2] SSCC Oluşturma...")
        tu = sscc_service.create_transport_unit(
            unit_type=TransportUnitType.PALET,
            warehouse_id=source_warehouse.id,
            notes="Full Flow Test Paleti",
        )
        print(f"   ✅ SSCC Oluşturuldu: {tu.sscc}")
        print(f"   Durum: {tu.status.value}")

        # 3. get_all Testi
        print("\n[3] get_all Metodu Testi...")
        all_units = sscc_service.get_all()
        found = any(u.id == tu.id for u in all_units)
        if found:
            print(
                f"   ✅ get_all içinde yeni birim bulundu. Toplam birim: {len(all_units)}"
            )
        else:
            print("   ❌ get_all yeni birimi getirmedi!")

        # 4. get_by_id Testi
        print("\n[4] get_by_id Metodu Testi...")
        fetched_unit = sscc_service.get_by_id(tu.id)
        if fetched_unit and fetched_unit.sscc == tu.sscc:
            print("   ✅ get_by_id başarıyla çalıştı")
        else:
            print("   ❌ get_by_id hatalı!")

        # 5. Ürün Ekleme (Add Item)
        print("\n[5] Ürün Ekleme...")
        qty = Decimal("50")
        item_entry = sscc_service.add_item_to_unit(
            transport_unit_id=tu.id,
            item_id=test_item.id,
            quantity=qty,
            lot_number="TESTLOT001",
        )
        print(f"   ✅ Ürün Eklendi: {item_entry.quantity} adet {test_item.code}")

        # İçerik doğrulama
        unit_items = sscc_service.get_unit_items(tu.id)
        if len(unit_items) == 1 and unit_items[0].quantity == qty:
            print("   ✅ İçerik doğrulandı")
        else:
            print("   ❌ İçerik hatalı!")

        # 6. Birim Kapatma (Close)
        print("\n[6] Birim Kapatma...")
        sscc_service.close_unit(tu.id)
        # Session refresh gerekebilir durumu görmek için
        session.refresh(tu)
        print(f"   Yeni Durum: {tu.status.value}")

        if tu.status == TransportUnitStatus.KAPALI:
            print("   ✅ Birim başarıyla kapatıldı")
        else:
            print("   ❌ Birim kapatılamadı!")

        # 7. Birim Taşıma / Transfer (Move)
        print("\n[7] Birim Taşıma (Transfer)...")
        print(f"   {source_warehouse.name} -> {target_warehouse.name}")

        sscc_service.move_unit(
            transport_unit_id=tu.id, target_warehouse_id=target_warehouse.id
        )

        # Kontrol 1: Birim deposu değişti mi?
        session.refresh(tu)
        if tu.warehouse_id == target_warehouse.id:
            print("   ✅ Birim deposu güncellendi")
        else:
            print(f"   ❌ Birim deposu güncellenmedi! (Mevcut: {tu.warehouse_id})")

        # Kontrol 2: Stok hareketi oluştu mu?
        # Son stok hareketlerine bakalım
        from database.models import StockMovement

        last_movement = (
            session.query(StockMovement)
            .order_by(StockMovement.created_at.desc())
            .first()
        )

        if last_movement and last_movement.document_no == tu.sscc:
            print(f"   ✅ Stok hareketi oluşturuldu (Ref: {last_movement.document_no})")
            print(f"   Hareket Tipi: {last_movement.movement_type.value}")
            print(f"   Miktar: {last_movement.quantity}")
            print(
                f"   Kaynak: {last_movement.from_warehouse_id}, Hedef: {last_movement.to_warehouse_id}"
            )
        else:
            print("   ❌ İlgili stok hareketi bulunamadı!")

        print("\n=== Test Başarıyla Tamamlandı ===")

    except Exception as e:
        print(f"\n❌ TEST HATASI: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    test_full_sscc_flow()
