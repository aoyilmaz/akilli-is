"""
Akıllı İş - Yetkilendirme Modülü

Kullanıcı yönetimi, rol ve izin sistemi, oturum yönetimi.
"""

from .exceptions import (
    AuthError,
    AuthenticationError,
    AuthorizationError,
    PermissionDenied,
    SessionExpired,
    AccountLocked,
)

from .decorators import (
    require_permission,
    require_any_permission,
    require_all_permissions,
    require_role,
    require_auth,
)

from .services import (
    AuthService,
    PermissionService,
    RoleService,
    UserService,
)

__all__ = [
    # Exceptions
    "AuthError",
    "AuthenticationError",
    "AuthorizationError",
    "PermissionDenied",
    "SessionExpired",
    "AccountLocked",
    # Decorators
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
    "require_role",
    "require_auth",
    # Services
    "AuthService",
    "PermissionService",
    "RoleService",
    "UserService",
]
