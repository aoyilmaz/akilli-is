"""
Inline stilleri kaldırma scripti
Tüm modül view dosyalarından setStyleSheet çağrılarını temizler
Böylece global theme.qss uygulanır
"""

import os
import re

# Temizlenecek modüller
MODULES = [
    "modules/inventory/views",
    "modules/sales/views",
    "modules/purchasing/views",
    "modules/production/views",
    "modules/accounting/views",
    "modules/finance/views",
    "modules/hr/views",
    "modules/quality/views",
]

# Korunacak dosyalar (özel stilli widget'lar)
SKIP_FILES = [
    "sidebar.py",
    "titlebar.py",
    "activity_bar.py",
]


def clean_inline_styles(filepath):
    """Dosyadan inline stilleri temizle"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # Çok satırlı setStyleSheet çağrılarını bul ve temizle
    # Pattern: widget.setStyleSheet("""...""") veya widget.setStyleSheet('...')

    # Önce _style_button, _style_input gibi helper metodları bul
    helper_methods = [
        r"def _style_\w+\(self[^)]*\):[^}]+?widget\.setStyleSheet\([^)]+\)",
        r"self\._style_\w+\([^)]+\)",
    ]

    # Multiline setStyleSheet çağrılarını kaldır
    # Pattern: .setStyleSheet(""" ... """) veya .setStyleSheet(''' ... ''')
    patterns = [
        # Triple quoted strings
        r'\.setStyleSheet\(\s*"""[^"]*"""\s*\)',
        r"\.setStyleSheet\(\s*'''[^']*'''\s*\)",
        # f-strings with triple quotes
        r'\.setStyleSheet\(\s*f"""[^"]*"""\s*\)',
        r"\.setStyleSheet\(\s*f'''[^']*'''\s*\)",
        # Single line
        r'\.setStyleSheet\("[^"]+"\)',
        r"\.setStyleSheet\('[^']+'\)",
    ]

    changes = 0
    for pattern in patterns:
        matches = re.findall(pattern, content, re.DOTALL)
        changes += len(matches)
        content = re.sub(pattern, "", content, flags=re.DOTALL)

    # Boş satırları temizle (3+ boş satırı 2'ye indir)
    content = re.sub(r"\n{4,}", "\n\n\n", content)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return changes
    return 0


def main():
    total_files = 0
    total_changes = 0

    for module_path in MODULES:
        if not os.path.exists(module_path):
            continue

        for filename in os.listdir(module_path):
            if not filename.endswith(".py"):
                continue
            if filename in SKIP_FILES:
                continue

            filepath = os.path.join(module_path, filename)
            changes = clean_inline_styles(filepath)

            if changes > 0:
                print(f"✓ {filepath}: {changes} inline stil kaldırıldı")
                total_files += 1
                total_changes += changes

    print(f"\n{'='*50}")
    print(f"Toplam: {total_files} dosya, {total_changes} inline stil kaldırıldı")
    print("Global theme.qss şimdi tüm widget'lara uygulanacak!")


if __name__ == "__main__":
    main()
