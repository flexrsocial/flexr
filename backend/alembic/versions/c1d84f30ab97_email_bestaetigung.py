"""e-mail-bestaetigung per aktivierungslink

Revision ID: c1d84f30ab97
Revises: b7c4e02a91d5
Create Date: 2026-08-14 15:10:00.000000

Neue Registrierungen muessen ihre Adresse bestaetigen, bevor die Alters- und
Identitaetspruefung startet (siehe routers/email_verify.py).

Bestandskonten werden ausdruecklich NICHT ausgesperrt: ``email_verified_at``
wird fuer alle vorhandenen Nutzer auf den Zeitpunkt dieser Migration gesetzt.
Sie gelten damit als bestaetigt und merken von der Umstellung nichts. Eine
nachtraegliche Bestaetigung liesse sich sonst gar nicht einholen - es gibt
keinen Weg, ein bestehendes Konto zur Mailbestaetigung zu zwingen, ohne es
zwischenzeitlich unbenutzbar zu machen.

Der Token liegt nur als SHA-256-Hash in der Tabelle. Er steht im
Aktivierungslink und ist damit ein Passwort auf Zeit; im Klartext gespeichert
waere ein Datenbankleck gleichbedeutend mit uebernehmbaren Konten.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d84f30ab97'
down_revision: Union[str, None] = 'b7c4e02a91d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(), nullable=True))

    # Bestandskonten gelten als bestaetigt - siehe Kopf.
    op.execute("UPDATE users SET email_verified_at = NOW() WHERE email_verified_at IS NULL")

    op.create_table(
        'email_verifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_email_verifications_user_id'), 'email_verifications', ['user_id'], unique=False
    )
    # Die Bestaetigung sucht ueber den Hash - ohne Index ein Full Scan je Klick.
    op.create_index(
        op.f('ix_email_verifications_token_hash'),
        'email_verifications',
        ['token_hash'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_email_verifications_token_hash'), table_name='email_verifications')
    op.drop_index(op.f('ix_email_verifications_user_id'), table_name='email_verifications')
    op.drop_table('email_verifications')
    op.drop_column('users', 'email_verified_at')
