"""Add messaging tables

Revision ID: add_messaging_tables
Revises: ac67fe11a27e
Create Date: 2026-02-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_messaging_tables'
down_revision = 'ac67fe11a27e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Conversations
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('conversation_type', sa.String(length=20), nullable=False, server_default='direct'),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.Column('last_message_preview', sa.String(length=200), nullable=True),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_conv_type', 'conversations', ['conversation_type'])
    op.create_index('idx_conv_entity', 'conversations', ['entity_type', 'entity_id'])
    op.create_index('idx_conv_dept', 'conversations', ['department_id'])
    op.create_index('idx_conv_last_msg', 'conversations', ['last_message_at'])
    op.create_index('idx_conv_created_by', 'conversations', ['created_by'])

    # Conversation Participants
    op.create_table(
        'conversation_participants',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='member'),
        sa.Column('last_read_at', sa.DateTime(), nullable=True),
        sa.Column('last_read_message_id', sa.Integer(), nullable=True),
        sa.Column('unread_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_muted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_cp_conv_user', 'conversation_participants', ['conversation_id', 'user_id'], unique=True)
    op.create_index('idx_cp_user_unread', 'conversation_participants', ['user_id', 'unread_count'])
    op.create_index('idx_cp_user_active', 'conversation_participants', ['user_id', 'is_active'])

    # Messages
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=20), nullable=False, server_default='text'),
        sa.Column('reply_to_id', sa.Integer(), nullable=True),
        sa.Column('priority', sa.String(length=10), nullable=False, server_default='normal'),
        sa.Column('is_edited', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('edited_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id']),
        sa.ForeignKeyConstraint(['reply_to_id'], ['messages.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_msg_conv', 'messages', ['conversation_id'])
    op.create_index('idx_msg_sender', 'messages', ['sender_id'])
    op.create_index('idx_msg_created', 'messages', ['created_at'])
    op.create_index('idx_msg_conv_created', 'messages', ['conversation_id', 'created_at'])
    op.create_index('idx_msg_reply', 'messages', ['reply_to_id'])
    op.create_index('idx_msg_pinned', 'messages', ['conversation_id', 'is_pinned'])

    # Message Attachments
    op.create_table(
        'message_attachments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('original_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('file_extension', sa.String(length=20), nullable=True),
        sa.Column('thumbnail_path', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_ma_message', 'message_attachments', ['message_id'])

    # Message Stars
    op.create_table(
        'message_stars',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_ms_user_message', 'message_stars', ['user_id', 'message_id'], unique=True)

    # Notification Preferences
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('in_app', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('in_message', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('quiet_start', sa.String(length=5), nullable=True),
        sa.Column('quiet_end', sa.String(length=5), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_np_user_event', 'notification_preferences', ['user_id', 'event_type'], unique=True)


def downgrade() -> None:
    op.drop_table('notification_preferences')
    op.drop_table('message_stars')
    op.drop_table('message_attachments')
    op.drop_table('messages')
    op.drop_table('conversation_participants')
    op.drop_table('conversations')
