"""Fehlende Indizes: users.gym, photos.status (pending), messages.is_flagged

``users.gym`` ist die fuehrende Filterspalte in ``deck_profiles``
(routers/swipes.py: ``User.gym.in_(batch)``) - dem meistaufgerufenen Pfad der
App (jedes Deck laden, jeder Swipe, seit dem Warteschlangen-Hinweis auch der
taegliche Mail-Job), bislang ohne eigenen Index. Mit wachsender
Nutzertabelle wird daraus ein Sequential Scan pro Gym-Batch.

``photos.status`` und ``messages.is_flagged`` werden im Admin-Dashboard bei
jedem Seitenaufruf abgefragt (get_stats, list_photos, list_flagged_messages,
siehe routers/admin.py) - jeweils nur fuer den kleinen Teil der Zeilen mit
status='pending' bzw. is_flagged=true. Ein partieller Index deckt genau diese
Abfragen ab, ohne fuer jede genehmigte Foto-/unmarkierte Nachrichtenzeile
mitgepflegt werden zu muessen.

CONCURRENTLY, damit das Anlegen auf der Produktionsdatenbank keine
schreibenden Zugriffe auf users/photos/messages blockiert.

Revision ID: 2e09478f0339
Revises: c93f18ad6b27
Create Date: 2026-09-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "2e09478f0339"
down_revision: Union[str, None] = "c93f18ad6b27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_users_gym", "users", ["gym"],
            unique=False, postgresql_concurrently=True,
        )
        op.create_index(
            "ix_photos_status_pending", "photos", ["status"],
            unique=False, postgresql_concurrently=True,
            postgresql_where=sa.text("status = 'pending'"),
        )
        op.create_index(
            "ix_messages_is_flagged", "messages", ["is_flagged"],
            unique=False, postgresql_concurrently=True,
            postgresql_where=sa.text("is_flagged"),
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index("ix_messages_is_flagged", table_name="messages", postgresql_concurrently=True)
        op.drop_index("ix_photos_status_pending", table_name="photos", postgresql_concurrently=True)
        op.drop_index("ix_users_gym", table_name="users", postgresql_concurrently=True)
