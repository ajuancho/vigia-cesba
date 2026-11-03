"""reporte — programación de envíos periódicos por email

Revision ID: 0010_reporte_programacion
Revises: 0009_reportes
Create Date: 2026-11-03

`programacion` (JSONB) guarda frecuencia, hora, período y destinatarios;
`proximo_envio` es lo que mira el worker (`enviar_reportes_programados`, cada
15 min) y `ultimo_envio` / `ultimo_estado` registran el último resultado.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0010_reporte_programacion"
down_revision: Union[str, None] = "0009_reportes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reporte", sa.Column("programacion", JSONB()))
    op.add_column("reporte", sa.Column("proximo_envio", sa.DateTime(timezone=True)))
    op.add_column("reporte", sa.Column("ultimo_envio", sa.DateTime(timezone=True)))
    op.add_column("reporte", sa.Column("ultimo_estado", sa.String(255)))
    op.create_index("ix_reporte_proximo_envio", "reporte", ["proximo_envio"])


def downgrade() -> None:
    op.drop_index("ix_reporte_proximo_envio", table_name="reporte")
    op.drop_column("reporte", "ultimo_estado")
    op.drop_column("reporte", "ultimo_envio")
    op.drop_column("reporte", "proximo_envio")
    op.drop_column("reporte", "programacion")
