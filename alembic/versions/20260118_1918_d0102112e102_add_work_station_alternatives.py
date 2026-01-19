"""add_work_station_alternatives

Revision ID: d0102112e102
Revises: 98465361d552
Create Date: 2026-01-18 19:18:24.334994

Alternatif istasyon ilişki tablosu eklendi.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d0102112e102"
down_revision: Union[str, None] = "98465361d552"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alternatif istasyon tablosu oluştur
    op.create_table(
        "work_station_alternatives",
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("alt_station_id", sa.Integer(), nullable=False),
        sa.Column("priority", sa.Integer(), default=1),
        sa.Column("efficiency_factor", sa.Numeric(precision=5, scale=2), default=100),
        sa.ForeignKeyConstraint(["alt_station_id"], ["work_stations.id"]),
        sa.ForeignKeyConstraint(["station_id"], ["work_stations.id"]),
        sa.PrimaryKeyConstraint("station_id", "alt_station_id"),
    )


def downgrade() -> None:
    op.drop_table("work_station_alternatives")
