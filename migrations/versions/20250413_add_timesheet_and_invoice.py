"""Add timesheet and invoice systems

Revision ID: 20250413_add_timesheet_and_invoice
Create Date: 2025-04-13
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic
revision = "20250413_add_timesheet_and_invoice"
down_revision = "20250412_add_receipt_fields_to_expense"
branch_labels = None
depends_on = None


def upgrade():
    # Check if User table has the hourly_rate column already
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [column["name"] for column in inspector.get_columns("users")]

    # Add hourly_rate to User model if it doesn't exist
    if "hourly_rate" not in columns:
        op.add_column("users", sa.Column("hourly_rate", sa.Numeric(10, 2), nullable=True))

    # Create Invoice table first (to avoid foreign key issues)
    op.create_table(
        "invoice",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("invoice_number", sa.String(50), nullable=False, unique=True),
        sa.Column("client", sa.String(255), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("issue_date", sa.Date, nullable=False),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("tax_rate", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("total", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("sent_date", sa.DateTime, nullable=True),
        sa.Column("paid_date", sa.DateTime, nullable=True),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column("payment_reference", sa.String(100), nullable=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.current_timestamp()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.current_timestamp(),
            onupdate=sa.func.current_timestamp(),
        ),
    )

    # Create Timesheet table (now we can reference invoice.id)
    op.create_table(
        "timesheet",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("client", sa.String(255), nullable=False),
        sa.Column("project", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("hours", sa.Numeric(5, 2), nullable=False),
        sa.Column("hourly_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("invoice_id", sa.Integer, sa.ForeignKey("invoice.id"), nullable=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.current_timestamp()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.current_timestamp(),
            onupdate=sa.func.current_timestamp(),
        ),
    )

    # Create indexes
    op.create_index("ix_timesheet_date", "timesheet", ["date"])
    op.create_index("ix_timesheet_client", "timesheet", ["client"])
    op.create_index("ix_timesheet_status", "timesheet", ["status"])
    op.create_index("ix_timesheet_user_id", "timesheet", ["user_id"])
    op.create_index("ix_timesheet_invoice_id", "timesheet", ["invoice_id"])

    op.create_index("ix_invoice_invoice_number", "invoice", ["invoice_number"])
    op.create_index("ix_invoice_client", "invoice", ["client"])
    op.create_index("ix_invoice_issue_date", "invoice", ["issue_date"])
    op.create_index("ix_invoice_status", "invoice", ["status"])
    op.create_index("ix_invoice_user_id", "invoice", ["user_id"])


def downgrade():
    # Drop indexes
    op.drop_index("ix_timesheet_date", "timesheet")
    op.drop_index("ix_timesheet_client", "timesheet")
    op.drop_index("ix_timesheet_status", "timesheet")
    op.drop_index("ix_timesheet_user_id", "timesheet")
    op.drop_index("ix_timesheet_invoice_id", "timesheet")

    op.drop_index("ix_invoice_invoice_number", "invoice")
    op.drop_index("ix_invoice_client", "invoice")
    op.drop_index("ix_invoice_issue_date", "invoice")
    op.drop_index("ix_invoice_status", "invoice")
    op.drop_index("ix_invoice_user_id", "invoice")

    # Drop tables
    op.drop_table("timesheet")
    op.drop_table("invoice")

    # Drop hourly_rate column from User model
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [column["name"] for column in inspector.get_columns("users")]

    if "hourly_rate" in columns:
        op.drop_column("users", "hourly_rate")
