"""Add sales_verified and accounts_verified to customers

Revision ID: 42cb529753f6
Revises: 5c15934f6a20
Create Date: 2024-09-16 03:06:18.087298

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42cb529753f6'
down_revision: Union[str, None] = '5c15934f6a20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():  op.add_column('customers', sa.Column('sales_verified', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():    op.drop_column('customers', 'sales_verified')