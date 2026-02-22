"""
Akıllı İş - Mesajlaşma Servis Katmanı
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, and_, or_

from database.models.messaging import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageAttachment,
    MessageStar,
    NotificationPreference,
    ConversationType,
    MessagePriority,
)
from database.models.user import User
from database.models.hr import Department, Employee


class MessagingService:
    def __init__(self, session: Session):
        self.session = session

    # ============================================================
    # KONUŞMA YÖNETİMİ
    # ============================================================

    def create_direct_conversation(
        self, user_id_1: int, user_id_2: int
    ) -> Conversation:
        """
        İki kullanıcı arasında direkt konuşma oluşturur.
        Zaten varsa mevcut olanı döndürür (idempotent).
        """
        existing = self._find_direct_conversation(user_id_1, user_id_2)
        if existing:
            return existing

        conversation = Conversation(
            conversation_type=ConversationType.DIRECT.value,
            created_by=user_id_1,
        )
        self.session.add(conversation)
        self.session.flush()

        # İki katılımcı ekle
        for uid, role in [(user_id_1, "admin"), (user_id_2, "member")]:
            participant = ConversationParticipant(
                conversation_id=conversation.id,
                user_id=uid,
                role=role,
            )
            self.session.add(participant)

        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def create_group_conversation(
        self,
        title: str,
        creator_id: int,
        participant_ids: List[int],
    ) -> Conversation:
        """Grup konuşması oluşturur."""
        conversation = Conversation(
            title=title,
            conversation_type=ConversationType.GROUP.value,
            created_by=creator_id,
        )
        self.session.add(conversation)
        self.session.flush()

        # Oluşturan admin olarak eklenir
        all_ids = set(participant_ids) | {creator_id}
        for uid in all_ids:
            participant = ConversationParticipant(
                conversation_id=conversation.id,
                user_id=uid,
                role="admin" if uid == creator_id else "member",
            )
            self.session.add(participant)

        # Sistem mesajı
        self._send_system_message(
            conversation.id, f"Grup oluşturuldu: {title}"
        )

        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def create_department_conversation(
        self, department_id: int, creator_id: int
    ) -> Conversation:
        """
        Departman kanalı oluşturur.
        Zaten varsa mevcut olanı döndürür.
        """
        existing = (
            self.session.query(Conversation)
            .filter(
                Conversation.conversation_type == ConversationType.DEPARTMENT.value,
                Conversation.department_id == department_id,
                Conversation.is_active == True,
            )
            .first()
        )
        if existing:
            return existing

        department = self.session.query(Department).get(department_id)
        if not department:
            raise ValueError(f"Departman bulunamadı: {department_id}")

        conversation = Conversation(
            title=f"{department.name} Kanalı",
            conversation_type=ConversationType.DEPARTMENT.value,
            department_id=department_id,
            created_by=creator_id,
        )
        self.session.add(conversation)
        self.session.flush()

        # Departmandaki tüm aktif çalışanları ekle
        employees = (
            self.session.query(Employee)
            .filter(
                Employee.department_id == department_id,
                Employee.is_active == True,
                Employee.user_id.isnot(None),
            )
            .all()
        )

        for emp in employees:
            participant = ConversationParticipant(
                conversation_id=conversation.id,
                user_id=emp.user_id,
                role="admin" if emp.user_id == creator_id else "member",
            )
            self.session.add(participant)

        self._send_system_message(
            conversation.id, f"Departman kanalı oluşturuldu: {department.name}"
        )

        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def create_record_conversation(
        self,
        entity_type: str,
        entity_id: int,
        creator_id: int,
        participant_ids: Optional[List[int]] = None,
    ) -> Conversation:
        """
        ERP kaydına bağlı konuşma oluşturur.
        Zaten varsa mevcut olanı döndürür.
        """
        existing = self.get_record_conversation(entity_type, entity_id)
        if existing:
            return existing

        conversation = Conversation(
            title=f"{entity_type} #{entity_id}",
            conversation_type=ConversationType.RECORD.value,
            entity_type=entity_type,
            entity_id=entity_id,
            created_by=creator_id,
        )
        self.session.add(conversation)
        self.session.flush()

        all_ids = set(participant_ids or []) | {creator_id}
        for uid in all_ids:
            participant = ConversationParticipant(
                conversation_id=conversation.id,
                user_id=uid,
                role="admin" if uid == creator_id else "member",
            )
            self.session.add(participant)

        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def get_record_conversation(
        self, entity_type: str, entity_id: int
    ) -> Optional[Conversation]:
        """Kayda bağlı konuşmayı bulur."""
        return (
            self.session.query(Conversation)
            .filter(
                Conversation.conversation_type == ConversationType.RECORD.value,
                Conversation.entity_type == entity_type,
                Conversation.entity_id == entity_id,
                Conversation.is_active == True,
            )
            .first()
        )

    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """Konuşmayı katılımcılarıyla birlikte getirir."""
        return (
            self.session.query(Conversation)
            .options(joinedload(Conversation.participants))
            .filter(Conversation.id == conversation_id)
            .first()
        )

    def get_user_conversations(
        self,
        user_id: int,
        conversation_type: Optional[str] = None,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Kullanıcının konuşmalarını listeler.
        Denormalize alanlar sayesinde hızlı sıralama yapar.
        """
        query = (
            self.session.query(Conversation, ConversationParticipant)
            .join(
                ConversationParticipant,
                ConversationParticipant.conversation_id == Conversation.id,
            )
            .filter(
                ConversationParticipant.user_id == user_id,
                ConversationParticipant.is_active == True,
                Conversation.is_active == True,
            )
        )

        if conversation_type:
            query = query.filter(
                Conversation.conversation_type == conversation_type
            )

        query = query.order_by(desc(Conversation.last_message_at))
        results = query.offset(offset).limit(limit).all()

        conversations = []
        for conv, participant in results:
            # Direkt mesajlarda karşı tarafın ismini al
            display_title = conv.title
            other_user = None

            if conv.conversation_type == ConversationType.DIRECT.value:
                other_participant = (
                    self.session.query(ConversationParticipant)
                    .filter(
                        ConversationParticipant.conversation_id == conv.id,
                        ConversationParticipant.user_id != user_id,
                        ConversationParticipant.is_active == True,
                    )
                    .first()
                )
                if other_participant:
                    other_user = self.session.query(User).get(
                        other_participant.user_id
                    )
                    if other_user:
                        display_title = (
                            f"{other_user.first_name} {other_user.last_name}".strip()
                            or other_user.username
                        )

            conversations.append(
                {
                    "id": conv.id,
                    "title": display_title,
                    "conversation_type": conv.conversation_type,
                    "last_message_at": conv.last_message_at,
                    "last_message_preview": conv.last_message_preview,
                    "unread_count": participant.unread_count,
                    "is_muted": participant.is_muted,
                    "is_pinned": participant.is_pinned,
                    "other_user_id": other_user.id if other_user else None,
                    "other_user_avatar": getattr(other_user, "avatar", None),
                    "department_id": conv.department_id,
                    "entity_type": conv.entity_type,
                    "entity_id": conv.entity_id,
                }
            )

        return conversations

    # ============================================================
    # MESAJ İŞLEMLERİ
    # ============================================================

    def send_message(
        self,
        conversation_id: int,
        sender_id: int,
        content: str,
        message_type: str = "text",
        reply_to_id: Optional[int] = None,
        priority: str = "normal",
    ) -> Message:
        """
        Mesaj gönderir.
        Yan etkiler:
        1. Conversation.last_message_at ve last_message_preview güncellenir
        2. Gönderici hariç tüm katılımcıların unread_count'ı artırılır
        """
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            reply_to_id=reply_to_id,
            priority=priority,
        )
        self.session.add(message)
        self.session.flush()

        # Conversation güncelle
        now = datetime.utcnow()
        preview = content[:200] if content else ""
        self.session.query(Conversation).filter(
            Conversation.id == conversation_id
        ).update(
            {
                "last_message_at": now,
                "last_message_preview": preview,
                "updated_at": now,
            }
        )

        # Okunmamış sayacı artır (gönderici hariç)
        self.session.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id != sender_id,
            ConversationParticipant.is_active == True,
        ).update(
            {"unread_count": ConversationParticipant.unread_count + 1},
            synchronize_session="fetch",
        )

        self.session.commit()
        self.session.refresh(message)
        return message

    def get_messages(
        self,
        conversation_id: int,
        limit: int = 50,
        before_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Konuşmadaki mesajları getirir (cursor-based pagination).
        Eski → yeni sıralı döner.
        """
        query = (
            self.session.query(Message)
            .options(joinedload(Message.sender))
            .filter(
                Message.conversation_id == conversation_id,
                Message.is_active == True,
                Message.is_deleted == False,
            )
        )

        if before_id:
            query = query.filter(Message.id < before_id)

        messages = (
            query.order_by(desc(Message.id)).limit(limit).all()
        )
        messages.reverse()  # Eski → yeni

        result = []
        for msg in messages:
            sender = msg.sender
            result.append(
                {
                    "id": msg.id,
                    "conversation_id": msg.conversation_id,
                    "sender_id": msg.sender_id,
                    "sender_name": (
                        f"{sender.first_name} {sender.last_name}".strip()
                        if sender
                        else "Sistem"
                    ),
                    "sender_avatar": getattr(sender, "avatar", None),
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "reply_to_id": msg.reply_to_id,
                    "priority": msg.priority,
                    "is_edited": msg.is_edited,
                    "is_pinned": msg.is_pinned,
                    "created_at": msg.created_at,
                }
            )

        return result

    def get_new_messages(
        self, conversation_id: int, after_id: int
    ) -> List[Dict[str, Any]]:
        """Son bilinen mesajdan sonraki yeni mesajları getirir (polling)."""
        messages = (
            self.session.query(Message)
            .options(joinedload(Message.sender))
            .filter(
                Message.conversation_id == conversation_id,
                Message.id > after_id,
                Message.is_active == True,
                Message.is_deleted == False,
            )
            .order_by(Message.id)
            .all()
        )

        result = []
        for msg in messages:
            sender = msg.sender
            result.append(
                {
                    "id": msg.id,
                    "conversation_id": msg.conversation_id,
                    "sender_id": msg.sender_id,
                    "sender_name": (
                        f"{sender.first_name} {sender.last_name}".strip()
                        if sender
                        else "Sistem"
                    ),
                    "sender_avatar": getattr(sender, "avatar", None),
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "reply_to_id": msg.reply_to_id,
                    "priority": msg.priority,
                    "is_edited": msg.is_edited,
                    "is_pinned": msg.is_pinned,
                    "created_at": msg.created_at,
                }
            )

        return result

    def edit_message(
        self, message_id: int, user_id: int, new_content: str
    ) -> Optional[Message]:
        """Kendi mesajını düzenler."""
        message = (
            self.session.query(Message)
            .filter(
                Message.id == message_id,
                Message.sender_id == user_id,
                Message.is_deleted == False,
            )
            .first()
        )
        if not message:
            return None

        message.content = new_content
        message.is_edited = True
        message.edited_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(message)
        return message

    def delete_message(
        self, message_id: int, user_id: int, is_admin: bool = False
    ) -> bool:
        """Mesajı soft-delete yapar. Admin herkesin mesajını silebilir."""
        query = self.session.query(Message).filter(Message.id == message_id)

        if not is_admin:
            query = query.filter(Message.sender_id == user_id)

        message = query.first()
        if not message:
            return False

        message.is_deleted = True
        message.deleted_at = datetime.utcnow()
        self.session.commit()
        return True

    def pin_message(self, message_id: int) -> bool:
        """Mesajı sabitler/kaldırır."""
        message = self.session.query(Message).get(message_id)
        if not message:
            return False

        message.is_pinned = not message.is_pinned
        self.session.commit()
        return True

    def search_messages(
        self,
        user_id: int,
        query_text: str,
        conversation_id: Optional[int] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Mesajlarda arama yapar."""
        search_term = f"%{query_text}%"

        # Kullanıcının katılımcı olduğu konuşmalar
        user_conv_ids = (
            self.session.query(ConversationParticipant.conversation_id)
            .filter(
                ConversationParticipant.user_id == user_id,
                ConversationParticipant.is_active == True,
            )
            .subquery()
        )

        query = (
            self.session.query(Message)
            .options(joinedload(Message.sender))
            .filter(
                Message.conversation_id.in_(user_conv_ids),
                Message.content.ilike(search_term),
                Message.is_deleted == False,
                Message.is_active == True,
            )
        )

        if conversation_id:
            query = query.filter(Message.conversation_id == conversation_id)

        messages = query.order_by(desc(Message.created_at)).limit(limit).all()

        return [
            {
                "id": msg.id,
                "conversation_id": msg.conversation_id,
                "sender_name": (
                    f"{msg.sender.first_name} {msg.sender.last_name}".strip()
                    if msg.sender
                    else "Sistem"
                ),
                "content": msg.content,
                "created_at": msg.created_at,
            }
            for msg in messages
        ]

    # ============================================================
    # OKUNMA DURUMU
    # ============================================================

    def mark_conversation_read(
        self, conversation_id: int, user_id: int
    ) -> int:
        """
        Konuşmayı okundu olarak işaretler.
        Önceki okunmamış sayısını döndürür.
        """
        participant = (
            self.session.query(ConversationParticipant)
            .filter(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
            )
            .first()
        )

        if not participant:
            return 0

        previous_count = participant.unread_count
        participant.unread_count = 0
        participant.last_read_at = datetime.utcnow()

        # Son mesaj ID'sini kaydet
        last_msg = (
            self.session.query(Message.id)
            .filter(Message.conversation_id == conversation_id)
            .order_by(desc(Message.id))
            .first()
        )
        if last_msg:
            participant.last_read_message_id = last_msg[0]

        self.session.commit()
        return previous_count

    def get_total_unread_count(self, user_id: int) -> int:
        """
        Toplam okunmamış mesaj sayısını döndürür.
        Status bar badge için optimize edilmiş tek sorgu.
        """
        result = (
            self.session.query(
                func.coalesce(
                    func.sum(ConversationParticipant.unread_count), 0
                )
            )
            .filter(
                ConversationParticipant.user_id == user_id,
                ConversationParticipant.is_active == True,
                ConversationParticipant.is_muted == False,
            )
            .scalar()
        )
        return int(result)

    # ============================================================
    # KATILIMCI YÖNETİMİ
    # ============================================================

    def add_participants(
        self,
        conversation_id: int,
        user_ids: List[int],
        added_by: int,
    ) -> List[ConversationParticipant]:
        """Konuşmaya katılımcı ekler."""
        added = []
        for uid in user_ids:
            # Zaten varsa atla
            existing = (
                self.session.query(ConversationParticipant)
                .filter(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == uid,
                )
                .first()
            )
            if existing:
                if not existing.is_active:
                    existing.is_active = True
                    existing.left_at = None
                    added.append(existing)
                continue

            participant = ConversationParticipant(
                conversation_id=conversation_id,
                user_id=uid,
                role="member",
            )
            self.session.add(participant)
            added.append(participant)

        if added:
            user = self.session.query(User).get(added_by)
            adder_name = (
                f"{user.first_name} {user.last_name}".strip()
                if user
                else "Bilinmeyen"
            )
            user_names = []
            for p in added:
                u = self.session.query(User).get(p.user_id)
                if u:
                    user_names.append(
                        f"{u.first_name} {u.last_name}".strip() or u.username
                    )
            names_str = ", ".join(user_names)
            self._send_system_message(
                conversation_id,
                f"{adder_name}, {names_str} kişisini gruba ekledi",
            )
            self.session.commit()

        return added

    def remove_participant(
        self, conversation_id: int, user_id: int, removed_by: int
    ) -> bool:
        """Konuşmadan katılımcı çıkarır."""
        participant = (
            self.session.query(ConversationParticipant)
            .filter(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
                ConversationParticipant.is_active == True,
            )
            .first()
        )
        if not participant:
            return False

        participant.is_active = False
        participant.left_at = datetime.utcnow()

        user = self.session.query(User).get(user_id)
        user_name = (
            f"{user.first_name} {user.last_name}".strip()
            if user
            else "Bilinmeyen"
        )

        if user_id == removed_by:
            self._send_system_message(
                conversation_id, f"{user_name} gruptan ayrıldı"
            )
        else:
            remover = self.session.query(User).get(removed_by)
            remover_name = (
                f"{remover.first_name} {remover.last_name}".strip()
                if remover
                else "Bilinmeyen"
            )
            self._send_system_message(
                conversation_id,
                f"{remover_name}, {user_name} kişisini gruptan çıkardı",
            )

        self.session.commit()
        return True

    def get_conversation_participants(
        self, conversation_id: int
    ) -> List[Dict[str, Any]]:
        """Konuşma katılımcılarını döndürür."""
        participants = (
            self.session.query(ConversationParticipant, User)
            .join(User, User.id == ConversationParticipant.user_id)
            .filter(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.is_active == True,
            )
            .all()
        )

        return [
            {
                "user_id": user.id,
                "username": user.username,
                "full_name": f"{user.first_name} {user.last_name}".strip(),
                "avatar": getattr(user, "avatar", None),
                "role": p.role,
                "joined_at": p.joined_at,
            }
            for p, user in participants
        ]

    # ============================================================
    # YILDIZLAMA
    # ============================================================

    def toggle_star(self, message_id: int, user_id: int) -> bool:
        """Mesajı yıldızlar/kaldırır. True ise yıldızlandı."""
        existing = (
            self.session.query(MessageStar)
            .filter(
                MessageStar.message_id == message_id,
                MessageStar.user_id == user_id,
            )
            .first()
        )

        if existing:
            self.session.delete(existing)
            self.session.commit()
            return False
        else:
            star = MessageStar(message_id=message_id, user_id=user_id)
            self.session.add(star)
            self.session.commit()
            return True

    def get_starred_messages(
        self, user_id: int, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Yıldızlı mesajları döndürür."""
        stars = (
            self.session.query(MessageStar, Message)
            .join(Message, Message.id == MessageStar.message_id)
            .options(joinedload(Message.sender))
            .filter(
                MessageStar.user_id == user_id,
                Message.is_deleted == False,
            )
            .order_by(desc(MessageStar.created_at))
            .limit(limit)
            .all()
        )

        return [
            {
                "id": msg.id,
                "conversation_id": msg.conversation_id,
                "content": msg.content,
                "sender_name": (
                    f"{msg.sender.first_name} {msg.sender.last_name}".strip()
                    if msg.sender
                    else "Sistem"
                ),
                "created_at": msg.created_at,
                "starred_at": star.created_at,
            }
            for star, msg in stars
        ]

    # ============================================================
    # SİSTEM BİLDİRİMLERİ
    # ============================================================

    def send_system_notification(
        self,
        user_id: int,
        title: str,
        content: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        priority: str = "normal",
    ) -> Message:
        """Sistem bildirimi mesajı gönderir."""
        # Kullanıcının sistem konuşmasını bul veya oluştur
        conv = (
            self.session.query(Conversation)
            .join(
                ConversationParticipant,
                ConversationParticipant.conversation_id == Conversation.id,
            )
            .filter(
                Conversation.conversation_type == ConversationType.SYSTEM.value,
                ConversationParticipant.user_id == user_id,
                Conversation.is_active == True,
            )
            .first()
        )

        if not conv:
            conv = Conversation(
                title="Sistem Bildirimleri",
                conversation_type=ConversationType.SYSTEM.value,
                created_by=user_id,
            )
            self.session.add(conv)
            self.session.flush()

            participant = ConversationParticipant(
                conversation_id=conv.id,
                user_id=user_id,
                role="member",
            )
            self.session.add(participant)

        full_content = f"**{title}**\n{content}"
        return self.send_message(
            conversation_id=conv.id,
            sender_id=user_id,
            content=full_content,
            message_type="system",
            priority=priority,
        )

    # ============================================================
    # YARDIMCI METODLAR
    # ============================================================

    def get_available_users(
        self, exclude_user_id: int, search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Mesaj gönderilebilecek aktif kullanıcıları listeler."""
        query = self.session.query(User).filter(
            User.is_active == True,
            User.id != exclude_user_id,
        )

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.email.ilike(search_term),
                )
            )

        users = query.order_by(User.first_name, User.last_name).all()

        return [
            {
                "id": u.id,
                "username": u.username,
                "full_name": f"{u.first_name} {u.last_name}".strip() or u.username,
                "email": u.email,
                "avatar": getattr(u, "avatar", None),
            }
            for u in users
        ]

    def get_departments_for_messaging(self) -> List[Dict[str, Any]]:
        """Mesajlaşma kanalı oluşturulabilecek departmanları listeler."""
        departments = (
            self.session.query(Department)
            .filter(Department.is_active == True)
            .order_by(Department.name)
            .all()
        )

        return [
            {
                "id": d.id,
                "name": d.name,
                "code": getattr(d, "code", None),
            }
            for d in departments
        ]

    def _find_direct_conversation(
        self, user_id_1: int, user_id_2: int
    ) -> Optional[Conversation]:
        """İki kullanıcı arasında mevcut direkt konuşmayı bulur."""
        conv_ids_1 = (
            self.session.query(ConversationParticipant.conversation_id)
            .filter(
                ConversationParticipant.user_id == user_id_1,
                ConversationParticipant.is_active == True,
            )
        )
        conv_ids_2 = (
            self.session.query(ConversationParticipant.conversation_id)
            .filter(
                ConversationParticipant.user_id == user_id_2,
                ConversationParticipant.is_active == True,
            )
        )

        return (
            self.session.query(Conversation)
            .filter(
                Conversation.conversation_type == ConversationType.DIRECT.value,
                Conversation.id.in_(conv_ids_1),
                Conversation.id.in_(conv_ids_2),
                Conversation.is_active == True,
            )
            .first()
        )

    def _send_system_message(
        self, conversation_id: int, content: str
    ) -> None:
        """Dahili sistem mesajı oluşturur (commit yapmaz)."""
        message = Message(
            conversation_id=conversation_id,
            sender_id=1,  # Sistem kullanıcısı
            content=content,
            message_type="system",
        )
        self.session.add(message)

        now = datetime.utcnow()
        self.session.query(Conversation).filter(
            Conversation.id == conversation_id
        ).update(
            {
                "last_message_at": now,
                "last_message_preview": content[:200],
            }
        )
