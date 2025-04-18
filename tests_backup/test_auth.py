"""Tests for authentication functionality."""

import pytest
import os
import sys
from flask import g, session

# Add the project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from akowe.models.user import User


def test_login_page(client):
    """Test login page loads correctly."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign in to your account" in response.data


def test_login_success(client, test_user, auth):
    """Test successful login."""
    response = auth.login()
    assert response.headers["Location"] == "/"

    with client:
        client.get("/")
        assert session["_user_id"] == str(test_user.id)


def test_login_failure(client, auth):
    """Test login with incorrect credentials."""
    response = auth.login("wronguser", "wrongpassword")
    assert b"Invalid username or password" in response.data


def test_login_inactive_user(client, app, auth):
    """Test login with inactive user."""
    with app.app_context():
        user = User.query.filter_by(username="test").first()
        user.is_active = False
        app.db.session.commit()

    response = auth.login()
    assert b"Account is disabled" in response.data


def test_logout(client, auth):
    """Test logout functionality."""
    auth.login()

    with client:
        auth.logout()
        assert "_user_id" not in session


def test_password_change(client, auth, app):
    """Test password change functionality."""
    auth.login()
    response = client.post(
        "/change-password",
        data={
            "current_password": "password",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        },
        follow_redirects=True,
    )

    assert b"Your password has been updated" in response.data

    # Verify the new password works
    auth.logout()
    response = client.post("/login", data={"username": "test", "password": "newpassword123"})
    assert response.headers["Location"] == "/"


def test_password_change_wrong_current(client, auth):
    """Test password change with wrong current password."""
    auth.login()
    response = client.post(
        "/change-password",
        data={
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        },
    )

    assert b"Invalid current password" in response.data


def test_password_change_mismatch(client, auth):
    """Test password change with mismatched new passwords."""
    auth.login()
    response = client.post(
        "/change-password",
        data={
            "current_password": "password",
            "new_password": "newpassword123",
            "confirm_password": "differentpassword",
        },
    )

    assert b"Passwords must match" in response.data


def test_auth_required(client):
    """Test that routes require authentication."""
    # Try to access a protected page
    response = client.get("/")
    assert response.headers["Location"].startswith("/login")


def test_admin_required(client, auth, test_user):
    """Test that admin routes require admin privileges."""
    auth.login()  # Login as regular user
    response = client.get("/admin/", follow_redirects=False)
    assert response.status_code == 403  # Forbidden
