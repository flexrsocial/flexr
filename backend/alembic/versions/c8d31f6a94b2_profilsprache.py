"""Profilsprache: users.language und notices.language

Die Sprachwahl lebte bisher nur im Client (localStorage `flexr_lang` im Web,
LanguageStore in Android und iOS). Der Server verschickt aber E-Mails, die ohne
Zutun des Clients entstehen - die Inaktivitaets-Erinnerung aus dem Tagesjob,
die Moderationsmitteilung aus dem Admin-Bereich, die Zahlungsmail aus einem
Stripe-Webhook. Ohne eine Sprache am Nutzer haette der Mailer nie erfahren, in
welcher Sprache er schreiben soll.

Bestandskonten bekommen "de": Deutsch ist die Ausgangssprache, und niemand hat
je etwas anderes gemeldet. Wer danach im Client umschaltet, schreibt den Wert
ueber PATCH /api/profiles/me fort.

``notices.language`` aus demselben Grund an zweiter Stelle: Eine Meldung nach
Art. 16 DSA darf jeder abgeben, auch ohne Konto - es gibt dort kein Profil,
aus dem sich die Sprache ablesen liesse. Die Entscheidung nach Art. 16 Abs. 5
kommt aber erst Tage spaeter und soll denselben Melder in derselben Sprache
erreichen wie die Empfangsbestaetigung.

Revision ID: c8d31f6a94b2
Revises: b1f994fbd4d0
Create Date: 2026-09-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8d31f6a94b2"
down_revision: Union[str, None] = "b1f994fbd4d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default statt nur default: Die Spalte ist NOT NULL, und bestehende
    # Zeilen brauchen im selben ALTER einen Wert. Der Default bleibt danach
    # bewusst stehen - so kommt auch ein INSERT an SQLAlchemy vorbei (Fixtures,
    # manuelle Korrekturen) nie ohne Sprache aus.
    op.add_column(
        "users",
        sa.Column("language", sa.String(length=2), nullable=False, server_default="de"),
    )
    op.add_column(
        "notices",
        sa.Column("language", sa.String(length=2), nullable=False, server_default="de"),
    )


def downgrade() -> None:
    op.drop_column("notices", "language")
    op.drop_column("users", "language")
