"""Abos aus App Store und Play Store

FLEXR Premium war bis hierher ein Stripe-Vertrag: Kunde bei uns, Rechnung von
uns, Kuendigung ueber das Stripe-Portal. Ein Kauf in der iOS- oder Android-App
ist etwas anderes - Apple und Google sind Haendler, wir erfahren vom Vertrag
nur ueber einen signierten Beleg und danach ueber Benachrichtigungen. Deshalb
eine eigene Tabelle statt weiterer Stripe-Spalten, die kein Stripe-Aufruf je
wiederfindet.

``users.store_premium_until`` ist die denormalisierte Antwort auf "darf dieses
Konto gerade": ``User.is_premium`` wird bei jeder Profilausgabe gelesen, im
Deck also bis zu 50-mal pro Anfrage - eine Unterabfrage je Profil waere dort
teuer.

Revision ID: b2e75c41a908
Revises: d8a1e4c6f209
Create Date: 2026-09-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2e75c41a908"
down_revision: Union[str, None] = "d8a1e4c6f209"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("store_premium_until", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "store_subscriptions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        # Als String und nicht als PostgreSQL-ENUM: Ein weiterer Store waere
        # sonst eine Migration mit ALTER TYPE. SQLAlchemy prueft die Werte
        # ohnehin ueber Enum(StoreProvider) auf der Anwendungsseite.
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("product_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("auto_renewing", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "environment", sa.String(length=20), nullable=False, server_default="Production"
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        # Verhindert, dass derselbe Kauf auf zwei Konten Premium erzeugt.
        sa.UniqueConstraint("provider", "external_id", name="uq_store_subscription"),
    )
    op.create_index(
        "ix_store_subscriptions_user_id", "store_subscriptions", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_store_subscriptions_user_id", table_name="store_subscriptions")
    op.drop_table("store_subscriptions")
    op.drop_column("users", "store_premium_until")
