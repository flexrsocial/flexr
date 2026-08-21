"""Fehlende sensitive_data-Consent-Zeilen nachtragen.

Die urspruengliche Migration (a1f7c39b2d40) hat beim Anlegen der
``consents``-Tabelle bereits alle damals bestehenden Konten mit
``sensitive_data_consent_at IS NOT NULL`` nachgetragen. Danach angelegte
Konten - u. a. per Registrierungs-API (die granted() korrekt aufruft), aber
auch mindestens ein per Skript direkt in die DB geschriebenes Konto - koennen
trotzdem ohne diese Zeile dastehen, wenn beim Anlegen nicht ueber
``consents.grant()`` gegangen wurde.

Das fiel auf, weil ein neuer Deck-Filter (siehe
``consents.sensitive_data_consent_condition()``, routers/swipes.py) ab jetzt
eine aktive Consent-Zeile verlangt, um das Widerruf-Versprechen "du
erscheinst in keinem Deck mehr" ueberhaupt durchzusetzen - ohne diesen
Nachtrag waeren betroffene Konten (u. a. ein echtes Bestandskonto) faelschlich
aus jedem fremden Deck verschwunden, obwohl nie widerrufen wurde.

Gleicher Ansatz wie in a1f7c39b2d40: Fassung wird nicht erfunden, sondern als
Nachtrag gekennzeichnet.

Revision ID: 9c4e1a7f2b83
Revises: 6f2a3c9d7e15
Create Date: 2026-08-21
"""

from typing import Sequence, Union

from alembic import op


revision: str = "9c4e1a7f2b83"
down_revision: Union[str, None] = "6f2a3c9d7e15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO consents (id, user_id, consent_type, version, granted_at)
        SELECT
            md5(random()::text || clock_timestamp()::text)::uuid::text,
            u.id,
            'sensitive_data',
            'nachtrag-2026-08-21',
            u.sensitive_data_consent_at
        FROM users u
        WHERE u.sensitive_data_consent_at IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM consents c
              WHERE c.user_id = u.id
                AND c.consent_type = 'sensitive_data'
                AND c.revoked_at IS NULL
          )
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM consents WHERE version = 'nachtrag-2026-08-21'")
