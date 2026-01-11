"""
MiniStatCard'a geçiş scripti
Tüm modüllerdeki _create_card fonksiyonlarını MiniStatCard kullanacak şekilde günceller
"""

import os
import re

FILES_TO_UPDATE = [
    "modules/inventory/views/reports_page.py",
    "modules/production/views/bom_list.py",
    "modules/production/views/work_order_list.py",
    "modules/production/views/work_station_list.py",
    "modules/reports/views/sales_reports.py",
    "modules/reports/views/supplier_performance.py",
    "modules/reports/views/stock_aging.py",
    "modules/reports/views/receivables_aging.py",
]

# Import satırı
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
        # config.styles import'undan sonra ekle
        if "from config.styles import" in content:
            content = re.sub(
                r"(from config\.styles import[^\n]+\n)",
                r"\1" + IMPORT_LINE + "\n",
                content,
            )
            changes.append("Import eklendi")
        elif "from config import" in content:
            content = re.sub(
                r"(from config import[^\n]+\n)", r"\1" + IMPORT_LINE + "\n", content
            )
            changes.append("Import eklendi")

    # 2. _create_card fonksiyonunu güncelle
    # Pattern: def _create_card(self, title: str, value: str, color: str) -> QFrame:
    old_pattern = (
        r"def _create_card\(self, title: str, value: str, color: str\) -> QFrame:"
    )
    new_func = (
        "def _create_card(self, title: str, value: str, color: str) -> MiniStatCard:"
    )

    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_func, content)
        changes.append("Fonksiyon type hint güncellendi")

    # Subtitle olan versiyon
    old_pattern2 = r"def _create_card\(self, title: str, value: str, color: str, subtitle: str\) -> QFrame:"
    new_func2 = "def _create_card(self, title: str, value: str, color: str, subtitle: str = '') -> MiniStatCard:"

    if re.search(old_pattern2, content):
        content = re.sub(old_pattern2, new_func2, content)
        changes.append("Fonksiyon type hint güncellendi (subtitle)")

    # 3. Fonksiyon içeriğini değiştir
    # Eski pattern: card = QFrame() ... return card
    old_body_pattern = r"""    def _create_card\(self,[^)]+\) -> (?:QFrame|MiniStatCard):
        card = QFrame\(\)
        card[^}]*

        layout = QVBoxLayout\(card\)
        layout\.setContentsMargins\([^)]+\)[^}]*

        title_label = QLabel\(title\)
        title_label\.setStyleSheet\([^)]+\)
        layout\.addWidget\(title_label\)

        value_label = QLabel\(value\)
        value_label\.setObjectName\([^)]+\)
        value_label\.setStyleSheet\([^)]+\)
        layout\.addWidget\(value_label\)(?:

        if subtitle:[^}]*)?

        return card"""

    # Basitleştirilmiş arama ve değiştirme
    if "card = QFrame()" in content and "_create_card" in content:
        # Manuel olarak eski fonksiyon gövdesini bul ve değiştir
        lines = content.split("\n")
        new_lines = []
        in_create_card = False
        skip_until_return = False

        for i, line in enumerate(lines):
            if "def _create_card" in line:
                in_create_card = True
                # Type hint'i güncelle
                if "-> QFrame:" in line:
                    line = line.replace("-> QFrame:", "-> MiniStatCard:")
                new_lines.append(line)
                # Yeni fonksiyon gövdesini ekle
                if "subtitle" in line:
                    new_lines.append(
                        '        """MiniStatCard kullanarak modern kart oluştur"""'
                    )
                    new_lines.append("        return MiniStatCard(title, value, color)")
                else:
                    new_lines.append(
                        '        """MiniStatCard kullanarak modern kart oluştur"""'
                    )
                    new_lines.append("        return MiniStatCard(title, value, color)")
                skip_until_return = True
                continue

            if skip_until_return:
                if line.strip().startswith("return card"):
                    skip_until_return = False
                    in_create_card = False
                continue

            new_lines.append(line)

        content = "\n".join(new_lines)
        changes.append("Fonksiyon gövdesi güncellendi")

    # 4. _update_card fonksiyonunu güncelle
    old_update = r"def _update_card\(self, card: QFrame, value: str\):"
    new_update = "def _update_card(self, card: MiniStatCard, value: str):"
    if re.search(old_update, content):
        content = re.sub(old_update, new_update, content)

        # Eski gövdeyi de değiştir
        old_update_body = r"""value_label = card\.findChild\(QLabel, "value"\)
        if value_label:
            value_label\.setText\(value\)"""
        new_update_body = "card.update_value(value)"
        content = re.sub(old_update_body, new_update_body, content)
        changes.append("_update_card güncellendi")

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ {filepath}: {', '.join(changes)}")
        return True
    else:
        print(f"○ {filepath}: Değişiklik yok")
        return False


def main():
    total = 0
    for filepath in FILES_TO_UPDATE:
        if update_file(filepath):
            total += 1

    print(f"\n{'='*50}")
    print(f"Toplam: {total} dosya güncellendi")


if __name__ == "__main__":
    main()
