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

# Auth ve Audit sistemi
from database.audit_engine import audit_engine
from core.session_manager import session_manager
from core.user_context import get_current_user, set_current_user, create_user_context


class ApplicationController:
    """Uygulama akış kontrolcüsü"""

    def __init__(self, app: QApplication):
        self.app = app
        self.splash = None
        self.login = None
        self.main_window = None
        self.current_user = None
        self._db_session = None

    def start(self):
        """Uygulama akışını başlat: Splash -> Login -> MainWindow"""
        # Audit engine'i başlat
        audit_engine.init_listeners()
        print("✓ Audit engine başlatıldı")

        self._show_splash()

    def _show_splash(self):
        """Splash screen göster"""
        from ui.screens import SplashScreen

        self.splash = SplashScreen()
        self.splash.finished.connect(self._on_splash_finished)
        self.splash.start()

    def _on_splash_finished(self):
        """Splash tamamlandığında ana pencereyi göster (Login devre dışı)"""
        self.splash = None
        self._show_main_window()

    def _show_login(self):
        """Login ekranını göster"""
        from ui.screens import LoginScreen

        self.login = LoginScreen()
        self.login.login_successful.connect(self._on_login_success)
        self.login.forgot_password.connect(self._on_forgot_password)
        self.login.show()

    def _on_login_success(self, user):
        """Başarılı giriş sonrası ana pencereyi göster"""
        self.current_user = user

        # User context'i ayarla
        from database.base import get_session
        db = get_session()
        try:
            context = create_user_context(user)
            set_current_user(context)
            print(f"✓ Kullanıcı context'i ayarlandı: {user.username}")
        except Exception as e:
            print(f"Kullanıcı context hatası: {e}")
        finally:
            db.close()

        if self.login:
            self.login.close()
            self.login = None

        self._show_main_window()

    def _on_forgot_password(self):
        """Şifremi unuttum işlemi"""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.information(
            self.login,
            "Şifre Sıfırlama",
            "Şifre sıfırlama talebi için sistem yöneticinize başvurun.",
        )

    def _show_main_window(self):
        """Ana pencereyi göster"""
        from ui.main_window import MainWindow

        self.main_window = MainWindow()

        # Kullanıcı bilgisini ayarla (varsa)
        if self.current_user:
            try:
                # Status bar'da kullanıcı bilgisini güncelle
                if hasattr(self.main_window, "status_user_name"):
                    name = getattr(self.current_user, "full_name", None) or getattr(
                        self.current_user, "username", "Kullanıcı"
                    )
                    self.main_window.status_user_name.setText(name)
                if hasattr(self.main_window, "status_role_badge"):
                    role = getattr(self.current_user, "role", None)
                    if role:
                        role_name = getattr(role, "name", "Kullanıcı")
                        self.main_window.status_role_badge.setText(role_name)
            except Exception:
                pass

        self.main_window.showMaximized()
        print("Uygulama başlatıldı!")


def main():
    """Ana uygulama fonksiyonu"""
    print("=" * 80)
    print(f"{APP_NAME} v{APP_VERSION} başlatılıyor...")
    print("=" * 80)
    print("=" * 80)

    # Uygulama oluştur
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Akıllı İş")

    # Uygulama ikonu
    icon_path = ICONS_DIR / "logo.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    else:
        # PNG alternatifi
        png_path = ICONS_DIR / "logo.png"
        if png_path.exists():
            app.setWindowIcon(QIcon(str(png_path)))

    # Varsayılan font
    font = QFont(UI["FONT_FAMILY"], UI["FONT_SIZE"])
    app.setFont(font)

    # Global tema uygula (config/theme.qss)
    from config.theme_manager import apply_global_theme

    apply_global_theme(app)

    # Uygulama kontrolcüsünü başlat
    controller = ApplicationController(app)
    controller.start()

    # Uygulama döngüsünü başlat
    sys.exit(app.exec())


def main_direct():
    """Login olmadan direkt ana pencereyi aç (geliştirme için)"""
    print("=" * 50)
    print(f"{APP_NAME} v{APP_VERSION} başlatılıyor (DIRECT MODE)...")
    print("=" * 50)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Akıllı İş")

    icon_path = ICONS_DIR / "logo.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    font = QFont(UI["FONT_FAMILY"], UI["FONT_SIZE"])
    app.setFont(font)

    from config.theme_manager import apply_global_theme

    apply_global_theme(app)

    # Audit engine'i başlat
    audit_engine.init_listeners()
    print("✓ Audit engine başlatıldı")

    # Dev modunda admin kullanıcısını otomatik ayarla
    from database.base import get_session
    from database.models.user import User

    db = get_session()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            context = create_user_context(admin_user)
            set_current_user(context)
            print(f"✓ Dev kullanıcı context'i ayarlandı: {admin_user.username}")
        else:
            print("! Admin kullanıcısı bulunamadı - seed_auth.py çalıştırın")
    except Exception as e:
        print(f"Dev kullanıcı hatası: {e}")
    finally:
        db.close()

    from ui.main_window import MainWindow

    window = MainWindow()
    window.showMaximized()

    print("Uygulama başlatıldı!")
    sys.exit(app.exec())


if __name__ == "__main__":
    # Normal başlatma (Splash -> Login -> Main)
    main()

    # Geliştirme modu için (direkt ana pencere):
    # main_direct()
