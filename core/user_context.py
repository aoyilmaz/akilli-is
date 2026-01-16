"""
Akıllı İş - Thread-Safe Kullanıcı Bağlamı

Desktop uygulaması için global kullanıcı bağlamını yönetir.
SQLAlchemy event listener'ları ve izin kontrolleri bu context'i kullanır.
"""

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Optional, Set, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from database.models.user import User


@dataclass
class UserContext:
    """Aktif kullanıcı bilgilerini tutar"""

    user_id: Optional[int] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None

    # Roller ve izinler (cache)
    roles: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=set)

    # Oturum bilgileri
    session_id: Optional[int] = None
    session_token: Optional[str] = None
    login_time: Optional[datetime] = None

    # Cihaz bilgileri
    ip_address: Optional[str] = None
    device_name: Optional[str] = None

    # Admin/superuser durumu
    is_superuser: bool = False

    @property
    def is_authenticated(self) -> bool:
        """Kullanıcı giriş yapmış mı?"""
        return self.user_id is not None

    def has_permission(self, permission_code: str) -> bool:
        """Belirli bir izni kontrol eder"""
        if self.is_superuser:
            return True
        return permission_code in self.permissions

    def has_any_permission(self, *permission_codes: str) -> bool:
        """Verilen izinlerden herhangi birine sahip mi?"""
        if self.is_superuser:
            return True
        return bool(self.permissions & set(permission_codes))

    def has_all_permissions(self, *permission_codes: str) -> bool:
        """Verilen izinlerin tümüne sahip mi?"""
        if self.is_superuser:
            return True
        return set(permission_codes).issubset(self.permissions)

    def has_role(self, role_code: str) -> bool:
        """Belirli bir rolü kontrol eder"""
        return role_code in self.roles

    def has_module_access(self, module: str, action: str = "view") -> bool:
        """Modül erişimini kontrol eder (örn: inventory.view)"""
        permission_code = f"{module}.{action}"
        return self.has_permission(permission_code)

    def clear(self) -> None:
        """Context'i temizler (çıkış için)"""
        self.user_id = None
        self.username = None
        self.full_name = None
        self.email = None
        self.roles = set()
        self.permissions = set()
        self.session_id = None
        self.session_token = None
        self.login_time = None
        self.ip_address = None
        self.device_name = None
        self.is_superuser = False


# Thread-safe context variable
_current_user: ContextVar[UserContext] = ContextVar(
    "current_user", default=UserContext()
)


def get_current_user() -> UserContext:
    """Mevcut kullanıcı context'ini döndürür"""
    return _current_user.get()


def set_current_user(context: UserContext) -> None:
    """Kullanıcı context'ini ayarlar"""
    _current_user.set(context)


def clear_current_user() -> None:
    """Kullanıcı context'ini temizler"""
    ctx = _current_user.get()
    ctx.clear()


def create_user_context(user: "User", session_id: Optional[int] = None) -> UserContext:
    """
    User model'inden UserContext oluşturur.

    Args:
        user: Veritabanından alınan User nesnesi
        session_id: Oturum ID'si (varsa)

    Returns:
        Doldurulmuş UserContext
    """
    # İzinleri topla
    permissions: Set[str] = set()
    roles: Set[str] = set()

    for role in user.roles:
        roles.add(role.code)
        for perm in role.permissions:
            permissions.add(perm.code)

    context = UserContext(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        roles=roles,
        permissions=permissions,
        session_id=session_id,
        login_time=datetime.utcnow(),
        is_superuser=user.is_superuser,
    )

    return context


# Audit loglama için yardımcı fonksiyonlar
def get_audit_user_info() -> dict:
    """
    Audit log için kullanıcı bilgilerini döndürür.

    Returns:
        dict: user_id, username, ip_address
    """
    ctx = get_current_user()
    return {
        "user_id": ctx.user_id,
        "username": ctx.username,
        "ip_address": ctx.ip_address,
    }


def get_current_user_id() -> Optional[int]:
    """Mevcut kullanıcının ID'sini döndürür"""
    return get_current_user().user_id


def get_current_username() -> Optional[str]:
    """Mevcut kullanıcının adını döndürür"""
    return get_current_user().username


def is_authenticated() -> bool:
    """Kullanıcı giriş yapmış mı?"""
    return get_current_user().is_authenticated
