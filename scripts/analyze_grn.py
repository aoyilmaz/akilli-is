import sys
import os

# Proje kök dizinini ekle
sys.path.append(os.getcwd())

from database import get_session
from database.models.inventory import StockMovement
from database.models.purchasing import GoodsReceipt, GoodsReceiptItem
from sqlalchemy.orm import joinedload


def analyze_grn():
    session = get_session()
    grn_no = "GRN26010007"

    print(f"=== {grn_no} Analizi ===\n")

    try:
        # 1. Mal Kabul Kaydını Bul
        receipt = (
            session.query(GoodsReceipt)
            .filter(GoodsReceipt.receipt_no == grn_no)
            .options(
                joinedload(GoodsReceipt.items).joinedload(GoodsReceiptItem.po_item)
            )
            .first()
        )

        if not receipt:
            print(f"Mal Kabul (GoodsReceipt) bulunamadı: {grn_no}")
        else:
            print(f"Mal Kabul Bulundu: ID {receipt.id}, Tarih: {receipt.receipt_date}")
            print(f"Bağlı Sipariş ID: {receipt.purchase_order_id}")
            print("\nKalemler:")
            for item in receipt.items:
                print(
                    f" - Item ID: {item.item_id}, Miktar: {item.quantity}, Kabul: {item.accepted_quantity}"
                )
                print(f"   PO Item ID: {item.po_item_id}")
                if item.po_item:
                    print(
                        f"   Sipariş Fiyatı: {item.po_item.unit_price} (Currency ID: {item.po_item.order.currency if item.po_item.order else 'Unknown'})"
                    )
                else:
                    print(f"   Sipariş Kalemi İLİŞKİSİ YOK! Fiyat bilinemiyor.")

        print("\n" + "=" * 30 + "\n")

        # 2. Stok Hareketlerini Bul
        movements = (
            session.query(StockMovement)
            .filter(StockMovement.document_no == grn_no)
            .options(joinedload(StockMovement.unit), joinedload(StockMovement.currency))
            .all()
        )

        if not movements:
            print(f"Stok Hareketi (StockMovement) bulunamadı: {grn_no}")
        else:
            print(f"Stok Hareketleri Bulundu: {len(movements)} adet")
            for mov in movements:
                print("-" * 20)
                print(f"ID: {mov.id}")
                print(f"Stok: {mov.item_id}")
                print(f"Miktar: {mov.quantity}")
                print(
                    f"Birim ID: {mov.unit_id} ({mov.unit.code if mov.unit else 'None'})"
                )
                print(f"Birim Fiyat: {mov.unit_price}")
                print(f"Toplam Fiyat: {mov.total_price}")
                print(
                    f"Döviz ID: {mov.currency_id} ({mov.currency.code if mov.currency else 'None'})"
                )
                print(f"Kur: {mov.exchange_rate}")

    except Exception as e:
        print(f"Hata: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    analyze_grn()
