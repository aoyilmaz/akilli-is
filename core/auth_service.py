"""
Akıllı İş ERP - Auth Service
Kullanıcı oturumu ve yetkilendirme yönetimi
"""

from typing import Optional, List, Set
from database.models.user import User


class AuthService:
    """
    Singleton Auth Service
    Kullanıcı oturumunu ve yetkilerini yönetir
    """

    _instance = None
    _current_user: Optional[User] = None
    _permissions_cache: Set[str] = set()
    _roles_cache: Set[str] = set()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def login(cls, user: User) -> None:
        """Kullanıcı oturumunu başlat"""
        cls._current_user = user
        cls._cache_permissions()

    @classmethod
    def logout(cls) -> None:
        """Kullanıcı oturumunu kapat"""
        cls._current_user = None
        cls._permissions_cache.clear()
        cls._roles_cache.clear()

    @classmethod
    def _cache_permissions(cls) -> None:
        """Kullanıcının izinlerini ve rollerini önbelleğe al"""
        cls._permissions_cache.clear()
        cls._roles_cache.clear()

        if cls._current_user is None:
            return

        # Rolleri cache'le
        for role in cls._current_user.roles:
            cls._roles_cache.add(role.code)
            # Her rolün izinlerini ekle
            for perm in role.permissions:
                cls._permissions_cache.add(perm.code)

    @classmethod
    def get_current_user(cls) -> Optional[User]:
        """Aktif kullanıcıyı döndür"""
        return cls._current_user

    @classmethod
    def is_authenticated(cls) -> bool:
        """Kullanıcı giriş yapmış mı?"""
        return cls._current_user is not None

    @classmethod
    def is_superuser(cls) -> bool:
        """Kullanıcı süper admin mi?"""
        if cls._current_user is None:
            return False
        return cls._current_user.is_superuser

    @classmethod
    def has_permission(cls, permission_code: str) -> bool:
        """
        Kullanıcının belirli bir izni var mı?
        Süper adminler her zaman True döner
        """
        if cls._current_user is None:
            return False

        if cls._current_user.is_superuser:
            return True

        return permission_code in cls._permissions_cache

    @classmethod
    def has_role(cls, role_code: str) -> bool:
        """Kullanıcının belirli bir rolü var mı?"""
        if cls._current_user is None:
            return False

        return role_code in cls._roles_cache

    @classmethod
    def has_any_role(cls, role_codes: List[str]) -> bool:
        """Kullanıcının verilen rollerden herhangi biri var mı?"""
        return any(cls.has_role(code) for code in role_codes)

    @classmethod
    def has_any_permission(cls, permission_codes: List[str]) -> bool:
        """Kullanıcının verilen izinlerden herhangi biri var mı?"""
        if cls._current_user is None:
            return False

        if cls._current_user.is_superuser:
            return True

        return any(code in cls._permissions_cache for code in permission_codes)

    @classmethod
    def get_allowed_modules(cls) -> Set[str]:
        """
        Kullanıcının erişebileceği modülleri döndür
        İzinlerden modül kısmını çıkar (örn: 'inventory.view' -> 'inventory')
        """
        if cls._current_user is None:
            return set()

        if cls._current_user.is_superuser:
            return {"*"}  # Tüm modüller

        modules = set()
        for perm in cls._permissions_cache:
            if "." in perm:
                module = perm.split(".")[0]
                modules.add(module)

        # Her zaman dashboard erişimi
        modules.add("dashboard")

        return modules

    @classmethod
    def can_access_page(cls, page_id: str) -> bool:
        """
        Kullanıcının belirli bir sayfaya erişip erişemeyeceğini kontrol et
        permission_map modülünden PAGE_PERMISSIONS kullanır
        """
        from core.permission_map import PAGE_PERMISSIONS

        if cls._current_user is None:
            return False

        if cls._current_user.is_superuser:
            return True

        # Sayfa için gerekli izni al
        required_permission = PAGE_PERMISSIONS.get(page_id)

        # None ise herkese açık
        if required_permission is None:
            return True

        # Liste ise herhangi biri yeterli
        if isinstance(required_permission, list):
            return cls.has_any_permission(required_permission)

        # Tek izin
        return cls.has_permission(required_permission)

    @classmethod
    def get_user_info(cls) -> dict:
        """Kullanıcı bilgilerini dictionary olarak döndür"""
        if cls._current_user is None:
            return {}

        user = cls._current_user
        return {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "is_superuser": user.is_superuser,
            "roles": list(cls._roles_cache),
            "permissions": list(cls._permissions_cache),
        }
