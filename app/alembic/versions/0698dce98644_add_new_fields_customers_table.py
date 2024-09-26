"""Add new fields customers table

Revision ID: 0698dce98644
Revises: b423aaf8d367
Create Date: 2024-09-26 14:18:51.398061

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0698dce98644'
down_revision: Union[str, None] = 'b423aaf8d367'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Add new columns to the 'customers' table
    op.add_column('customers', sa.Column('total_price', sa.DECIMAL(10, 2), nullable=True))
    op.add_column('customers', sa.Column('finance_amount', sa.DECIMAL(10, 2), nullable=True))
    op.add_column('customers', sa.Column('booking', sa.DECIMAL(10, 2), nullable=True))
    op.add_column('customers', sa.Column('insurance', sa.DECIMAL(10, 2), nullable=True))
    op.add_column('customers', sa.Column('tp_registration', sa.DECIMAL(10, 2), nullable=True))
    op.add_column('customers', sa.Column('man_accessories', sa.DECIMAL(10, 2), nullable=True))
    op.add_column('customers', sa.Column('optional_accessories', sa.DECIMAL(10, 2), nullable=True))
    op.add_column('customers', sa.Column('alternate_phone_number', sa.String(), nullable=True))
    op.add_column('customers', sa.Column('dob', sa.Date(), nullable=True))
    op.add_column('customers', sa.Column('nominee', sa.String(), nullable=True))
    op.add_column('customers', sa.Column('relation', sa.String(), nullable=True))
    op.add_column('customers', sa.Column('pin_code', sa.String(), nullable=True))


def downgrade():
    # Remove the columns from the 'customers' table
    op.drop_column('customers', 'total_price')
    op.drop_column('customers', 'finance_amount')
    op.drop_column('customers', 'booking')
    op.drop_column('customers', 'insurance')
    op.drop_column('customers', 'tp_registration')
    op.drop_column('customers', 'man_accessories')
    op.drop_column('customers', 'optional_accessories')
    op.drop_column('customers', 'alternate_phone_number')
    op.drop_column('customers', 'dob')
    op.drop_column('customers', 'nominee')
    op.drop_column('customers', 'relation')
    op.drop_column('customers', 'pin_code')
