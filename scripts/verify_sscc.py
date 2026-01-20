import sys
import os

# Proje kök dizinini path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.base import SessionLocal
from modules.inventory.services import SSCCService, ItemService, UnitService
from database.models import TransportUnitType


def verify_sscc():
    session = SessionLocal()
    sscc_service = SSCCService(session)
    # Diğer servisler kendi session'larını yönetiyor (ServiceBase default)
    # Session paylaşımı gerektiğinde bu servislerin de güncellenmesi gerekir
    # Şimdilik verify script'inde okuma yaptıkları için sorun yok
    item_service = ItemService()
    unit_service = UnitService()

    try:
        print("=== SSCC Doğrulama Başlıyor ===")

        # 1. Örnek veri hazırlığı
        items = item_service.get_all()
        if items:
            items = items[:1]
        if not items:
            print("HATA: Test için stok kartı bulunamadı!")
            return

        test_item = items[0]
        print(f"Test Stoku: {test_item.code} - {test_item.name}")

        units = unit_service.get_all()
        unit_id = units[0].id if units else None

        # 2. SSCC Oluşturma
        print("\n[1] SSCC Oluşturuluyor...")
        tu = sscc_service.create_transport_unit(
            unit_type=TransportUnitType.PALET, notes="Otomatik test paleti"
        )
        print(f"Oluşturulan SSCC: {tu.sscc}")
        print(f"Durum: {tu.status.value}")

        # 3. Ürün Ekleme
        print("\n[2] Ürün Ekleniyor...")
        qty = 10
        item = sscc_service.add_item_to_unit(
            transport_unit_id=tu.id, item_id=test_item.id, quantity=qty, unit_id=unit_id
        )
        print(f"Eklenen Miktar: {item.quantity}")

        # 4. Kontrol
        print("\n[3] İçerik Kontrol Ediliyor...")
        tu_items = sscc_service.get_unit_items(tu.id)
        print(f"Toplam Kalem Sayısı: {len(tu_items)}")

        if len(tu_items) == 1 and tu_items[0].quantity == qty:
            print("✅ BAŞARILI: Ürün ekleme doğrulandı")
        else:
            print("❌ BAŞARISIZ: Ürün miktarı veya kalem sayısı hatalı")

        # 5. Kapatma
        print("\n[4] Palet Kapatılıyor...")
        closed_tu = sscc_service.close_unit(tu.id)
        print(f"Yeni Durum: {closed_tu.status.value}")

        if closed_tu.status.name == "KAPALI":
            print("✅ BAŞARILI: Kapatma işlemi doğrulandı")
        else:
            print("❌ BAŞARISIZ: Kapatma işlemi hatalı")

    except Exception as e:
        print(f"❌ HATA OLUŞTU: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    verify_sscc()
