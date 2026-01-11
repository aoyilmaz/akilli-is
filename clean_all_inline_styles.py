"""
KAPSAMLI İNLINE STİL TEMİZLEME SCRIPTİ
Tüm modüllerdeki setStyleSheet() çağrılarını kaldırır
Sadece global tema (theme.qss) kullanılmasını sağlar
"""

import os
import re

# İşlenecek dizinler
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
    "ui/pages",
]

# Atlanacak dosyalar (core UI)
SKIP_FILES = [
    "sidebar.py",
    "titlebar.py",
    "activity_bar.py",
    "__init__.py",
    "__pycache__",
]

# setStyleSheet pattern'ları
PATTERNS = [
    # Tek satırlık: widget.setStyleSheet("...")
    r'^\s*[\w\.]+\.setStyleSheet\(["\'][^"\']*["\']\)\s*$',
    # Çok satırlık f-string: widget.setStyleSheet(f"""...""")
    r'^\s*[\w\.]+\.setStyleSheet\(f?"""[\s\S]*?"""\)\s*$',
    # Çok satırlık normal: widget.setStyleSheet("""...""")
    r'^\s*[\w\.]+\.setStyleSheet\("""[\s\S]*?"""\)\s*$',
    # Tek satırlık f-string
    r'^\s*[\w\.]+\.setStyleSheet\(f"[^"]*"\)\s*$',
    # get_*_style() çağrıları (bunları da kaldır)
    r"^\s*[\w\.]+\.setStyleSheet\(get_\w+_style\([^)]*\)\)\s*$",
]


def remove_inline_styles(filepath):
    """Bir dosyadaki inline stilleri kaldır"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    removed_count = 0

    # Satır satır işle
    lines = content.split("\n")
    new_lines = []
    skip_until_close = False
    multiline_count = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Çok satırlık setStyleSheet başlangıcı
        if ".setStyleSheet(" in line and ('"""' in line or "'''" in line):
            # Açılış quote'u say
            quote_type = '"""' if '"""' in line else "'''"
            quote_count = line.count(quote_type)

            if quote_count == 1:
                # Çok satırlı - kapanana kadar atla
                skip_until_close = True
                multiline_count = 1
                i += 1
                while i < len(lines) and skip_until_close:
                    if quote_type in lines[i]:
                        skip_until_close = False
                        removed_count += 1
                    i += 1
                continue
            elif quote_count >= 2:
                # Tek satırda açılıp kapanıyor
                removed_count += 1
                i += 1
                continue

        # Tek satırlık setStyleSheet
        if re.match(r"^\s*[\w\.]+\.setStyleSheet\([^)]+\)\s*$", line):
            removed_count += 1
            i += 1
            continue

        # f-string çok satırlı
        if '.setStyleSheet(f"""' in line or ".setStyleSheet(f'''" in line:
            quote = '"""' if '"""' in line else "'''"
            if line.count(quote) == 1:
                # Kapanışa kadar atla
                i += 1
                while i < len(lines):
                    if quote in lines[i]:
                        removed_count += 1
                        i += 1
                        break
                    i += 1
                continue

        # _style_* metodları için sadece çağrıları temizle
        # self._style_input(widget) gibi
        if re.match(r"^\s*self\._style_\w+\([^)]+\)\s*$", line):
            removed_count += 1
            i += 1
            continue

        new_lines.append(line)
        i += 1

    new_content = "\n".join(new_lines)

    # Eğer değişiklik varsa kaydet
    if new_content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return removed_count

    return 0


def clean_style_methods(filepath):
    """_style_* metodlarını dosyadan kaldır"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # _style_input, _style_combo, _style_button gibi metodları bul ve kaldır
    patterns = [
        r"\n    def _style_\w+\(self[^)]*\):[^\n]*(?:\n        [^\n]+)*",
    ]

    for pattern in patterns:
        content = re.sub(pattern, "", content)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


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

            removed = remove_inline_styles(filepath)
            if removed > 0:
                print(f"✓ {filepath}: {removed} inline stil kaldırıldı")
                total_files += 1
                total_removed += removed

            # Style metodlarını temizle
            if clean_style_methods(filepath):
                print(f"  → _style_* metodları temizlendi")

    print(f"\n{'='*60}")
    print(f"Toplam: {total_files} dosya, {total_removed} inline stil kaldırıldı")
    print("Global tema (theme.qss) artık tüm stilleri yönetecek!")


if __name__ == "__main__":
    main()
