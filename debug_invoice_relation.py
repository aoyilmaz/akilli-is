from database.base import get_session
from database.models.purchasing import PurchaseInvoice, PurchaseOrder, GoodsReceipt

session = get_session()
inv_no = "PI26010001"
inv = (
    session.query(PurchaseInvoice).filter(PurchaseInvoice.invoice_no == inv_no).first()
)

if inv:
    print(f"Fatura: {inv.invoice_no}")
    print(f"  Fatura Currency: {inv.currency}")
    print(f"  İlişkili Sipariş ID: {inv.purchase_order_id}")
    print(f"  İlişkili Mal Kabul ID: {inv.goods_receipt_id}")

    if inv.purchase_order:
        print(f"  Sipariş No: {inv.purchase_order.order_no}")
        print(f"  Sipariş Currency: {inv.purchase_order.currency}")
    else:
        print("  Sipariş bulunamadı.")

    if inv.goods_receipt:
        print(f"  Mal Kabul No: {inv.goods_receipt.receipt_no}")
        # Mal kabulde currency yok, siparişten gelir
else:
    print(f"{inv_no} bulunamadı.")
