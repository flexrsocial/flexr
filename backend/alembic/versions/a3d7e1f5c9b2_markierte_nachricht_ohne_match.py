"""markierte nachricht ohne match

Revision ID: a3d7e1f5c9b2
Revises: d2a9f4c6b8e1
Create Date: 2026-10-14 18:00:00.000000

messages.match_id darf leer sein: Eine automatisch markierte Nachricht, deren
Match vor der Pruefung aufgeloest wurde, bleibt fuer die Moderation stehen
(routers/matches.unmatch) - ohne Chat, hoechstens bis zur Pruefung bzw.
FLAGGED_MESSAGE_UNMATCHED_DAYS (cleanup.purge_unmatched_flagged_messages).

Nur das NOT NULL faellt weg, die Tabelle wird nicht umgeschrieben.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3d7e1f5c9b2'
down_revision: Union[str, None] = 'd2a9f4c6b8e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('messages') as batch:
        batch.alter_column('match_id', existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    # Ohne Match laesst sich die Zeile nicht zurueckhaengen - sie war ohnehin
    # nur noch fuer die Pruefung da.
    op.execute("DELETE FROM messages WHERE match_id IS NULL")
    with op.batch_alter_table('messages') as batch:
        batch.alter_column('match_id', existing_type=sa.String(), nullable=False)
