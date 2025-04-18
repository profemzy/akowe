"""Tests for the import service."""

import pytest
import os
import tempfile
from datetime import date
from decimal import Decimal

from akowe.models.income import Income
from akowe.models.expense import Expense
from akowe.services.import_service import ImportService


@pytest.fixture
def income_csv_file():
    """Create a temporary CSV file with income data."""
    content = """date,amount,client,project,invoice
2025-06-21,8000.00,ImportClient,ImportProject,ImportInvoice
2025-07-15,9000.00,Client2,Project2,Invoice2
2025-08-10,7500.00,Client3,Project3,Invoice3"""

    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w") as f:
        f.write(content)

    yield path

    # Cleanup
    os.unlink(path)


@pytest.fixture
def expense_csv_file():
    """Create a temporary CSV file with expense data."""
    content = """date,title,amount,category,payment_method,status,vendor
2025-06-21,Expense1,199.99,software,debit_card,pending,Vendor1
2025-07-15,Expense2,299.99,hardware,credit_card,paid,Vendor2
2025-08-10,Expense3,399.99,travel,bank_transfer,paid,Vendor3"""

    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w") as f:
        f.write(content)

    yield path

    # Cleanup
    os.unlink(path)


def test_import_income_csv(app, income_csv_file):
    """Test importing income from a CSV file."""
    with app.app_context():
        # Count initial records
        initial_count = Income.query.count()

        # Import the CSV
        records, count = ImportService.import_income_csv(income_csv_file)

        # Verify records imported
        assert count == 3
        assert len(records) == 3
        assert Income.query.count() == initial_count + 3

        # Check specific record
        income = Income.query.filter_by(client="ImportClient").first()
        assert income is not None
        assert income.date == date(2025, 6, 21)
        assert income.amount == Decimal("8000.00")
        assert income.project == "ImportProject"
        assert income.invoice == "ImportInvoice"


def test_import_expense_csv(app, expense_csv_file):
    """Test importing expenses from a CSV file."""
    with app.app_context():
        # Count initial records
        initial_count = Expense.query.count()

        # Import the CSV
        records, count = ImportService.import_expense_csv(expense_csv_file)

        # Verify records imported
        assert count == 3
        assert len(records) == 3
        assert Expense.query.count() == initial_count + 3

        # Check specific record
        expense = Expense.query.filter_by(title="Expense1").first()
        assert expense is not None
        assert expense.date == date(2025, 6, 21)
        assert expense.amount == Decimal("199.99")
        assert expense.category == "software"
        assert expense.payment_method == "debit_card"
        assert expense.status == "pending"
        assert expense.vendor == "Vendor1"


def test_import_income_invalid_csv(app):
    """Test importing from an invalid CSV file."""
    with app.app_context():
        # Create an invalid CSV file
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w") as f:
            f.write("invalid,csv,format\n1,2,3")

        # Import should fail
        with pytest.raises(Exception):
            ImportService.import_income_csv(path)

        # Cleanup
        os.unlink(path)


def test_import_expense_rollback_on_error(app):
    """Test that the transaction is rolled back if an error occurs."""
    with app.app_context():
        # Create a CSV with invalid data in the middle
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w") as f:
            f.write(
                """date,title,amount,category,payment_method,status,vendor
2025-06-21,Valid1,199.99,software,debit_card,pending,Vendor1
2025-07-15,Invalid,not_a_number,hardware,credit_card,paid,Vendor2
2025-08-10,Valid2,399.99,travel,bank_transfer,paid,Vendor3"""
            )

        # Initial count
        initial_count = Expense.query.count()

        # Import should fail
        with pytest.raises(Exception):
            ImportService.import_expense_csv(path)

        # Verify no records were added due to rollback
        assert Expense.query.count() == initial_count

        # Cleanup
        os.unlink(path)
