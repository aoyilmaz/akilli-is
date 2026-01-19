"""add_backflush_mode

Revision ID: 98465361d552
Revises: 200a54a3f431
Create Date: 2026-01-18 18:33:02.631455

Backflush mode alanı eklendi - malzeme düşüm zamanlaması için.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "98465361d552"
down_revision: Union[str, None] = "200a54a3f431"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # BackflushMode enum oluştur
    backflush_enum = sa.Enum("ON_START", "ON_COMPLETE", "MANUAL", name="backflushmode")
    backflush_enum.create(op.get_bind(), checkfirst=True)

    # work_orders tablosuna backflush_mode ekle
    with op.batch_alter_table("work_orders", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "backflush_mode",
                sa.Enum("ON_START", "ON_COMPLETE", "MANUAL", name="backflushmode"),
                nullable=True,
                server_default="ON_START",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("work_orders", schema=None) as batch_op:
        batch_op.drop_column("backflush_mode")

    # Enum'u sil
    op.execute("DROP TYPE IF EXISTS backflushmode")
