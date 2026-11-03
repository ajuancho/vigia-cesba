"""alerta — filtro por fuente (Boletín Oficial / Legislatura)

Revision ID: 0011_alerta_fuentes
Revises: 0010_reporte_programacion
Create Date: 2026-11-03

`fuentes` (JSONB, lista) acota qué fuentes vigila cada alerta: "boletin",
"legislatura". Lista vacía = todas, que es el comportamiento de las alertas
existentes (por eso el default '[]').
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0011_alerta_fuentes"
down_revision: Union[str, None] = "0010_reporte_programacion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "alerta",
        sa.Column("fuentes", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )


def downgrade() -> None:
    op.drop_column("alerta", "fuentes")
