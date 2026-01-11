"""
İşlem butonlarından inline setStyleSheet çağrılarını kaldır - Sadece satırları kaldır
"""

import os
import re


def clean_action_btn_styles(filepath):
    """Dosyadan action button inline stillerini kaldır"""
    if not os.path.exists(filepath):
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    removed = 0

    for line in lines:
        # setStyleSheet(_action_btn_style(...)) satırlarını atla
        if ".setStyleSheet(self._action_btn_style(" in line:
            removed += 1
            continue
        new_lines.append(line)

    if removed > 0:
        content = "".join(new_lines)
        try:
            compile(content, filepath, "exec")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✓ {filepath}: {removed} setStyleSheet satırı kaldırıldı")
            return True
        except SyntaxError as e:
            print(f"⚠ {filepath}: Syntax hatası line {e.lineno}")
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
        if clean_action_btn_styles(f):
            total += 1
    print(f"\nToplam: {total} dosya güncellendi")
