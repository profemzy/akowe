"""Tests for admin functionality."""
import pytest
from akowe.models.user import User


def test_admin_access(client, auth, admin_user):
    """Test that admin pages are accessible to admin users."""
    # Login as admin
    auth.login('admin', 'password')
    response = client.get('/admin/')
    assert response.status_code == 200
    assert b'Admin Dashboard' in response.data


def test_admin_denied_to_regular_users(client, auth, test_user):
    """Test that admin pages are not accessible to regular users."""
    # Login as regular user
    auth.login('test', 'password')
    response = client.get('/admin/')
    assert response.status_code == 403  # Forbidden


def test_user_list(client, auth, admin_user, test_user):
    """Test viewing the user list as admin."""
    auth.login('admin', 'password')
    response = client.get('/admin/users')
    assert response.status_code == 200
    
    # Both users should be listed
    assert b'admin' in response.data
    assert b'test' in response.data


def test_user_creation(client, auth, admin_user, app):
    """Test creating a new user as admin."""
    auth.login('admin', 'password')
    
    # Submit the form
    response = client.post('/admin/users/new', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'first_name': 'New',
        'last_name': 'User',
        'password': 'newpassword',
        'confirm_password': 'newpassword',
        'is_admin': False
    }, follow_redirects=True)
    
    assert b'User newuser has been created' in response.data
    
    # Verify it's in the database
    with app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'newuser@example.com'
        assert user.first_name == 'New'
        assert user.last_name == 'User'
        assert user.is_admin is False
        assert user.verify_password('newpassword')


def test_user_edit(client, auth, admin_user, test_user, app):
    """Test editing a user as admin."""
    auth.login('admin', 'password')
    
    with app.app_context():
        user_id = User.query.filter_by(username='test').first().id
    
    # Submit the edit form
    response = client.post(f'/admin/users/{user_id}/edit', data={
        'email': 'updated@example.com',
        'first_name': 'Updated',
        'last_name': 'User',
        'is_admin': True,
        'is_active': True
    }, follow_redirects=True)
    
    assert b'User test has been updated' in response.data
    
    # Verify it's updated in the database
    with app.app_context():
        user = User.query.get(user_id)
        assert user.email == 'updated@example.com'
        assert user.first_name == 'Updated'
        assert user.is_admin is True


def test_user_delete(client, auth, admin_user, test_user, app):
    """Test deleting a user as admin."""
    auth.login('admin', 'password')
    
    with app.app_context():
        user_id = User.query.filter_by(username='test').first().id
    
    # Submit deletion
    response = client.post(f'/admin/users/{user_id}/delete', follow_redirects=True)
    
    assert b'User test has been deleted' in response.data
    
    # Verify it's deleted from the database
    with app.app_context():
        assert User.query.get(user_id) is None


def test_admin_cannot_delete_self(client, auth, admin_user, app):
    """Test that an admin cannot delete their own account."""
    auth.login('admin', 'password')
    
    with app.app_context():
        admin_id = User.query.filter_by(username='admin').first().id
    
    # Try to delete own account
    response = client.post(f'/admin/users/{admin_id}/delete', follow_redirects=True)
    
    assert b'You cannot delete your own account' in response.data
    
    # Admin should still exist
    with app.app_context():
        assert User.query.get(admin_id) is not None


def test_admin_reset_password(client, auth, admin_user, test_user, app):
    """Test resetting a user's password as admin."""
    auth.login('admin', 'password')
    
    with app.app_context():
        user_id = User.query.filter_by(username='test').first().id
    
    # Reset password
    response = client.post(f'/admin/users/{user_id}/reset-password', follow_redirects=True)
    
    assert b'Password for test has been reset' in response.data
    
    # Get the new password from the response
    import re
    password_pattern = re.compile(r'reset to: (\S+)')
    match = password_pattern.search(response.data.decode('utf-8'))
    new_password = match.group(1) if match else None
    
    # Verify the new password works
    auth.logout()
    response = client.post('/login', data={
        'username': 'test',
        'password': new_password
    })
    assert response.headers['Location'] == '/'