import sys
import os

# Proje dizinini path'e ekle
sys.path.append(os.getcwd())

from database.base import get_session, Base
from database.models.inventory import Warehouse, WarehouseLocation


def create_warehouses():
    session = get_session()
    print("🚀 Depo kurulum işlemi başlatılıyor...")

    # PVC Streç Fabrikası İçin Depo Listesi
    warehouses_data = [
        {
            "code": "DEP-01",
            "name": "Hammadde Deposu",
            "short_name": "HM Depo",
            "description": "PVC granül, reçine, DOTP yağı ve sıvı katkıların bulunduğu ana depo.",
            "warehouse_type": "general",
            "is_production": False,
            "locations": ["A-01-01", "A-01-02", "B-01-01", "TANK-01", "SILO-01"],
        },
        {
            "code": "DEP-02",
            "name": "Üretim Sahası (WIP)",
            "short_name": "Üretim",
            "description": "Ekstrüder ve dilimleme makinelerinin bulunduğu aktif üretim alanı.",
            "warehouse_type": "production",
            "is_production": True,
            "allow_negative": True,
            "locations": ["EXT-HAT-01", "EXT-HAT-02", "DILIMLEME-01", "DILIMLEME-02"],
        },
        {
            "code": "DEP-03",
            "name": "Yarı Mamul Deposu",
            "short_name": "YM Depo",
            "description": "Dilimlenmeyi bekleyen Jumbo bobinlerin bekletildiği alan.",
            "warehouse_type": "general",
            "is_production": False,
            "locations": ["JUMBO-A1", "JUMBO-A2", "JUMBO-B1"],
        },
        {
            "code": "DEP-04",
            "name": "Mamul Sevkiyat Deposu",
            "short_name": "Sevkiyat",
            "description": "Satışa hazır, kolilenmiş ve paletlenmiş ürünler.",
            "warehouse_type": "general",
            "is_production": False,
            "locations": ["RAF-A-01", "RAF-A-02", "RAF-B-01", "ZEMIN-01"],
        },
        {
            "code": "DEP-05",
            "name": "Ambalaj ve Sarf Malzeme Deposu",
            "short_name": "Sarf",
            "description": "Masura, koli, etiket, streç, palet vb. malzemeler.",
            "warehouse_type": "general",
            "is_production": False,
            "locations": ["AMB-01", "AMB-02", "AMB-03"],
        },
        {
            "code": "DEP-06",
            "name": "Teknik ve Yedek Parça Deposu",
            "short_name": "Teknik",
            "description": "Makine yedek parçaları, rulmanlar, ısıtıcılar, yağlar.",
            "warehouse_type": "general",
            "is_production": False,
            "locations": ["YDK-01", "YDK-02", "BAKIM-DOLAP"],
        },
        {
            "code": "DEP-07",
            "name": "Karantina ve İade Deposu",
            "short_name": "Karantina",
            "description": "Kalite kontrolden geçmeyen veya müşteriden iade gelen ürünler.",
            "warehouse_type": "quarantine",
            "is_production": False,
            "locations": ["RED-01", "IADE-01"],
        },
    ]

    for w_data in warehouses_data:
        existing_warehouse = (
            session.query(Warehouse).filter(Warehouse.code == w_data["code"]).first()
        )

        if not existing_warehouse:
            loc_codes = w_data.pop("locations", [])
            new_warehouse = Warehouse(**w_data)
            session.add(new_warehouse)
            session.flush()

            print(f"✅ Depo oluşturuldu: {new_warehouse.name}")

            for loc_code in loc_codes:
                new_loc = WarehouseLocation(
                    warehouse_id=new_warehouse.id,
                    code=loc_code,
                    name=f"{w_data['short_name']} - {loc_code}",
                )
                session.add(new_loc)
        else:
            print(f"ℹ️  Depo zaten mevcut: {w_data['name']}")

    try:
        session.commit()
        print("\n🎉 Tüm depolar başarıyla oluşturuldu.")
    except Exception as e:
        session.rollback()
        print(f"\n❌ Hata: {str(e)}")
    finally:
        session.close()


if __name__ == "__main__":
    create_warehouses()
