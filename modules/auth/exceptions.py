"""
Akıllı İş - Yetkilendirme Hataları

Tüm auth/authorization ile ilgili özel exception sınıfları.
"""


class AuthError(Exception):
    """Tüm yetkilendirme hatalarının temel sınıfı"""

    def __init__(self, message: str = "Yetkilendirme hatası", code: str = "AUTH_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AuthenticationError(AuthError):
    """Kimlik doğrulama hatası (giriş başarısız)"""

    def __init__(self, message: str = "Kimlik doğrulama başarısız"):
        super().__init__(message, "AUTHENTICATION_FAILED")


class AuthorizationError(AuthError):
    """Yetkilendirme hatası (izin yok)"""

    def __init__(self, message: str = "Bu işlem için yetkiniz yok"):
        super().__init__(message, "AUTHORIZATION_FAILED")


class PermissionDenied(AuthorizationError):
    """Belirli bir izin eksik"""

    def __init__(
        self, permission: str, message: str = None
    ):
        self.permission = permission
        msg = message or f"'{permission}' izni gerekli"
        super().__init__(msg)
        self.code = "PERMISSION_DENIED"


class SessionExpired(AuthError):
    """Oturum süresi dolmuş"""

    def __init__(self, message: str = "Oturumunuz sona erdi. Lütfen tekrar giriş yapın."):
        super().__init__(message, "SESSION_EXPIRED")


class AccountLocked(AuthError):
    """Hesap kilitli"""

    def __init__(
        self, minutes_remaining: int = 0, message: str = None
    ):
        self.minutes_remaining = minutes_remaining
        msg = message or f"Hesabınız kilitli. {minutes_remaining} dakika sonra tekrar deneyin."
        super().__init__(msg, "ACCOUNT_LOCKED")


class InvalidCredentials(AuthenticationError):
    """Geçersiz kullanıcı adı veya şifre"""

    def __init__(self, message: str = "Kullanıcı adı veya şifre hatalı"):
        super().__init__(message)
        self.code = "INVALID_CREDENTIALS"


class UserNotFound(AuthenticationError):
    """Kullanıcı bulunamadı"""

    def __init__(self, username: str = None):
        msg = f"Kullanıcı bulunamadı: {username}" if username else "Kullanıcı bulunamadı"
        super().__init__(msg)
        self.code = "USER_NOT_FOUND"


class UserInactive(AuthenticationError):
    """Kullanıcı hesabı devre dışı"""

    def __init__(self, message: str = "Kullanıcı hesabı devre dışı"):
        super().__init__(message)
        self.code = "USER_INACTIVE"


class RoleNotFound(AuthError):
    """Rol bulunamadı"""

    def __init__(self, role_code: str = None):
        msg = f"Rol bulunamadı: {role_code}" if role_code else "Rol bulunamadı"
        super().__init__(msg, "ROLE_NOT_FOUND")
