"""Add user_sessions table for multi-device session management

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-01-16 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d4e5f6g7h8i9"
down_revision: Union[str, None] = "c3d4e5f6g7h8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_sessions table
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_token", sa.String(64), nullable=False),
        sa.Column("refresh_token", sa.String(64), nullable=True),
        sa.Column("device_name", sa.String(100), nullable=True),
        sa.Column("device_type", sa.String(20), nullable=True),
        sa.Column("os_info", sa.String(100), nullable=True),
        sa.Column("app_version", sa.String(20), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("last_activity", sa.DateTime(), nullable=True),
        sa.Column("is_revoked", sa.Boolean(), default=False, nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revoke_reason", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # Create indexes
    op.create_index("idx_session_user", "user_sessions", ["user_id"])
    op.create_index("idx_session_token", "user_sessions", ["session_token"], unique=True)
    op.create_index("idx_session_refresh", "user_sessions", ["refresh_token"], unique=True)
    op.create_index("idx_session_expires", "user_sessions", ["expires_at"])
    op.create_index("idx_session_active", "user_sessions", ["is_active", "is_revoked"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_session_active", table_name="user_sessions")
    op.drop_index("idx_session_expires", table_name="user_sessions")
    op.drop_index("idx_session_refresh", table_name="user_sessions")
    op.drop_index("idx_session_token", table_name="user_sessions")
    op.drop_index("idx_session_user", table_name="user_sessions")

    # Drop table
    op.drop_table("user_sessions")
