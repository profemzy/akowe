"""Tests for expense-related functionality."""

import pytest
from decimal import Decimal
from datetime import date
import io
from unittest.mock import patch

from akowe.models.expense import Expense


def test_expense_list(client, auth, sample_expense):
    """Test listing expense records."""
    auth.login()
    response = client.get("/expense/")

    # Check that the expense data is displayed
    assert b"WD Red Plus 12TB NAS Hard Disk Drive" in response.data
    assert b"386.37" in response.data
    assert b"Newegg" in response.data


def test_expense_creation(client, auth, app):
    """Test creating a new expense record."""
    auth.login()

    # Submit the form
    response = client.post(
        "/expense/new",
        data={
            "date": "2025-05-01",
            "title": "Test Expense",
            "amount": "250.00",
            "category": "software",
            "payment_method": "credit_card",
            "status": "paid",
            "vendor": "Test Vendor",
        },
        follow_redirects=True,
    )

    assert b"Expense record added successfully" in response.data

    # Verify it's in the database
    with app.app_context():
        expense = Expense.query.filter_by(title="Test Expense").first()
        assert expense is not None
        assert expense.amount == Decimal("250.00")
        assert expense.date == date(2025, 5, 1)
        assert expense.category == "software"
        assert expense.payment_method == "credit_card"
        assert expense.status == "paid"
        assert expense.vendor == "Test Vendor"
        assert expense.receipt_blob_name is None
        assert expense.receipt_url is None


@patch("akowe.services.storage_service.StorageService.upload_file")
def test_expense_creation_with_receipt(mock_upload_file, client, auth, app):
    """Test creating a new expense record with receipt."""
    auth.login()

    # Mock storage service response
    mock_upload_file.return_value = (
        "test-blob-name.jpg",
        "https://test.blob.core.windows.net/receipts/test-blob-name.jpg",
    )

    # Prepare form data
    form_data = {
        "date": "2025-05-01",
        "title": "Expense With Receipt",
        "amount": "350.00",
        "category": "hardware",
        "payment_method": "credit_card",
        "status": "paid",
        "vendor": "Receipt Vendor",
    }

    # Create file data
    file_data = io.BytesIO(b"test file content")

    # Submit the form with file
    response = client.post(
        "/expense/new",
        data={**form_data, "receipt": (file_data, "receipt.jpg")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert b"Expense record added successfully" in response.data

    # Verify it's in the database with receipt information
    with app.app_context():
        expense = Expense.query.filter_by(title="Expense With Receipt").first()
        assert expense is not None
        assert expense.amount == Decimal("350.00")
        assert expense.receipt_blob_name == "test-blob-name.jpg"
        assert (
            expense.receipt_url == "https://test.blob.core.windows.net/receipts/test-blob-name.jpg"
        )


def test_expense_edit(client, auth, app, sample_expense):
    """Test editing an expense record."""
    auth.login()

    with app.app_context():
        # Get ID of first expense record
        expense_id = Expense.query.first().id

    # Submit the edit form
    response = client.post(
        f"/expense/edit/{expense_id}",
        data={
            "date": "2025-04-12",
            "title": "WD Red Plus 12TB NAS Hard Disk Drive",
            "amount": "400.00",  # Changed amount
            "category": "hardware",
            "payment_method": "credit_card",
            "status": "paid",  # Changed status
            "vendor": "Newegg",
        },
        follow_redirects=True,
    )

    assert b"Expense record updated successfully" in response.data

    # Verify it's updated in the database
    with app.app_context():
        expense = Expense.query.get(expense_id)
        assert expense.amount == Decimal("400.00")
        assert expense.status == "paid"


def test_expense_delete(client, auth, app, sample_expense):
    """Test deleting an expense record."""
    auth.login()

    with app.app_context():
        # Get ID of first expense record
        expense_id = Expense.query.first().id
        initial_count = Expense.query.count()

    # Submit deletion
    response = client.post(f"/expense/delete/{expense_id}", follow_redirects=True)

    assert b"Expense record deleted successfully" in response.data

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

    csv_data = io.BytesIO(csv_content.encode("utf-8"))

    # Post the CSV file
    response = client.post(
        "/expense/import", data={"file": (csv_data, "expense.csv")}, follow_redirects=True
    )

    assert b"Successfully imported" in response.data

    # Verify the data was imported
    with app.app_context():
        expense = Expense.query.filter_by(title="Imported Expense").first()
        assert expense is not None
        assert expense.amount == Decimal("199.99")
        assert expense.date == date(2025, 6, 21)
        assert expense.category == "software"
        assert expense.payment_method == "debit_card"
        assert expense.status == "pending"
        assert expense.vendor == "ImportVendor"


@patch("akowe.services.storage_service.StorageService.generate_sas_url")
def test_view_receipt(mock_generate_sas_url, client, auth, app, sample_expense):
    """Test viewing receipt."""
    auth.login()

    with app.app_context():
        # Get first expense and add receipt info
        expense = Expense.query.first()
        expense.receipt_blob_name = "test-blob-name.jpg"
        expense.receipt_url = "https://test.blob.core.windows.net/receipts/test-blob-name.jpg"
        app.db.session.commit()
        expense_id = expense.id

    # Mock SAS URL generation
    mock_generate_sas_url.return_value = (
        "https://test.blob.core.windows.net/receipts/test-blob-name.jpg?sastoken"
    )

    # Request to view receipt
    response = client.get(f"/expense/view-receipt/{expense_id}", follow_redirects=False)

    # Should redirect to the SAS URL
    assert response.status_code == 302
    assert (
        response.location
        == "https://test.blob.core.windows.net/receipts/test-blob-name.jpg?sastoken"
    )

    # Verify SAS URL was generated with the correct parameters
    mock_generate_sas_url.assert_called_once_with("test-blob-name.jpg", "receipts")


@patch("akowe.services.storage_service.StorageService.delete_file")
def test_delete_receipt(mock_delete_file, client, auth, app, sample_expense):
    """Test deleting a receipt from an expense."""
    auth.login()

    with app.app_context():
        # Get first expense and add receipt info
        expense = Expense.query.first()
        expense.receipt_blob_name = "test-blob-name.jpg"
        expense.receipt_url = "https://test.blob.core.windows.net/receipts/test-blob-name.jpg"
        app.db.session.commit()
        expense_id = expense.id

    # Delete receipt
    response = client.post(f"/expense/delete-receipt/{expense_id}", follow_redirects=True)

    assert b"Receipt deleted successfully" in response.data

    # Verify receipt information was removed
    with app.app_context():
        expense = Expense.query.get(expense_id)
        assert expense.receipt_blob_name is None
        assert expense.receipt_url is None

    # Verify file was deleted from storage
    mock_delete_file.assert_called_once_with("test-blob-name.jpg", "receipts")
