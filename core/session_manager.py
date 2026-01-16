"""
Akıllı İş - Oturum Yöneticisi

Kullanıcı giriş/çıkış, oturum oluşturma ve doğrulama işlemlerini yönetir.
Çoklu cihaz desteği sağlar.
"""

import secrets
import platform
from datetime import datetime, timedelta
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session as DBSession

from database.models.user import User, UserSession, AuditLog
from core.user_context import (
    UserContext,
    create_user_context,
    set_current_user,
    clear_current_user,
    get_current_user,
)


class SessionManager:
    """
    Oturum yönetimi sınıfı.

    Singleton pattern kullanır - tüm uygulama genelinde tek instance.
    """

    _instance: Optional["SessionManager"] = None

    # Oturum süreleri
    SESSION_DURATION_HOURS = 24  # Normal oturum süresi
    REMEMBER_ME_DAYS = 30  # "Beni hatırla" süresi
    MAX_SESSIONS_PER_USER = 5  # Kullanıcı başına max oturum

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._current_session: Optional[UserSession] = None

    @staticmethod
    def _generate_token(length: int = 64) -> str:
        """Güvenli rastgele token üretir"""
        return secrets.token_hex(length // 2)

    @staticmethod
    def _get_device_info() -> dict:
        """Mevcut cihaz bilgilerini döndürür"""
        return {
            "device_name": platform.node() or "Unknown",
            "device_type": "desktop",
            "os_info": f"{platform.system()} {platform.release()}",
        }

    def login(
        self,
        db: DBSession,
        username: str,
        password: str,
        remember_me: bool = False,
        ip_address: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Kullanıcı girişi yapar.

        Args:
            db: Veritabanı session'ı
            username: Kullanıcı adı veya e-posta
            password: Şifre
            remember_me: Uzun süreli oturum
            ip_address: İstemci IP adresi

        Returns:
            (success, message, user)
        """
        # Kullanıcıyı bul
        user = (
            db.query(User)
            .filter(
                (User.username == username) | (User.email == username),
                User.is_active == True,
            )
            .first()
        )

        if not user:
            return False, "Kullanıcı bulunamadı", None

        # Hesap kilitli mi?
        if user.locked_until and user.locked_until > datetime.utcnow():
            remaining = (user.locked_until - datetime.utcnow()).seconds // 60
            return False, f"Hesap kilitli. {remaining} dakika sonra tekrar deneyin.", None

        # Şifre kontrolü
        if not user.check_password(password):
            user.failed_login_attempts += 1

            # 5 başarısız denemeden sonra kilitle
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)

            db.commit()
            return False, "Şifre hatalı", None

        # Başarılı giriş - sayacı sıfırla
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()

        # Eski oturumları kontrol et ve sınırla
        self._cleanup_old_sessions(db, user.id)

        # Yeni oturum oluştur
        session = self._create_session(
            db, user, remember_me=remember_me, ip_address=ip_address
        )

        # User context'i ayarla
        context = create_user_context(user, session_id=session.id)
        context.session_token = session.session_token
        context.ip_address = ip_address
        context.device_name = session.device_name
        set_current_user(context)

        self._current_session = session

        # Audit log
        self._log_action(
            db,
            user=user,
            action="LOGIN",
            module="auth",
            description=f"Başarılı giriş: {session.device_name}",
            ip_address=ip_address,
        )

        db.commit()
        return True, "Giriş başarılı", user

    def logout(self, db: DBSession, revoke_all: bool = False) -> bool:
        """
        Kullanıcı çıkışı yapar.

        Args:
            db: Veritabanı session'ı
            revoke_all: Tüm cihazlardan çıkış yap

        Returns:
            Başarılı mı?
        """
        ctx = get_current_user()
        if not ctx.is_authenticated:
            return False

        if revoke_all:
            # Tüm oturumları iptal et
            db.query(UserSession).filter(
                UserSession.user_id == ctx.user_id,
                UserSession.is_revoked == False,
            ).update(
                {
                    "is_revoked": True,
                    "revoked_at": datetime.utcnow(),
                    "revoke_reason": "logout_all",
                }
            )
        elif self._current_session:
            # Sadece mevcut oturumu iptal et
            self._current_session.revoke("logout")

        # Audit log
        self._log_action(
            db,
            action="LOGOUT",
            module="auth",
            description="Tüm cihazlardan çıkış" if revoke_all else "Çıkış yapıldı",
        )

        db.commit()

        # Context'i temizle
        clear_current_user()
        self._current_session = None

        return True

    def validate_session(self, db: DBSession, session_token: str) -> Optional[User]:
        """
        Oturum token'ını doğrular.

        Args:
            db: Veritabanı session'ı
            session_token: Oturum token'ı

        Returns:
            Geçerliyse User, değilse None
        """
        session = (
            db.query(UserSession)
            .filter(
                UserSession.session_token == session_token,
                UserSession.is_active == True,
                UserSession.is_revoked == False,
            )
            .first()
        )

        if not session or not session.is_valid:
            return None

        # Son aktiviteyi güncelle
        session.refresh_activity()
        db.commit()

        # User'ı döndür
        return session.user

    def restore_session(self, db: DBSession, session_token: str) -> bool:
        """
        Kaydedilmiş oturumu geri yükler (uygulama yeniden başlatıldığında).

        Args:
            db: Veritabanı session'ı
            session_token: Kaydedilmiş token

        Returns:
            Başarılı mı?
        """
        session = (
            db.query(UserSession)
            .filter(
                UserSession.session_token == session_token,
                UserSession.is_active == True,
                UserSession.is_revoked == False,
            )
            .first()
        )

        if not session or not session.is_valid:
            return False

        user = session.user
        if not user or not user.is_active:
            return False

        # Context'i yeniden oluştur
        context = create_user_context(user, session_id=session.id)
        context.session_token = session.session_token
        context.ip_address = session.ip_address
        context.device_name = session.device_name
        set_current_user(context)

        self._current_session = session
        session.refresh_activity()
        db.commit()

        return True

    def get_user_sessions(self, db: DBSession, user_id: int) -> List[UserSession]:
        """
        Kullanıcının aktif oturumlarını döndürür.

        Args:
            db: Veritabanı session'ı
            user_id: Kullanıcı ID

        Returns:
            Aktif oturum listesi
        """
        return (
            db.query(UserSession)
            .filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.is_revoked == False,
                UserSession.expires_at > datetime.utcnow(),
            )
            .order_by(UserSession.last_activity.desc())
            .all()
        )

    def revoke_session(self, db: DBSession, session_id: int, reason: str = "forced") -> bool:
        """
        Belirli bir oturumu iptal eder.

        Args:
            db: Veritabanı session'ı
            session_id: İptal edilecek oturum ID
            reason: İptal nedeni

        Returns:
            Başarılı mı?
        """
        session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if not session:
            return False

        session.revoke(reason)
        db.commit()
        return True

    def _create_session(
        self,
        db: DBSession,
        user: User,
        remember_me: bool = False,
        ip_address: Optional[str] = None,
    ) -> UserSession:
        """Yeni oturum oluşturur"""
        device_info = self._get_device_info()

        # Süre hesapla
        if remember_me:
            expires_at = datetime.utcnow() + timedelta(days=self.REMEMBER_ME_DAYS)
        else:
            expires_at = datetime.utcnow() + timedelta(hours=self.SESSION_DURATION_HOURS)

        session = UserSession(
            user_id=user.id,
            session_token=self._generate_token(),
            refresh_token=self._generate_token() if remember_me else None,
            device_name=device_info["device_name"],
            device_type=device_info["device_type"],
            os_info=device_info["os_info"],
            ip_address=ip_address,
            expires_at=expires_at,
        )

        db.add(session)
        db.flush()  # ID almak için

        return session

    def _cleanup_old_sessions(self, db: DBSession, user_id: int) -> None:
        """Eski ve aşırı oturumları temizler"""
        # Süresi dolmuş oturumları iptal et
        db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_revoked == False,
            UserSession.expires_at < datetime.utcnow(),
        ).update(
            {
                "is_revoked": True,
                "revoked_at": datetime.utcnow(),
                "revoke_reason": "expired",
            }
        )

        # Maksimum oturum sayısını aş
        active_sessions = (
            db.query(UserSession)
            .filter(
                UserSession.user_id == user_id,
                UserSession.is_revoked == False,
                UserSession.is_active == True,
            )
            .order_by(UserSession.last_activity.desc())
            .all()
        )

        # Fazla oturumları iptal et (en eski olanları)
        if len(active_sessions) >= self.MAX_SESSIONS_PER_USER:
            for old_session in active_sessions[self.MAX_SESSIONS_PER_USER - 1 :]:
                old_session.revoke("max_sessions")

    def _log_action(
        self,
        db: DBSession,
        action: str,
        module: str,
        description: str,
        user: Optional[User] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Audit log kaydı oluşturur"""
        ctx = get_current_user()

        log = AuditLog(
            user_id=user.id if user else ctx.user_id,
            username=user.username if user else ctx.username,
            action=action,
            module=module,
            description=description,
            ip_address=ip_address or ctx.ip_address,
        )
        db.add(log)

    @property
    def current_session(self) -> Optional[UserSession]:
        """Mevcut oturumu döndürür"""
        return self._current_session

    @property
    def session_token(self) -> Optional[str]:
        """Mevcut oturum token'ını döndürür"""
        if self._current_session:
            return self._current_session.session_token
        return None


# Singleton instance
session_manager = SessionManager()
