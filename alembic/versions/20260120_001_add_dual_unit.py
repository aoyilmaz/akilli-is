"""
Dual-Unit (İkincil Birim) Takibi için migration
StockMovement ve StockBalance tablolarına secondary_quantity ve secondary_unit_id alanları eklenir.

Tarih: 20260120
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "20260120_001_add_dual_unit"
down_revision = "0fccb7b94c4f"
branch_labels = None
depends_on = None


def upgrade():
    """Dual-Unit alanlarını ekle"""

    # StockBalance tablosuna ikincil birim alanları
    op.add_column(
        "stock_balances",
        sa.Column("secondary_quantity", sa.Numeric(18, 4), nullable=True),
    )
    op.add_column(
        "stock_balances",
        sa.Column(
            "secondary_unit_id", sa.Integer(), sa.ForeignKey("units.id"), nullable=True
        ),
    )

    # StockMovement tablosuna ikincil birim alanları
    op.add_column(
        "stock_movements",
        sa.Column("secondary_quantity", sa.Numeric(18, 4), nullable=True),
    )
    op.add_column(
        "stock_movements",
        sa.Column(
            "secondary_unit_id", sa.Integer(), sa.ForeignKey("units.id"), nullable=True
        ),
    )


def downgrade():
    """Dual-Unit alanlarını kaldır"""

    # StockMovement'tan kaldır
    op.drop_column("stock_movements", "secondary_unit_id")
    op.drop_column("stock_movements", "secondary_quantity")

    # StockBalance'tan kaldır
    op.drop_column("stock_balances", "secondary_unit_id")
    op.drop_column("stock_balances", "secondary_quantity")
