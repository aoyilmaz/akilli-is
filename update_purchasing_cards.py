"""
Satınalma modülü gösterge kartlarını güncelle
"""

import os
import re

FILES = [
    "modules/purchasing/views/goods_receipt_list.py",
    "modules/purchasing/views/purchase_invoice_list.py",
    "modules/purchasing/views/purchase_request_list.py",
    "modules/purchasing/views/supplier_list.py",
]

IMPORT_LINE = "from ui.components.stat_cards import MiniStatCard"


def update_file(filepath):
    if not os.path.exists(filepath):
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    changes = []

    # Import ekle
    if "from ui.components.stat_cards import" not in content:
        if "from PyQt6" in content:
            lines = content.split("\n")
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("from PyQt6"):
                    insert_idx = i + 1
            lines.insert(insert_idx, IMPORT_LINE)
            content = "\n".join(lines)
            changes.append("Import eklendi")

    # _create_stat_card metodunu değiştir
    lines = content.split("\n")
    new_lines = []
    skip_until_return = False
    replaced = False

    for i, line in enumerate(lines):
        if "def _create_stat_card(" in line and not replaced:
            # Signature'ı MiniStatCard ile değiştir
            new_lines.append("    def _create_stat_card(")
            new_lines.append(
                "        self, icon: str, title: str, value: str, color: str"
            )
            new_lines.append("    ) -> MiniStatCard:")
            new_lines.append('        """Dashboard tarzı istatistik kartı"""')
            new_lines.append(
                '        return MiniStatCard(f"{icon} {title}", value, color)'
            )
            skip_until_return = True
            replaced = True
            changes.append("_create_stat_card güncellendi")
            continue

        if skip_until_return:
            if "return card" in line or "return self" in line:
                skip_until_return = False
            continue

        new_lines.append(line)

    content = "\n".join(new_lines)

    # _update_card metodunu değiştir
    old_update = r'def _update_card\(self, card: QFrame, value: str\):\s*\n\s*label = card\.findChild\(QLabel, "value"\)\s*\n\s*if label:\s*\n\s*label\.setText\(value\)'
    new_update = '''def _update_card(self, card: MiniStatCard, value: str):
        """Kart değerini güncelle"""
        card.update_value(value)'''

    if re.search(old_update, content):
        content = re.sub(old_update, new_update, content)
        changes.append("_update_card güncellendi")

    if content != original:
        try:
            compile(content, filepath, "exec")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✓ {filepath}: {', '.join(changes)}")
            return True
        except SyntaxError as e:
            print(f"⚠ {filepath}: Syntax hatası line {e.lineno}")
            return False

    print(f"○ {filepath}: Değişiklik yok")
    return False


if __name__ == "__main__":
    for f in FILES:
        update_file(f)
