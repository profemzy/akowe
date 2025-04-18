"""Basic app tests that don't require template rendering."""

import os
import sys
import pytest
from flask import Flask, url_for

# Make sure the project root is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_ping_route(client):
    """Test the ping route responds correctly."""
    response = client.get('/ping')
    assert response.status_code == 200
    assert response.json == {"status": "ok", "message": "Akowe is running"}


def test_auth_redirect(client):
    """Test that private routes redirect to login."""
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']