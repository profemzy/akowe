"""Add client and project relationships to income model

Revision ID: 20250417_add_income_relationships
Create Date: 2025-04-17
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text


# revision identifiers
revision = "20250417_add_income_relationships"
down_revision = "20250414_add_clients_and_projects"  # Use the last migration as down_revision


def upgrade():
    # 1. Add client_id and project_id columns to income table as nullable
    # This ensures backwards compatibility with existing code that doesn't use the relationships
    op.add_column("income", sa.Column("client_id", sa.Integer(), nullable=True))
    op.add_column("income", sa.Column("project_id", sa.Integer(), nullable=True))

    # 2. Add foreign key constraints
    op.create_foreign_key("fk_income_client_id", "income", "client", ["client_id"], ["id"])
    op.create_foreign_key("fk_income_project_id", "income", "project", ["project_id"], ["id"])


def downgrade():
    # 1. Drop foreign key constraints
    op.drop_constraint("fk_income_project_id", "income", type_="foreignkey")
    op.drop_constraint("fk_income_client_id", "income", type_="foreignkey")
    
    # 2. Drop columns
    op.drop_column("income", "project_id")
    op.drop_column("income", "client_id")