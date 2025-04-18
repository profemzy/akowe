"""Test suite using the comprehensive mock fixtures."""

import os
import sys
import pytest
from flask import session, g

# Make sure the project root is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Only use mock conftest during testing
# This is safer than setting an environment variable which might persist
pytest_plugins = ["tests.conftest_with_mocks"]


def test_login_page(client):
    """Test login page loads correctly."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign in to your account" in response.data


def test_login_success(client, auth):
    """Test successful login."""
    response = auth.login()
    assert response.headers["Location"] == "/"
    
    # Test session is set correctly
    with client:
        client.get("/")
        assert session.get("_user_id") is not None


def test_dashboard_access(client, auth):
    """Test dashboard access after login."""
    # Login first
    auth.login()
    
    # Access dashboard
    response = client.get("/")
    assert response.status_code == 200
    assert b"Dashboard" in response.data


def test_client_pages(client, auth):
    """Test client management pages."""
    auth.login()
    
    # List clients
    response = client.get("/client/")
    assert response.status_code == 200
    assert b"Clients" in response.data
    
    # New client form
    response = client.get("/client/new")
    assert response.status_code == 200
    assert b"New Client" in response.data


def test_expense_pages(client, auth):
    """Test expense management pages."""
    auth.login()
    
    # List expenses
    response = client.get("/expense/")
    assert response.status_code == 200
    assert b"Expenses" in response.data
    
    # Expense analysis
    response = client.get("/expense/analyze-expenses")
    assert response.status_code == 200
    assert b"Tax Category Overview" in response.data  # Looking for content that's actually on the page