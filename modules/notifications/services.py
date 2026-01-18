"""
Akıllı İş ERP - Bildirim Servisi

Olay tabanlı bildirim yönetimi.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict

from database.base import get_session
from database.models.common import Notification, NotificationType
from database.models.user import User, Role


class NotificationService:
    """
    Bildirim yönetim servisi

    Kullanım:
        # Tek kullanıcıya bildirim
        NotificationService.send(
            user_id=1,
            title="Stok Uyarısı",
            message="Ürün X stoğu kritik seviyede",
            notification_type=NotificationType.WARNING,
            related_module="inventory"
        )

        # Bir role bildirim
        NotificationService.send_to_role(
            role_code="PURCHASE",
            title="Onay Bekliyor",
            message="Yeni satınalma talebi onay bekliyor",
            notification_type=NotificationType.ACTION_REQUIRED
        )
    """

    @classmethod
    def send(
        cls,
        user_id: int,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        link: Optional[str] = None,
        related_module: Optional[str] = None,
        related_record_id: Optional[int] = None,
    ) -> Optional[Notification]:
        """
        Tek bir kullanıcıya bildirim gönderir.

        Args:
            user_id: Hedef kullanıcı ID'si
            title: Bildirim başlığı
            message: Bildirim mesajı
            notification_type: Bildirim türü (INFO, WARNING, ERROR, SUCCESS, ACTION_REQUIRED)
            link: Tıklanınca gidilecek sayfa (örn: 'inventory/stock-cards/15')
            related_module: İlgili modül (sidebar badge için)
            related_record_id: İlgili kaydın ID'si

        Returns:
            Oluşturulan Notification objesi veya None (hata durumunda)
        """
        session = get_session()
        try:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                link=link,
                related_module=related_module,
                related_record_id=related_record_id,
            )
            session.add(notification)
            session.commit()
            session.refresh(notification)
            return notification
        except Exception as e:
            session.rollback()
            print(f"Bildirim gönderme hatası: {e}")
            return None
        finally:
            session.close()

    @classmethod
    def send_to_users(
        cls,
        user_ids: List[int],
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        link: Optional[str] = None,
        related_module: Optional[str] = None,
        related_record_id: Optional[int] = None,
    ) -> List[Notification]:
        """
        Birden fazla kullanıcıya toplu bildirim gönderir.

        Args:
            user_ids: Hedef kullanıcı ID listesi
            ... (diğer parametreler send ile aynı)

        Returns:
            Oluşturulan Notification listesi
        """
        session = get_session()
        notifications = []
        try:
            for user_id in user_ids:
                notification = Notification(
                    user_id=user_id,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    link=link,
                    related_module=related_module,
                    related_record_id=related_record_id,
                )
                session.add(notification)
                notifications.append(notification)

            session.commit()
            for n in notifications:
                session.refresh(n)
            return notifications
        except Exception as e:
            session.rollback()
            print(f"Toplu bildirim gönderme hatası: {e}")
            return []
        finally:
            session.close()

    @classmethod
    def send_to_role(
        cls,
        role_code: str,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        link: Optional[str] = None,
        related_module: Optional[str] = None,
        related_record_id: Optional[int] = None,
    ) -> List[Notification]:
        """
        Belirli bir role sahip tüm kullanıcılara bildirim gönderir.

        Args:
            role_code: Hedef rol kodu (örn: 'PURCHASE', 'ADMIN')
            ... (diğer parametreler send ile aynı)

        Returns:
            Oluşturulan Notification listesi
        """
        session = get_session()
        try:
            # Role sahip aktif kullanıcıları bul
            role = session.query(Role).filter(Role.code == role_code).first()
            if not role:
                print(f"Rol bulunamadı: {role_code}")
                return []

            user_ids = [
                user.id for user in role.users
                if user.is_active
            ]

            if not user_ids:
                return []

        finally:
            session.close()

        # Kullanıcılara bildirim gönder
        return cls.send_to_users(
            user_ids=user_ids,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
            related_module=related_module,
            related_record_id=related_record_id,
        )

    @classmethod
    def get_unread_count(
        cls,
        user_id: int,
        module: Optional[str] = None,
    ) -> int:
        """
        Okunmamış bildirim sayısını döner.

        Args:
            user_id: Kullanıcı ID'si
            module: Modül filtresi (opsiyonel)

        Returns:
            Okunmamış bildirim sayısı
        """
        session = get_session()
        try:
            query = session.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_active == True,
            )

            if module:
                query = query.filter(Notification.related_module == module)

            return query.count()
        finally:
            session.close()

    @classmethod
    def get_module_counts(cls, user_id: int) -> Dict[str, int]:
        """
        Tüm modüllerin okunmamış bildirim sayılarını döner.
        Sidebar badge'leri için optimize edilmiş tek sorgu.

        Args:
            user_id: Kullanıcı ID'si

        Returns:
            Dict[module_name, count] - Örn: {'inventory': 3, 'purchasing': 1}
        """
        session = get_session()
        try:
            from sqlalchemy import func

            results = (
                session.query(
                    Notification.related_module,
                    func.count(Notification.id),
                )
                .filter(
                    Notification.user_id == user_id,
                    Notification.is_read == False,
                    Notification.is_active == True,
                    Notification.related_module.isnot(None),
                )
                .group_by(Notification.related_module)
                .all()
            )

            return {module: count for module, count in results if module}
        finally:
            session.close()

    @classmethod
    def mark_as_read(
        cls,
        notification_id: int,
        user_id: Optional[int] = None,
    ) -> bool:
        """
        Bildirimi okundu olarak işaretler.

        Args:
            notification_id: Bildirim ID'si
            user_id: Yetki kontrolü için kullanıcı ID (opsiyonel)

        Returns:
            Başarılı ise True
        """
        session = get_session()
        try:
            query = session.query(Notification).filter(
                Notification.id == notification_id
            )

            # Yetki kontrolü
            if user_id:
                query = query.filter(Notification.user_id == user_id)

            notification = query.first()
            if notification:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Bildirim okundu işaretleme hatası: {e}")
            return False
        finally:
            session.close()

    @classmethod
    def mark_all_as_read(
        cls,
        user_id: int,
        module: Optional[str] = None,
    ) -> int:
        """
        Kullanıcının tüm bildirimlerini okundu işaretler.

        Args:
            user_id: Kullanıcı ID'si
            module: Sadece bu modülün bildirimlerini işaretle (opsiyonel)

        Returns:
            İşaretlenen bildirim sayısı
        """
        session = get_session()
        try:
            query = session.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )

            if module:
                query = query.filter(Notification.related_module == module)

            now = datetime.utcnow()
            count = query.update({
                Notification.is_read: True,
                Notification.read_at: now,
            })
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            print(f"Toplu okundu işaretleme hatası: {e}")
            return 0
        finally:
            session.close()

    @classmethod
    def get_latest(
        cls,
        user_id: int,
        limit: int = 10,
        include_read: bool = False,
    ) -> List[Notification]:
        """
        Kullanıcının son bildirimlerini listeler.

        Args:
            user_id: Kullanıcı ID'si
            limit: Maksimum bildirim sayısı
            include_read: Okunmuş bildirimleri de dahil et

        Returns:
            Notification listesi (en yeniden en eskiye)
        """
        session = get_session()
        try:
            query = session.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_active == True,
            )

            if not include_read:
                query = query.filter(Notification.is_read == False)

            notifications = (
                query
                .order_by(Notification.created_at.desc())
                .limit(limit)
                .all()
            )

            # Detached state'i önlemek için kopyala
            return [n for n in notifications]
        finally:
            session.close()

    @classmethod
    def delete_old(cls, days: int = 30) -> int:
        """
        Eski okunmuş bildirimleri siler (temizlik).

        Args:
            days: Bu günden eski okunmuş bildirimler silinir

        Returns:
            Silinen bildirim sayısı
        """
        session = get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            count = session.query(Notification).filter(
                Notification.is_read == True,
                Notification.created_at < cutoff_date,
            ).delete()

            session.commit()
            return count
        except Exception as e:
            session.rollback()
            print(f"Eski bildirim silme hatası: {e}")
            return 0
        finally:
            session.close()

    @classmethod
    def get_by_id(cls, notification_id: int) -> Optional[Notification]:
        """
        ID'ye göre bildirim getirir.

        Args:
            notification_id: Bildirim ID'si

        Returns:
            Notification objesi veya None
        """
        session = get_session()
        try:
            return session.query(Notification).filter(
                Notification.id == notification_id
            ).first()
        finally:
            session.close()
