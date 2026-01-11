"""
GÜVENLI INLINE STİL TEMİZLEME
Sadece setStyleSheet satırlarını kaldırır, başka hiçbir şeye dokunmaz
"""

import os
import re

DIRECTORIES = [
    "modules/inventory/views",
    "modules/sales/views",
    "modules/purchasing/views",
    "modules/production/views",
    "modules/accounting/views",
    "modules/finance/views",
    "modules/hr/views",
    "modules/quality/views",
    "modules/reports/views",
    "modules/mrp/views",
    "ui/pages",
]

SKIP_FILES = [
    "sidebar.py",
    "titlebar.py",
    "activity_bar.py",
    "__init__.py",
]


def safe_remove_setstylesheet(filepath):
    """Sadece setStyleSheet satırlarını güvenli şekilde kaldır"""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    removed = 0

    while i < len(lines):
        line = lines[i]

        # setStyleSheet çağrısı içeren satır
        if ".setStyleSheet(" in line:
            # Parantez dengesi kontrol et
            open_parens = line.count("(")
            close_parens = line.count(")")
            balance = open_parens - close_parens

            if balance == 0:
                # Tek satırda tamamlanmış - atla
                removed += 1
                i += 1
                continue
            elif balance > 0:
                # Çok satırlı - kapanana kadar atla
                i += 1
                while i < len(lines) and balance > 0:
                    balance += lines[i].count("(") - lines[i].count(")")
                    i += 1
                removed += 1
                continue

        new_lines.append(line)
        i += 1

    if removed > 0:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    return removed


def main():
    total_files = 0
    total_removed = 0

    for dir_path in DIRECTORIES:
        if not os.path.exists(dir_path):
            continue

        for filename in os.listdir(dir_path):
            if filename in SKIP_FILES or not filename.endswith(".py"):
                continue

            filepath = os.path.join(dir_path, filename)

            removed = safe_remove_setstylesheet(filepath)

            if removed > 0:
                print(f"✓ {filepath}: {removed} setStyleSheet kaldırıldı")
                total_files += 1
                total_removed += removed

    print(f"\n{'='*60}")
    print(f"Toplam: {total_files} dosya, {total_removed} setStyleSheet kaldırıldı")


if __name__ == "__main__":
    main()
