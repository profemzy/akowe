"""Test configuration for Akowe Financial Tracker."""

import os
import tempfile
import pytest
from datetime import datetime, date
from decimal import Decimal

from akowe import create_app
from akowe.models import db
from akowe.models.user import User
from akowe.models.income import Income
from akowe.models.expense import Expense
from akowe.models.timesheet import Timesheet
from akowe.models.invoice import Invoice


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "WTF_CSRF_ENABLED": False,
            "MAX_CONTENT_LENGTH": 5 * 1024 * 1024,  # 5MB max upload for tests
            "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test;EndpointSuffix=core.windows.net",
        }
    )

    # Store db reference on app for test access
    app.db = db

    # Create the database and the tables
    with app.app_context():
        db.create_all()

    yield app

    # Close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner for the app."""
    return app.test_cli_runner()


@pytest.fixture
def auth(client, test_user):
    """Authentication helper for tests."""

    class AuthActions:
        def __init__(self, test_user):
            self.test_user = test_user

        def login(self, username="test", password="password"):
            return client.post("/login", data={"username": username, "password": password})

        def logout(self):
            return client.get("/logout")

    return AuthActions(test_user)


@pytest.fixture
def test_user(app):
    """Create a test user in the database."""
    with app.app_context():
        user = User(
            username="test",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hourly_rate=Decimal("120.00"),
            is_admin=False,
        )
        user.password = "password"
        db.session.add(user)
        db.session.commit()

        return user


@pytest.fixture
def admin_user(app):
    """Create an admin user in the database."""
    with app.app_context():
        user = User(
            username="admin",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            is_admin=True,
        )
        user.password = "password"
        db.session.add(user)
        db.session.commit()

        return user


@pytest.fixture
def sample_income(app, test_user):
    """Create sample income records."""
    with app.app_context():
        incomes = [
            Income(
                date=date(2025, 3, 21),
                amount=Decimal("9040.00"),
                client="SearchLabs (RAVL)",
                project="P2025001 - Interac Konek",
                invoice="Invoice #INV-202503-0002 - SearchLabs",
            ),
            Income(
                date=date(2025, 2, 21),
                amount=Decimal("9040.00"),
                client="SearchLabs (RAVL)",
                project="P2025001 - Interac Konek",
                invoice="Invoice #INV-202502-0001 - SearchLabs",
            ),
        ]

        for income in incomes:
            db.session.add(income)

        db.session.commit()

        return incomes


@pytest.fixture
def sample_expense(app, test_user):
    """Create sample expense records."""
    with app.app_context():
        expenses = [
            Expense(
                date=date(2025, 4, 12),
                title="WD Red Plus 12TB NAS Hard Disk Drive",
                amount=Decimal("386.37"),
                category="hardware",
                payment_method="credit_card",
                status="pending",
                vendor="Newegg",
            ),
            Expense(
                date=date(2025, 3, 30),
                title="Corsair MP600 Pro LPX 2TB M.2 NVMe PCI-e (Gen 4) Internal Solid State Drive",
                amount=Decimal("251.00"),
                category="hardware",
                payment_method="credit_card",
                status="paid",
                vendor="BestBuy",
            ),
        ]

        for expense in expenses:
            db.session.add(expense)

        db.session.commit()

        return expenses


@pytest.fixture
def sample_timesheet(app, test_user):
    """Create sample timesheet entries."""
    with app.app_context():
        entries = [
            Timesheet(
                date=date(2025, 4, 15),
                client="SearchLabs (RAVL)",
                project="P2025001 - Interac Konek",
                description="API development and testing",
                hours=Decimal("8.5"),
                hourly_rate=Decimal("125.00"),
                status="pending",
                user_id=test_user.id,
            ),
            Timesheet(
                date=date(2025, 4, 16),
                client="SearchLabs (RAVL)",
                project="P2025001 - Interac Konek",
                description="Frontend integration",
                hours=Decimal("6.0"),
                hourly_rate=Decimal("125.00"),
                status="pending",
                user_id=test_user.id,
            ),
            Timesheet(
                date=date(2025, 4, 17),
                client="TechCorp",
                project="Website Redesign",
                description="UI/UX improvements",
                hours=Decimal("4.5"),
                hourly_rate=Decimal("110.00"),
                status="pending",
                user_id=test_user.id,
            ),
        ]

        for entry in entries:
            db.session.add(entry)

        db.session.commit()

        return entries


@pytest.fixture
def sample_invoice(app, test_user, sample_timesheet):
    """Create a sample invoice with timesheet entries."""
    with app.app_context():
        # Get the SearchLabs timesheet entries
        entries = [
            entry
            for entry in sample_timesheet
            if entry.client == "SearchLabs (RAVL)" and entry.status == "pending"
        ]

        # Create invoice
        invoice = Invoice(
            invoice_number="INV-202504-0001",
            client="SearchLabs (RAVL)",
            company_name="Akowe Test Company",
            issue_date=date(2025, 4, 20),
            due_date=date(2025, 5, 20),
            notes="Payment due within 30 days",
            tax_rate=Decimal("13.00"),
            status="draft",
            user_id=test_user.id,
        )

        db.session.add(invoice)
        db.session.flush()  # Get the ID

        # Link timesheet entries to invoice
        for entry in entries:
            entry.invoice_id = invoice.id
            entry.status = "billed"

        # Calculate invoice totals
        invoice.calculate_totals()

        db.session.commit()

        return invoice
