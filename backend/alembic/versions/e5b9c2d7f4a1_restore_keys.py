"""restore_keys

Revision ID: e5b9c2d7f4a1
Revises: b8d4f0a2c6e3
Create Date: 2026-11-07 20:00:00.000000

Restore Credentials der Android-App: oeffentliche Schluessel
(restore_credentials) und Einmal-Challenges (restore_challenges) - siehe
app/restore_keys.py.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5b9c2d7f4a1'
down_revision: Union[str, None] = 'b8d4f0a2c6e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'restore_credentials',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('credential_id', sa.String(), nullable=False),
        sa.Column('public_key', sa.Text(), nullable=False),
        sa.Column('sign_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('device_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('credential_id'),
    )
    op.create_index('ix_restore_credentials_user_id', 'restore_credentials', ['user_id'])
    op.create_index('ix_restore_credentials_device_id', 'restore_credentials', ['device_id'])

    op.create_table(
        'restore_challenges',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('challenge', sa.String(), nullable=False),
        sa.Column('purpose', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('challenge'),
    )
    op.create_index('ix_restore_challenges_user_id', 'restore_challenges', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_restore_challenges_user_id', table_name='restore_challenges')
    op.drop_table('restore_challenges')
    op.drop_index('ix_restore_credentials_device_id', table_name='restore_credentials')
    op.drop_index('ix_restore_credentials_user_id', table_name='restore_credentials')
    op.drop_table('restore_credentials')
