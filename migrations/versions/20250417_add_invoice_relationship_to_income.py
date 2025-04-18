"""Add invoice relationship to income model

Revision ID: 20250417_add_invoice_relationship_to_income
Create Date: 2025-04-17
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text


# revision identifiers
revision = "20250417_add_invoice_relationship_to_income"
down_revision = "20250417_add_income_relationships"


def upgrade():
    # Add invoice_id column to income table as nullable
    op.add_column("income", sa.Column("invoice_id", sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        "fk_income_invoice_id", "income", "invoice", ["invoice_id"], ["id"]
    )
    
    # Attempt to link existing income records to invoices based on invoice number
    # This is a best-effort migration - it might not link all records
    conn = op.get_bind()
    
    # Get all income records that have an invoice field filled
    conn.execute(
        text("""
        UPDATE income i
        SET invoice_id = (
            SELECT inv.id 
            FROM invoice inv 
            WHERE inv.invoice_number = i.invoice
            LIMIT 1
        )
        WHERE i.invoice IS NOT NULL AND i.invoice != ''
        """)
    )


def downgrade():
    # Drop foreign key constraint
    op.drop_constraint("fk_income_invoice_id", "income", type_="foreignkey")
    
    # Drop column
    op.drop_column("income", "invoice_id")