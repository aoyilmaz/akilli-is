"""
Tüm liste sayfalarına Qt simgelerini ekle
"""

import os
import re


# Import satırlarını güncelle
def update_imports(content):
    # QStyle ve QApplication import et
    if "QStyle" not in content:
        content = content.replace(
            "from PyQt6.QtWidgets import (",
            "from PyQt6.QtWidgets import (\n    QStyle, QApplication,",
        )
    elif "QApplication" not in content:
        content = content.replace("QStyle,", "QStyle, QApplication,")

    # QSize import et
    if "QSize" not in content and "from PyQt6.QtCore import" in content:
        content = re.sub(
            r"from PyQt6\.QtCore import ([^\n]+)",
            r"from PyQt6.QtCore import \1, QSize",
            content,
        )

    return content


# Buton oluşturmayı güncelle
BUTTON_REPLACEMENTS = [
    # View button
    (
        r'(\w+)_btn = QPushButton\("Gör"\)',
        r"\1_btn = QPushButton()\n            \1_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))\n            \1_btn.setIconSize(QSize(16, 16))",
    ),
    (
        r'(\w+)_btn = QPushButton\("👁"\)',
        r"\1_btn = QPushButton()\n            \1_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))\n            \1_btn.setIconSize(QSize(16, 16))",
    ),
    # Edit button
    (
        r'(\w+)_btn = QPushButton\("Düz"\)',
        r"\1_btn = QPushButton()\n            \1_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))\n            \1_btn.setIconSize(QSize(16, 16))",
    ),
    (
        r'(\w+)_btn = QPushButton\("✏️"\)',
        r"\1_btn = QPushButton()\n            \1_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))\n            \1_btn.setIconSize(QSize(16, 16))",
    ),
    # Delete button
    (
        r'(\w+)_btn = QPushButton\("Sil"\)',
        r"\1_btn = QPushButton()\n            \1_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon))\n            \1_btn.setIconSize(QSize(16, 16))",
    ),
    (
        r'(\w+)_btn = QPushButton\("🗑"\)',
        r"\1_btn = QPushButton()\n            \1_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon))\n            \1_btn.setIconSize(QSize(16, 16))",
    ),
    # Send/Approve button
    (
        r'(\w+)_btn = QPushButton\("Gön"\)',
        r"\1_btn = QPushButton()\n            \1_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))\n            \1_btn.setIconSize(QSize(16, 16))",
    ),
    (
        r'(\w+)_btn = QPushButton\("On"\)',
        r"\1_btn = QPushButton()\n            \1_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))\n            \1_btn.setIconSize(QSize(16, 16))",
    ),
    # Receive button
    (
        r'(\w+)_btn = QPushButton\("Al"\)',
        r"\1_btn = QPushButton()\n            \1_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowDown))\n            \1_btn.setIconSize(QSize(16, 16))",
    ),
    # Cancel button
    (
        r'(\w+)_btn = QPushButton\("İpt"\)',
        r"\1_btn = QPushButton()\n            \1_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))\n            \1_btn.setIconSize(QSize(16, 16))",
    ),
    # Pay button
    (
        r'(\w+)_btn = QPushButton\("Öde"\)',
        r"\1_btn = QPushButton()\n            \1_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogYesButton))\n            \1_btn.setIconSize(QSize(16, 16))",
    ),
    # Ship button (Sev)
    (
        r'(\w+)_btn = QPushButton\("Sev"\)',
        r"\1_btn = QPushButton()\n            \1_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowRight))\n            \1_btn.setIconSize(QSize(16, 16))",
    ),
]


def add_style_variable(content):
    """btn_layout tanımından sonra style değişkeni ekle"""
    if "style = QApplication.style()" in content:
        return content

    # btn_layout.setSpacing satırından sonra style ekle
    pattern = r"(btn_layout\.setSpacing\(\d+\))"
    if re.search(pattern, content):
        content = re.sub(
            pattern,
            r"\1\n\n            style = QApplication.style()",
            content,
            count=1,  # Sadece ilk eşleşmeyi değiştir - sonra hepsini regex ile bul
        )

    return content


def update_file(filepath):
    if not os.path.exists(filepath):
        print(f"⚠ {filepath}: Dosya bulunamadı")
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # Import'ları güncelle
    content = update_imports(content)

    # Style değişkeni ekle (her btn_layout.setSpacing sonrasına)
    content = add_style_variable(content)

    # Buton tanımlarını güncelle
    for pattern, replacement in BUTTON_REPLACEMENTS:
        content = re.sub(pattern, replacement, content)

    # setFixedSize(40, 28) -> setFixedSize(32, 28)
    content = content.replace("setFixedSize(40, 28)", "setFixedSize(32, 28)")

    if content != original:
        try:
            compile(content, filepath, "exec")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✓ {filepath}")
            return True
        except SyntaxError as e:
            print(f"⚠ {filepath}: Syntax hatası line {e.lineno}")
            # Syntax hatası varsa değişiklikleri kaydetme
            return False

    print(f"○ {filepath}: Değişiklik yok")
    return False


FILES = [
    # Purchasing
    "modules/purchasing/views/goods_receipt_list.py",
    "modules/purchasing/views/purchase_invoice_list.py",
    "modules/purchasing/views/purchase_order_list.py",
    "modules/purchasing/views/purchase_request_list.py",
    "modules/purchasing/views/supplier_list.py",
    # Sales (customer_list zaten yapıldı)
    "modules/sales/views/delivery_note_list.py",
    "modules/sales/views/invoice_list.py",
    "modules/sales/views/sales_order_list.py",
    "modules/sales/views/sales_quote_list.py",
    "modules/sales/views/price_list_list.py",
]

if __name__ == "__main__":
    print("Qt simgeleri ekleniyor...")
    print("=" * 50)
    total = 0
    for f in FILES:
        if update_file(f):
            total += 1
    print("=" * 50)
    print(f"Toplam: {total} dosya güncellendi")
