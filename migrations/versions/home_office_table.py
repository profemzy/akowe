"""Add home_office table

Revision ID: home_office_table
Revises: 
Create Date: 2025-05-12 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'home_office_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Get the database dialect
    connection = op.get_bind()
    dialect = connection.dialect.name

    # Create home_office table with the appropriate SQL for each dialect
    if dialect == 'sqlite':
        op.create_table('home_office',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('tax_year', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('total_home_area', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('office_area', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('area_unit', sa.String(length=20), nullable=True, default='sq_ft'),
            sa.Column('rent', sa.Numeric(precision=10, scale=2), nullable=True, default=0.00),
            sa.Column('mortgage_interest', sa.Numeric(precision=10, scale=2), nullable=True, default=0.00),
            sa.Column('property_tax', sa.Numeric(precision=10, scale=2), nullable=True, default=0.00),
            sa.Column('home_insurance', sa.Numeric(precision=10, scale=2), nullable=True, default=0.00),
            sa.Column('utilities', sa.Numeric(precision=10, scale=2), nullable=True, default=0.00),
            sa.Column('maintenance', sa.Numeric(precision=10, scale=2), nullable=True, default=0.00),
            sa.Column('internet', sa.Numeric(precision=10, scale=2), nullable=True, default=0.00),
            sa.Column('phone', sa.Numeric(precision=10, scale=2), nullable=True, default=0.00),
            sa.Column('business_use_percentage', sa.Numeric(precision=5, scale=2), nullable=True, default=0.00),
            sa.Column('is_primary_income', sa.Boolean(), nullable=True, default=1),
            sa.Column('hours_per_week', sa.Integer(), nullable=True, default=0),
            sa.Column('calculation_method', sa.String(length=20), nullable=True, default='percentage'),
            sa.Column('simplified_rate', sa.Numeric(precision=10, scale=2), nullable=True, default=0.00),
            sa.Column('total_deduction', sa.Numeric(precision=10, scale=2), nullable=True, default=0.00),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    else:  # PostgreSQL or other
        op.create_table('home_office',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('tax_year', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('total_home_area', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('office_area', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('area_unit', sa.String(length=20), nullable=True, server_default='sq_ft'),
            sa.Column('rent', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0.00'),
            sa.Column('mortgage_interest', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0.00'),
            sa.Column('property_tax', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0.00'),
            sa.Column('home_insurance', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0.00'),
            sa.Column('utilities', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0.00'),
            sa.Column('maintenance', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0.00'),
            sa.Column('internet', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0.00'),
            sa.Column('phone', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0.00'),
            sa.Column('business_use_percentage', sa.Numeric(precision=5, scale=2), nullable=True, server_default='0.00'),
            sa.Column('is_primary_income', sa.Boolean(), nullable=True, server_default='TRUE'),
            sa.Column('hours_per_week', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('calculation_method', sa.String(length=20), nullable=True, server_default='percentage'),
            sa.Column('simplified_rate', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0.00'),
            sa.Column('total_deduction', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0.00'),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Optionally add an index on user_id and tax_year for quicker lookups
    op.create_index(op.f('ix_home_office_user_id'), 'home_office', ['user_id'], unique=False)
    op.create_index(op.f('ix_home_office_tax_year'), 'home_office', ['tax_year'], unique=False)


def downgrade():
    # Drop the home_office table
    op.drop_index(op.f('ix_home_office_tax_year'), table_name='home_office')
    op.drop_index(op.f('ix_home_office_user_id'), table_name='home_office')
    op.drop_table('home_office')