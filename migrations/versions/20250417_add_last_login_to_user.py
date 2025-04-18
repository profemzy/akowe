"""add last_login to user

Revision ID: 20250417_add_last_login_to_user
Revises: 20250418_add_user_id_to_income
Create Date: 2025-04-17 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250417_add_last_login_to_user'
down_revision = '20250418_add_user_id_to_income'
branch_labels = None
depends_on = None


def upgrade():
    # Add last_login column to users table
    op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))


def downgrade():
    # Remove last_login column from users table
    op.drop_column('users', 'last_login')