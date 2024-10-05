"""Add customer_sign coulumn to customers table

Revision ID: 4df77bc21033
Revises: a0a0d0778823
Create Date: 2024-10-05 19:15:07.302567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4df77bc21033'
down_revision: Union[str, None] = 'a0a0d0778823'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('customers', sa.Column('customer_sign', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('customers','customer_sign')
