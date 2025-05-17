"""Add user_id to income model

Revision ID: 20250418_add_user_id_to_income
Create Date: 2025-04-18
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers
revision = "20250418_add_user_id_to_income"
down_revision = "20250417_add_invoice_relationship_to_income"  # Use the last migration as down_revision


def upgrade():
    # 1. First add the user_id column as nullable
    op.add_column("income", sa.Column("user_id", sa.Integer(), nullable=True))
    
    # 2. Link existing income records to users based on related invoices
    conn = op.get_bind()
    
    # Update income records that have an invoice_id
    conn.execute(
        text(
            """
            UPDATE income i
            SET user_id = inv.user_id
            FROM invoice inv
            WHERE i.invoice_id = inv.id
            AND i.user_id IS NULL
            """
        )
    )
    
    # Get admin user for records without invoices
    admin_id = conn.execute(
        text("SELECT MIN(id) FROM users WHERE is_admin = TRUE")
    ).fetchone()[0]
    
    # Update remaining records
    conn.execute(
        text(f"UPDATE income SET user_id = {admin_id} WHERE user_id IS NULL")
    )
    
    # 3. Make the column non-nullable
    op.alter_column("income", "user_id", nullable=False)
    
    # 4. Create foreign key constraint
    op.create_foreign_key("fk_income_user_id", "income", "users", ["user_id"], ["id"])


def downgrade():
    # 1. Drop the foreign key constraint
    op.drop_constraint("fk_income_user_id", "income", type_="foreignkey")
    
    # 2. Drop the user_id column
    op.drop_column("income", "user_id")