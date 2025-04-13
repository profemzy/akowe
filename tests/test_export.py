"""Tests for export functionality."""
import pytest
import csv
import io
from datetime import date
from decimal import Decimal

from akowe.models.income import Income
from akowe.models.expense import Expense
from akowe.services.export_service import ExportService


def test_export_income_csv(app, sample_income):
    """Test exporting income to CSV."""
    with app.app_context():
        # Export income to CSV
        csv_data, filename = ExportService.export_income_csv()
        
        # Check filename
        assert filename.startswith('income_export_')
        assert filename.endswith('.csv')
        
        # Read CSV data
        reader = csv.reader(io.StringIO(csv_data.getvalue()))
        rows = list(reader)
        
        # Check header
        assert rows[0] == ['date', 'amount', 'client', 'project', 'invoice']
        
        # Check data rows (should match sample_income fixture)
        assert len(rows) == 3  # Header + 2 income records
        assert rows[1][0] in ['2025-03-21', '2025-02-21']  # Date
        assert rows[1][1] in ['9040.00']  # Amount
        assert rows[1][2] in ['SearchLabs (RAVL)']  # Client


def test_export_income_filtered_by_year(app, sample_income):
    """Test exporting income filtered by year."""
    with app.app_context():
        # Export income for 2025
        csv_data, filename = ExportService.export_income_csv(year=2025)
        
        # Check filename
        assert filename.startswith('income_export_2025_')
        
        # Read CSV data
        reader = csv.reader(io.StringIO(csv_data.getvalue()))
        rows = list(reader)
        
        # Check data (should include only 2025 records)
        assert len(rows) == 3  # Header + 2 records
        
        # Add an income for a different year
        income_2024 = Income(
            date=date(2024, 1, 15),
            amount=Decimal('5000.00'),
            client='OldClient',
            project='OldProject',
            invoice='OldInvoice'
        )
        app.db.session.add(income_2024)
        app.db.session.commit()
        
        # Export income for 2024
        csv_data, filename = ExportService.export_income_csv(year=2024)
        
        # Read CSV data
        reader = csv.reader(io.StringIO(csv_data.getvalue()))
        rows = list(reader)
        
        # Check that we only have the 2024 record
        assert len(rows) == 2  # Header + 1 record
        assert rows[1][0] == '2024-01-15'  # Date
        assert rows[1][2] == 'OldClient'  # Client


def test_export_expense_csv(app, sample_expense):
    """Test exporting expenses to CSV."""
    with app.app_context():
        # Export expenses to CSV
        csv_data, filename = ExportService.export_expense_csv()
        
        # Check filename
        assert filename.startswith('expense_export_')
        assert filename.endswith('.csv')
        
        # Read CSV data
        reader = csv.reader(io.StringIO(csv_data.getvalue()))
        rows = list(reader)
        
        # Check header
        assert rows[0] == ['date', 'title', 'amount', 'category', 'payment_method', 'status', 'vendor']
        
        # Check data rows (should match sample_expense fixture)
        assert len(rows) == 3  # Header + 2 expense records
        assert rows[1][0] in ['2025-04-12', '2025-03-30']  # Date
        assert rows[1][3] == 'hardware'  # Category


def test_export_expense_filtered_by_category(app, sample_expense):
    """Test exporting expenses filtered by category."""
    with app.app_context():
        # Add an expense with a different category
        expense_software = Expense(
            date=date(2025, 3, 15),
            title='Software License',
            amount=Decimal('299.99'),
            category='software',
            payment_method='credit_card',
            status='paid',
            vendor='Microsoft'
        )
        app.db.session.add(expense_software)
        app.db.session.commit()
        
        # Export expenses filtered by category
        csv_data, filename = ExportService.export_expense_csv(category='software')
        
        # Check filename
        assert filename.startswith('expense_export_')
        assert '_software_' in filename
        
        # Read CSV data
        reader = csv.reader(io.StringIO(csv_data.getvalue()))
        rows = list(reader)
        
        # Check data (should include only software category)
        assert len(rows) == 2  # Header + 1 record
        assert rows[1][2] == '299.99'  # Amount
        assert rows[1][3] == 'software'  # Category
        assert rows[1][6] == 'Microsoft'  # Vendor


def test_export_all_transactions(app, sample_income, sample_expense):
    """Test exporting all transactions to CSV."""
    with app.app_context():
        # Export all transactions
        csv_data, filename = ExportService.export_all_transactions_csv()
        
        # Check filename
        assert filename.startswith('all_transactions_')
        
        # Read CSV data
        reader = csv.reader(io.StringIO(csv_data.getvalue()))
        rows = list(reader)
        
        # Check header
        assert rows[0] == ['date', 'type', 'description', 'amount', 'category', 'payment_method', 'status', 'reference']
        
        # Check that we have all transactions (2 income + 2 expense = 4)
        assert len(rows) == 5  # Header + 4 records
        
        # Check that we have both income and expense records
        types = [row[1] for row in rows[1:]]
        assert 'Income' in types
        assert 'Expense' in types
        
        # Check that incomes are positive and expenses are negative
        for row in rows[1:]:
            if row[1] == 'Income':
                assert float(row[3]) > 0
            else:  # Expense
                assert float(row[3]) < 0