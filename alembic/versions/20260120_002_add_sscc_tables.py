"""
SSCC (Transport Unit) Migration
TransportUnit ve TransportUnitItem tabloları oluşturulur.

Tarih: 20260120
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers
revision = "20260120_002_add_sscc_tables"
down_revision = "20260120_001_add_dual_unit"
branch_labels = None
depends_on = None


def upgrade():
    """SSCC tablolarını oluştur"""

    # TransportUnit tablosu
    op.create_table(
        "transport_units",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sscc", sa.String(length=20), nullable=False),
        sa.Column("barcode", sa.String(length=50), nullable=True),
        sa.Column(
            "unit_type",
            sa.Enum(
                "PALET",
                "KONTEYNER",
                "KOLI",
                "KASA",
                "SANDIK",
                "DIGER",
                name="transportunittype",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "ACIK",
                "KAPALI",
                "SEVK_EDILDI",
                "TESLIM_ALINDI",
                "IPTAL",
                name="transportunitstatus",
            ),
            nullable=False,
        ),
        sa.Column("warehouse_id", sa.Integer(), nullable=True),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.Column("length_cm", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("width_cm", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("height_cm", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("gross_weight_kg", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("net_weight_kg", sa.Numeric(precision=12, scale=3), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=False),
        sa.Column("closed_date", sa.DateTime(), nullable=True),
        sa.Column("shipped_date", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        # BaseModel columns
        sa.Column("created_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["warehouse_locations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["warehouse_id"],
            ["warehouses.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexler
    op.create_index("ix_transport_units_sscc", "transport_units", ["sscc"], unique=True)
    op.create_index("idx_tu_status", "transport_units", ["status"], unique=False)
    op.create_index(
        "idx_tu_warehouse", "transport_units", ["warehouse_id"], unique=False
    )
    op.create_index("idx_tu_created", "transport_units", ["created_date"], unique=False)

    # TransportUnitItem tablosu
    op.create_table(
        "transport_unit_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transport_unit_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column(
            "secondary_quantity", sa.Numeric(precision=18, scale=4), nullable=True
        ),
        sa.Column("secondary_unit_id", sa.Integer(), nullable=True),
        sa.Column("lot_number", sa.String(length=100), nullable=True),
        sa.Column("serial_number", sa.String(length=100), nullable=True),
        sa.Column("expiry_date", sa.DateTime(), nullable=True),
        sa.Column("added_date", sa.DateTime(), nullable=False),
        sa.Column("added_by", sa.Integer(), nullable=True),
        # BaseModel columns
        sa.Column("created_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(
            ["added_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["item_id"],
            ["items.id"],
        ),
        sa.ForeignKeyConstraint(
            ["secondary_unit_id"],
            ["units.id"],
        ),
        sa.ForeignKeyConstraint(
            ["transport_unit_id"], ["transport_units.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["unit_id"],
            ["units.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexler for items
    op.create_index(
        "idx_tui_transport", "transport_unit_items", ["transport_unit_id"], unique=False
    )
    op.create_index("idx_tui_item", "transport_unit_items", ["item_id"], unique=False)
    op.create_index("idx_tui_lot", "transport_unit_items", ["lot_number"], unique=False)


def downgrade():
    """SSCC tablolarını kaldır"""
    op.drop_table("transport_unit_items")
    op.drop_table("transport_units")

    # Enum tiplerini de temizlemek gerekebilir (PostgreSQL için otomatik kalkmayabilir ama dev ortamında şimdilik kalsın)
