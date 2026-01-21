from database.base import get_session
from database.models.purchasing import PurchaseInvoice, Currency

session = get_session()
invoices = session.query(PurchaseInvoice).all()

print(f"Toplam Fatura Sayısı: {len(invoices)}")
for inv in invoices:
    print(f"Fatura No: {inv.invoice_no}")
    print(f"  Currency (Raw): {inv.currency!r}")
    print(f"  Currency Type: {type(inv.currency)}")
    if hasattr(inv.currency, "value"):
        print(f"  Currency Value: {inv.currency.value}")
    else:
        print("  Currency has no .value attribute")
    print("-" * 30)
