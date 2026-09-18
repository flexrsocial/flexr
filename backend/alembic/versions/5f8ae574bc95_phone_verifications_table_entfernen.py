"""phone_verifications-Tabelle entfernen (verworfene SMS-Telefonpruefung)

Die selbstbedienbare SMS-Telefonpruefung (/api/phone/request, /api/phone/confirm)
wurde nie in Betrieb genommen - der Router war seit seiner Einfuehrung nie in
main.py registriert (siehe tests/test_security_features.py::
test_phone_verification_is_not_exposed, das genau das absichtlich prueft).
Die Tabelle blieb seitdem ungenutzt und leer. app/routers/phone.py und
app/sms.py sowie das PhoneVerification-Modell wurden im selben Aufraeumdurch-
gang entfernt.

Revision ID: 5f8ae574bc95
Revises: 2e09478f0339
Create Date: 2026-09-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "5f8ae574bc95"
down_revision: Union[str, None] = "2e09478f0339"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_phone_verifications_user_id"), table_name="phone_verifications")
    op.drop_table("phone_verifications")


def downgrade() -> None:
    op.create_table(
        "phone_verifications",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("code_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_phone_verifications_user_id"), "phone_verifications", ["user_id"], unique=False
    )
