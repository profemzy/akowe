"""Alternative test configuration with comprehensive template mocking."""

import os
import sys
import tempfile
import importlib.util
import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import patch
from flask import render_template_string

# Add the project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load create_app directly from the file
spec = importlib.util.spec_from_file_location(
    "akowe_app", 
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "akowe", "akowe.py"))
)
akowe_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(akowe_module)
create_app = akowe_module.create_app

# Template mocking setup
TEMPLATE_MOCKS = {
    'auth/login.html': '<html><body><h1>Sign in to your account</h1><form></form></body></html>',
    'auth/change_password.html': '<html><body><h1>Change Password</h1><form></form></body></html>',
    
    # Dashboard templates
    'dashboard/index.html': '<html><body><h1>Dashboard</h1><div class="stats"></div></body></html>',
    
    # Admin templates
    'admin/index.html': '<html><body><h1>Admin Dashboard</h1></body></html>',
    'admin/users.html': '<html><body><h1>User Management</h1></body></html>',
    'admin/edit_user.html': '<html><body><h1>Edit User</h1></body></html>',
    'admin/new_user.html': '<html><body><h1>Create User</h1></body></html>',
    'admin/stats.html': '<html><body><h1>Statistics</h1></body></html>',
    'admin/logs.html': '<html><body><h1>System Logs</h1></body></html>',
    'admin/settings.html': '<html><body><h1>System Settings</h1></body></html>',
    'admin/data.html': '<html><body><h1>System Data</h1></body></html>',
    
    # Client templates
    'client/index.html': '<html><body><h1>Clients</h1></body></html>',
    'client/new.html': '<html><body><h1>New Client</h1></body></html>',
    'client/edit.html': '<html><body><h1>Edit Client</h1></body></html>',
    'client/view.html': '<html><body><h1>View Client</h1></body></html>',
    
    # Expense templates
    'expense/index.html': '<html><body><h1>Expenses</h1></body></html>',
    'expense/new.html': '<html><body><h1>New Expense</h1></body></html>',
    'expense/edit.html': '<html><body><h1>Edit Expense</h1></body></html>',
    'expense/analysis.html': '<html><body><h1>Expense Analysis</h1></body></html>',
    'expense/import.html': '<html><body><h1>Import Expenses</h1></body></html>',
    'expense/import_success.html': '<html><body><h1>Import Success</h1></body></html>',
    
    # Income templates
    'income/index.html': '<html><body><h1>Income</h1></body></html>',
    'income/new.html': '<html><body><h1>New Income</h1></body></html>',
    'income/edit.html': '<html><body><h1>Edit Income</h1></body></html>',
    'income/import.html': '<html><body><h1>Import Income</h1></body></html>',
    'income/import_success.html': '<html><body><h1>Import Success</h1></body></html>',
    'income/projects_dropdown.html': '<select name="project"></select>',
    
    # Invoice templates
    'invoice/index.html': '<html><body><h1>Invoices</h1></body></html>',
    'invoice/new.html': '<html><body><h1>New Invoice</h1></body></html>',
    'invoice/edit.html': '<html><body><h1>Edit Invoice</h1></body></html>',
    'invoice/view.html': '<html><body><h1>View Invoice</h1></body></html>',
    'invoice/print.html': '<html><body><h1>Print Invoice</h1></body></html>',
    
    # Project templates
    'project/index.html': '<html><body><h1>Projects</h1></body></html>',
    'project/new.html': '<html><body><h1>New Project</h1></body></html>',
    'project/edit.html': '<html><body><h1>Edit Project</h1></body></html>',
    'project/view.html': '<html><body><h1>View Project</h1></body></html>',
    
    # Import/Export templates
    'import/index.html': '<html><body><h1>Import Data</h1></body></html>',
    'import/import_success.html': '<html><body><h1>Import Success</h1></body></html>',
    'export/index.html': '<html><body><h1>Export Data</h1></body></html>',
    
    # Tax Dashboard templates
    'tax_dashboard/index.html': '<html><body><h1>Tax Dashboard</h1></body></html>',
    'tax_dashboard/prediction.html': '<html><body><h1>Tax Prediction</h1></body></html>',
    
    # Timesheet templates
    'timesheet/index.html': '<html><body><h1>Timesheets</h1></body></html>',
    'timesheet/new.html': '<html><body><h1>New Timesheet</h1></body></html>',
    'timesheet/edit.html': '<html><body><h1>Edit Timesheet</h1></body></html>',
    'timesheet/weekly.html': '<html><body><h1>Weekly Timesheet</h1></body></html>',
    
    # Common layout/includes
    'layouts/base.html': '<!DOCTYPE html><html><head><title>{{ title }}</title></head><body>{% block content %}{% endblock %}</body></html>',
}


def mock_render_template(template_name, **kwargs):
    """Mock template rendering for tests."""
    if template_name in TEMPLATE_MOCKS:
        return render_template_string(TEMPLATE_MOCKS[template_name], **kwargs)
    else:
        # Generic fallback template
        return render_template_string(
            f'<html><body><h1>{template_name}</h1><p>Template mocked for testing</p></body></html>',
            **kwargs
        )


@pytest.fixture
def app():
    """Create and configure a Flask app for testing with mocked templates."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    # Create app with test config
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "WTF_CSRF_ENABLED": False,
        "MAX_CONTENT_LENGTH": 5 * 1024 * 1024,  # 5MB max upload for tests
        "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test;EndpointSuffix=core.windows.net",
    })
    
    # Import after creating app to avoid circular imports
    from akowe.models import db
    
    # Store db reference on app for test access
    app.db = db
    
    # Create the database and the tables
    with app.app_context():
        db.create_all()
    
    # Apply template mocking
    with patch('flask.render_template', side_effect=mock_render_template):
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
        from akowe.models import db
        from akowe.models.user import User
        
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
        from akowe.models import db
        from akowe.models.user import User
        
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