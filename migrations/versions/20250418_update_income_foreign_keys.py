"""Update income with client and project foreign keys

Revision ID: 20250418_update_income_foreign_keys
Create Date: 2025-04-18
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, ForeignKey, and_, table, column

# revision identifiers
revision = "20250418_update_income_foreign_keys"
down_revision = "20250414_add_clients_and_projects"  # Use the last migration as down_revision


def upgrade():
    # 1. First add client_id and project_id columns as nullable
    op.add_column("income", sa.Column("client_id", sa.Integer(), nullable=True))
    op.add_column("income", sa.Column("project_id", sa.Integer(), nullable=True))
    
    # Get database connection
    conn = op.get_bind()
    
    # 2. Get all unique income records with client and project names
    income_records = conn.execute(
        text("""
            SELECT DISTINCT i.client, i.project, i.user_id 
            FROM income i
            JOIN users u ON i.user_id = u.id
        """)
    ).fetchall()
    
    # 3. Process each unique client and project combination
    for client_name, project_name, user_id in income_records:
        # Check if client exists
        client_id = conn.execute(
            text(f"SELECT id FROM client WHERE name = :name"),
            {"name": client_name}
        ).scalar()
        
        # If client doesn't exist, create it
        if not client_id:
            conn.execute(
                text("""
                    INSERT INTO client (name, user_id, created_at, updated_at)
                    VALUES (:name, :user_id, NOW(), NOW())
                """),
                {"name": client_name, "user_id": user_id}
            )
            
            # Get the newly created client's ID
            client_id = conn.execute(
                text(f"SELECT id FROM client WHERE name = :name"),
                {"name": client_name}
            ).scalar()
        
        # Check if project exists for this client
        project_id = conn.execute(
            text("""
                SELECT p.id 
                FROM project p
                JOIN client c ON p.client_id = c.id
                WHERE p.name = :project_name AND c.id = :client_id
            """),
            {"project_name": project_name, "client_id": client_id}
        ).scalar()
        
        # If project doesn't exist, create it
        if not project_id:
            conn.execute(
                text("""
                    INSERT INTO project (name, status, client_id, user_id, created_at, updated_at)
                    VALUES (:name, 'active', :client_id, :user_id, NOW(), NOW())
                """),
                {"name": project_name, "client_id": client_id, "user_id": user_id}
            )
            
            # Get the newly created project's ID
            project_id = conn.execute(
                text("""
                    SELECT p.id 
                    FROM project p
                    JOIN client c ON p.client_id = c.id
                    WHERE p.name = :project_name AND c.id = :client_id
                """),
                {"project_name": project_name, "client_id": client_id}
            ).scalar()
        
        # Update income records with the client_id and project_id
        conn.execute(
            text("""
                UPDATE income
                SET client_id = :client_id, project_id = :project_id
                WHERE client = :client_name AND project = :project_name
            """),
            {
                "client_id": client_id,
                "project_id": project_id,
                "client_name": client_name,
                "project_name": project_name
            }
        )
    
    # 4. Create foreign key constraints
    op.create_foreign_key(
        "fk_income_client_id", "income", "client", ["client_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_income_project_id", "income", "project", ["project_id"], ["id"]
    )
    
    # 5. Make foreign key columns non-nullable now that they have been populated
    op.alter_column("income", "client_id", nullable=False)
    op.alter_column("income", "project_id", nullable=False)
    
    # 6. Add user_id to income if not already there, which is needed for the relationships
    # First check if user_id column exists
    has_user_id = False
    for column in sa.inspect(op.get_bind()).get_columns("income"):
        if column["name"] == "user_id":
            has_user_id = True
            break
    
    # Add user_id column if it doesn't exist
    if not has_user_id:
        op.add_column("income", sa.Column("user_id", sa.Integer(), nullable=True))
        
        # Update user_id based on project's user_id
        conn.execute(
            text("""
                UPDATE income i
                SET user_id = (
                    SELECT p.user_id
                    FROM project p
                    WHERE p.id = i.project_id
                )
                WHERE i.user_id IS NULL
            """)
        )
        
        # Create foreign key constraint for user_id
        op.create_foreign_key(
            "fk_income_user_id", "income", "users", ["user_id"], ["id"]
        )
        
        # Make user_id non-nullable
        op.alter_column("income", "user_id", nullable=False)
    
    # 7. Keep the original string columns for now, but they could be dropped later
    # op.drop_column("income", "client")
    # op.drop_column("income", "project")


def downgrade():
    # 1. If the client and project string columns were dropped, add them back
    # op.add_column("income", sa.Column("client", sa.String(255), nullable=True))
    # op.add_column("income", sa.Column("project", sa.String(255), nullable=True))
    
    # 2. Copy data back from the related tables to the string columns
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE income i
            SET client = (SELECT name FROM client c WHERE c.id = i.client_id),
                project = (SELECT name FROM project p WHERE p.id = i.project_id)
        """)
    )
    
    # 3. Make the string columns non-nullable if they were before
    # op.alter_column("income", "client", nullable=False)
    # op.alter_column("income", "project", nullable=False)
    
    # 4. Drop the foreign key constraints
    op.drop_constraint("fk_income_project_id", "income", type_="foreignkey")
    op.drop_constraint("fk_income_client_id", "income", type_="foreignkey")
    
    # 5. Drop the foreign key columns
    op.drop_column("income", "project_id")
    op.drop_column("income", "client_id")
    
    # 6. Drop user_id if it was added in this migration
    # First check if income has foreign key to users
    has_user_id_fk = False
    for fk in sa.inspect(op.get_bind()).get_foreign_keys("income"):
        if fk["referred_table"] == "users" and "user_id" in fk["constrained_columns"]:
            has_user_id_fk = True
            break
    
    if has_user_id_fk:
        op.drop_constraint("fk_income_user_id", "income", type_="foreignkey")
        op.drop_column("income", "user_id")