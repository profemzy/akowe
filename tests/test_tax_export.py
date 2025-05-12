"""Test the tax export functionality."""

import io
import csv
import pytest
from datetime import date
from decimal import Decimal

from akowe.services.tax_export_service import TaxExportService
from akowe.app.tax_dashboard import GST_HST_RATES, QST_RATE


def test_t2125_export_format(app, sample_income, sample_expense):
    """Test the T2125 export format."""
    with app.app_context():
        # Test Ontario export (13% HST)
        buffer, filename = TaxExportService.export_t2125_format(2025, "Ontario")
        
        # Check that the buffer contains data
        assert buffer.getvalue()
        assert isinstance(buffer, io.BytesIO)
        
        # Check filename format
        assert filename.startswith("T2125_CRA_export_2025_")
        assert filename.endswith(".csv")
        
        # Parse CSV data for validation
        buffer.seek(0)
        reader = csv.reader(io.StringIO(buffer.getvalue().decode('utf-8')))
        rows = list(reader)
        
        # Check headers
        assert rows[0] == ['Date', 'Description', 'Amount', 'T2125 Category', 'GST/HST Paid', 'Receipt Reference']
        
        # Find the income section header
        income_section_idx = None
        for i, row in enumerate(rows):
            if row and row[0] == 'INCOME SECTION':
                income_section_idx = i
                break
                
        assert income_section_idx is not None, "Income section not found in export"
        
        # Check income header
        income_header = rows[income_section_idx + 1]
        assert income_header == [
            'Date', 'Description', 'Amount', 'T2125 Income Type', 
            'GST/HST Collected', 'Reference'
        ]
        
        # Check income rows
        income_rows = [rows[i] for i in range(income_section_idx + 2, len(rows))]
        assert len(income_rows) == len(sample_income)
        
        # Check tax calculations for first income record
        # For income of $9040.00 with 13% HST in Ontario
        # HST collected should be $9040.00 - ($9040.00 / 1.13) = $1040.00
        first_income = income_rows[0]
        income_amount = Decimal(first_income[2])
        tax_collected = Decimal(first_income[4])
        
        # Calculate expected tax
        hst_rate = Decimal(str(GST_HST_RATES["Ontario"]))
        expected_tax = income_amount - (income_amount / (Decimal('1.0') + hst_rate))
        expected_tax = expected_tax.quantize(Decimal('0.01'))
        
        assert tax_collected == expected_tax, f"Expected HST collected: {expected_tax}, got: {tax_collected}"


def test_turbotax_export_format(app, sample_income, sample_expense):
    """Test the TurboTax export format."""
    with app.app_context():
        # Test Ontario export (13% HST)
        buffer, filename = TaxExportService.export_turbotax_format(2025, "Ontario")
        
        # Check that the buffer contains data
        assert buffer.getvalue()
        assert isinstance(buffer, io.BytesIO)
        
        # Check filename format
        assert filename.startswith("TurboTax_export_2025_")
        assert filename.endswith(".csv")
        
        # Parse CSV data for validation
        buffer.seek(0)
        reader = csv.reader(io.StringIO(buffer.getvalue().decode('utf-8')))
        rows = list(reader)
        
        # Check headers
        assert rows[0] == ['Date', 'Description', 'Amount', 'Category', 'GST/HST', 'Tax Form', 'TurboTax Category']
        
        # Count expense and income rows
        expense_count = 0
        income_count = 0
        
        for row in rows[1:]:  # Skip header
            if len(row) >= 6:  # Ensure row has enough columns
                if row[5] == 'T2125' and 'income' in row[6].lower():
                    income_count += 1
                    
                    # Check tax calculations
                    income_amount = Decimal(row[2])
                    tax_collected = Decimal(row[4])
                    
                    # Calculate expected tax
                    hst_rate = Decimal(str(GST_HST_RATES["Ontario"]))
                    expected_tax = income_amount - (income_amount / (Decimal('1.0') + hst_rate))
                    expected_tax = expected_tax.quantize(Decimal('0.01'))
                    
                    assert tax_collected == expected_tax, f"Income row {row}: Expected HST: {expected_tax}, got: {tax_collected}"
                    
                elif row[5] == 'T2125' and 'income' not in row[6].lower():
                    expense_count += 1
        
        # Verify we found the right number of records
        assert expense_count == len(sample_expense)
        assert income_count == len(sample_income)


def test_wealthsimple_export_format(app, sample_income, sample_expense):
    """Test the Wealthsimple Tax export format."""
    with app.app_context():
        # Test Ontario export (13% HST)
        buffer, filename = TaxExportService.export_wealthsimple_format(2025, "Ontario")
        
        # Check that the buffer contains data
        assert buffer.getvalue()
        assert isinstance(buffer, io.BytesIO)
        
        # Check filename format
        assert filename.startswith("WealthsimpleTax_export_2025_")
        assert filename.endswith(".csv")
        
        # Parse CSV data for validation
        buffer.seek(0)
        reader = csv.reader(io.StringIO(buffer.getvalue().decode('utf-8')))
        rows = list(reader)
        
        # Check headers
        assert rows[0] == ['Date', 'Description', 'Amount', 'Category', 'GST/HST', 'Type']
        
        # Count expense and income rows
        expense_count = 0
        income_count = 0
        
        for row in rows[1:]:  # Skip header
            if len(row) >= 6:  # Ensure row has enough columns
                if row[5] == 'Income':
                    income_count += 1
                    
                    # Check tax calculations
                    income_amount = Decimal(row[2])
                    tax_collected = Decimal(row[4])
                    
                    # Calculate expected tax
                    hst_rate = Decimal(str(GST_HST_RATES["Ontario"]))
                    expected_tax = income_amount - (income_amount / (Decimal('1.0') + hst_rate))
                    expected_tax = expected_tax.quantize(Decimal('0.01'))
                    
                    assert tax_collected == expected_tax, f"Income row {row}: Expected HST: {expected_tax}, got: {tax_collected}"
                    
                elif row[5] == 'Expense':
                    expense_count += 1
        
        # Verify we found the right number of records
        assert expense_count == len(sample_expense)
        assert income_count == len(sample_income)


def test_quebec_tax_calculations(app, sample_income, sample_expense):
    """Test the Quebec GST/QST tax calculations."""
    with app.app_context():
        # Test Quebec export (5% GST + 9.975% QST)
        buffer, filename = TaxExportService.export_t2125_format(2025, "Quebec")
        
        # Parse CSV data for validation
        buffer.seek(0)
        reader = csv.reader(io.StringIO(buffer.getvalue().decode('utf-8')))
        rows = list(reader)
        
        # Find the income section header
        income_section_idx = None
        for i, row in enumerate(rows):
            if row and row[0] == 'INCOME SECTION':
                income_section_idx = i
                break
                
        assert income_section_idx is not None, "Income section not found in export"
        
        # Check income header - should have GST/QST Collected for Quebec
        income_header = rows[income_section_idx + 1]
        assert 'GST/QST Collected' in income_header
        
        # Check income rows
        income_rows = [rows[i] for i in range(income_section_idx + 2, len(rows))]
        assert len(income_rows) == len(sample_income)
        
        # Check tax calculations for first income record
        first_income = income_rows[0]
        income_amount = Decimal(first_income[2])
        tax_collected = Decimal(first_income[4])
        
        # Calculate expected tax for Quebec
        gst_rate = Decimal(str(GST_HST_RATES["Quebec"]))  # 5%
        qst_rate = Decimal(str(QST_RATE))                 # 9.975%
        
        # GST calculation - on original amount
        expected_gst = (income_amount * gst_rate) / (Decimal('1.0') + gst_rate + (gst_rate * qst_rate))
        expected_gst = expected_gst.quantize(Decimal('0.01'))
        
        # QST calculation - on GST-included amount
        expected_qst = ((income_amount - expected_gst) * qst_rate) / (Decimal('1.0') + qst_rate)
        expected_qst = expected_qst.quantize(Decimal('0.01'))
        
        expected_total_tax = expected_gst + expected_qst
        expected_total_tax = expected_total_tax.quantize(Decimal('0.01'))
        
        assert tax_collected == expected_total_tax, f"Expected GST/QST: {expected_total_tax}, got: {tax_collected}"


def test_all_provinces_tax_rates(app, test_user):
    """Test tax calculations for all provinces."""
    with app.app_context():
        # Create a specific income record for testing
        from akowe.models.income import Income
        from akowe.models import db

        test_amount = Decimal("1000.00")  # Easy to calculate percentages

        # Create a test income record
        test_income = Income(
            date=date(2025, 1, 1),
            amount=test_amount,
            client="Test Client",
            project="Test Project",
            invoice="Test Invoice",
            user_id=test_user.id  # Use fixture test user
        )
        
        db.session.add(test_income)
        db.session.commit()
        
        try:
            # Test each province
            for province, rate in GST_HST_RATES.items():
                if province == "Quebec":
                    # Quebec has special GST+QST calculation
                    continue
                
                # Get export for this province
                buffer, _ = TaxExportService.export_t2125_format(2025, province)
                
                # Parse CSV for validation
                buffer.seek(0)
                reader = csv.reader(io.StringIO(buffer.getvalue().decode('utf-8')))
                rows = list(reader)
                
                # Find the income section
                income_section_idx = None
                for i, row in enumerate(rows):
                    if row and row[0] == "INCOME SECTION":
                        income_section_idx = i
                        break

                assert income_section_idx is not None, f"Income section not found in {province} export"

                # Get income rows (skip header)
                income_rows = [row for row in rows[income_section_idx + 2:] if row and len(row) >= 3]

                # Debug output - print all income rows to see what's wrong
                print(f"\nIncome rows for {province}:")
                for idx, row in enumerate(income_rows):
                    print(f"  Row {idx}: {row}")

                # Find our test income record by looking for any row with "Test Client"
                income_row = None
                for row in income_rows:
                    if len(row) >= 3 and "Test Client" in row[1]:
                        income_row = row
                        break

                # If we still didn't find it, use the first income row if available
                if income_row is None and income_rows:
                    income_row = income_rows[0]
                    print(f"Using first available income row for {province}: {income_row}")

                assert income_row is not None, f"Test income record not found in {province} export"
                
                # Get the tax amount
                tax_collected = Decimal(income_row[4])
                
                # Calculate expected HST/GST
                tax_rate = Decimal(str(rate))
                expected_tax = test_amount - (test_amount / (Decimal('1.0') + tax_rate))
                expected_tax = expected_tax.quantize(Decimal('0.01'))
                
                assert tax_collected == expected_tax, f"{province}: Expected tax: {expected_tax}, got: {tax_collected}"
        
        finally:
            # Clean up test income record
            db.session.delete(test_income)
            db.session.commit()