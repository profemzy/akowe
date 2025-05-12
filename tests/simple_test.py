"""Simple standalone test."""

import os
import sys
import pytest
from flask import Flask, request, url_for
from werkzeug.security import generate_password_hash, check_password_hash

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class SampleUser:
    """Sample user class for testing passwords."""

    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches."""
        return check_password_hash(self.password_hash, password)
  
        
def test_user_password():
    """Test password hashing and checking."""
    user = SampleUser("test", "password")
    assert user.check_password("password") is True
    assert user.check_password("wrong") is False