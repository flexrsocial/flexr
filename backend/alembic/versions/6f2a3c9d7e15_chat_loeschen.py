"""'Chat löschen' getrennt von 'Match auflösen'.

Bislang loeste der Button "Chat loeschen" im 3-Punkte-Menue denselben
Endpunkt wie "Match aufloesen" aus (Match, Swipe und Nachrichten wurden
komplett entfernt). Gewuenscht ist stattdessen: das Match bleibt bestehen,
nur die Unterhaltung verschwindet fuer die loeschende Seite aus der
Chats-Uebersicht - analog zu user_a/b_cleared_at fuer "Chatverlauf leeren".

Revision ID: 6f2a3c9d7e15
Revises: 2c7e9f4a1b6d
Create Date: 2026-08-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6f2a3c9d7e15"
down_revision: Union[str, None] = "2c7e9f4a1b6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("matches", sa.Column("user_a_chat_deleted_at", sa.DateTime(), nullable=True))
    op.add_column("matches", sa.Column("user_b_chat_deleted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "user_b_chat_deleted_at")
    op.drop_column("matches", "user_a_chat_deleted_at")
