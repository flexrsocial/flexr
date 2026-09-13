"""Fehlende Indizes: swipes.to_user_id, matches.user_b_id, photos.user_id

Alle drei Spalten werden auf jedem Deck-Aufruf, jeder "wer hat mich
geliket"-Abfrage, jeder Matches-Liste und jedem Foto-Upload/-Löschen gefiltert
(siehe routers/swipes.py, routers/matches.py, routers/profiles.py,
app/email_jobs.py) - bislang ohne eigenen Index. Der Unique-Constraint auf
swipes deckt nur from_user_id als führende Spalte ab, der auf matches nur
user_a_id; photos.user_id hatte gar keinen Index. Mit wachsender Tabelle wird
aus jeder dieser Abfragen sonst zunehmend ein Sequential Scan.

CONCURRENTLY, damit das Anlegen auf der Produktionsdatenbank keine
schreibenden Zugriffe auf swipes/matches/photos blockiert - genau diese
Tabellen werden bei jedem Swipe beschrieben.

Revision ID: d8a1e4c6f209
Revises: c8d31f6a94b2
Create Date: 2026-09-13
"""

from typing import Sequence, Union

from alembic import op

revision: str = "d8a1e4c6f209"
down_revision: Union[str, None] = "c8d31f6a94b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_swipes_to_user_id", "swipes", ["to_user_id"],
            unique=False, postgresql_concurrently=True,
        )
        op.create_index(
            "ix_matches_user_b_id", "matches", ["user_b_id"],
            unique=False, postgresql_concurrently=True,
        )
        op.create_index(
            "ix_photos_user_id", "photos", ["user_id"],
            unique=False, postgresql_concurrently=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index("ix_photos_user_id", table_name="photos", postgresql_concurrently=True)
        op.drop_index("ix_matches_user_b_id", table_name="matches", postgresql_concurrently=True)
        op.drop_index("ix_swipes_to_user_id", table_name="swipes", postgresql_concurrently=True)
