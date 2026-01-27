"""Add workflow engine tables

Revision ID: 20260126_workflow
Revises: 1d12a4ad122d
Create Date: 2026-01-26

Workflow Engine için 4 tablo:
- workflow_definitions: İş akışı tanımları
- workflow_steps: Akış adımları
- workflow_instances: Başlatılmış akış örnekleri
- workflow_actions: Onay/red aksiyonları
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260126_workflow"
down_revision = "1d12a4ad122d"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Enum tipleri oluştur (raw SQL ile)
    op.execute(
        "CREATE TYPE workflowstatus AS ENUM "
        "('pending', 'approved', 'rejected', 'cancelled')"
    )
    op.execute(
        "CREATE TYPE workflowactiontype AS ENUM "
        "('approve', 'reject', 'delegate', 'request_info')"
    )

    # 2. workflow_definitions tablosu
    op.create_table(
        "workflow_definitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_table", sa.String(100), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default="false"),
        sa.Column("priority", sa.Integer(), server_default="0"),
        sa.Column("activation_condition", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_wf_def_code", "workflow_definitions", ["code"], unique=True
    )
    op.create_index(
        "idx_wf_def_table", "workflow_definitions", ["target_table"]
    )
    op.create_index(
        "idx_wf_def_active", "workflow_definitions", ["is_active", "target_table"]
    )

    # 3. workflow_steps tablosu
    op.create_table(
        "workflow_steps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workflow_id", sa.Integer(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("required_role_id", sa.Integer(), nullable=True),
        sa.Column("required_permission_code", sa.String(100), nullable=True),
        sa.Column("approver_user_id", sa.Integer(), nullable=True),
        sa.Column("dynamic_approver_field", sa.String(200), nullable=True),
        sa.Column("condition_script", sa.Text(), nullable=True),
        sa.Column("timeout_hours", sa.Integer(), nullable=True),
        sa.Column("timeout_action", sa.String(50), server_default="escalate"),
        sa.Column("is_final_step", sa.Boolean(), server_default="false"),
        sa.Column("is_parallel", sa.Boolean(), server_default="false"),
        sa.Column("requires_all", sa.Boolean(), server_default="true"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["workflow_id"], ["workflow_definitions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["required_role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["approver_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_wf_step_workflow", "workflow_steps", ["workflow_id", "step_order"]
    )

    # 4. workflow_instances tablosu
    # PostgreSQL ENUM tipini doğrudan referans al
    workflowstatus = postgresql.ENUM(
        "pending", "approved", "rejected", "cancelled",
        name="workflowstatus", create_type=False
    )

    op.create_table(
        "workflow_instances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workflow_id", sa.Integer(), nullable=False),
        sa.Column("document_table", sa.String(100), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("document_no", sa.String(100), nullable=True),
        sa.Column("current_step_id", sa.Integer(), nullable=True),
        sa.Column("status", workflowstatus, server_default="pending"),
        sa.Column("initiated_by", sa.Integer(), nullable=False),
        sa.Column("initiated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("final_comment", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflow_definitions.id"]),
        sa.ForeignKeyConstraint(["current_step_id"], ["workflow_steps.id"]),
        sa.ForeignKeyConstraint(["initiated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_wf_inst_doc", "workflow_instances", ["document_table", "document_id"]
    )
    op.create_index("idx_wf_inst_status", "workflow_instances", ["status"])

    # 5. workflow_actions tablosu
    workflowactiontype = postgresql.ENUM(
        "approve", "reject", "delegate", "request_info",
        name="workflowactiontype", create_type=False
    )

    op.create_table(
        "workflow_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("step_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", workflowactiontype, nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("delegated_to", sa.Integer(), nullable=True),
        sa.Column("delegation_reason", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["instance_id"], ["workflow_instances.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["step_id"], ["workflow_steps.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["delegated_to"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_wf_action_instance", "workflow_actions", ["instance_id"])
    op.create_index("idx_wf_action_user", "workflow_actions", ["user_id"])


def downgrade():
    # Tabloları ters sırayla sil
    op.drop_table("workflow_actions")
    op.drop_table("workflow_instances")
    op.drop_table("workflow_steps")
    op.drop_table("workflow_definitions")

    # Enum tiplerini sil
    op.execute("DROP TYPE IF EXISTS workflowactiontype")
    op.execute("DROP TYPE IF EXISTS workflowstatus")
