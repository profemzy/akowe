"""Add receipt fields to expense model

Revision ID: 20250412_add_receipt
Revises: 
Create Date: 2025-04-12

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250412_add_receipt"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("expense", sa.Column("receipt_blob_name", sa.String(255), nullable=True))
    op.add_column("expense", sa.Column("receipt_url", sa.String(1024), nullable=True))


def downgrade():
    op.drop_column("expense", "receipt_url")
    op.drop_column("expense", "receipt_blob_name")
