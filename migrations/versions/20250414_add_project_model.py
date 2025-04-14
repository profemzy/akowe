"""Add project model and update timesheet relationship

Revision ID: 20250414_add_project_model
Create Date: 2025-04-14
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers
revision = '20250414_add_project_model'
down_revision = '20250414_add_client_model'

def upgrade():
    # Create project table
    op.create_table(
        'project',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='active'),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes
    op.create_index('ix_project_name', 'project', ['name'], unique=False)
    
    # Add project_id column to timesheet table
    op.add_column('timesheet', sa.Column('project_id', sa.Integer(), nullable=False))
    op.create_foreign_key('fk_timesheet_project_id', 'timesheet', 'project', ['project_id'], ['id'])
    
    # Since we don't have existing data, we don't need to migrate anything
    # The project_id column is already set up with a foreign key constraint

def downgrade():
    # Remove foreign key constraint
    op.drop_constraint('fk_timesheet_project_id', 'timesheet', type_='foreignkey')
    
    # Remove project_id column
    op.drop_column('timesheet', 'project_id')
    
    # Drop project table
    op.drop_index('ix_project_name', 'project')
    op.drop_table('project')