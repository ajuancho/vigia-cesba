"""alertas — alerta + alerta_match

Revision ID: 0003_alertas
Revises: 0002_multitenant
Create Date: 2026-06-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_alertas"
down_revision: Union[str, None] = "0002_multitenant"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "alerta",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("workspace_id", sa.BigInteger(), sa.ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("app_user.id", ondelete="SET NULL")),
        sa.Column("keyword", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(64)),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_match_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_alerta_workspace", "alerta", ["workspace_id"])
    op.create_index("ix_alerta_activa", "alerta", ["activa"])

    op.create_table(
        "alerta_match",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("alerta_id", sa.BigInteger(), sa.ForeignKey("alerta.id", ondelete="CASCADE"), nullable=False),
        sa.Column("norma_id", sa.BigInteger(), sa.ForeignKey("norma.id", ondelete="CASCADE"), nullable=False),
        sa.Column("notified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("matched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("alerta_id", "norma_id", name="uq_match_alerta_norma"),
    )
    op.create_index("ix_match_alerta", "alerta_match", ["alerta_id"])
    op.create_index("ix_match_notified", "alerta_match", ["notified"])


def downgrade() -> None:
    op.drop_table("alerta_match")
    op.drop_table("alerta")
