"""Add role_id to users and drop role column

Revision ID: 446184dde12f
Revises: 8e7cac6077e4
Create Date: 2024-09-14 15:44:20.729432

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '446184dde12f'
down_revision: Union[str, None] = '8e7cac6077e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Drop the 'role' column from users table
    op.drop_column('users', 'role')
    
    # Add the 'role_id' column to users table as a foreign key
    op.add_column('users', sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.role_id')))
    

def downgrade():
    # Reverse the changes: add back the 'role' column and drop the 'role_id' column
    op.add_column('users', sa.Column('role', sa.String()))
    
    # Drop the 'role_id' column from users table
    op.drop_column('users', 'role_id')
