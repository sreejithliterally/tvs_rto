"""Remove onroad_price from customers table

Revision ID: c14eb39261aa
Revises: 0698dce98644
Create Date: 2024-09-26 14:32:21.860181

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c14eb39261aa'
down_revision: Union[str, None] = '0698dce98644'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Remove the 'onroad_price' column from the 'customers' table
    op.drop_column('customers', 'onroad_price')


def downgrade():
    # Add the 'onroad_price' column back to the 'customers' table (for rollback)
    op.add_column('customers', sa.Column('onroad_price', sa.DECIMAL(10, 2), nullable=True))