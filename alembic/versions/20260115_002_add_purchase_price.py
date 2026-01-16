"""Add purchase_price to equipments

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-15 10:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6g7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('equipments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('purchase_price', sa.Numeric(precision=18, scale=2), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('equipments', schema=None) as batch_op:
        batch_op.drop_column('purchase_price')
