"""foto verifizierung (blauer haken)

Revision ID: 0ae806a24f7a
Revises: b06c1b8f5dff
Create Date: 2026-07-18 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0ae806a24f7a'
down_revision: Union[str, None] = 'b06c1b8f5dff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=True))
    op.execute("UPDATE users SET is_verified = FALSE")
    op.alter_column('users', 'is_verified', nullable=False)

    # Enum-Typ explizit anlegen; in der Tabellendefinition create_type=False,
    # sonst versucht create_table denselben Typ ein zweites Mal anzulegen.
    sa.Enum(
        'in_progress', 'submitted', 'approved', 'rejected', name='verificationstatus'
    ).create(op.get_bind(), checkfirst=True)
    status_col_type = postgresql.ENUM(
        'in_progress', 'submitted', 'approved', 'rejected',
        name='verificationstatus', create_type=False,
    )

    op.create_table(
        'verification_requests',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('status', status_col_type, nullable=False),
        sa.Column('prompts', sa.Text(), nullable=False),
        sa.Column('selfies', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_verification_requests_user_id'), 'verification_requests', ['user_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_verification_requests_user_id'), table_name='verification_requests')
    op.drop_table('verification_requests')
    sa.Enum(name='verificationstatus').drop(op.get_bind(), checkfirst=True)
    op.drop_column('users', 'is_verified')
