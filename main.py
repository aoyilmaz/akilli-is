#!/usr/bin/env python3
"""
Akıllı İş - Kurumsal Kaynak Planlama
Ana uygulama giriş noktası
"""

import sys
from pathlib import Path

# Proje kök dizinini Python path'ine ekle
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon

from config import APP_NAME, APP_VERSION, UI, ICONS_DIR


def main():
    """Ana uygulama fonksiyonu"""
    print("=" * 50)
    print(f"{APP_NAME} v{APP_VERSION} başlatılıyor...")
    print("=" * 50)

    # Uygulama oluştur
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Akıllı İş")

    # Uygulama ikonu
    icon_path = ICONS_DIR / "logo.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Varsayılan font
    font = QFont(UI["FONT_FAMILY"], UI["FONT_SIZE"])
    app.setFont(font)

    # Global tema uygula (config/theme.qss)
    from config.theme_manager import apply_global_theme

    apply_global_theme(app)

    # Ana pencereyi oluştur ve tam ekran göster
    from ui.main_window import MainWindow

    window = MainWindow()
    window.showMaximized()

    print("Uygulama başlatıldı!")

    # Uygulama döngüsünü başlat
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
