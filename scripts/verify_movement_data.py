import sys
import os

# Proje kök dizinini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_session
from database.models import StockMovement
from sqlalchemy.orm import joinedload


def verify_data():
    session = get_session()
    try:
        # Son 5 hareketi çek (eager load ile)
        movements = (
            session.query(StockMovement)
            .options(
                joinedload(StockMovement.item),
                joinedload(StockMovement.unit),
                joinedload(StockMovement.from_warehouse),
                joinedload(StockMovement.to_warehouse),
            )
            .order_by(StockMovement.id.desc())
            .limit(5)
            .all()
        )

        print(f"Toplam {len(movements)} hareket bulundu.\n")

        for mov in movements:
            print("-" * 50)
            print(f"ID: {mov.id}")
            print(f"Tarih: {mov.movement_date}")
            print(f"Tip: {mov.movement_type}")

            # Item
            if mov.item:
                print(f"Stok: {mov.item.code} - {mov.item.name} (ID: {mov.item_id})")
            else:
                print(f"Stok: İLİŞKİ YOK! (ID: {mov.item_id})")

            # Unit
            print(f"Unit ID: {mov.unit_id}")
            if mov.unit:
                print(f"Birim: {mov.unit.code} (İlişkiden geldi)")
            else:
                print("Birim: İLİŞKİ YOK veya NULL")

            # Fiyat
            print(f"Miktar: {mov.quantity}")
            print(f"Birim Fiyat: {mov.unit_price}")
            print(f"Toplam Fiyat: {mov.total_price}")

    except Exception as e:
        print(f"Hata: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    verify_data()
