"""Test the invoice functionality."""
import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from flask import session

from akowe.models import db
from akowe.models.invoice import Invoice
from akowe.models.timesheet import Timesheet


def test_invoice_index_requires_login(client):
    """Test that the invoice index page requires login."""
    response = client.get('/invoice/')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_invoice_index(client, auth, test_user, sample_invoice):
    """Test that the invoice index page shows invoice entries."""
    auth.login()
    response = client.get('/invoice/')
    assert response.status_code == 200
    
    # Check that invoice is displayed
    assert sample_invoice.invoice_number.encode() in response.data
    assert sample_invoice.client.encode() in response.data
    assert b'Draft' in response.data  # Status


def test_invoice_new_form(client, auth, test_user, sample_timesheet):
    """Test that the new invoice form is accessible."""
    auth.login()
    response = client.get('/invoice/new')
    assert response.status_code == 200
    assert b'New Invoice' in response.data
    
    # Check for form elements
    assert b'<form' in response.data
    assert b'name="client"' in response.data
    assert b'name="issue_date"' in response.data
    assert b'name="due_date"' in response.data
    assert b'name="tax_rate"' in response.data
    assert b'name="notes"' in response.data
    
    # Check that unbilled timesheet entries are shown
    for entry in sample_timesheet:
        if entry.status == 'pending':
            assert entry.client.encode() in response.data
            assert entry.project.encode() in response.data


def test_invoice_create(client, auth, test_user, app, sample_timesheet):
    """Test creating a new invoice."""
    auth.login()
    
    # Get IDs of unbilled timesheet entries
    with app.app_context():
        unbilled = Timesheet.query.filter_by(
            user_id=test_user.id,
            status='pending'
        ).all()
        entry_ids = [str(entry.id) for entry in unbilled]
    
    # Submit new invoice
    response = client.post('/invoice/new', data={
        'client': 'TestClient',
        'issue_date': '2025-04-25',
        'due_date': '2025-05-25',
        'tax_rate': '5.00',
        'notes': 'Test invoice notes',
        'timesheet_entries': entry_ids
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Invoice created successfully!' in response.data
    
    # Verify invoice was created in database
    with app.app_context():
        invoice = Invoice.query.filter_by(client='TestClient').first()
        assert invoice is not None
        assert invoice.issue_date == date(2025, 4, 25)
        assert invoice.due_date == date(2025, 5, 25)
        assert invoice.tax_rate == Decimal('5.00')
        assert invoice.notes == 'Test invoice notes'
        assert invoice.status == 'draft'
        assert invoice.user_id == test_user.id
        
        # Verify timesheet entries were linked and marked as billed
        for entry_id in entry_ids:
            entry = Timesheet.query.get(int(entry_id))
            assert entry.invoice_id == invoice.id
            assert entry.status == 'billed'
        
        # Verify totals were calculated
        assert invoice.subtotal > 0
        assert invoice.tax_amount == invoice.subtotal * Decimal('0.05')
        assert invoice.total == invoice.subtotal + invoice.tax_amount


def test_invoice_view(client, auth, sample_invoice):
    """Test viewing an invoice."""
    auth.login()
    
    response = client.get(f'/invoice/view/{sample_invoice.id}')
    assert response.status_code == 200
    
    # Check invoice details are displayed
    assert sample_invoice.invoice_number.encode() in response.data
    assert sample_invoice.client.encode() in response.data
    assert sample_invoice.issue_date.strftime('%Y-%m-%d').encode() in response.data
    assert sample_invoice.due_date.strftime('%Y-%m-%d').encode() in response.data
    
    # Check for timesheet entries
    for entry in sample_invoice.timesheet_entries:
        assert entry.project.encode() in response.data
        assert f"{entry.hours:.2f}".encode() in response.data
        assert f"{entry.hourly_rate:.2f}".encode() in response.data


def test_invoice_edit(client, auth, sample_invoice, app):
    """Test editing an invoice."""
    auth.login()
    
    # Check edit form
    response = client.get(f'/invoice/edit/{sample_invoice.id}')
    assert response.status_code == 200
    assert b'Edit Invoice' in response.data
    
    # Get current timesheet entry IDs
    with app.app_context():
        current_entries = [str(entry.id) for entry in sample_invoice.timesheet_entries]
    
    # Submit edit with same entries
    response = client.post(f'/invoice/edit/{sample_invoice.id}', data={
        'client': 'UpdatedClient',
        'issue_date': '2025-04-26',
        'due_date': '2025-05-26',
        'tax_rate': '7.50',
        'notes': 'Updated invoice notes',
        'timesheet_entries': current_entries
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Invoice updated successfully!' in response.data
    
    # Verify changes in database
    with app.app_context():
        updated_invoice = Invoice.query.get(sample_invoice.id)
        assert updated_invoice.client == 'UpdatedClient'
        assert updated_invoice.issue_date == date(2025, 4, 26)
        assert updated_invoice.due_date == date(2025, 5, 26)
        assert updated_invoice.tax_rate == Decimal('7.50')
        assert updated_invoice.notes == 'Updated invoice notes'


def test_invoice_delete(client, auth, sample_invoice, app):
    """Test deleting an invoice."""
    auth.login()
    
    # Check initial status of timesheet entries
    with app.app_context():
        entries = Timesheet.query.filter_by(invoice_id=sample_invoice.id).all()
        assert all(entry.status == 'billed' for entry in entries)
    
    # Delete the invoice
    response = client.post(f'/invoice/delete/{sample_invoice.id}', follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Invoice deleted successfully!' in response.data
    
    # Verify invoice was deleted and timesheet entries were updated
    with app.app_context():
        invoice = Invoice.query.get(sample_invoice.id)
        assert invoice is None
        
        # Entries should now be unbilled
        for entry in entries:
            refreshed_entry = Timesheet.query.get(entry.id)
            assert refreshed_entry.invoice_id is None
            assert refreshed_entry.status == 'pending'


def test_invoice_mark_sent(client, auth, sample_invoice, app):
    """Test marking an invoice as sent."""
    auth.login()
    
    # Mark as sent
    response = client.post(f'/invoice/mark_sent/{sample_invoice.id}', follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Invoice marked as sent!' in response.data
    
    # Verify status change
    with app.app_context():
        invoice = Invoice.query.get(sample_invoice.id)
        assert invoice.status == 'sent'
        assert invoice.sent_date is not None


def test_invoice_mark_paid(client, auth, app):
    """Test marking an invoice as paid."""
    auth.login()
    
    # First create and mark an invoice as sent
    with app.app_context():
        # Get unbilled entries
        entries = Timesheet.query.filter_by(
            user_id=auth.test_user.id,
            status='pending'
        ).limit(2).all()
        
        # Create invoice
        invoice = Invoice(
            invoice_number='INV-202504-0002',
            client='PaymentTestClient',
            issue_date=date(2025, 4, 20),
            due_date=date(2025, 5, 20),
            tax_rate=Decimal('10.00'),
            status='sent',
            sent_date=datetime.utcnow(),
            user_id=auth.test_user.id
        )
        
        db.session.add(invoice)
        db.session.flush()
        
        # Link entries
        for entry in entries:
            entry.invoice_id = invoice.id
            entry.status = 'billed'
        
        # Calculate totals
        invoice.calculate_totals()
        db.session.commit()
        
        invoice_id = invoice.id
    
    # Mark as paid
    response = client.post(f'/invoice/mark_paid/{invoice_id}', data={
        'payment_method': 'bank_transfer',
        'payment_reference': 'TRX123456789'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Invoice marked as paid!' in response.data
    
    # Verify status change
    with app.app_context():
        invoice = Invoice.query.get(invoice_id)
        assert invoice.status == 'paid'
        assert invoice.paid_date is not None
        assert invoice.payment_method == 'bank_transfer'
        assert invoice.payment_reference == 'TRX123456789'
        
        # Verify timesheet entries
        for entry in invoice.timesheet_entries:
            assert entry.status == 'paid'


def test_invoice_print(client, auth, sample_invoice):
    """Test print view for invoice."""
    auth.login()
    
    response = client.get(f'/invoice/print/{sample_invoice.id}')
    assert response.status_code == 200
    
    # Check for print-specific elements
    assert b'<title>Invoice' in response.data
    assert b'Print Invoice' in response.data
    assert b'Thank you for your business!' in response.data
    
    # Check invoice details
    assert sample_invoice.invoice_number.encode() in response.data
    assert sample_invoice.company_name.encode() in response.data
    
    # HTML structure for print view
    assert b'<style' in response.data  # Should have print styles
    assert b'@media print' in response.data


def test_company_name_from_env(client, auth, app, test_user, sample_timesheet, monkeypatch):
    """Test that the company name is taken from environment variable."""
    auth.login()
    
    # Set environment variable
    monkeypatch.setenv('COMPANY_NAME', 'Test Company Name')
    
    # Get IDs of unbilled timesheet entries
    with app.app_context():
        unbilled = Timesheet.query.filter_by(
            user_id=test_user.id,
            status='pending'
        ).limit(1).all()
        entry_ids = [str(entry.id) for entry in unbilled]
    
    # Submit new invoice
    response = client.post('/invoice/new', data={
        'client': 'EnvTestClient',
        'issue_date': '2025-04-27',
        'due_date': '2025-05-27',
        'tax_rate': '6.00',
        'notes': 'Testing environment variable',
        'timesheet_entries': entry_ids
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verify company name in database
    with app.app_context():
        invoice = Invoice.query.filter_by(client='EnvTestClient').first()
        assert invoice is not None
        assert invoice.company_name == 'Test Company Name'