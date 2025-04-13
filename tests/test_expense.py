"""Tests for expense-related functionality."""
import pytest
from decimal import Decimal
from datetime import date
import io

from akowe.models.expense import Expense


def test_expense_list(client, auth, sample_expense):
    """Test listing expense records."""
    auth.login()
    response = client.get('/expense/')
    
    # Check that the expense data is displayed
    assert b'WD Red Plus 12TB NAS Hard Disk Drive' in response.data
    assert b'386.37' in response.data
    assert b'Newegg' in response.data


def test_expense_creation(client, auth, app):
    """Test creating a new expense record."""
    auth.login()
    
    # Submit the form
    response = client.post('/expense/new', data={
        'date': '2025-05-01',
        'title': 'Test Expense',
        'amount': '250.00',
        'category': 'software',
        'payment_method': 'credit_card',
        'status': 'paid',
        'vendor': 'Test Vendor'
    }, follow_redirects=True)
    
    assert b'Expense record added successfully' in response.data
    
    # Verify it's in the database
    with app.app_context():
        expense = Expense.query.filter_by(title='Test Expense').first()
        assert expense is not None
        assert expense.amount == Decimal('250.00')
        assert expense.date == date(2025, 5, 1)
        assert expense.category == 'software'
        assert expense.payment_method == 'credit_card'
        assert expense.status == 'paid'
        assert expense.vendor == 'Test Vendor'


def test_expense_edit(client, auth, app, sample_expense):
    """Test editing an expense record."""
    auth.login()
    
    with app.app_context():
        # Get ID of first expense record
        expense_id = Expense.query.first().id
    
    # Submit the edit form
    response = client.post(f'/expense/edit/{expense_id}', data={
        'date': '2025-04-12',
        'title': 'WD Red Plus 12TB NAS Hard Disk Drive',
        'amount': '400.00',  # Changed amount
        'category': 'hardware',
        'payment_method': 'credit_card',
        'status': 'paid',  # Changed status
        'vendor': 'Newegg'
    }, follow_redirects=True)
    
    assert b'Expense record updated successfully' in response.data
    
    # Verify it's updated in the database
    with app.app_context():
        expense = Expense.query.get(expense_id)
        assert expense.amount == Decimal('400.00')
        assert expense.status == 'paid'


def test_expense_delete(client, auth, app, sample_expense):
    """Test deleting an expense record."""
    auth.login()
    
    with app.app_context():
        # Get ID of first expense record
        expense_id = Expense.query.first().id
        initial_count = Expense.query.count()
    
    # Submit deletion
    response = client.post(f'/expense/delete/{expense_id}', follow_redirects=True)
    
    assert b'Expense record deleted successfully' in response.data
    
    # Verify it's deleted from the database
    with app.app_context():
        assert Expense.query.count() == initial_count - 1
        assert Expense.query.get(expense_id) is None


def test_expense_import(client, auth, app):
    """Test importing expense from CSV."""
    auth.login()
    
    # Create a sample CSV file
    csv_content = """date,title,amount,category,payment_method,status,vendor
2025-06-21,Imported Expense,199.99,software,debit_card,pending,ImportVendor"""
    
    csv_data = io.BytesIO(csv_content.encode('utf-8'))
    
    # Post the CSV file
    response = client.post('/expense/import', data={
        'file': (csv_data, 'expense.csv')
    }, follow_redirects=True)
    
    assert b'Successfully imported' in response.data
    
    # Verify the data was imported
    with app.app_context():
        expense = Expense.query.filter_by(title='Imported Expense').first()
        assert expense is not None
        assert expense.amount == Decimal('199.99')
        assert expense.date == date(2025, 6, 21)
        assert expense.category == 'software'
        assert expense.payment_method == 'debit_card'
        assert expense.status == 'pending'
        assert expense.vendor == 'ImportVendor'