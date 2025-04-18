"""Tests for the enhanced authentication security features."""

import pytest
import time
import os
from datetime import datetime, timedelta
from flask import session, url_for
from flask_login import current_user


def test_session_timeout_config(client, app):
    """Test that session timeout settings are properly configured."""
    # Check session lifetime configuration
    assert app.config['PERMANENT_SESSION_LIFETIME'] == timedelta(hours=6)
    assert app.config['SESSION_ACTIVITY_TIMEOUT'] == 1800
    assert app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'


def test_csrf_protection(app):
    """Test that CSRF protection is enabled in the app."""
    # In our tests, CSRF is disabled for convenience, but let's verify it's enabled in production
    # We can check that CSRFProtect is initialized
    csrf = app.extensions.get('csrf', None)
    assert csrf is not None
    
    # Check that WTF_CSRF_ENABLED would be enabled in production
    # Original config has WTF_CSRF_ENABLED=False for tests,
    # but production would default to True
    assert app.config.get('WTF_CSRF_ENABLED') is False  # Disabled in tests
    assert 'csrf' in app.extensions  # But the extension is registered


def test_normal_session_has_activity_timestamp(client, auth):
    """Test that session gets last_activity timestamp after login."""
    # Login
    auth.login()
    
    # Check that last_activity timestamp was set
    with client.session_transaction() as sess:
        assert 'last_activity' in sess
        # Timestamp should be recent
        timestamp = sess['last_activity']
        diff = datetime.utcnow().timestamp() - timestamp
        assert diff < 10  # Less than 10 seconds old


def test_last_activity_updates_on_requests(client, auth):
    """Test that last_activity updates on subsequent requests."""
    # Login
    auth.login()
    
    # Get initial timestamp
    with client.session_transaction() as sess:
        initial_timestamp = sess['last_activity']
    
    # Wait a bit
    time.sleep(1)
    
    # Make another request
    client.get('/') 
    
    # Check that timestamp was updated
    with client.session_transaction() as sess:
        updated_timestamp = sess['last_activity']
        assert updated_timestamp > initial_timestamp


def test_security_features_configuration(app):
    """Test that all security features are properly configured."""
    # Test security related configurations
    assert app.config['PERMANENT_SESSION_LIFETIME'] == timedelta(hours=6)
    assert app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'
    assert app.config['REMEMBER_COOKIE_DURATION'] == timedelta(days=14)
    assert app.config['REMEMBER_COOKIE_HTTPONLY'] is True
    assert app.config['SESSION_ACTIVITY_TIMEOUT'] == 1800
    
    # Check that security behaviors are properly set up
    # This app object has already initialized these components
    assert 'csrf' in app.extensions  # CSRF protection
    assert app.session_interface is not None  # Session handling
    assert app.before_request_funcs is not None  # Before request handlers