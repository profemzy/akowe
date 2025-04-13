"""Tests for income-related functionality."""
import pytest
from decimal import Decimal
from datetime import date
import io

from akowe.models.income import Income


def test_income_list(client, auth, sample_income):
    """Test listing income records."""
    auth.login()
    response = client.get('/income/')
    
    # Check that the income data is displayed
    assert b'SearchLabs (RAVL)' in response.data
    assert b'9,040.00' in response.data
    assert b'P2025001 - Interac Konek' in response.data


def test_income_creation(client, auth, app):
    """Test creating a new income record."""
    auth.login()
    
    # Submit the form
    response = client.post('/income/new', data={
        'date': '2025-05-01',
        'amount': '5000.00',
        'client': 'New Client',
        'project': 'New Project',
        'invoice': 'INV-001'
    }, follow_redirects=True)
    
    assert b'Income record added successfully' in response.data
    
    # Verify it's in the database
    with app.app_context():
        income = Income.query.filter_by(client='New Client').first()
        assert income is not None
        assert income.amount == Decimal('5000.00')
        assert income.date == date(2025, 5, 1)


def test_income_edit(client, auth, app, sample_income):
    """Test editing an income record."""
    auth.login()
    
    with app.app_context():
        # Get ID of first income record
        income_id = Income.query.first().id
    
    # Submit the edit form
    response = client.post(f'/income/edit/{income_id}', data={
        'date': '2025-03-21',
        'amount': '10000.00',  # Changed amount
        'client': 'SearchLabs (RAVL)',
        'project': 'P2025001 - Interac Konek',
        'invoice': 'Invoice #INV-202503-0002 - SearchLabs'
    }, follow_redirects=True)
    
    assert b'Income record updated successfully' in response.data
    
    # Verify it's updated in the database
    with app.app_context():
        income = Income.query.get(income_id)
        assert income.amount == Decimal('10000.00')


def test_income_delete(client, auth, app, sample_income):
    """Test deleting an income record."""
    auth.login()
    
    with app.app_context():
        # Get ID of first income record
        income_id = Income.query.first().id
        initial_count = Income.query.count()
    
    # Submit deletion
    response = client.post(f'/income/delete/{income_id}', follow_redirects=True)
    
    assert b'Income record deleted successfully' in response.data
    
    # Verify it's deleted from the database
    with app.app_context():
        assert Income.query.count() == initial_count - 1
        assert Income.query.get(income_id) is None


def test_income_import(client, auth, app):
    """Test importing income from CSV."""
    auth.login()
    
    # Create a sample CSV file
    csv_content = """date,amount,client,project,invoice
2025-06-21,8000.00,ImportClient,ImportProject,ImportInvoice"""
    
    csv_data = io.BytesIO(csv_content.encode('utf-8'))
    
    # Post the CSV file
    response = client.post('/income/import', data={
        'file': (csv_data, 'income.csv')
    }, follow_redirects=True)
    
    assert b'Successfully imported' in response.data
    
    # Verify the data was imported
    with app.app_context():
        income = Income.query.filter_by(client='ImportClient').first()
        assert income is not None
        assert income.amount == Decimal('8000.00')
        assert income.date == date(2025, 6, 21)
        assert income.project == 'ImportProject'
        assert income.invoice == 'ImportInvoice'