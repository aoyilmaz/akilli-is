"""
Düğme boyutlarını güncelle - 32x32'den 40x28'e
"""

import os
import re


def update_button_sizes(filepath):
    if not os.path.exists(filepath):
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # setFixedSize(32, 32) -> setFixedSize(40, 28)
    content = content.replace("setFixedSize(32, 32)", "setFixedSize(40, 28)")

    if content != original:
        try:
            compile(content, filepath, "exec")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✓ {filepath}")
            return True
        except SyntaxError as e:
            print(f"⚠ {filepath}: Syntax hatası {e.lineno}")
            return False

    print(f"○ {filepath}: Değişiklik yok")
    return False


FILES = [
    "modules/finance/views/payment_list.py",
    "modules/finance/views/receipt_list.py",
    "modules/purchasing/views/goods_receipt_list.py",
    "modules/purchasing/views/purchase_invoice_list.py",
    "modules/purchasing/views/purchase_order_list.py",
    "modules/purchasing/views/purchase_request_list.py",
    "modules/purchasing/views/supplier_list.py",
    "modules/sales/views/customer_list.py",
    "modules/sales/views/delivery_note_list.py",
    "modules/sales/views/invoice_list.py",
    "modules/sales/views/sales_order_list.py",
    "modules/sales/views/sales_quote_list.py",
    "modules/sales/views/price_list_list.py",
]

if __name__ == "__main__":
    total = 0
    for f in FILES:
        if update_button_sizes(f):
            total += 1
    print(f"\nToplam: {total} dosya güncellendi")
