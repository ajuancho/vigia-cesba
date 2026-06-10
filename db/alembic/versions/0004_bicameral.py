"""bicameral — dnu_tracking: dictamen_url + raw (crudo del dictamen)

Revision ID: 0004_bicameral
Revises: 0003_alertas
Create Date: 2026-06-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0004_bicameral"
down_revision: Union[str, None] = "0003_alertas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("dnu_tracking", sa.Column("dictamen_url", sa.String(1024)))
    op.add_column("dnu_tracking", sa.Column("raw", JSONB))


def downgrade() -> None:
    op.drop_column("dnu_tracking", "raw")
    op.drop_column("dnu_tracking", "dictamen_url")
