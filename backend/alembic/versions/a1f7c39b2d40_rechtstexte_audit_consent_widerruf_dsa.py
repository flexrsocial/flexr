"""Rechtstexte-Audit: Consent-Log, Online-Ruecktritt, DSA-Meldeverfahren

Vier Aenderungen, die zusammengehoeren, weil sie alle aus demselben Befund
stammen: Die Rechtstexte behaupteten Ablaeufe, die es im Code nicht gab.

1. ``consents`` - versionierter Einwilligungsnachweis. Bisher gab es zwei
   Zeitstempel am Nutzer, ohne die Fassung des Textes und ohne Platz fuer einen
   Widerruf (Art. 7 Abs. 1 und 3 DSGVO).

2. ``users.withdrawal_waiver_consent_at`` wird nullable. Die Erklaerung "ich
   verliere mein Ruecktrittsrecht" wurde bei jeder Registrierung erzwungen,
   obwohl bei der Registrierung gar kein entgeltlicher Vertrag entsteht.

3. ``withdrawal_declarations`` - Online-Ruecktrittsfunktion nach § 13a FAGG.
   Bisher gab es nur "Abo kuendigen", was etwas anderes ist.

4. ``notices`` plus strukturierte Begruendungsfelder an ``users`` und
   ``photos`` - Meldeverfahren nach Art. 16 DSA und Begruendung nach Art. 17
   DSA. Eine abgelehnte Foto-Freigabe war vorher kommentarlos.

Revision ID: a1f7c39b2d40
Revises: c1d84f30ab97
Create Date: 2026-08-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1f7c39b2d40"
down_revision: Union[str, None] = "c1d84f30ab97"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- 1. Einwilligungsnachweis ------------------------------------------
    op.create_table(
        "consents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("consent_type", sa.String(length=30), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column("granted_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_consents_user_id", "consents", ["user_id"])

    # Bestandskonten bekommen ihren Art.-9-Nachweis aus dem vorhandenen
    # Zeitstempel. Die Fassung ist unbekannt - sie wird als "pre-2026-08-15"
    # gekennzeichnet, statt eine Fassung zu behaupten, die damals nicht galt.
    op.execute(
        """
        INSERT INTO consents (id, user_id, consent_type, version, granted_at)
        SELECT
            md5(random()::text || clock_timestamp()::text)::uuid::text,
            id,
            'sensitive_data',
            'pre-2026-08-15',
            sensitive_data_consent_at
        FROM users
        WHERE sensitive_data_consent_at IS NOT NULL
        """
    )

    # ---- 2. Ruecktrittsverzicht entschaerfen -------------------------------
    op.alter_column(
        "users", "withdrawal_waiver_consent_at", existing_type=sa.DateTime(), nullable=True
    )

    # ---- 3. Online-Ruecktrittsfunktion (§ 13a FAGG) ------------------------
    op.create_table(
        "withdrawal_declarations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("contract_reference", sa.String(length=200), nullable=True),
        sa.Column("message", sa.String(length=1000), nullable=True),
        sa.Column("declaration_text", sa.Text(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("confirmation_sent_at", sa.DateTime(), nullable=True),
        sa.Column("confirmation_channel", sa.String(length=20), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("processing_note", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_withdrawal_declarations_email", "withdrawal_declarations", ["email"]
    )
    op.create_index(
        "ix_withdrawal_declarations_received_at", "withdrawal_declarations", ["received_at"]
    )

    # ---- 4a. Oeffentliches DSA-Meldeverfahren ------------------------------
    op.create_table(
        "notices",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("content_reference", sa.String(length=500), nullable=False),
        sa.Column("reporter_name", sa.String(length=120), nullable=True),
        sa.Column("reporter_email", sa.String(), nullable=True),
        sa.Column("good_faith", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("outcome", sa.String(length=20), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column(
            "decision_automated", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notices_created_at", "notices", ["created_at"])

    # ---- 4b. Begruendung nach Art. 17 DSA ----------------------------------
    op.add_column("users", sa.Column("moderation_scope", sa.String(length=200), nullable=True))
    op.add_column("users", sa.Column("moderation_facts", sa.String(length=1000), nullable=True))
    op.add_column("users", sa.Column("moderation_source", sa.String(length=20), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "moderation_automated", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column("users", sa.Column("moderation_basis", sa.String(length=20), nullable=True))
    op.add_column(
        "users", sa.Column("moderation_basis_detail", sa.String(length=300), nullable=True)
    )

    op.add_column("photos", sa.Column("rejection_reason", sa.String(length=40), nullable=True))
    op.add_column("photos", sa.Column("rejection_note", sa.String(length=300), nullable=True))
    op.add_column("photos", sa.Column("rejected_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("photos", "rejected_at")
    op.drop_column("photos", "rejection_note")
    op.drop_column("photos", "rejection_reason")

    op.drop_column("users", "moderation_basis_detail")
    op.drop_column("users", "moderation_basis")
    op.drop_column("users", "moderation_automated")
    op.drop_column("users", "moderation_source")
    op.drop_column("users", "moderation_facts")
    op.drop_column("users", "moderation_scope")

    op.drop_index("ix_notices_created_at", table_name="notices")
    op.drop_table("notices")

    op.drop_index(
        "ix_withdrawal_declarations_received_at", table_name="withdrawal_declarations"
    )
    op.drop_index("ix_withdrawal_declarations_email", table_name="withdrawal_declarations")
    op.drop_table("withdrawal_declarations")

    # Zurueck auf NOT NULL: Konten ohne Wert bekommen ersatzweise den Zeitpunkt
    # der Art.-9-Einwilligung - anders liesse sich die Bedingung nicht
    # wiederherstellen.
    op.execute(
        "UPDATE users SET withdrawal_waiver_consent_at = sensitive_data_consent_at "
        "WHERE withdrawal_waiver_consent_at IS NULL"
    )
    op.alter_column(
        "users", "withdrawal_waiver_consent_at", existing_type=sa.DateTime(), nullable=False
    )

    op.drop_index("ix_consents_user_id", table_name="consents")
    op.drop_table("consents")
