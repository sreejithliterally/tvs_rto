"""Add accounts_verified column

Revision ID: ccf92cf8aa3b
Revises: 42cb529753f6
Create Date: 2024-09-16 03:21:24.089482

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ccf92cf8aa3b'
down_revision: Union[str, None] = '42cb529753f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():  op.add_column('customers', sa.Column('accounts_verified', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():     op.drop_column('customers', 'accounts_verified')
