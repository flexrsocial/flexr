"""Benachrichtigungen: Schalter, Vordergrund-Aktivitaet und Push-Zustellfach.

Revision ID: a4e17c9b2d58
Revises: 9c4e1a7f2b83
Create Date: 2026-08-31
"""

from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4e17c9b2d58"
down_revision: Union[str, None] = "9c4e1a7f2b83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Die sechs Schalter unter "Benachrichtigungen" - je Anlass einer fuer E-Mail
# und einer fuer die App.
_FLAGS = (
    "notify_match_email",
    "notify_match_push",
    "notify_queue_email",
    "notify_queue_push",
    "notify_inactive_email",
    "notify_inactive_push",
)


def upgrade() -> None:
    for flag in _FLAGS:
        # server_default: Bestandszeilen bekommen die Voreinstellung "an",
        # sonst stuenden sie nach der Migration auf NULL und waeren damit
        # faktisch abgeschaltet, ohne dass es jemand eingestellt haette.
        op.add_column(
            "users",
            sa.Column(flag, sa.Boolean(), nullable=False, server_default=sa.true()),
        )

    op.add_column("users", sa.Column("last_active_at", sa.DateTime(), nullable=True))
    # Bestandskonten auf "jetzt" setzen, nicht auf NULL.
    #
    # Ohne diese Zeile stuenden nach der Migration ALLE Konten auf NULL, und der
    # Job faellt bei NULL auf created_at zurueck (siehe email_jobs.py). Der erste
    # naechtliche Lauf haette damit jedem Konto, das aelter als sieben Tage ist,
    # auf einen Schlag die Inaktivitaets-Erinnerung geschickt - per E-Mail und
    # als App-Benachrichtigung, an den gesamten ruhenden Bestand gleichzeitig.
    # Verschickt ist verschickt.
    #
    # Auch nicht aus last_seen_at ableiten: das ist bei App-Nutzern durch den
    # Hintergrund-Poller verfaelscht, und bei allen wirklich ruhenden Konten
    # laege es ueber sieben Tage zurueck - also derselbe Schwall.
    #
    # Mit "jetzt" beginnt die Frist beim Deploy: Wer ab hier sieben Tage nicht
    # auftaucht, bekommt die Erinnerung reguraer. Einmalig warten die ohnehin
    # schon laenger Ruhenden eine Woche laenger - der Preis dafuer, dass die
    # Funktion still statt mit einem Rundumschlag anlaeuft.
    #
    # Zeitstempel bewusst aus Python statt per NOW(): die Anwendung schreibt
    # naive UTC-Werte (datetime.utcnow()), NOW() lieferte dagegen die Ortszeit
    # des Servers - auf einem Wiener Host also zwei Stunden Versatz gegen alle
    # uebrigen Zeitstempel derselben Spalte.
    op.execute(
        sa.text("UPDATE users SET last_active_at = :now WHERE last_active_at IS NULL")
        .bindparams(now=datetime.utcnow())
    )

    op.create_table(
        "push_notifications",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column(
            "topic",
            sa.Enum("new_match", "queue_waiting", "inactivity", name="notificationtopic"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("body", sa.String(length=300), nullable=False),
        sa.Column("target", sa.String(length=20), nullable=True),
        sa.Column("dedupe_key", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_push_notifications_dedupe_key", "push_notifications", ["dedupe_key"], unique=True
    )
    op.create_index(
        "ix_push_notifications_user_id", "push_notifications", ["user_id"], unique=False
    )
    op.create_index(
        "ix_push_notifications_created_at", "push_notifications", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_push_notifications_created_at", table_name="push_notifications")
    op.drop_index("ix_push_notifications_user_id", table_name="push_notifications")
    op.drop_index("ix_push_notifications_dedupe_key", table_name="push_notifications")
    op.drop_table("push_notifications")
    sa.Enum(name="notificationtopic").drop(op.get_bind(), checkfirst=True)

    op.drop_column("users", "last_active_at")
    for flag in _FLAGS:
        op.drop_column("users", flag)
