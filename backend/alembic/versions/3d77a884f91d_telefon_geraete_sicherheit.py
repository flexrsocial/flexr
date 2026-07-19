"""telefonpruefung, geraetepruefung, nachrichten-flags

Revision ID: 3d77a884f91d
Revises: 0ae806a24f7a
Create Date: 2026-07-18 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d77a884f91d'
down_revision: Union[str, None] = '0ae806a24f7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Telefonprüfung
    op.add_column('users', sa.Column('phone', sa.String(), nullable=True))
    op.add_column('users', sa.Column('phone_verified_at', sa.DateTime(), nullable=True))

    op.create_table(
        'phone_verifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('code_hash', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_phone_verifications_user_id'), 'phone_verifications', ['user_id'], unique=False
    )

    # Geräteprüfung
    op.create_table(
        'user_devices',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'device_id', name='uq_user_device'),
    )
    op.create_index(op.f('ix_user_devices_user_id'), 'user_devices', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_devices_device_id'), 'user_devices', ['device_id'], unique=False)

    # Nachrichten-Sicherheitsflags
    op.add_column('messages', sa.Column('is_flagged', sa.Boolean(), nullable=True))
    op.execute("UPDATE messages SET is_flagged = FALSE")
    op.alter_column('messages', 'is_flagged', nullable=False)
    op.add_column('messages', sa.Column('flag_reason', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('messages', 'flag_reason')
    op.drop_column('messages', 'is_flagged')
    op.drop_index(op.f('ix_user_devices_device_id'), table_name='user_devices')
    op.drop_index(op.f('ix_user_devices_user_id'), table_name='user_devices')
    op.drop_table('user_devices')
    op.drop_index(op.f('ix_phone_verifications_user_id'), table_name='phone_verifications')
    op.drop_table('phone_verifications')
    op.drop_column('users', 'phone_verified_at')
    op.drop_column('users', 'phone')
