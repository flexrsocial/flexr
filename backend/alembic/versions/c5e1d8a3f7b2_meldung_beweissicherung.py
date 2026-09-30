"""meldung beweissicherung

Revision ID: c5e1d8a3f7b2
Revises: b7c2e4f9a1d3
Create Date: 2026-09-30 12:00:00.000000

Chat-Auszug an der Meldung (reports.evidence), damit ein aufgeloestes Match
die Beweise nicht vor der Pruefung mitnimmt.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c5e1d8a3f7b2'
down_revision: Union[str, None] = 'b7c2e4f9a1d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('evidence', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('reports', 'evidence')
