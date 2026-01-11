"""
Akıllı İş ERP - Global Tema Yöneticisi

Bu modül, tüm uygulamaya Qt stylesheet (QSS) uygular.
Tema değişikliği için sadece theme.qss dosyasını düzenleyin.
"""

import os
from PyQt6.QtWidgets import QApplication


def load_theme() -> str:
    """theme.qss dosyasını oku ve içeriğini döndür"""
    theme_path = os.path.join(os.path.dirname(__file__), "theme.qss")

    if not os.path.exists(theme_path):
        print(f"⚠️ Tema dosyası bulunamadı: {theme_path}")
        return ""

    try:
        with open(theme_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"⚠️ Tema dosyası okunamadı: {e}")
        return ""


def apply_global_theme(app: QApplication) -> bool:
    """
    Uygulamaya global temayı uygula.

    Args:
        app: QApplication instance

    Returns:
        bool: Tema başarıyla uygulandı mı
    """
    qss = load_theme()

    if not qss:
        return False

    try:
        app.setStyleSheet(qss)
        print("✓ Global tema uygulandı")
        return True
    except Exception as e:
        print(f"⚠️ Tema uygulanamadı: {e}")
        return False


def reload_theme(app: QApplication) -> bool:
    """
    Temayı yeniden yükle (hot reload için).
    Geliştirme sırasında kullanışlı.
    """
    return apply_global_theme(app)
