"""Widerruf haerten: Idempotenz, Vienna-Lokalzeit, Status, Stripe-Storno

Revision ID: 16909686d8bd
Revises: a1f7c39b2d40
Create Date: 2026-08-17

Vier Luecken, die beim Nachziehen der Online-Ruecktrittsfunktion (§ 13a FAGG)
aufgefallen sind:

* Ein Doppelklick auf "Widerruf bestaetigen" konnte zwei Erklaerungen und
  zwei Bestaetigungsmails erzeugen - request_id macht das serverseitig
  idempotent, nicht nur per deaktiviertem Button im Browser.
* Gespeichert war nur der UTC-Zeitpunkt; § 13a Abs. 4 FAGG verlangt Datum und
  Uhrzeit in der Bestaetigung, angezeigt wird sie in Europe/Vienna.
* Es gab keinen Status auf der Erklaerung selbst, nur die Kombination aus
  confirmation_sent_at/processed_at - jetzt ein Feld dafuer.
* subscription_stopped_at haelt fest, wann (und ob) ein zugeordnetes
  Stripe-Abo automatisch an der Verlaengerung gehindert wurde.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "16909686d8bd"
down_revision = "a1f7c39b2d40"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "withdrawal_declarations",
        sa.Column("request_id", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_withdrawal_declarations_request_id",
        "withdrawal_declarations",
        ["request_id"],
        unique=True,
    )
    op.add_column(
        "withdrawal_declarations",
        # Bestehende Zeilen: Platzhalter, weil die tatsaechliche Lokalzeit aus
        # dem UTC-Zeitpunkt ohne weitere Annahmen ueber Sommer-/Winterzeit im
        # Nachhinein nicht mehr zuverlaessig rekonstruierbar ist. In der Praxis
        # betrifft das ohnehin niemanden: Vor diesem Deploy lief die Funktion
        # nur in Tests.
        sa.Column("received_at_vienna", sa.String(length=40), nullable=False,
                  server_default="unbekannt (vor diesem Deploy erklaert)"),
    )
    op.alter_column("withdrawal_declarations", "received_at_vienna", server_default=None)
    op.add_column(
        "withdrawal_declarations",
        sa.Column("status", sa.String(length=30), nullable=False, server_default="eingegangen"),
    )
    op.alter_column("withdrawal_declarations", "status", server_default=None)
    op.add_column(
        "withdrawal_declarations",
        sa.Column("subscription_stopped_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("withdrawal_declarations", "subscription_stopped_at")
    op.drop_column("withdrawal_declarations", "status")
    op.drop_column("withdrawal_declarations", "received_at_vienna")
    op.drop_index("ix_withdrawal_declarations_request_id", table_name="withdrawal_declarations")
    op.drop_column("withdrawal_declarations", "request_id")
