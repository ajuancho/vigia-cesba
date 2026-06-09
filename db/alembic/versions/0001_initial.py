"""initial — source_catalog, norma (FTS spanish), dnu_tracking

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensiones (idempotente; también se crean vía db/init en docker).
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")

    op.create_table(
        "source_catalog",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("base_url", sa.String(512)),
        sa.Column("last_run_at", sa.DateTime(timezone=True)),
        sa.Column("last_status", sa.String(32)),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("code", name="uq_source_code"),
    )
    op.create_index("ix_source_catalog_code", "source_catalog", ["code"])

    op.create_table(
        "norma",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("source_catalog.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("tipo", sa.String(32), nullable=False),
        sa.Column("numero", sa.String(64)),
        sa.Column("titulo", sa.Text(), nullable=False),
        sa.Column("resumen", sa.Text()),
        sa.Column("resumen_ia", sa.Text()),
        sa.Column("fecha_publicacion", sa.Date()),
        sa.Column("jurisdiccion", sa.String(64)),
        sa.Column("sector", sa.String(64)),
        sa.Column("organismo", sa.String(255)),
        sa.Column("estado", sa.String(128)),
        sa.Column("impacto", sa.String(16)),
        sa.Column("bora_seccion", sa.String(64)),
        sa.Column("entidades", postgresql.JSONB()),
        sa.Column("tags", postgresql.JSONB()),
        sa.Column("url", sa.String(1024)),
        sa.Column("raw", postgresql.JSONB()),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_id", "external_id", name="uq_norma_source_external"),
    )
    op.create_index("ix_norma_fecha", "norma", ["fecha_publicacion"])
    op.create_index("ix_norma_tipo_sector", "norma", ["tipo", "sector"])
    op.create_index("ix_norma_impacto", "norma", ["impacto"])

    # Columna generada para full-text search en español (título pesa más que resumen).
    op.execute(
        """
        ALTER TABLE norma ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('spanish', coalesce(titulo, '')), 'A') ||
            setweight(to_tsvector('spanish', coalesce(resumen, '')), 'B') ||
            setweight(to_tsvector('spanish', coalesce(organismo, '')), 'C')
        ) STORED
        """
    )
    op.create_index(
        "ix_norma_search_vector", "norma", ["search_vector"], postgresql_using="gin"
    )

    op.create_table(
        "dnu_tracking",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("norma_id", sa.BigInteger(), sa.ForeignKey("norma.id", ondelete="CASCADE"), nullable=False),
        sa.Column("estado_bicameral", sa.String(32), nullable=False, server_default="pendiente"),
        sa.Column("fecha_dictamen", sa.Date()),
        sa.Column("plazo_limite", sa.Date()),
        sa.Column("notas", sa.Text()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("norma_id", name="uq_dnu_norma"),
    )
    op.create_index("ix_dnu_estado", "dnu_tracking", ["estado_bicameral"])


def downgrade() -> None:
    op.drop_table("dnu_tracking")
    op.drop_index("ix_norma_search_vector", table_name="norma")
    op.drop_table("norma")
    op.drop_index("ix_source_catalog_code", table_name="source_catalog")
    op.drop_table("source_catalog")
