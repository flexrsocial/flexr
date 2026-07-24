"""chat-zensur: display_content + was_censored

Revision ID: c610705a09a8
Revises: 9f293e0a8d54
Create Date: 2026-07-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c610705a09a8'
down_revision: Union[str, None] = '9f293e0a8d54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('messages', sa.Column('display_content', sa.String(length=2000), nullable=True))
    op.add_column('messages', sa.Column('was_censored', sa.Boolean(), nullable=True))
    op.execute("UPDATE messages SET was_censored = FALSE")
    op.alter_column('messages', 'was_censored', nullable=False)


def downgrade() -> None:
    op.drop_column('messages', 'was_censored')
    op.drop_column('messages', 'display_content')
