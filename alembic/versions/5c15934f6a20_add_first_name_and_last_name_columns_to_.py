"""Add first_name and last_name columns to Customer

Revision ID: 5c15934f6a20
Revises: 69b9958cf1cb
Create Date: 2024-09-16 00:17:22.776393

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5c15934f6a20'
down_revision: Union[str, None] = '69b9958cf1cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    
    # Add new 'last_name' column
    op.add_column('customers', sa.Column('first_name', sa.String(length=255), nullable=True))
    op.add_column('customers', sa.Column('last_name', sa.String(length=255), nullable=True))



def downgrade():
    # Reverse the 'last_name' column addition
    op.drop_column('customers', 'first_name')
    op.drop_column('customers', 'last_name')


    