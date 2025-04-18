"""Tests for automatic income generation when invoices are marked as paid."""

import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from flask import url_for
from flask_login import current_user

from akowe import create_app
from akowe.models import db
from akowe.models.invoice import Invoice
from akowe.models.income import Income
from akowe.models.client import Client
from akowe.models.user import User
from akowe.models.timesheet import Timesheet

class InvoiceAutoIncomeTestCase(unittest.TestCase):
    """Test the automatic income generation when invoices are marked as paid."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)
        
        # Create database and tables
        db.create_all()
        
        # Create a test user
        self.user = User(
            email="test@example.com",
            password="password",
            name="Test User",
            is_admin=False,
            hourly_rate=Decimal("50.00")
        )
        db.session.add(self.user)
        db.session.commit()
        
        # Create a test client
        self.test_client = Client(
            name="Test Client",
            email="client@example.com",
            user_id=self.user.id
        )
        db.session.add(self.test_client)
        db.session.commit()
        
        # Log in the user
        with self.client.session_transaction() as session:
            session["_user_id"] = self.user.id
            session["_fresh"] = True
    
    def tearDown(self):
        """Tear down test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def create_test_invoice(self):
        """Create a test invoice."""
        # Create timesheet entry
        timesheet = Timesheet(
            date=datetime.utcnow().date(),
            client_id=self.test_client.id,
            project="Test Project",
            description="Test Description",
            hours=Decimal("5"),
            hourly_rate=Decimal("50.00"),
            status="pending",
            user_id=self.user.id
        )
        db.session.add(timesheet)
        db.session.commit()
        
        # Create invoice
        invoice = Invoice(
            invoice_number=f"INV-{datetime.utcnow().strftime('%Y%m')}-0001",
            client_id=self.test_client.id,
            company_name="Test Company",
            issue_date=datetime.utcnow().date(),
            due_date=datetime.utcnow().date() + timedelta(days=30),
            notes="Test notes",
            subtotal=Decimal("250.00"),
            tax_rate=Decimal("10.00"),
            tax_amount=Decimal("25.00"),
            total=Decimal("275.00"),
            status="sent",
            user_id=self.user.id
        )
        db.session.add(invoice)
        db.session.commit()
        
        # Associate timesheet with invoice
        timesheet.invoice_id = invoice.id
        timesheet.status = "billed"
        db.session.commit()
        
        return invoice
    
    def test_mark_paid_creates_income(self):
        """Test that marking an invoice as paid creates an income record."""
        # Create a test invoice
        invoice = self.create_test_invoice()
        
        # Count income records before marking the invoice as paid
        income_before = Income.query.filter_by(invoice_id=invoice.id).count()
        
        # Mark the invoice as paid
        response = self.client.post(
            f"/invoice/mark_paid/{invoice.id}", 
            data={
                "payment_method": "Bank Transfer",
                "payment_reference": "TRX12345"
            },
            follow_redirects=True
        )
        
        # Check that the invoice was marked as paid
        invoice = Invoice.query.get(invoice.id)
        self.assertEqual(invoice.status, "paid")
        
        # Check that an income record was created
        income_after = Income.query.filter_by(invoice_id=invoice.id).count()
        self.assertEqual(income_after, income_before + 1)
        
        # Get the income record
        income = Income.query.filter_by(invoice_id=invoice.id).first()
        
        # Check that the income record has the correct values
        self.assertEqual(income.amount, invoice.total)
        self.assertEqual(income.client_id, invoice.client_id)
        self.assertEqual(income.invoice, invoice.invoice_number)
    
    def test_mark_paid_does_not_create_duplicate_income(self):
        """Test that marking an invoice as paid does not create duplicate income records."""
        # Create a test invoice
        invoice = self.create_test_invoice()
        
        # Create an income record for this invoice
        income = Income(
            date=datetime.utcnow().date(),
            amount=invoice.total,
            client=self.test_client.name,
            project="Test Project",
            invoice=invoice.invoice_number,
            client_id=invoice.client_id,
            invoice_id=invoice.id
        )
        try:
            # Try with user_id first
            income.user_id = self.user.id
            db.session.add(income)
            db.session.commit()
        except Exception:
            # If that fails, try without user_id
            db.session.rollback()
            income = Income(
                date=datetime.utcnow().date(),
                amount=invoice.total,
                client=self.test_client.name,
                project="Test Project",
                invoice=invoice.invoice_number,
                client_id=invoice.client_id,
                invoice_id=invoice.id
            )
            db.session.add(income)
            db.session.commit()
        
        # Count income records before marking the invoice as paid
        income_before = Income.query.filter_by(invoice_id=invoice.id).count()
        
        # Mark the invoice as paid
        response = self.client.post(
            f"/invoice/mark_paid/{invoice.id}", 
            data={
                "payment_method": "Bank Transfer",
                "payment_reference": "TRX12345"
            },
            follow_redirects=True
        )
        
        # Check that the invoice was marked as paid
        invoice = Invoice.query.get(invoice.id)
        self.assertEqual(invoice.status, "paid")
        
        # Check that no new income record was created
        income_after = Income.query.filter_by(invoice_id=invoice.id).count()
        self.assertEqual(income_after, income_before)


if __name__ == "__main__":
    unittest.main()