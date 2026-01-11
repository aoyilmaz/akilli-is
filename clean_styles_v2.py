"""
TÜM INLINE STİLLERİ KALDIR - VERSİYON 2
get_*_style() çağrılarını da kaldırır
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
    "modules/development/views",
    "ui/pages",
]

SKIP_FILES = [
    "sidebar.py",
    "titlebar.py",
    "activity_bar.py",
    "__init__.py",
]


def remove_all_setstylesheet(filepath):
    """Tüm setStyleSheet çağrılarını kaldır"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    lines = content.split("\n")
    new_lines = []
    removed = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # setStyleSheet başlangıcı
        if ".setStyleSheet(" in stripped:
            # Parantez dengesi kontrol et
            paren_count = stripped.count("(") - stripped.count(")")

            if paren_count == 0:
                # Tek satırda tamamlanmış
                removed += 1
                i += 1
                continue
            elif paren_count > 0:
                # Çok satırlı - kapanana kadar atla
                i += 1
                current_count = paren_count
                while i < len(lines) and current_count > 0:
                    current_line = lines[i]
                    current_count += current_line.count("(") - current_line.count(")")
                    i += 1
                removed += 1
                continue

        # Standalone self._style_* çağrıları
        if re.match(r"^\s*self\._style_\w+\(", stripped):
            paren_count = stripped.count("(") - stripped.count(")")
            if paren_count == 0:
                removed += 1
                i += 1
                continue

        new_lines.append(line)
        i += 1

    if removed > 0:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines))

    return removed


def remove_style_helper_methods(filepath):
    """_style_* metodlarını kaldır"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # _style_* metod tanımlarını kaldır
    # def _style_xxx(self, widget): ... şeklindeki metodlar
    pattern = r"\n    def _style_\w+\(self[^)]*\):(?:\n(?:        |\n).*)*?(?=\n    def |\n\nclass |\Z)"

    # Daha basit yaklaşım - satır satır işle
    lines = content.split("\n")
    new_lines = []
    in_style_method = False
    base_indent = 0

    for line in lines:
        # Yeni metod başlangıcı
        if line.strip().startswith("def _style_"):
            in_style_method = True
            base_indent = len(line) - len(line.lstrip())
            continue

        # Style metodunun içindeyiz
        if in_style_method:
            current_indent = (
                len(line) - len(line.lstrip()) if line.strip() else base_indent + 1
            )

            # Yeni bir def veya class görürsek veya indent azalırsa çık
            if line.strip() and (
                line.strip().startswith("def ")
                or line.strip().startswith("class ")
                or current_indent <= base_indent
            ):
                in_style_method = False
                new_lines.append(line)
            continue

        new_lines.append(line)

    new_content = "\n".join(new_lines)

    if new_content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False


def clean_unused_imports(filepath):
    """Kullanılmayan stil import'larını temizle"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # get_*_style fonksiyonları kullanılmıyorsa import'tan kaldır
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
    ]

    for func in style_funcs:
        # Eğer sadece import'ta varsa ve başka yerde kullanılmıyorsa kaldır
        import_match = re.search(rf"\b{func}\b", content)
        if import_match:
            # Import dışında kullanılıyor mu kontrol et
            # İlk import satırını bul
            lines = content.split("\n")
            import_line_idx = -1
            used_elsewhere = False

            for idx, line in enumerate(lines):
                if "from config.styles import" in line or "from config import" in line:
                    if func in line:
                        import_line_idx = idx
                elif func in line:
                    used_elsewhere = True
                    break

            if not used_elsewhere and import_line_idx >= 0:
                # Import'tan kaldır
                line = lines[import_line_idx]
                # Basit kaldırma
                new_line = re.sub(rf",?\s*{func}\b", "", line)
                new_line = re.sub(rf"\b{func}\s*,?", "", new_line)
                new_line = re.sub(r",\s*\)", ")", new_line)  # trailing comma
                new_line = re.sub(r"\(\s*,", "(", new_line)  # leading comma
                new_line = re.sub(r",\s*,", ",", new_line)  # double comma
                lines[import_line_idx] = new_line
                content = "\n".join(lines)

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

            removed = remove_all_setstylesheet(filepath)

            if removed > 0:
                print(f"✓ {filepath}: {removed} setStyleSheet kaldırıldı")
                total_files += 1
                total_removed += removed

                # Style metodlarını da temizle
                if remove_style_helper_methods(filepath):
                    print(f"  → _style_* metodları temizlendi")

                # Unused imports temizle
                if clean_unused_imports(filepath):
                    print(f"  → Kullanılmayan import'lar temizlendi")

    print(f"\n{'='*60}")
    print(f"Toplam: {total_files} dosya, {total_removed} setStyleSheet kaldırıldı")


if __name__ == "__main__":
    main()
