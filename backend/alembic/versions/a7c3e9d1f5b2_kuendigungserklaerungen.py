"""kuendigungserklaerungen (kuendigungsbutton nach § 312k BGB)

Revision ID: a7c3e9d1f5b2
Revises: f4d9b2e6a8c1
Create Date: 2026-11-03 14:00:00.000000

Neue Tabelle cancellation_declarations fuer den Kuendigungsbutton, der mit dem
Start in Deutschland Pflicht wird (siehe models.CancellationDeclaration).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7c3e9d1f5b2'
down_revision: Union[str, None] = 'f4d9b2e6a8c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'cancellation_declarations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('request_id', sa.String(length=64), nullable=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('contract_reference', sa.String(length=200), nullable=True),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.String(length=1000), nullable=True),
        sa.Column('requested_end', sa.Date(), nullable=True),
        sa.Column('declaration_text', sa.Text(), nullable=False),
        sa.Column('received_at', sa.DateTime(), nullable=False),
        sa.Column('received_at_local', sa.String(length=40), nullable=False),
        sa.Column('effective_at', sa.DateTime(), nullable=True),
        sa.Column('subscription_cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('confirmation_sent_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_note', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_cancellation_declarations_email'), 'cancellation_declarations', ['email'])
    op.create_index(op.f('ix_cancellation_declarations_received_at'), 'cancellation_declarations', ['received_at'])
    op.create_index(op.f('ix_cancellation_declarations_request_id'), 'cancellation_declarations', ['request_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_cancellation_declarations_request_id'), table_name='cancellation_declarations')
    op.drop_index(op.f('ix_cancellation_declarations_received_at'), table_name='cancellation_declarations')
    op.drop_index(op.f('ix_cancellation_declarations_email'), table_name='cancellation_declarations')
    op.drop_table('cancellation_declarations')
