"""
Akıllı İş - Yetkilendirme Decorator'ları

Fonksiyon ve metod düzeyinde izin kontrolü için decorator'lar.
"""

from functools import wraps
from typing import Callable, Union, List, Any

from core.user_context import get_current_user
from .exceptions import PermissionDenied, AuthorizationError, AuthenticationError


def require_auth(func: Callable) -> Callable:
    """
    Kullanıcının giriş yapmış olmasını gerektirir.

    Kullanım:
        @require_auth
        def some_function():
            pass
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        ctx = get_current_user()
        if not ctx.is_authenticated:
            raise AuthenticationError("Bu işlem için giriş yapmalısınız")
        return func(*args, **kwargs)

    return wrapper


def require_permission(permission: str) -> Callable:
    """
    Belirli bir izni gerektirir.

    Kullanım:
        @require_permission("inventory.edit")
        def update_stock():
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            ctx = get_current_user()

            if not ctx.is_authenticated:
                raise AuthenticationError("Bu işlem için giriş yapmalısınız")

            if not ctx.has_permission(permission):
                raise PermissionDenied(permission)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_any_permission(*permissions: str) -> Callable:
    """
    Verilen izinlerden en az birini gerektirir.

    Kullanım:
        @require_any_permission("inventory.view", "inventory.edit")
        def view_stock():
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            ctx = get_current_user()

            if not ctx.is_authenticated:
                raise AuthenticationError("Bu işlem için giriş yapmalısınız")

            if not ctx.has_any_permission(*permissions):
                raise AuthorizationError(
                    f"Şu izinlerden en az biri gerekli: {', '.join(permissions)}"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_all_permissions(*permissions: str) -> Callable:
    """
    Verilen izinlerin tümünü gerektirir.

    Kullanım:
        @require_all_permissions("inventory.view", "inventory.edit")
        def manage_stock():
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            ctx = get_current_user()

            if not ctx.is_authenticated:
                raise AuthenticationError("Bu işlem için giriş yapmalısınız")

            if not ctx.has_all_permissions(*permissions):
                missing = set(permissions) - ctx.permissions
                raise AuthorizationError(
                    f"Eksik izinler: {', '.join(missing)}"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(role: Union[str, List[str]]) -> Callable:
    """
    Belirli bir rol veya rollerden birini gerektirir.

    Kullanım:
        @require_role("ADMIN")
        def admin_only():
            pass

        @require_role(["ADMIN", "MANAGER"])
        def admin_or_manager():
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            ctx = get_current_user()

            if not ctx.is_authenticated:
                raise AuthenticationError("Bu işlem için giriş yapmalısınız")

            roles = [role] if isinstance(role, str) else role

            if not any(ctx.has_role(r) for r in roles):
                raise AuthorizationError(
                    f"Bu işlem için şu rollerden biri gerekli: {', '.join(roles)}"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_superuser(func: Callable) -> Callable:
    """
    Superuser (sistem yöneticisi) yetkisi gerektirir.

    Kullanım:
        @require_superuser
        def system_config():
            pass
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        ctx = get_current_user()

        if not ctx.is_authenticated:
            raise AuthenticationError("Bu işlem için giriş yapmalısınız")

        if not ctx.is_superuser:
            raise AuthorizationError("Bu işlem sadece sistem yöneticileri içindir")

        return func(*args, **kwargs)

    return wrapper


def require_module_access(module: str, action: str = "view") -> Callable:
    """
    Modül erişimi gerektirir (module.action formatında).

    Kullanım:
        @require_module_access("inventory", "edit")
        def edit_item():
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            ctx = get_current_user()

            if not ctx.is_authenticated:
                raise AuthenticationError("Bu işlem için giriş yapmalısınız")

            if not ctx.has_module_access(module, action):
                raise PermissionDenied(
                    f"{module}.{action}",
                    f"'{module}' modülüne {action} erişimi yok",
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


# PyQt6 slot'ları için decorator
def protected_slot(permission: str = None) -> Callable:
    """
    PyQt slot'ları için yetkilendirme decorator'ı.
    Hata durumunda QMessageBox gösterir.

    Kullanım:
        @protected_slot("inventory.edit")
        def on_save_clicked(self):
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            from PyQt6.QtWidgets import QMessageBox

            ctx = get_current_user()

            if not ctx.is_authenticated:
                QMessageBox.warning(
                    self if hasattr(self, "window") else None,
                    "Yetkilendirme Hatası",
                    "Bu işlem için giriş yapmalısınız.",
                )
                return None

            if permission and not ctx.has_permission(permission):
                QMessageBox.warning(
                    self if hasattr(self, "window") else None,
                    "Yetkilendirme Hatası",
                    f"Bu işlem için '{permission}' izniniz yok.",
                )
                return None

            return func(self, *args, **kwargs)

        return wrapper

    return decorator
