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
    # Enums defined in HR models
    gender_enum = sa.Enum("MALE", "FEMALE", "OTHER", name="gender")
    employment_type_enum = sa.Enum(
        "FULL_TIME",
        "PART_TIME",
        "CONTRACT",
        "INTERN",
        "TEMPORARY",
        name="employmenttype",
    )

    # Create Tables if they don't exist (Missing HR migrations)

    # Departments
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("manager_id", sa.Integer(), nullable=True),
        sa.Column("level", sa.Integer(), server_default="0"),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["departments.id"]),
        # manager_id FK deferred to avoid circular dependency
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_dept_code", "departments", ["code"], unique=True)
    op.create_index("idx_dept_parent", "departments", ["parent_id"])

    # Positions
    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("min_salary", sa.Numeric(15, 2), nullable=True),
        sa.Column("max_salary", sa.Numeric(15, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_pos_code", "positions", ["code"], unique=True)

    # Employees
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_no", sa.String(20), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("mobile", sa.String(20), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("tc_no", sa.String(11), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("gender", gender_enum, nullable=True),
        sa.Column("marital_status", sa.String(20), nullable=True),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("position_id", sa.Integer(), nullable=True),
        sa.Column("manager_id", sa.Integer(), nullable=True),
        # shift_team_id added later in this migration
        sa.Column(
            "hire_date",
            sa.Date(),
            nullable=False,
            server_default=sa.text("CURRENT_DATE"),
        ),
        sa.Column("employment_type", employment_type_enum, server_default="FULL_TIME"),
        sa.Column("salary", sa.Numeric(15, 2), nullable=True),
        sa.Column("exit_date", sa.Date(), nullable=True),
        sa.Column("exit_reason", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("photo", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"]),
        sa.ForeignKeyConstraint(["manager_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_emp_no", "employees", ["employee_no"], unique=True)
    op.create_index("idx_emp_email", "employees", ["email"], unique=True)

    # Add deferred FK for department manager
    op.create_foreign_key(
        "fk_dept_manager", "departments", "employees", ["manager_id"], ["id"]
    )
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

    # Drop restored HR tables
    op.drop_index("idx_emp_email", table_name="employees")
    op.drop_index("idx_emp_no", table_name="employees")
    op.drop_table("employees")

    op.drop_index("idx_pos_code", table_name="positions")
    op.drop_table("positions")

    op.drop_index("idx_dept_parent", table_name="departments")
    op.drop_index("idx_dept_code", table_name="departments")
    op.drop_table("departments")

    # Drop enums
    sa.Enum(name="employmenttype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="gender").drop(op.get_bind(), checkfirst=True)
