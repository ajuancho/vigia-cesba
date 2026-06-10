"""aviso_societario — BORA 2ª sección (Radar societario)

Revision ID: 0005_aviso_societario
Revises: 0004_bicameral
Create Date: 2026-06-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0005_aviso_societario"
down_revision: Union[str, None] = "0004_bicameral"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "aviso_societario",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("aviso_id", sa.String(32), nullable=False, unique=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("razon_social", sa.String(512)),
        sa.Column("rubro", sa.String(255)),
        sa.Column("texto", sa.Text()),
        sa.Column("url", sa.String(1024)),
        sa.Column("raw", JSONB()),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_aviso_fecha", "aviso_societario", ["fecha"])
    op.create_index("ix_aviso_rubro", "aviso_societario", ["rubro"])

    # FTS propio: razón social pesa más que el rubro y el texto del aviso.
    op.execute(
        """
        ALTER TABLE aviso_societario ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('spanish', coalesce(razon_social, '')), 'A') ||
            setweight(to_tsvector('spanish', coalesce(rubro, '')), 'B') ||
            setweight(to_tsvector('spanish', coalesce(texto, '')), 'C')
        ) STORED
        """
    )
    op.create_index(
        "ix_aviso_search_vector", "aviso_societario", ["search_vector"], postgresql_using="gin"
    )


def downgrade() -> None:
    op.drop_table("aviso_societario")
