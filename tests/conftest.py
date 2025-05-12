"""Test configuration for Akowe Financial Tracker."""

import os
import sys
import tempfile
import importlib.util
import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal

# Add app root to path to ensure imports work correctly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Patch the import system to handle akowe.* imports
from tests.patch_imports import patch_imports
patch_imports()

# Now we can safely import from akowe.akowe
from akowe.akowe import create_app


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    # Ensure template path is correctly set
    template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "akowe", "templates"))
    
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "WTF_CSRF_ENABLED": False,
            "MAX_CONTENT_LENGTH": 5 * 1024 * 1024,  # 5MB max upload for tests
            "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test;EndpointSuffix=core.windows.net",
            "TEMPLATE_FOLDER": template_path,  # Specify the template path
            "SESSION_ACTIVITY_TIMEOUT": 1800,  # 30 minutes for session timeout
            "PERMANENT_SESSION_LIFETIME": timedelta(hours=6),  # 6 hours for session lifetime
            "REMEMBER_COOKIE_DURATION": timedelta(days=14),  # 14 days for remember cookie
            "SESSION_TYPE": "filesystem",  # For testing we use filesystem sessions
        }
    )
    
    # Explicitly set the template folder
    app.template_folder = template_path

    # Import after creating app to avoid circular imports
    from akowe.models import db
    
    # Store db reference on app for test access
    app.db = db

    # Create the database and the tables
    with app.app_context():
        db.create_all()
        
        # Add config to app
        app.config["COMPANY_NAME"] = "Test Company"
        app.config["COMPANY_EMAIL"] = "test@example.com"
        app.config["COMPANY_PHONE"] = "123-456-7890"
        app.config["COMPANY_ADDRESS"] = "123 Test Street"
        app.config["COMPANY_WEBSITE"] = "https://example.com"
        app.config["COMPANY_TAX_ID"] = "123456789"

    yield app

    # Clean up after the test
    with app.app_context():
        db.session.remove()
        db.drop_all()
    
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

        def login(self, username="test", password="password", remember=False):
            return client.post("/login", data={
                "username": username, 
                "password": password,
                "remember_me": remember
            }, follow_redirects=True)

        def logout(self):
            return client.get("/logout", follow_redirects=True)

    return AuthActions(test_user)


@pytest.fixture
def test_user(app):
    """Create a test user in the database."""
    with app.app_context():
        from akowe.models import db
        from akowe.models.user import User
        
        # First check if the user already exists
        user = User.query.filter_by(username="test").first()
        if user is None:
            user = User(
                username="test",
                email="test@example.com",
                first_name="Test",
                last_name="User",
                hourly_rate=Decimal("120.00"),
                is_admin=False,
                is_active=True,
            )
            user.password = "password"
            db.session.add(user)
            db.session.commit()
        
        # Get a fresh copy of the user
        user_id = user.id
        db.session.flush()
        db.session.expunge_all()  # Detach all objects from session
        
        # Return a freshly loaded user object
        return User.query.get(user_id)


@pytest.fixture
def admin_user(app):
    """Create an admin user in the database."""
    with app.app_context():
        from akowe.models import db
        from akowe.models.user import User
        
        # First check if the admin already exists
        admin = User.query.filter_by(username="admin").first()
        if admin is None:
            admin = User(
                username="admin",
                email="admin@example.com",
                first_name="Admin",
                last_name="User",
                hourly_rate=Decimal("150.00"),
                is_admin=True,
                is_active=True,
            )
            admin.password = "password"
            db.session.add(admin)
            db.session.commit()
        
        # Get a fresh copy of the admin
        admin_id = admin.id
        db.session.flush()
        db.session.expunge_all()
        
        # Return a freshly loaded admin object
        return User.query.get(admin_id)


@pytest.fixture
def sample_income(app, test_user):
    """Create sample income records."""
    with app.app_context():
        from akowe.models import db
        from akowe.models.income import Income
        from akowe.models.client import Client
        
        # Create a client if it doesn't exist
        client = Client.query.filter_by(name="SearchLabs").first()
        if client is None:
            client = Client(
                name="SearchLabs",
                email="contact@searchlabs.com",
                contact_person="John Doe",
                user_id=test_user.id
            )
            db.session.add(client)
            db.session.commit()
        
        # Check if incomes already exist
        existing_count = Income.query.count()
        if existing_count == 0:
            incomes = [
                Income(
                    date=date(2025, 3, 21),
                    amount=Decimal("9040.00"),
                    client="SearchLabs (RAVL)",
                    project="P2025001 - Interac Konek",
                    invoice="Invoice #INV-202503-0002 - SearchLabs",
                    user_id=test_user.id
                ),
                Income(
                    date=date(2025, 2, 21),
                    amount=Decimal("9040.00"),
                    client="SearchLabs (RAVL)",
                    project="P2025001 - Interac Konek",
                    invoice="Invoice #INV-202502-0001 - SearchLabs",
                    user_id=test_user.id
                ),
            ]

            for income in incomes:
                db.session.add(income)

            db.session.commit()
            
            # Fetch fresh copies
            income_ids = [income.id for income in incomes]
            db.session.expunge_all()
            incomes = [Income.query.get(id) for id in income_ids]
        else:
            # Get existing incomes
            incomes = Income.query.all()

        return incomes


@pytest.fixture
def sample_expense(app, test_user):
    """Create sample expense records."""
    with app.app_context():
        from akowe.models import db
        from akowe.models.expense import Expense
        
        # Check if expenses already exist
        existing_count = Expense.query.count()
        if existing_count == 0:
            expenses = [
                Expense(
                    date=date(2025, 4, 12),
                    title="WD Red Plus 12TB NAS Hard Disk Drive",
                    amount=Decimal("386.37"),
                    category="hardware",
                    payment_method="credit_card",
                    status="pending",
                    vendor="Newegg",
                    user_id=test_user.id
                ),
                Expense(
                    date=date(2025, 3, 30),
                    title="Corsair MP600 Pro LPX 2TB M.2 NVMe PCI-e (Gen 4) Internal Solid State Drive",
                    amount=Decimal("251.00"),
                    category="hardware",
                    payment_method="credit_card",
                    status="paid",
                    vendor="BestBuy",
                    user_id=test_user.id
                ),
            ]

            for expense in expenses:
                db.session.add(expense)

            db.session.commit()
            
            # Fetch fresh copies
            expense_ids = [expense.id for expense in expenses]
            db.session.expunge_all()
            expenses = [Expense.query.get(id) for id in expense_ids]
        else:
            # Get existing expenses
            expenses = Expense.query.all()

        return expenses


@pytest.fixture
def sample_timesheet(app, test_user):
    """Create sample timesheet entries."""
    with app.app_context():
        from akowe.models import db
        from akowe.models.timesheet import Timesheet
        from akowe.models.client import Client
        from akowe.models.project import Project
        
        # Create clients if needed
        client1 = Client.query.filter_by(name="SearchLabs").first()
        if not client1:
            client1 = Client(
                name="SearchLabs",
                contact_person="John Search",
                email="john@searchlabs.com",
                user_id=test_user.id
            )
            db.session.add(client1)

        client2 = Client.query.filter_by(name="TechCorp").first()
        if not client2:
            client2 = Client(
                name="TechCorp",
                contact_person="Jane Tech",
                email="jane@techcorp.com",
                user_id=test_user.id
            )
            db.session.add(client2)
        
        db.session.commit()
        
        # Create projects if needed
        project1 = Project.query.filter_by(name="Interac Konek").first()
        if not project1:
            project1 = Project(
                name="Interac Konek",
                code="P2025001",
                description="Interac payment integration",
                client_id=client1.id,
                user_id=test_user.id
            )
            db.session.add(project1)
            
        project2 = Project.query.filter_by(name="Website Redesign").first()
        if not project2:
            project2 = Project(
                name="Website Redesign",
                code="P2025002",
                description="Corporate website redesign",
                client_id=client2.id,
                user_id=test_user.id
            )
            db.session.add(project2)
            
        db.session.commit()
        
        # Check if timesheets already exist
        existing_count = Timesheet.query.count()
        if existing_count == 0:
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
            
            # Fetch fresh copies
            entry_ids = [entry.id for entry in entries]
            db.session.expunge_all()
            entries = [Timesheet.query.get(id) for id in entry_ids]
        else:
            # Get existing entries
            entries = Timesheet.query.all()

        return entries


@pytest.fixture
def sample_invoice(app, test_user, sample_timesheet):
    """Create a sample invoice with timesheet entries."""
    with app.app_context():
        from akowe.models import db
        from akowe.models.invoice import Invoice
        from akowe.models.client import Client
        
        # Check if invoice already exists
        existing_invoice = Invoice.query.filter_by(invoice_number="INV-202504-0001").first()
        if existing_invoice:
            # Return existing invoice
            return existing_invoice
            
        # Get the SearchLabs timesheet entries
        entries = [
            entry
            for entry in sample_timesheet
            if entry.client == "SearchLabs (RAVL)" and entry.status == "pending"
        ]
        
        # Make sure we have SearchLabs client
        client = Client.query.filter_by(name="SearchLabs").first()
        if not client:
            client = Client(
                name="SearchLabs",
                contact_person="John Search",
                email="john@searchlabs.com",
                user_id=test_user.id
            )
            db.session.add(client)
            db.session.commit()

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
        
        # Get a fresh copy
        invoice_id = invoice.id
        db.session.expunge_all()
        
        return Invoice.query.get(invoice_id)