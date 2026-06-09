"""multi-tenant — app_user, workspace, workspace_member, workspace_invitation, audit_log

Revision ID: 0002_multitenant
Revises: 0001_initial
Create Date: 2026-06-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_multitenant"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_user",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("image_url", sa.String(1024)),
        sa.Column("provider", sa.String(32), nullable=False, server_default="google"),
        sa.Column("provider_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("email", name="uq_app_user_email"),
    )
    op.create_index("ix_app_user_provider_id", "app_user", ["provider", "provider_id"])

    op.create_table(
        "workspace",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("plan", sa.String(32), nullable=False, server_default="free"),
        sa.Column("seat_limit", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("sectores_interes", postgresql.JSONB()),
        sa.Column("onboarded_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_workspace_slug"),
    )
    op.create_index("ix_workspace_plan", "workspace", ["plan"])

    op.create_table(
        "workspace_member",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("workspace_id", sa.BigInteger(), sa.ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False, server_default="viewer"),
        sa.Column("invited_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("role IN ('owner', 'admin', 'viewer')", name="ck_member_role"),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_member_unique"),
    )
    op.create_index("ix_member_user", "workspace_member", ["user_id"])
    op.create_index("ix_member_workspace", "workspace_member", ["workspace_id"])

    op.create_table(
        "workspace_invitation",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("workspace_id", sa.BigInteger(), sa.ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("role", sa.String(16), nullable=False, server_default="viewer"),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_by_user_id", sa.BigInteger(), sa.ForeignKey("app_user.id", ondelete="SET NULL")),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('owner', 'admin', 'viewer')", name="ck_invite_role"),
        sa.UniqueConstraint("token", name="uq_invite_token"),
    )
    op.create_index("ix_invite_workspace_email", "workspace_invitation", ["workspace_id", "email"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("workspace_id", sa.BigInteger(), sa.ForeignKey("workspace.id", ondelete="CASCADE")),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("app_user.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource", sa.String(128)),
        sa.Column("params", postgresql.JSONB()),
        sa.Column("ip", sa.String(64)),
        sa.Column("user_agent", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_workspace_created", "audit_log", ["workspace_id", "created_at"])
    op.create_index("ix_audit_action", "audit_log", ["action"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("workspace_invitation")
    op.drop_table("workspace_member")
    op.drop_table("workspace")
    op.drop_table("app_user")
