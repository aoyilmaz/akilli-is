from __future__ import annotations

"""
Akıllı İş - Dashboard Widget Manager

Widget kayıt, oluşturma ve yönetim işlemleri.
"""

from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass

from database.base import get_session
from database.models.dashboard import (
    DashboardWidget,
    RoleDefaultLayout,
    UserDashboardLayout,
)
from core.user_context import UserContext

from .widgets.base import BaseWidget, WidgetConfig


@dataclass
class WidgetDefinition:
    """Widget tanım bilgileri"""

    code: str
    name: str
    description: str
    widget_type: str
    icon: str
    default_size: tuple  # (width, height)
    min_size: tuple
    max_size: tuple
    required_permission: Optional[str]
    widget_class: Type[BaseWidget]


class WidgetManager:
    """
    Dashboard widget yöneticisi

    Widget'ları kayıt altına alır, oluşturur ve kullanıcı düzenlerini yönetir.

    Kullanım:
        # Widget sınıfını kaydet
        WidgetManager.register(WeatherWidget)

        # Widget oluştur
        widget = WidgetManager.create_widget("weather", config)

        # Kullanıcı düzenini al
        layout = WidgetManager.get_user_layout(user_id)

        # Düzeni kaydet
        WidgetManager.save_user_layout(user_id, layout)
    """

    # Kayıtlı widget sınıfları
    _registry: Dict[str, Type[BaseWidget]] = {}

    @classmethod
    def register(cls, widget_class: Type[BaseWidget]):
        """
        Widget sınıfını kaydet

        Args:
            widget_class: BaseWidget'tan türetilmiş widget sınıfı
        """
        if not widget_class.widget_code:
            raise ValueError(
                f"Widget sınıfı {widget_class.__name__} için widget_code tanımlı değil"
            )

        cls._registry[widget_class.widget_code] = widget_class

    @classmethod
    def unregister(cls, widget_code: str):
        """Widget kaydını kaldır"""
        cls._registry.pop(widget_code, None)

    @classmethod
    def get_registered_widgets(cls) -> Dict[str, Type[BaseWidget]]:
        """Kayıtlı tüm widget sınıflarını döner"""
        return cls._registry.copy()

    @classmethod
    def create_widget(
        cls,
        widget_code: str,
        config: Optional[WidgetConfig] = None,
        edit_mode: bool = False,
    ) -> Optional[BaseWidget]:
        """
        Widget kodu ile yeni widget oluşturur

        Args:
            widget_code: Widget kodu
            config: Widget yapılandırması
            edit_mode: Düzenleme modunda mı

        Returns:
            Oluşturulan widget veya None
        """
        widget_class = cls._registry.get(widget_code)
        if not widget_class:
            print(f"Widget bulunamadı: {widget_code}")
            return None

        try:
            widget_config = config or WidgetConfig(widget_code=widget_code)
            return widget_class(config=widget_config, edit_mode=edit_mode)
        except Exception as e:
            print(f"Widget oluşturma hatası ({widget_code}): {e}")
            return None

    @classmethod
    def get_available_widgets(
        cls, user_context: Optional[UserContext] = None
    ) -> List[WidgetDefinition]:
        """
        Kullanıcının erişebildiği widget listesini döner

        Args:
            user_context: Kullanıcı bağlamı (izin kontrolü için)

        Returns:
            Erişilebilir widget tanımları listesi
        """
        available = []

        for code, widget_class in cls._registry.items():
            # Erişim kontrolü
            if user_context and not widget_class.can_user_access(user_context):
                continue

            definition = WidgetDefinition(
                code=code,
                name=widget_class.widget_name,
                description=getattr(widget_class, "widget_description", ""),
                widget_type=widget_class.widget_type,
                icon=getattr(widget_class, "widget_icon", "puzzle-piece"),
                default_size=widget_class.default_size,
                min_size=widget_class.min_size,
                max_size=widget_class.max_size,
                required_permission=widget_class.required_permission,
                widget_class=widget_class,
            )
            available.append(definition)

        return sorted(available, key=lambda w: w.name)

    @classmethod
    def get_widgets_from_db(cls) -> List[DashboardWidget]:
        """Veritabanından widget tanımlarını getirir"""
        session = get_session()
        try:
            return (
                session.query(DashboardWidget)
                .filter(DashboardWidget.is_active == True)
                .order_by(DashboardWidget.sort_order)
                .all()
            )
        finally:
            pass

    @classmethod
    def get_user_layout(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Kullanıcının dashboard düzenini getirir

        Args:
            user_id: Kullanıcı ID

        Returns:
            Layout JSON veya None
        """
        session = get_session()
        try:
            user_layout = (
                session.query(UserDashboardLayout)
                .filter(
                    UserDashboardLayout.user_id == user_id,
                    UserDashboardLayout.is_active == True,
                )
                .first()
            )

            if user_layout:
                return user_layout.layout

            return None
        finally:
            pass

    @classmethod
    def get_role_default_layout(cls, role_id: int) -> Optional[Dict[str, Any]]:
        """
        Rol için varsayılan dashboard düzenini getirir

        Args:
            role_id: Rol ID

        Returns:
            Layout JSON veya None
        """
        session = get_session()
        try:
            role_layout = (
                session.query(RoleDefaultLayout)
                .filter(
                    RoleDefaultLayout.role_id == role_id,
                    RoleDefaultLayout.is_active == True,
                )
                .first()
            )

            if role_layout:
                return role_layout.layout

            return None
        finally:
            pass

    @classmethod
    def get_effective_layout(cls, user_context: UserContext) -> Dict[str, Any]:
        """
        Kullanıcı için etkili dashboard düzenini getirir

        Öncelik sırası:
        1. Kullanıcının özel düzeni
        2. Rolün varsayılan düzeni
        3. Sistem varsayılan düzeni

        Args:
            user_context: Kullanıcı bağlamı

        Returns:
            Layout JSON
        """
        if not user_context or not user_context.user_id:
            return cls.get_default_layout(None)

        # 1. Kullanıcı düzeni
        user_layout = cls.get_user_layout(user_context.user_id)
        if user_layout:
            return user_layout

        # 2. Rol düzeni - roles set'inden ilk rolü al
        if user_context.roles:
            # Rol adından role_id bulmak için veritabanı sorgusu
            session = get_session()
            try:
                from database.models.user import Role

                role_name = next(iter(user_context.roles))
                role = session.query(Role).filter(Role.code == role_name).first()
                if role:
                    role_layout = cls.get_role_default_layout(role.id)
                    if role_layout:
                        return role_layout
            finally:
                pass

        # 3. Sistem varsayılanı
        return cls.get_default_layout(user_context)

    @classmethod
    def get_default_layout(
        cls, user_context: Optional[UserContext] = None
    ) -> Dict[str, Any]:
        """
        Sistem varsayılan düzenini oluşturur

        Args:
            user_context: Kullanıcı bağlamı (izin filtresi için)

        Returns:
            Varsayılan layout JSON
        """
        widgets = []

        # Temel widget'lar - herkes görebilir
        # NOT: Harici API gerektiren widget'lar şu an devre dışı
        widgets.extend(
            [
                {
                    "widget_code": "notifications",
                    "position": {"row": 1, "col": 3},
                    "size": {"width": 1, "height": 2},
                    "config": {},
                },
                {
                    "widget_code": "quick_actions",
                    "position": {"row": 1, "col": 0},
                    "size": {"width": 1, "height": 1},
                    "config": {},
                },
            ]
        )

        # İzne bağlı widget'lar
        if user_context:
            permissions = user_context.permissions or []

            if "sales.view" in permissions or user_context.is_superuser:
                widgets.append(
                    {
                        "widget_code": "stat_sales_today",
                        "position": {"row": 0, "col": 0},
                        "size": {"width": 1, "height": 1},
                        "config": {},
                    }
                )

            if "inventory.view" in permissions or user_context.is_superuser:
                widgets.append(
                    {
                        "widget_code": "stat_low_stock",
                        "position": {"row": 0, "col": 1},
                        "size": {"width": 1, "height": 1},
                        "config": {},
                    }
                )

            if "production.view" in permissions or user_context.is_superuser:
                widgets.append(
                    {
                        "widget_code": "stat_open_work_orders",
                        "position": {"row": 0, "col": 2},
                        "size": {"width": 1, "height": 1},
                        "config": {},
                    }
                )

        return {"version": "1.0", "grid_columns": 4, "widgets": widgets}

    @classmethod
    def save_user_layout(cls, user_id: int, layout: Dict[str, Any]) -> bool:
        """
        Kullanıcı düzenini kaydeder

        Args:
            user_id: Kullanıcı ID
            layout: Layout JSON

        Returns:
            Başarılı ise True
        """
        session = get_session()
        try:
            existing = (
                session.query(UserDashboardLayout)
                .filter(UserDashboardLayout.user_id == user_id)
                .first()
            )

            if existing:
                existing.layout = layout
            else:
                new_layout = UserDashboardLayout(user_id=user_id, layout=layout)
                session.add(new_layout)

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Düzen kaydetme hatası: {e}")
            return False
        finally:
            pass

    @classmethod
    def reset_user_layout(cls, user_id: int) -> bool:
        """
        Kullanıcı düzenini sıfırlar (varsayılana döner)

        Args:
            user_id: Kullanıcı ID

        Returns:
            Başarılı ise True
        """
        session = get_session()
        try:
            session.query(UserDashboardLayout).filter(
                UserDashboardLayout.user_id == user_id
            ).delete()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Düzen sıfırlama hatası: {e}")
            return False
        finally:
            pass

    @classmethod
    def save_role_default_layout(cls, role_id: int, layout: Dict[str, Any]) -> bool:
        """
        Rol varsayılan düzenini kaydeder

        Args:
            role_id: Rol ID
            layout: Layout JSON

        Returns:
            Başarılı ise True
        """
        session = get_session()
        try:
            existing = (
                session.query(RoleDefaultLayout)
                .filter(RoleDefaultLayout.role_id == role_id)
                .first()
            )

            if existing:
                existing.layout = layout
            else:
                new_layout = RoleDefaultLayout(role_id=role_id, layout=layout)
                session.add(new_layout)

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Rol düzeni kaydetme hatası: {e}")
            return False
        finally:
            pass
