"""Add vehicle_color column to customers table

Revision ID: 8718f3476eca
Revises: a27752974b08
Create Date: 2024-09-15 18:52:01.024611

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8718f3476eca'
down_revision: Union[str, None] = 'a27752974b08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    
    # Add new 'last_name' column
    op.add_column('customers', sa.Column('vehicle_color', sa.String(length=255), nullable=True))


def downgrade():
    # Reverse the 'last_name' column addition
    op.drop_column('customers', 'vehicle_color')

    