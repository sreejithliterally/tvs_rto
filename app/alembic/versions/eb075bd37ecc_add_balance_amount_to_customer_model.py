"""Add balance_amount to Customer model

Revision ID: eb075bd37ecc
Revises: 4df77bc21033
Create Date: 2024-10-09 22:15:30.731148

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb075bd37ecc'
down_revision: Union[str, None] = '4df77bc21033'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add the balance_amount column to the customers table
    op.add_column('customers', sa.Column('balance_amount', sa.DECIMAL(precision=10, scale=2), nullable=True))


def downgrade():
    # Remove the balance_amount column from the customers table
    op.drop_column('customers', 'balance_amount')