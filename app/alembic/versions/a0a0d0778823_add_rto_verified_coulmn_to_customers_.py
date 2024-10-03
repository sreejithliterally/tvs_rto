"""Add rto verified coulmn to customers table

Revision ID: a0a0d0778823
Revises: 4fe7e7f736d7
Create Date: 2024-10-03 15:50:16.172124

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0a0d0778823'
down_revision: Union[str, None] = '4fe7e7f736d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('customers', sa.Column('rto_verified', sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column('customers','rto_verified')
