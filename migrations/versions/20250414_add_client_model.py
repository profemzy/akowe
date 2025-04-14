"""Add client model and establish relationships

Revision ID: 20250414_add_client_model
Create Date: 2025-04-14
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers
revision = '20250414_add_client_model'
down_revision = '20250413_add_timesheet_and_invoice'

def upgrade():
    # Create client table
    op.create_table(
        'client',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('contact_person', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes
    op.create_index('ix_client_name', 'client', ['name'], unique=True)
    
    # Add client_id columns to invoice and timesheet tables
    op.add_column('invoice', sa.Column('client_id', sa.Integer(), nullable=False))
    op.create_foreign_key('fk_invoice_client_id', 'invoice', 'client', ['client_id'], ['id'])
    
    op.add_column('timesheet', sa.Column('client_id', sa.Integer(), nullable=False))
    op.create_foreign_key('fk_timesheet_client_id', 'timesheet', 'client', ['client_id'], ['id'])
    
    # Since we don't have existing data, we don't need to migrate anything
    # The client_id columns are already set up with foreign key constraints

def downgrade():
    # Remove foreign key constraints
    op.drop_constraint('fk_invoice_client_id', 'invoice', type_='foreignkey')
    op.drop_constraint('fk_timesheet_client_id', 'timesheet', type_='foreignkey')
    
    # Remove client_id columns
    op.drop_column('invoice', 'client_id')
    op.drop_column('timesheet', 'client_id')
    
    # Drop client table
    op.drop_index('ix_client_name', 'client')
    op.drop_table('client')