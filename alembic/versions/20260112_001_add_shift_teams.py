"""Add shift teams and rotation system

Revision ID: 20260112_001
Revises: 5e189441534b
Create Date: 2026-01-12 11:35:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260112_001_add_shift_teams"
down_revision = "5e189441534b"
branch_labels = None
depends_on = None


def upgrade():
    # Vardiya Ekipleri tablosu
    op.create_table(
        "shift_teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(10), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color", sa.String(7), server_default="#6366f1"),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_shift_team_code", "shift_teams", ["code"], unique=True)

    # Rotasyon Şablonları tablosu
    op.create_table(
        "rotation_patterns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cycle_days", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("shifts_per_day", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_rotation_pattern_code", "rotation_patterns", ["code"], unique=True
    )

    # Rotasyon Takvimi tablosu
    op.create_table(
        "rotation_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pattern_id", sa.Integer(), nullable=False),
        sa.Column("day_in_cycle", sa.Integer(), nullable=False),
        sa.Column("shift_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["pattern_id"], ["rotation_patterns.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["shift_id"], ["production_shifts.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["shift_teams.id"]),
    )
    op.create_index(
        "idx_rotation_pattern_day", "rotation_schedules", ["pattern_id", "day_in_cycle"]
    )
    op.create_index("idx_rotation_team", "rotation_schedules", ["team_id"])

    # Employee tablosuna shift_team_id ekle
    op.add_column("employees", sa.Column("shift_team_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_employee_shift_team", "employees", "shift_teams", ["shift_team_id"], ["id"]
    )


def downgrade():
    # Employee tablosundan shift_team_id sil
    op.drop_constraint("fk_employee_shift_team", "employees", type_="foreignkey")
    op.drop_column("employees", "shift_team_id")

    # Tabloları sil
    op.drop_table("rotation_schedules")
    op.drop_table("rotation_patterns")
    op.drop_table("shift_teams")
