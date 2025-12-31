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
from PyQt6.QtCore import QFile, QTextStream
from PyQt6.QtGui import QFont, QIcon

from config import APP_NAME, APP_VERSION, UI, THEMES_DIR, ICONS_DIR


def load_stylesheet(theme: str = "dark") -> str:
    """Tema stil dosyasını yükle"""
    theme_file = THEMES_DIR / f"{theme}.qss"
    if theme_file.exists():
        file = QFile(str(theme_file))
        if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            stream = QTextStream(file)
            stylesheet = stream.readAll()
            file.close()
            return stylesheet
    return ""


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
    
    # Tema yükle
    stylesheet = load_stylesheet(UI["THEME"])
    if stylesheet:
        app.setStyleSheet(stylesheet)
    
    # Ana pencereyi oluştur ve göster
    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    
    print("Uygulama başlatıldı!")
    
    # Uygulama döngüsünü başlat
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
