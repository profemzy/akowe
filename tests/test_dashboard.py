"""Tests for the dashboard functionality."""
import pytest
from datetime import date
from decimal import Decimal

from akowe.models.income import Income
from akowe.models.expense import Expense


def test_dashboard_access(client, auth):
    """Test that the dashboard is accessible after login."""
    auth.login()
    response = client.get('/')
    assert response.status_code == 200
    assert b'Dashboard' in response.data


def test_dashboard_year_selection(client, auth, app, sample_income, sample_expense):
    """Test year selection on dashboard."""
    auth.login()
    
    # Test the default view (current year)
    response = client.get('/')
    assert response.status_code == 200
    
    # Test selecting a specific year
    response = client.get('/?year=2025')
    assert response.status_code == 200
    assert b'2025' in response.data
    
    # Analytics data should be present
    assert b'Monthly Income vs Expenses' in response.data


def test_dashboard_analytics(client, auth, app):
    """Test that the dashboard shows correct analytics."""
    # Add income and expense for the same year
    with app.app_context():
        income1 = Income(
            date=date(2025, 1, 15),
            amount=Decimal('5000.00'),
            client='Client A',
            project='Project A'
        )
        
        income2 = Income(
            date=date(2025, 2, 15),
            amount=Decimal('6000.00'),
            client='Client B',
            project='Project B'
        )
        
        expense1 = Expense(
            date=date(2025, 1, 20),
            title='Expense A',
            amount=Decimal('1000.00'),
            category='software',
            payment_method='credit_card',
            status='paid'
        )
        
        expense2 = Expense(
            date=date(2025, 2, 10),
            title='Expense B',
            amount=Decimal('2000.00'),
            category='hardware',
            payment_method='credit_card',
            status='paid'
        )
        
        app.db.session.add_all([income1, income2, expense1, expense2])
        app.db.session.commit()
    
    auth.login()
    response = client.get('/?year=2025')
    
    # Check that totals are displayed
    assert b'$11,000.00' in response.data  # Total income
    assert b'$3,000.00' in response.data   # Total expense
    assert b'$8,000.00' in response.data   # Net profit


def test_dashboard_monthly_chart_data(client, auth, app):
    """Test that monthly chart data is correctly calculated."""
    # Create data across multiple months
    with app.app_context():
        # January income and expense
        income_jan = Income(
            date=date(2025, 1, 15),
            amount=Decimal('5000.00'),
            client='Client Jan',
            project='Project Jan'
        )
        
        expense_jan = Expense(
            date=date(2025, 1, 20),
            title='Expense Jan',
            amount=Decimal('1000.00'),
            category='software',
            payment_method='credit_card',
            status='paid'
        )
        
        # February income and expense
        income_feb = Income(
            date=date(2025, 2, 15),
            amount=Decimal('6000.00'),
            client='Client Feb',
            project='Project Feb'
        )
        
        expense_feb = Expense(
            date=date(2025, 2, 10),
            title='Expense Feb',
            amount=Decimal('2000.00'),
            category='hardware',
            payment_method='credit_card',
            status='paid'
        )
        
        app.db.session.add_all([income_jan, expense_jan, income_feb, expense_feb])
        app.db.session.commit()
    
    auth.login()
    response = client.get('/?year=2025')
    
    # Check that the monthly chart data is included in the page
    assert b'monthlyChart' in response.data
    assert b'Jan' in response.data
    assert b'Feb' in response.data


def test_dashboard_category_chart_data(client, auth, app):
    """Test that category chart data is correctly calculated."""
    # Create expenses in different categories
    with app.app_context():
        expense1 = Expense(
            date=date(2025, 1, 20),
            title='Software Expense',
            amount=Decimal('1000.00'),
            category='software',
            payment_method='credit_card',
            status='paid'
        )
        
        expense2 = Expense(
            date=date(2025, 2, 10),
            title='Hardware Expense',
            amount=Decimal('2000.00'),
            category='hardware',
            payment_method='credit_card',
            status='paid'
        )
        
        expense3 = Expense(
            date=date(2025, 3, 15),
            title='Travel Expense',
            amount=Decimal('1500.00'),
            category='travel',
            payment_method='credit_card',
            status='paid'
        )
        
        app.db.session.add_all([expense1, expense2, expense3])
        app.db.session.commit()
    
    auth.login()
    response = client.get('/?year=2025')
    
    # Check that the category chart data is included in the page
    assert b'categoryChart' in response.data
    assert b'software' in response.data
    assert b'hardware' in response.data
    assert b'travel' in response.data


def test_dashboard_no_data(client, auth, app):
    """Test dashboard behavior when there's no data."""
    # Ensure no data for year 2024
    with app.app_context():
        # Clear any existing data
        Income.query.delete()
        Expense.query.delete()
        app.db.session.commit()
    
    auth.login()
    response = client.get('/?year=2024')
    
    assert response.status_code == 200
    # Should still display the dashboard with zero values
    assert b'$0.00' in response.data