"""
Akıllı İş - Yetkilendirme Servisleri

Kullanıcı, rol ve izin yönetimi için servis sınıfları.
"""

from datetime import datetime
from typing import Optional, List, Dict, Set, Any
from functools import lru_cache

from sqlalchemy.orm import Session as DBSession, joinedload
from sqlalchemy import or_

from database.models.user import User, Role, Permission, AuditLog, user_roles, role_permissions
from core.user_context import get_current_user, get_audit_user_info
from .exceptions import (
    UserNotFound,
    UserInactive,
    RoleNotFound,
    PermissionDenied,
    InvalidCredentials,
)


class PermissionService:
    """
    İzin yönetimi servisi.

    Özellikleri:
    - İzin CRUD işlemleri
    - İzin cache'leme (performans için)
    - Modül bazlı izin grupları
    """

    # İzin cache'i (permission_code -> Permission)
    _permission_cache: Dict[str, Permission] = {}
    _cache_loaded: bool = False

    @classmethod
    def load_cache(cls, db: DBSession) -> None:
        """Tüm izinleri cache'e yükler"""
        permissions = db.query(Permission).filter(Permission.is_active == True).all()
        cls._permission_cache = {p.code: p for p in permissions}
        cls._cache_loaded = True

    @classmethod
    def clear_cache(cls) -> None:
        """Cache'i temizler"""
        cls._permission_cache.clear()
        cls._cache_loaded = False

    @classmethod
    def get_permission(cls, db: DBSession, code: str) -> Optional[Permission]:
        """İzni kod ile getirir (cache'den)"""
        if not cls._cache_loaded:
            cls.load_cache(db)
        return cls._permission_cache.get(code)

    @staticmethod
    def get_all(db: DBSession, module: Optional[str] = None) -> List[Permission]:
        """Tüm izinleri getirir"""
        query = db.query(Permission).filter(Permission.is_active == True)
        if module:
            query = query.filter(Permission.module == module)
        return query.order_by(Permission.module, Permission.code).all()

    @staticmethod
    def get_by_id(db: DBSession, permission_id: int) -> Optional[Permission]:
        """ID ile izin getirir"""
        return db.query(Permission).filter(Permission.id == permission_id).first()

    @staticmethod
    def create(
        db: DBSession,
        code: str,
        name: str,
        module: str,
        description: Optional[str] = None,
    ) -> Permission:
        """Yeni izin oluşturur"""
        permission = Permission(
            code=code,
            name=name,
            module=module,
            description=description,
        )
        db.add(permission)
        db.flush()

        # Cache'i güncelle
        PermissionService._permission_cache[code] = permission

        return permission

    @staticmethod
    def get_modules(db: DBSession) -> List[str]:
        """Tüm modül isimlerini döndürür"""
        result = (
            db.query(Permission.module)
            .filter(Permission.is_active == True)
            .distinct()
            .all()
        )
        return [r[0] for r in result]


class RoleService:
    """
    Rol yönetimi servisi.
    """

    @staticmethod
    def get_all(db: DBSession, include_inactive: bool = False) -> List[Role]:
        """Tüm rolleri getirir"""
        query = db.query(Role).options(joinedload(Role.permissions))
        if not include_inactive:
            query = query.filter(Role.is_active == True)
        return query.order_by(Role.level.desc(), Role.name).all()

    @staticmethod
    def get_by_id(db: DBSession, role_id: int) -> Optional[Role]:
        """ID ile rol getirir"""
        return (
            db.query(Role)
            .options(joinedload(Role.permissions))
            .filter(Role.id == role_id)
            .first()
        )

    @staticmethod
    def get_by_code(db: DBSession, code: str) -> Optional[Role]:
        """Kod ile rol getirir"""
        return (
            db.query(Role)
            .options(joinedload(Role.permissions))
            .filter(Role.code == code)
            .first()
        )

    @staticmethod
    def create(
        db: DBSession,
        code: str,
        name: str,
        description: Optional[str] = None,
        level: int = 0,
        parent_id: Optional[int] = None,
        permission_ids: Optional[List[int]] = None,
    ) -> Role:
        """Yeni rol oluşturur"""
        role = Role(
            code=code,
            name=name,
            description=description,
            level=level,
            parent_id=parent_id,
        )

        if permission_ids:
            permissions = (
                db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
            )
            role.permissions = permissions

        db.add(role)
        db.flush()
        return role

    @staticmethod
    def update(
        db: DBSession,
        role_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        level: Optional[int] = None,
        permission_ids: Optional[List[int]] = None,
    ) -> Optional[Role]:
        """Rolü günceller"""
        role = RoleService.get_by_id(db, role_id)
        if not role:
            return None

        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        if level is not None:
            role.level = level
        if permission_ids is not None:
            permissions = (
                db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
            )
            role.permissions = permissions

        return role

    @staticmethod
    def delete(db: DBSession, role_id: int) -> bool:
        """Rolü siler (soft delete)"""
        role = RoleService.get_by_id(db, role_id)
        if not role:
            return False

        # ADMIN rolü silinemez
        if role.code == "ADMIN":
            raise PermissionDenied("ADMIN", "ADMIN rolü silinemez")

        role.is_active = False
        return True

    @staticmethod
    def add_permission(db: DBSession, role_id: int, permission_id: int) -> bool:
        """Role izin ekler"""
        role = RoleService.get_by_id(db, role_id)
        permission = db.query(Permission).filter(Permission.id == permission_id).first()

        if not role or not permission:
            return False

        if permission not in role.permissions:
            role.permissions.append(permission)

        return True

    @staticmethod
    def remove_permission(db: DBSession, role_id: int, permission_id: int) -> bool:
        """Rolden izin kaldırır"""
        role = RoleService.get_by_id(db, role_id)
        permission = db.query(Permission).filter(Permission.id == permission_id).first()

        if not role or not permission:
            return False

        if permission in role.permissions:
            role.permissions.remove(permission)

        return True


class UserService:
    """
    Kullanıcı yönetimi servisi.
    """

    @staticmethod
    def get_all(
        db: DBSession,
        include_inactive: bool = False,
        search: Optional[str] = None,
    ) -> List[User]:
        """Tüm kullanıcıları getirir"""
        query = db.query(User).options(joinedload(User.roles))

        if not include_inactive:
            query = query.filter(User.is_active == True)

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_filter),
                    User.email.ilike(search_filter),
                    User.first_name.ilike(search_filter),
                    User.last_name.ilike(search_filter),
                )
            )

        return query.order_by(User.username).all()

    @staticmethod
    def get_by_id(db: DBSession, user_id: int) -> Optional[User]:
        """ID ile kullanıcı getirir"""
        return (
            db.query(User)
            .options(joinedload(User.roles).joinedload(Role.permissions))
            .filter(User.id == user_id)
            .first()
        )

    @staticmethod
    def get_by_username(db: DBSession, username: str) -> Optional[User]:
        """Kullanıcı adı ile getirir"""
        return (
            db.query(User)
            .options(joinedload(User.roles).joinedload(Role.permissions))
            .filter(User.username == username)
            .first()
        )

    @staticmethod
    def get_by_email(db: DBSession, email: str) -> Optional[User]:
        """E-posta ile getirir"""
        return (
            db.query(User)
            .options(joinedload(User.roles).joinedload(Role.permissions))
            .filter(User.email == email)
            .first()
        )

    @staticmethod
    def create(
        db: DBSession,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role_ids: Optional[List[int]] = None,
        is_superuser: bool = False,
        phone: Optional[str] = None,
    ) -> User:
        """Yeni kullanıcı oluşturur"""
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_superuser=is_superuser,
            phone=phone,
        )
        user.set_password(password)

        if role_ids:
            roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
            user.roles = roles

        db.add(user)
        db.flush()
        return user

    @staticmethod
    def update(
        db: DBSession,
        user_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        is_active: Optional[bool] = None,
        role_ids: Optional[List[int]] = None,
    ) -> Optional[User]:
        """Kullanıcıyı günceller"""
        user = UserService.get_by_id(db, user_id)
        if not user:
            return None

        if username is not None:
            user.username = username
        if email is not None:
            user.email = email
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if phone is not None:
            user.phone = phone
        if is_active is not None:
            user.is_active = is_active
        if role_ids is not None:
            roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
            user.roles = roles

        return user

    @staticmethod
    def change_password(
        db: DBSession,
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Kullanıcı şifresini değiştirir"""
        user = UserService.get_by_id(db, user_id)
        if not user:
            raise UserNotFound()

        if not user.check_password(current_password):
            raise InvalidCredentials("Mevcut şifre hatalı")

        user.set_password(new_password)
        return True

    @staticmethod
    def reset_password(db: DBSession, user_id: int, new_password: str) -> bool:
        """Kullanıcı şifresini sıfırlar (admin işlemi)"""
        user = UserService.get_by_id(db, user_id)
        if not user:
            raise UserNotFound()

        user.set_password(new_password)
        user.failed_login_attempts = 0
        user.locked_until = None
        return True

    @staticmethod
    def add_role(db: DBSession, user_id: int, role_id: int) -> bool:
        """Kullanıcıya rol ekler"""
        user = UserService.get_by_id(db, user_id)
        role = db.query(Role).filter(Role.id == role_id).first()

        if not user or not role:
            return False

        if role not in user.roles:
            user.roles.append(role)

        return True

    @staticmethod
    def remove_role(db: DBSession, user_id: int, role_id: int) -> bool:
        """Kullanıcıdan rol kaldırır"""
        user = UserService.get_by_id(db, user_id)
        role = db.query(Role).filter(Role.id == role_id).first()

        if not user or not role:
            return False

        if role in user.roles:
            user.roles.remove(role)

        return True

    @staticmethod
    def get_permissions(db: DBSession, user_id: int) -> Set[str]:
        """Kullanıcının tüm izinlerini döndürür"""
        user = UserService.get_by_id(db, user_id)
        if not user:
            return set()

        if user.is_superuser:
            # Superuser tüm izinlere sahip
            return {p.code for p in db.query(Permission).all()}

        permissions = set()
        for role in user.roles:
            for perm in role.permissions:
                permissions.add(perm.code)

        return permissions

    @staticmethod
    def deactivate(db: DBSession, user_id: int) -> bool:
        """Kullanıcıyı devre dışı bırakır"""
        user = UserService.get_by_id(db, user_id)
        if not user:
            return False

        # Kendini devre dışı bırakamaz
        ctx = get_current_user()
        if ctx.user_id == user_id:
            raise PermissionDenied("self_deactivate", "Kendi hesabınızı devre dışı bırakamazsınız")

        user.is_active = False
        return True


class AuthService:
    """
    Kimlik doğrulama servisi.

    SessionManager'ın üst katmanı - iş mantığı burada.
    """

    @staticmethod
    def authenticate(
        db: DBSession,
        username: str,
        password: str,
    ) -> Optional[User]:
        """
        Kullanıcı adı ve şifre ile doğrulama yapar.

        Returns:
            Başarılıysa User, değilse None
        """
        user = UserService.get_by_username(db, username)
        if not user:
            user = UserService.get_by_email(db, username)

        if not user:
            raise UserNotFound(username)

        if not user.is_active:
            raise UserInactive()

        if not user.check_password(password):
            raise InvalidCredentials()

        return user

    @staticmethod
    def get_audit_logs(
        db: DBSession,
        user_id: Optional[int] = None,
        module: Optional[str] = None,
        action: Optional[str] = None,
        table_name: Optional[str] = None,
        record_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        """Audit logları getirir"""
        query = db.query(AuditLog)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if module:
            query = query.filter(AuditLog.module == module)
        if action:
            query = query.filter(AuditLog.action == action)
        if table_name:
            query = query.filter(AuditLog.table_name == table_name)
        if record_id:
            query = query.filter(AuditLog.record_id == record_id)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        return (
            query.order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_record_history(
        db: DBSession,
        table_name: str,
        record_id: int,
    ) -> List[AuditLog]:
        """Belirli bir kaydın tüm geçmişini getirir"""
        return (
            db.query(AuditLog)
            .filter(
                AuditLog.table_name == table_name,
                AuditLog.record_id == record_id,
            )
            .order_by(AuditLog.created_at.desc())
            .all()
        )
