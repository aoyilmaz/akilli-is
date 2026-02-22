"""
Akıllı İş - Mesajlaşma Modelleri
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from database.base import Base, BaseModel


# --- Enum Tanımları ---


class ConversationType(str, PyEnum):
    DIRECT = "direct"
    GROUP = "group"
    DEPARTMENT = "department"
    RECORD = "record"
    SYSTEM = "system"


class MessagePriority(str, PyEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# --- Modeller ---


class Conversation(BaseModel):
    """Konuşma / Sohbet odası"""

    __tablename__ = "conversations"

    title = Column(String(200), nullable=True)
    conversation_type = Column(
        String(20), default=ConversationType.DIRECT.value, nullable=False
    )

    # Departman kanalı için
    department_id = Column(
        Integer, ForeignKey("departments.id"), nullable=True
    )

    # Kayıt bağlantısı (polimorfik)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(Integer, nullable=True)

    # Oluşturan
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Denormalize alanlar (performans)
    last_message_at = Column(DateTime, nullable=True)
    last_message_preview = Column(String(200), nullable=True)

    # Ayarlar
    is_pinned = Column(Boolean, default=False)

    # İlişkiler
    creator = relationship("User", foreign_keys=[created_by])
    department = relationship("Department", foreign_keys=[department_id])
    participants = relationship(
        "ConversationParticipant",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_conv_type", "conversation_type"),
        Index("idx_conv_entity", "entity_type", "entity_id"),
        Index("idx_conv_dept", "department_id"),
        Index("idx_conv_last_msg", "last_message_at"),
        Index("idx_conv_created_by", "created_by"),
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, type={self.conversation_type})>"


class ConversationParticipant(BaseModel):
    """Konuşma katılımcısı"""

    __tablename__ = "conversation_participants"

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Rol
    role = Column(String(20), default="member")  # admin, member

    # Okunma takibi
    last_read_at = Column(DateTime, nullable=True)
    last_read_message_id = Column(Integer, nullable=True)
    unread_count = Column(Integer, default=0)

    # Tercihler
    is_muted = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)

    # Katılım
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)

    # İlişkiler
    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index(
            "idx_cp_conv_user",
            "conversation_id",
            "user_id",
            unique=True,
        ),
        Index("idx_cp_user_unread", "user_id", "unread_count"),
        Index("idx_cp_user_active", "user_id", "is_active"),
    )

    def __repr__(self):
        return f"<ConversationParticipant(conv={self.conversation_id}, user={self.user_id})>"


class Message(BaseModel):
    """Mesaj"""

    __tablename__ = "messages"

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # İçerik
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # text, system, file, record_link

    # Yanıt
    reply_to_id = Column(
        Integer, ForeignKey("messages.id"), nullable=True
    )

    # Öncelik
    priority = Column(
        String(10), default=MessagePriority.NORMAL.value
    )

    # Düzenleme
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime, nullable=True)

    # Silme (mesaj bazlı soft delete)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Sabitleme
    is_pinned = Column(Boolean, default=False)

    # İlişkiler
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    reply_to = relationship(
        "Message", remote_side="Message.id", backref="replies"
    )
    attachments = relationship(
        "MessageAttachment",
        back_populates="message",
        cascade="all, delete-orphan",
    )
    stars = relationship(
        "MessageStar",
        back_populates="message",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_msg_conv", "conversation_id"),
        Index("idx_msg_sender", "sender_id"),
        Index("idx_msg_created", "created_at"),
        Index("idx_msg_conv_created", "conversation_id", "created_at"),
        Index("idx_msg_reply", "reply_to_id"),
        Index("idx_msg_pinned", "conversation_id", "is_pinned"),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, conv={self.conversation_id})>"


class MessageAttachment(BaseModel):
    """Mesaj dosya eki"""

    __tablename__ = "message_attachments"

    message_id = Column(
        Integer,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )

    file_name = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_extension = Column(String(20), nullable=True)
    thumbnail_path = Column(String(500), nullable=True)

    # İlişkiler
    message = relationship("Message", back_populates="attachments")

    __table_args__ = (Index("idx_ma_message", "message_id"),)

    def __repr__(self):
        return f"<MessageAttachment(id={self.id}, file={self.original_name})>"


class MessageStar(BaseModel):
    """Mesaj yıldızlama"""

    __tablename__ = "message_stars"

    message_id = Column(
        Integer,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # İlişkiler
    message = relationship("Message", back_populates="stars")
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index(
            "idx_ms_user_message",
            "user_id",
            "message_id",
            unique=True,
        ),
    )

    def __repr__(self):
        return f"<MessageStar(message={self.message_id}, user={self.user_id})>"


class NotificationPreference(BaseModel):
    """Kullanıcı bildirim tercihleri"""

    __tablename__ = "notification_preferences"

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    event_type = Column(String(50), nullable=False)

    # Kanallar
    in_app = Column(Boolean, default=True)
    in_message = Column(Boolean, default=False)

    # Sessiz saatler
    quiet_start = Column(String(5), nullable=True)  # "22:00"
    quiet_end = Column(String(5), nullable=True)  # "08:00"

    # İlişkiler
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index(
            "idx_np_user_event",
            "user_id",
            "event_type",
            unique=True,
        ),
    )

    def __repr__(self):
        return f"<NotificationPreference(user={self.user_id}, event={self.event_type})>"
