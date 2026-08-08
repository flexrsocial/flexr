"""alters- und identitaetspruefung (manueller lichtbildausweis)

Revision ID: b7c4e02a91d5
Revises: a3c9e15d7b42
Create Date: 2026-08-07 10:00:00.000000

Bestandskonten werden ausdrücklich NICHT angetastet:

* ``verification_required`` wird für alle vorhandenen Nutzer auf FALSE gesetzt.
  Sie bleiben damit unverändert nutzbar; niemand wird durch die Migration
  ausgesperrt, kein laufender Probemonat und kein Abo ändert sich.
* ``age_verified`` bleibt bei allen FALSE - auch bei Nutzern, deren
  selbst angegebenes Geburtsdatum über 18 liegt. Eine Selbstauskunft ist keine
  geprüfte Altersangabe.
* Nachgefordert wird die Prüfung gezielt über
  POST /api/admin/users/{id}/require-verification.

Neue Registrierungen setzen ``verification_required`` selbst auf TRUE
(siehe routers/auth.py), deshalb bleibt der Server-Default hier FALSE.

Laufende Verifizierungen aus der Zeit vor dieser Migration (Status
``submitted``) bleiben stehen. Sie haben keine Ausweisaufnahme; der Prüfer
fordert dafür im Admin-Tool eine Aufnahme nach.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c4e02a91d5'
down_revision: Union[str, None] = 'a3c9e15d7b42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_STATUS_VALUES = ('id_required', 'reupload_required')


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == 'postgresql'

    # ---- Neue Statuswerte im Enum ----
    # Bestandswerte bleiben unverändert, damit ausgelieferte App-Versionen die
    # Antworten weiterhin verstehen.
    if is_postgres:
        with op.get_context().autocommit_block():
            for value in NEW_STATUS_VALUES:
                op.execute(
                    f"ALTER TYPE verificationstatus ADD VALUE IF NOT EXISTS '{value}'"
                )

    # ---- users ----
    op.add_column(
        'users',
        sa.Column(
            'verification_required', sa.Boolean(), nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        'users', sa.Column('verification_required_at', sa.DateTime(), nullable=True)
    )
    op.add_column('users', sa.Column('activated_at', sa.DateTime(), nullable=True))
    op.add_column(
        'users',
        sa.Column('age_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column('users', sa.Column('age_verified_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('verification_method', sa.String(length=20), nullable=True))

    # ---- verification_requests ----
    op.add_column(
        'verification_requests', sa.Column('document_type', sa.String(length=20), nullable=True)
    )
    op.add_column('verification_requests', sa.Column('documents', sa.Text(), nullable=True))
    op.add_column('verification_requests', sa.Column('submitted_at', sa.DateTime(), nullable=True))
    op.add_column('verification_requests', sa.Column('reviewed_by', sa.String(), nullable=True))
    op.add_column(
        'verification_requests', sa.Column('review_reason', sa.String(length=40), nullable=True)
    )
    op.add_column(
        'verification_requests',
        sa.Column('cleanup_pending', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_foreign_key(
        'fk_verification_requests_reviewed_by',
        'verification_requests', 'admin_users',
        ['reviewed_by'], ['id'], ondelete='SET NULL',
    )
    # Bereits eingereichte Vorgänge gelten als vollständig eingereicht.
    op.execute(
        "UPDATE verification_requests SET submitted_at = created_at "
        "WHERE status = 'submitted' AND submitted_at IS NULL"
    )

    # ---- Registrierungsversuche unter 18 ----
    op.create_table(
        'underage_signup_attempts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_underage_signup_attempts_device_id'),
        'underage_signup_attempts', ['device_id'], unique=False,
    )
    op.create_index(
        op.f('ix_underage_signup_attempts_created_at'),
        'underage_signup_attempts', ['created_at'], unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_underage_signup_attempts_created_at'), table_name='underage_signup_attempts'
    )
    op.drop_index(
        op.f('ix_underage_signup_attempts_device_id'), table_name='underage_signup_attempts'
    )
    op.drop_table('underage_signup_attempts')

    op.drop_constraint(
        'fk_verification_requests_reviewed_by', 'verification_requests', type_='foreignkey'
    )
    op.drop_column('verification_requests', 'cleanup_pending')
    op.drop_column('verification_requests', 'review_reason')
    op.drop_column('verification_requests', 'reviewed_by')
    op.drop_column('verification_requests', 'submitted_at')
    op.drop_column('verification_requests', 'documents')
    op.drop_column('verification_requests', 'document_type')

    op.drop_column('users', 'verification_method')
    op.drop_column('users', 'age_verified_at')
    op.drop_column('users', 'age_verified')
    op.drop_column('users', 'activated_at')
    op.drop_column('users', 'verification_required_at')
    op.drop_column('users', 'verification_required')

    # Die zusätzlichen Enum-Werte bleiben bestehen: PostgreSQL kann einzelne
    # Werte nicht entfernen, und ein Neuaufbau des Typs würde die Spalte
    # anfassen. Sie stören nicht - es gibt danach keine Zeilen mehr, die sie
    # verwenden.
