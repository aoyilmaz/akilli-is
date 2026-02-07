"""
Akıllı İş - Notification Service
Bildirim yönetimi servisi
"""

from typing import List, Optional
from datetime import datetime

from database.base import get_session
from database.models.common import Notification


class NotificationService:
    """
    Bildirim Yönetimi Servisi

    Kullanım:
        NotificationService.create_notification(user_id, title, message)
        NotificationService.create_admin_notification(title, message, link)
        notifications = NotificationService.get_unread(user_id)
    """

    @staticmethod
    def create_notification(
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "info",
        link: str = None,
        related_module: str = None,
        related_record_id: int = None
    ) -> Optional[Notification]:
        """
        Tek bir kullanıcıya bildirim oluştur

        Args:
            user_id: Hedef kullanıcı ID
            title: Bildirim başlığı
            message: Bildirim mesajı
            notification_type: info, warning, error, success, action_required
            link: Tıklandığında gidilecek sayfa (örn: "inventory/stock-cards/15")
            related_module: İlişkili modül adı
            related_record_id: İlişkili kayıt ID

        Returns:
            Oluşturulan Notification objesi
        """
        try:
            session = get_session()
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                link=link,
                related_module=related_module,
                related_record_id=related_record_id,
                is_read=False
            )
            session.add(notification)
            session.commit()
            return notification
        except Exception as e:
            print(f"[NotificationService] create_notification error: {e}")
            return None

    @staticmethod
    def create_admin_notification(
        title: str,
        message: str,
        link: str = None,
        notification_type: str = "info"
    ) -> List[Notification]:
        """
        Tüm admin kullanıcılara bildirim gönder

        Args:
            title: Bildirim başlığı
            message: Bildirim mesajı
            link: Tıklandığında gidilecek sayfa
            notification_type: info, warning, error, success, action_required

        Returns:
            Oluşturulan Notification listesi
        """
        notifications = []
        try:
            session = get_session()

            # Admin kullanıcıları bul (is_admin=True veya role='admin')
            from database.models.user import User
            admins = session.query(User).filter(
                (User.is_active == True) &
                ((User.is_admin == True) | (User.role == 'admin'))
            ).all()

            for admin in admins:
                notification = Notification(
                    user_id=admin.id,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    link=link,
                    is_read=False
                )
                session.add(notification)
                notifications.append(notification)

            session.commit()
            return notifications

        except Exception as e:
            print(f"[NotificationService] create_admin_notification error: {e}")
            return notifications

    @staticmethod
    def get_unread(user_id: int, limit: int = 20) -> List[Notification]:
        """
        Kullanıcının okunmamış bildirimlerini getir

        Args:
            user_id: Kullanıcı ID
            limit: Maksimum bildirim sayısı

        Returns:
            Notification listesi (en yeniden eskiye)
        """
        try:
            session = get_session()
            return session.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_active == True
            ).order_by(
                Notification.created_at.desc()
            ).limit(limit).all()
        except Exception as e:
            print(f"[NotificationService] get_unread error: {e}")
            return []

    @staticmethod
    def get_all(user_id: int, limit: int = 50) -> List[Notification]:
        """
        Kullanıcının tüm bildirimlerini getir

        Args:
            user_id: Kullanıcı ID
            limit: Maksimum bildirim sayısı

        Returns:
            Notification listesi
        """
        try:
            session = get_session()
            return session.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_active == True
            ).order_by(
                Notification.created_at.desc()
            ).limit(limit).all()
        except Exception as e:
            print(f"[NotificationService] get_all error: {e}")
            return []

    @staticmethod
    def mark_as_read(notification_id: int) -> bool:
        """
        Bildirimi okundu olarak işaretle

        Args:
            notification_id: Bildirim ID

        Returns:
            Başarılı mı?
        """
        try:
            session = get_session()
            notification = session.query(Notification).get(notification_id)
            if notification:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            print(f"[NotificationService] mark_as_read error: {e}")
            return False

    @staticmethod
    def mark_all_as_read(user_id: int) -> int:
        """
        Kullanıcının tüm bildirimlerini okundu olarak işaretle

        Args:
            user_id: Kullanıcı ID

        Returns:
            İşaretlenen bildirim sayısı
        """
        try:
            session = get_session()
            now = datetime.utcnow()
            count = session.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            ).update({
                Notification.is_read: True,
                Notification.read_at: now
            })
            session.commit()
            return count
        except Exception as e:
            print(f"[NotificationService] mark_all_as_read error: {e}")
            return 0

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        """
        Kullanıcının okunmamış bildirim sayısını getir

        Args:
            user_id: Kullanıcı ID

        Returns:
            Okunmamış bildirim sayısı
        """
        try:
            session = get_session()
            return session.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_active == True
            ).count()
        except Exception as e:
            print(f"[NotificationService] get_unread_count error: {e}")
            return 0
