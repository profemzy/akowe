"""Test the export API endpoints."""

import io
import csv
import pytest
from decimal import Decimal

from akowe.app.tax_dashboard import GST_HST_RATES


def test_export_income_endpoint(client, auth, sample_income):
    """Test the export_income endpoint."""
    # Login first
    auth.login()
    
    # Test export endpoint
    response = client.get("/export/income")
    
    # Check response status
    assert response.status_code == 200
    
    # Verify content type and attachment filename
    assert response.mimetype == "text/csv"
    assert "attachment" in response.headers["Content-Disposition"]
    assert "income_export" in response.headers["Content-Disposition"]
    
    # Parse CSV content
    content = response.data.decode("utf-8")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    
    # Check header row (case-insensitive comparison)
    actual_headers = [h.lower() for h in rows[0]]
    expected_headers = ["date", "amount", "client", "project", "invoice"]
    assert actual_headers == expected_headers
    
    # Check that we have the expected number of rows (header + data)
    assert len(rows) == len(sample_income) + 1
    
    # Check data rows - but don't validate specific order since data might be returned differently
    # Just check that all data is present somewhere in the results
    all_rows_text = " ".join([" ".join(row) for row in rows])
    for income in sample_income:
        assert str(income.amount) in all_rows_text
        assert income.client in all_rows_text
        assert income.project in all_rows_text
        assert income.invoice in all_rows_text


def test_export_expense_endpoint(client, auth, sample_expense):
    """Test the export_expense endpoint."""
    # Login first
    auth.login()
    
    # Test export endpoint
    response = client.get("/export/expense")
    
    # Check response status
    assert response.status_code == 200
    
    # Verify content type and attachment filename
    assert response.mimetype == "text/csv"
    assert "attachment" in response.headers["Content-Disposition"]
    assert "expense_export" in response.headers["Content-Disposition"]
    
    # Parse CSV content
    content = response.data.decode("utf-8")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    
    # Check header row (case-insensitive comparison)
    actual_headers = [h.lower() for h in rows[0]]
    expected_headers = ["date", "title", "amount", "category", "payment_method", "status", "vendor", "receipt_url"]
    assert actual_headers == expected_headers
    
    # Check that we have the expected number of rows (header + data)
    assert len(rows) == len(sample_expense) + 1
    
    # Check data rows - but don't validate specific order since data might be returned differently
    # Just check that all data is present somewhere in the results
    all_rows_text = " ".join([" ".join(row) for row in rows])
    for expense in sample_expense:
        assert expense.title in all_rows_text
        assert str(expense.amount) in all_rows_text
        assert expense.category in all_rows_text
        assert expense.vendor in all_rows_text
        assert expense.payment_method in all_rows_text
        assert expense.status in all_rows_text


def test_export_t2125_endpoint(client, auth, sample_income, sample_expense):
    """Test the export_t2125 endpoint."""
    # Login first
    auth.login()
    
    # Test export endpoint with Ontario as province
    response = client.get("/export/tax/t2125?year=2025&province=Ontario")
    
    # Check response status
    assert response.status_code == 200
    
    # Verify content type and attachment filename
    assert response.mimetype == "text/csv"
    assert "attachment" in response.headers["Content-Disposition"]
    assert "T2125_CRA_export" in response.headers["Content-Disposition"]
    
    # Parse CSV content
    content = response.data.decode("utf-8")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    
    # Find the income section
    income_section_idx = None
    for i, row in enumerate(rows):
        if row and row[0] == "INCOME SECTION":
            income_section_idx = i
            break
    
    assert income_section_idx is not None, "Income section not found in export"
    
    # Get income rows (skip income header)
    income_rows = [row for row in rows[income_section_idx + 2:] if row and len(row) >= 5]
    
    # Verify tax calculation for income
    for row in income_rows:
        income_amount = Decimal(row[2])
        tax_collected = Decimal(row[4])
        
        # Calculate expected HST (13% for Ontario)
        hst_rate = Decimal(str(GST_HST_RATES["Ontario"]))
        expected_tax = income_amount - (income_amount / (Decimal('1.0') + hst_rate))
        expected_tax = expected_tax.quantize(Decimal('0.01'))
        
        assert tax_collected == expected_tax, f"Income row {row}: Expected HST: {expected_tax}, got: {tax_collected}"


def test_export_turbotax_endpoint(client, auth, sample_income):
    """Test the export_turbotax endpoint."""
    # Login first
    auth.login()
    
    # Test export endpoint with Ontario as province
    response = client.get("/export/tax/turbotax?year=2025&province=Ontario")
    
    # Check response status
    assert response.status_code == 200
    
    # Verify content type and attachment filename
    assert response.mimetype == "text/csv"
    assert "attachment" in response.headers["Content-Disposition"]
    assert "TurboTax_export" in response.headers["Content-Disposition"]
    
    # Parse CSV content
    content = response.data.decode("utf-8")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    
    # Check header row
    assert "GST/HST" in rows[0]
    
    # Find income rows
    income_rows = []
    for row in rows[1:]:  # Skip header
        if len(row) >= 7 and row[6] == "Self-employment income":
            income_rows.append(row)
    
    # Verify we found income rows
    assert len(income_rows) > 0, "No income rows found in TurboTax export"
    
    # Verify tax calculation for income
    for row in income_rows:
        income_amount = Decimal(row[2])
        tax_collected = Decimal(row[4])
        
        # Calculate expected HST (13% for Ontario)
        hst_rate = Decimal(str(GST_HST_RATES["Ontario"]))
        expected_tax = income_amount - (income_amount / (Decimal('1.0') + hst_rate))
        expected_tax = expected_tax.quantize(Decimal('0.01'))
        
        assert tax_collected == expected_tax, f"Income row {row}: Expected HST: {expected_tax}, got: {tax_collected}"


def test_export_wealthsimple_endpoint(client, auth, sample_income):
    """Test the export_wealthsimple endpoint."""
    # Login first
    auth.login()
    
    # Test export endpoint with Ontario as province
    response = client.get("/export/tax/wealthsimple?year=2025&province=Ontario")
    
    # Check response status
    assert response.status_code == 200
    
    # Verify content type and attachment filename
    assert response.mimetype == "text/csv"
    assert "attachment" in response.headers["Content-Disposition"]
    assert "WealthsimpleTax_export" in response.headers["Content-Disposition"]
    
    # Parse CSV content
    content = response.data.decode("utf-8")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    
    # Check header row
    assert "GST/HST" in rows[0]
    
    # Find income rows
    income_rows = []
    for row in rows[1:]:  # Skip header
        if len(row) >= 6 and row[5] == "Income":
            income_rows.append(row)
    
    # Verify we found income rows
    assert len(income_rows) > 0, "No income rows found in Wealthsimple export"
    
    # Verify tax calculation for income
    for row in income_rows:
        income_amount = Decimal(row[2])
        tax_collected = Decimal(row[4])
        
        # Calculate expected HST (13% for Ontario)
        hst_rate = Decimal(str(GST_HST_RATES["Ontario"]))
        expected_tax = income_amount - (income_amount / (Decimal('1.0') + hst_rate))
        expected_tax = expected_tax.quantize(Decimal('0.01'))
        
        assert tax_collected == expected_tax, f"Income row {row}: Expected HST: {expected_tax}, got: {tax_collected}"


def test_unauthorized_access(client):
    """Test that unauthorized users cannot access export endpoints."""
    # Try to access export endpoints without logging in
    endpoints = [
        "/export/income",
        "/export/expense",
        "/export/all",
        "/export/tax/t2125?year=2025",
        "/export/tax/turbotax?year=2025",
        "/export/tax/wealthsimple?year=2025",
        "/export/tax/corporate/t2gifi?year=2025",
        "/export/tax/corporate/schedule8?year=2025",
        "/export/tax/corporate/turbotax?year=2025",
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        
        # Should redirect to login page
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]