"""
Emoji simgelerini ASCII ya da basit Unicode simgelerle değiştir
"""

import os

# Emoji -> Basit karakter eşleştirmesi
REPLACEMENTS = {
    '("👁")': '("Gör")',
    '("✏️")': '("Düz")',
    '("🗑")': '("Sil")',
    '("🗑️")': '("Sil")',
    '("📤")': '("Gön")',
    '("📥")': '("Al")',
    '("✅")': '("On")',
    '("❌")': '("İpt")',
    '("💰")': '("Öde")',
    '("🚚")': '("Sev")',
    '("📝")': '("Yaz")',
    '("📋")': '("Lst")',
    '("🔄")': '("Yen")',
    '("➕")': '("+")',
}

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


def replace_emojis(filepath):
    if not os.path.exists(filepath):
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    changes = 0

    for emoji, replacement in REPLACEMENTS.items():
        if emoji in content:
            content = content.replace(emoji, replacement)
            changes += 1

    if content != original:
        try:
            compile(content, filepath, "exec")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✓ {filepath}: {changes} değişiklik")
            return True
        except SyntaxError as e:
            print(f"⚠ {filepath}: Syntax hatası {e.lineno}")
            return False

    print(f"○ {filepath}: Değişiklik yok")
    return False


if __name__ == "__main__":
    total = 0
    for f in FILES:
        if replace_emojis(f):
            total += 1
    print(f"\nToplam: {total} dosya güncellendi")
