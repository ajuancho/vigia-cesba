"""norma — índice en jurisdiccion + source_catalog seed para bocba

Revision ID: 0008_bocba
Revises: 0007_norma_emisor
Create Date: 2026-06-18

La columna `norma.jurisdiccion` existe desde 0001_initial pero nunca tuvo
índice. El BOCBA introduce filtros frecuentes por jurisdiccion='CABA' (feed,
búsqueda, stats), por lo que el índice evita seq-scans sobre el corpus completo.

También siembra la fila de `source_catalog` para 'bocba' mediante un INSERT
idempotente (ON CONFLICT DO NOTHING), igual que hacen las tasks de ingesta en
cada arranque. Esto asegura que la fila exista antes de que corra la primera
task, lo que permite que `GET /health/sources` la muestre desde el deploy.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_bocba"
down_revision: Union[str, None] = "0007_norma_emisor"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Índice para filtros por jurisdiccion (CABA / Nacional / etc.)
    op.create_index("ix_norma_jurisdiccion", "norma", ["jurisdiccion"])

    # Seed de source_catalog para bocba (idempotente).
    op.execute(
        """
        INSERT INTO source_catalog (code, name, kind, base_url)
        VALUES (
            'bocba',
            'Boletín Oficial CABA — edición del día (boletinoficial.buenosaires.gob.ar)',
            'api',
            'https://api-restboletinoficial.buenosaires.gob.ar'
        )
        ON CONFLICT (code) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM source_catalog WHERE code = 'bocba'")
    op.drop_index("ix_norma_jurisdiccion", table_name="norma")
