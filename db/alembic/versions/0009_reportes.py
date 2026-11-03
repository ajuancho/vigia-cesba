"""reporte — reportes guardados por workspace + índice por sección del boletín

Revision ID: 0009_reportes
Revises: 0008_bocba
Create Date: 2026-11-03

`reporte` guarda la configuración del constructor de reportes (filtros,
formato, orden) por workspace; los resultados se recalculan al abrirlo.

El índice en `norma.bora_seccion` acelera los reportes, que casi siempre
acotan por sección del boletín (p.ej. "Licitaciones").
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0009_reportes"
down_revision: Union[str, None] = "0008_bocba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reporte",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.BigInteger(),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("app_user.id", ondelete="SET NULL")),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("config", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reporte_workspace", "reporte", ["workspace_id"])
    op.create_index("ix_norma_bora_seccion", "norma", ["bora_seccion"])


def downgrade() -> None:
    op.drop_index("ix_norma_bora_seccion", table_name="norma")
    op.drop_index("ix_reporte_workspace", table_name="reporte")
    op.drop_table("reporte")
