"""Add client and project models

Revision ID: 20250414_add_clients_and_projects
Create Date: 2025-04-14
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers
revision = '20250414_add_clients_and_projects'
down_revision = '20250413_add_timesheet_and_invoice'  # Use the last migration as down_revision

def upgrade():
    # 1. First create the client table
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
    
    # Add client name index
    op.create_index('ix_client_name', 'client', ['name'], unique=True)
    
    # 2. Create default admin client for existing data (if any)
    conn = op.get_bind()
    conn.execute(
        text("""
            INSERT INTO client (name, user_id, created_at, updated_at)
            SELECT 'Default Client', MIN(id), NOW(), NOW() FROM users WHERE is_admin = TRUE
        """)
    )
    
    # Get ID of the default client
    default_client_id = conn.execute(text("SELECT id FROM client WHERE name = 'Default Client'")).fetchone()[0]
    
    # 3. Add client_id column to invoice and timesheet as nullable first
    op.add_column('invoice', sa.Column('client_id', sa.Integer(), nullable=True))
    op.add_column('timesheet', sa.Column('client_id', sa.Integer(), nullable=True))
    
    # 4. Update existing records to use the default client
    conn.execute(
        text(f"UPDATE invoice SET client_id = {default_client_id}")
    )
    conn.execute(
        text(f"UPDATE timesheet SET client_id = {default_client_id}")
    )
    
    # 5. Now create foreign key constraints
    op.create_foreign_key('fk_invoice_client_id', 'invoice', 'client', ['client_id'], ['id'])
    op.create_foreign_key('fk_timesheet_client_id', 'timesheet', 'client', ['client_id'], ['id'])
    
    # 6. Make columns non-nullable
    op.alter_column('invoice', 'client_id', nullable=False)
    op.alter_column('timesheet', 'client_id', nullable=False)
    
    # 7. Create project table
    op.create_table(
        'project',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add project name index
    op.create_index('ix_project_name', 'project', ['name'], unique=False)
    
    # 8. Create default project for existing timesheet entries
    conn.execute(
        text(f"""
            INSERT INTO project (name, description, status, client_id, user_id, created_at, updated_at)
            SELECT 'Default Project', 'Created during migration', 'active', {default_client_id}, 
                   MIN(user_id), NOW(), NOW() 
            FROM timesheet
            GROUP BY user_id
        """)
    )
    
    # 9. Add project_id column to timesheet as nullable first
    op.add_column('timesheet', sa.Column('project_id', sa.Integer(), nullable=True))
    
    # 10. Update existing records with default project
    default_projects = conn.execute(
        text("SELECT id, user_id FROM project WHERE name = 'Default Project'")
    ).fetchall()
    
    for project_id, user_id in default_projects:
        conn.execute(
            text(f"UPDATE timesheet SET project_id = {project_id} WHERE user_id = {user_id}")
        )
    
    # 11. Create foreign key constraint
    op.create_foreign_key('fk_timesheet_project_id', 'timesheet', 'project', ['project_id'], ['id'])
    
    # 12. Make column non-nullable
    op.alter_column('timesheet', 'project_id', nullable=False)
    
    # 13. Drop original columns if needed (uncomment if you want to remove them)
    # op.drop_column('invoice', 'client')
    # op.drop_column('timesheet', 'client')
    # op.drop_column('timesheet', 'project')

def downgrade():
    # 1. Drop project-related constraints and columns
    op.drop_constraint('fk_timesheet_project_id', 'timesheet', type_='foreignkey')
    op.drop_column('timesheet', 'project_id')
    
    # 2. Drop client-related constraints and columns
    op.drop_constraint('fk_invoice_client_id', 'invoice', type_='foreignkey')
    op.drop_constraint('fk_timesheet_client_id', 'timesheet', type_='foreignkey')
    op.drop_column('invoice', 'client_id')
    op.drop_column('timesheet', 'client_id')
    
    # 3. Drop project table
    op.drop_index('ix_project_name', 'project')
    op.drop_table('project')
    
    # 4. Drop client table
    op.drop_index('ix_client_name', 'client')
    op.drop_table('client')