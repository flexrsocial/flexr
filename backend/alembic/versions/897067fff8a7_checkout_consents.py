"""Zwei getrennte Checkout-Erklaerungen (checkout_consents)

Revision ID: 897067fff8a7
Revises: 16909686d8bd
Create Date: 2026-08-17

Beim kostenpflichtigen Checkout muessen zwei Erklaerungen einzeln bestaetigt
und einzeln nachgewiesen werden: das Verlangen nach sofortigem
Leistungsbeginn (§ 10 FAGG) und die Kenntnisnahme, dass das Ruecktrittsrecht
nach vollstaendiger Vertragserfuellung erlischt (§ 18 Abs. 1 Z 1 FAGG). Eine
eigene Tabelle statt der bestehenden ``consents``-Tabelle, weil das
widerrufbare DSGVO-Einwilligungen sind und diese beiden Erklaerungen keine
Einwilligungen im Sinne der DSGVO sind, sondern Wissenserklaerungen zum
Vertrag - siehe models.CheckoutConsent.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "897067fff8a7"
down_revision = "16909686d8bd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "checkout_consents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("immediate_start_version", sa.String(length=20), nullable=False),
        sa.Column("immediate_start_granted_at", sa.DateTime(), nullable=False),
        sa.Column("withdrawal_ack_version", sa.String(length=20), nullable=False),
        sa.Column("withdrawal_ack_granted_at", sa.DateTime(), nullable=False),
        sa.Column("stripe_subscription_id", sa.String(), nullable=True),
        sa.Column("stripe_customer_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_checkout_consents_user_id", "checkout_consents", ["user_id"], unique=False
    )
    op.create_index(
        "ix_checkout_consents_stripe_subscription_id",
        "checkout_consents",
        ["stripe_subscription_id"],
        unique=False,
    )
    op.create_index(
        "ix_checkout_consents_created_at", "checkout_consents", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_checkout_consents_created_at", table_name="checkout_consents")
    op.drop_index("ix_checkout_consents_stripe_subscription_id", table_name="checkout_consents")
    op.drop_index("ix_checkout_consents_user_id", table_name="checkout_consents")
    op.drop_table("checkout_consents")
