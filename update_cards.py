"""
Gösterge kartlarını MiniStatCard'a güncelle
"""

import os
import re

FILES = [
    "modules/inventory/views/stock_count_list.py",
    "modules/inventory/views/reports_page.py",
    "modules/production/views/bom_list.py",
    "modules/production/views/work_order_list.py",
    "modules/production/views/work_station_list.py",
    "modules/reports/views/sales_reports.py",
    "modules/reports/views/supplier_performance.py",
    "modules/reports/views/stock_aging.py",
    "modules/reports/views/receivables_aging.py",
]

# MiniStatCard import satırı
IMPORT_LINE = "from ui.components.stat_cards import MiniStatCard"


def update_file(filepath):
    if not os.path.exists(filepath):
        print(f"✗ Dosya yok: {filepath}")
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    changes = []

    # 1. Import ekle (yoksa)
    if "from ui.components.stat_cards import" not in content:
        # PyQt6 importlarından sonra ekle
        if "from PyQt6" in content:
            # Son PyQt6 import satırından sonra ekle
            lines = content.split("\n")
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("from PyQt6"):
                    insert_idx = i + 1

            lines.insert(insert_idx, IMPORT_LINE)
            content = "\n".join(lines)
            changes.append("Import eklendi")

    # 2. _create_card return tipini güncelle
    content = re.sub(
        r"def _create_card\(self,[^)]+\)\s*->\s*QFrame:",
        lambda m: m.group(0).replace("-> QFrame:", "-> MiniStatCard:"),
        content,
    )

    # 3. _create_card fonksiyon gövdesini değiştir
    # Eski gövdeyi bul ve yenisiyle değiştir
    old_body = r"""(def _create_card\(self, title: str, value: str, color: str(?:, subtitle: str)?\)\s*->\s*(?:QFrame|MiniStatCard):)\s*
        card = QFrame\(\).*?return card"""

    # Daha esnek pattern
    lines = content.split("\n")
    new_lines = []
    in_create_card = False
    skip_until_return = False
    replaced = False

    for i, line in enumerate(lines):
        if "def _create_card(" in line and not replaced:
            in_create_card = True
            # Signature'ı düzelt
            line = line.replace("-> QFrame:", "-> MiniStatCard:")
            new_lines.append(line)
            # Yeni gövde ekle
            new_lines.append('        """Dashboard tarzı istatistik kartı"""')
            new_lines.append("        return MiniStatCard(title, value, color)")
            skip_until_return = True
            replaced = True
            changes.append("_create_card güncellendi")
            continue

        if skip_until_return:
            if line.strip().startswith("return card") or line.strip().startswith(
                "return self"
            ):
                skip_until_return = False
                in_create_card = False
            continue

        new_lines.append(line)

    content = "\n".join(new_lines)

    # 4. _update_card metodunu güncelle
    if "_update_card" in content and "card.findChild" in content:
        content = re.sub(
            r"def _update_card\(self, card: QFrame, value: str\):",
            "def _update_card(self, card: MiniStatCard, value: str):",
            content,
        )
        content = re.sub(
            r'value_label = card\.findChild\(QLabel, "value"\)\s*\n\s*if value_label:\s*\n\s*value_label\.setText\(value\)',
            "card.update_value(value)",
            content,
        )
        changes.append("_update_card güncellendi")

    # 5. Kullanılmayan QFrame import'unu kontrol et
    # (Eğer QFrame başka yerde kullanılıyorsa kaldırma)

    if content != original:
        # Syntax kontrolü
        try:
            compile(content, filepath, "exec")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✓ {filepath}: {', '.join(changes)}")
            return True
        except SyntaxError as e:
            print(f"⚠ {filepath}: Syntax hatası line {e.lineno}")
            return False
    else:
        print(f"○ {filepath}: Değişiklik yok")
        return False


def main():
    total = 0
    for filepath in FILES:
        if update_file(filepath):
            total += 1

    print(f"\n{'='*50}")
    print(f"Toplam: {total} dosya güncellendi")


if __name__ == "__main__":
    main()
