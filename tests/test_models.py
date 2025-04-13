"""Tests for database models."""
import pytest
from datetime import date
from decimal import Decimal

from akowe.models.user import User
from akowe.models.income import Income
from akowe.models.expense import Expense


def test_user_password_hashing(app):
    """Test that user passwords are hashed and verified correctly."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.password = 'password123'
        
        # Password should be hashed, not stored as plaintext
        assert user.password_hash != 'password123'
        
        # Verify password works
        assert user.verify_password('password123')
        
        # Verify wrong password fails
        assert not user.verify_password('wrongpassword')


def test_user_password_not_readable(app):
    """Test that password attribute is not readable."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.password = 'password123'
        
        with pytest.raises(AttributeError):
            user.password


def test_user_creation(app):
    """Test creating a user in the database."""
    with app.app_context():
        user = User(
            username='newuser',
            email='newuser@example.com',
            first_name='New',
            last_name='User',
            is_admin=False
        )
        user.password = 'password123'
        
        # Add user to database
        app.db.session.add(user)
        app.db.session.commit()
        
        # Retrieve the user from database
        saved_user = User.query.filter_by(username='newuser').first()
        assert saved_user is not None
        assert saved_user.email == 'newuser@example.com'
        assert saved_user.verify_password('password123')


def test_user_get_full_name(app):
    """Test the get_full_name method."""
    with app.app_context():
        # User with first and last name
        user1 = User(
            username='user1',
            first_name='First',
            last_name='Last'
        )
        assert user1.get_full_name() == 'First Last'
        
        # User without name
        user2 = User(username='user2')
        assert user2.get_full_name() == 'user2'


def test_income_model(app):
    """Test the Income model."""
    with app.app_context():
        income = Income(
            date=date(2025, 3, 21),
            amount=Decimal('9040.00'),
            client='SearchLabs',
            project='P2025001',
            invoice='INV-001'
        )
        
        app.db.session.add(income)
        app.db.session.commit()
        
        saved_income = Income.query.first()
        assert saved_income is not None
        assert saved_income.date == date(2025, 3, 21)
        assert saved_income.amount == Decimal('9040.00')
        assert saved_income.client == 'SearchLabs'
        assert saved_income.project == 'P2025001'
        assert saved_income.invoice == 'INV-001'


def test_expense_model(app):
    """Test the Expense model."""
    with app.app_context():
        expense = Expense(
            date=date(2025, 4, 12),
            title='Hard Drive',
            amount=Decimal('386.37'),
            category='hardware',
            payment_method='credit_card',
            status='pending',
            vendor='Newegg'
        )
        
        app.db.session.add(expense)
        app.db.session.commit()
        
        saved_expense = Expense.query.first()
        assert saved_expense is not None
        assert saved_expense.date == date(2025, 4, 12)
        assert saved_expense.title == 'Hard Drive'
        assert saved_expense.amount == Decimal('386.37')
        assert saved_expense.category == 'hardware'
        assert saved_expense.payment_method == 'credit_card'
        assert saved_expense.status == 'pending'
        assert saved_expense.vendor == 'Newegg'


def test_income_expense_relationship(app):
    """Test relationships between income and expense."""
    with app.app_context():
        # Add some income and expense data
        income = Income(
            date=date(2025, 3, 21),
            amount=Decimal('10000.00'),
            client='Client',
            project='Project'
        )
        
        expense1 = Expense(
            date=date(2025, 3, 22),
            title='Expense 1',
            amount=Decimal('1000.00'),
            category='software',
            payment_method='credit_card',
            status='paid'
        )
        
        expense2 = Expense(
            date=date(2025, 3, 23),
            title='Expense 2',
            amount=Decimal('2000.00'),
            category='hardware',
            payment_method='credit_card',
            status='paid'
        )
        
        app.db.session.add_all([income, expense1, expense2])
        app.db.session.commit()
        
        # Query and aggregate for a report
        total_income = app.db.session.query(
            func.sum(Income.amount)
        ).scalar() or Decimal('0.00')
        
        total_expense = app.db.session.query(
            func.sum(Expense.amount)
        ).scalar() or Decimal('0.00')
        
        assert total_income == Decimal('10000.00')
        assert total_expense == Decimal('3000.00')
        assert (total_income - total_expense) == Decimal('7000.00')