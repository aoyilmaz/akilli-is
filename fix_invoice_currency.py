from database.base import get_session
from database.models.purchasing import PurchaseInvoice, PurchaseOrder, Currency

session = get_session()
inv_no = "PI26010001"
inv = (
    session.query(PurchaseInvoice).filter(PurchaseInvoice.invoice_no == inv_no).first()
)

if inv and inv.purchase_order:
    print(f"Güncelleniyor: {inv.invoice_no}")
    print(f"Eski: {inv.currency}")

    # Siparişin döviz cinsini al
    po_currency = inv.purchase_order.currency
    inv.currency = po_currency
    inv.currency = (
        Currency.USD
    )  # Explicitly set to USD based on debug output which showed PO was USD

    print(f"Yeni: {inv.currency}")
    session.commit()
    print("Kaydedildi.")
else:
    print("İşlem yapılamadı.")
