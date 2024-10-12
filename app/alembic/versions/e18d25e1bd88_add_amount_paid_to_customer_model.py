"""add amount_paid to Customer model

Revision ID: e18d25e1bd88
Revises: eb075bd37ecc
Create Date: 2024-10-11 10:48:55.819550

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e18d25e1bd88'
down_revision: Union[str, None] = 'eb075bd37ecc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add the 'amount_paid' column to the 'customers' table
    op.add_column('customers', sa.Column('amount_paid', sa.DECIMAL(10, 2), nullable=True))


def downgrade():
    # Remove the 'amount_paid' column from the 'customers' table
    op.drop_column('customers', 'amount_paid')