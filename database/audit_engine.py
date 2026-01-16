"""
Akıllı İş - Otomatik Audit Loglama Engine

SQLAlchemy event listener'ları kullanarak veritabanı değişikliklerini
otomatik olarak AuditLog tablosuna kaydeder.
"""

from datetime import datetime
from typing import Any, Dict, Set, Optional, List

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.orm.attributes import get_history

from database.base import Base
from database.models.user import AuditLog


# Audit loglamadan hariç tutulacak tablolar
EXCLUDED_TABLES: Set[str] = {
    "audit_logs",  # Audit log kendini loglamamalı
    "user_sessions",  # Oturum detayları gereksiz
    "settings",  # Ayarlar ayrı loglanıyor
    "sequences",  # Numara serileri
    "alembic_version",  # Migration versiyonu
}

# Loglama için dahil edilmeyecek alanlar (hassas veri)
EXCLUDED_COLUMNS: Set[str] = {
    "password_hash",
    "password",
    "secret",
    "token",
    "session_token",
    "refresh_token",
}

# Tablo adından modül adını çıkar
TABLE_TO_MODULE: Dict[str, str] = {
    # Kullanıcı yönetimi
    "users": "auth",
    "roles": "auth",
    "permissions": "auth",
    "user_roles": "auth",
    "role_permissions": "auth",
    # Stok
    "items": "inventory",
    "item_categories": "inventory",
    "warehouses": "inventory",
    "stock_movements": "inventory",
    "stock_balances": "inventory",
    "units": "inventory",
    # Üretim
    "work_orders": "production",
    "bom": "production",
    "work_stations": "production",
    # Satış
    "customers": "sales",
    "sales_orders": "sales",
    "sales_order_items": "sales",
    "invoices": "sales",
    # Satın alma
    "suppliers": "purchasing",
    "purchase_orders": "purchasing",
    "purchase_order_items": "purchasing",
    # HR
    "employees": "hr",
    "departments": "hr",
    "positions": "hr",
    "leaves": "hr",
    # Ortak
    "notes": "common",
    "attachments": "common",
}


class AuditEngine:
    """
    SQLAlchemy event listener'ları ile otomatik audit loglama.

    Kullanım:
        from database.audit_engine import audit_engine
        audit_engine.init_listeners()  # Uygulama başlangıcında çağır
    """

    _instance: Optional["AuditEngine"] = None
    _enabled: bool = True
    _pending_logs: List[Dict[str, Any]] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init_listeners(self) -> None:
        """SQLAlchemy event listener'larını kaydeder"""
        event.listen(DBSession, "before_flush", self._before_flush)
        event.listen(DBSession, "after_commit", self._after_commit)
        event.listen(DBSession, "after_rollback", self._after_rollback)

    def enable(self) -> None:
        """Audit loglamayı etkinleştirir"""
        self._enabled = True

    def disable(self) -> None:
        """Audit loglamayı devre dışı bırakır (migration, seed vb. için)"""
        self._enabled = False

    def _before_flush(self, session: DBSession, flush_context, instances) -> None:
        """Flush öncesi değişiklikleri yakalar"""
        if not self._enabled:
            return

        # Mevcut kullanıcı bilgilerini al
        from core.user_context import get_audit_user_info

        user_info = get_audit_user_info()

        # Yeni nesneler (INSERT)
        for obj in session.new:
            if self._should_audit(obj):
                self._pending_logs.append(
                    self._create_log_entry(
                        action="CREATE",
                        obj=obj,
                        user_info=user_info,
                        new_values=self._get_object_values(obj),
                    )
                )

        # Değişen nesneler (UPDATE)
        for obj in session.dirty:
            if self._should_audit(obj) and session.is_modified(obj):
                changes = self._get_changes(obj)
                if changes:  # Gerçek değişiklik varsa
                    old_values, new_values = changes
                    self._pending_logs.append(
                        self._create_log_entry(
                            action="UPDATE",
                            obj=obj,
                            user_info=user_info,
                            old_values=old_values,
                            new_values=new_values,
                        )
                    )

        # Silinen nesneler (DELETE)
        for obj in session.deleted:
            if self._should_audit(obj):
                self._pending_logs.append(
                    self._create_log_entry(
                        action="DELETE",
                        obj=obj,
                        user_info=user_info,
                        old_values=self._get_object_values(obj),
                    )
                )

    def _after_commit(self, session: DBSession) -> None:
        """Commit sonrası logları veritabanına yazar"""
        if not self._pending_logs:
            return

        # Logları kopyala ve temizle (reentrant güvenliği)
        logs_to_write = self._pending_logs.copy()
        self._pending_logs.clear()

        try:
            # Bağımsız bir session oluştur (scoped_session'dan bağımsız)
            from database.base import get_engine
            from sqlalchemy.orm import sessionmaker

            # Yeni bir session factory oluştur (scoped olmayan)
            AuditSessionFactory = sessionmaker(
                bind=get_engine(),
                autocommit=False,
                autoflush=True,
                expire_on_commit=False,
            )

            audit_session = AuditSessionFactory()
            try:
                for log_data in logs_to_write:
                    log = AuditLog(**log_data)
                    audit_session.add(log)
                audit_session.commit()
            except Exception as e:
                audit_session.rollback()
                print(f"Audit log hatası: {e}")
            finally:
                audit_session.close()

        except Exception as e:
            # Audit log hatası ana işlemi etkilememeli
            print(f"Audit log hatası: {e}")

    def _after_rollback(self, session: DBSession) -> None:
        """Rollback sonrası bekleyen logları temizler"""
        self._pending_logs.clear()

    def _should_audit(self, obj: Any) -> bool:
        """Bu nesne loglanmalı mı?"""
        if not hasattr(obj, "__tablename__"):
            return False
        return obj.__tablename__ not in EXCLUDED_TABLES

    def _get_table_name(self, obj: Any) -> str:
        """Nesnenin tablo adını döndürür"""
        return getattr(obj, "__tablename__", "unknown")

    def _get_module(self, table_name: str) -> str:
        """Tablo adından modül adını çıkarır"""
        return TABLE_TO_MODULE.get(table_name, "other")

    def _get_object_values(self, obj: Any) -> Dict[str, Any]:
        """Nesnenin tüm değerlerini döndürür (hassas alanlar hariç)"""
        mapper = inspect(obj.__class__)
        values = {}

        for column in mapper.columns:
            if column.name in EXCLUDED_COLUMNS:
                continue
            value = getattr(obj, column.name, None)
            values[column.name] = self._serialize_value(value)

        return values

    def _get_changes(self, obj: Any) -> Optional[tuple]:
        """
        Değişen alanları tespit eder.

        Returns:
            (old_values, new_values) veya None (değişiklik yoksa)
        """
        mapper = inspect(obj.__class__)
        old_values = {}
        new_values = {}

        for column in mapper.columns:
            if column.name in EXCLUDED_COLUMNS:
                continue

            history = get_history(obj, column.name)

            if history.has_changes():
                old = history.deleted[0] if history.deleted else None
                new = history.added[0] if history.added else getattr(obj, column.name)

                old_values[column.name] = self._serialize_value(old)
                new_values[column.name] = self._serialize_value(new)

        if old_values:
            return old_values, new_values
        return None

    def _serialize_value(self, value: Any) -> Any:
        """Değeri JSON-serializable formata çevirir"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, (int, float, str, bool)):
            return value
        if hasattr(value, "name"):  # Enum
            return value.name
        return str(value)

    def _create_log_entry(
        self,
        action: str,
        obj: Any,
        user_info: Dict[str, Any],
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Audit log kaydı oluşturur"""
        table_name = self._get_table_name(obj)
        record_id = getattr(obj, "id", None)

        return {
            "user_id": user_info.get("user_id"),
            "username": user_info.get("username"),
            "ip_address": user_info.get("ip_address"),
            "action": action,
            "module": self._get_module(table_name),
            "table_name": table_name,
            "record_id": record_id,
            "old_values": old_values,
            "new_values": new_values,
            "description": self._generate_description(action, table_name, record_id, obj),
        }

    def _generate_description(
        self, action: str, table_name: str, record_id: Any, obj: Any
    ) -> str:
        """İnsan okunabilir açıklama oluşturur"""
        # Nesne adını bulmaya çalış
        name = None
        for attr in ["name", "code", "username", "title", "employee_no"]:
            if hasattr(obj, attr):
                name = getattr(obj, attr)
                break

        action_tr = {"CREATE": "oluşturuldu", "UPDATE": "güncellendi", "DELETE": "silindi"}

        if name:
            return f"{table_name} '{name}' {action_tr.get(action, action)}"
        return f"{table_name} #{record_id} {action_tr.get(action, action)}"


# Singleton instance
audit_engine = AuditEngine()


# Manuel audit log fonksiyonu (özel durumlar için)
def log_action(
    db: DBSession,
    action: str,
    module: str,
    description: str,
    table_name: Optional[str] = None,
    record_id: Optional[int] = None,
    old_values: Optional[Dict] = None,
    new_values: Optional[Dict] = None,
) -> None:
    """
    Manuel audit log kaydı oluşturur.

    Args:
        db: Veritabanı session'ı
        action: İşlem türü (CREATE, UPDATE, DELETE, EXPORT, IMPORT, vb.)
        module: Modül adı
        description: Açıklama
        table_name: Tablo adı (opsiyonel)
        record_id: Kayıt ID (opsiyonel)
        old_values: Eski değerler (opsiyonel)
        new_values: Yeni değerler (opsiyonel)
    """
    from core.user_context import get_audit_user_info

    user_info = get_audit_user_info()

    log = AuditLog(
        user_id=user_info.get("user_id"),
        username=user_info.get("username"),
        ip_address=user_info.get("ip_address"),
        action=action,
        module=module,
        table_name=table_name,
        record_id=record_id,
        old_values=old_values,
        new_values=new_values,
        description=description,
    )

    db.add(log)
