"""alerta — keywords/sectores como listas + anchor_at temporal

Revision ID: 0006_alerta_multi
Revises: 0005_aviso_societario
Create Date: 2026-06-14

Migra `alerta` de un solo keyword/sector escalar a listas JSONB (OR entre sí) y
agrega `anchor_at`: el piso temporal que evita que una alerta nueva spamee con
todo el corpus histórico (el matcher solo notifica normas con
`ingested_at >= anchor_at`). Para las alertas existentes el ancla es su alta.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0006_alerta_multi"
down_revision: Union[str, None] = "0005_aviso_societario"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) columnas nuevas (nullable de entrada para poder backfillear).
    op.add_column("alerta", sa.Column("keywords", JSONB()))
    op.add_column("alerta", sa.Column("sectores", JSONB()))
    op.add_column(
        "alerta",
        sa.Column("anchor_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 2) backfill desde los escalares; ancla = alta de la alerta.
    op.execute(
        """
        UPDATE alerta SET
            keywords = jsonb_build_array(keyword),
            sectores = CASE WHEN sector IS NULL THEN '[]'::jsonb
                            ELSE jsonb_build_array(sector) END,
            anchor_at = created_at
        """
    )

    # 3) ahora sí, NOT NULL.
    op.alter_column("alerta", "keywords", nullable=False)
    op.alter_column("alerta", "sectores", nullable=False)
    op.alter_column("alerta", "anchor_at", nullable=False)

    # 4) fuera los escalares.
    op.drop_column("alerta", "keyword")
    op.drop_column("alerta", "sector")


def downgrade() -> None:
    op.add_column("alerta", sa.Column("keyword", sa.String(255)))
    op.add_column("alerta", sa.Column("sector", sa.String(64)))
    # Recuperar el primer elemento de cada lista (mejor esfuerzo).
    op.execute(
        """
        UPDATE alerta SET
            keyword = COALESCE(keywords->>0, ''),
            sector = sectores->>0
        """
    )
    op.alter_column("alerta", "keyword", nullable=False)
    op.drop_column("alerta", "anchor_at")
    op.drop_column("alerta", "sectores")
    op.drop_column("alerta", "keywords")
