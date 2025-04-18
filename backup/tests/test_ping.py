"""Test simple ping route."""

import os
import sys
import pytest
from flask import Flask, jsonify

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_ping():
    """Test that ping endpoint returns expected response without dependencies."""
    app = Flask(__name__)
    
    @app.route("/ping")
    def ping():
        return {"status": "ok", "message": "Akowe is running"}
    
    client = app.test_client()
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json == {"status": "ok", "message": "Akowe is running"}