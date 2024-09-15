"""Add first_name and last_name columns to users

Revision ID: a27752974b08
Revises: 446184dde12f
Create Date: 2024-09-14 19:19:55.474546

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a27752974b08'
down_revision: Union[str, None] = '446184dde12f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Rename 'username' to 'first_name'
    op.alter_column('users', 'username', new_column_name='first_name')

    # Add new 'last_name' column
    op.add_column('users', sa.Column('last_name', sa.String(length=255), nullable=True))


def downgrade():
    # Reverse the 'last_name' column addition
    op.drop_column('users', 'last_name')

    # Reverse the rename 'first_name' back to 'username'
    op.alter_column('users', 'first_name', new_column_name='username')