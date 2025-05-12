"""Service for exporting financial data to CSV and tax preparation formats."""

import csv
import io
import json
from datetime import datetime
from typing import Tuple, Dict, List, Optional, Union
from decimal import Decimal

from akowe.models.expense import Expense
from akowe.models.income import Income
from akowe.app.tax_dashboard import CRA_TAX_CATEGORIES, GST_HST_RATES


class ExportService:
    """Service for exporting financial data to CSV and tax preparation formats."""

    # CRA category mappings from internal categories to T2125 form fields
    CRA_CATEGORY_MAPPING = {
        "advertising": "Advertising",
        "meals_entertainment": "Meals and entertainment",
        "bad_debts": "Bad debts",
        "insurance": "Insurance",
        "interest": "Interest",
        "bank_charges": "Bank charges",
        "business_tax": "Business taxes, fees, licenses, dues",
        "office_supplies": "Office expenses",
        "supplies": "Supplies",
        "professional_fees": "Professional fees",
        "legal": "Legal, accounting, and other professional fees",
        "accounting": "Professional fees",
        "rent": "Rent",
        "repairs": "Maintenance and repairs",
        "maintenance": "Maintenance and repairs",
        "salaries": "Salaries, wages, and benefits",
        "travel": "Travel",
        "utilities": "Utilities",
        "telephone": "Utilities",
        "internet": "Utilities",
        "vehicle": "Motor vehicle expenses",
        "fuel": "Motor vehicle expenses",
        "home_office": "Home office expenses",
        "hardware": "Computer, equipment, and phone costs",
        "software": "Computer, equipment, and phone costs",
        "subscription": "Subscriptions",
        "training": "Other expenses",
        "memberships": "Business taxes, fees, licenses, dues",
        "other": "Other expenses",
        # Map other categories to appropriate T2125 fields
    }

    # Map Akowe categories to TurboTax categories
    TURBOTAX_CATEGORY_MAPPING = {
        "advertising": "Advertising",
        "meals_entertainment": "Meals and entertainment",
        "insurance": "Insurance",
        "interest": "Interest",
        "bank_charges": "Business expenses: Bank charges",
        "office_supplies": "Office expenses",
        "supplies": "Supplies",
        "professional_fees": "Professional fees",
        "rent": "Rent",
        "repairs": "Repairs and maintenance",
        "maintenance": "Repairs and maintenance",
        "travel": "Travel expenses",
        "utilities": "Utilities",
        "vehicle": "Motor vehicle expenses",
        "home_office": "Business-use-of-home expenses",
        "hardware": "Equipment under $500",
        "software": "Software expenses",
        "other": "Other business expenses",
        # Add more mappings as needed
    }

    # Map Akowe categories to Wealthsimple Tax categories
    WEALTHSIMPLE_CATEGORY_MAPPING = {
        "advertising": "Advertising",
        "meals_entertainment": "Meals and entertainment",
        "insurance": "Insurance",
        "interest": "Interest",
        "bank_charges": "Bank charges",
        "office_supplies": "Office expenses",
        "supplies": "Supplies",
        "professional_fees": "Professional fees",
        "rent": "Rent",
        "repairs": "Repairs and maintenance",
        "maintenance": "Repairs and maintenance",
        "travel": "Travel",
        "utilities": "Utilities",
        "vehicle": "Motor vehicle expenses",
        "home_office": "Business-use-of-home expenses",
        "hardware": "Capital equipment",
        "software": "Software",
        "other": "Other expenses",
        # Add more mappings as needed
    }

    @staticmethod
    def export_income_csv(year: int = None) -> Tuple[io.BytesIO, str]:
        """Export income data to CSV.

        Args:
            year: Optional year to filter income records

        Returns:
            Tuple containing the CSV data as BytesIO and the filename
        """
        # Create a string buffer for building the CSV
        string_buffer = io.StringIO()
        writer = csv.writer(string_buffer)

        # Write header row
        writer.writerow(["date", "amount", "client", "project", "invoice"])

        # Query income records, optionally filtered by year
        income_records = Income.query
        if year:
            income_records = income_records.filter(
                Income.date.between(datetime(year, 1, 1), datetime(year, 12, 31))
            )
        income_records = income_records.order_by(Income.date).all()

        # Write data rows
        for income in income_records:
            writer.writerow(
                [
                    income.date.strftime("%Y-%m-%d"),
                    f"{income.amount:.2f}",
                    income.client,
                    income.project,
                    income.invoice or "",
                ]
            )

        # Convert string buffer to bytes buffer
        bytes_buffer = io.BytesIO()
        bytes_buffer.write(string_buffer.getvalue().encode("utf-8"))
        bytes_buffer.seek(0)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        year_suffix = f"_{year}" if year else ""
        filename = f"income_export{year_suffix}_{timestamp}.csv"

        return bytes_buffer, filename

    @staticmethod
    def export_expense_csv(year: int = None, category: str = None) -> Tuple[io.BytesIO, str]:
        """Export expense data to CSV.

        Args:
            year: Optional year to filter expense records
            category: Optional category to filter expense records

        Returns:
            Tuple containing the CSV data as BytesIO and the filename
        """
        # Create a string buffer for building the CSV
        string_buffer = io.StringIO()
        writer = csv.writer(string_buffer)

        # Write header row
        writer.writerow(
            ["date", "title", "amount", "category", "payment_method", "status", "vendor", "receipt_url"]
        )

        # Query expense records, optionally filtered by year and category
        expense_records = Expense.query
        if year:
            expense_records = expense_records.filter(
                Expense.date.between(datetime(year, 1, 1), datetime(year, 12, 31))
            )
        if category:
            expense_records = expense_records.filter(Expense.category == category)
        expense_records = expense_records.order_by(Expense.date).all()

        # Write data rows
        for expense in expense_records:
            writer.writerow(
                [
                    expense.date.strftime("%Y-%m-%d"),
                    expense.title,
                    f"{expense.amount:.2f}",
                    expense.category,
                    expense.payment_method,
                    expense.status,
                    expense.vendor or "",
                    expense.receipt_url or "",
                ]
            )

        # Convert string buffer to bytes buffer
        bytes_buffer = io.BytesIO()
        bytes_buffer.write(string_buffer.getvalue().encode("utf-8"))
        bytes_buffer.seek(0)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        year_suffix = f"_{year}" if year else ""
        category_suffix = f"_{category}" if category else ""
        filename = f"expense_export{year_suffix}{category_suffix}_{timestamp}.csv"

        return bytes_buffer, filename

    @staticmethod
    def export_all_transactions_csv(year: int = None) -> Tuple[io.BytesIO, str]:
        """Export all financial transactions to CSV.

        Args:
            year: Optional year to filter transactions

        Returns:
            Tuple containing the CSV data as BytesIO and the filename
        """
        # Create a string buffer for building the CSV
        string_buffer = io.StringIO()
        writer = csv.writer(string_buffer)

        # Write header row
        writer.writerow(
            [
                "Date",
                "Type",
                "Description",
                "Amount",
                "Category",
                "Payment Method",
                "Status",
                "Reference",
                "Receipt URL",
            ]
        )

        # Query income records, optionally filtered by year
        income_records = Income.query
        if year:
            income_records = income_records.filter(
                Income.date.between(datetime(year, 1, 1), datetime(year, 12, 31))
            )
        income_records = income_records.order_by(Income.date).all()

        # Query expense records, optionally filtered by year
        expense_records = Expense.query
        if year:
            expense_records = expense_records.filter(
                Expense.date.between(datetime(year, 1, 1), datetime(year, 12, 31))
            )
        expense_records = expense_records.order_by(Expense.date).all()

        # Create a combined list of transactions to sort by date
        transactions = []

        for income in income_records:
            transactions.append(
                {
                    "date": income.date,
                    "type": "Income",
                    "description": f"{income.client} - {income.project}",
                    "amount": income.amount,
                    "category": "",
                    "payment_method": "",
                    "status": "received",
                    "reference": income.invoice or "",
                    "receipt_url": "",
                }
            )

        for expense in expense_records:
            transactions.append(
                {
                    "date": expense.date,
                    "type": "Expense",
                    "description": expense.title,
                    "amount": -expense.amount,  # Negative for expenses
                    "category": expense.category,
                    "payment_method": expense.payment_method,
                    "status": expense.status,
                    "reference": expense.vendor or "",
                    "receipt_url": expense.receipt_url or "",
                }
            )

        # Sort transactions by date
        transactions.sort(key=lambda x: x["date"])

        # Write data rows
        for transaction in transactions:
            writer.writerow(
                [
                    transaction["date"].strftime("%Y-%m-%d"),
                    transaction["type"],
                    transaction["description"],
                    f"{transaction['amount']:.2f}",
                    transaction["category"],
                    transaction["payment_method"],
                    transaction["status"],
                    transaction["reference"],
                    transaction["receipt_url"],
                ]
            )

        # Convert string buffer to bytes buffer
        bytes_buffer = io.BytesIO()
        bytes_buffer.write(string_buffer.getvalue().encode("utf-8"))
        bytes_buffer.seek(0)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        year_suffix = f"_{year}" if year else ""
        filename = f"all_transactions{year_suffix}_{timestamp}.csv"

        return bytes_buffer, filename
