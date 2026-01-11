"""
MODÜL MODÜL İNLINE STİL TEMİZLEME
Her dosyayı dikkatlice işler, syntax kontrolü yapar
"""

import os
import re
import sys


def clean_file(filepath):
    """Tek dosyayı temizle"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # 1. setStyleSheet çağrılarını kaldır (tek satırlık)
    content = re.sub(
        r"^\s*[\w\.]+\.setStyleSheet\([^)]+\)\s*\n", "", content, flags=re.MULTILINE
    )

    # 2. Çok satırlık setStyleSheet (f""" veya """)
    content = re.sub(
        r'^\s*[\w\.]+\.setStyleSheet\(f?"""[\s\S]*?"""\)\s*\n',
        "",
        content,
        flags=re.MULTILINE,
    )

    # 3. Çok satırlık setStyleSheet (f''' veya ''')
    content = re.sub(
        r"^\s*[\w\.]+\.setStyleSheet\(f?'''[\s\S]*?'''\)\s*\n",
        "",
        content,
        flags=re.MULTILINE,
    )

    # 4. get_*_style() çağrılarıyla setStyleSheet
    content = re.sub(
        r"^\s*[\w\.]+\.setStyleSheet\(get_\w+_style\([^)]*\)\)\s*\n",
        "",
        content,
        flags=re.MULTILINE,
    )

    # 5. self._style_xxx() çağrıları
    content = re.sub(
        r"^\s*self\._style_\w+\([^)]*\)\s*\n", "", content, flags=re.MULTILINE
    )

    # 6. _style_* metod tanımlarını kaldır
    # def _style_xxx(self, ...): ile başlayan ve bir sonraki def'e kadar
    def remove_style_methods(text):
        lines = text.split("\n")
        result = []
        skip = False
        indent_level = 0

        for i, line in enumerate(lines):
            # _style_ metod başlangıcı
            match = re.match(r"^(\s*)def _style_\w+\(", line)
            if match:
                skip = True
                indent_level = len(match.group(1))
                continue

            if skip:
                # Boş satır veya docstring devam edebilir
                stripped = line.strip()
                if stripped == "":
                    continue
                # Aynı veya daha az indentli yeni tanım (def, class)
                current_indent = len(line) - len(line.lstrip())
                if (
                    stripped
                    and current_indent <= indent_level
                    and not stripped.startswith(("#", '"""', "'''"))
                ):
                    skip = False
                    result.append(line)
                continue

            result.append(line)

        return "\n".join(result)

    content = remove_style_methods(content)

    # 7. Kullanılmayan style importlarını temizle
    style_funcs = [
        "get_button_style",
        "get_table_style",
        "get_title_style",
        "get_combo_style",
        "get_menu_style",
        "get_input_style",
        "get_tab_style",
        "get_tree_style",
        "get_dialog_style",
        "get_card_style",
        "get_frame_style",
        "get_label_style",
        "BG_DARK",
        "BG_MEDIUM",
        "BG_LIGHT",
        "BG_SECONDARY",
        "TEXT_PRIMARY",
        "TEXT_MUTED",
        "BORDER",
        "ACCENT",
        "SUCCESS",
        "WARNING",
        "ERROR",
        "INFO",
    ]

    for func in style_funcs:
        # Import dışında kullanılıp kullanılmadığını kontrol et
        lines = content.split("\n")
        import_lines = []
        usage_found = False

        for idx, line in enumerate(lines):
            if (
                "from config.styles import" in line or "from config import" in line
            ) and func in line:
                import_lines.append(idx)
            elif func in line and "import" not in line:
                usage_found = True
                break

        # Kullanılmıyorsa import'tan kaldır
        if not usage_found and import_lines:
            for idx in import_lines:
                line = lines[idx]
                # Doğrudan fonksiyon adını kaldır
                new_line = re.sub(rf",?\s*{func}\s*", "", line)
                new_line = re.sub(rf"{func}\s*,?\s*", "", new_line)
                # Boş parantez kontrolü
                new_line = re.sub(r"\(\s*\)", "()", new_line)
                new_line = re.sub(r",\s*\)", ")", new_line)
                new_line = re.sub(r"\(\s*,", "(", new_line)
                lines[idx] = new_line
            content = "\n".join(lines)

    # 8. Boş import satırlarını temizle
    content = re.sub(
        r"^from config\.styles import\s*\(\s*\)\s*\n", "", content, flags=re.MULTILINE
    )
    content = re.sub(
        r"^from config\.styles import\s*\n", "", content, flags=re.MULTILINE
    )

    # 9. Ardışık boş satırları 2'ye düşür
    content = re.sub(r"\n{3,}", "\n\n", content)

    if content != original:
        # Syntax kontrolü
        try:
            compile(content, filepath, "exec")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except SyntaxError as e:
            print(f"  ⚠ Syntax hatası (line {e.lineno}), atlandı")
            return False

    return False


def process_module(module_path):
    """Bir modülü temizle"""
    views_path = os.path.join(module_path, "views")
    if not os.path.exists(views_path):
        return 0

    cleaned = 0
    for filename in os.listdir(views_path):
        if not filename.endswith(".py") or filename.startswith("__"):
            continue

        filepath = os.path.join(views_path, filename)
        if clean_file(filepath):
            print(f"  ✓ {filename}")
            cleaned += 1

    return cleaned


def main():
    modules = [
        "modules/hr",
        "modules/quality",
        "modules/inventory",
        "modules/sales",
        "modules/purchasing",
        "modules/production",
        "modules/accounting",
        "modules/finance",
        "modules/reports",
        "modules/mrp",
        "modules/development",
    ]

    total = 0

    for module in modules:
        if not os.path.exists(module):
            continue

        print(f"\n📁 {module}")
        cleaned = process_module(module)
        total += cleaned

        if cleaned == 0:
            print("  (değişiklik yok)")

    # UI pages
    print(f"\n📁 ui/pages")
    ui_path = "ui/pages"
    for filename in os.listdir(ui_path):
        if not filename.endswith(".py") or filename.startswith("__"):
            continue
        if filename in ["sidebar.py", "titlebar.py", "activity_bar.py"]:
            continue

        filepath = os.path.join(ui_path, filename)
        if clean_file(filepath):
            print(f"  ✓ {filename}")
            total += 1

    print(f"\n{'='*50}")
    print(f"✅ Toplam {total} dosya temizlendi")


if __name__ == "__main__":
    main()
