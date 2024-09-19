"""Add address, phone number, branch manager to Branch model

Revision ID: b423aaf8d367
Revises: ccf92cf8aa3b
Create Date: 2024-09-19 15:25:16.762614

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b423aaf8d367'
down_revision: Union[str, None] = 'd4bb39f271e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add new columns to branches table
    op.add_column('branches', sa.Column('address', sa.String(), nullable=True))
    op.add_column('branches', sa.Column('phone_number', sa.String(), nullable=True))
    op.add_column('branches', sa.Column('branch_manager', sa.String(), nullable=True))


def downgrade():
    # Remove columns in case of downgrade
    op.drop_column('branches', 'branch_manager')
    op.drop_column('branches', 'phone_number')
    op.drop_column('branches', 'address')
