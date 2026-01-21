import sys
import os
from decimal import Decimal

# Proje kök dizinini ekle
sys.path.append(os.getcwd())

from database import get_session
from database.models.inventory import StockMovement
from database.models.purchasing import GoodsReceipt, GoodsReceiptItem
from database.models.common import Currency as FinanceCurrency
from sqlalchemy.orm import joinedload


def fix_missing_data():
    session = get_session()

    print("=== Stok Hareketi Veri Düzeltme İşlemi ===\n")

    try:
        # Fiyatı 0 olan SATIN_ALMA hareketlerini bul (Mal Kabul kaynaklı)
        movements = (
            session.query(StockMovement)
            .filter(
                StockMovement.document_type == "goods_receipt",
                StockMovement.unit_price == 0,
            )
            .all()
        )

        print(f"Düzeltilecek {len(movements)} hareket bulundu.\n")

        updated_count = 0

        # Döviz Cache
        currency_map = {}

        for mov in movements:
            if not mov.document_no:
                continue

            # İlgili Mal Kabulü bul
            receipt = (
                session.query(GoodsReceipt)
                .filter(GoodsReceipt.receipt_no == mov.document_no)
                .options(
                    joinedload(GoodsReceipt.purchase_order),
                    joinedload(GoodsReceipt.items).joinedload(GoodsReceiptItem.po_item),
                )
                .first()
            )

            if not receipt:
                print(f"UYARI: {mov.document_no} nolu mal kabul bulunamadı!")
                continue

            # Harekete karşılık gelen item'ı bul
            # (Basit eşleştirme: item_id üzerinden)
            # Not: Aynı item'dan birden fazla satır varsa sorun olabilir ama şimdilik ilkini alalım.
            gr_item = None
            for item in receipt.items:
                if item.item_id == mov.item_id:
                    gr_item = item
                    break

            if not gr_item:
                print(f"UYARI: {mov.document_no} içinde Item {mov.item_id} bulunamadı!")
                continue

            # Verileri al
            changes = []

            # 1. Birim
            if not mov.unit_id and gr_item.unit_id:
                mov.unit_id = gr_item.unit_id
                changes.append(f"Birim: {gr_item.unit_id}")

            # 2. Fiyat ve Döviz (Siparişten)
            if gr_item.po_item:
                po_item = gr_item.po_item
                po = receipt.purchase_order

                # Fiyat
                if mov.unit_price == 0:
                    mov.unit_price = po_item.unit_price
                    mov.total_price = Decimal(mov.quantity) * Decimal(
                        po_item.unit_price
                    )
                    changes.append(f"Fiyat: {po_item.unit_price}")

                # Döviz
                if not mov.currency_id and po:
                    currency_code = po.currency.value if po.currency else "TRY"

                    if currency_code in currency_map:
                        currency_id = currency_map[currency_code]
                    else:
                        fin_curr = (
                            session.query(FinanceCurrency)
                            .filter(FinanceCurrency.code == currency_code)
                            .first()
                        )
                        if fin_curr:
                            currency_id = fin_curr.id
                            currency_map[currency_code] = currency_id
                        else:
                            currency_id = None

                    if currency_id:
                        mov.currency_id = currency_id
                        mov.exchange_rate = po.exchange_rate or 1
                        changes.append(f"Döviz: {currency_code}")

            if changes:
                print(
                    f"Mov {mov.id} ({mov.document_no}) güncellendi: {', '.join(changes)}"
                )
                updated_count += 1

        if updated_count > 0:
            session.commit()
            print(f"\nBaşarıyla {updated_count} kayıt güncellendi.")
        else:
            print("\nGüncellenecek kayıt bulunamadı.")

    except Exception as e:
        session.rollback()
        print(f"Hata: {e}")
        import traceback

        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    fix_missing_data()
