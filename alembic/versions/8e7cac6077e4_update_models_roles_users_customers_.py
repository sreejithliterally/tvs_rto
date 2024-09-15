"""Update models: roles, users, customers, transactions, and finance options

Revision ID: 8e7cac6077e4
Revises: b55d7f3b9e62
Create Date: 2024-09-14 14:48:15.806692

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8e7cac6077e4'
down_revision: Union[str, None] = 'b55d7f3b9e62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Creating new tables first ###
    
    # Create 'roles' table
    op.create_table('roles',
        sa.Column('role_id', sa.Integer(), primary_key=True, index=True),
        sa.Column('role_name', sa.String(), unique=True)
    )

    # Create 'finance_options' table
    op.create_table('finance_options',
        sa.Column('finance_id', sa.Integer(), primary_key=True, index=True),
        sa.Column('company_name', sa.String(), unique=True),
        sa.Column('details', sa.String())
    )

    # ### Altering columns in existing tables ###
    
    # Rename 'id' to 'user_id' in 'users' table
    op.alter_column('users', 'id', new_column_name='user_id')

    # Rename 'id' to 'branch_id' in 'branches' table
    op.alter_column('branches', 'id', new_column_name='branch_id')

    # Rename 'photo_adhaar' to 'photo_adhaar_front' in 'customers' table
    op.alter_column('customers', 'photo_adhaar', new_column_name='photo_adhaar_front')

    op.alter_column('customers', 'id', new_column_name='customer_id')
    # ### Adding new columns ###
    
    # Adding new columns to 'customers' table
    op.add_column('customers', sa.Column('photo_adhaar_back', sa.String(), nullable=True))
    op.add_column('customers', sa.Column('sales_executive_id', sa.Integer(), sa.ForeignKey('users.user_id')))
    op.add_column('customers', sa.Column('vehicle_name', sa.String()))
    op.add_column('customers', sa.Column('vehicle_variant', sa.String()))
    op.add_column('customers', sa.Column('ex_showroom_price', sa.DECIMAL(10, 2)))
    op.add_column('customers', sa.Column('tax', sa.DECIMAL(10, 2)))
    op.add_column('customers', sa.Column('onroad_price', sa.DECIMAL(10, 2)))
    op.add_column('customers', sa.Column('finance_id', sa.Integer(), sa.ForeignKey('finance_options.finance_id'), nullable=True))

    # Create 'transactions' table
    op.create_table('transactions',
        sa.Column('transaction_id', sa.Integer(), primary_key=True, index=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.customer_id')),
        sa.Column('finance_id', sa.Integer(), sa.ForeignKey('finance_options.finance_id'), nullable=True),
        sa.Column('branch_id', sa.Integer(), sa.ForeignKey('branches.branch_id')),
        sa.Column('sales_executive_id', sa.Integer(), sa.ForeignKey('users.user_id')),
        sa.Column('total_price', sa.DECIMAL(10, 2)),
        sa.Column('payment_status', sa.String(), default='Pending'),
        sa.Column('payment_verified', sa.Boolean(), default=False),
        sa.Column('finance_verified', sa.Boolean(), default=False),
        sa.Column('rto_submitted', sa.Boolean(), default=False),
        sa.Column('transaction_date', sa.DateTime(), default=sa.func.now())
    )


def downgrade() -> None:
    # ### Drop newly created tables ###
    op.drop_table('transactions')
    op.drop_table('finance_options')
    op.drop_table('roles')

    # ### Remove added columns ###
    op.drop_column('customers', 'photo_adhaar_back')
    op.drop_column('customers', 'sales_executive_id')
    op.drop_column('customers', 'vehicle_name')
    op.drop_column('customers', 'vehicle_variant')
    op.drop_column('customers', 'ex_showroom_price')
    op.drop_column('customers', 'tax')
    op.drop_column('customers', 'onroad_price')
    op.drop_column('customers', 'finance_id')

    # ### Revert column renames ###
    op.alter_column('customers', 'photo_adhaar_front', new_column_name='photo_adhaar')
    op.alter_column('users', 'user_id', new_column_name='id')
    op.alter_column('branches', 'branch_id', new_column_name='id')
