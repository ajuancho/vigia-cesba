"""norma — columna emisor (organismo canónico, faceteable)

Revision ID: 0007_norma_emisor
Revises: 0006_alerta_multi
Create Date: 2026-06-14

Agrega `norma.emisor`: normaliza el `organismo` (texto libre) a una clave estable
(ARCA, CNV, CNDC, BCRA, …) para filtrar/facetear. Se puebla en ingesta vía
`detect_emisor`; el histórico se rellena con la task `backfill_emisores`.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_norma_emisor"
down_revision: Union[str, None] = "0006_alerta_multi"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("norma", sa.Column("emisor", sa.String(64)))
    op.create_index("ix_norma_emisor", "norma", ["emisor"])


def downgrade() -> None:
    op.drop_index("ix_norma_emisor", table_name="norma")
    op.drop_column("norma", "emisor")
