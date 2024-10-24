"""Change firstname unique constraint

Revision ID: caaa9c44d0cc
Revises: a95cbf7416f1
Create Date: 2024-10-24 18:34:46.942584

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'caaa9c44d0cc'
down_revision: Union[str, None] = 'a95cbf7416f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Drop the unique constraint from the first_name column
    op.drop_index('ix_users_username', table_name='users')


def downgrade():
    # Recreate the unique index if you need to roll back
    op.create_index('ix_users_username', 'users', ['first_name'], unique=True)