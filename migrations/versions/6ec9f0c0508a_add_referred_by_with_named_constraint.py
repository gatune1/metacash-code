"""Add referred_by with named constraint

Revision ID: 6ec9f0c0508a
Revises: 
Create Date: 2025-09-16 01:43:39.531170
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6ec9f0c0508a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Alter payment table: make user_id non-nullable
    with op.batch_alter_table('payment', schema=None) as batch_op:
        batch_op.alter_column(
            'user_id',
            existing_type=sa.INTEGER(),
            nullable=False
        )

    # Alter user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        # Add referred_by column
        batch_op.add_column(sa.Column('referred_by', sa.Integer(), nullable=True))
        
        # Create named foreign key constraint
        batch_op.create_foreign_key(
            'fk_user_referred_by',  # name of the foreign key
            'user',                 # remote table
            ['referred_by'],        # local column
            ['id']                  # remote column
        )
        
        # KEEP mpesa_code column (do NOT drop it)


def downgrade():
    # Revert user table changes
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('fk_user_referred_by', type_='foreignkey')
        batch_op.drop_column('referred_by')
        # mpesa_code is not touched

    # Revert payment table changes
    with op.batch_alter_table('payment', schema=None) as batch_op:
        batch_op.alter_column(
            'user_id',
            existing_type=sa.INTEGER(),
            nullable=True
        )
