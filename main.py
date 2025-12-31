#!/usr/bin/env python3
"""
Akıllı İş ERP - Ana Uygulama
============================
Kurumsal Kaynak Planlama Sistemi

Developed with ❤️ in Turkey
"""

import sys
import os
from pathlib import Path

# Proje kök dizinini path'e ekle
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QFile, QTextStream
from PyQt6.QtGui import QIcon, QFont, QFontDatabase

from config import settings
from ui.main_window import MainWindow
from loguru import logger


def setup_logging():
    """Loglama sistemini yapılandır"""
    log_path = PROJECT_ROOT / "logs"
    log_path.mkdir(exist_ok=True)
    
    logger.add(
        log_path / "akilli_is_{time}.log",
        rotation="10 MB",
        retention="30 days",
        level="DEBUG" if settings.DEBUG else "INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8"
    )


def load_stylesheet(app: QApplication) -> None:
    """Tema dosyasını yükle"""
    theme_file = PROJECT_ROOT / "ui" / "themes" / f"{settings.THEME}.qss"
    
    if theme_file.exists():
        file = QFile(str(theme_file))
        if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            stream = QTextStream(file)
            stylesheet = stream.readAll()
            app.setStyleSheet(stylesheet)
            file.close()
            logger.info(f"Tema yüklendi: {settings.THEME}")
    else:
        logger.warning(f"Tema dosyası bulunamadı: {theme_file}")


def setup_fonts(app: QApplication) -> None:
    """Fontları yapılandır"""
    # Sistem fontunu kullan
    font = QFont()
    font.setFamily("-apple-system")  # macOS için
    font.setPointSize(13)
    app.setFont(font)


def main():
    """Ana uygulama başlatıcı"""
    # Loglama
    setup_logging()
    logger.info("=" * 50)
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} başlatılıyor...")
    logger.info("=" * 50)
    
    # High DPI desteği
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    # Uygulama oluştur
    app = QApplication(sys.argv)
    app.setApplicationName(settings.APP_NAME)
    app.setApplicationVersion(settings.APP_VERSION)
    app.setOrganizationName("Akıllı İş")
    app.setOrganizationDomain("akilli-is.com")
    
    # macOS için dock icon
    app.setWindowIcon(QIcon(str(PROJECT_ROOT / "assets" / "logo.svg")))
    
    # Tema ve font
    load_stylesheet(app)
    setup_fonts(app)
    
    # Ana pencereyi oluştur ve göster
    window = MainWindow()
    window.show()
    
    logger.info("Uygulama başarıyla başlatıldı")
    
    # Event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
