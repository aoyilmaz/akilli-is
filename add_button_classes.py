"""
Primary buton stili uygulama scripti
"Yeni", "Ekle", "Kaydet" gibi butonlara primary class ekler
"""

import os
import re

# İşlenecek modüller
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

# Primary olması gereken buton metinleri
PRIMARY_PATTERNS = [
    r'QPushButton\("➕[^"]+"\)',
    r'QPushButton\("\+ [^"]+"\)',
    r'QPushButton\("Yeni [^"]+"\)',
    r'QPushButton\("💾 Kaydet"\)',
    r'QPushButton\("Kaydet"\)',
    r'QPushButton\("✅[^"]+"\)',
]

# Success olması gereken butonlar
SUCCESS_PATTERNS = [
    r'QPushButton\("📥 Giriş[^"]*"\)',
    r'QPushButton\("✓[^"]+"\)',
]

# Danger olması gereken butonlar
DANGER_PATTERNS = [
    r'QPushButton\("📤 Çıkış[^"]*"\)',
    r'QPushButton\("🗑[^"]+"\)',
]


def add_button_classes(filepath):
    """Butonlara class property ekle"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    changes = 0

    # Primary butonları bul ve class ekle
    for pattern in PRIMARY_PATTERNS:
        matches = re.finditer(pattern, content)
        for match in matches:
            btn_text = match.group(0)
            # Değişken adını bul (önceki satırda)
            start = match.start()
            # Önceki 100 karakteri al ve değişken adını bul
            prefix = content[max(0, start - 100) : start]

            # "btn_name = " pattern'ını bul
            var_match = re.search(r"(\w+)\s*=\s*$", prefix)
            if var_match:
                var_name = var_match.group(1)
                # Bu satırdan sonra setProperty kontrolü
                end_of_line = content.find("\n", match.end())
                next_50_chars = (
                    content[match.end() : end_of_line + 100] if end_of_line > 0 else ""
                )

                # Zaten setProperty varsa atla
                if f"{var_name}.setProperty" not in next_50_chars:
                    # Satır sonuna setProperty ekle
                    insert_pos = content.find("\n", match.end())
                    if insert_pos > 0:
                        insert_text = (
                            f'\n        {var_name}.setProperty("class", "primary")'
                        )
                        content = (
                            content[:insert_pos] + insert_text + content[insert_pos:]
                        )
                        changes += 1

    if content != original and changes > 0:
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

            filepath = os.path.join(module_path, filename)
            changes = add_button_classes(filepath)

            if changes > 0:
                print(f"✓ {filepath}: {changes} primary buton")
                total_files += 1
                total_changes += changes

    print(f"\n{'='*50}")
    print(f"Toplam: {total_files} dosya, {total_changes} buton primary yapıldı")


if __name__ == "__main__":
    main()
