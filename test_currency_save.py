from database.base import get_session
from database.models.purchasing import PurchaseInvoice, Currency, Supplier
from datetime import date
import random

session = get_session()

# Tedarikçi bul
sup = session.query(Supplier).first()
if not sup:
    # Tedarikçi yoksa oluştur
    sup = Supplier(code="SUP_TEST", name="Test Tedarikçi")
    session.add(sup)
    session.commit()

# USD ile fatura oluşturmayı dene (String olarak vererek)
inv_no = f"TEST_USD_{random.randint(1000,9999)}"
print(f"Deneme: {inv_no} currency='USD' ile...")

try:
    inv = PurchaseInvoice(
        invoice_no=inv_no,
        invoice_date=date.today(),
        supplier_id=sup.id,
        currency="USD",  # String olarak veriyorum!
    )
    session.add(inv)
    session.commit()

    # Geri oku (flush'tan öte commit sonrası yeni session/refresh ile görmek lazım)
    session.refresh(inv)
    print(f"Fatura oluşturuldu. ID: {inv.id}")
    print(f"Kaydedilen Currency: {inv.currency!r}")

    if inv.currency == Currency.USD:
        print("BAŞARILI: Enum'a dönüştü.")
    else:
        print("BAŞARISIZ: Enum'a dönüşmedi.")

except Exception as e:
    print("HATA:", e)
