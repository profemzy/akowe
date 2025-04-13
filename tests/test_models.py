"""Tests for database models."""
import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import func

from akowe.models.user import User
from akowe.models.income import Income
from akowe.models.expense import Expense
from akowe.models.timesheet import Timesheet
from akowe.models.invoice import Invoice


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


def test_timesheet_model(app, test_user):
    """Test the Timesheet model."""
    with app.app_context():
        timesheet = Timesheet(
            date=date(2025, 4, 15),
            client='TestClient',
            project='Test Project',
            description='Testing timesheet model',
            hours=Decimal('8.5'),
            hourly_rate=Decimal('125.00'),
            status='pending',
            user_id=test_user.id
        )
        
        app.db.session.add(timesheet)
        app.db.session.commit()
        
        saved_timesheet = Timesheet.query.first()
        assert saved_timesheet is not None
        assert saved_timesheet.date == date(2025, 4, 15)
        assert saved_timesheet.client == 'TestClient'
        assert saved_timesheet.project == 'Test Project'
        assert saved_timesheet.description == 'Testing timesheet model'
        assert saved_timesheet.hours == Decimal('8.5')
        assert saved_timesheet.hourly_rate == Decimal('125.00')
        assert saved_timesheet.status == 'pending'
        assert saved_timesheet.user_id == test_user.id
        
        # Test amount property
        assert saved_timesheet.amount == Decimal('8.5') * Decimal('125.00')


def test_invoice_model(app, test_user):
    """Test the Invoice model."""
    with app.app_context():
        # Create invoice
        invoice = Invoice(
            invoice_number='INV-TEST-001',
            client='TestClient',
            company_name='Test Company',
            issue_date=date(2025, 4, 20),
            due_date=date(2025, 5, 20),
            notes='Test invoice notes',
            tax_rate=Decimal('13.00'),
            status='draft',
            user_id=test_user.id
        )
        
        app.db.session.add(invoice)
        app.db.session.flush()  # Get invoice ID without committing
        
        # Create timesheet entries linked to invoice
        entries = [
            Timesheet(
                date=date(2025, 4, 15),
                client='TestClient',
                project='Test Project',
                description='Entry 1',
                hours=Decimal('8.5'),
                hourly_rate=Decimal('125.00'),
                status='billed',
                invoice_id=invoice.id,
                user_id=test_user.id
            ),
            Timesheet(
                date=date(2025, 4, 16),
                client='TestClient',
                project='Test Project',
                description='Entry 2',
                hours=Decimal('6.0'),
                hourly_rate=Decimal('125.00'),
                status='billed',
                invoice_id=invoice.id,
                user_id=test_user.id
            )
        ]
        
        for entry in entries:
            app.db.session.add(entry)
            
        app.db.session.flush()
        
        # Calculate invoice totals
        invoice.calculate_totals()
        app.db.session.commit()
        
        # Verify invoice in database
        saved_invoice = Invoice.query.first()
        assert saved_invoice is not None
        assert saved_invoice.invoice_number == 'INV-TEST-001'
        assert saved_invoice.client == 'TestClient'
        assert saved_invoice.company_name == 'Test Company'
        assert saved_invoice.issue_date == date(2025, 4, 20)
        assert saved_invoice.due_date == date(2025, 5, 20)
        assert saved_invoice.notes == 'Test invoice notes'
        assert saved_invoice.tax_rate == Decimal('13.00')
        assert saved_invoice.status == 'draft'
        assert saved_invoice.user_id == test_user.id
        
        # Verify timesheet entries relationship
        assert len(saved_invoice.timesheet_entries) == 2
        
        # Verify calculations
        expected_subtotal = Decimal('8.5') * Decimal('125.00') + Decimal('6.0') * Decimal('125.00')
        expected_tax = expected_subtotal * Decimal('0.13')
        expected_total = expected_subtotal + expected_tax
        
        assert saved_invoice.subtotal == expected_subtotal
        assert saved_invoice.tax_amount == expected_tax
        assert saved_invoice.total == expected_total


def test_timesheet_invoice_relationship(app, test_user):
    """Test the relationship between timesheet entries and invoices."""
    with app.app_context():
        # Create an invoice
        invoice = Invoice(
            invoice_number='INV-TEST-002',
            client='RelationshipClient',
            issue_date=date(2025, 4, 25),
            due_date=date(2025, 5, 25),
            tax_rate=Decimal('5.00'),
            status='draft',
            user_id=test_user.id
        )
        
        app.db.session.add(invoice)
        app.db.session.flush()
        
        # Create timesheet entries
        timesheet1 = Timesheet(
            date=date(2025, 4, 20),
            client='RelationshipClient',
            project='Relationship Project',
            description='Testing relationships',
            hours=Decimal('4.0'),
            hourly_rate=Decimal('100.00'),
            status='billed',
            invoice_id=invoice.id,
            user_id=test_user.id
        )
        
        timesheet2 = Timesheet(
            date=date(2025, 4, 21),
            client='RelationshipClient',
            project='Relationship Project',
            description='More testing',
            hours=Decimal('5.0'),
            hourly_rate=Decimal('100.00'),
            status='billed',
            invoice_id=invoice.id,
            user_id=test_user.id
        )
        
        app.db.session.add_all([timesheet1, timesheet2])
        app.db.session.flush()
        
        # Calculate invoice totals
        invoice.calculate_totals()
        app.db.session.commit()
        
        # Test the relationship in both directions
        saved_invoice = Invoice.query.filter_by(invoice_number='INV-TEST-002').first()
        assert len(saved_invoice.timesheet_entries) == 2
        
        saved_timesheet = Timesheet.query.filter_by(description='Testing relationships').first()
        assert saved_timesheet.invoice is not None
        assert saved_timesheet.invoice.invoice_number == 'INV-TEST-002'
        
        # Test invoice calculation
        assert saved_invoice.subtotal == Decimal('900.00')  # 4*100 + 5*100
        assert saved_invoice.tax_amount == Decimal('45.00')  # 900 * 0.05
        assert saved_invoice.total == Decimal('945.00')  # 900 + 45